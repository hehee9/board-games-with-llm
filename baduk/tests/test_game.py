import asyncio

import pytest

from llm_baduk.game import (
    ColorRequiredError,
    GameManager,
    IllegalMoveError,
    ScoreStateError,
    WrongTurnError,
)


@pytest.mark.asyncio
async def test_start_snapshot_and_turn_enforcement() -> None:
    manager = GameManager()
    initial = await manager.snapshot()
    assert initial["status"] == "setup"
    started = await manager.start_game("black", 9)
    assert started["status"] == "active"
    assert started["turn"] == "human"
    assert started["board_size"] == 9
    assert started["komi"] == 6.5
    assert len(started["legal_moves"]) == 82
    human = await manager.human_move("d4")
    assert human["last_move"] == {
        "ply": 1,
        "move": "D4",
        "color": "black",
        "actor": "human",
        "captured": [],
    }
    with pytest.raises(WrongTurnError):
        await manager.human_move("e4")
    llm = await manager.llm_move("d5", wait=False)
    assert llm["last_move"]["actor"] == "llm"


@pytest.mark.asyncio
async def test_wait_and_reset_wake_blocking_llm_operations() -> None:
    manager = GameManager()
    await manager.start_game("black")
    await manager.human_move("d4")
    waiting = asyncio.create_task(manager.wait_for_llm())
    await asyncio.sleep(0)
    result = await asyncio.wait_for(waiting, timeout=1)
    assert result["event"] == "human_move"
    await manager.llm_move("d5", wait=False)
    await manager.human_move("e4")
    blocking = asyncio.create_task(manager.llm_move("e5", wait=True))
    await asyncio.sleep(0)
    reset = await manager.start_game("black")
    assert reset["event"] == "game_reset"
    assert (await asyncio.wait_for(blocking, timeout=1))["event"] == "game_reset"


@pytest.mark.asyncio
async def test_takeback_acceptance_restores_board_and_reject_preserves_it() -> None:
    manager = GameManager()
    await manager.start_game("black")
    await manager.human_move("d4")
    await manager.llm_move("d5", wait=False)
    before = await manager.snapshot()
    pending = await manager.takeback("human", "request")
    assert pending["takeback"]["undone_plies"] == 2
    accepted = await manager.takeback("llm", "accept")
    assert accepted["stones"] == {}
    assert accepted["move_history"] == []
    assert accepted["takeback"]["state"] == "accepted"
    await manager.human_move("d4")
    await manager.llm_move("d5", wait=False)
    await manager.takeback("human", "request")
    rejected = await manager.takeback("llm", "reject")
    assert rejected["stones"] == before["stones"]
    assert rejected["takeback"]["state"] == "rejected"


@pytest.mark.asyncio
async def test_takeback_of_latest_llm_ply_restores_previous_position() -> None:
    manager = GameManager()
    await manager.start_game("black", 9)
    await manager.human_move("d4")
    await manager.llm_move("e4", wait=False)
    request = asyncio.create_task(manager.takeback("llm", "request"))
    await asyncio.sleep(0)
    accepted = await manager.takeback("human", "accept")
    await asyncio.wait_for(request, timeout=1)
    assert accepted["stones"] == {"D4": "black"}
    assert accepted["move_history"] == [
        {"ply": 1, "move": "D4", "color": "black", "actor": "human", "captured": []}
    ]
    assert accepted["to_play"] == "white"
    assert accepted["turn"] == "llm"


@pytest.mark.asyncio
async def test_takeback_reply_removes_requesters_move_and_reply() -> None:
    manager = GameManager()
    await manager.start_game("black", 9)
    await manager.human_move("d4")
    await manager.llm_move("e4", wait=False)
    await manager.takeback("human", "request")
    accepted = await manager.takeback("llm", "accept")
    assert accepted["stones"] == {}
    assert accepted["move_history"] == []
    assert accepted["to_play"] == "black"
    assert accepted["turn"] == "human"


@pytest.mark.asyncio
async def test_scoring_dead_seki_revision_and_resume() -> None:
    manager = GameManager()
    await manager.start_game("black", 9)
    await manager.human_move("d4")
    await manager.llm_move("e5", wait=False)
    await manager.human_move("pass")
    scoring = await manager.llm_move("pass", wait=False)
    assert scoring["status"] == "scoring"
    with pytest.raises(ScoreStateError) as missing:
        await manager.score("human", "accept")
    assert missing.value.code == "score_revision_required"
    marked = await manager.score("human", "dead", point="d4")
    assert marked["score"]["accepted"] == {"human": False, "llm": False}
    with pytest.raises(ScoreStateError) as stale:
        await manager.score("human", "accept", revision=marked["revision"] - 1)
    assert stale.value.code == "stale_revision"
    accepted = await manager.score("human", "accept", revision=marked["revision"])
    finished = await manager.score("llm", "accept", revision=accepted["revision"])
    assert finished["status"] == "finished"
    assert finished["score"]["accepted"] == {"human": True, "llm": True}
    manager = GameManager()
    await manager.start_game("black", 9)
    await manager.human_move("d4")
    await manager.llm_move("e5", wait=False)
    await manager.human_move("pass")
    await manager.llm_move("pass", wait=False)
    resumed = await manager.score("human", "resume")
    assert resumed["status"] == "active"
    assert resumed["score"] is None
    assert resumed["consecutive_passes"] == 0


@pytest.mark.asyncio
async def test_illegal_move_is_domain_error() -> None:
    manager = GameManager()
    await manager.start_game("black")
    await manager.human_move("d4")
    with pytest.raises(IllegalMoveError) as error:
        await manager.llm_move("d4", wait=False)
    assert error.value.code == "illegal_move"


