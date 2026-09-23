"""로컬 리버시 서버용 명령줄 도구."""

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
PORT = 8768
BASE_URL = f"http://{HOST}:{PORT}"
_SHORT_TIMEOUT = httpx.Timeout(1.5, connect=0.6)
_WAIT_TIMEOUT = httpx.Timeout(connect=0.6, read=None, write=1.5, pool=1.5)


def _help_text() -> str:
    """세션 사용법을 Markdown으로 반환한다."""
    return """# reversi

Control a local human-vs-LLM or CLI-vs-CLI Reversi game.

## Usage

```text
reversi start
reversi status
reversi --color black status
reversi wait [--after-revision N]
reversi move A1 [--no-wait]
reversi takeback request|accept|reject
reversi resign
```

For CLI-vs-CLI, put `--color black` or `--color white` before every
participant command:

```text
reversi --color black wait [--after-revision N]
reversi --color black move A1 [--no-wait]
reversi --color black takeback request|accept|reject
reversi --color black resign
```

Coordinates run from A1 at the upper-left to H8 at the lower-right. The
server lists legal destinations; a move must flip at least one opposing disc.
The default move command waits for the next turn. Add `--no-wait` to return
after the move. `status` only reads the current game state.

In CLI-vs-CLI mode, run two independent AI sessions with a color on each
command. Each process controls only its selected color. The CLI never starts
an AI or an opponent process.
"""


def _request(
    method: str,
    path: str,
    payload: dict[str, Any] | None = None,
    *,
    wait_for_event: bool = False,
) -> tuple[dict[str, Any] | None, int]:
    """로컬 API를 호출하고 통신·도메인 오류를 출력한다."""
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
            print("**Error:** The server returned an invalid game state.")
            return None, 1
        return body, 0
    try:
        body = response.json()
    except ValueError:
        print(f"**Error:** Server request failed (HTTP {response.status_code}).")
        return None, 1
    detail = body.get("detail") if isinstance(body, dict) else None
    if isinstance(detail, dict) and isinstance(detail.get("message"), str):
        message = detail["message"]
    elif isinstance(detail, str):
        message = detail
    else:
        message = f"Server request failed (HTTP {response.status_code})."
    if message.startswith("이미"):
        message = "Illegal move: " + message.split(":", maxsplit=1)[-1].strip()
    elif message.startswith("상대 돌을 뒤집지 못하는 수입니다:"):
        message = "Illegal move: " + message.split(":", maxsplit=1)[-1].strip()
    elif message.startswith("현재 차례와 다른 색으로 둘 수 없습니다."):
        message = "It is not the requested player's turn."
    elif message.startswith("진행 중인 게임이 없습니다."):
        message = "No game is in progress. Start a game first."
    print(f"**Error:** {message}")
    return None, 1


def _render_board(discs: dict[str, str]) -> list[str]:
    """A1이 왼쪽 위인 보드를 ASCII Markdown으로 그린다."""
    lines = ["**Board:**", "", "```text", "    A B C D E F G H"]
    for row in range(1, 9):
        cells = []
        for column in "ABCDEFGH":
            color = discs.get(f"{column}{row}")
            cells.append("X" if color == "black" else "O" if color == "white" else ".")
        lines.append(f"{row}   {' '.join(cells)}")
    lines.extend(["    A B C D E F G H", "```"])
    return lines


def _player_name(snapshot: dict[str, Any], color: str) -> str:
    """색상별 참가자 표시 이름을 만든다."""
    player = snapshot["players"][color]
    if player["name"]:
        return str(player["name"])
    actor = player["actor"]
    return {"human": "Human", "llm": "LLM", "black": "Black", "white": "White"}[actor]


