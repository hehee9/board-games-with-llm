import pytest

from llm_connect4.rules import ConnectFourBoard, IllegalMoveError


def test_red_moves_first_and_discs_fall_to_the_lowest_open_cell() -> None:
    board = ConnectFourBoard()
    assert board.to_play == "red"
    assert board.drop("4").row == 5
    assert board.drop("4").row == 4
    assert board.cells[5][3] == "red"
    assert board.cells[4][3] == "yellow"


@pytest.mark.parametrize(
    "columns, expected",
    [
        ([1, 1, 2, 2, 3, 3, 4], {(5, 0), (5, 1), (5, 2), (5, 3)}),
        ([2, 1, 2, 1, 2, 1, 2], {(2, 1), (3, 1), (4, 1), (5, 1)}),
        ([1, 2, 2, 3, 7, 3, 3, 4, 7, 4, 7, 4, 4], {(2, 3), (3, 2), (4, 1), (5, 0)}),
        ([7, 6, 6, 5, 1, 5, 5, 4, 1, 4, 1, 4, 4], {(2, 3), (3, 4), (4, 5), (5, 6)}),
    ],
)
def test_horizontal_vertical_and_both_diagonal_wins(columns: list[int], expected: set[tuple[int, int]]) -> None:
    board = ConnectFourBoard()
    result = None
    for column in columns:
        result = board.drop(column)
    assert board.winner == "red"
    assert set(result.winning_line) == expected


def test_rejects_bad_columns_and_full_column() -> None:
    board = ConnectFourBoard()
    for column in ("0", "8", "1.5", "x"):
        with pytest.raises(IllegalMoveError):
            board.drop(column)
    for _ in range(3):
        board.drop(1)
        board.drop(1)
    assert 1 not in board.legal_columns
    with pytest.raises(IllegalMoveError, match="full"):
        board.drop(1)


def test_full_board_without_a_four_is_a_draw() -> None:
    board = ConnectFourBoard()
    palette = ("red", "red", "yellow", "yellow")
    board.cells = [[palette[(row + column * 2) % 4] for column in range(7)] for row in range(6)]
    board.cells[0][0] = None
    board.to_play = "red"
    board.drop(1)
    assert board.is_draw
    assert board.winner is None
    assert board.legal_columns == []
