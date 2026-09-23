"""인메모리 Connect Four 게임과 비동기 상태 알림."""

from __future__ import annotations

import asyncio
import copy
import uuid
from collections.abc import AsyncIterator
from dataclasses import dataclass
from typing import Literal

from .rules import BoardState, Color, ConnectFourBoard, IllegalMoveError as RuleIllegalMoveError, other_color


Actor = Literal["human", "llm", "red", "yellow"]
Controller = Literal["human", "cli"]
GameMode = Literal["human_vs_llm", "cli_vs_cli"]
TakebackAction = Literal["request", "accept", "reject"]


class GameError(Exception):
    """클라이언트에 반환할 게임 오류."""

    def __init__(self, code: str, message: str, status_code: int = 409) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.status_code = status_code


class NoGameError(GameError):
    """시작한 게임이 없음."""

    def __init__(self) -> None:
        super().__init__("no_game", "No game is in progress. Start a game first.")


class WrongTurnError(GameError):
    """요청한 행위자의 차례가 아님."""

    def __init__(self, actor: Actor) -> None:
        super().__init__("wrong_turn", f"It is not {actor}'s turn.")


class GameOverError(GameError):
    """이미 끝난 게임에 수를 두려고 함."""

    def __init__(self) -> None:
        super().__init__("game_over", "The game is already over.")


class IllegalMoveError(GameError):
    """잘못된 열 또는 가득 찬 열."""

    def __init__(self, move: str) -> None:
        super().__init__("illegal_move", f"Illegal move: {move}", 422)


class TakebackStateError(GameError):
    """현재 상태에서 처리할 수 없는 무르기 동작."""

    _MESSAGES = {
        "no_move": ("takeback_no_move", "There is no move by this player to take back."),
        "duplicate": ("takeback_pending", "A takeback request is already pending."),
        "own_request": ("takeback_own_request", "You cannot respond to your own takeback request."),
        "no_pending": ("takeback_no_pending", "There is no pending takeback request."),
        "pending_move": ("takeback_move_blocked", "Moves are disabled while a takeback request is pending."),
        "inactive": ("takeback_unavailable", "Takeback is unavailable in this game state."),
    }

    def __init__(self, reason: str) -> None:
        code, message = self._MESSAGES[reason]
        super().__init__(code, message)


class InvalidGameSetupError(GameError):
    """새 게임 설정값이 유효하지 않음."""

    def __init__(self, field: str, value: object) -> None:
        if field == "human_color":
            code = "invalid_color"
            message = f"Unsupported human color: {value}"
        else:
            code = "invalid_game_mode"
            message = f"Unsupported game mode: {value}"
        super().__init__(code, message, 422)


class InvalidPlayerColorError(GameError):
    """색상별 CLI 경로에 유효하지 않은 색이 전달됨."""

    def __init__(self, color: str) -> None:
        super().__init__("invalid_color", f"Unsupported player color: {color}", 422)


class PlayerNotCliError(GameError):
    """요청한 색을 CLI가 제어하지 않음."""

    def __init__(self, color: str) -> None:
        super().__init__("player_not_cli", f"Player {color} is not controlled by a CLI.")


class ColorRequiredError(GameError):
    """CLI 대 CLI에서 색을 지정하지 않은 경로를 사용함."""

    def __init__(self) -> None:
        super().__init__("color_required", "Use a color-specific player endpoint for CLI-vs-CLI games.")


@dataclass(frozen=True)
class MoveData:
    """API 응답용 착수 기록."""

    ply: int
    move: int
    row: int
    color: Color
    actor: Actor

    def as_dict(self) -> dict[str, object]:
        return {"ply": self.ply, "move": self.move, "column": self.move, "row": self.row, "color": self.color, "actor": self.actor}


@dataclass(frozen=True)
class PositionBeforeMove:
    """착수 전 보드와 이력."""

    board: BoardState
    history: tuple[MoveData, ...]


