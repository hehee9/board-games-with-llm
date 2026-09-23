"""한 개의 인메모리 바둑 게임과 비동기 상태 알림."""

from __future__ import annotations

import asyncio
import copy
import uuid
from collections.abc import AsyncIterator
from dataclasses import dataclass
from typing import Literal

from .rules import (
    Color,
    GoBoard,
    IllegalMoveError as RuleIllegalMoveError,
    InvalidCoordinateError,
    RuleState,
    normalize_coordinate,
)


Actor = Literal["human", "llm", "black", "white"]
Controller = Literal["human", "cli"]
GameMode = Literal["human_vs_llm", "cli_vs_cli"]
TakebackAction = Literal["request", "accept", "reject"]
ScoreAction = Literal["dead", "seki", "accept", "resume"]


class GameError(Exception):
    """클라이언트에 반환할 정상적인 게임 도메인 오류."""

    def __init__(self, code: str, message: str, status_code: int = 409) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.status_code = status_code


class NoGameError(GameError):
    """시작된 게임이 없는 상태에서 동작을 요청했다."""

    def __init__(self) -> None:
        super().__init__("no_game", "No game is in progress. Start a game first.")


class WrongTurnError(GameError):
    """현재 요청한 행위자의 차례가 아니다."""

    def __init__(self, actor: Actor) -> None:
        super().__init__("wrong_turn", f"It is not {actor}'s turn.")


class GameOverError(GameError):
    """이미 끝난 게임에 수를 두거나 동작을 요청했다."""

    def __init__(self) -> None:
        super().__init__("game_over", "The game is already over.")


class IllegalMoveError(GameError):
    """바둑 규칙에 맞지 않는 수를 요청했다."""

    def __init__(self, move: str) -> None:
        super().__init__("illegal_move", f"Illegal move: {move}", 422)


class TakebackStateError(GameError):
    """현재 상태에서 유효하지 않은 되돌리기 동작이다."""

    _MESSAGES = {
        "no_move": ("takeback_no_move", "There is no move by this actor to take back."),
        "duplicate": ("takeback_pending", "A takeback request is already pending."),
        "own_request": ("takeback_own_request", "You cannot respond to your own takeback request."),
        "no_pending": ("takeback_no_pending", "There is no pending takeback request."),
        "pending_move": ("takeback_move_blocked", "Moves are disabled while a takeback request is pending."),
        "inactive": ("takeback_unavailable", "Takeback is available only during an active game."),
    }

    def __init__(self, reason: str) -> None:
        code, message = self._MESSAGES[reason]
        super().__init__(code, message)


class ScoreStateError(GameError):
    """현재 상태에서 유효하지 않은 점수 동작이다."""

    def __init__(self, code: str, message: str, status_code: int = 409) -> None:
        super().__init__(code, message, status_code)


class InvalidGameSetupError(GameError):
    """게임 시작 요청의 설정값이 지원 범위를 벗어났다."""

    def __init__(self, field: str, value: object) -> None:
        if field == "human_color":
            code = "invalid_color"
            message = f"Unsupported human color: {value}"
        elif field == "game_mode":
            code = "invalid_game_mode"
            message = f"Unsupported game mode: {value}"
        else:
            code = "invalid_board_size"
            message = f"Unsupported board size: {value}"
        super().__init__(code, message, 422)


class InvalidPlayerColorError(GameError):
    """색상별 플레이어 경로의 색상이 유효하지 않다."""

    def __init__(self, color: str) -> None:
        super().__init__("invalid_color", f"Unsupported player color: {color}", 422)


class PlayerNotCliError(GameError):
    """선택한 색상이 CLI 플레이어로 제어되지 않는다."""

    def __init__(self, color: str) -> None:
        super().__init__("player_not_cli", f"Player {color} is not controlled by a CLI.")


class ColorRequiredError(GameError):
    """CLI 대 CLI 대국에서 기존 역할 경로를 사용했다."""

    def __init__(self) -> None:
        super().__init__("color_required", "Use a color-specific player endpoint for CLI-vs-CLI games.")


@dataclass(frozen=True)
class MoveData:
    """API 응답용 수 기록."""

    ply: int
    move: str
    color: Color
    actor: Actor
    captured: list[str]

    def as_dict(self) -> dict[str, object]:
        """수 기록을 딕셔너리로 변환."""
        return {
            "ply": self.ply,
            "move": self.move,
            "color": self.color,
            "actor": self.actor,
            "captured": list(self.captured),
        }


