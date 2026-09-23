import pytest

from llm_reversi.rules import (
    IllegalMoveError,
    InvalidCoordinateError,
    ReversiBoard,
    coordinate_to_point,
    normalize_coordinate,
    point_to_coordinate,
)


def test_initial_moves_and_coordinate_normalization() -> None:
    board = ReversiBoard()

    assert board.legal_moves() == ["D3", "C4", "F5", "E6"]
    assert coordinate_to_point("a1") == (0, 0)
    assert point_to_coordinate((7, 7)) == "H8"
    assert normalize_coordinate(" d3 ") == "D3"


def test_move_flips_bracketed_discs_in_all_eight_directions() -> None:
    board = ReversiBoard()
    board.discs = {}
    center_x, center_y = coordinate_to_point("D4")
    expected_flips = set()
    for dx in (-1, 0, 1):
        for dy in (-1, 0, 1):
            if dx == dy == 0:
                continue
            adjacent = point_to_coordinate((center_x + dx, center_y + dy))
            bracket = point_to_coordinate((center_x + 2 * dx, center_y + 2 * dy))
            board.discs[adjacent] = "white"
            board.discs[bracket] = "black"
            expected_flips.add(adjacent)

    result = board.play("d4")

    assert result.move == "D4"
    assert set(result.flipped) == expected_flips
    assert all(board.discs[square] == "black" for square in expected_flips | {"D4"})


def test_illegal_and_out_of_board_moves_are_rejected() -> None:
    board = ReversiBoard()

    with pytest.raises(IllegalMoveError):
        board.play("A1")
    with pytest.raises(InvalidCoordinateError):
        board.play("I9")
