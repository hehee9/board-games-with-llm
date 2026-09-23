"""FastAPI 서버와 로컬 바둑 API."""

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
    """새 게임 설정 요청."""

    model_config = ConfigDict(extra="forbid", strict=True)

    game_mode: Literal["human_vs_llm", "cli_vs_cli"] = "human_vs_llm"
    human_color: Literal["black", "white"] | None = None
    board_size: Literal[9, 13, 19] = 19
    black_name: str | None = None
    white_name: str | None = None


class MoveRequest(BaseModel):
    """수 요청."""

    model_config = ConfigDict(extra="forbid", strict=True)

    move: str


class LlmMoveRequest(MoveRequest):
    """수 적용과 대기 설정 요청."""

    wait: bool = True


class TakebackRequest(BaseModel):
    """되돌리기 요청."""

    model_config = ConfigDict(extra="forbid", strict=True)

    action: Literal["request", "accept", "reject"]


class ScoreRequest(BaseModel):
    """수읽기 종료 후 점수 처리 요청."""

    model_config = ConfigDict(extra="forbid", strict=True)

    action: Literal["dead", "seki", "accept", "resume"]
    point: str | None = None
    revision: int | None = None


class WaitRequest(BaseModel):
    """상태 대기용 revision 커서."""

    model_config = ConfigDict(extra="forbid", strict=True)

    after_revision: int | None = None


manager = GameManager()
app = FastAPI(title="llm-baduk", version="0.1.1")


def _raise_game_error(error: GameError) -> None:
    """게임 오류를 계약된 HTTP 오류로 변환."""
    raise HTTPException(
        status_code=error.status_code,
        detail={"code": error.code, "message": error.message},
    ) from error


@app.get("/api/health")
async def health() -> dict[str, str]:
    """서버 상태 반환."""
    return {"app": "llm-baduk", "status": "ok"}


@app.get("/api/state")
async def state() -> dict[str, object]:
    """현재 게임 스냅샷 반환."""
    return await manager.snapshot()


@app.post("/api/games")
async def games(request: NewGameRequest) -> dict[str, object]:
    """게임 시작 또는 초기화."""
    try:
        return await manager.start_game(
            request.human_color,
            request.board_size,
            game_mode=request.game_mode,
            black_name=request.black_name,
            white_name=request.white_name,
        )
    except GameError as error:
        _raise_game_error(error)


@app.post("/api/human/moves")
async def human_moves(request: MoveRequest) -> dict[str, object]:
    """사람 수 적용."""
    try:
        return await manager.human_move(request.move)
    except GameError as error:
        _raise_game_error(error)


@app.post("/api/llm/moves")
async def llm_moves(request: LlmMoveRequest) -> dict[str, object]:
    """LLM 수 적용."""
    try:
        return await manager.llm_move(request.move, request.wait)
    except GameError as error:
        _raise_game_error(error)


@app.post("/api/human/takeback")
async def human_takeback(request: TakebackRequest) -> dict[str, object]:
    """사람 되돌리기 요청 또는 LLM 요청 응답."""
    try:
        return await manager.takeback("human", request.action)
    except GameError as error:
        _raise_game_error(error)


@app.post("/api/llm/takeback")
async def llm_takeback(request: TakebackRequest) -> dict[str, object]:
    """LLM 되돌리기 요청 또는 사람 요청 응답."""
    try:
        return await manager.takeback("llm", request.action)
    except GameError as error:
        _raise_game_error(error)


@app.post("/api/human/resign")
async def human_resign() -> dict[str, object]:
    """사람 사임 처리."""
    try:
        return await manager.resign("human")
    except GameError as error:
        _raise_game_error(error)


@app.post("/api/llm/resign")
async def llm_resign() -> dict[str, object]:
    """LLM 사임 처리."""
    try:
        return await manager.resign("llm")
    except GameError as error:
        _raise_game_error(error)


@app.post("/api/human/score")
async def human_score(request: ScoreRequest) -> dict[str, object]:
    """사람 점수 표시 또는 합의 처리."""
    try:
        return await manager.score("human", request.action, request.point, request.revision)
    except GameError as error:
        _raise_game_error(error)


@app.post("/api/llm/score")
async def llm_score(request: ScoreRequest) -> dict[str, object]:
    """LLM 점수 표시 또는 합의 처리."""
    try:
        return await manager.score("llm", request.action, request.point, request.revision)
    except GameError as error:
        _raise_game_error(error)


@app.post("/api/llm/wait")
async def llm_wait(request: WaitRequest | None = None) -> dict[str, object]:
    """LLM에게 의미 있는 새 상태를 반환."""
    try:
        return await manager.wait_for_llm(request.after_revision if request is not None else None)
    except GameError as error:
        _raise_game_error(error)


@app.post("/api/players/{color}/moves")
async def player_moves(color: str, request: LlmMoveRequest) -> dict[str, object]:
    """CLI 색상 플레이어의 수 적용."""
    try:
        return await manager.player_move(color, request.move, request.wait)
    except GameError as error:
        _raise_game_error(error)


@app.post("/api/players/{color}/wait")
async def player_wait(color: str, request: WaitRequest | None = None) -> dict[str, object]:
    """CLI 색상 플레이어의 의미 있는 상태 대기."""
    try:
        return await manager.wait_for_player(color, request.after_revision if request is not None else None)
    except GameError as error:
        _raise_game_error(error)


@app.post("/api/players/{color}/takeback")
async def player_takeback(color: str, request: TakebackRequest) -> dict[str, object]:
    """CLI 색상 플레이어의 되돌리기 요청 또는 응답."""
    try:
        return await manager.player_takeback(color, request.action)
    except GameError as error:
        _raise_game_error(error)


@app.post("/api/players/{color}/resign")
async def player_resign(color: str) -> dict[str, object]:
    """CLI 색상 플레이어의 사임 처리."""
    try:
        return await manager.player_resign(color)
    except GameError as error:
        _raise_game_error(error)


@app.post("/api/players/{color}/score")
async def player_score(color: str, request: ScoreRequest) -> dict[str, object]:
    """CLI 색상 플레이어의 계가 동작 처리."""
    try:
        return await manager.player_score(color, request.action, request.point, request.revision)
    except GameError as error:
        _raise_game_error(error)


@app.get("/api/events")
async def events() -> StreamingResponse:
    """브라우저에 상태 변경을 서버 전송 이벤트로 전송."""

    async def stream():
        async for snapshot in manager.event_stream():
            yield f"data: {json.dumps(snapshot, ensure_ascii=False, separators=(',', ':'))}\n\n"

    return StreamingResponse(stream(), media_type="text/event-stream")


STATIC_DIR = Path(__file__).parent / "static"
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static-assets")
app.mount("/", StaticFiles(directory=STATIC_DIR, html=True), name="static")


__all__ = ["app", "manager"]