@dataclass(frozen=True)
class TakebackData:
    """되돌리기 요청과 처리 결과."""

    state: Literal["pending", "accepted", "rejected"]
    requester: Actor
    target_ply: int
    undone_plies: int

    def as_dict(self) -> dict[str, object]:
        """되돌리기 정보를 딕셔너리로 변환."""
        return {
            "state": self.state,
            "requester": self.requester,
            "target_ply": self.target_ply,
            "undone_plies": self.undone_plies,
        }


class GameManager:
    """바둑 규칙 상태와 대기 중인 클라이언트 알림을 소유."""

    def __init__(self) -> None:
        self._condition = asyncio.Condition()
        self._board: GoBoard | None = None
        self._game_id: str | None = None
        self._game_mode: GameMode = "human_vs_llm"
        self._human_color: Color | None = None
        self._llm_color: Color | None = None
        self._players: dict[Color, dict[str, Actor | Controller | str | None]] = {}
        self._move_history: list[MoveData] = []
        self._position_states: list[RuleState] = []
        self._last_move: MoveData | None = None
        self._takeback: TakebackData | None = None
        self._resigned_by: Actor | None = None
        self._phase: Literal["setup", "active", "scoring", "finished", "resigned", "draw"] = "setup"
        self._draw_reason: str | None = None
        self._score_groups: dict[str, frozenset[str]] = {}
        self._score_dead: set[str] = set()
        self._score_seki: set[str] = set()
        self._score_accepted: dict[Actor, bool] = {"human": False, "llm": False}
        self._revision = 0
        self._event = "setup"
        self._published: list[dict[str, object]] = [self._snapshot_unlocked()]

    def _status_reason_unlocked(self) -> str:
        if self._phase == "setup":
            return "no_game"
        if self._phase == "active":
            if self._takeback is not None and self._takeback.state == "pending":
                return "takeback_pending"
            return "in_progress"
        if self._phase == "scoring":
            return "two_passes"
        if self._phase == "finished":
            return "score_agreed"
        if self._phase == "resigned":
            return "resignation"
        return self._draw_reason or "repetition"

    def _turn_unlocked(self) -> Actor | None:
        if self._board is None or self._phase != "active":
            return None
        if self._game_mode == "cli_vs_cli":
            return self._board.to_play
        return "human" if self._board.to_play == self._human_color else "llm"

    def _score_snapshot_unlocked(self) -> dict[str, object] | None:
        if self._board is None or self._phase not in {"scoring", "finished"}:
            return None
        score = self._board.score(self._score_dead, self._score_seki)
        score["accepted"] = dict(self._score_accepted)
        return score

    def _snapshot_unlocked(self) -> dict[str, object]:
        board = self._board
        stones = dict(board.stones) if board is not None else {}
        to_play = board.to_play if board is not None else None
        legal_moves: list[str] = []
        if board is not None and self._phase == "active":
            pending = self._takeback is not None and self._takeback.state == "pending"
            if not pending:
                legal_moves = board.legal_moves()
        captures = dict(board.captures) if board is not None else {"black": 0, "white": 0}
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
            "to_play": to_play,
            "board_size": board.size if board is not None else 19,
            "komi": 6.5,
            "stones": stones,
            "legal_moves": legal_moves,
            "captures": captures,
            "consecutive_passes": board.consecutive_passes if board is not None else 0,
            "move_history": [move.as_dict() for move in self._move_history],
            "last_move": self._last_move.as_dict() if self._last_move else None,
            "takeback": self._takeback.as_dict() if self._takeback else None,
            "resigned_by": self._resigned_by,
            "result": self._result_unlocked(),
            "score": self._score_snapshot_unlocked(),
        }

    def _result_unlocked(self) -> str | None:
        if self._phase == "resigned" and self._resigned_by is not None:
            resigned_color = self._actor_color_unlocked(self._resigned_by)
            winner = "white" if resigned_color == "black" else "black"
            return "B+R" if winner == "black" else "W+R"
        if self._phase == "finished":
            score = self._score_snapshot_unlocked()
            if score is None:
                return None
            black = float(score["totals"]["black"])
            white = float(score["totals"]["white"])
            if black == white:
                return "Draw"
            winner = "B" if black > white else "W"
            margin = abs(black - white)
            return f"{winner}+{margin:g}"
        if self._phase == "draw":
            return "Draw"
        return None

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
        if self._game_mode == "cli_vs_cli":
            return actor if actor in {"black", "white"} else None
        return self._human_color if actor == "human" else self._llm_color

    def _actor_keys_unlocked(self) -> tuple[Actor, Actor]:
        if self._game_mode == "cli_vs_cli":
            return "black", "white"
        return "human", "llm"

    def _is_actor_actionable(self, snapshot: dict[str, object], actor: Actor) -> bool:
        status = snapshot["status"]
        if status in {"finished", "draw", "resigned"}:
            return True
        takeback = snapshot["takeback"]
        pending = isinstance(takeback, dict) and takeback["state"] == "pending"
        if pending:
            return takeback["requester"] != actor
        if status == "active":
            return snapshot["turn"] == actor
        if status == "scoring":
            accepted = snapshot["score"]["accepted"]
            return not accepted[actor]
        return False

    def _is_llm_actionable(self, snapshot: dict[str, object]) -> bool:
        return self._is_actor_actionable(snapshot, "llm")

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
        if color not in {"black", "white"}:
            raise InvalidPlayerColorError(color)
        if color not in self._players or self._players[color]["controller"] != "cli":
            raise PlayerNotCliError(color)
        player = self._players[color]
        return player["actor"]

    def _require_board_unlocked(self) -> GoBoard:
        if self._board is None:
            raise NoGameError()
        return self._board

    def _require_active_unlocked(self) -> GoBoard:
        board = self._require_board_unlocked()
        if self._phase != "active":
            raise GameOverError()
        if self._takeback is not None and self._takeback.state == "pending":
            raise TakebackStateError("pending_move")
        return board

    def _require_actor_turn_unlocked(self, actor: Actor, board: GoBoard) -> Color:
        expected = self._actor_color_unlocked(actor)
        if expected is None or board.to_play != expected:
            raise WrongTurnError(actor)
        return expected

    def _apply_move_unlocked(self, actor: Actor, move_text: str) -> MoveData:
        board = self._require_active_unlocked()
        color = self._require_actor_turn_unlocked(actor, board)
        state_before = board.save_state()
        try:
            result = board.play(move_text, color)
        except (RuleIllegalMoveError, InvalidCoordinateError):
            raise IllegalMoveError(move_text) from None
        self._position_states.append(state_before)
        move = MoveData(len(self._move_history) + 1, result.move, result.color, actor, result.captured)
        self._move_history.append(move)
        self._last_move = move
        if self._takeback is not None and self._takeback.state != "pending":
            self._takeback = None
        if board.consecutive_passes >= 2:
            self._phase = "scoring"
            self._score_groups = {
                coordinate: frozenset(group)
                for group in board.original_groups()
                for coordinate in group
            }
            self._score_dead.clear()
            self._score_seki.clear()
            self._score_accepted = {actor_key: False for actor_key in self._actor_keys_unlocked()}
        elif board.is_repetition_draw:
            self._phase = "draw"
            self._draw_reason = "repetition"
        return move

    async def snapshot(self) -> dict[str, object]:
        """현재 게임 스냅샷 반환."""
        async with self._condition:
            return copy.deepcopy(self._snapshot_unlocked())

    async def start_game(
        self,
        human_color: Color | None = None,
        board_size: int = 19,
        *,
        game_mode: GameMode = "human_vs_llm",
        black_name: str | None = None,
        white_name: str | None = None,
    ) -> dict[str, object]:
        """지정한 대국 모드·판 크기로 새 게임 시작."""
        if game_mode not in {"human_vs_llm", "cli_vs_cli"}:
            raise InvalidGameSetupError("game_mode", game_mode)
        if game_mode == "human_vs_llm" and human_color not in {"black", "white"}:
            raise InvalidGameSetupError("human_color", human_color)
        if board_size not in {9, 13, 19}:
            raise InvalidGameSetupError("board_size", board_size)
        normalized_names = {
            "black": black_name.strip() if black_name and black_name.strip() else None,
            "white": white_name.strip() if white_name and white_name.strip() else None,
        }
        async with self._condition:
            had_game = self._board is not None
            self._board = GoBoard(board_size)
            self._game_id = uuid.uuid4().hex
            self._game_mode = game_mode
            self._human_color = human_color if game_mode == "human_vs_llm" else None
            self._llm_color = (
                "white" if human_color == "black" else "black"
            ) if game_mode == "human_vs_llm" else None
            if game_mode == "cli_vs_cli":
                self._players = {
                    "black": {"actor": "black", "controller": "cli", "name": normalized_names["black"]},
                    "white": {"actor": "white", "controller": "cli", "name": normalized_names["white"]},
                }
            else:
                self._players = {
                    "black": {
                        "actor": "human" if human_color == "black" else "llm",
                        "controller": "human" if human_color == "black" else "cli",
                        "name": normalized_names["black"],
                    },
                    "white": {
                        "actor": "human" if human_color == "white" else "llm",
                        "controller": "human" if human_color == "white" else "cli",
                        "name": normalized_names["white"],
                    },
                }
            self._move_history = []
            self._position_states = []
            self._last_move = None
            self._takeback = None
            self._resigned_by = None
            self._phase = "active"
            self._draw_reason = None
            self._score_groups = {}
            self._score_dead.clear()
            self._score_seki.clear()
            self._score_accepted = {actor: False for actor in self._actor_keys_unlocked()}
            event = "game_reset" if had_game else "game_started"
            snapshot = self._publish_unlocked(event)
            self._notify_unlocked()
            return snapshot

    async def human_move(self, move_text: str) -> dict[str, object]:
        """사람의 수를 적용."""
        async with self._condition:
            self._require_legacy_mode_unlocked()
            self._apply_move_unlocked("human", move_text)
            event = "scoring_started" if self._phase == "scoring" else "draw" if self._phase == "draw" else "human_move"
            snapshot = self._publish_unlocked(event)
            self._notify_unlocked()
            return snapshot

    async def llm_move(self, move_text: str, wait: bool = True) -> dict[str, object]:
        """LLM의 수를 적용하고 필요하면 다음 관련 상태까지 대기."""
        async with self._condition:
            self._require_legacy_mode_unlocked()
            self._apply_move_unlocked("llm", move_text)
            event = "scoring_started" if self._phase == "scoring" else "draw" if self._phase == "draw" else "llm_move"
            snapshot = self._publish_unlocked(event)
            waited_revision = int(snapshot["revision"])
            self._notify_unlocked()
            if not wait or snapshot["status"] != "active":
                return snapshot
            while True:
                while self._revision <= waited_revision:
                    await self._condition.wait()
                result = self._wait_result_unlocked(waited_revision, "llm")
                if result is not None:
                    return result
                waited_revision = self._revision

    async def wait_for_llm(self, after_revision: int | None = None) -> dict[str, object]:
        """LLM 차례, 점수 동작, 종료 또는 초기화를 대기."""
        async with self._condition:
            self._require_legacy_mode_unlocked()
            return await self._wait_for_actor_unlocked("llm", after_revision)

    async def _wait_for_actor_unlocked(
        self, actor: Actor, after_revision: int | None = None
    ) -> dict[str, object]:
        """행위자 차례, 상대 동작, 종료 또는 초기화를 대기."""
        if after_revision is None:
            current = self._current_snapshot_unlocked()
            if self._is_actor_actionable(current, actor):
                return current
            waited_revision = int(current["revision"])
        else:
            if after_revision < 0:
                raise ScoreStateError("invalid_revision", "Revision must be non-negative.", 422)
            result = self._wait_result_unlocked(after_revision, actor)
            if result is not None:
                return result
            waited_revision = after_revision
        while True:
            while self._revision <= waited_revision:
                await self._condition.wait()
            result = self._wait_result_unlocked(waited_revision, actor)
            if result is not None:
                return result
            waited_revision = self._revision

    async def wait_for_player(self, color: str, after_revision: int | None = None) -> dict[str, object]:
        """CLI 색상 플레이어가 의미 있는 새 상태를 대기."""
        async with self._condition:
            actor = self._resolve_cli_actor_unlocked(color)
            return await self._wait_for_actor_unlocked(actor, after_revision)

    async def player_move(self, color: str, move_text: str, wait: bool = True) -> dict[str, object]:
        """CLI 색상 플레이어의 수를 적용하고 필요하면 다음 상태까지 대기."""
        async with self._condition:
            actor = self._resolve_cli_actor_unlocked(color)
            self._apply_move_unlocked(actor, move_text)
            event = "scoring_started" if self._phase == "scoring" else "draw" if self._phase == "draw" else f"{color}_move"
            snapshot = self._publish_unlocked(event)
            waited_revision = int(snapshot["revision"])
            self._notify_unlocked()
            if not wait or snapshot["status"] != "active":
                return snapshot
            while True:
                while self._revision <= waited_revision:
                    await self._condition.wait()
                result = self._wait_result_unlocked(waited_revision, actor)
                if result is not None:
                    return result
                waited_revision = self._revision

    def _current_snapshot_unlocked(self) -> dict[str, object]:
        return copy.deepcopy(self._snapshot_unlocked())

    async def takeback(self, actor: Actor, action: TakebackAction) -> dict[str, object]:
        """되돌리기를 요청하거나 상대 요청에 응답."""
        if action not in {"request", "accept", "reject"}:
            raise TakebackStateError("no_pending")
        async with self._condition:
            if actor in {"human", "llm"}:
                self._require_legacy_mode_unlocked()
            return await self._takeback_unlocked(actor, action)

    async def player_takeback(self, color: str, action: TakebackAction) -> dict[str, object]:
        """CLI 색상 플레이어의 되돌리기 요청 또는 응답."""
        if action not in {"request", "accept", "reject"}:
            raise TakebackStateError("no_pending")
        async with self._condition:
            actor = self._resolve_cli_actor_unlocked(color)
            return await self._takeback_unlocked(actor, action)

    async def _takeback_unlocked(self, actor: Actor, action: TakebackAction) -> dict[str, object]:
        """잠금 보유 상태에서 되돌리기 동작 처리."""
        board = self._require_board_unlocked()
        if self._phase != "active":
            raise TakebackStateError("inactive")
        pending = self._takeback
        if action == "request":
            if pending is not None and pending.state == "pending":
                raise TakebackStateError("duplicate")
            own_index = next(
                (index for index in range(len(self._move_history) - 1, -1, -1) if self._move_history[index].actor == actor),
                None,
            )
            if own_index is None:
                raise TakebackStateError("no_move")
            undone_plies = 1 if own_index == len(self._move_history) - 1 else 2
            request = TakebackData("pending", actor, self._move_history[own_index].ply, undone_plies)
            self._takeback = request
            snapshot = self._publish_unlocked("takeback_requested")
            self._notify_unlocked()
            if actor == "human":
                return snapshot
            while self._takeback is request:
                await self._condition.wait()
            responses = {
                "takeback_accepted",
                "takeback_rejected",
                "human_resigned",
                "llm_resigned",
                "black_resigned",
                "white_resigned",
                "game_reset",
            }
            for response in self._snapshots_after_unlocked(int(snapshot["revision"])):
                if response["event"] in responses:
                    return response
            return self._current_snapshot_unlocked()
        if pending is None or pending.state != "pending":
            raise TakebackStateError("no_pending")
        if pending.requester == actor:
            raise TakebackStateError("own_request")
        if action == "reject":
            self._takeback = TakebackData("rejected", pending.requester, pending.target_ply, 0)
            snapshot = self._publish_unlocked("takeback_rejected")
            self._notify_unlocked()
            return snapshot
        target_index = pending.target_ply - 1
        state = self._position_states[target_index]
        board.restore_state(state)
        self._move_history = self._move_history[:target_index]
        self._position_states = self._position_states[:target_index]
        self._last_move = self._move_history[-1] if self._move_history else None
        self._takeback = TakebackData("accepted", pending.requester, pending.target_ply, pending.undone_plies)
        snapshot = self._publish_unlocked("takeback_accepted")
        self._notify_unlocked()
        return snapshot

    async def resign(self, actor: Actor) -> dict[str, object]:
        """행위자의 사임으로 게임 종료."""
        async with self._condition:
            if actor in {"human", "llm"}:
                self._require_legacy_mode_unlocked()
            return self._resign_unlocked(actor)

    async def player_resign(self, color: str) -> dict[str, object]:
        """CLI 색상 플레이어의 사임 처리."""
        async with self._condition:
            actor = self._resolve_cli_actor_unlocked(color)
            return self._resign_unlocked(actor)

    def _resign_unlocked(self, actor: Actor) -> dict[str, object]:
        """잠금 보유 상태에서 사임 처리."""
        self._require_board_unlocked()
        if self._phase in {"finished", "draw", "resigned"}:
            raise GameOverError()
        self._takeback = None
        self._resigned_by = actor
        self._phase = "resigned"
        snapshot = self._publish_unlocked(f"{actor}_resigned")
        self._notify_unlocked()
        return snapshot

    async def score(
        self,
        actor: Actor,
        action: ScoreAction,
        point: str | None = None,
        revision: int | None = None,
    ) -> dict[str, object]:
        """죽은 돌·세키 표시, 합의 또는 점수 재개 처리."""
        if action not in {"dead", "seki", "accept", "resume"}:
            raise ScoreStateError("score_action_invalid", "Unsupported score action.", 422)
        async with self._condition:
            if actor in {"human", "llm"}:
                self._require_legacy_mode_unlocked()
            return self._apply_score_unlocked(actor, action, point, revision, require_revision=False)

    async def player_score(
        self,
        color: str,
        action: ScoreAction,
        point: str | None = None,
        revision: int | None = None,
    ) -> dict[str, object]:
        """CLI 색상 플레이어의 계가 동작 처리."""
        if action not in {"dead", "seki", "accept", "resume"}:
            raise ScoreStateError("score_action_invalid", "Unsupported score action.", 422)
        async with self._condition:
            actor = self._resolve_cli_actor_unlocked(color)
            return self._apply_score_unlocked(actor, action, point, revision, require_revision=True)

    def _apply_score_unlocked(
        self,
        actor: Actor,
        action: ScoreAction,
        point: str | None,
        revision: int | None,
        *,
        require_revision: bool,
    ) -> dict[str, object]:
        """잠금 보유 상태에서 계가 동작 처리."""
        board = self._require_board_unlocked()
        if self._phase in {"finished", "draw", "resigned"}:
            raise GameOverError()
        if self._phase != "scoring":
            raise ScoreStateError("scoring_not_active", "Scoring is not active.")
        if action in {"dead", "seki"}:
            if require_revision:
                self._require_score_revision(revision)
            if point is None:
                raise ScoreStateError("score_point_required", "A stone coordinate is required.", 422)
            try:
                normalized = normalize_coordinate(point, board.size)
            except InvalidCoordinateError:
                raise ScoreStateError("score_point_invalid", f"Invalid score coordinate: {point}", 422) from None
            group = self._score_groups.get(normalized)
            if group is None:
                raise ScoreStateError("score_point_invalid", "The coordinate does not contain a stone.", 422)
            target = self._score_dead if action == "dead" else self._score_seki
            other = self._score_seki if action == "dead" else self._score_dead
            if group.issubset(target):
                target.difference_update(group)
            else:
                target.update(group)
                other.difference_update(group)
            self._score_accepted = {actor_key: False for actor_key in self._actor_keys_unlocked()}
            snapshot = self._publish_unlocked("score_updated")
            self._notify_unlocked()
            return snapshot
        if action == "accept":
            self._require_score_revision(revision)
            self._score_accepted[actor] = True
            first_actor, second_actor = self._actor_keys_unlocked()
            if self._score_accepted[first_actor] and self._score_accepted[second_actor]:
                self._phase = "finished"
                event = "score_finished"
            else:
                event = "score_accepted"
            snapshot = self._publish_unlocked(event)
            self._notify_unlocked()
            return snapshot
        self._phase = "active"
        board.consecutive_passes = 0
        self._score_groups = {}
        self._score_dead.clear()
        self._score_seki.clear()
        self._score_accepted = {actor_key: False for actor_key in self._actor_keys_unlocked()}
        snapshot = self._publish_unlocked("score_resumed")
        self._notify_unlocked()
        return snapshot

    def _require_score_revision(self, revision: int | None) -> None:
        """계가 변경·수락 요청의 최신 revision 검증."""
        if revision is None:
            raise ScoreStateError("score_revision_required", "Revision is required to accept a score.", 422)
        if revision != self._revision:
            raise ScoreStateError("stale_revision", "The score revision is stale.")

    async def event_stream(self) -> AsyncIterator[dict[str, object]]:
        """초기 스냅샷부터 상태 변경을 순서대로 내보냄."""
        async with self._condition:
            initial = self._current_snapshot_unlocked()
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
    "Controller",
    "GameError",
    "GameManager",
    "GameOverError",
    "IllegalMoveError",
    "InvalidGameSetupError",
    "InvalidPlayerColorError",
    "NoGameError",
    "PlayerNotCliError",
    "ScoreAction",
    "ScoreStateError",
    "TakebackAction",
    "TakebackStateError",
    "WrongTurnError",
    "GameMode",
]
