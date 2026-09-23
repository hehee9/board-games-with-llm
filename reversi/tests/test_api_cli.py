import asyncio

import httpx
import pytest

from llm_reversi import app as app_module
from llm_reversi.cli import render_snapshot
from llm_reversi.game import GameManager


@pytest.mark.asyncio
async def test_api_starts_game_applies_move_and_reports_domain_error(monkeypatch) -> None:
    monkeypatch.setattr(app_module, "manager", GameManager())
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app_module.app),
        base_url="http://test",
    ) as client:
        started = await client.post("/api/games", json={"human_color": "black"})
        assert started.status_code == 200
        assert started.json()["event"] == "game_started"

        illegal = await client.post("/api/human/moves", json={"move": "A1"})
        assert illegal.status_code == 422
        assert illegal.json()["detail"]["code"] == "illegal_move"

        moved = await client.post("/api/human/moves", json={"move": "D3"})
        assert moved.status_code == 200
        assert moved.json()["discs"]["D4"] == "black"


@pytest.mark.asyncio
async def test_cli_renders_reset_event_and_pending_takeback_fields() -> None:
    manager = GameManager()
    await manager.start_game(game_mode="cli_vs_cli")
    snapshot = await manager.player_move("black", "D3", wait=False)
    snapshot = await manager.player_move("white", snapshot["legal_moves"][0], wait=False)
    request = asyncio.create_task(manager.player_takeback("black", "request"))
    await asyncio.sleep(0)
    pending = await manager.snapshot()
    assert pending["event"] == "takeback_requested"
    accepted = await manager.player_takeback("white", "accept")
    response = await request
    assert response["event"] == "takeback_accepted"
    reset = await manager.start_game(game_mode="cli_vs_cli")

    reset_output = render_snapshot(reset)
    assert "**Event:** game_reset" in reset_output

    pending_output = render_snapshot(pending)
    assert "**Event:** takeback_requested" in pending_output
    assert "**Takeback:** pending · requester black · target ply 1 · 2 plies to undo" in pending_output

    accepted_output = render_snapshot(accepted)
    assert "**Event:** takeback_accepted" in accepted_output
    assert "**Takeback:** accepted · requester black · target ply 1 · 2 plies undone" in accepted_output
