"""로컬 사람 대 언어 모델 바둑 서버용 명령줄 인터페이스."""

from __future__ import annotations

import argparse
import sys
import threading
import time
import webbrowser
from collections.abc import Sequence
from typing import Any

import httpx
import uvicorn


HOST = "127.0.0.1"
PORT = 8766
BASE_URL = f"http://{HOST}:{PORT}"
_SHORT_TIMEOUT = httpx.Timeout(1.5, connect=0.6)
_WAIT_TIMEOUT = httpx.Timeout(connect=0.6, read=None, write=1.5, pool=1.5)
_COLUMNS = "ABCDEFGHJKLMNOPQRST"
_ILLEGAL_MOVE_PREFIX = "불법 수입니다:"
_SERVER_ERROR_TRANSLATIONS = {
    "진행 중인 게임이 없습니다. 먼저 게임을 시작하세요.": "No game is in progress. Start a game first.",
    "현재 사람 차례가 아닙니다.": "It is not the human's turn.",
    "현재 LLM 차례가 아닙니다.": "It is not the LLM's turn.",
    "게임이 이미 끝났습니다.": "The game has already ended.",
    "되돌릴 자신의 수가 없습니다.": "There is no previous move by this player to take back.",
    "이미 되돌리기 요청이 대기 중입니다.": "A takeback request is already pending.",
    "자신이 요청한 되돌리기에 응답할 수 없습니다.": "You cannot respond to your own takeback request.",
    "대기 중인 되돌리기 요청이 없습니다.": "There is no pending takeback request.",
    "되돌리기 요청이 대기 중일 때는 수를 둘 수 없습니다.": "Moves are disabled while a takeback request is pending.",
}
_SERVER_ERROR_CODE_TRANSLATIONS = {
    "color_required": "A player color is required for this command.",
    "player_not_cli": "The selected player is not controlled by the CLI.",
}


def _help_text() -> str:
    """Markdown 형식의 바둑 명령 도움말을 반환한다."""
    return """# baduk

Control a local human-vs-LLM or CLI-vs-CLI baduk game.

## Usage

```text
baduk start
baduk status
baduk --color black|white status
baduk wait [--after-revision N]
baduk move MOVE [--no-wait]
baduk takeback request|accept|reject
baduk resign
baduk score dead POINT [--revision N]
baduk score seki POINT [--revision N]
baduk score accept [--revision N]
baduk score resume
```

For CLI-vs-CLI participant commands, put `--color black` or `--color white`
before the subcommand. For example:

```text
baduk --color black wait [--after-revision N]
baduk --color black move MOVE [--no-wait]
baduk --color black takeback request|accept|reject
baduk --color black resign
baduk --color black score dead POINT --revision N
baduk --color black score seki POINT --revision N
baduk --color black score accept --revision N
baduk --color black score resume
```

Coordinates use uppercase Go notation (`A-T`, skipping `I`), and `pass` is a
valid move. The default move command waits for the opponent response.

In CLI-vs-CLI mode, run two independent AI sessions. Include that session's
`--color` before every participant command. Each session keeps its own color;
there is no shared session-global setting. There is one pending wait per
session; reset events require a fresh `status`, and takebacks are handled by
the opponent. Re-read and review after a revision conflict, and resume after
the sessions disagree on the score; two acceptances finish scoring. The CLI
does not launch the other AI.
"""


def _english_server_error(detail: object, status_code: int) -> str:
    """서버 오류 상세를 CLI용 영어 문구로 변환한다."""
    code: object = None
    if isinstance(detail, dict):
        code = detail.get("code")
        message = detail.get("message")
        if isinstance(message, str):
            detail = message
    if isinstance(detail, str):
        translated = _SERVER_ERROR_TRANSLATIONS.get(detail)
        if translated is not None:
            return translated
        if detail.startswith(_ILLEGAL_MOVE_PREFIX):
            move = detail.removeprefix(_ILLEGAL_MOVE_PREFIX).strip()
            return f"Illegal move: {move}"
        if detail.isascii():
            return detail
    if isinstance(code, str):
        translated = _SERVER_ERROR_CODE_TRANSLATIONS.get(code)
        if translated is not None:
            return translated
    return f"Server request failed (HTTP {status_code})."


