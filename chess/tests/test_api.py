import asyncio

import httpx
import pytest

from llm_chess.app import app, manager


@pytest.fixture(autouse=True)
def reset_manager() -> None:
    manager._condition = asyncio.Condition()
    manager._board = None
    manager._game_id = None
    manager._game_mode = "human_vs_llm"
    manager._human_color = None
    manager._llm_color = None
    manager._players = {}
    manager._move_history = []
    manager._last_move = None
    manager._takeback = None
    manager._resigned_by = None
    manager._revision = 0
    manager._event = "setup"
    manager._published = [manager._snapshot_unlocked()]


@pytest.mark.asyncio
async def test_api_game_flow_and_errors() -> None:
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        health = await client.get("/api/health")
        assert health.json()["app"] == "llm-chess"
        assert app.version == "0.3.0"
        state = await client.get("/api/state")
        assert state.json()["status"] == "setup"
        assert state.json()["game_mode"] == "human_vs_llm"
        assert state.json()["players"] == {}
        no_game = await client.post("/api/human/moves", json={"move": "e2e4"})
        assert no_game.status_code == 409
        started = await client.post("/api/games", json={"human_color": "white"})
        assert started.status_code == 200
        human = await client.post("/api/human/moves", json={"move": "e2e4"})
        assert human.json()["last_move"]["uci"] == "e2e4"
        wrong_turn = await client.post("/api/human/moves", json={"move": "d2d4"})
        assert wrong_turn.status_code == 409
        llm = await client.post("/api/llm/moves", json={"move": "e5", "wait": False})
        assert llm.json()["last_move"]["san"] == "e5"
        assert llm.json()["turn"] == "human"


@pytest.mark.asyncio
async def test_llm_wait_starts_after_human_move() -> None:
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        waiter = asyncio.create_task(client.post("/api/llm/wait"))
        await asyncio.sleep(0)
        await client.post("/api/games", json={"human_color": "white"})
        await client.post("/api/human/moves", json={"move": "e2e4"})
        response = await asyncio.wait_for(waiter, timeout=1)
        assert response.json()["event"] == "human_move"


@pytest.mark.asyncio
async def test_sse_source_starts_with_snapshot() -> None:
    from llm_chess.app import manager

    stream = manager.event_stream()
    first = await anext(stream)
    await stream.aclose()
    assert first["event"] == "setup"


@pytest.mark.asyncio
async def test_takeback_api_is_strict_and_supports_acceptance() -> None:
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        await client.post("/api/games", json={"human_color": "white"})
        no_move = await client.post("/api/human/takeback", json={"action": "request"})
        assert no_move.status_code == 409
        await client.post("/api/human/moves", json={"move": "e2e4"})
        pending = await client.post("/api/human/takeback", json={"action": "request"})
        assert pending.status_code == 200
        assert pending.json()["event"] == "takeback_requested"
        extra = await client.post(
            "/api/llm/takeback",
            json={"action": "accept", "extra": True},
        )
        assert extra.status_code == 422
        accepted = await client.post("/api/llm/takeback", json={"action": "accept"})
        assert accepted.status_code == 200
        assert accepted.json()["takeback"]["state"] == "accepted"
        assert accepted.json()["move_history"] == []


@pytest.mark.asyncio
async def test_llm_takeback_blocks_until_human_response_and_resign_is_terminal() -> None:
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        await client.post("/api/games", json={"human_color": "white"})
        await client.post("/api/human/moves", json={"move": "e2e4"})
        await client.post("/api/llm/moves", json={"move": "e7e5", "wait": False})
        waiting = asyncio.create_task(
            client.post("/api/llm/takeback", json={"action": "request"})
        )
        await asyncio.sleep(0)
        state = await client.get("/api/state")
        assert state.json()["takeback"]["state"] == "pending"
        resigned = await client.post("/api/human/resign")
        assert resigned.status_code == 200
        assert resigned.json()["status"] == "resigned"
        result = await asyncio.wait_for(waiting, timeout=1)
        assert result.json()["event"] == "human_resigned"
        assert result.json()["resigned_by"] == "human"
        assert result.json()["result"] == "0-1"
        terminal_request = await client.post("/api/llm/resign")
        assert terminal_request.status_code == 409


