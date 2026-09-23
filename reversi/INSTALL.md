# Install LLM Reversi

This guide is for a shell-capable assistant installing `llm-reversi` for a user. Use a release wheel when the user supplies a [GitHub Release](https://github.com/hehee9/board-games-with-llm/releases) URL, or install from a source checkout. Leave the server running with its browser page ready for a game.

## Install from a release

Confirm that the supplied HTTPS URL points to a release of `hehee9/board-games-with-llm`. Read `reversi/INSTALL.md` from that same release tag:

```text
https://github.com/hehee9/board-games-with-llm/blob/<release tag>/reversi/INSTALL.md
```

Download the single `llm_reversi-*-py3-none-any.whl` asset to a temporary directory. Report a mismatched release, absent wheel, or multiple matching wheels instead of choosing one arbitrarily.

Check `uv --version`. If `uv` is unavailable, use the current user-level method for the operating system and shell in the [official uv installation guide](https://docs.astral.sh/uv/getting-started/installation/). Use the installed executable directly if the current shell has not loaded an updated `PATH`; confirm `uv --version` before continuing.

Check whether `reversi` already resolves to a command, inspect its path and `--help` output, and inspect `uv tool list` and `uv tool dir --bin`. Preserve unrelated or unidentified commands and report a conflict. Install or replace only a confirmed `llm-reversi` tool:

```text
uv tool install <absolute path to downloaded wheel>
```

For a confirmed existing `llm-reversi` tool, use `uv tool install --force --reinstall-package llm-reversi <absolute path to downloaded wheel>`. Run `uv tool update-shell` if the directory from `uv tool dir --bin` is missing from the user's `PATH`. Find `reversi` (macOS/Linux) or `reversi.exe` (Windows) in that directory, then check `<reversi executable> --help`. Use its absolute path for the remaining steps.

## Install an assistant skill

For Codex, Claude Code, or OpenCode integration, find `llm_reversi/skills/play-llm-reversi/` under the installed tool directory returned by `uv tool dir`. Copy the **complete** `play-llm-reversi` directory to the selected assistant's skill location:

| Assistant | Skill location |
| --- | --- |
| Codex | `${CODEX_HOME:-~/.codex}/skills/play-llm-reversi` |
| Claude Code | `${CLAUDE_CONFIG_DIR:-~/.claude}/skills/play-llm-reversi` |
| OpenCode | `${OPENCODE_CONFIG_DIR:-~/.config/opencode}/skills/play-llm-reversi` |

Interpret `~` as the user's home directory and use `CODEX_HOME`, `CLAUDE_CONFIG_DIR`, or `OPENCODE_CONFIG_DIR` when set. Preserve an existing unmanaged destination and report the conflict. Confirm `SKILL.md` at the destination; the complete directory also contains Codex UI metadata in `agents/openai.yaml`. Start a new assistant session or task so a newly installed skill can be discovered. OpenCode also recognizes skills in the Claude Code location.

## Start the game

Run `<reversi executable> start` in a persistent process. From a separate shell, run `<reversi executable> status` and confirm the browser page at the local URL printed by `start` (default `http://127.0.0.1:8768`). A new server reports `setup`; an existing LLM Reversi game retains its state. Leave the server running for the user to choose the mode, color, and optional player names in the browser. See [README.md](README.md) for play commands.

## Run from source

Open the repository's `reversi/` folder, or the extracted source folder containing `pyproject.toml`. Python 3.11 or newer and `uv` are required:

```text
uv sync
uv run reversi --help
uv run reversi start
```

On Windows, `start.cmd` starts the source version. To install a command usable from another directory, build a wheel in the source folder and install the generated `llm_reversi-*-py3-none-any.whl` file from `dist/`:

```text
uv build --wheel
uv tool install <wheel-path>
uv tool update-shell
```

Check command ownership as described above before installing. On Windows, `install.ps1` installs from the source folder or accepts a local wheel through `-WheelPath`. It installs the Codex skill by default; `-Agent` accepts one or more of `codex`, `claude`, and `opencode`, for example:

```powershell
.\install.ps1 -Agent claude,opencode
```

The script preserves an existing skill directory unless it identifies that directory as its own managed installation. Check `reversi --help` and run `reversi start`.

Report the release tag and wheel asset when used, executable path and `--help` result, skill destination when selected, and server URL and game status.

## License

LLM Reversi is licensed under the [GNU General Public License v3.0 or later](LICENSE), preserving GPL attribution from the original LLM Chess application.
