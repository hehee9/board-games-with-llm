# LLM Connect Four

Play Connect Four against an LLM, or watch two independent LLM sessions play. Start a game in the browser; human players choose columns on the board, while LLMs use the `connect4` command-line tool.

The 7-column, 6-row board starts with Red. Drop a disc into columns 1–7 to connect four horizontally, vertically, or diagonally. A full board without a winner is a draw. Games support player names, takeback requests, resignation, and starting a new game.

[한국어](README_ko.md) · [Repository](https://github.com/hehee9/board-games-with-llm/tree/main/connect4) · [Issues](https://github.com/hehee9/board-games-with-llm/issues)

## Install and start

See [INSTALL.md](INSTALL.md) for installation from a GitHub Release or source, including the `play-llm-connect4` skill for Codex, Claude Code, or OpenCode. Once installed, start the local server with:

```text
connect4 start
```

The browser opens at `http://127.0.0.1:8767` by default. Choose human vs. LLM or CLI vs. CLI, your color when playing as a human, and optional names for Red and Yellow. The browser updates live as moves arrive. In CLI-vs-CLI mode, give each color its own LLM session.

## Command-line play

The following examples use the installed `connect4` command. From a source checkout, prefix each command with `uv run`. Run `connect4 --help` for options.

In a human-vs-LLM game, the LLM can use:

```text
connect4 status
connect4 move 4
connect4 wait
connect4 takeback request
connect4 takeback accept
connect4 takeback reject
connect4 resign
```

Read `legal_columns` from `status` and submit one of those column numbers. `move` waits until the LLM can act again or the game changes; `move 4 --no-wait` returns immediately after placing the disc. `wait` pauses until the LLM can act, a takeback needs a response, or the game ends or resets. A takeback request needs the other player's acceptance or rejection. When accepted, it removes the requester's most recent move and any moves made after it.

### Two LLMs

Run separate sessions for Red and Yellow. Put `--color red` or `--color yellow` immediately after `connect4` on every participant command:

```text
connect4 --color red status
connect4 --color red move 4
connect4 --color red wait
connect4 --color yellow status
connect4 --color yellow move 3 --no-wait
connect4 --color yellow takeback accept
connect4 --color red resign
```

Each session reads the latest state and responds to the other session's takeback requests. Keep one pending wait per session. After a game reset, run `status` again before continuing.

## License

LLM Connect Four is licensed under the [GNU General Public License v3.0 or later](LICENSE). It retains the GPL attribution from the original LLM Chess application.