@pytest.mark.asyncio
async def test_game_setup_modes_names_and_required_human_color() -> None:
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        missing_color = await client.post("/api/games", json={})
        assert missing_color.status_code == 422
        assert missing_color.json()["detail"] == "Human color is required in human-vs-LLM mode."

        started = await client.post(
            "/api/games",
            json={"game_mode": "cli_vs_cli", "white_name": " White Bot ", "black_name": "  "},
        )
        assert started.status_code == 200
        assert started.json()["turn"] == "white"
        assert started.json()["players"] == {
            "white": {"actor": "white", "controller": "cli", "name": "White Bot"},
            "black": {"actor": "black", "controller": "cli", "name": None},
        }


@pytest.mark.asyncio
async def test_player_routes_authorize_cli_colors_and_old_routes_reject_cli_mode() -> None:
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        await client.post("/api/games", json={"human_color": "black"})
        wrong_controller = await client.post("/api/players/black/wait")
        assert wrong_controller.status_code == 409
        assert wrong_controller.json()["detail"] == "Player black is not controlled by CLI."

        cli_move = await client.post(
            "/api/players/white/moves", json={"move": "e2e4", "wait": False}
        )
        assert cli_move.status_code == 200
        assert cli_move.json()["event"] == "white_move"
        assert cli_move.json()["move_history"][0]["actor"] == "llm"

        await client.post("/api/games", json={"game_mode": "cli_vs_cli"})
        old_routes = [
            ("/api/human/moves", {"move": "e2e4"}),
            ("/api/llm/moves", {"move": "e2e4", "wait": False}),
            ("/api/human/takeback", {"action": "request"}),
            ("/api/llm/takeback", {"action": "request"}),
            ("/api/human/resign", None),
            ("/api/llm/resign", None),
            ("/api/llm/wait", None),
        ]
        for path, body in old_routes:
            response = await client.post(path, json=body) if body is not None else await client.post(path)
            assert response.status_code == 409
            assert response.json()["detail"] == "CLI-vs-CLI games require --color white or --color black."

        wrong_turn = await client.post(
            "/api/players/black/moves", json={"move": "e7e5", "wait": False}
        )
        assert wrong_turn.status_code == 409
        assert wrong_turn.json()["detail"] == "It is not black's turn."
        invalid_color = await client.post("/api/players/red/wait")
        assert invalid_color.status_code == 422


@pytest.mark.asyncio
async def test_player_wait_can_start_during_setup_without_payload() -> None:
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        waiter = asyncio.create_task(client.post("/api/players/white/wait"))
        await asyncio.sleep(0)
        await client.post("/api/games", json={"game_mode": "cli_vs_cli"})
        ready = await asyncio.wait_for(waiter, timeout=1)
        assert ready.status_code == 200
        assert ready.json()["event"] == "game_started"
        assert ready.json()["turn"] == "white"


@pytest.mark.asyncio
async def test_legacy_wait_started_in_setup_rejects_cli_game_after_start() -> None:
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        waiter = asyncio.create_task(client.post("/api/llm/wait"))
        await asyncio.sleep(0)
        await client.post("/api/games", json={"game_mode": "cli_vs_cli"})

        response = await asyncio.wait_for(waiter, timeout=1)
        assert response.status_code == 409
        assert response.json()["detail"] == "CLI-vs-CLI games require --color white or --color black."


@pytest.mark.asyncio
async def test_player_takeback_wait_and_both_color_resign_routes() -> None:
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        await client.post("/api/games", json={"game_mode": "cli_vs_cli"})
        await client.post("/api/players/white/moves", json={"move": "e2e4", "wait": False})
        await client.post("/api/players/black/moves", json={"move": "e7e5", "wait": False})
        request = asyncio.create_task(
            client.post("/api/players/white/takeback", json={"action": "request"})
        )
        await asyncio.sleep(0)
        assert not request.done()
        pending = await client.get("/api/state")
        assert pending.json()["takeback"]["requester"] == "white"
        accepted = await client.post("/api/players/black/takeback", json={"action": "accept"})
        response = await asyncio.wait_for(request, timeout=1)
        assert accepted.json()["takeback"]["undone_plies"] == 2
        assert response.json()["event"] == "takeback_accepted"

        white_resigned = await client.post("/api/players/white/resign")
        assert white_resigned.json()["event"] == "white_resigned"
        assert white_resigned.json()["resigned_by"] == "white"
        await client.post("/api/games", json={"game_mode": "cli_vs_cli"})
        black_resigned = await client.post("/api/players/black/resign")
        assert black_resigned.json()["event"] == "black_resigned"
        assert black_resigned.json()["resigned_by"] == "black"