def _request(
    method: str,
    path: str,
    payload: dict[str, Any] | None = None,
    *,
    wait_for_event: bool = False,
) -> tuple[dict[str, Any] | None, int]:
    """로컬 API를 호출하고 도메인 오류를 Markdown으로 출력한다."""
    timeout = _WAIT_TIMEOUT if wait_for_event else _SHORT_TIMEOUT
    try:
        with httpx.Client(base_url=BASE_URL, timeout=timeout) as client:
            response = client.request(method, path, json=payload)
    except httpx.RequestError:
        print(f"**Error:** Unable to connect to the server at `{BASE_URL}`.")
        return None, 1

    if response.is_success:
        try:
            body = response.json()
        except ValueError:
            print("**Error:** The server returned invalid JSON.")
            return None, 1
        if not isinstance(body, dict):
            print("**Error:** The server returned an invalid snapshot.")
            return None, 1
        return body, 0

    try:
        body = response.json()
    except ValueError:
        print(f"**Error:** Server request failed (HTTP {response.status_code}).")
        return None, 1
    detail = body.get("detail") if isinstance(body, dict) else None
    print(f"**Error:** {_english_server_error(detail, response.status_code)}")
    return None, 1


def _render_board(stones: dict[str, str], board_size: int) -> list[str]:
    """바둑판을 흑 X, 백 O 표기의 ASCII Markdown으로 렌더링한다."""
    columns = _COLUMNS[:board_size]
    row_label_width = len(str(board_size))
    lines = ["**Board:**", "", "```text", f"{'':>{row_label_width}}  {' '.join(columns)}"]
    for row in range(board_size, 0, -1):
        cells = []
        for column in columns:
            stone = stones.get(f"{column}{row}")
            cells.append("X" if stone == "black" else "O" if stone == "white" else ".")
        rendered = " ".join(cells)
        lines.append(f"{row:>{row_label_width}}  {rendered}")
    lines.extend([f"{'':>{row_label_width}}  {' '.join(columns)}", "```"])
    return lines


def _render_list(values: object) -> str:
    """좌표 목록을 짧은 인라인 Markdown으로 렌더링한다."""
    if not isinstance(values, list) or not values:
        return "—"
    return " ".join(f"`{value}`" for value in values)


def _render_flag(value: object) -> str:
    """불리언 값을 짧은 영어 표기로 렌더링한다."""
    if value is True:
        return "Yes"
    if value is False:
        return "No"
    return "—"


def _participant_path(color: str | None, resource: str) -> str:
    """참가자 색상에 맞는 API 경로를 반환한다."""
    if color is None:
        return f"/api/llm/{resource}"
    return f"/api/players/{color}/{resource}"


def _player_label(snapshot: dict[str, Any], color: str) -> str:
    """참가자 이름과 색상을 영어 표시명으로 결합한다."""
    players = snapshot["players"]
    player = players[color]
    name = player["name"]
    if name is not None:
        identity = str(name)
    elif snapshot["game_mode"] == "cli_vs_cli":
        identity = color.title()
    else:
        actor = player["actor"]
        if actor == "human":
            identity = "Human"
        elif actor == "llm":
            identity = "LLM"
        else:
            identity = str(actor).title()
    return f"{identity} ({color})"


def _actor_label(snapshot: dict[str, Any], actor: object, color: object = None) -> str:
    """스냅샷 행위자를 참가자 표시명으로 변환한다."""
    player_color = color if color == "black" or color == "white" else None
    if player_color is None:
        for candidate_color, player in snapshot["players"].items():
            if player["actor"] == actor:
                player_color = candidate_color
                break
    if player_color == "black" or player_color == "white":
        return _player_label(snapshot, player_color)
    return str(actor or "—").title()


