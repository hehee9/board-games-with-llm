"""Connect Four 보드와 기본 규칙."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal


Color = Literal["red", "yellow"]
COLORS: tuple[Color, Color] = ("red", "yellow")
WIDTH = 7
HEIGHT = 6
CONNECT = 4


class RuleError(ValueError):
    """게임 규칙에 맞지 않는 입력."""


class IllegalMoveError(RuleError):
    """선택한 열에 둘 수 없는 수."""


@dataclass(frozen=True)
class BoardState:
    """이전 위치 복원에 필요한 보드 상태."""

    cells: tuple[tuple[Color | None, ...], ...]
    to_play: Color
    winner: Color | None
    winning_line: tuple[tuple[int, int], ...]
    is_draw: bool


@dataclass(frozen=True)
class MoveResult:
    """적용한 수의 결과."""

    column: int
    row: int
    color: Color
    winning_line: tuple[tuple[int, int], ...]


def other_color(color: Color) -> Color:
    """상대 색 반환."""
    return "yellow" if color == "red" else "red"


def parse_column(value: str | int) -> int:
    """1부터 7까지의 사용자 열 번호를 0부터 시작하는 값으로 변환."""
    if isinstance(value, bool):
        raise IllegalMoveError(f"Invalid column: {value}")
    try:
        column = int(value)
    except (TypeError, ValueError):
        raise IllegalMoveError(f"Invalid column: {value}") from None
    if isinstance(value, str) and str(column) != value.strip():
        raise IllegalMoveError(f"Invalid column: {value}")
    if not 1 <= column <= WIDTH:
        raise IllegalMoveError(f"Column must be between 1 and {WIDTH}: {value}")
    return column - 1


class ConnectFourBoard:
    """7열 6행 보드에서 중력과 승리 조건을 적용."""

    def __init__(self) -> None:
        self.cells: list[list[Color | None]] = [[None] * WIDTH for _ in range(HEIGHT)]
        self.to_play: Color = "red"
        self.winner: Color | None = None
        self.winning_line: tuple[tuple[int, int], ...] = ()
        self.is_draw = False

    @property
    def legal_columns(self) -> list[int]:
        """아직 놓을 수 있는 1-based 열 번호."""
        return [column + 1 for column in range(WIDTH) if self.cells[0][column] is None]

    def save_state(self) -> BoardState:
        """현재 위치를 불변 상태로 복사."""
        return BoardState(
            cells=tuple(tuple(row) for row in self.cells),
            to_play=self.to_play,
            winner=self.winner,
            winning_line=self.winning_line,
            is_draw=self.is_draw,
        )

    def restore_state(self, state: BoardState) -> None:
        """저장한 위치 복원."""
        self.cells = [list(row) for row in state.cells]
        self.to_play = state.to_play
        self.winner = state.winner
        self.winning_line = state.winning_line
        self.is_draw = state.is_draw

    def _winning_run(self, row: int, column: int, color: Color) -> tuple[tuple[int, int], ...]:
        """놓은 돌을 지나는 모든 4개 이상 연속 수를 찾음."""
        for row_step, column_step in ((0, 1), (1, 0), (1, 1), (1, -1)):
            line = [(row, column)]
            for direction in (-1, 1):
                next_row = row + row_step * direction
                next_column = column + column_step * direction
                while (
                    0 <= next_row < HEIGHT
                    and 0 <= next_column < WIDTH
                    and self.cells[next_row][next_column] == color
                ):
                    line.append((next_row, next_column))
                    next_row += row_step * direction
                    next_column += column_step * direction
            if len(line) >= CONNECT:
                return tuple(sorted(line))
        return ()

    def drop(self, column: str | int, color: Color | None = None) -> MoveResult:
        """지정한 열에 차례의 돌을 떨어뜨림."""
        column_index = parse_column(column)
        color = self.to_play if color is None else color
        if color not in COLORS or color != self.to_play:
            raise IllegalMoveError("It is not this color's turn.")
        if self.winner is not None or self.is_draw:
            raise IllegalMoveError("The game is already over.")
        row = next((candidate for candidate in range(HEIGHT - 1, -1, -1) if self.cells[candidate][column_index] is None), None)
        if row is None:
            raise IllegalMoveError(f"Column {column_index + 1} is full.")
        self.cells[row][column_index] = color
        self.winning_line = self._winning_run(row, column_index, color)
        if self.winning_line:
            self.winner = color
        elif not self.legal_columns:
            self.is_draw = True
        self.to_play = other_color(color)
        return MoveResult(column_index + 1, row, color, self.winning_line)


__all__ = [
    "BoardState",
    "Color",
    "COLORS",
    "ConnectFourBoard",
    "HEIGHT",
    "IllegalMoveError",
    "MoveResult",
    "RuleError",
    "WIDTH",
    "other_color",
    "parse_column",
]
