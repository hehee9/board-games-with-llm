# Install LLM Chess

Give a shell-capable LLM agent a specific [GitHub Release](https://github.com/hehee9/board-games-with-llm/releases) URL for `hehee9/board-games-with-llm`. The agent can install the wheel for your operating system, add the Codex skill when applicable, and leave the game ready in your browser.

## Select the release

Confirm that the URL uses HTTPS and points to a release of `hehee9/board-games-with-llm`. Read `chess/INSTALL.md` from the same release tag and follow that guide for the selected release:

```text
https://github.com/hehee9/board-games-with-llm/blob/<release tag>/chess/INSTALL.md
```

Download the single `llm_chess-*-py3-none-any.whl` asset from that release to a temporary directory. Report a mismatched release, missing wheel, or multiple matching wheels rather than guessing.

## Install the command

Check `uv --version`. If `uv` is unavailable, detect the operating system and shell and use the current user-level method in the [official uv installation guide](https://docs.astral.sh/uv/getting-started/installation/). If the current shell has not loaded its updated `PATH`, use the installed `uv` executable directly. Confirm `uv --version` before continuing; `uv` supplies the required Python runtime.

Check whether `chess` already resolves to a command, and inspect its path and `--help` output. Also run `uv tool list` to identify any installed tool providing `chess`. Preserve unrelated or unidentified commands and report a conflict; only replace a confirmed LLM Chess installation.

Install the downloaded wheel as a user-level tool:

```text
uv tool install <absolute path to downloaded wheel>
uv tool dir --bin
```

If the tool executable directory is missing from the user's `PATH`, run `uv tool update-shell`. Find `chess` (macOS/Linux) or `chess.exe` (Windows) in that directory and use its absolute path as `<chess executable>` for the rest of the installation. Check the installed command with:

```text
<chess executable> --help
```

## Add the Codex skill

For Codex installation or an explicit request for Codex integration, find `llm_chess/skills/play-llm-chess/` under `uv tool dir`. Its `SKILL.md` and `agents/openai.yaml` files must be present. Use `CODEX_HOME` when set, or `.codex` in the user's home directory, and set these paths:

```text
<CODEX_HOME>/skills/play-llm-chess
<CODEX_HOME>/skills/play-llm-chess.llm-chess-managed
```

The second path is an ownership marker containing exactly `llm-chess:play-llm-chess`. Preserve an existing skill without that marker, or with a different marker, and report the conflict. For a new skill or an existing skill with the exact marker, copy the complete packaged skill to a sibling staging directory and validate both files there before placing it at the destination. When replacing a managed skill, retain the previous directory and restore it if replacement fails. Write the marker for a new installation, and confirm both files at the destination. Open a new Codex task to discover the skill. Other LLM environments can use the installed command directly.

## Start the game

Run `<chess executable> start` in a persistent process. From a separate shell, run `<chess executable> status` and confirm that the browser page is available at the local URL printed by `start`. A new server reports `setup` in the **Status** field; an existing LLM Chess game retains its current state. Leave the server running for the user to choose a color and play. If another application occupies the local address, report the conflict while leaving that application running.

At the end, report the release tag and wheel asset, executable path and `--help` result, Codex skill status when applicable, and server URL and game status.
