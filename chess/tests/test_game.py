import asyncio

import chess
import pytest

from llm_chess.game import (
    GameManager,
    GameOverError,
    IllegalMoveError,
    TakebackStateError,
    WrongTurnError,
)


@pytest.mark.asyncio
async def test_game_snapshot_and_turn_enforcement() -> None:
    manager = GameManager()

    initial = await manager.snapshot()
    assert initial["status"] == "setup"
    assert initial["game_mode"] == "human_vs_llm"
    assert initial["players"] == {}
    started = await manager.start_game("white")
    assert started["status"] == "active"
    assert started["turn"] == "human"
    assert started["players"] == {
        "white": {"actor": "human", "controller": "human", "name": None},
        "black": {"actor": "llm", "controller": "cli", "name": None},
    }
    assert len(started["pieces"]) == 32

    human_move = await manager.human_move("e2e4")
    assert human_move["last_move"]["san"] == "e4"
    assert human_move["turn"] == "llm"
    with pytest.raises(WrongTurnError):
        await manager.human_move("d2d4")

    llm_move = await manager.llm_move("e5", wait=False)
    assert llm_move["last_move"]["actor"] == "llm"
    assert llm_move["turn"] == "human"


@pytest.mark.asyncio
async def test_llm_wait_does_not_lose_human_move() -> None:
    manager = GameManager()
    waiter = asyncio.create_task(manager.wait_for_llm())
    await asyncio.sleep(0)
    await manager.start_game("white")
    await manager.human_move("e2e4")
    snapshot = await asyncio.wait_for(waiter, timeout=1)
    assert snapshot["event"] == "human_move"
    assert snapshot["turn"] == "llm"


@pytest.mark.asyncio
async def test_llm_move_wait_returns_reset() -> None:
    manager = GameManager()
    await manager.start_game("black")
    await manager.llm_move("e2e4", wait=False)
    await manager.human_move("e7e5")
    waiting_move = asyncio.create_task(manager.llm_move("g1f3", wait=True))
    await asyncio.sleep(0)
    reset = await manager.start_game("white")
    result = await asyncio.wait_for(waiting_move, timeout=1)
    assert reset["event"] == "game_reset"
    assert result["event"] == "game_reset"


@pytest.mark.asyncio
async def test_llm_move_wait_prefers_reset_after_a_fast_human_move() -> None:
    manager = GameManager()
    await manager.start_game("black")
    await manager.llm_move("e2e4", wait=False)
    await manager.human_move("e7e5")
    waiting_move = asyncio.create_task(manager.llm_move("g1f3", wait=True))
    await asyncio.sleep(0)

    await manager.human_move("b8c6")
    await manager.start_game("white")

    result = await asyncio.wait_for(waiting_move, timeout=1)
    assert result["event"] == "game_reset"


@pytest.mark.asyncio
async def test_illegal_and_terminal_moves_are_domain_errors() -> None:
    manager = GameManager()
    await manager.start_game("white")
    with pytest.raises(IllegalMoveError):
        await manager.human_move("e4")
    await manager.human_move("f2f3")
    await manager.llm_move("e5", wait=False)
    await manager.human_move("g2g4")
    terminal = await manager.llm_move("d8h4", wait=False)
    assert terminal["status"] == "checkmate"
    assert terminal["result"] == "0-1"
    with pytest.raises(GameOverError):
        await manager.human_move("a2a3")


@pytest.mark.asyncio
async def test_castling_and_en_passant_follow_standard_rules() -> None:
    castling = GameManager()
    await castling.start_game("white")
    await castling.human_move("e2e4")
    await castling.llm_move("e7e5", wait=False)
    await castling.human_move("g1f3")
    await castling.llm_move("b8c6", wait=False)
    await castling.human_move("f1e2")
    await castling.llm_move("g8f6", wait=False)
    castled = await castling.human_move("e1g1")
    assert castled["pieces"]["g1"] == "K"
    assert castled["pieces"]["f1"] == "R"

    en_passant = GameManager()
    await en_passant.start_game("white")
    await en_passant.human_move("e2e4")
    await en_passant.llm_move("a7a6", wait=False)
    await en_passant.human_move("e4e5")
    await en_passant.llm_move("d7d5", wait=False)
    captured = await en_passant.human_move("e5d6")
    assert captured["pieces"]["d6"] == "P"
    assert "d5" not in captured["pieces"]


