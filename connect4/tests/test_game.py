import asyncio

import pytest

from llm_connect4.game import (
    ColorRequiredError,
    GameManager,
    GameOverError,
    IllegalMoveError,
    TakebackStateError,
    WrongTurnError,
)


@pytest.mark.asyncio
async def test_human_vs_llm_color_choice_and_invalid_move() -> None:
    manager = GameManager()
    started = await manager.start_game("yellow")
    assert started["turn"] == "llm"
    assert started["to_play"] == "red"
    with pytest.raises(WrongTurnError):
        await manager.human_move("4")
    with pytest.raises(IllegalMoveError):
        await manager.llm_move("9", wait=False)
    llm_move = await manager.llm_move("4", wait=False)
    assert llm_move["last_move"]["color"] == "red"
    human_move = await manager.human_move("4")
    assert human_move["last_move"]["color"] == "yellow"
    assert human_move["board"][4][3] == "yellow"


@pytest.mark.asyncio
async def test_cli_vs_cli_names_turn_validation_and_read_only_status() -> None:
    manager = GameManager()
    started = await manager.start_game(game_mode="cli_vs_cli", red_name=" Red CLI ", yellow_name=" ")
    assert started["players"]["red"]["name"] == "Red CLI"
    assert started["players"]["yellow"]["name"] is None
    assert started["to_play"] == "red"
    before = await manager.snapshot()
    with pytest.raises(WrongTurnError):
        await manager.player_move("yellow", "1", wait=False)
    red_move = await manager.player_move("red", "1", wait=False)
    assert red_move["event"] == "red_move"
    with pytest.raises(ColorRequiredError):
        await manager.llm_move("2", wait=False)
    assert int(before["revision"]) + 1 == red_move["revision"]


@pytest.mark.asyncio
async def test_color_wait_blocks_before_game_and_until_selected_turn() -> None:
    manager = GameManager()
    red_wait = asyncio.create_task(manager.wait_for_player("red"))
    yellow_wait = asyncio.create_task(manager.wait_for_player("yellow"))
    await asyncio.sleep(0)
    assert not red_wait.done() and not yellow_wait.done()
    started = await manager.start_game(game_mode="cli_vs_cli")
    assert (await asyncio.wait_for(red_wait, timeout=1))["event"] == "game_started"
    await asyncio.sleep(0)
    assert not yellow_wait.done()
    await manager.player_move("red", "4", wait=False)
    yellow_turn = await asyncio.wait_for(yellow_wait, timeout=1)
    assert yellow_turn["turn"] == "yellow"
    assert yellow_turn["revision"] > started["revision"]


@pytest.mark.asyncio
async def test_takeback_restores_requesters_exact_before_position_and_history() -> None:
    manager = GameManager()
    await manager.start_game(game_mode="cli_vs_cli")
    await manager.player_move("red", "1", wait=False)
    await manager.player_move("yellow", "2", wait=False)
    await manager.player_move("red", "3", wait=False)
    request = asyncio.create_task(manager.player_takeback("yellow", "request"))
    await asyncio.sleep(0)
    pending = await manager.snapshot()
    assert pending["takeback"] == {
        "state": "pending", "requester": "yellow", "target_ply": 2, "undone_plies": 2,
    }
    with pytest.raises(TakebackStateError) as blocked:
        await manager.player_move("red", "4", wait=False)
    assert blocked.value.code == "takeback_move_blocked"
    await manager.player_takeback("red", "accept")
    restored = await asyncio.wait_for(request, timeout=1)
    assert restored["event"] == "takeback_accepted"
    assert restored["board"][5][0] == "red"
    assert restored["board"][5][1] is None
    assert restored["board"][5][2] is None
    assert [move["move"] for move in restored["move_history"]] == [1]
    assert restored["last_move"]["color"] == "red"
    assert restored["to_play"] == "yellow"
    assert restored["legal_columns"] == [1, 2, 3, 4, 5, 6, 7]


@pytest.mark.asyncio
async def test_takeback_reject_preserves_board_and_both_moves_are_blocked() -> None:
    manager = GameManager()
    await manager.start_game("red")
    await manager.human_move("3")
    await manager.llm_move("4", wait=False)
    before = await manager.snapshot()
    await manager.takeback("human", "request")
    for action in (manager.human_move("2"), manager.llm_move("2", wait=False)):
        with pytest.raises(TakebackStateError):
            await action
    rejected = await manager.takeback("llm", "reject")
    assert rejected["board"] == before["board"]
    assert rejected["move_history"] == before["move_history"]
    assert rejected["to_play"] == before["to_play"]
    assert rejected["takeback"]["state"] == "rejected"


@pytest.mark.asyncio
async def test_takeback_request_wait_ends_on_accept_reset_or_resignation() -> None:
    manager = GameManager()
    await manager.start_game("red")
    await manager.human_move("1")
    await manager.llm_move("2", wait=False)
    request = asyncio.create_task(manager.takeback("llm", "request"))
    await asyncio.sleep(0)
    await manager.takeback("human", "accept")
    assert (await asyncio.wait_for(request, timeout=1))["event"] == "takeback_accepted"

    await manager.llm_move("2", wait=False)
    await manager.human_move("3")
    reset_request = asyncio.create_task(manager.takeback("llm", "request"))
    await asyncio.sleep(0)
    await manager.start_game("red")
    assert (await asyncio.wait_for(reset_request, timeout=1))["event"] == "game_reset"

    await manager.human_move("1")
    await manager.llm_move("2", wait=False)
    resign_request = asyncio.create_task(manager.takeback("llm", "request"))
    await asyncio.sleep(0)
    resigned = await manager.resign("human")
    assert resigned["status"] == "resigned"
    assert (await asyncio.wait_for(resign_request, timeout=1))["event"] == "human_resigned"


@pytest.mark.asyncio
async def test_blocking_move_waits_for_turn_and_reset_or_resignation_releases_it() -> None:
    manager = GameManager()
    await manager.start_game(game_mode="cli_vs_cli")
    blocking = asyncio.create_task(manager.player_move("red", "1", wait=True))
    await asyncio.sleep(0)
    assert not blocking.done()
    await manager.player_move("yellow", "2", wait=False)
    next_turn = await asyncio.wait_for(blocking, timeout=1)
    assert next_turn["turn"] == "red"

    blocking = asyncio.create_task(manager.player_move("red", "3", wait=True))
    await asyncio.sleep(0)
    reset = await manager.start_game(game_mode="cli_vs_cli")
    assert reset["event"] == "game_reset"
    assert (await asyncio.wait_for(blocking, timeout=1))["event"] == "game_reset"

    blocking = asyncio.create_task(manager.player_move("red", "3", wait=True))
    await asyncio.sleep(0)
    await manager.player_resign("yellow")
    assert (await asyncio.wait_for(blocking, timeout=1))["event"] == "yellow_resigned"


@pytest.mark.asyncio
async def test_win_and_draw_end_game() -> None:
    manager = GameManager()
    await manager.start_game("red")
    for column in (1, 1, 2, 2, 3, 3):
        await manager.human_move(str(column))
        await manager.llm_move(str(column), wait=False)
    won = await manager.human_move("4")
    assert won["status"] == "won"
    assert won["winner"] == "red"
    with pytest.raises(GameOverError):
        await manager.llm_move("4", wait=False)
