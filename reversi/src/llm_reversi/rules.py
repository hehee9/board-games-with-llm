"""리버시 좌표와 착수 규칙을 관리한다."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Literal


Color = Literal["black", "white"]
COLORS: tuple[Color, Color] = ("black", "white")
_COORDINATE_RE = re.compile(r"^([A-Ha-h])([1-8])$")
_DIRECTIONS = tuple(
    (dx, dy)
    for dy in (-1, 0, 1)
    for dx in (-1, 0, 1)
    if dx != 0 or dy != 0
)


class RuleError(ValueError):
    """리버시 규칙 엔진의 입력 오류."""


class InvalidCoordinateError(RuleError):
    """좌표 형식 또는 범위가 잘못되었다."""


class IllegalMoveError(RuleError):
    """상대 돌을 뒤집지 못하는 착수다."""


@dataclass(frozen=True)
class BoardState:
    """되돌리기에 필요한 보드와 차례."""

    discs: dict[str, Color]
    to_play: Color


@dataclass(frozen=True)
class MoveResult:
    """착수한 칸과 뒤집힌 칸."""

    move: str
    color: Color
    flipped: list[str]


def other_color(color: Color) -> Color:
    """상대 색을 반환한다."""
    return "white" if color == "black" else "black"


def coordinate_to_point(coordinate: str) -> tuple[int, int]:
    """A1 왼쪽 위 기준 좌표를 0부터 시작하는 `(x, y)`로 바꾼다."""
    if not isinstance(coordinate, str):
        raise InvalidCoordinateError("좌표는 문자열이어야 합니다.")
    match = _COORDINATE_RE.fullmatch(coordinate.strip())
    if match is None:
        raise InvalidCoordinateError(f"잘못된 좌표입니다: {coordinate}")
    column, row = match.groups()
    return ord(column.upper()) - ord("A"), int(row) - 1


def point_to_coordinate(point: tuple[int, int]) -> str:
    """0부터 시작하는 `(x, y)`를 A1 왼쪽 위 기준 좌표로 바꾼다."""
    x, y = point
    if not (0 <= x < 8 and 0 <= y < 8):
        raise InvalidCoordinateError(f"보드 밖 좌표입니다: {point}")
    return f"{chr(ord('A') + x)}{y + 1}"


def normalize_coordinate(coordinate: str) -> str:
    """좌표를 검증하고 대문자 표기로 정규화한다."""
    return point_to_coordinate(coordinate_to_point(coordinate))


class ReversiBoard:
    """표준 8×8 리버시 보드와 합법 수를 관리한다."""

    def __init__(self) -> None:
        self.discs: dict[str, Color] = {
            "D4": "white",
            "E4": "black",
            "D5": "black",
            "E5": "white",
        }
        self.to_play: Color = "black"

    def save_state(self) -> BoardState:
        """현재 보드와 차례를 복사한다."""
        return BoardState(dict(self.discs), self.to_play)

    def restore_state(self, state: BoardState) -> None:
        """저장한 보드와 차례를 복원한다."""
        self.discs = dict(state.discs)
        self.to_play = state.to_play

    def _flips_for(self, coordinate: str, color: Color) -> list[str]:
        x, y = coordinate_to_point(coordinate)
        flips: list[str] = []
        for dx, dy in _DIRECTIONS:
            line: list[str] = []
            next_x, next_y = x + dx, y + dy
            while 0 <= next_x < 8 and 0 <= next_y < 8:
                candidate = point_to_coordinate((next_x, next_y))
                occupant = self.discs.get(candidate)
                if occupant == other_color(color):
                    line.append(candidate)
                    next_x += dx
                    next_y += dy
                    continue
                if occupant == color and line:
                    flips.extend(line)
                break
        return sorted(set(flips), key=lambda value: coordinate_to_point(value)[::-1])

    def legal_moves(self, color: Color | None = None) -> list[str]:
        """지정한 색 또는 현재 차례의 모든 합법 수를 반환한다."""
        active_color = color or self.to_play
        moves: list[str] = []
        for y in range(8):
            for x in range(8):
                coordinate = point_to_coordinate((x, y))
                if coordinate not in self.discs and self._flips_for(coordinate, active_color):
                    moves.append(coordinate)
        return moves

    def play(self, move: str, color: Color | None = None) -> MoveResult:
        """합법 수를 두고 모든 방향의 포위된 상대 돌을 뒤집는다."""
        active_color = color or self.to_play
        if active_color != self.to_play:
            raise IllegalMoveError("현재 차례와 다른 색으로 둘 수 없습니다.")
        normalized = normalize_coordinate(move)
        if normalized in self.discs:
            raise IllegalMoveError(f"이미 돌이 있는 칸입니다: {normalized}")
        flipped = self._flips_for(normalized, active_color)
        if not flipped:
            raise IllegalMoveError(f"상대 돌을 뒤집지 못하는 수입니다: {normalized}")
        self.discs[normalized] = active_color
        for coordinate in flipped:
            self.discs[coordinate] = active_color
        self.to_play = other_color(active_color)
        return MoveResult(normalized, active_color, flipped)


__all__ = [
    "BoardState",
    "Color",
    "IllegalMoveError",
    "InvalidCoordinateError",
    "MoveResult",
    "ReversiBoard",
    "RuleError",
    "coordinate_to_point",
    "normalize_coordinate",
    "other_color",
    "point_to_coordinate",
]