@pytest.mark.asyncio
@pytest.mark.parametrize("promotion", ["q", "r", "b", "n"])
async def test_all_promotion_choices_are_applied(promotion: str) -> None:
    manager = GameManager()
    manager._board = chess.Board("8/P7/8/8/8/8/7k/K7 w - - 0 1")
    manager._game_id = "promotion"
    manager._human_color = "white"
    manager._llm_color = "black"

    snapshot = await manager.human_move(f"a7a8{promotion}")

    assert snapshot["last_move"]["promotion"] == promotion
    assert snapshot["pieces"]["a8"] == promotion.upper()


@pytest.mark.asyncio
async def test_stalemate_repetition_and_fifty_move_draws_are_detected() -> None:
    stalemate = GameManager()
    stalemate._board = chess.Board("7k/5Q2/6K1/8/8/8/8/8 b - - 0 1")
    stalemate._game_id = "stalemate"
    stalemate._human_color = "black"
    stalemate._llm_color = "white"
    stalemate_snapshot = await stalemate.snapshot()
    assert stalemate_snapshot["status"] == "draw"
    assert stalemate_snapshot["status_reason"] == "stalemate"

    fifty_move = GameManager()
    fifty_move._board = chess.Board("7k/8/8/8/8/8/8/KR6 w - - 100 51")
    fifty_move._game_id = "fifty-move"
    fifty_move._human_color = "white"
    fifty_move._llm_color = "black"
    fifty_move_snapshot = await fifty_move.snapshot()
    assert fifty_move_snapshot["status"] == "draw"
    assert fifty_move_snapshot["status_reason"] == "fifty_moves"
    assert fifty_move_snapshot["legal_moves"] == []

    repetition = GameManager()
    await repetition.start_game("white")
    await repetition.human_move("g1f3")
    await repetition.llm_move("g8f6", wait=False)
    await repetition.human_move("f3g1")
    await repetition.llm_move("f6g8", wait=False)
    await repetition.human_move("g1f3")
    await repetition.llm_move("g8f6", wait=False)
    repeated = await repetition.human_move("f3g1")
    assert repeated["status"] == "draw"
    assert repeated["status_reason"] == "threefold_repetition"


@pytest.mark.asyncio
async def test_takeback_request_and_acceptance_undo_one_or_two_plies() -> None:
    one_ply = GameManager()
    await one_ply.start_game("white")
    await one_ply.human_move("e2e4")
    pending = await one_ply.takeback("human", "request")
    assert pending["event"] == "takeback_requested"
    assert pending["status"] == "active"
    assert pending["status_reason"] == "takeback_pending"
    assert pending["takeback"] == {
        "state": "pending",
        "requester": "human",
        "target_ply": 1,
        "undone_plies": 1,
    }
    assert pending["legal_moves"] == []
    accepted = await one_ply.takeback("llm", "accept")
    assert accepted["event"] == "takeback_accepted"
    assert accepted["takeback"]["undone_plies"] == 1
    assert accepted["turn"] == "human"
    assert accepted["move_history"] == []
    assert accepted["last_move"] is None

    two_plies = GameManager()
    await two_plies.start_game("white")
    await two_plies.human_move("e2e4")
    await two_plies.llm_move("e7e5", wait=False)
    pending = await two_plies.takeback("human", "request")
    assert pending["takeback"]["undone_plies"] == 2
    accepted = await two_plies.takeback("llm", "accept")
    assert accepted["takeback"]["undone_plies"] == 2
    assert accepted["turn"] == "human"
    assert accepted["move_history"] == []
    assert accepted["last_move"] is None


@pytest.mark.asyncio
async def test_takeback_rejection_preserves_position_and_move_clears_result() -> None:
    manager = GameManager()
    await manager.start_game("white")
    await manager.human_move("e2e4")
    await manager.llm_move("e7e5", wait=False)
    before = await manager.snapshot()
    await manager.takeback("human", "request")
    rejected = await manager.takeback("llm", "reject")
    assert rejected["event"] == "takeback_rejected"
    assert rejected["takeback"]["state"] == "rejected"
    assert rejected["takeback"]["undone_plies"] == 0
    assert rejected["fen"] == before["fen"]
    assert rejected["move_history"] == before["move_history"]
    resumed = await manager.human_move("g1f3")
    assert resumed["takeback"] is None


@pytest.mark.asyncio
async def test_pending_takeback_freezes_moves_and_wakes_waiters() -> None:
    manager = GameManager()
    await manager.start_game("black")
    await manager.llm_move("e2e4", wait=False)
    await manager.human_move("e7e5")
    waiting_move = asyncio.create_task(manager.llm_move("g1f3", wait=True))
    await asyncio.sleep(0)
    await manager.takeback("human", "request")
    result = await asyncio.wait_for(waiting_move, timeout=1)
    assert result["event"] == "takeback_requested"
    with pytest.raises(TakebackStateError):
        await manager.llm_move("g1f3", wait=False)
    with pytest.raises(TakebackStateError):
        await manager.takeback("human", "request")
    assert (await manager.wait_for_llm())["event"] == "takeback_requested"


