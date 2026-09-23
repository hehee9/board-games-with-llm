import re

from llm_baduk import cli


def _snapshot(**overrides):
    snapshot = {
        "event": "human_move",
        "game_id": "game-1",
        "revision": 3,
        "status": "active",
        "status_reason": "in_progress",
        "game_mode": "human_vs_llm",
        "players": {
            "black": {"actor": "human", "controller": "human", "name": None},
            "white": {"actor": "llm", "controller": "cli", "name": None},
        },
        "human_color": "black",
        "llm_color": "white",
        "turn": "llm",
        "to_play": "white",
        "board_size": 9,
        "komi": 6.5,
        "stones": {"A1": "black", "J9": "white"},
        "legal_moves": ["D4", "pass"],
        "captures": {"black": 2, "white": 1},
        "consecutive_passes": 0,
        "move_history": [
            {"ply": 1, "move": "A1", "color": "black", "actor": "human", "captured": []}
        ],
        "last_move": {"ply": 1, "move": "A1", "color": "black", "actor": "human", "captured": []},
        "takeback": None,
        "resigned_by": None,
        "result": None,
        "score": None,
    }
    snapshot.update(overrides)
    return snapshot


def _cli_snapshot(**overrides):
    snapshot = _snapshot(
        event="black_move",
        game_mode="cli_vs_cli",
        players={
            "black": {"actor": "black", "controller": "cli", "name": "Alpha"},
            "white": {"actor": "white", "controller": "cli", "name": None},
        },
        human_color=None,
        llm_color=None,
        turn="white",
        to_play="white",
        move_history=[
            {"ply": 1, "move": "A1", "color": "black", "actor": "black", "captured": []}
        ],
        last_move={"ply": 1, "move": "A1", "color": "black", "actor": "black", "captured": []},
    )
    snapshot.update(overrides)
    return snapshot


def _assert_english(output: str) -> None:
    assert re.search(r"[가-힣]", output) is None


def test_help_lists_all_commands_and_options(capsys) -> None:
    assert cli.main(["--help"]) == 0
    output = capsys.readouterr().out
    assert output.startswith("# baduk")
    for command in (
        "baduk start",
        "baduk status",
        "baduk wait [--after-revision N]",
        "baduk move MOVE [--no-wait]",
        "baduk takeback request|accept|reject",
        "baduk resign",
        "baduk score dead POINT",
        "baduk score seki POINT",
        "baduk score accept [--revision N]",
        "baduk score resume",
    ):
        assert command in output
    assert "--color black|white" in output
    assert "two independent AI sessions" in output
    assert "before the subcommand" in output
    _assert_english(output)


def test_render_snapshot_uses_go_coordinates_symbols_and_compact_legal_moves() -> None:
    output = cli.render_snapshot(_snapshot())
    assert "**Event:** human_move" in output
    assert "**Revision:** `3`" in output
    assert "**Board:**" in output
    assert "9  . . . . . . . . O" in output
    assert "1  X . . . . . . . ." in output
    assert "A B C D E F G H J" in output
    assert "**Legal moves:** `D4` `pass`" in output
    assert "**Captures:** Black `2` · White `1`" in output
    assert "| 1 | `A1` | `black` | `Human (black)` | `—` |" in output
    _assert_english(output)


def test_render_snapshot_includes_score_breakdown() -> None:
    output = cli.render_snapshot(
        _snapshot(
            event="score_updated",
            status="scoring",
            score={
                "dead": ["D4"],
                "seki": ["Q16"],
                "accepted": {"human": True, "llm": False},
                "territory": {"black": ["A1"], "white": ["J9"]},
                "prisoners": {"black": 2, "white": 3},
                "totals": {"black": 5.5, "white": 6.5},
            },
        )
    )
    assert "**Score:**" in output
    assert "- Dead: `D4`" in output
    assert "- Seki: `Q16`" in output
    assert "- Accepted: Human (black) `Yes` · LLM (white) `No`" in output
    assert "- Territory: Black `A1` · White `J9`" in output
    assert "- Prisoners: Black `2` · White `3`" in output
    assert "- Totals: Black `5.5` · White `6.5`" in output