def _render_score(score: object, snapshot: dict[str, Any]) -> list[str]:
    """스코어 정보를 Markdown으로 렌더링한다."""
    if not isinstance(score, dict):
        return ["**Score:** —"]
    accepted = score.get("accepted")
    territory = score.get("territory")
    prisoners = score.get("prisoners")
    totals = score.get("totals")
    players = snapshot["players"]
    black_player = players["black"]
    white_player = players["white"]
    accepted_black_key = black_player["actor"] if black_player["actor"] in {"human", "llm"} else "black"
    accepted_white_key = white_player["actor"] if white_player["actor"] in {"human", "llm"} else "white"
    accepted_black = accepted.get(accepted_black_key) if isinstance(accepted, dict) else None
    accepted_white = accepted.get(accepted_white_key) if isinstance(accepted, dict) else None
    accepted_text = (
        f"- Accepted: {_player_label(snapshot, 'black')} `{_render_flag(accepted_black)}` · "
        f"{_player_label(snapshot, 'white')} `{_render_flag(accepted_white)}`"
    )
    territory_black = territory.get("black") if isinstance(territory, dict) else None
    territory_white = territory.get("white") if isinstance(territory, dict) else None
    prisoners_black = prisoners.get("black") if isinstance(prisoners, dict) else None
    prisoners_white = prisoners.get("white") if isinstance(prisoners, dict) else None
    totals_black = totals.get("black") if isinstance(totals, dict) else None
    totals_white = totals.get("white") if isinstance(totals, dict) else None
    return [
        "**Score:**",
        f"- Dead: {_render_list(score.get('dead'))}",
        f"- Seki: {_render_list(score.get('seki'))}",
        accepted_text,
        f"- Territory: Black {_render_list(territory_black)} · White {_render_list(territory_white)}",
        f"- Prisoners: Black `{prisoners_black}` · White `{prisoners_white}`",
        f"- Totals: Black `{totals_black}` · White `{totals_white}`",
    ]


