"""로컬 체스 서버용 명령줄 인터페이스."""

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
PORT = 8765
BASE_URL = f"http://{HOST}:{PORT}"
_SHORT_TIMEOUT = httpx.Timeout(1.5, connect=0.6)
_WAIT_TIMEOUT = httpx.Timeout(connect=0.6, read=None, write=1.5, pool=1.5)
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
_ILLEGAL_MOVE_PREFIX = "불법 수입니다:"


def _help_text() -> str:
    """Markdown 형식의 명령 도움말을 반환한다."""
    return """# chess

Control a local human-vs-LLM or CLI-vs-CLI chess game.

## Usage

```text
chess start
chess status
chess wait
chess move MOVE [--no-wait]
chess takeback request|accept|reject
chess resign
chess --color white|black status
chess --color white|black wait
chess --color white|black move MOVE [--no-wait]
chess --color white|black takeback request|accept|reject
chess --color white|black resign
```

Enter `MOVE` in UCI or SAN notation. A move waits for the opponent by default;
use `--no-wait` to return immediately.

For CLI-vs-CLI games, run two independent chess sessions and put that
session's `--color white` or `--color black` before every participant command.
Each session can have one pending blocking command at a time. If a blocking
command returns a `game_reset` event, run `status` to read the fresh game state.
The other color's session handles a takeback request. The CLI does not launch
the other session.
"""


def _english_server_error(detail: object, status_code: int) -> str:
    """서버 오류를 CLI용 영어 문구로 변환한다."""
    if isinstance(detail, str):
        translated = _SERVER_ERROR_TRANSLATIONS.get(detail)
        if translated is not None:
            return translated
        if detail.startswith(_ILLEGAL_MOVE_PREFIX):
            move = detail.removeprefix(_ILLEGAL_MOVE_PREFIX).strip()
            return f"Illegal move: {move}"
        if detail.isascii():
            return detail
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
        return body, 0

    try:
        body = response.json()
    except ValueError:
        print(f"**Error:** Server request failed (HTTP {response.status_code}).")
        return None, 1
    detail = body.get("detail") if isinstance(body, dict) else None
    print(f"**Error:** {_english_server_error(detail, response.status_code)}")
    return None, 1


def _render_board(pieces: dict[str, str]) -> list[str]:
    """기물을 흰색 기준 ASCII 보드로 렌더링한다."""
    lines = ["**Board:**", "", "```text", "    a b c d e f g h"]
    for rank in range(8, 0, -1):
        cells = [pieces.get(f"{file}{rank}", ".") for file in "abcdefgh"]
        lines.append(f"{rank}   {' '.join(cells)}  {rank}")
    lines.extend(["    a b c d e f g h", "```"])
    return lines


def _player_label(snapshot: dict[str, Any], color: str) -> str:
    """참가자 이름과 색상 또는 기존 행위자 이름을 반환한다."""
    player = snapshot["players"][color]
    name = player["name"]
    if name is not None:
        identity = str(name)
    elif snapshot["game_mode"] == "cli_vs_cli":
        identity = color.title()
    else:
        identity = {"human": "Human", "llm": "LLM"}.get(
            player["actor"], str(player["actor"]).title()
        )
    if snapshot["game_mode"] == "cli_vs_cli":
        return f"{identity} ({color})"
    return identity


def _actor_label(snapshot: dict[str, Any], actor: object, color: object = None) -> str:
    """행위자 식별자를 참가자 표시명으로 바꾼다."""
    player_color = color if color == "white" or color == "black" else None
    if player_color is None and (actor == "white" or actor == "black"):
        player_color = actor
    if player_color is None:
        for candidate_color, player in snapshot["players"].items():
            if player["actor"] == actor:
                player_color = candidate_color
                break
    if player_color in {"white", "black"}:
        return _player_label(snapshot, player_color)
    if actor == "human":
        return "Human"
    if actor == "llm":
        return "LLM"
    return str(actor or "—").title()