def test_render_snapshot_uses_cli_player_identity_and_color() -> None:
    output = cli.render_snapshot(
        _cli_snapshot(
            event="takeback_requested",
            takeback={"state": "pending", "requester": "black", "target_ply": 1, "undone_plies": 1},
        )
    )
    assert "**Game mode:** `cli_vs_cli`" in output
    assert "**Players:** Alpha (black) · White (white)" in output
    assert "**Takeback request:** Alpha (black) requested" in output
    assert "**Alpha (black) move:** `A1` (black)" in output
    assert "| 1 | `A1` | `black` | `Alpha (black)` | `—` |" in output
    assert "Human" not in output
    _assert_english(output)


def test_render_snapshot_maps_cli_score_acceptance_to_player_labels() -> None:
    output = cli.render_snapshot(
        _cli_snapshot(
            event="score_updated",
            status="scoring",
            score={
                "dead": ["D4"],
                "seki": ["Q16"],
                "accepted": {"black": True, "white": False},
                "territory": {"black": ["A1"], "white": ["J9"]},
                "prisoners": {"black": 2, "white": 3},
                "totals": {"black": 5.5, "white": 6.5},
            },
        )
    )
    assert "- Accepted: Alpha (black) `Yes` · White (white) `No`" in output
    assert "Human" not in output


def test_wait_forwards_after_revision(monkeypatch, capsys) -> None:
    calls = []

    def request(method, path, payload=None, **kwargs):
        calls.append((method, path, payload, kwargs))
        return _snapshot(event="human_move", revision=10), 0

    monkeypatch.setattr(cli, "_request", request)
    assert cli.main(["wait", "--after-revision", "9"]) == 0
    assert calls == [("POST", "/api/llm/wait", {"after_revision": 9}, {"wait_for_event": True})]
    assert "**Event:** human_move" in capsys.readouterr().out


def test_color_status_is_read_only(monkeypatch, capsys) -> None:
    calls = []

    def request(method, path, payload=None, **kwargs):
        calls.append((method, path, payload, kwargs))
        return _cli_snapshot(), 0

    monkeypatch.setattr(cli, "_request", request)
    assert cli.main(["--color", "white", "status"]) == 0
    assert calls == [("GET", "/api/state", None, {})]
    assert "**Game mode:** `cli_vs_cli`" in capsys.readouterr().out


def test_color_participant_commands_use_color_routes(monkeypatch) -> None:
    calls = []

    def request(method, path, payload=None, **kwargs):
        calls.append((method, path, payload, kwargs))
        return _cli_snapshot(event="score_updated", status="scoring", score={}), 0

    monkeypatch.setattr(cli, "_request", request)
    assert cli.main(["--color", "black", "move", "D4", "--no-wait"]) == 0
    assert cli.main(["--color", "black", "wait", "--after-revision", "9"]) == 0
    assert cli.main(["--color", "black", "takeback", "request"]) == 0
    assert cli.main(["--color", "black", "resign"]) == 0
    assert cli.main(["--color", "black", "score", "resume"]) == 0
    assert [call[1] for call in calls] == [
        "/api/players/black/moves",
        "/api/players/black/wait",
        "/api/players/black/takeback",
        "/api/players/black/resign",
        "/api/players/black/score",
    ]
    assert calls[0][2:] == ({"move": "D4", "wait": False}, {"wait_for_event": False})
    assert calls[1][2:] == ({"after_revision": 9}, {"wait_for_event": True})
    assert calls[2][2:] == ({"action": "request"}, {"wait_for_event": True})
    assert calls[3][2:] == (None, {})
    assert calls[4][2:] == ({"action": "resume"}, {})


def test_color_move_waits_for_opponent_by_default(monkeypatch) -> None:
    calls = []

    def request(method, path, payload=None, **kwargs):
        calls.append((method, path, payload, kwargs))
        return _cli_snapshot(), 0

    monkeypatch.setattr(cli, "_request", request)
    assert cli.main(["--color", "white", "move", "pass"]) == 0
    assert calls == [
        (
            "POST",
            "/api/players/white/moves",
            {"move": "pass", "wait": True},
            {"wait_for_event": True},
        )
    ]


def test_score_accept_uses_explicit_revision_without_fetch(monkeypatch) -> None:
    calls = []

    def request(method, path, payload=None, **kwargs):
        calls.append((method, path, payload, kwargs))
        return _snapshot(event="score_accepted", status="finished", score={}), 0

    monkeypatch.setattr(cli, "_request", request)
    assert cli.main(["score", "accept", "--revision", "21"]) == 0
    assert calls == [("POST", "/api/llm/score", {"action": "accept", "revision": 21}, {})]


