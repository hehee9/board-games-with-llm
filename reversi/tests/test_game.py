import asyncio

import pytest

from llm_reversi.game import GameManager


@pytest.mark.asyncio
async def test_wait_for_player_returns_current_actionable_initial_turn() -> None:
    manager = GameManager()
    started = await manager.start_game(game_mode="cli_vs_cli")

    snapshot = await asyncio.wait_for(manager.wait_for_player("black"), timeout=1)

    assert snapshot["revision"] == started["revision"]
    assert snapshot["event"] == "game_started"
    assert snapshot["turn"] == "black"


@pytest.mark.asyncio
async def test_wait_for_player_returns_same_side_after_automatic_pass() -> None:
    manager = GameManager()
    snapshot = await manager.start_game(game_mode="cli_vs_cli")

    while snapshot["status"] == "active" and snapshot["auto_passed_color"] is None:
        color = snapshot["turn"]
        snapshot = await manager.player_move(color, snapshot["legal_moves"][0], wait=False)

    assert snapshot["status"] == "active"
    assert snapshot["auto_passed_color"] is not None
    waited = await asyncio.wait_for(manager.wait_for_player(snapshot["turn"]), timeout=1)

    assert waited["revision"] == snapshot["revision"]
    assert waited["turn"] == snapshot["turn"]
    assert waited["auto_passed_color"] == snapshot["auto_passed_color"]


@pytest.mark.asyncio
async def test_first_legal_moves_finish_game_after_automatic_passes() -> None:
    manager = GameManager()
    snapshot = await manager.start_game(game_mode="cli_vs_cli")
    saw_automatic_pass = False

    while snapshot["status"] == "active":
        color = snapshot["turn"]
        snapshot = await manager.player_move(color, snapshot["legal_moves"][0], wait=False)
        saw_automatic_pass |= snapshot["event"] == "automatic_pass"

    assert saw_automatic_pass
    assert snapshot["event"] == "game_finished"
    assert snapshot["status"] == "finished"
    assert snapshot["turn"] is None
    assert sum(snapshot["counts"].values()) == 64
    counts = snapshot["counts"]
    expected_result = (
        "Draw"
        if counts["black"] == counts["white"]
        else "black"
        if counts["black"] > counts["white"]
        else "white"
    )
    assert snapshot["result"] == expected_result


@pytest.mark.asyncio
async def test_takeback_restores_position_before_last_move_after_automatic_pass() -> None:
    manager = GameManager()
    snapshot = await manager.start_game(game_mode="cli_vs_cli")

    while snapshot["status"] == "active" and snapshot["auto_passed_color"] is None:
        color = snapshot["turn"]
        snapshot = await manager.player_move(color, snapshot["legal_moves"][0], wait=False)

    assert snapshot["status"] == "active"
    assert snapshot["auto_passed_color"] is not None
    before_last_move = snapshot
    requester = snapshot["turn"]
    snapshot = await manager.player_move(requester, snapshot["legal_moves"][0], wait=False)
    assert len(snapshot["move_history"]) == len(before_last_move["move_history"]) + 1

    request = asyncio.create_task(manager.player_takeback(requester, "request"))
    await asyncio.sleep(0)
    pending = await manager.snapshot()
    assert pending["takeback"]["state"] == "pending"
    snapshot = await manager.player_takeback(
        "white" if requester == "black" else "black", "accept"
    )
    await request

    assert snapshot["event"] == "takeback_accepted"
    assert snapshot["discs"] == before_last_move["discs"]
    assert snapshot["to_play"] == before_last_move["to_play"]
    assert snapshot["turn"] == before_last_move["turn"]
    assert snapshot["auto_passed_color"] == before_last_move["auto_passed_color"]
    assert snapshot["move_history"] == before_last_move["move_history"]
    assert snapshot["takeback"]["moves_to_undo"] == 1