@pytest.mark.asyncio
async def test_llm_takeback_waits_for_human_and_resignation_wakes_it() -> None:
    manager = GameManager()
    await manager.start_game("white")
    await manager.human_move("e2e4")
    await manager.llm_move("e7e5", wait=False)
    request = asyncio.create_task(manager.takeback("llm", "request"))
    await asyncio.sleep(0)
    assert (await manager.snapshot())["takeback"]["state"] == "pending"
    resigned = await manager.resign("human")
    result = await asyncio.wait_for(request, timeout=1)
    assert resigned["event"] == "human_resigned"
    assert result["status"] == "resigned"
    assert result["status_reason"] == "resignation"
    assert result["resigned_by"] == "human"
    assert result["turn"] is None
    assert result["legal_moves"] == []
    assert result["result"] == "0-1"


@pytest.mark.asyncio
async def test_llm_takeback_waiter_returns_its_original_reset_after_new_request() -> None:
    manager = GameManager()
    await manager.start_game("white")
    await manager.human_move("e2e4")
    await manager.llm_move("e7e5", wait=False)
    original = asyncio.create_task(manager.takeback("llm", "request"))
    await asyncio.sleep(0)

    await manager.start_game("white")
    await manager.human_move("e2e4")
    await manager.takeback("human", "request")

    result = await asyncio.wait_for(original, timeout=1)
    assert result["event"] == "game_reset"


@pytest.mark.asyncio
async def test_llm_pending_takeback_does_not_wake_llm_wait_or_blocking_move() -> None:
    manager = GameManager()
    await manager.start_game("black")
    await manager.llm_move("e2e4", wait=False)
    await manager.human_move("e7e5")
    blocking_move = asyncio.create_task(manager.llm_move("g1f3", wait=True))
    await asyncio.sleep(0)
    request = asyncio.create_task(manager.takeback("llm", "request"))
    await asyncio.sleep(0)
    assert not blocking_move.done()

    waiting = asyncio.create_task(manager.wait_for_llm())
    await asyncio.sleep(0)
    assert not waiting.done()

    rejected = await manager.takeback("human", "reject")
    assert rejected["event"] == "takeback_rejected"
    assert not blocking_move.done()
    assert not waiting.done()
    await manager.human_move("d7d5")

    move_result = await asyncio.wait_for(blocking_move, timeout=1)
    wait_result = await asyncio.wait_for(waiting, timeout=1)
    request_result = await asyncio.wait_for(request, timeout=1)
    assert move_result["event"] == "human_move"
    assert wait_result["event"] == "human_move"
    assert request_result["event"] == "takeback_rejected"


@pytest.mark.asyncio
async def test_cli_players_alternate_colors_and_keep_names_and_actors() -> None:
    manager = GameManager()
    started = await manager.start_game(
        game_mode="cli_vs_cli",
        white_name="  Alpha  ",
        black_name="   ",
    )

    assert started["game_mode"] == "cli_vs_cli"
    assert started["human_color"] is None
    assert started["llm_color"] is None
    assert started["players"] == {
        "white": {"actor": "white", "controller": "cli", "name": "Alpha"},
        "black": {"actor": "black", "controller": "cli", "name": None},
    }
    assert started["turn"] == "white"

    white_move = await manager.player_move("white", "e2e4", wait=False)
    assert white_move["event"] == "white_move"
    assert white_move["turn"] == "black"
    black_move = await manager.player_move("black", "e7e5", wait=False)
    assert black_move["event"] == "black_move"
    assert black_move["turn"] == "white"
    assert [move["actor"] for move in black_move["move_history"]] == ["white", "black"]


@pytest.mark.asyncio
async def test_cli_color_wait_resolves_setup_and_waits_for_that_color() -> None:
    manager = GameManager()
    white_wait = asyncio.create_task(manager.wait_for_player("white"))
    black_wait = asyncio.create_task(manager.wait_for_player("black"))
    await asyncio.sleep(0)

    started = await manager.start_game(game_mode="cli_vs_cli")
    white_ready = await asyncio.wait_for(white_wait, timeout=1)
    assert white_ready["event"] == "game_started"
    assert white_ready["turn"] == "white"
    assert not black_wait.done()

    await manager.player_move("white", "e2e4", wait=False)
    black_ready = await asyncio.wait_for(black_wait, timeout=1)
    assert black_ready["event"] == "white_move"
    assert black_ready["turn"] == "black"
    assert started["event"] == "game_started"