@pytest.mark.asyncio
async def test_cli_vs_cli_uses_color_actors_and_rejects_legacy_paths() -> None:
    manager = GameManager()
    started = await manager.start_game(
        board_size=9,
        game_mode="cli_vs_cli",
        black_name="  ",
        white_name=" White CLI ",
    )
    assert started["players"] == {
        "black": {"actor": "black", "controller": "cli", "name": None},
        "white": {"actor": "white", "controller": "cli", "name": "White CLI"},
    }
    assert started["human_color"] is None
    assert started["llm_color"] is None
    assert started["turn"] == "black"
    black = await manager.player_move("black", "d4", wait=False)
    assert black["last_move"]["actor"] == "black"
    with pytest.raises(WrongTurnError):
        await manager.player_move("black", "e4", wait=False)
    white = await manager.player_move("white", "d5", wait=False)
    assert white["last_move"]["actor"] == "white"
    with pytest.raises(ColorRequiredError) as legacy:
        await manager.llm_move("e5", wait=False)
    assert legacy.value.code == "color_required"


@pytest.mark.asyncio
async def test_cli_wait_is_symmetric_and_reset_wakes_both_waiters() -> None:
    manager = GameManager()
    await manager.start_game(game_mode="cli_vs_cli", board_size=9)
    await manager.player_move("black", "d4", wait=False)
    white_wait = asyncio.create_task(manager.wait_for_player("white"))
    black_wait = asyncio.create_task(manager.wait_for_player("black"))
    assert (await asyncio.wait_for(white_wait, timeout=1))["turn"] == "white"
    await asyncio.sleep(0)
    assert not black_wait.done()
    await manager.player_move("white", "d5", wait=False)
    assert (await asyncio.wait_for(black_wait, timeout=1))["turn"] == "black"
    latest = await manager.player_move("black", "e4", wait=False)
    reset_black = asyncio.create_task(manager.wait_for_player("black", latest["revision"]))
    reset_white = asyncio.create_task(manager.wait_for_player("white", latest["revision"]))
    await asyncio.sleep(0)
    reset = await manager.start_game(game_mode="cli_vs_cli", board_size=9)
    assert reset["event"] == "game_reset"
    assert (await asyncio.wait_for(reset_black, timeout=1))["event"] == "game_reset"
    assert (await asyncio.wait_for(reset_white, timeout=1))["event"] == "game_reset"


@pytest.mark.asyncio
async def test_cli_takeback_blocks_both_request_directions() -> None:
    manager = GameManager()
    await manager.start_game(game_mode="cli_vs_cli", board_size=9)
    await manager.player_move("black", "d4", wait=False)
    await manager.player_move("white", "d5", wait=False)
    black_request = asyncio.create_task(manager.player_takeback("black", "request"))
    await asyncio.sleep(0)
    accepted = await manager.player_takeback("white", "accept")
    assert accepted["takeback"] == {
        "state": "accepted",
        "requester": "black",
        "target_ply": 1,
        "undone_plies": 2,
    }
    assert (await asyncio.wait_for(black_request, timeout=1))["event"] == "takeback_accepted"
    await manager.player_move("black", "d4", wait=False)
    await manager.player_move("white", "d5", wait=False)
    white_request = asyncio.create_task(manager.player_takeback("white", "request"))
    await asyncio.sleep(0)
    rejected = await manager.player_takeback("black", "reject")
    assert rejected["takeback"]["requester"] == "white"
    assert (await asyncio.wait_for(white_request, timeout=1))["event"] == "takeback_rejected"


@pytest.mark.asyncio
async def test_cli_scoring_revision_and_resign_wakes_waiter() -> None:
    manager = GameManager()
    await manager.start_game(game_mode="cli_vs_cli", board_size=9)
    await manager.player_move("black", "d4", wait=False)
    await manager.player_move("white", "e5", wait=False)
    await manager.player_move("black", "pass", wait=False)
    scoring = await manager.player_move("white", "pass", wait=False)
    assert scoring["status"] == "scoring"
    with pytest.raises(ScoreStateError) as missing:
        await manager.player_score("black", "dead", point="d4")
    assert missing.value.code == "score_revision_required"
    with pytest.raises(ScoreStateError) as stale:
        await manager.player_score("black", "dead", point="d4", revision=scoring["revision"] - 1)
    assert stale.value.code == "stale_revision"
    marked = await manager.player_score("black", "dead", point="d4", revision=scoring["revision"])
    assert marked["score"]["accepted"] == {"black": False, "white": False}
    accepted = await manager.player_score("black", "accept", revision=marked["revision"])
    with pytest.raises(ScoreStateError) as stale_accept:
        await manager.player_score("white", "accept", revision=marked["revision"])
    assert stale_accept.value.code == "stale_revision"
    finished = await manager.player_score("white", "accept", revision=accepted["revision"])
    assert finished["status"] == "finished"
    assert finished["score"]["accepted"] == {"black": True, "white": True}

    manager = GameManager()
    await manager.start_game(game_mode="cli_vs_cli", board_size=9)
    latest = await manager.player_move("black", "d4", wait=False)
    waiter = asyncio.create_task(manager.wait_for_player("white", latest["revision"]))
    await asyncio.sleep(0)
    resigned = await manager.player_resign("black")
    assert resigned["resigned_by"] == "black"
    assert (await asyncio.wait_for(waiter, timeout=1))["event"] == "black_resigned"