def render_snapshot(snapshot: dict[str, Any]) -> str:
    """게임 스냅샷을 문서형 Markdown으로 렌더링한다."""
    lines = [f"**Event:** {snapshot.get('event', 'unknown')}"]
    event = snapshot.get("event")
    takeback = snapshot.get("takeback")
    if isinstance(takeback, dict):
        requester = takeback.get("requester")
        requester_label = _actor_label(snapshot, requester)
        target_ply = takeback.get("target_ply")
        if event == "takeback_requested":
            lines.append(
                f"**Takeback request:** {requester_label} requested a takeback at ply {target_ply}."
            )
        elif event in {"takeback_accepted", "takeback_rejected"}:
            requester_color = requester if requester == "black" or requester == "white" else None
            if requester_color is None:
                for candidate_color, player in snapshot["players"].items():
                    if player["actor"] == requester:
                        requester_color = candidate_color
                        break
            responder_color = "white" if requester_color == "black" else "black" if requester_color == "white" else None
            responder = _player_label(snapshot, responder_color) if responder_color else "Opponent"
            if event == "takeback_accepted":
                undone_plies = takeback.get("undone_plies", 0)
                unit = "ply" if undone_plies == 1 else "plies"
                lines.append(
                    f"**Takeback result:** {responder} accepted the takeback for {requester_label}; "
                    f"{undone_plies} {unit} undone."
                )
            else:
                lines.append(
                    f"**Takeback result:** {responder} rejected the takeback for {requester_label}."
                )
    if event in {"human_resigned", "llm_resigned", "black_resigned", "white_resigned"}:
        actor = snapshot.get("resigned_by")
        if actor is None:
            actor = "human" if event == "human_resigned" else "llm" if event == "llm_resigned" else event.removesuffix("_resigned")
        lines.append(f"**Resignation:** {_actor_label(snapshot, actor)} resigned.")
    last_move = snapshot.get("last_move")
    if isinstance(last_move, dict):
        actor = last_move.get("actor")
        actor_label = _actor_label(snapshot, actor, last_move.get("color"))
        label = f"{actor_label} move"
        move = last_move.get("move", "?")
        color = last_move.get("color")
        color_suffix = f" ({color})" if color else ""
        captured = last_move.get("captured")
        capture_suffix = f" · captured {_render_list(captured)}" if captured else ""
        lines.append(f"**{label}:** `{move}`{color_suffix}{capture_suffix}")

    captures = snapshot.get("captures")
    captures_black = captures.get("black") if isinstance(captures, dict) else None
    captures_white = captures.get("white") if isinstance(captures, dict) else None
    players = snapshot["players"]
    players_text = "—"
    if players:
        players_text = f"{_player_label(snapshot, 'black')} · {_player_label(snapshot, 'white')}"
    turn = snapshot.get("turn")
    lines.extend(
        [
            f"**Game mode:** `{snapshot['game_mode']}`",
            f"**Players:** {players_text}",
            f"**Revision:** `{snapshot.get('revision', '—')}`",
            f"**Turn:** `{_actor_label(snapshot, turn) if turn else '—'}`",
            f"**To play:** `{snapshot.get('to_play') or '—'}`",
            f"**Status:** `{snapshot.get('status')}` ({snapshot.get('status_reason')})",
            f"**Captures:** Black `{captures_black}` · White `{captures_white}`",
            f"**Consecutive passes:** `{snapshot.get('consecutive_passes', 0)}`",
            f"**Result:** `{snapshot.get('result') or '—'}`",
        ]
    )

    game_id = snapshot.get("game_id")
    stones = snapshot.get("stones")
    board_size = snapshot.get("board_size", 19)
    if game_id and isinstance(stones, dict) and isinstance(board_size, int):
        lines.extend(["", *_render_board(stones, board_size)])
    else:
        lines.extend(["", "**Board:** _(no game in progress)_"])

    lines.extend(["", f"**Legal moves:** {_render_list(snapshot.get('legal_moves'))}"])
    move_history = snapshot.get("move_history")
    if isinstance(move_history, list) and move_history:
        lines.extend(["", "**Move history:**", "", "| Ply | Move | Color | Actor | Captured |", "| ---: | --- | --- | --- | --- |"])
        for item in move_history:
            if isinstance(item, dict):
                captured = ", ".join(str(value) for value in item.get("captured", [])) or "—"
                actor = _actor_label(snapshot, item.get("actor"), item.get("color"))
                lines.append(
                    f"| {item.get('ply', '—')} | `{item.get('move', '—')}` | "
                    f"`{item.get('color', '—')}` | `{actor}` | `{captured}` |"
                )
    if snapshot.get("status") == "scoring" or isinstance(snapshot.get("score"), dict):
        lines.extend(["", *_render_score(snapshot.get("score"), snapshot)])
    return "\n".join(lines)


def _server_is_running() -> bool:
    """해당 주소의 상태 확인 응답이 이 앱인지 확인한다."""
    try:
        with httpx.Client(timeout=_SHORT_TIMEOUT) as client:
            response = client.get(f"{BASE_URL}/api/health")
    except httpx.RequestError:
        return False
    if not response.is_success:
        return False
    try:
        body = response.json()
    except ValueError:
        return False
    return isinstance(body, dict) and body.get("app") == "llm-baduk"


def _open_browser_when_ready() -> None:
    """서버 상태 확인이 성공한 뒤 브라우저를 연다."""
    deadline = time.monotonic() + 5
    while time.monotonic() < deadline:
        if _server_is_running():
            webbrowser.open(BASE_URL)
            return
        time.sleep(0.1)


def _start() -> int:
    """서버를 시작하거나 실행 중인 서버의 브라우저를 연다."""
    if _server_is_running():
        webbrowser.open(BASE_URL)
        return 0
    threading.Thread(target=_open_browser_when_ready, daemon=True).start()
    print(f"LLM Baduk server: {BASE_URL}", flush=True)
    print("Press Ctrl+C to stop.", flush=True)
    try:
        uvicorn.run(
            "llm_baduk.app:app",
            host=HOST,
            port=PORT,
            timeout_graceful_shutdown=1,
            access_log=False,
            log_level="critical",
        )
    except OSError:
        print("**Error:** Unable to start the server.")
        return 1
    return 0