@pytest.mark.asyncio
async def test_setup_wait_resolves_cli_side_in_human_vs_llm_mode() -> None:
    manager = GameManager()
    black_wait = asyncio.create_task(manager.wait_for_player("black"))
    await asyncio.sleep(0)

    await manager.start_game("white")
    assert not black_wait.done()
    await manager.human_move("e2e4")

    ready = await asyncio.wait_for(black_wait, timeout=1)
    assert ready["event"] == "human_move"
    assert ready["turn"] == "llm"


@pytest.mark.asyncio
async def test_cli_blocking_move_and_wait_return_reset_before_intermediate_turn() -> None:
    manager = GameManager()
    await manager.start_game(game_mode="cli_vs_cli")
    move_wait = asyncio.create_task(manager.player_move("white", "e2e4", wait=True))
    await asyncio.sleep(0)
    reset = await manager.start_game(game_mode="cli_vs_cli")
    move_result = await asyncio.wait_for(move_wait, timeout=1)
    assert reset["event"] == "game_reset"
    assert move_result["event"] == "game_reset"

    black_wait = asyncio.create_task(manager.wait_for_player("black"))
    await asyncio.sleep(0)
    await manager.player_move("white", "e2e4", wait=False)
    await manager.start_game(game_mode="cli_vs_cli")
    wait_result = await asyncio.wait_for(black_wait, timeout=1)
    assert wait_result["event"] == "game_reset"


@pytest.mark.asyncio
async def test_cli_takeback_request_waits_for_response_and_locks_moves() -> None:
    manager = GameManager()
    await manager.start_game(game_mode="cli_vs_cli")
    await manager.player_move("white", "e2e4", wait=False)
    await manager.player_move("black", "e7e5", wait=False)

    request = asyncio.create_task(manager.player_takeback("white", "request"))
    await asyncio.sleep(0)
    pending = await manager.snapshot()
    assert pending["takeback"]["requester"] == "white"
    assert not request.done()
    with pytest.raises(TakebackStateError):
        await manager.player_move("black", "b8c6", wait=False)
    responder = await manager.wait_for_player("black")
    assert responder["event"] == "takeback_requested"

    accepted = await manager.player_takeback("black", "accept")
    request_result = await asyncio.wait_for(request, timeout=1)
    assert accepted["takeback"]["undone_plies"] == 2
    assert request_result["event"] == "takeback_accepted"
    assert request_result["turn"] == "white"
    assert request_result["move_history"] == []


@pytest.mark.asyncio
async def test_cli_takeback_wait_is_released_by_reset_before_response() -> None:
    manager = GameManager()
    await manager.start_game(game_mode="cli_vs_cli")
    await manager.player_move("white", "e2e4", wait=False)
    request = asyncio.create_task(manager.player_takeback("white", "request"))
    await asyncio.sleep(0)

    reset = await manager.start_game(game_mode="cli_vs_cli")
    result = await asyncio.wait_for(request, timeout=1)
    assert reset["event"] == "game_reset"
    assert result["event"] == "game_reset"


@pytest.mark.asyncio
@pytest.mark.parametrize("resolution", ["reject", "resign"])
async def test_cli_takeback_request_wait_returns_rejection_or_resignation(resolution: str) -> None:
    manager = GameManager()
    await manager.start_game(game_mode="cli_vs_cli")
    await manager.player_move("white", "e2e4", wait=False)
    await manager.player_move("black", "e7e5", wait=False)
    request = asyncio.create_task(manager.player_takeback("white", "request"))
    await asyncio.sleep(0)

    if resolution == "reject":
        response = await manager.player_takeback("black", "reject")
        expected_event = "takeback_rejected"
    else:
        response = await manager.player_resign("black")
        expected_event = "black_resigned"

    result = await asyncio.wait_for(request, timeout=1)
    assert response["event"] == expected_event
    assert result["event"] == expected_event


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("color", "event", "result"),
    [("white", "white_resigned", "0-1"), ("black", "black_resigned", "1-0")],
)
async def test_cli_player_resignation_uses_color_identity(
    color: str, event: str, result: str
) -> None:
    manager = GameManager()
    await manager.start_game(game_mode="cli_vs_cli")

    resigned = await manager.player_resign(color)

    assert resigned["event"] == event
    assert resigned["resigned_by"] == color
    assert resigned["status"] == "resigned"
    assert resigned["result"] == result
