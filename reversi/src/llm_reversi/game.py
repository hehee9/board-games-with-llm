"""리버시 한 판의 규칙·대기·게임 상태를 관리한다."""

from __future__ import annotations

import asyncio
import copy
import uuid
from collections.abc import AsyncIterator
from dataclasses import dataclass, field
from typing import Literal

from .rules import (
    BoardState,
    Color,
    IllegalMoveError as RuleIllegalMoveError,
    InvalidCoordinateError,
    ReversiBoard,
    other_color,
)


Actor = Literal["human", "llm", "black", "white"]
Controller = Literal["human", "cli"]
GameMode = Literal["human_vs_llm", "cli_vs_cli"]
TakebackAction = Literal["request", "accept", "reject"]
Phase = Literal["setup", "active", "finished", "resigned"]


class GameError(Exception):
    """API에 반환할 게임 도메인 오류."""

    def __init__(self, code: str, message: str, status_code: int = 409) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.status_code = status_code


class NoGameError(GameError):
    """시작한 게임이 없는 상태에서 게임 동작을 요청했다."""

    def __init__(self) -> None:
        super().__init__("no_game", "No game is in progress. Start a game first.")


class WrongTurnError(GameError):
    """요청한 참가자의 차례가 아니다."""

    def __init__(self, actor: Actor) -> None:
        super().__init__("wrong_turn", f"It is not {actor}'s turn.")


class GameOverError(GameError):
    """이미 끝난 게임에 수를 두거나 동작을 요청했다."""

    def __init__(self) -> None:
        super().__init__("game_over", "The game is already over.")


class IllegalMoveError(GameError):
    """현재 보드에 둘 수 없는 리버시 수다."""

    def __init__(self, move: str) -> None:
        super().__init__("illegal_move", f"Illegal move: {move}", 422)


class TakebackStateError(GameError):
    """현재 상태와 맞지 않는 되돌리기 동작이다."""

    _MESSAGES = {
        "no_move": ("takeback_no_move", "There is no move by this player to take back."),
        "duplicate": ("takeback_pending", "A takeback request is already pending."),
        "own_request": ("takeback_own_request", "You cannot respond to your own takeback request."),
        "no_pending": ("takeback_no_pending", "There is no pending takeback request."),
        "pending_move": ("takeback_move_blocked", "Moves are disabled while a takeback request is pending."),
        "inactive": ("takeback_unavailable", "Takeback is available only during an active game."),
    }

    def __init__(self, reason: str) -> None:
        code, message = self._MESSAGES[reason]
        super().__init__(code, message)


class InvalidGameSetupError(GameError):
    """지원하지 않는 새 게임 설정이다."""

    def __init__(self, field_name: str, value: object) -> None:
        if field_name == "human_color":
            code, message = "invalid_color", f"Unsupported human color: {value}"
        else:
            code, message = "invalid_game_mode", f"Unsupported game mode: {value}"
        super().__init__(code, message, 422)


class InvalidPlayerColorError(GameError):
    """색상별 플레이어 경로에 잘못된 색을 지정했다."""

    def __init__(self, color: str) -> None:
        super().__init__("invalid_color", f"Unsupported player color: {color}", 422)


class PlayerNotCliError(GameError):
    """지정한 색의 참가자는 CLI가 아니다."""

    def __init__(self, color: str) -> None:
        super().__init__("player_not_cli", f"Player {color} is not controlled by a CLI.")


class ColorRequiredError(GameError):
    """CLI 대 CLI에서 색상별 경로가 필요한 요청이다."""

    def __init__(self) -> None:
        super().__init__("color_required", "Use a color-specific player endpoint for CLI-vs-CLI games.")


class InvalidRevisionError(GameError):
    """상태 대기 커서가 음수다."""

    def __init__(self) -> None:
        super().__init__("invalid_revision", "Revision must be non-negative.", 422)


@dataclass(frozen=True)
class MoveData:
    """수순 기록과 해당 수 이전의 복구 지점."""

    ply: int
    move: str
    color: Color
    actor: Actor
    flipped: tuple[str, ...]
    before_board: BoardState = field(repr=False)
    before_auto_passed_color: Color | None = field(repr=False)

    def as_dict(self) -> dict[str, object]:
        """수순 기록을 스냅샷용 딕셔너리로 바꾼다."""
        return {
            "ply": self.ply,
            "move": self.move,
            "color": self.color,
            "actor": self.actor,
            "flipped": list(self.flipped),
        }


