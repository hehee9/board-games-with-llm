"""바둑판 좌표, 수 적용, 패·반복과 영토 점수 계산."""

from __future__ import annotations

import re
from collections import Counter, deque
from dataclasses import dataclass
from typing import Iterable, Literal


Color = Literal["black", "white"]
COLORS: tuple[Color, Color] = ("black", "white")
LETTERS = "ABCDEFGHJKLMNOPQRST"
_COORDINATE_RE = re.compile(r"^([A-Za-z])([0-9]{1,2})$")


class RuleError(ValueError):
    """규칙 엔진에서 발생하는 정상적인 입력 오류."""


class InvalidCoordinateError(RuleError):
    """바둑판 좌표 형식 또는 크기가 잘못되었다."""


class IllegalMoveError(RuleError):
    """착수할 수 없는 바둑 수다."""


@dataclass(frozen=True)
class RuleState:
    """되돌리기에 필요한 한 시점의 규칙 상태."""

    stones: dict[str, Color]
    captures: dict[Color, int]
    to_play: Color
    ko: str | None
    seen: dict[tuple[frozenset[str], frozenset[str], Color], int]
    consecutive_passes: int


@dataclass(frozen=True)
class MoveResult:
    """착수 결과."""

    move: str
    color: Color
    captured: list[str]


def other_color(color: Color) -> Color:
    """상대 색 반환."""
    return "white" if color == "black" else "black"


def _validate_size(size: int) -> None:
    if size not in (9, 13, 19):
        raise ValueError("지원하는 바둑판 크기는 9, 13, 19입니다.")


def coordinate_to_point(coordinate: str, size: int) -> tuple[int, int]:
    """대문자 좌표를 왼쪽 아래 원점의 `(x, y)`로 변환."""
    _validate_size(size)
    if not isinstance(coordinate, str):
        raise InvalidCoordinateError("좌표는 문자열이어야 합니다.")
    match = _COORDINATE_RE.fullmatch(coordinate)
    if match is None:
        raise InvalidCoordinateError(f"잘못된 좌표입니다: {coordinate}")
    letter, row_text = match.groups()
    letter = letter.upper()
    if row_text.startswith("0"):
        raise InvalidCoordinateError(f"잘못된 좌표입니다: {coordinate}")
    row = int(row_text)
    if letter not in LETTERS or row < 1 or row > size:
        raise InvalidCoordinateError(f"바둑판 밖 좌표입니다: {coordinate}")
    x = LETTERS.index(letter)
    if x >= size:
        raise InvalidCoordinateError(f"바둑판 밖 좌표입니다: {coordinate}")
    return x, row - 1


def point_to_coordinate(point: tuple[int, int], size: int) -> str:
    """왼쪽 아래 원점의 `(x, y)`를 대문자 좌표로 변환."""
    _validate_size(size)
    x, y = point
    if not (0 <= x < size and 0 <= y < size):
        raise InvalidCoordinateError(f"바둑판 밖 점입니다: {point}")
    return f"{LETTERS[x]}{y + 1}"


def normalize_coordinate(coordinate: str, size: int) -> str:
    """좌표를 검증하고 대문자 표기로 정규화."""
    return point_to_coordinate(coordinate_to_point(coordinate, size), size)


def _neighbors(point: tuple[int, int], size: int) -> Iterable[tuple[int, int]]:
    x, y = point
    if x > 0:
        yield x - 1, y
    if x + 1 < size:
        yield x + 1, y
    if y > 0:
        yield x, y - 1
    if y + 1 < size:
        yield x, y + 1


