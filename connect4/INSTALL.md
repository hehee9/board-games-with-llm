# Install LLM Connect Four

This guide is for installing the `connect4` command and the optional `play-llm-connect4` assistant skill. It supports a release wheel when one is available, or a source checkout. The game runs locally; the default address is `http://127.0.0.1:8767`.

## Install from a release

Choose a specific [GitHub Release](https://github.com/hehee9/board-games-with-llm/releases) of `hehee9/board-games-with-llm`. Read `connect4/INSTALL.md` at the same release tag:

```text
https://github.com/hehee9/board-games-with-llm/blob/<release tag>/connect4/INSTALL.md
```

Download the single `llm_connect4-*-py3-none-any.whl` asset from that release. If the release has no matching wheel or more than one, report that instead of selecting an unrelated asset.

Install [uv](https://docs.astral.sh/uv/getting-started/installation/) for your operating system if needed, and confirm `uv --version`. Before installing, check whether `connect4` already resolves to a command. Inspect its path, `--help`, `uv tool list`, and `uv tool dir --bin`; preserve an unrelated or unidentified command and report the name conflict. Install the wheel as a user-level tool:

```text
uv tool install <absolute path to downloaded wheel>
```

For a confirmed existing `llm-connect4` tool, use `uv tool install --force --reinstall-package llm-connect4 <absolute path to downloaded wheel>`. Run `uv tool update-shell` if the directory from `uv tool dir --bin` is absent from `PATH`. Locate `connect4` (macOS/Linux) or `connect4.exe` (Windows) there and check:

```text
<connect4 executable> --help
```

## Install the assistant skill

Find `llm_connect4/skills/play-llm-connect4/` in the installed package under `uv tool dir`. Copy the **whole** `play-llm-connect4` directory, including `SKILL.md` and `agents/openai.yaml`, to the skill directory for each assistant you use:

| Assistant | Skill destination |
| --- | --- |
| Codex | `$CODEX_HOME/skills/play-llm-connect4`, or `~/.codex/skills/play-llm-connect4` when unset |
| Claude Code | `$CLAUDE_CONFIG_DIR/skills/play-llm-connect4`, or `~/.claude/skills/play-llm-connect4` when unset |
| OpenCode | `$OPENCODE_CONFIG_DIR/skills/play-llm-connect4`, or `~/.config/opencode/skills/play-llm-connect4` when unset |

OpenCode also recognizes the Claude Code skill directory. Preserve any existing destination that you do not own, and report a conflict instead of replacing it. Confirm the two packaged files at each destination. Start a new assistant task or session to discover the new skill.

## Start the game

Run `<connect4 executable> start` in a persistent process. In another shell, run `<connect4 executable> status` and open the local address in the browser. A fresh server reports `setup`; use the browser to choose human vs. LLM or CLI vs. CLI, color when applicable, and optional player names. Leave the server running during play. See [README.md](README.md) for moves and other commands.

## Run from source

Open the repository's `connect4/` directory, or the directory containing `pyproject.toml` in a source archive. This route requires Python 3.11 or newer and `uv`:

```text
uv sync
uv run connect4 --help
uv run connect4 start
```

On Windows, `start.cmd` starts the source version. To install a reusable command from this source folder, build a wheel and install the generated file from `dist/`:

```text
uv build --wheel
uv tool install <wheel-path>
uv tool update-shell
```

Replace `<wheel-path>` with the generated `llm_connect4-*-py3-none-any.whl` path. Check command ownership as described above. On Windows, `install.ps1` installs from the source folder or accepts a local wheel with `-WheelPath`. It installs the Codex skill by default. Use `-Agent` to select one or more assistants, for example:

```powershell
.\install.ps1 -Agent claude,opencode
.\install.ps1 -WheelPath .\dist\llm_connect4-0.1.0-py3-none-any.whl -Agent codex,claude
```

The script replaces only a skill previously marked as managed by this game; it preserves other same-name skill directories. The skill also lives at `src/llm_connect4/skills/play-llm-connect4/` in the source tree and can be copied to the destinations above.

At the end, report the installed wheel or source path, executable path and `--help` result, selected skill destinations, server URL, and game status.

## License

LLM Connect Four is licensed under the [GNU General Public License v3.0 or later](LICENSE), with GPL attribution retained from the original LLM Chess application.