def render_snapshot(snapshot: dict[str, Any]) -> str:
    """게임 스냅샷을 문서형 Markdown으로 렌더링한다."""
    lines = [f"**Event:** {snapshot.get('event', 'unknown')}"]
    game_mode = snapshot["game_mode"]
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
            if game_mode == "cli_vs_cli":
                responder_color = "black" if requester == "white" else "white"
                responder = _player_label(snapshot, responder_color)
            else:
                responder = "LLM" if requester == "human" else "Human"
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
    if event in {"human_resigned", "llm_resigned", "white_resigned", "black_resigned"}:
        actor = snapshot.get("resigned_by")
        if actor is None:
            actor = event.removesuffix("_resigned")
        lines.append(f"**Resignation:** {_actor_label(snapshot, actor)} resigned.")
    last_move = snapshot.get("last_move")
    if isinstance(last_move, dict):
        actor = last_move.get("actor", "unknown")
        move_text = f"`{last_move.get('uci')}` (`{last_move.get('san')}`)"
        actor_label = _actor_label(snapshot, actor, last_move.get("color"))
        label = f"{actor_label} move"
        lines.append(f"**{label}:** {move_text}")

    if game_mode == "cli_vs_cli":
        players = snapshot["players"]
        players_text = "—"
        if players:
            players_text = f"{_player_label(snapshot, 'white')} · {_player_label(snapshot, 'black')}"
        turn = snapshot.get("turn")
        turn_text = _actor_label(snapshot, turn) if turn else "—"
        result = snapshot.get("result")
        result_text = result or "—"
        if result == "1-0":
            result_text = f"{result} — {_player_label(snapshot, 'white')} wins"
        elif result == "0-1":
            result_text = f"{result} — {_player_label(snapshot, 'black')} wins"
        elif result == "1/2-1/2":
            result_text = f"{result} — draw"
        lines.extend(
            [
                f"**Players:** {players_text}",
                f"**Turn:** `{turn_text}`",
                f"**Status:** `{snapshot.get('status')}` ({snapshot.get('status_reason')})",
                f"**Check:** `{'Yes' if snapshot.get('check') else 'No'}`",
                f"**Result:** `{result_text}`",
                f"**FEN:** `{snapshot.get('fen') or '—'}`",
            ]
        )
    else:
        human_color = snapshot.get("human_color") or "—"
        llm_color = snapshot.get("llm_color") or "—"
        lines.extend(
            [
                f"**Colors:** Human `{human_color}` · LLM `{llm_color}`",
                f"**Turn:** `{snapshot.get('turn') or '—'}`",
                f"**Status:** `{snapshot.get('status')}` ({snapshot.get('status_reason')})",
                f"**Check:** `{'Yes' if snapshot.get('check') else 'No'}`",
                f"**Result:** `{snapshot.get('result') or '—'}`",
                f"**FEN:** `{snapshot.get('fen') or '—'}`",
            ]
        )

    pieces = snapshot.get("pieces")
    if isinstance(pieces, dict) and snapshot.get("fen"):
        lines.extend(["", *_render_board(pieces)])
    else:
        lines.extend(["", "**Board:** _(no game in progress)_"])

    legal_moves = snapshot.get("legal_moves")
    if isinstance(legal_moves, list):
        lines.extend(["", "**Legal moves:**", "", "| UCI | SAN |", "| --- | --- |"])
        for move in legal_moves:
            if isinstance(move, dict):
                lines.append(f"| `{move.get('uci')}` | `{move.get('san')}` |")
        if not legal_moves:
            lines.append("| — | — |")
    move_history = snapshot.get("move_history")
    if game_mode == "cli_vs_cli" and isinstance(move_history, list) and move_history:
        lines.extend(
            [
                "",
                "**Move history:**",
                "",
                "| Ply | Player | Move |",
                "| ---: | --- | --- |",
            ]
        )
        for move in move_history:
            if isinstance(move, dict):
                actor = _actor_label(snapshot, move.get("actor"), move.get("color"))
                move_text = f"{move.get('uci', '—')} ({move.get('san', '—')})"
                lines.append(f"| {move.get('ply', '—')} | {actor} | `{move_text}` |")
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
    return isinstance(body, dict) and body.get("app") == "llm-chess"


def _open_browser_when_ready() -> None:
    """서버 상태 확인이 성공한 뒤 브라우저를 연다."""
    deadline = time.monotonic() + 5
    while time.monotonic() < deadline:
        if _server_is_running():
            webbrowser.open(BASE_URL)
            return
        time.sleep(0.1)


def _start() -> int:
    """서버를 시작하고 브라우저를 연다."""
    if _server_is_running():
        webbrowser.open(BASE_URL)
        return 0
    threading.Thread(target=_open_browser_when_ready, daemon=True).start()
    print(f"LLM Chess server: {BASE_URL}", flush=True)
    print("Press Ctrl+C to stop.", flush=True)
    try:
        uvicorn.run(
            "llm_chess.app:app",
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
    parser = argparse.ArgumentParser(prog="chess", add_help=False)
    parser.add_argument("--help", action="store_true", dest="show_help")
    parser.add_argument("--color", choices=("white", "black"))
    subparsers = parser.add_subparsers(dest="command")
    subparsers.add_parser("start")
    subparsers.add_parser("status")
    subparsers.add_parser("wait")
    move_parser = subparsers.add_parser("move")
    move_parser.add_argument("move")
    move_parser.add_argument("--no-wait", action="store_true")
    takeback_parser = subparsers.add_parser("takeback")
    takeback_parser.add_argument("action", choices=("request", "accept", "reject"))
    subparsers.add_parser("resign")
    return parser


def _participant_path(color: str | None, resource: str) -> str:
    """색상 지정 여부에 맞는 참가자 API 경로를 반환한다."""
    if color is None:
        return f"/api/llm/{resource}"
    return f"/api/players/{color}/{resource}"


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
        snapshot, exit_code = _request(
            "POST",
            _participant_path(args.color, "wait"),
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
    else:
        snapshot, exit_code = _request(
            "POST",
            _participant_path(args.color, "moves"),
            {"move": args.move, "wait": not args.no_wait},
            wait_for_event=not args.no_wait,
        )
    if snapshot is None:
        return exit_code
    print(render_snapshot(snapshot))
    if (
        args.command in {"wait", "move"}
        or (args.command == "takeback" and args.action == "request")
    ) and snapshot.get("event") == "game_reset":
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