def test_score_accept_fetches_current_revision_when_omitted(monkeypatch) -> None:
    calls = []

    def request(method, path, payload=None, **kwargs):
        calls.append((method, path, payload, kwargs))
        if path == "/api/state":
            return _snapshot(revision=18), 0
        return _snapshot(event="score_accepted", status="finished", score={}), 0

    monkeypatch.setattr(cli, "_request", request)
    assert cli.main(["score", "accept"]) == 0
    assert calls == [
        ("GET", "/api/state", None, {}),
        ("POST", "/api/llm/score", {"action": "accept", "revision": 18}, {}),
    ]


def test_color_score_edits_require_explicit_revision(monkeypatch, capsys) -> None:
    calls = []

    def request(method, path, payload=None, **kwargs):
        calls.append((method, path, payload, kwargs))
        return _cli_snapshot(event="score_updated", status="scoring", score={}), 0

    monkeypatch.setattr(cli, "_request", request)
    assert cli.main(["--color", "white", "score", "dead", "D4"]) == 1
    assert cli.main(["--color", "white", "score", "seki", "D4"]) == 1
    assert cli.main(["--color", "white", "score", "accept"]) == 1
    assert calls == []
    output = capsys.readouterr().out
    assert output.count("requires an explicitly reviewed `--revision N`") == 3


def test_color_score_commands_forward_reviewed_revision(monkeypatch) -> None:
    calls = []

    def request(method, path, payload=None, **kwargs):
        calls.append((method, path, payload, kwargs))
        return _cli_snapshot(event="score_updated", status="scoring", score={}), 0

    monkeypatch.setattr(cli, "_request", request)
    assert cli.main(["--color", "white", "score", "dead", "D4", "--revision", "12"]) == 0
    assert cli.main(["--color", "white", "score", "seki", "D4", "--revision", "13"]) == 0
    assert cli.main(["--color", "white", "score", "accept", "--revision", "14"]) == 0
    assert [call[2] for call in calls] == [
        {"action": "dead", "point": "D4", "revision": 12},
        {"action": "seki", "point": "D4", "revision": 13},
        {"action": "accept", "revision": 14},
    ]
    assert all(call[1] == "/api/players/white/score" for call in calls)


def test_score_commands_send_point_or_resume_action(monkeypatch) -> None:
    calls = []

    def request(method, path, payload=None, **kwargs):
        calls.append((method, path, payload, kwargs))
        return _snapshot(event="score_updated", status="scoring", score={}), 0

    monkeypatch.setattr(cli, "_request", request)
    assert cli.main(["score", "dead", "d4"]) == 0
    assert cli.main(["score", "seki", "Q16"]) == 0
    assert cli.main(["score", "resume"]) == 0
    assert [call[2] for call in calls] == [
        {"action": "dead", "point": "d4"},
        {"action": "seki", "point": "Q16"},
        {"action": "resume"},
    ]


def test_legacy_score_edits_accept_optional_revision(monkeypatch) -> None:
    calls = []

    def request(method, path, payload=None, **kwargs):
        calls.append((method, path, payload, kwargs))
        return _snapshot(event="score_updated", status="scoring", score={}), 0

    monkeypatch.setattr(cli, "_request", request)
    assert cli.main(["score", "dead", "D4", "--revision", "8"]) == 0
    assert cli.main(["score", "seki", "D4", "--revision", "9"]) == 0
    assert [call[2] for call in calls] == [
        {"action": "dead", "point": "D4", "revision": 8},
        {"action": "seki", "point": "D4", "revision": 9},
    ]
    assert all(call[1] == "/api/llm/score" for call in calls)


def test_reset_wake_is_nonzero(monkeypatch, capsys) -> None:
    monkeypatch.setattr(cli, "_request", lambda *args, **kwargs: (_snapshot(event="game_reset"), 0))
    assert cli.main(["wait"]) == 1
    assert "game_reset" in capsys.readouterr().out


def test_server_error_detail_uses_contract_message() -> None:
    assert cli._english_server_error({"code": "stale_revision", "message": "Stale score revision."}, 409) == "Stale score revision."
    assert cli._english_server_error("불법 수입니다: D4", 422) == "Illegal move: D4"