@dataclass(frozen=True)
class TakebackData:
    """무르기 요청 및 응답 상태."""

    state: Literal["pending", "accepted", "rejected"]
    requester: Actor
    target_ply: int
    undone_plies: int
    target_index: int

    def as_dict(self) -> dict[str, object]:
        return {"state": self.state, "requester": self.requester, "target_ply": self.target_ply, "undone_plies": self.undone_plies}


class GameManager:
    """게임 보드와 연결된 CLI·브라우저 상태를 관리."""

    def __init__(self) -> None:
        self._condition = asyncio.Condition()
        self._board: ConnectFourBoard | None = None
        self._game_id: str | None = None
        self._game_mode: GameMode = "human_vs_llm"
        self._human_color: Color | None = None
        self._llm_color: Color | None = None
        self._players: dict[Color, dict[str, Actor | Controller | str | None]] = {}
        self._move_history: list[MoveData] = []
        self._positions_before: list[PositionBeforeMove] = []
        self._last_move: MoveData | None = None
        self._takeback: TakebackData | None = None
        self._resigned_by: Actor | None = None
        self._phase: Literal["setup", "active", "won", "draw", "resigned"] = "setup"
        self._revision = 0
        self._event = "setup"
        self._published: list[dict[str, object]] = [self._snapshot_unlocked()]

    def _status_reason_unlocked(self) -> str:
        if self._phase == "setup":
            return "no_game"
        if self._takeback is not None and self._takeback.state == "pending":
            return "takeback_pending"
        if self._phase == "active":
            return "in_progress"
        if self._phase == "won":
            return "four_in_a_row"
        if self._phase == "draw":
            return "board_full"
        return "resignation"

    def _turn_unlocked(self) -> Actor | None:
        if self._board is None or self._phase != "active":
            return None
        if self._game_mode == "cli_vs_cli":
            return self._board.to_play
        return "human" if self._board.to_play == self._human_color else "llm"

    def _snapshot_unlocked(self) -> dict[str, object]:
        board = self._board
        winner = board.winner if board is not None else None
        return {
            "event": self._event,
            "game_id": self._game_id,
            "revision": self._revision,
            "status": self._phase,
            "status_reason": self._status_reason_unlocked(),
            "game_mode": self._game_mode if board is not None else None,
            "players": copy.deepcopy(self._players),
            "human_color": self._human_color,
            "llm_color": self._llm_color,
            "turn": self._turn_unlocked(),
            "to_play": board.to_play if board is not None else None,
            "board": [list(row) for row in board.cells] if board is not None else [[None] * 7 for _ in range(6)],
            "legal_columns": board.legal_columns if board is not None and self._phase == "active" and not self._pending_takeback_unlocked() else [],
            "move_history": [move.as_dict() for move in self._move_history],
            "last_move": self._last_move.as_dict() if self._last_move else None,
            "winning_line": [list(point) for point in board.winning_line] if board is not None else [],
            "takeback": self._takeback.as_dict() if self._takeback else None,
            "resigned_by": self._resigned_by,
            "winner": winner if winner is not None else (other_color(self._actor_color_unlocked(self._resigned_by)) if self._resigned_by is not None else None),
            "result": f"{winner} wins" if winner is not None else ("Draw" if self._phase == "draw" else f"{other_color(self._actor_color_unlocked(self._resigned_by))} wins by resignation" if self._resigned_by is not None else None),
        }

    def _pending_takeback_unlocked(self) -> bool:
        return self._takeback is not None and self._takeback.state == "pending"

    def _publish_unlocked(self, event: str) -> dict[str, object]:
        self._event = event
        self._revision += 1
        snapshot = self._snapshot_unlocked()
        self._published.append(snapshot)
        return copy.deepcopy(snapshot)

    def _notify_unlocked(self) -> None:
        self._condition.notify_all()

    def _snapshots_after_unlocked(self, revision: int) -> list[dict[str, object]]:
        return [copy.deepcopy(snapshot) for snapshot in self._published if int(snapshot["revision"]) > revision]

    def _actor_color_unlocked(self, actor: Actor) -> Color | None:
        if actor in {"red", "yellow"}:
            return actor
        if actor == "human":
            return self._human_color
        if actor == "llm":
            return self._llm_color
        return None

    def _actor_keys_unlocked(self) -> tuple[Actor, Actor]:
        return ("red", "yellow") if self._game_mode == "cli_vs_cli" else ("human", "llm")

    def _is_actor_actionable(self, snapshot: dict[str, object], actor: Actor) -> bool:
        if snapshot["status"] in {"won", "draw", "resigned"}:
            return True
        takeback = snapshot["takeback"]
        if isinstance(takeback, dict) and takeback["state"] == "pending":
            return takeback["requester"] != actor
        return snapshot["status"] == "active" and snapshot["turn"] == actor

    def _wait_result_unlocked(self, revision: int, actor: Actor) -> dict[str, object] | None:
        pending = self._snapshots_after_unlocked(revision)
        for snapshot in pending:
            if snapshot["event"] == "game_reset":
                return snapshot
        for snapshot in pending:
            if self._is_actor_actionable(snapshot, actor):
                return snapshot
        return None

    def _require_legacy_mode_unlocked(self) -> None:
        if self._game_mode == "cli_vs_cli":
            raise ColorRequiredError()

    def _resolve_cli_actor_unlocked(self, color: str) -> Actor:
        if color not in {"red", "yellow"}:
            raise InvalidPlayerColorError(color)
        if color not in self._players or self._players[color]["controller"] != "cli":
            raise PlayerNotCliError(color)
        return self._players[color]["actor"]

    def _require_board_unlocked(self) -> ConnectFourBoard:
        if self._board is None:
            raise NoGameError()
        return self._board

    def _require_active_unlocked(self) -> ConnectFourBoard:
        board = self._require_board_unlocked()
        if self._phase != "active":
            raise GameOverError()
        if self._pending_takeback_unlocked():
            raise TakebackStateError("pending_move")
        return board

    def _require_actor_turn_unlocked(self, actor: Actor, board: ConnectFourBoard) -> Color:
        color = self._actor_color_unlocked(actor)
        if color is None or board.to_play != color:
            raise WrongTurnError(actor)
        return color

    def _apply_move_unlocked(self, actor: Actor, move_text: str | int) -> MoveData:
        board = self._require_active_unlocked()
        color = self._require_actor_turn_unlocked(actor, board)
        before = PositionBeforeMove(board.save_state(), tuple(self._move_history))
        try:
            result = board.drop(move_text, color)
        except RuleIllegalMoveError:
            raise IllegalMoveError(str(move_text)) from None
        self._positions_before.append(before)
        move = MoveData(len(self._move_history) + 1, result.column, result.row, result.color, actor)
        self._move_history.append(move)
        self._last_move = move
        if self._takeback is not None and self._takeback.state != "pending":
            self._takeback = None
        if board.winner is not None:
            self._phase = "won"
        elif board.is_draw:
            self._phase = "draw"
        return move

    async def snapshot(self) -> dict[str, object]:
        async with self._condition:
            return copy.deepcopy(self._snapshot_unlocked())

    async def start_game(
        self,
        human_color: Color | None = None,
        *,
        game_mode: GameMode = "human_vs_llm",
        red_name: str | None = None,
        yellow_name: str | None = None,
    ) -> dict[str, object]:
        if game_mode not in {"human_vs_llm", "cli_vs_cli"}:
            raise InvalidGameSetupError("game_mode", game_mode)
        if game_mode == "human_vs_llm" and human_color not in {"red", "yellow"}:
            raise InvalidGameSetupError("human_color", human_color)
        names = {"red": red_name.strip() if red_name and red_name.strip() else None, "yellow": yellow_name.strip() if yellow_name and yellow_name.strip() else None}
        async with self._condition:
            had_game = self._board is not None
            self._board = ConnectFourBoard()
            self._game_id = uuid.uuid4().hex
            self._game_mode = game_mode
            self._human_color = human_color if game_mode == "human_vs_llm" else None
            self._llm_color = other_color(human_color) if game_mode == "human_vs_llm" else None
            self._players = {
                color: {
                    "actor": ("human" if color == human_color else "llm") if game_mode == "human_vs_llm" else color,
                    "controller": ("human" if color == human_color else "cli") if game_mode == "human_vs_llm" else "cli",
                    "name": names[color],
                }
                for color in ("red", "yellow")
            }
            self._move_history = []
            self._positions_before = []
            self._last_move = None
            self._takeback = None
            self._resigned_by = None
            self._phase = "active"
            snapshot = self._publish_unlocked("game_reset" if had_game else "game_started")
            self._notify_unlocked()
            return snapshot

    async def human_move(self, move_text: str | int) -> dict[str, object]:
        async with self._condition:
            self._require_legacy_mode_unlocked()
            self._apply_move_unlocked("human", move_text)
            event = "win" if self._phase == "won" else "draw" if self._phase == "draw" else "human_move"
            snapshot = self._publish_unlocked(event)
            self._notify_unlocked()
            return snapshot

    async def llm_move(self, move_text: str | int, wait: bool = True) -> dict[str, object]:
        async with self._condition:
            self._require_legacy_mode_unlocked()
            self._apply_move_unlocked("llm", move_text)
            event = "win" if self._phase == "won" else "draw" if self._phase == "draw" else "llm_move"
            snapshot = self._publish_unlocked(event)
            waited_revision = int(snapshot["revision"])
            self._notify_unlocked()
            return await self._wait_after_move_unlocked(waited_revision, "llm") if wait and self._phase == "active" else snapshot

    async def _wait_after_move_unlocked(self, revision: int, actor: Actor) -> dict[str, object]:
        while True:
            while self._revision <= revision:
                await self._condition.wait()
            result = self._wait_result_unlocked(revision, actor)
            if result is not None:
                return result
            revision = self._revision

    async def wait_for_llm(self, after_revision: int | None = None) -> dict[str, object]:
        async with self._condition:
            self._require_legacy_mode_unlocked()
            return await self._wait_for_actor_unlocked("llm", after_revision)

    async def _wait_for_actor_unlocked(self, actor: Actor, after_revision: int | None = None) -> dict[str, object]:
        if after_revision is None:
            current = copy.deepcopy(self._snapshot_unlocked())
            if self._is_actor_actionable(current, actor):
                return current
            revision = int(current["revision"])
        else:
            if after_revision < 0:
                raise GameError("invalid_revision", "Revision must be non-negative.", 422)
            result = self._wait_result_unlocked(after_revision, actor)
            if result is not None:
                return result
            revision = after_revision
        return await self._wait_after_move_unlocked(revision, actor)

    async def wait_for_player(self, color: str) -> dict[str, object]:
        async with self._condition:
            if color not in {"red", "yellow"}:
                raise InvalidPlayerColorError(color)
            while self._board is None:
                await self._condition.wait()
            actor = self._resolve_cli_actor_unlocked(color)
            return await self._wait_for_actor_unlocked(actor)

    async def player_move(self, color: str, move_text: str | int, wait: bool = True) -> dict[str, object]:
        async with self._condition:
            actor = self._resolve_cli_actor_unlocked(color)
            self._apply_move_unlocked(actor, move_text)
            event = "win" if self._phase == "won" else "draw" if self._phase == "draw" else f"{color}_move"
            snapshot = self._publish_unlocked(event)
            waited_revision = int(snapshot["revision"])
            self._notify_unlocked()
            return await self._wait_after_move_unlocked(waited_revision, actor) if wait and self._phase == "active" else snapshot

    async def takeback(self, actor: Actor, action: TakebackAction) -> dict[str, object]:
        if action not in {"request", "accept", "reject"}:
            raise TakebackStateError("no_pending")
        async with self._condition:
            if actor in {"human", "llm"}:
                self._require_legacy_mode_unlocked()
            return await self._takeback_unlocked(actor, action)

    async def player_takeback(self, color: str, action: TakebackAction) -> dict[str, object]:
        if action not in {"request", "accept", "reject"}:
            raise TakebackStateError("no_pending")
        async with self._condition:
            actor = self._resolve_cli_actor_unlocked(color)
            return await self._takeback_unlocked(actor, action)

    async def _takeback_unlocked(self, actor: Actor, action: TakebackAction) -> dict[str, object]:
        self._require_board_unlocked()
        pending = self._takeback
        if action == "request":
            if self._phase not in {"active", "won", "draw"}:
                raise TakebackStateError("inactive")
            if self._pending_takeback_unlocked():
                raise TakebackStateError("duplicate")
            own_index = next((index for index in range(len(self._move_history) - 1, -1, -1) if self._move_history[index].actor == actor), None)
            if own_index is None:
                raise TakebackStateError("no_move")
            target = self._move_history[own_index]
            request = TakebackData("pending", actor, target.ply, len(self._move_history) - own_index, own_index)
            self._takeback = request
            snapshot = self._publish_unlocked("takeback_requested")
            self._notify_unlocked()
            if actor == "human":
                return snapshot
            revision = int(snapshot["revision"])
            while self._takeback is request:
                await self._condition.wait()
            for response in self._snapshots_after_unlocked(revision):
                if response["event"] in {"takeback_accepted", "takeback_rejected", "game_reset", "human_resigned", "llm_resigned", "red_resigned", "yellow_resigned"}:
                    return response
            return copy.deepcopy(self._snapshot_unlocked())
        if pending is None or pending.state != "pending":
            raise TakebackStateError("no_pending")
        if pending.requester == actor:
            raise TakebackStateError("own_request")
        if action == "reject":
            self._takeback = TakebackData("rejected", pending.requester, pending.target_ply, 0, pending.target_index)
            snapshot = self._publish_unlocked("takeback_rejected")
            self._notify_unlocked()
            return snapshot
        position = self._positions_before[pending.target_index]
        self._require_board_unlocked().restore_state(position.board)
        self._move_history = list(position.history)
        self._positions_before = self._positions_before[:pending.target_index]
        self._last_move = self._move_history[-1] if self._move_history else None
        self._phase = "active"
        self._resigned_by = None
        self._takeback = TakebackData("accepted", pending.requester, pending.target_ply, pending.undone_plies, pending.target_index)
        snapshot = self._publish_unlocked("takeback_accepted")
        self._notify_unlocked()
        return snapshot

    async def resign(self, actor: Actor) -> dict[str, object]:
        async with self._condition:
            if actor in {"human", "llm"}:
                self._require_legacy_mode_unlocked()
            return self._resign_unlocked(actor)

    async def player_resign(self, color: str) -> dict[str, object]:
        async with self._condition:
            actor = self._resolve_cli_actor_unlocked(color)
            return self._resign_unlocked(actor)

    def _resign_unlocked(self, actor: Actor) -> dict[str, object]:
        self._require_board_unlocked()
        if self._phase in {"won", "draw", "resigned"}:
            raise GameOverError()
        self._takeback = None
        self._resigned_by = actor
        self._phase = "resigned"
        snapshot = self._publish_unlocked(f"{actor}_resigned")
        self._notify_unlocked()
        return snapshot

    async def event_stream(self) -> AsyncIterator[dict[str, object]]:
        revision = -1
        while True:
            async with self._condition:
                if self._revision <= revision:
                    await self._condition.wait()
                snapshots = self._snapshots_after_unlocked(revision)
            for snapshot in snapshots:
                revision = int(snapshot["revision"])
                yield snapshot


__all__ = [
    "Actor", "Color", "GameError", "GameManager", "GameMode", "IllegalMoveError",
    "InvalidGameSetupError", "InvalidPlayerColorError", "NoGameError", "PlayerNotCliError",
    "TakebackAction", "TakebackStateError", "WrongTurnError", "ColorRequiredError", "GameOverError",
]
