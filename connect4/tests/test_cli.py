import json

import pytest

from llm_connect4 import cli


def test_color_precedes_command_and_no_wait_is_a_move_option() -> None:
    args = cli._parser().parse_args(["--color", "yellow", "move", "4", "--no-wait"])
    assert args.color == "yellow"
    assert args.column == "4"
    assert args.no_wait
    with pytest.raises(SystemExit):
        cli._parser().parse_args(["move", "4", "--color", "yellow"])


def test_status_is_read_only_and_outputs_complete_snapshot(monkeypatch, capsys) -> None:
    snapshot = {
        "event": "takeback_requested", "status": "active",
        "takeback": {"state": "pending", "requester": "yellow", "target_ply": 2, "undone_plies": 2},
    }
    calls = []

    def request(url, method, path, *, json_body=None):
        calls.append((method, path, json_body))
        return snapshot

    monkeypatch.setattr(cli, "_request", request)
    assert cli._run(cli._parser().parse_args(["status"])) == 0
    assert calls == [("GET", "/api/state", None)]
    output = json.loads(capsys.readouterr().out)
    assert output == snapshot


def test_move_wait_and_takeback_use_only_the_selected_api(monkeypatch) -> None:
    calls = []

    def request(url, method, path, *, json_body=None):
        calls.append((method, path, json_body))
        return {"event": "red_move"}

    monkeypatch.setattr(cli, "_request", request)
    args = cli._parser().parse_args(["--color", "red", "move", "4", "--no-wait"])
    cli._run(args)
    cli._run(cli._parser().parse_args(["--color", "yellow", "takeback", "request"]))
    assert calls == [
        ("POST", "/api/players/red/moves", {"move": "4", "wait": False}),
        ("POST", "/api/players/yellow/takeback", {"action": "request"}),
    ]
