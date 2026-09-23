"""Connect Four 서버를 실행하거나 로컬 게임에 접속하는 명령줄 도구."""

from __future__ import annotations

import argparse
import json
import sys
import webbrowser
from typing import Sequence

import httpx
import uvicorn


DEFAULT_URL = "http://127.0.0.1:8767"


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="connect4", description="로컬 사람 대 LLM 또는 CLI 대 CLI Connect Four")
    parser.add_argument("--color", choices=("red", "yellow"), help="CLI 플레이어 색상 (하위 명령 앞에 지정)")
    parser.add_argument("--url", default=DEFAULT_URL, help=f"게임 서버 주소 (기본값: {DEFAULT_URL})")
    subparsers = parser.add_subparsers(dest="command", required=True)

    start = subparsers.add_parser("start", help="웹 게임 서버 시작")
    start.add_argument("--host", default="127.0.0.1")
    start.add_argument("--port", type=int, default=8767)
    start.add_argument("--no-browser", action="store_true", help="브라우저를 자동으로 열지 않음")

    subparsers.add_parser("status", help="현재 게임 상태 읽기")
    subparsers.add_parser("wait", help="지정 색의 차례 또는 게임 상태 변경 대기")

    move = subparsers.add_parser("move", help="1부터 7까지 열 번호로 수 두기")
    move.add_argument("column", help="열 번호 1–7")
    move.add_argument("--no-wait", action="store_true", help="상대 차례나 다음 상태를 기다리지 않고 반환")

    takeback = subparsers.add_parser("takeback", help="무르기 요청 또는 응답")
    takeback.add_argument("action", choices=("request", "accept", "reject"))
    subparsers.add_parser("resign", help="게임 기권")
    return parser


def _request(url: str, method: str, path: str, *, json_body: dict[str, object] | None = None) -> dict[str, object]:
    try:
        with httpx.Client(timeout=None) as client:
            response = client.request(method, f"{url.rstrip('/')}{path}", json=json_body)
    except httpx.HTTPError as error:
        raise RuntimeError(f"Cannot reach Connect Four server at {url}: {error}") from error
    if response.is_error:
        try:
            detail = response.json().get("detail", {})
        except ValueError:
            detail = {}
        message = detail.get("message", response.text)
        code = detail.get("code")
        raise RuntimeError(f"{message} [{code}]" if code else str(message))
    return response.json()


def _print_snapshot(snapshot: dict[str, object]) -> None:
    print(json.dumps(snapshot, ensure_ascii=False, indent=2))


def _endpoint(color: str | None, suffix: str) -> str:
    return f"/api/players/{color}/{suffix}" if color else f"/api/llm/{suffix}"


def _run(args: argparse.Namespace) -> int:
    if args.command == "start":
        if not args.no_browser:
            webbrowser.open(f"http://{args.host}:{args.port}")
        uvicorn.run("llm_connect4.app:app", host=args.host, port=args.port, reload=False)
        return 0
    if args.command == "status":
        _print_snapshot(_request(args.url, "GET", "/api/state"))
        return 0
    if args.command == "wait":
        _print_snapshot(_request(args.url, "POST", _endpoint(args.color, "wait"), json_body={} if args.color is None else None))
        return 0
    if args.command == "move":
        body = {"move": args.column, "wait": not args.no_wait}
        _print_snapshot(_request(args.url, "POST", _endpoint(args.color, "moves"), json_body=body))
        return 0
    if args.command == "takeback":
        _print_snapshot(_request(args.url, "POST", _endpoint(args.color, "takeback"), json_body={"action": args.action}))
        return 0
    if args.command == "resign":
        _print_snapshot(_request(args.url, "POST", _endpoint(args.color, "resign")))
        return 0
    return 2


def main(argv: Sequence[str] | None = None) -> None:
    args = _parser().parse_args(argv)
    try:
        raise SystemExit(_run(args))
    except RuntimeError as error:
        print(f"connect4: {error}", file=sys.stderr)
        raise SystemExit(1) from None


if __name__ == "__main__":
    main()