def render_snapshot(snapshot: dict[str, Any]) -> str:
    """현재 보드, 차례, 결과와 합법 수를 Markdown으로 렌더링한다."""
    lines = _render_board(snapshot["discs"])
    counts = snapshot["counts"]
    lines.extend(
        [
            "",
            f"**Status:** {snapshot['status']} · revision {snapshot['revision']}",
            f"**Black:** {_player_name(snapshot, 'black')} · {counts['black']} discs",
            f"**White:** {_player_name(snapshot, 'white')} · {counts['white']} discs",
            f"**Turn:** {snapshot['turn'] or '—'}",
            f"**Event:** {snapshot['event']}",
        ]
    )
    takeback = snapshot["takeback"]
    if takeback:
        plies = takeback["moves_to_undo"]
        count_label = f"{plies} {'ply' if plies == 1 else 'plies'}"
        outcome = "to undo" if takeback["state"] == "pending" else "undone"
        lines.append(
            f"**Takeback:** {takeback['state']} · requester {takeback['requester']}"
            f" · target ply {takeback['target_ply']} · {count_label} {outcome}"
        )
    if snapshot["auto_passed_color"]:
        lines.append(f"**Automatic pass:** {snapshot['auto_passed_color']} has no legal move.")
    if snapshot["last_move"]:
        last = snapshot["last_move"]
        lines.append(f"**Last move:** {last['color']} {last['move']} · flipped {', '.join(last['flipped'])}")
    if snapshot["status"] in {"finished", "resigned"}:
        lines.append(f"**Result:** {snapshot['result'] or 'Draw'}")
    lines.append(f"**Legal moves:** {' '.join(snapshot['legal_moves']) or '—'}")
    return "\n".join(lines)


def _start() -> int:
    """localhost 서버를 시작하고 브라우저를 연다."""
    if _server_is_running():
        webbrowser.open(BASE_URL)
        print(f"LLM Reversi is already running at {BASE_URL}")
        return 0
    threading.Thread(target=_open_browser_when_ready, daemon=True).start()
    uvicorn.run("llm_reversi.app:app", host=HOST, port=PORT, log_level="warning")
    return 0


def _server_is_running() -> bool:
    """고정 로컬 주소에서 리버시 상태를 확인한다."""
    try:
        with httpx.Client(base_url=BASE_URL, timeout=httpx.Timeout(0.4, connect=0.3)) as client:
            return client.get("/api/health").is_success
    except httpx.RequestError:
        return False


def _open_browser_when_ready() -> None:
    """서버 준비 후 기본 브라우저를 연다."""
    while True:
        if _server_is_running():
            webbrowser.open(BASE_URL)
            return
        time.sleep(0.25)


def _build_parser() -> argparse.ArgumentParser:
    """색상 옵션과 CLI 동작을 등록한다."""
    parser = argparse.ArgumentParser(prog="reversi", description="Local human-vs-LLM or CLI-vs-CLI Reversi")
    parser.add_argument("--color", choices=("black", "white"), help="CLI-vs-CLI participant color")
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("start", help="start the local browser app")
    subparsers.add_parser("status", help="read the current game state")
    wait_parser = subparsers.add_parser("wait", help="wait until this CLI can act")
    wait_parser.add_argument("--after-revision", type=int)
    move_parser = subparsers.add_parser("move", help="place a disc, such as A1")
    move_parser.add_argument("move")
    move_parser.add_argument("--no-wait", action="store_true", help="return immediately after placing the disc")
    takeback_parser = subparsers.add_parser("takeback", help="request or answer a takeback")
    takeback_parser.add_argument("action", choices=("request", "accept", "reject"))
    subparsers.add_parser("resign", help="resign the current game")
    subparsers.add_parser("help-markdown", help="print the session guide as Markdown")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """명령을 해석해 리버시 서버에 요청한다."""
    parser = _build_parser()
    args = parser.parse_args(argv)
    if args.command == "help-markdown":
        print(_help_text())
        return 0
    if args.command == "start":
        if args.color is not None:
            parser.error("--color is only used with participant commands")
        return _start()
    if args.command == "status":
        snapshot, status = _request("GET", "/api/state")
    elif args.command == "wait":
        payload = {"after_revision": args.after_revision} if args.after_revision is not None else None
        path = f"/api/players/{args.color}/wait" if args.color else "/api/llm/wait"
        snapshot, status = _request("POST", path, payload, wait_for_event=True)
    elif args.command == "move":
        path = f"/api/players/{args.color}/moves" if args.color else "/api/llm/moves"
        snapshot, status = _request(
            "POST",
            path,
            {"move": args.move, "wait": not args.no_wait},
            wait_for_event=not args.no_wait,
        )
    elif args.command == "takeback":
        path = f"/api/players/{args.color}/takeback" if args.color else "/api/llm/takeback"
        snapshot, status = _request(
            "POST",
            path,
            {"action": args.action},
            wait_for_event=args.action == "request",
        )
    else:
        path = f"/api/players/{args.color}/resign" if args.color else "/api/llm/resign"
        snapshot, status = _request("POST", path, wait_for_event=False)
    if snapshot is not None:
        print(render_snapshot(snapshot))
    return status


if __name__ == "__main__":
    sys.exit(main())
