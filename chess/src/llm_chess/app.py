"""FastAPI 서버와 로컬 체스 API."""

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
    """새 게임 모드와 참가자 설정 요청."""

    model_config = ConfigDict(extra="forbid")
    game_mode: Literal["human_vs_llm", "cli_vs_cli"] = "human_vs_llm"
    human_color: Literal["white", "black"] | None = None
    white_name: str | None = None
    black_name: str | None = None


class MoveRequest(BaseModel):
    """수 적용 요청."""

    model_config = ConfigDict(extra="forbid")
    move: str


class LlmMoveRequest(MoveRequest):
    """언어 모델 수 적용 요청."""

    wait: bool = True


class TakebackRequest(BaseModel):
    """되돌리기 동작 요청."""

    model_config = ConfigDict(extra="forbid")
    action: Literal["request", "accept", "reject"]


manager = GameManager()
app = FastAPI(title="llm-chess", version="0.3.0")


def _raise_game_error(error: GameError) -> None:
    raise HTTPException(status_code=error.status_code, detail=error.message) from error


@app.get("/api/health")
async def health() -> dict[str, str]:
    """서버가 이 앱인지 확인한다."""
    return {"app": "llm-chess", "status": "ok"}


@app.get("/api/state")
async def state() -> dict[str, object]:
    """현재 게임 스냅샷을 반환한다."""
    return await manager.snapshot()


@app.post("/api/games")
async def games(request: NewGameRequest) -> dict[str, object]:
    """게임을 시작하거나 현재 게임을 초기화한다."""
    try:
        return await manager.start_game(
            request.human_color,
            game_mode=request.game_mode,
            white_name=request.white_name,
            black_name=request.black_name,
        )
    except GameError as error:
        _raise_game_error(error)


@app.post("/api/human/moves")
async def human_moves(request: MoveRequest) -> dict[str, object]:
    """사람의 UCI 수를 적용한다."""
    try:
        return await manager.human_move(request.move)
    except GameError as error:
        _raise_game_error(error)


@app.post("/api/human/takeback")
async def human_takeback(request: TakebackRequest) -> dict[str, object]:
    """사람이 되돌리기를 요청하거나 언어 모델의 요청에 응답한다."""
    try:
        return await manager.takeback("human", request.action)
    except GameError as error:
        _raise_game_error(error)


@app.post("/api/llm/takeback")
async def llm_takeback(request: TakebackRequest) -> dict[str, object]:
    """언어 모델이 되돌리기를 요청하거나 사람의 요청에 응답한다."""
    try:
        return await manager.takeback("llm", request.action)
    except GameError as error:
        _raise_game_error(error)


@app.post("/api/human/resign")
async def human_resign() -> dict[str, object]:
    """사람의 사임으로 게임을 종료한다."""
    try:
        return await manager.resign("human")
    except GameError as error:
        _raise_game_error(error)


@app.post("/api/llm/resign")
async def llm_resign() -> dict[str, object]:
    """언어 모델의 사임으로 게임을 종료한다."""
    try:
        return await manager.resign("llm")
    except GameError as error:
        _raise_game_error(error)


@app.post("/api/llm/wait")
async def llm_wait() -> dict[str, object]:
    """언어 모델 차례 또는 종료 상태를 기다린다."""
    try:
        return await manager.wait_for_llm()
    except GameError as error:
        _raise_game_error(error)


@app.post("/api/llm/moves")
async def llm_moves(request: LlmMoveRequest) -> dict[str, object]:
    """언어 모델의 UCI 또는 SAN 수를 적용한다."""
    try:
        return await manager.llm_move(request.move, request.wait)
    except GameError as error:
        _raise_game_error(error)


@app.post("/api/players/{color}/moves")
async def player_moves(color: Literal["white", "black"], request: LlmMoveRequest) -> dict[str, object]:
    """CLI 색상 플레이어의 수를 적용한다."""
    try:
        return await manager.player_move(color, request.move, request.wait)
    except GameError as error:
        _raise_game_error(error)


@app.post("/api/players/{color}/wait")
async def player_wait(color: Literal["white", "black"]) -> dict[str, object]:
    """CLI 색상 플레이어의 차례나 종료 상태를 기다린다."""
    try:
        return await manager.wait_for_player(color)
    except GameError as error:
        _raise_game_error(error)


@app.post("/api/players/{color}/takeback")
async def player_takeback(
    color: Literal["white", "black"], request: TakebackRequest
) -> dict[str, object]:
    """CLI 색상 플레이어의 되돌리기 요청 또는 응답을 처리한다."""
    try:
        return await manager.player_takeback(color, request.action)
    except GameError as error:
        _raise_game_error(error)


@app.post("/api/players/{color}/resign")
async def player_resign(color: Literal["white", "black"]) -> dict[str, object]:
    """CLI 색상 플레이어의 사임을 처리한다."""
    try:
        return await manager.player_resign(color)
    except GameError as error:
        _raise_game_error(error)


@app.get("/api/events")
async def events() -> StreamingResponse:
    """브라우저에 상태 변경을 서버 전송 이벤트로 보낸다."""

    async def stream():
        async for snapshot in manager.event_stream():
            yield f"data: {json.dumps(snapshot, ensure_ascii=False, separators=(',', ':'))}\n\n"

    return StreamingResponse(stream(), media_type="text/event-stream")


STATIC_DIR = Path(__file__).parent / "static"
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static-assets")
app.mount("/", StaticFiles(directory=STATIC_DIR, html=True), name="static")
