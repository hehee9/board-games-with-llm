import asyncio

import httpx
import pytest

from llm_connect4.app import app, events, manager


@pytest.fixture(autouse=True)
def reset_manager() -> None:
    manager.__init__()


@pytest.mark.asyncio
async def test_game_api_and_invalid_move() -> None:
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        assert (await client.get("/api/health")).json() == {"app": "llm-connect4", "status": "ok"}
        assert (await client.get("/api/state")).json()["status"] == "setup"
        extra = await client.post("/api/games", json={"human_color": "red", "extra": True})
        assert extra.status_code == 422
        started = await client.post("/api/games", json={"human_color": "red"})
        assert started.status_code == 200
        assert started.json()["board"] == [[None] * 7 for _ in range(6)]
        invalid = await client.post("/api/human/moves", json={"move": "8"})
        assert invalid.status_code == 422
        assert invalid.json()["detail"]["code"] == "illegal_move"
        move = await client.post("/api/human/moves", json={"move": "4"})
        assert move.json()["last_move"]["column"] == 4
        assert move.json()["last_move"]["color"] == "red"


@pytest.mark.asyncio
async def test_invalid_player_wait_color_is_rejected_before_game_starts() -> None:
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        response = await asyncio.wait_for(client.post("/api/players/invalid/wait"), timeout=1)
        assert response.status_code == 422
        assert response.json()["detail"]["code"] == "invalid_color"


@pytest.mark.asyncio
async def test_cli_player_waits_before_game_until_selected_color_is_actionable() -> None:
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        yellow_wait = asyncio.create_task(client.post("/api/players/yellow/wait"))
        await asyncio.sleep(0)
        started = await client.post("/api/games", json={"game_mode": "cli_vs_cli"})
        await asyncio.sleep(0)
        assert not yellow_wait.done()
        await client.post("/api/players/red/moves", json={"move": "4", "wait": False})
        yellow = await asyncio.wait_for(yellow_wait, timeout=1)
        assert yellow.json()["turn"] == "yellow"
        assert yellow.json()["revision"] > started.json()["revision"]


@pytest.mark.asyncio
async def test_takeback_accept_and_terminal_wait_api() -> None:
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        await client.post("/api/games", json={"game_mode": "cli_vs_cli"})
        await client.post("/api/players/red/moves", json={"move": "1", "wait": False})
        await client.post("/api/players/yellow/moves", json={"move": "2", "wait": False})
        await client.post("/api/players/red/moves", json={"move": "3", "wait": False})
        waiting = asyncio.create_task(client.post("/api/players/red/wait"))
        await asyncio.sleep(0)
        request = asyncio.create_task(client.post("/api/players/yellow/takeback", json={"action": "request"}))
        pending = await asyncio.wait_for(waiting, timeout=1)
        assert pending.json()["takeback"]["state"] == "pending"
        taken = await client.post("/api/players/red/takeback", json={"action": "accept"})
        assert taken.json()["event"] == "takeback_accepted"
        assert [move["move"] for move in taken.json()["move_history"]] == [1]
        assert (await asyncio.wait_for(request, timeout=1)).json()["event"] == "takeback_accepted"

        await client.post("/api/players/yellow/moves", json={"move": "2", "wait": False})
        blocking_move = asyncio.create_task(client.post("/api/players/red/moves", json={"move": "1", "wait": True}))
        await asyncio.sleep(0)
        resigned = await client.post("/api/players/yellow/resign")
        assert resigned.json()["status"] == "resigned"
        assert (await asyncio.wait_for(blocking_move, timeout=1)).json()["event"] == "yellow_resigned"


@pytest.mark.asyncio
async def test_events_stream_sends_snapshot_updates() -> None:
    response = await events()
    assert response.media_type == "text/event-stream"
