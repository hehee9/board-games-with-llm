"""FastAPI 서버와 Connect Four 웹 화면."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Literal

from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, ConfigDict

from .game import GameError, GameManager
from .rules import Color


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class NewGameRequest(StrictModel):
    game_mode: Literal["human_vs_llm", "cli_vs_cli"] = "human_vs_llm"
    human_color: Color | None = "red"
    red_name: str | None = None
    yellow_name: str | None = None


class MoveRequest(StrictModel):
    move: str


class LlmMoveRequest(MoveRequest):
    wait: bool = True


class PlayerMoveRequest(MoveRequest):
    wait: bool = True


class TakebackRequest(StrictModel):
    action: Literal["request", "accept", "reject"]


class WaitRequest(StrictModel):
    after_revision: int | None = None


manager = GameManager()
app = FastAPI(title="LLM Connect Four", version="0.1.0")
static_dir = Path(__file__).parent / "static"
app.mount("/static", StaticFiles(directory=static_dir), name="static")


@app.exception_handler(GameError)
async def game_error_handler(_: Request, exc: GameError) -> JSONResponse:
    return JSONResponse(status_code=exc.status_code, content={"detail": {"code": exc.code, "message": exc.message}})


@app.get("/")
async def index() -> FileResponse:
    return FileResponse(static_dir / "index.html")


@app.get("/api/health")
async def health() -> dict[str, str]:
    return {"app": "llm-connect4", "status": "ok"}


@app.get("/api/state")
async def state() -> dict[str, object]:
    return await manager.snapshot()


@app.post("/api/games")
async def start_game(body: NewGameRequest) -> dict[str, object]:
    return await manager.start_game(body.human_color, game_mode=body.game_mode, red_name=body.red_name, yellow_name=body.yellow_name)


@app.post("/api/human/moves")
async def human_move(body: MoveRequest) -> dict[str, object]:
    return await manager.human_move(body.move)


@app.post("/api/llm/moves")
async def llm_move(body: LlmMoveRequest) -> dict[str, object]:
    return await manager.llm_move(body.move, wait=body.wait)


@app.post("/api/llm/wait")
async def wait_for_llm(body: WaitRequest) -> dict[str, object]:
    return await manager.wait_for_llm(body.after_revision)


@app.post("/api/llm/takeback")
async def llm_takeback(body: TakebackRequest) -> dict[str, object]:
    return await manager.takeback("llm", body.action)


@app.post("/api/llm/resign")
async def llm_resign() -> dict[str, object]:
    return await manager.resign("llm")


@app.post("/api/human/takeback")
async def human_takeback(body: TakebackRequest) -> dict[str, object]:
    return await manager.takeback("human", body.action)


@app.post("/api/human/resign")
async def human_resign() -> dict[str, object]:
    return await manager.resign("human")


@app.post("/api/players/{color}/moves")
async def player_move(color: str, body: PlayerMoveRequest) -> dict[str, object]:
    return await manager.player_move(color, body.move, wait=body.wait)


@app.post("/api/players/{color}/wait")
async def wait_for_player(color: str) -> dict[str, object]:
    return await manager.wait_for_player(color)


@app.post("/api/players/{color}/takeback")
async def player_takeback(color: str, body: TakebackRequest) -> dict[str, object]:
    return await manager.player_takeback(color, body.action)


@app.post("/api/players/{color}/resign")
async def player_resign(color: str) -> dict[str, object]:
    return await manager.player_resign(color)


@app.get("/api/events")
async def events() -> StreamingResponse:
    async def stream():
        async for snapshot in manager.event_stream():
            yield f"id: {snapshot['revision']}\nevent: state\ndata: {json.dumps(snapshot, separators=(',', ':'))}\n\n"

    return StreamingResponse(stream(), media_type="text/event-stream", headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})


__all__ = ["app", "events", "manager"]
