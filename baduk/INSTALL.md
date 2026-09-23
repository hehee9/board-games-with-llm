# Install LLM Baduk

Give a shell-capable LLM agent a specific [GitHub Release](https://github.com/hehee9/board-games-with-llm/releases) URL for `hehee9/board-games-with-llm`. The agent can install the wheel, add the `play-llm-baduk` skill for Codex, Claude Code, or OpenCode, and leave the game ready in your browser.

## Select the release

Confirm that the URL uses HTTPS and points to a release of `hehee9/board-games-with-llm`. Read `baduk/INSTALL.md` from the same release tag and follow that guide for the selected release:

```text
https://github.com/hehee9/board-games-with-llm/blob/<release tag>/baduk/INSTALL.md
```

Download the single `llm_baduk-*-py3-none-any.whl` asset from that release to a temporary directory. Report a mismatched release, missing wheel, or multiple matching wheels rather than guessing.

## Install the command

Check `uv --version`. If `uv` is unavailable, detect the operating system and shell and use the current user-level method in the [official uv installation guide](https://docs.astral.sh/uv/getting-started/installation/). If the current shell has not loaded its updated `PATH`, use the installed `uv` executable directly. Confirm `uv --version` before continuing; `uv` supplies the required Python runtime.

Check whether `baduk` already resolves to a command, and inspect its path and `--help` output. Also run `uv tool list` and check the directory returned by `uv tool dir --bin`. Preserve unrelated or unidentified commands and report a conflict; only replace a confirmed `llm-baduk` installation.

Install the downloaded wheel as a user-level tool:

```text
uv tool install <absolute path to downloaded wheel>
```

For a confirmed existing `llm-baduk` tool, use `uv tool install --force --reinstall-package llm-baduk <absolute path to downloaded wheel>`. If the directory returned by `uv tool dir --bin` is missing from the user's `PATH`, run `uv tool update-shell`. Find `baduk` (macOS/Linux) or `baduk.exe` (Windows) in that directory and use its absolute path as `<baduk executable>` for the rest of the installation. Check the installed command with:

```text
<baduk executable> --help
```

## Add the assistant skill

Find `llm_baduk/skills/play-llm-baduk/` under `uv tool dir`. Copy the **whole** packaged skill folder, including `SKILL.md` and `agents/openai.yaml`, to the directory for each assistant you use:

| Assistant | Skill directory |
| --- | --- |
| Codex | `$CODEX_HOME/skills/play-llm-baduk`, or `~/.codex/skills/play-llm-baduk` when `CODEX_HOME` is unset |
| Claude Code | `$CLAUDE_CONFIG_DIR/skills/play-llm-baduk`, or `~/.claude/skills/play-llm-baduk` when `CLAUDE_CONFIG_DIR` is unset |
| OpenCode | `$OPENCODE_CONFIG_DIR/skills/play-llm-baduk`, or `~/.config/opencode/skills/play-llm-baduk` when `OPENCODE_CONFIG_DIR` is unset |

From the source folder on Windows, `.\install.ps1 -Agent codex`, `.\install.ps1 -Agent claude`, or `.\install.ps1 -Agent opencode` installs the selected skill as well as the command; select multiple assistants with `.\install.ps1 -Agent claude,opencode`. With no `-Agent`, the script installs the command only. It preserves an existing skill that it did not install and updates only its own marked installation. When installing manually, preserve an existing skill directory and report a conflict rather than replacing it. Start a new assistant session to discover the skill. The `baduk` command also works without a skill.

## Start the game

Run `<baduk executable> start` in a persistent process. From a separate shell, run `<baduk executable> status` and confirm that the browser page is available at the local URL printed by `start`. A new server reports `setup` in the **Status** field; an existing LLM Baduk game retains its current state. Leave the server running for the user to choose the game mode, board size, and player names. If another application occupies the local address, report the conflict while leaving that application running. See [README.md](README.md) for play commands.

## Run from source

For a source checkout, open the repository's `baduk/` folder. For a standalone source archive, extract it and open the folder containing `pyproject.toml`. This workflow requires Python 3.11 or newer and `uv`:

```text
uv sync
uv run baduk --help
uv run baduk start
```

On Windows, `start.cmd` starts the source version. To use the command from another directory, build a wheel in that source folder and install the generated file from `dist/`:

```text
uv build --wheel
uv tool install <wheel-path>
uv tool update-shell
```

Replace `<wheel-path>` with the generated `llm_baduk-*-py3-none-any.whl` path. Check command ownership as above before installing, then run `baduk --help` and `baduk start`. On Windows, `install.ps1` installs from the source folder or accepts a local wheel through `-WheelPath`; it checks for an existing `baduk` command. Add `-Agent` to install a skill for the selected assistant or assistants.

At the end, report the release tag and wheel asset, executable path and `--help` result, skill status for each selected assistant, and server URL and game status.

## License

LLM Baduk is licensed under the [GNU General Public License v3.0 or later](LICENSE), with GPL attribution preserved from the original LLM Chess application.