class GoBoard:
    """한 판의 바둑 규칙 상태를 관리."""

    def __init__(self, size: int = 19) -> None:
        _validate_size(size)
        self.size = size
        self.stones: dict[str, Color] = {}
        self.captures: dict[Color, int] = {"black": 0, "white": 0}
        self.to_play: Color = "black"
        self.ko: str | None = None
        self.consecutive_passes = 0
        self._seen: Counter[tuple[frozenset[str], frozenset[str], Color]] = Counter()
        self._seen[self.position_key()] = 1

    def position_key(self) -> tuple[frozenset[str], frozenset[str], Color]:
        """반복 판정을 위한 돌·차례 상태 키."""
        return (
            frozenset(coordinate for coordinate, color in self.stones.items() if color == "black"),
            frozenset(coordinate for coordinate, color in self.stones.items() if color == "white"),
            self.to_play,
        )

    def save_state(self) -> RuleState:
        """현재 규칙 상태를 복사해 저장."""
        return RuleState(
            stones=dict(self.stones),
            captures=dict(self.captures),
            to_play=self.to_play,
            ko=self.ko,
            seen=dict(self._seen),
            consecutive_passes=self.consecutive_passes,
        )

    def restore_state(self, state: RuleState) -> None:
        """저장한 규칙 상태 복원."""
        self.stones = dict(state.stones)
        self.captures = dict(state.captures)
        self.to_play = state.to_play
        self.ko = state.ko
        self._seen = Counter(state.seen)
        self.consecutive_passes = state.consecutive_passes

    def _group(self, coordinate: str, stones: dict[str, Color] | None = None) -> set[str]:
        current = stones if stones is not None else self.stones
        color = current[coordinate]
        start = coordinate_to_point(coordinate, self.size)
        group = {coordinate}
        queue = deque([start])
        while queue:
            point = queue.popleft()
            for neighbor in _neighbors(point, self.size):
                candidate = point_to_coordinate(neighbor, self.size)
                if candidate in group or current.get(candidate) != color:
                    continue
                group.add(candidate)
                queue.append(neighbor)
        return group

    def group_at(self, coordinate: str) -> set[str]:
        """좌표의 연결된 돌 무리를 반환."""
        normalized = normalize_coordinate(coordinate, self.size)
        if normalized not in self.stones:
            raise InvalidCoordinateError(f"돌이 없는 좌표입니다: {coordinate}")
        return self._group(normalized)

    def _liberties(self, group: set[str], stones: dict[str, Color] | None = None) -> set[str]:
        current = stones if stones is not None else self.stones
        liberties: set[str] = set()
        for coordinate in group:
            for neighbor in _neighbors(coordinate_to_point(coordinate, self.size), self.size):
                candidate = point_to_coordinate(neighbor, self.size)
                if candidate not in current:
                    liberties.add(candidate)
        return liberties

    def liberties_at(self, coordinate: str) -> set[str]:
        """좌표의 연결된 돌 무리가 가진 활로를 반환."""
        return self._liberties(self.group_at(coordinate))

    def legal_points(self, color: Color | None = None) -> list[str]:
        """현재 상태에서 합법적인 착수 좌표를 반환."""
        color = color or self.to_play
        points: list[str] = []
        for y in range(self.size):
            for x in range(self.size):
                coordinate = point_to_coordinate((x, y), self.size)
                try:
                    self._proposed_state(coordinate, color)
                except IllegalMoveError:
                    continue
                points.append(coordinate)
        return points

    def legal_moves(self, color: Color | None = None) -> list[str]:
        """현재 상태에서 합법적인 좌표와 패를 반환."""
        return [*self.legal_points(color), "pass"]

    def _proposed_state(self, move: str, color: Color) -> tuple[dict[str, Color], list[str], str | None]:
        """착수 후 돌·잡은 돌·새 패 좌표를 계산."""
        normalized = normalize_coordinate(move, self.size)
        if normalized in self.stones:
            raise IllegalMoveError(f"이미 돌이 있는 좌표입니다: {move}")
        if normalized == self.ko:
            raise IllegalMoveError(f"패 규칙 위반입니다: {move}")
        proposed = dict(self.stones)
        proposed[normalized] = color
        captured: list[str] = []
        for neighbor in _neighbors(coordinate_to_point(normalized, self.size), self.size):
            adjacent = point_to_coordinate(neighbor, self.size)
            if proposed.get(adjacent) != other_color(color):
                continue
            group = self._group(adjacent, proposed)
            if not self._liberties(group, proposed):
                captured.extend(sorted(group, key=self._coordinate_sort_key))
                for stone in group:
                    del proposed[stone]
        own_group = self._group(normalized, proposed)
        if not self._liberties(own_group, proposed):
            raise IllegalMoveError(f"자살 수입니다: {move}")
        new_ko: str | None = None
        if len(captured) == 1 and len(own_group) == 1 and len(self._liberties(own_group, proposed)) == 1:
            new_ko = captured[0]
        captured.sort(key=self._coordinate_sort_key)
        return proposed, captured, new_ko

    def _coordinate_sort_key(self, coordinate: str) -> tuple[int, int]:
        x, y = coordinate_to_point(coordinate, self.size)
        return y, x

    def play(self, move: str, color: Color | None = None) -> MoveResult:
        """착수 또는 패를 적용하고 결과를 반환."""
        color = color or self.to_play
        if color != self.to_play:
            raise IllegalMoveError("현재 차례와 다른 색으로 착수할 수 없습니다.")
        if not isinstance(move, str):
            raise IllegalMoveError("수는 문자열이어야 합니다.")
        if move.strip().lower() == "pass":
            normalized = "pass"
            captured: list[str] = []
            self.ko = None
            self.consecutive_passes += 1
        else:
            normalized = normalize_coordinate(move.strip(), self.size)
            proposed, captured, new_ko = self._proposed_state(normalized, color)
            self.stones = proposed
            self.captures[color] += len(captured)
            self.ko = new_ko
            self.consecutive_passes = 0
        self.to_play = other_color(color)
        if normalized != "pass":
            self._seen[self.position_key()] += 1
        return MoveResult(normalized, color, captured)

    @property
    def repetition_count(self) -> int:
        """현재 돌·차례 상태의 반복 횟수."""
        return self._seen[self.position_key()]

    @property
    def is_repetition_draw(self) -> bool:
        """현재 상태가 이전 상태와 한 번 더 반복되었는지 반환."""
        return self.repetition_count >= 2

    def original_groups(self) -> list[set[str]]:
        """현재 판의 연결된 돌 무리를 반환."""
        groups: list[set[str]] = []
        remaining = set(self.stones)
        while remaining:
            coordinate = next(iter(remaining))
            group = self._group(coordinate)
            groups.append(group)
            remaining.difference_update(group)
        return groups

    def score(self, dead: Iterable[str] = (), seki: Iterable[str] = ()) -> dict[str, object]:
        """죽은 돌·빅/세키 표시를 반영해 영토 점수를 계산."""
        dead_set = {normalize_coordinate(coordinate, self.size) for coordinate in dead}
        seki_set = {normalize_coordinate(coordinate, self.size) for coordinate in seki}
        for coordinate in dead_set | seki_set:
            if coordinate not in self.stones:
                raise InvalidCoordinateError(f"돌이 없는 좌표입니다: {coordinate}")
        if dead_set & seki_set:
            raise ValueError("죽은 돌과 세키 돌은 겹칠 수 없습니다.")
        removed = set(dead_set)
        live_stones = {coordinate: color for coordinate, color in self.stones.items() if coordinate not in removed}
        excluded_empty: set[str] = set()
        for coordinate in seki_set:
            for neighbor in _neighbors(coordinate_to_point(coordinate, self.size), self.size):
                candidate = point_to_coordinate(neighbor, self.size)
                if candidate not in live_stones:
                    excluded_empty.add(candidate)

        territory: dict[Color, set[str]] = {"black": set(), "white": set()}
        visited: set[str] = set(live_stones)
        for y in range(self.size):
            for x in range(self.size):
                start = point_to_coordinate((x, y), self.size)
                if start in visited:
                    continue
                region: set[str] = {start}
                queue = deque([(x, y)])
                visited.add(start)
                boundary: set[Color] = set()
                touches_seki = start in excluded_empty
                while queue:
                    point = queue.popleft()
                    for neighbor in _neighbors(point, self.size):
                        candidate = point_to_coordinate(neighbor, self.size)
                        if candidate in live_stones:
                            boundary.add(live_stones[candidate])
                        elif candidate not in visited:
                            visited.add(candidate)
                            region.add(candidate)
                            touches_seki = touches_seki or candidate in excluded_empty
                            queue.append(neighbor)
                if not touches_seki and len(boundary) == 1:
                    territory[next(iter(boundary))].update(region)
        prisoners: dict[Color, int] = {
            "black": self.captures["black"] + sum(1 for coordinate in dead_set if self.stones[coordinate] == "white"),
            "white": self.captures["white"] + sum(1 for coordinate in dead_set if self.stones[coordinate] == "black"),
        }
        totals = {
            "black": float(len(territory["black"]) + prisoners["black"]),
            "white": float(len(territory["white"]) + prisoners["white"] + 6.5),
        }
        return {
            "dead": sorted(dead_set, key=self._coordinate_sort_key),
            "seki": sorted(seki_set, key=self._coordinate_sort_key),
            "territory": {
                "black": sorted(territory["black"], key=self._coordinate_sort_key),
                "white": sorted(territory["white"], key=self._coordinate_sort_key),
            },
            "prisoners": prisoners,
            "totals": totals,
        }


__all__ = [
    "Color",
    "GoBoard",
    "IllegalMoveError",
    "InvalidCoordinateError",
    "MoveResult",
    "RuleError",
    "RuleState",
    "coordinate_to_point",
    "normalize_coordinate",
    "other_color",
    "point_to_coordinate",
]