@dataclass(frozen=True)
class TakebackData:
    """상대 응답을 기다리는 되돌리기 요청 또는 처리 결과."""

    state: Literal["pending", "accepted", "rejected"]
    requester: Actor
    target_ply: int
    moves_to_undo: int
    target_index: int = field(repr=False)
    target_board: BoardState = field(repr=False)
    target_auto_passed_color: Color | None = field(repr=False)

    def as_dict(self) -> dict[str, object]:
        """요청 정보를 공개 API 형식으로 바꾼다."""
        return {
            "state": self.state,
            "requester": self.requester,
            "target_ply": self.target_ply,
            "moves_to_undo": self.moves_to_undo if self.state != "rejected" else 0,
        }


class GameManager:
    """한 판의 상태와 CLI·브라우저 알림을 소유한다."""

    def __init__(self) -> None:
        self._condition = asyncio.Condition()
        self._board: ReversiBoard | None = None
        self._game_id: str | None = None
        self._game_mode: GameMode = "human_vs_llm"
        self._human_color: Color | None = None
        self._llm_color: Color | None = None
        self._players: dict[Color, dict[str, Actor | Controller | str | None]] = {}
        self._move_history: list[MoveData] = []
        self._last_move: MoveData | None = None
        self._auto_passed_color: Color | None = None
        self._takeback: TakebackData | None = None
        self._phase: Phase = "setup"
        self._resigned_by: Actor | None = None
        self._revision = 0
        self._event = "setup"
        self._published: list[dict[str, object]] = [self._snapshot_unlocked()]

    def _status_reason_unlocked(self) -> str:
        if self._phase == "setup":
            return "no_game"
        if self._phase == "active" and self._takeback is not None and self._takeback.state == "pending":
            return "takeback_pending"
        if self._phase == "active":
            return "in_progress"
        if self._phase == "finished":
            return "no_legal_moves"
        return "resignation"

    def _actor_color_unlocked(self, actor: Actor) -> Color | None:
        if actor in {"black", "white"}:
            return actor
        return self._human_color if actor == "human" else self._llm_color

    def _turn_unlocked(self) -> Actor | None:
        if self._board is None or self._phase != "active":
            return None
        if self._game_mode == "cli_vs_cli":
            return self._board.to_play
        return "human" if self._board.to_play == self._human_color else "llm"

    def _counts_unlocked(self) -> dict[str, int]:
        discs = self._board.discs if self._board is not None else {}
        return {color: sum(occupant == color for occupant in discs.values()) for color in ("black", "white")}

    def _winner_unlocked(self) -> Color | None:
        if self._phase == "resigned" and self._resigned_by is not None:
            resigned_color = self._actor_color_unlocked(self._resigned_by)
            return other_color(resigned_color) if resigned_color is not None else None
        if self._phase != "finished":
            return None
        counts = self._counts_unlocked()
        if counts["black"] == counts["white"]:
            return None
        return "black" if counts["black"] > counts["white"] else "white"

    def _snapshot_unlocked(self) -> dict[str, object]:
        board = self._board
        pending = self._takeback is not None and self._takeback.state == "pending"
        legal_moves = board.legal_moves() if board is not None and self._phase == "active" and not pending else []
        winner = self._winner_unlocked()
        return {
            "event": self._event,
            "game_id": self._game_id,
            "revision": self._revision,
            "status": self._phase,
            "status_reason": self._status_reason_unlocked(),
            "game_mode": self._game_mode,
            "players": copy.deepcopy(self._players),
            "human_color": self._human_color,
            "llm_color": self._llm_color,
            "turn": self._turn_unlocked(),
            "to_play": board.to_play if board is not None and self._phase == "active" else None,
            "board_size": 8,
            "discs": dict(board.discs) if board is not None else {},
            "counts": self._counts_unlocked(),
            "legal_moves": legal_moves,
            "auto_passed_color": self._auto_passed_color,
            "move_history": [move.as_dict() for move in self._move_history],
            "last_move": self._last_move.as_dict() if self._last_move is not None else None,
            "takeback": self._takeback.as_dict() if self._takeback is not None else None,
            "resigned_by": self._resigned_by,
            "winner": winner,
            "result": "Draw" if self._phase == "finished" and winner is None else winner,
        }

    def _publish_unlocked(self, event: str) -> dict[str, object]:
        self._event = event
        self._revision += 1
        snapshot = self._snapshot_unlocked()
        self._published.append(snapshot)
        return copy.deepcopy(snapshot)

    def _snapshots_after_unlocked(self, revision: int) -> list[dict[str, object]]:
        return [copy.deepcopy(snapshot) for snapshot in self._published if int(snapshot["revision"]) > revision]

    def _is_actor_actionable_unlocked(self, snapshot: dict[str, object], actor: Actor) -> bool:
        if snapshot["status"] in {"finished", "resigned"}:
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
            if self._is_actor_actionable_unlocked(snapshot, actor):
                return snapshot
        return None

    def _resolve_cli_actor_unlocked(self, color: str) -> Actor:
        if color not in {"black", "white"}:
            raise InvalidPlayerColorError(color)
        if self._board is None:
            raise NoGameError()
        player = self._players[color]
        if player["controller"] != "cli":
            raise PlayerNotCliError(color)
        return player["actor"]

    def _require_board_unlocked(self) -> ReversiBoard:
        if self._board is None:
            raise NoGameError()
        return self._board

    def _require_active_unlocked(self) -> ReversiBoard:
        board = self._require_board_unlocked()
        if self._phase != "active":
            raise GameOverError()
        if self._takeback is not None and self._takeback.state == "pending":
            raise TakebackStateError("pending_move")
        return board

    def _require_legacy_mode_unlocked(self) -> None:
        if self._game_mode == "cli_vs_cli":
            raise ColorRequiredError()

    def _actor_for_color_unlocked(self, color: Color) -> Actor:
        if self._game_mode == "cli_vs_cli":
            return color
        return "human" if color == self._human_color else "llm"

    def _require_actor_turn_unlocked(self, actor: Actor, board: ReversiBoard) -> Color:
        color = self._actor_color_unlocked(actor)
        if color is None or board.to_play != color:
            raise WrongTurnError(actor)
        return color

    def _apply_move_unlocked(self, actor: Actor, move_text: str) -> MoveData:
        board = self._require_active_unlocked()
        color = self._require_actor_turn_unlocked(actor, board)
        before_board = board.save_state()
        before_auto_passed_color = self._auto_passed_color
        try:
            result = board.play(move_text, color)
        except (RuleIllegalMoveError, InvalidCoordinateError):
            raise IllegalMoveError(move_text) from None
        move = MoveData(
            ply=len(self._move_history) + 1,
            move=result.move,
            color=color,
            actor=actor,
            flipped=tuple(result.flipped),
            before_board=before_board,
            before_auto_passed_color=before_auto_passed_color,
        )
        self._move_history.append(move)
        self._last_move = move
        opponent = other_color(color)
        self._auto_passed_color = None
        if not board.legal_moves(opponent):
            self._auto_passed_color = opponent
            if board.legal_moves(color):
                board.to_play = color
            else:
                self._phase = "finished"
        else:
            board.to_play = opponent
        return move

    async def snapshot(self) -> dict[str, object]:
        """현재 공개 상태를 반환한다."""
        async with self._condition:
            return copy.deepcopy(self._snapshot_unlocked())

    async def start_game(
        self,
        human_color: Color | None = None,
        *,
        game_mode: GameMode = "human_vs_llm",
        black_name: str | None = None,
        white_name: str | None = None,
    ) -> dict[str, object]:
        """사람 대 LLM 또는 CLI 대 CLI 게임을 시작하거나 초기화한다."""
        if game_mode not in {"human_vs_llm", "cli_vs_cli"}:
            raise InvalidGameSetupError("game_mode", game_mode)
        if game_mode == "human_vs_llm" and human_color not in {"black", "white"}:
            raise InvalidGameSetupError("human_color", human_color)
        names = {
            "black": black_name.strip() if black_name and black_name.strip() else None,
            "white": white_name.strip() if white_name and white_name.strip() else None,
        }
        async with self._condition:
            had_game = self._board is not None
            self._board = ReversiBoard()
            self._game_id = uuid.uuid4().hex
            self._game_mode = game_mode
            self._human_color = human_color if game_mode == "human_vs_llm" else None
            self._llm_color = other_color(human_color) if game_mode == "human_vs_llm" else None
            self._players = {
                color: {
                    "actor": (
                        color
                        if game_mode == "cli_vs_cli"
                        else "human"
                        if color == human_color
                        else "llm"
                    ),
                    "controller": (
                        "cli"
                        if game_mode == "cli_vs_cli" or color != human_color
                        else "human"
                    ),
                    "name": names[color],
                }
                for color in ("black", "white")
            }
            self._move_history = []
            self._last_move = None
            self._auto_passed_color = None
            self._takeback = None
            self._phase = "active"
            self._resigned_by = None
            snapshot = self._publish_unlocked("game_reset" if had_game else "game_started")
            self._condition.notify_all()
            return snapshot

    async def human_move(self, move_text: str) -> dict[str, object]:
        """브라우저 사람의 수를 적용한다."""
        async with self._condition:
            self._require_legacy_mode_unlocked()
            self._apply_move_unlocked("human", move_text)
            event = self._move_event_unlocked("human")
            snapshot = self._publish_unlocked(event)
            self._condition.notify_all()
            return snapshot

    async def llm_move(self, move_text: str, wait: bool = True) -> dict[str, object]:
        """LLM 수를 적용하고 다음 행동 기회까지 기다린다."""
        async with self._condition:
            self._require_legacy_mode_unlocked()
            self._apply_move_unlocked("llm", move_text)
            snapshot = self._publish_unlocked(self._move_event_unlocked("llm"))
            return await self._finish_move_request_unlocked("llm", snapshot, wait)

    async def wait_for_llm(self, after_revision: int | None = None) -> dict[str, object]:
        """LLM 차례, 종료 또는 새 대국을 기다린다."""
        async with self._condition:
            self._require_legacy_mode_unlocked()
            return await self._wait_for_actor_unlocked("llm", after_revision)

    async def wait_for_player(self, color: str, after_revision: int | None = None) -> dict[str, object]:
        """지정 색의 CLI 차례나 게임 시작을 기다린다."""
        if color not in {"black", "white"}:
            raise InvalidPlayerColorError(color)
        async with self._condition:
            revision = after_revision
            if self._board is None:
                revision = self._revision if revision is None else self._validate_revision(revision)
                while self._board is None:
                    await self._condition.wait()
            actor = self._resolve_cli_actor_unlocked(color)
            return await self._wait_for_actor_unlocked(actor, revision)

    async def player_move(self, color: str, move_text: str, wait: bool = True) -> dict[str, object]:
        """CLI 색상 참가자의 수를 적용하고 필요하면 다음 행동까지 기다린다."""
        async with self._condition:
            actor = self._resolve_cli_actor_unlocked(color)
            self._apply_move_unlocked(actor, move_text)
            snapshot = self._publish_unlocked(self._move_event_unlocked(color))
            return await self._finish_move_request_unlocked(actor, snapshot, wait)

    def _move_event_unlocked(self, actor: Actor) -> str:
        if self._phase == "finished":
            return "game_finished"
        if self._auto_passed_color is not None:
            return "automatic_pass"
        return f"{actor}_move"

    async def _finish_move_request_unlocked(
        self, actor: Actor, snapshot: dict[str, object], wait: bool
    ) -> dict[str, object]:
        waited_revision = int(snapshot["revision"])
        self._condition.notify_all()
        if not wait or snapshot["status"] != "active" or snapshot["turn"] == actor:
            return snapshot
        while True:
            while self._revision <= waited_revision:
                await self._condition.wait()
            result = self._wait_result_unlocked(waited_revision, actor)
            if result is not None:
                return result
            waited_revision = self._revision

    def _validate_revision(self, revision: int) -> int:
        if revision < 0:
            raise InvalidRevisionError()
        return revision

    async def _wait_for_actor_unlocked(
        self, actor: Actor, after_revision: int | None = None
    ) -> dict[str, object]:
        if after_revision is None:
            current = self._snapshot_unlocked()
            if self._is_actor_actionable_unlocked(current, actor):
                return copy.deepcopy(current)
            waited_revision = self._revision
        else:
            waited_revision = self._validate_revision(after_revision)
            result = self._wait_result_unlocked(waited_revision, actor)
            if result is not None:
                return result
        while True:
            while self._revision <= waited_revision:
                await self._condition.wait()
            result = self._wait_result_unlocked(waited_revision, actor)
            if result is not None:
                return result
            waited_revision = self._revision

    async def takeback(self, actor: Actor, action: TakebackAction) -> dict[str, object]:
        """되돌리기를 요청하거나 상대 요청에 응답한다."""
        async with self._condition:
            self._require_legacy_mode_unlocked()
            return await self._takeback_unlocked(actor, action)

    async def player_takeback(self, color: str, action: TakebackAction) -> dict[str, object]:
        """CLI 색상 참가자의 되돌리기를 처리한다."""
        async with self._condition:
            actor = self._resolve_cli_actor_unlocked(color)
            return await self._takeback_unlocked(actor, action)

    async def _takeback_unlocked(self, actor: Actor, action: TakebackAction) -> dict[str, object]:
        board = self._require_board_unlocked()
        if action not in {"request", "accept", "reject"}:
            raise GameError("Invalid takeback action.", 422)
        if self._phase != "active":
            raise TakebackStateError("inactive")
        pending = self._takeback
        if action == "request":
            if pending is not None and pending.state == "pending":
                raise TakebackStateError("duplicate")
            target_index = next(
                (index for index in range(len(self._move_history) - 1, -1, -1)
                 if self._move_history[index].actor == actor),
                None,
            )
            if target_index is None:
                raise TakebackStateError("no_move")
            target = self._move_history[target_index]
            request = TakebackData(
                state="pending",
                requester=actor,
                target_ply=target.ply,
                moves_to_undo=len(self._move_history) - target_index,
                target_index=target_index,
                target_board=target.before_board,
                target_auto_passed_color=target.before_auto_passed_color,
            )
            self._takeback = request
            snapshot = self._publish_unlocked("takeback_requested")
            self._condition.notify_all()
            if self._actor_controller_unlocked(actor) == "human":
                return snapshot
            while self._takeback is request:
                await self._condition.wait()
            return self._takeback_response_unlocked(int(snapshot["revision"]))

        if pending is None or pending.state != "pending":
            raise TakebackStateError("no_pending")
        if pending.requester == actor:
            raise TakebackStateError("own_request")
        if action == "reject":
            self._takeback = TakebackData(
                state="rejected",
                requester=pending.requester,
                target_ply=pending.target_ply,
                moves_to_undo=0,
                target_index=pending.target_index,
                target_board=pending.target_board,
                target_auto_passed_color=pending.target_auto_passed_color,
            )
            snapshot = self._publish_unlocked("takeback_rejected")
            self._condition.notify_all()
            return snapshot
        board.restore_state(pending.target_board)
        self._auto_passed_color = pending.target_auto_passed_color
        self._move_history = self._move_history[:pending.target_index]
        self._last_move = self._move_history[-1] if self._move_history else None
        self._takeback = TakebackData(
            state="accepted",
            requester=pending.requester,
            target_ply=pending.target_ply,
            moves_to_undo=pending.moves_to_undo,
            target_index=pending.target_index,
            target_board=pending.target_board,
            target_auto_passed_color=pending.target_auto_passed_color,
        )
        snapshot = self._publish_unlocked("takeback_accepted")
        self._condition.notify_all()
        return snapshot

    def _actor_controller_unlocked(self, actor: Actor) -> Controller:
        color = self._actor_color_unlocked(actor)
        return self._players[color]["controller"]

    def _takeback_response_unlocked(self, revision: int) -> dict[str, object]:
        snapshots = self._snapshots_after_unlocked(revision)
        for snapshot in snapshots:
            if snapshot["event"] == "game_reset":
                return snapshot
        for snapshot in snapshots:
            if snapshot["event"] in {"takeback_accepted", "takeback_rejected"} or str(snapshot["event"]).endswith("_resigned"):
                return snapshot
        return copy.deepcopy(self._snapshot_unlocked())

    async def resign(self, actor: Actor) -> dict[str, object]:
        """사임으로 진행 중인 게임을 끝낸다."""
        async with self._condition:
            self._require_legacy_mode_unlocked()
            return self._resign_unlocked(actor)

    async def player_resign(self, color: str) -> dict[str, object]:
        """CLI 색상 참가자의 사임을 적용한다."""
        async with self._condition:
            actor = self._resolve_cli_actor_unlocked(color)
            return self._resign_unlocked(actor)

    def _resign_unlocked(self, actor: Actor) -> dict[str, object]:
        self._require_board_unlocked()
        if self._phase != "active":
            raise GameOverError()
        self._takeback = None
        self._phase = "resigned"
        self._resigned_by = actor
        snapshot = self._publish_unlocked(f"{actor}_resigned")
        self._condition.notify_all()
        return snapshot

    async def event_stream(self) -> AsyncIterator[dict[str, object]]:
        """초기 스냅샷과 이후 상태 변경을 순서대로 내보낸다."""
        async with self._condition:
            initial = copy.deepcopy(self._snapshot_unlocked())
        yield initial
        seen_revision = int(initial["revision"])
        while True:
            async with self._condition:
                while self._revision <= seen_revision:
                    await self._condition.wait()
                pending = self._snapshots_after_unlocked(seen_revision)
            for snapshot in pending:
                seen_revision = int(snapshot["revision"])
                yield snapshot


__all__ = [
    "Actor",
    "ColorRequiredError",
    "GameError",
    "GameManager",
    "GameMode",
    "GameOverError",
    "IllegalMoveError",
    "InvalidGameSetupError",
    "InvalidPlayerColorError",
    "NoGameError",
    "PlayerNotCliError",
    "TakebackAction",
    "TakebackStateError",
    "WrongTurnError",
]
