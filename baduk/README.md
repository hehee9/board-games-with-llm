# LLM Baduk

Play Go against an LLM, or watch two LLM sessions play each other. Start the game in your browser; human players use the board, while LLMs play through the `baduk` command-line tool.

Choose a 9×9, 13×13, or 19×19 board. The game supports captures, ko, passes, takebacks, and resignation. After two consecutive passes, players review the score using Korean-style territory counting and a fixed 6.5-point komi for White.

[Repository](https://github.com/hehee9/board-games-with-llm/tree/main/baduk) · [Issues](https://github.com/hehee9/board-games-with-llm/issues)

## Install and start

Give a shell-capable LLM agent a [GitHub Release](https://github.com/hehee9/board-games-with-llm/releases) URL. It can install the prebuilt Baduk wheel with `uv`, verify the command, and set up the `play-llm-baduk` skill for Codex, Claude Code, or OpenCode when requested.

Copy this request and replace `<release URL>`:

```text
Install and configure LLM Baduk from this GitHub Release: <release URL>. Read baduk/INSTALL.md from the same release tag, detect my operating system, install the play-llm-baduk skill for the assistant I use (Codex, Claude Code, or OpenCode), preserve unrelated commands and unmanaged skills, verify the CLI, and leave the server ready for a game.
```

See [INSTALL.md](INSTALL.md) for the full installation guide and source-based alternatives. Installation leaves the server running. To start it again later, run:

```text
baduk start
```

## Play

Starting the app opens the browser. Choose the language, game mode, board size, and player names. In human-vs-LLM mode, choose your color and play on the board. In LLM-vs-LLM mode, the browser shows the game while each LLM uses its own command-line session.

## Command-line play

The examples below use the installed `baduk` command. Use `baduk --help` for the full command list. When running from source, prefix each command with `uv run` (for example, `uv run baduk status`).

For human-vs-LLM play, the LLM can use:

```text
baduk status
baduk move D4
baduk move pass --no-wait
baduk wait
baduk takeback request
baduk takeback accept
baduk takeback reject
baduk resign
baduk score dead D4
baduk score seki D4
baduk score accept
baduk score resume
```

Coordinates use uppercase `A`–`T`, skipping `I`. By default, `move` waits for the opponent's response; `--no-wait` returns after submitting the move. Use `wait` when the session needs to pause until it can act again or the game ends or resets. `wait --after-revision N` starts waiting from a particular revision reported by `status`. A takeback needs the opponent's response before play continues.

After two consecutive passes, mark dead stones or seki and review the score; both players must accept it to finish. In a human-vs-LLM game, `score accept` can use the current revision automatically; `--revision N` is optional. Use `score resume` to continue playing if the score needs more work.

### Two LLMs

Run one independent LLM session for Black and one for White. Put `--color black` or `--color white` before **every** participant command, including `status`, `wait`, scoring, takebacks, and resignation. For example:

```text
baduk --color black status
baduk --color black move D4
baduk --color black wait
baduk --color white status
baduk --color white move pass --no-wait
baduk --color white takeback accept
baduk --color black score dead D4 --revision N
baduk --color white score seki D4 --revision N
baduk --color black score accept --revision N
baduk --color white score resume
```

Keep at most one pending `wait` per session, and run `status` after a game reset before continuing. The other session accepts or rejects a takeback request. During scoring, each colored `score dead`, `score seki`, and `score accept` command requires `--revision N` from a `status` whose position and score that session has reviewed. If the revision has changed, inspect the latest `status` and use its new revision. The second session must review the updated score after the first accepts; both acceptances finish the game. If they disagree, `score resume` returns to play.

## License

LLM Baduk is licensed under the [GNU General Public License v3.0 or later](LICENSE), with GPL attribution preserved from the original LLM Chess application.
