import re

from llm_chess import cli


def _human_snapshot(**overrides):
    snapshot = {
        "event": "human_move",
        "game_mode": "human_vs_llm",
        "players": {
            "white": {"actor": "human", "controller": "human", "name": None},
            "black": {"actor": "llm", "controller": "cli", "name": None},
        },
        "human_color": "white",
        "llm_color": "black",
        "turn": "llm",
        "status": "active",
        "status_reason": "in_progress",
        "check": False,
        "result": None,
        "fen": "fen",
        "pieces": {"e4": "P"},
        "legal_moves": [{"uci": "e7e5", "san": "e5"}],
        "last_move": {"actor": "human", "uci": "e2e4", "san": "e4"},
        "move_history": [],
        "takeback": None,
        "resigned_by": None,
    }
    snapshot.update(overrides)
    return snapshot


def _cli_snapshot(**overrides):
    snapshot = {
        "event": "white_move",
        "game_mode": "cli_vs_cli",
        "players": {
            "white": {"actor": "white", "controller": "cli", "name": "Ada"},
            "black": {"actor": "black", "controller": "cli", "name": "Turing"},
        },
        "human_color": None,
        "llm_color": None,
        "turn": "black",
        "status": "active",
        "status_reason": "in_progress",
        "check": False,
        "result": None,
        "fen": "fen",
        "pieces": {"e4": "P"},
        "legal_moves": [{"uci": "e7e5", "san": "e5"}],
        "last_move": {"actor": "white", "color": "white", "uci": "e2e4", "san": "e4"},
        "move_history": [
            {"ply": 1, "actor": "white", "color": "white", "uci": "e2e4", "san": "e4"},
            {"ply": 2, "actor": "black", "color": "black", "uci": "e7e5", "san": "e5"},
        ],
        "takeback": None,
        "resigned_by": None,
    }
    snapshot.update(overrides)
    return snapshot


def _assert_english(output: str) -> None:
    assert re.search(r"[가-힣]", output) is None


def test_help_is_markdown(capsys) -> None:
    assert cli.main(["--help"]) == 0
    output = capsys.readouterr().out
    assert output.startswith("# chess")
    assert "chess move MOVE" in output
    assert "chess takeback request|accept|reject" in output
    assert "chess resign" in output
    assert "Control a local human-vs-LLM or CLI-vs-CLI chess game." in output
    assert "two independent chess sessions" in output
    assert "before every participant command" in output
    assert "one pending blocking command at a time" in output
    assert "run `status` to read the fresh game state" in output
    assert "The other color's session handles a takeback request." in output
    _assert_english(output)


def test_status_renders_event_first(monkeypatch, capsys) -> None:
    monkeypatch.setattr(
        cli,
        "_request",
        lambda method, path, payload=None: (_human_snapshot(), 0),
    )
    assert cli.main(["status"]) == 0
    output = capsys.readouterr().out
    assert output.startswith("**Event:** human_move")
    assert "**Human move:** `e2e4` (`e4`)" in output
    assert "**Check:** `No`" in output
    assert "**Legal moves:**" in output
    assert "| `e7e5` | `e5` |" in output
    _assert_english(output)


def test_reset_wake_is_nonzero(monkeypatch, capsys) -> None:
    monkeypatch.setattr(
        cli,
        "_request",
        lambda method, path, payload=None, **kwargs: (_human_snapshot(event="game_reset"), 0),
    )
    assert cli.main(["wait"]) == 1
    output = capsys.readouterr().out
    assert "game_reset" in output
    _assert_english(output)


def test_server_errors_are_rendered_in_english() -> None:
    assert cli._english_server_error(
        "진행 중인 게임이 없습니다. 먼저 게임을 시작하세요.",
        409,
    ) == "No game is in progress. Start a game first."
    assert cli._english_server_error(
        "불법 수입니다: e2e5",
        422,
    ) == "Illegal move: e2e5"
    assert cli._english_server_error(
        "알 수 없는 서버 오류",
        500,
    ) == "Server request failed (HTTP 500)."


def test_takeback_request_and_human_rejection_are_explicit_in_cli_results(capsys) -> None:
    requested = _human_snapshot(
        event="takeback_requested",
        status_reason="takeback_pending",
        legal_moves=[],
        takeback={
            "state": "pending",
            "requester": "human",
            "target_ply": 1,
            "undone_plies": 1,
        },
    )
    print(cli.render_snapshot(requested))
    output = capsys.readouterr().out
    assert "**Takeback request:** Human requested a takeback at ply 1." in output
    _assert_english(output)

    rejected = _human_snapshot(
        event="takeback_rejected",
        turn="human",
        status_reason="in_progress",
        takeback={
            "state": "rejected",
            "requester": "llm",
            "target_ply": 2,
            "undone_plies": 0,
        },
    )
    print(cli.render_snapshot(rejected))
    output = capsys.readouterr().out
    assert "**Takeback result:** Human rejected the takeback for LLM." in output
    _assert_english(output)


