import asyncio

import httpx
import pytest

from llm_baduk.app import app, events, manager


@pytest.fixture(autouse=True)
def reset_manager() -> None:
    manager.__init__()


@pytest.mark.asyncio
async def test_health_state_and_strict_game_api() -> None:
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        health = await client.get("/api/health")
        assert health.json() == {"app": "llm-baduk", "status": "ok"}
        assert app.version == "0.1.0"
        state = await client.get("/api/state")
        assert state.json()["status"] == "setup"
        extra = await client.post("/api/games", json={"human_color": "black", "extra": True})
        assert extra.status_code == 422
        started = await client.post("/api/games", json={"human_color": "black", "board_size": 9})
        assert started.status_code == 200
        move = await client.post("/api/human/moves", json={"move": "d4"})
        assert move.json()["last_move"]["move"] == "D4"
        wrong_turn = await client.post("/api/human/moves", json={"move": "e4"})
        assert wrong_turn.status_code == 409
        assert wrong_turn.json()["detail"]["code"] == "wrong_turn"


@pytest.mark.asyncio
async def test_api_scoring_revision_and_takeback() -> None:
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        await client.post("/api/games", json={"human_color": "black", "board_size": 9})
        await client.post("/api/human/moves", json={"move": "pass"})
        await client.post("/api/llm/moves", json={"move": "pass", "wait": False})
        missing = await client.post("/api/human/score", json={"action": "accept"})
        assert missing.status_code == 422
        assert missing.json()["detail"]["code"] == "score_revision_required"
        current = await client.get("/api/state")
        accepted = await client.post(
            "/api/human/score",
            json={"action": "accept", "revision": current.json()["revision"]},
        )
        assert accepted.status_code == 200
        stale = await client.post(
            "/api/llm/score",
            json={"action": "accept", "revision": current.json()["revision"]},
        )
        assert stale.status_code == 409
        assert stale.json()["detail"]["code"] == "stale_revision"


@pytest.mark.asyncio
async def test_wait_request_cursor_and_sse_initial_snapshot() -> None:
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        initial = await client.get("/api/state")
        await client.post("/api/games", json={"human_color": "black"})
        waiting = asyncio.create_task(client.post("/api/llm/wait", json={"after_revision": 1}))
        await asyncio.sleep(0)
        await client.post("/api/human/moves", json={"move": "d4"})
        result = await asyncio.wait_for(waiting, timeout=1)
        assert result.json()["event"] == "human_move"
        assert result.json()["revision"] > initial.json()["revision"]
        response = await events()
        assert response.media_type == "text/event-stream"


@pytest.mark.asyncio
async def test_cli_player_endpoints_and_legacy_mode_error() -> None:
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        started = await client.post(
            "/api/games",
            json={
                "game_mode": "cli_vs_cli",
                "board_size": 9,
                "black_name": "  ",
                "white_name": " White CLI ",
            },
        )
        assert started.status_code == 200
        snapshot = started.json()
        assert snapshot["players"] == {
            "black": {"actor": "black", "controller": "cli", "name": None},
            "white": {"actor": "white", "controller": "cli", "name": "White CLI"},
        }
        legacy = await client.post("/api/llm/moves", json={"move": "d4", "wait": False})
        assert legacy.status_code == 409
        assert legacy.json()["detail"]["code"] == "color_required"
        legacy_human = await client.post("/api/human/moves", json={"move": "d4"})
        assert legacy_human.status_code == 409
        assert legacy_human.json()["detail"]["code"] == "color_required"
        invalid = await client.post("/api/players/green/moves", json={"move": "d4", "wait": False})
        assert invalid.status_code == 422
        assert invalid.json()["detail"]["code"] == "invalid_color"
        black = await client.post("/api/players/black/moves", json={"move": "d4", "wait": False})
        assert black.status_code == 200
        assert black.json()["last_move"]["actor"] == "black"
        white = await client.post("/api/players/white/moves", json={"move": "d5", "wait": False})
        assert white.status_code == 200
        assert white.json()["last_move"]["actor"] == "white"
        await client.post("/api/games", json={"human_color": "black"})
        not_cli = await client.post("/api/players/black/moves", json={"move": "d4", "wait": False})
        assert not_cli.status_code == 409
        assert not_cli.json()["detail"]["code"] == "player_not_cli"
        await client.post("/api/human/moves", json={"move": "d4"})
        llm_color = await client.post("/api/players/white/moves", json={"move": "d5", "wait": False})
        assert llm_color.status_code == 200
        assert llm_color.json()["last_move"]["actor"] == "llm"


@pytest.mark.asyncio
async def test_cli_player_score_revision_and_terminal_wait_api() -> None:
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        await client.post("/api/games", json={"game_mode": "cli_vs_cli", "board_size": 9})
        await client.post("/api/players/black/moves", json={"move": "d4", "wait": False})
        await client.post("/api/players/white/moves", json={"move": "e5", "wait": False})
        await client.post("/api/players/black/moves", json={"move": "pass", "wait": False})
        scoring = await client.post("/api/players/white/moves", json={"move": "pass", "wait": False})
        assert scoring.json()["status"] == "scoring"
        missing = await client.post("/api/players/black/score", json={"action": "dead", "point": "d4"})
        assert missing.status_code == 422
        assert missing.json()["detail"]["code"] == "score_revision_required"
        stale = await client.post(
            "/api/players/black/score",
            json={"action": "dead", "point": "d4", "revision": scoring.json()["revision"] - 1},
        )
        assert stale.status_code == 409
        assert stale.json()["detail"]["code"] == "stale_revision"
        marked = await client.post(
            "/api/players/black/score",
            json={"action": "dead", "point": "d4", "revision": scoring.json()["revision"]},
        )
        assert marked.status_code == 200
        revision = marked.json()["revision"]
        accepted = await client.post(
            "/api/players/black/score",
            json={"action": "accept", "revision": revision},
        )
        assert accepted.status_code == 200
        finished = await client.post(
            "/api/players/white/score",
            json={"action": "accept", "revision": accepted.json()["revision"]},
        )
        assert finished.status_code == 200
        assert finished.json()["resigned_by"] is None

        await client.post("/api/games", json={"game_mode": "cli_vs_cli", "board_size": 9})
        latest = await client.post("/api/players/black/moves", json={"move": "d4", "wait": False})
        waiting = asyncio.create_task(
            client.post("/api/players/white/wait", json={"after_revision": latest.json()["revision"]})
        )
        await asyncio.sleep(0)
        resigned = await client.post("/api/players/black/resign")
        assert resigned.json()["resigned_by"] == "black"
        assert (await asyncio.wait_for(waiting, timeout=1)).json()["event"] == "black_resigned"