def _build_parser() -> argparse.ArgumentParser:
    """CLI 인자를 구성한다."""
    parser = argparse.ArgumentParser(prog="baduk", add_help=False)
    parser.add_argument("--help", action="store_true", dest="show_help")
    parser.add_argument("--color", choices=("black", "white"))
    subparsers = parser.add_subparsers(dest="command")
    subparsers.add_parser("start")
    subparsers.add_parser("status")
    wait_parser = subparsers.add_parser("wait")
    wait_parser.add_argument("--after-revision", type=int)
    move_parser = subparsers.add_parser("move")
    move_parser.add_argument("move")
    move_parser.add_argument("--no-wait", action="store_true")
    takeback_parser = subparsers.add_parser("takeback")
    takeback_parser.add_argument("action", choices=("request", "accept", "reject"))
    subparsers.add_parser("resign")
    score_parser = subparsers.add_parser("score")
    score_subparsers = score_parser.add_subparsers(dest="score_action", required=True)
    for action in ("dead", "seki"):
        action_parser = score_subparsers.add_parser(action)
        action_parser.add_argument("point")
        action_parser.add_argument("--revision", type=int)
    accept_parser = score_subparsers.add_parser("accept")
    accept_parser.add_argument("--revision", type=int)
    score_subparsers.add_parser("resume")
    return parser


def _score_request(
    action: str,
    point: str | None = None,
    revision: int | None = None,
    *,
    color: str | None = None,
) -> tuple[dict[str, Any] | None, int]:
    """스코어 동작을 현재 API에 전달한다."""
    payload: dict[str, Any] = {"action": action}
    if point is not None:
        payload["point"] = point
    if revision is not None:
        payload["revision"] = revision
    return _request("POST", _participant_path(color, "score"), payload)


def main(argv: Sequence[str] | None = None) -> int:
    """명령을 실행하고 종료 코드를 반환한다."""
    parser = _build_parser()
    args = parser.parse_args(argv)
    if args.show_help or args.command is None:
        print(_help_text())
        return 0
    if args.command == "start":
        return _start()
    if args.command == "status":
        snapshot, exit_code = _request("GET", "/api/state")
    elif args.command == "wait":
        payload = {"after_revision": args.after_revision} if args.after_revision is not None else None
        snapshot, exit_code = _request(
            "POST",
            _participant_path(args.color, "wait"),
            payload,
            wait_for_event=True,
        )
    elif args.command == "takeback":
        snapshot, exit_code = _request(
            "POST",
            _participant_path(args.color, "takeback"),
            {"action": args.action},
            wait_for_event=args.action == "request",
        )
    elif args.command == "resign":
        snapshot, exit_code = _request("POST", _participant_path(args.color, "resign"))
    elif args.command == "move":
        snapshot, exit_code = _request(
            "POST",
            _participant_path(args.color, "moves"),
            {"move": args.move, "wait": not args.no_wait},
            wait_for_event=not args.no_wait,
        )
    elif args.color and args.score_action in {"dead", "seki", "accept"} and args.revision is None:
        print(
            f"**Error:** `--color {args.color} score {args.score_action}` requires an explicitly reviewed `--revision N`."
        )
        return 1
    elif args.score_action == "accept" and args.revision is None:
        current, exit_code = _request("GET", "/api/state")
        if current is None:
            return exit_code
        revision = current.get("revision")
        if not isinstance(revision, int):
            print("**Error:** The server returned an invalid revision.")
            return 1
        snapshot, exit_code = _score_request("accept", revision=revision, color=args.color)
    elif args.score_action == "accept":
        snapshot, exit_code = _score_request("accept", revision=args.revision, color=args.color)
    elif args.score_action in {"dead", "seki"}:
        snapshot, exit_code = _score_request(
            args.score_action,
            point=args.point,
            revision=args.revision,
            color=args.color,
        )
    else:
        snapshot, exit_code = _score_request("resume", color=args.color)
    if snapshot is None:
        return exit_code
    print(render_snapshot(snapshot))
    if args.command == "wait" and snapshot.get("event") == "game_reset":
        return 1
    if args.command == "move" and snapshot.get("event") == "game_reset":
        return 1
    if args.command == "takeback" and args.action == "request" and snapshot.get("event") == "game_reset":
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