def test_takeback_and_resignation_commands_use_llm_endpoints(monkeypatch, capsys) -> None:
    calls = []

    def request(method, path, payload=None, **kwargs):
        calls.append((method, path, payload, kwargs))
        if path.endswith("takeback"):
            return (
                _human_snapshot(
                    event="takeback_requested",
                    takeback={
                        "state": "pending",
                        "requester": "llm",
                        "target_ply": 2,
                        "undone_plies": 1,
                    },
                    status_reason="takeback_pending",
                    pieces={},
                    legal_moves=[],
                    last_move=None,
                ),
                0,
            )
        return (
            _human_snapshot(
                event="llm_resigned",
                turn=None,
                status="resigned",
                status_reason="resignation",
                result="1-0",
                pieces={},
                legal_moves=[],
                last_move=None,
                resigned_by="llm",
            ),
            0,
        )

    monkeypatch.setattr(cli, "_request", request)
    assert cli.main(["takeback", "request"]) == 0
    assert cli.main(["resign"]) == 0
    output = capsys.readouterr().out
    assert calls[0] == (
        "POST",
        "/api/llm/takeback",
        {"action": "request"},
        {"wait_for_event": True},
    )
    assert calls[1][0:3] == ("POST", "/api/llm/resign", None)
    assert "LLM requested a takeback" in output
    assert "**Resignation:** LLM resigned." in output
    _assert_english(output)


def test_colored_commands_route_to_the_selected_player(monkeypatch, capsys) -> None:
    calls = []

    def request(method, path, payload=None, **kwargs):
        calls.append((method, path, payload, kwargs))
        return _cli_snapshot(), 0

    monkeypatch.setattr(cli, "_request", request)
    commands = [
        (["wait"], "wait", None, {"wait_for_event": True}),
        (["move", "e2e4"], "moves", {"move": "e2e4", "wait": True}, {"wait_for_event": True}),
        (["takeback", "request"], "takeback", {"action": "request"}, {"wait_for_event": True}),
        (["takeback", "accept"], "takeback", {"action": "accept"}, {"wait_for_event": False}),
        (["resign"], "resign", None, {}),
    ]
    for color in (None, "white", "black"):
        for command, resource, payload, kwargs in commands:
            prefix = [] if color is None else ["--color", color]
            assert cli.main([*prefix, *command]) == 0
            if color is None:
                path = f"/api/llm/{resource}"
            else:
                path = f"/api/players/{color}/{resource}"
            assert calls[-1] == (
                "POST",
                path,
                payload,
                kwargs,
            )
            capsys.readouterr()


def test_uncolored_move_keeps_llm_endpoint_and_no_wait_payload(monkeypatch, capsys) -> None:
    calls = []

    def request(method, path, payload=None, **kwargs):
        calls.append((method, path, payload, kwargs))
        return _human_snapshot(), 0

    monkeypatch.setattr(cli, "_request", request)
    assert cli.main(["move", "e2e4", "--no-wait"]) == 0
    assert calls == [
        ("POST", "/api/llm/moves", {"move": "e2e4", "wait": False}, {"wait_for_event": False})
    ]
    _assert_english(capsys.readouterr().out)


def test_colored_status_is_always_read_only(monkeypatch, capsys) -> None:
    calls = []

    def request(method, path, payload=None):
        calls.append((method, path, payload))
        return _human_snapshot(), 0

    monkeypatch.setattr(cli, "_request", request)
    for color in ("white", "black"):
        assert cli.main(["--color", color, "status"]) == 0
        capsys.readouterr()
    assert calls == [("GET", "/api/state", None), ("GET", "/api/state", None)]


def test_colored_blocking_commands_return_nonzero_after_reset(monkeypatch, capsys) -> None:
    monkeypatch.setattr(
        cli,
        "_request",
        lambda *args, **kwargs: (_cli_snapshot(event="game_reset"), 0),
    )
    assert cli.main(["--color", "white", "wait"]) == 1
    capsys.readouterr()
    assert cli.main(["--color", "black", "move", "e7e5"]) == 1
    capsys.readouterr()
    assert cli.main(["--color", "white", "takeback", "request"]) == 1
    _assert_english(capsys.readouterr().out)


def test_cli_vs_cli_snapshot_renders_participants_turn_moves_and_result() -> None:
    output = cli.render_snapshot(_cli_snapshot())
    assert "**Players:** Ada (white) · Turing (black)" in output
    assert "**Turn:** `Turing (black)`" in output
    assert "**Ada (white) move:** `e2e4` (`e4`)" in output
    assert "| 1 | Ada (white) | `e2e4 (e4)` |" in output
    assert "| 2 | Turing (black) | `e7e5 (e5)` |" in output

    resigned = _cli_snapshot(event="black_resigned", turn=None, result="1-0", resigned_by="black")
    output = cli.render_snapshot(resigned)
    assert "**Resignation:** Turing (black) resigned." in output
    assert "**Result:** `1-0 — Ada (white) wins`" in output

    drawn = _cli_snapshot(result="1/2-1/2")
    assert "**Result:** `1/2-1/2 — draw`" in cli.render_snapshot(drawn)


def test_cli_vs_cli_takeback_names_requester_and_responder() -> None:
    requested = _cli_snapshot(
        event="takeback_requested",
        takeback={"state": "pending", "requester": "white", "target_ply": 1, "undone_plies": 1},
    )
    assert "**Takeback request:** Ada (white) requested a takeback at ply 1." in cli.render_snapshot(requested)

    accepted = _cli_snapshot(
        event="takeback_accepted",
        takeback={"state": "accepted", "requester": "white", "target_ply": 1, "undone_plies": 2},
    )
    assert (
        "**Takeback result:** Turing (black) accepted the takeback for Ada (white); 2 plies undone."
        in cli.render_snapshot(accepted)
    )
