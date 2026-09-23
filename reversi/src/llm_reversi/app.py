"""리버시 API와 정적 브라우저 화면."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Literal

from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, ConfigDict

from .game import GameError, GameManager


class NewGameRequest(BaseModel):
    """새 게임 또는 게임 초기화 설정."""

    model_config = ConfigDict(extra="forbid", strict=True)

    game_mode: Literal["human_vs_llm", "cli_vs_cli"] = "human_vs_llm"
    human_color: Literal["black", "white"] | None = None
    black_name: str | None = None
    white_name: str | None = None


class MoveRequest(BaseModel):
    """착수와 CLI 대기 설정."""

    model_config = ConfigDict(extra="forbid", strict=True)

    move: str
    wait: bool = True


class TakebackRequest(BaseModel):
    """되돌리기 요청 또는 응답."""

    model_config = ConfigDict(extra="forbid", strict=True)

    action: Literal["request", "accept", "reject"]


class WaitRequest(BaseModel):
    """상태 대기용 선택적 revision 커서."""

    model_config = ConfigDict(extra="forbid", strict=True)

    after_revision: int | None = None


manager = GameManager()
app = FastAPI(title="llm-reversi", version="0.1.0")


def _raise_game_error(error: GameError) -> None:
    """게임 오류를 계약된 HTTP 응답으로 바꾼다."""
    raise HTTPException(
        status_code=error.status_code,
        detail={"code": error.code, "message": error.message},
    ) from error


@app.get("/api/health")
async def health() -> dict[str, str]:
    """서버 준비 상태를 반환한다."""
    return {"app": "llm-reversi", "status": "ok"}


@app.get("/api/state")
async def state() -> dict[str, object]:
    """현재 스냅샷을 반환한다."""
    return await manager.snapshot()


@app.post("/api/games")
async def games(request: NewGameRequest) -> dict[str, object]:
    """게임을 시작하거나 새 게임으로 초기화한다."""
    try:
        return await manager.start_game(
            request.human_color,
            game_mode=request.game_mode,
            black_name=request.black_name,
            white_name=request.white_name,
        )
    except GameError as error:
        _raise_game_error(error)


@app.post("/api/human/moves")
async def human_moves(request: MoveRequest) -> dict[str, object]:
    """브라우저 사람의 착수를 적용한다."""
    try:
        return await manager.human_move(request.move)
    except GameError as error:
        _raise_game_error(error)


@app.post("/api/llm/moves")
async def llm_moves(request: MoveRequest) -> dict[str, object]:
    """LLM의 착수를 적용한다."""
    try:
        return await manager.llm_move(request.move, request.wait)
    except GameError as error:
        _raise_game_error(error)


@app.post("/api/human/takeback")
async def human_takeback(request: TakebackRequest) -> dict[str, object]:
    """브라우저 사람의 되돌리기 요청 또는 응답을 처리한다."""
    try:
        return await manager.takeback("human", request.action)
    except GameError as error:
        _raise_game_error(error)


@app.post("/api/llm/takeback")
async def llm_takeback(request: TakebackRequest) -> dict[str, object]:
    """LLM의 되돌리기 요청 또는 응답을 처리한다."""
    try:
        return await manager.takeback("llm", request.action)
    except GameError as error:
        _raise_game_error(error)


@app.post("/api/human/resign")
async def human_resign() -> dict[str, object]:
    """브라우저 사람의 기권을 처리한다."""
    try:
        return await manager.resign("human")
    except GameError as error:
        _raise_game_error(error)


@app.post("/api/llm/resign")
async def llm_resign() -> dict[str, object]:
    """LLM의 기권을 처리한다."""
    try:
        return await manager.resign("llm")
    except GameError as error:
        _raise_game_error(error)


@app.post("/api/llm/wait")
async def llm_wait(request: WaitRequest | None = None) -> dict[str, object]:
    """LLM이 행동할 수 있는 상태까지 기다린다."""
    try:
        return await manager.wait_for_llm(request.after_revision if request is not None else None)
    except GameError as error:
        _raise_game_error(error)


@app.post("/api/players/{color}/moves")
async def player_moves(color: str, request: MoveRequest) -> dict[str, object]:
    """색상별 CLI 착수를 적용한다."""
    try:
        return await manager.player_move(color, request.move, request.wait)
    except GameError as error:
        _raise_game_error(error)


@app.post("/api/players/{color}/wait")
async def player_wait(color: str, request: WaitRequest | None = None) -> dict[str, object]:
    """색상별 CLI가 행동할 수 있는 상태까지 기다린다."""
    try:
        return await manager.wait_for_player(
            color,
            request.after_revision if request is not None else None,
        )
    except GameError as error:
        _raise_game_error(error)


@app.post("/api/players/{color}/takeback")
async def player_takeback(color: str, request: TakebackRequest) -> dict[str, object]:
    """색상별 CLI의 되돌리기 요청 또는 응답을 처리한다."""
    try:
        return await manager.player_takeback(color, request.action)
    except GameError as error:
        _raise_game_error(error)


@app.post("/api/players/{color}/resign")
async def player_resign(color: str) -> dict[str, object]:
    """색상별 CLI의 기권을 처리한다."""
    try:
        return await manager.player_resign(color)
    except GameError as error:
        _raise_game_error(error)


@app.get("/api/events")
async def events() -> StreamingResponse:
    """상태 변경을 서버 전송 이벤트로 브라우저에 보낸다."""

    async def stream():
        async for snapshot in manager.event_stream():
            payload = json.dumps(snapshot, ensure_ascii=False, separators=(",", ":"))
            yield f"data: {payload}\n\n"

    return StreamingResponse(
        stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


STATIC_DIR = Path(__file__).parent / "static"
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static-assets")
app.mount("/", StaticFiles(directory=STATIC_DIR, html=True), name="static")


__all__ = ["app", "manager"]
