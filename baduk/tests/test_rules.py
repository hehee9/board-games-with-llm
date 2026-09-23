import pytest

from llm_baduk.rules import GoBoard, IllegalMoveError, InvalidCoordinateError, normalize_coordinate


def test_coordinates_skip_i_and_use_bottom_left_origin() -> None:
    assert normalize_coordinate("a1", 19) == "A1"
    assert normalize_coordinate("j19", 19) == "J19"
    assert normalize_coordinate("j9", 9) == "J9"
    with pytest.raises(InvalidCoordinateError):
        normalize_coordinate("i4", 19)


def test_capture_and_suicide() -> None:
    board = GoBoard(9)
    board.play("B1")
    board.play("A1")
    result = board.play("A2")
    assert result.captured == ["A1"]
    assert board.captures == {"black": 1, "white": 0}
    with pytest.raises(IllegalMoveError):
        board.play("A1")


def test_pass_enters_two_pass_scoring_and_clears_ko() -> None:
    board = GoBoard(9)
    board.play("pass")
    assert board.consecutive_passes == 1
    board.ko = "A1"
    board.play("pass")
    assert board.consecutive_passes == 2
    assert board.ko is None


def test_ko_cycle_repeating_board_and_turn_is_a_draw() -> None:
    board = GoBoard(9)
    board.stones = {
        "A3": "white",
        "C3": "white",
        "B4": "white",
        "A2": "black",
        "B2": "white",
        "C2": "black",
        "B1": "black",
    }
    board.to_play = "black"
    board._seen.clear()
    board._seen[board.position_key()] = 1
    board.play("B3")
    board.play("pass")
    board.play("pass")
    board.play("B2")
    assert board.repetition_count == 2
    assert board.is_repetition_draw


def test_state_restore_restores_repetition_and_capture_counts() -> None:
    board = GoBoard(9)
    state = board.save_state()
    board.play("A1")
    board.play("B1")
    board.restore_state(state)
    assert board.stones == {}
    assert board.to_play == "black"
    assert board.captures == {"black": 0, "white": 0}
    assert not board.is_repetition_draw


def test_territory_and_dead_prisoner_scoring() -> None:
    board = GoBoard(9)
    board.stones = {"A1": "black", "B1": "black", "A2": "black", "B2": "white"}
    board.captures = {"black": 0, "white": 0}
    score = board.score(dead={"b2"})
    assert score["dead"] == ["B2"]
    assert score["prisoners"] == {"black": 1, "white": 0}
    assert "B2" in score["territory"]["black"]
