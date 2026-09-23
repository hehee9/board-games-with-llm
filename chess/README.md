# LLM Chess

Play chess against an LLM in your browser, or watch two LLMs play. LLM players make their moves through the `chess` command-line tool; a local server manages the game.

## Install

Give a shell-capable LLM agent a [GitHub Release](https://github.com/hehee9/board-games-with-llm/releases) URL. It can install the release with `uv` and set up the `play-llm-chess` skill for Codex, Claude Code, or OpenCode.

Copy this request and replace `<release URL>`:

```text
Install and configure LLM Chess from this GitHub Release: <release URL>. Read chess/INSTALL.md from the same release tag, detect my operating system, install the play-llm-chess skill for the assistant I use (Codex, Claude Code, or OpenCode), preserve unrelated commands and unmanaged skills, verify the CLI, and leave the server ready for a game.
```

See [INSTALL.md](INSTALL.md) for the full installation guide.

## Start a game

Installation leaves the server running and opens the game in your browser. If you need to start the server later, run:

```text
chess start
```

Choose **Human vs LLM** or **LLM vs LLM** in the browser, then choose your color for a human game. You can change the interface language; it initially follows your browser language when supported, or uses English. In an LLM-vs-LLM game, moves come from the two LLM sessions while the browser shows a spectator view. **New game** remains available to return to setup.

In a human game, click a piece and its destination or drag it to move. The right panel shows whose turn it is, the last move, and move history. On promotion, choose a queen, rook, bishop, or knight. You can request to take back your latest move, subject to your opponent's approval. Use **Resign** to end the game or **New game** to return to setup.

## LLM CLI

Use `chess --help` for the full command list. Common commands are:

```text
chess status
chess wait
chess move e7e5
chess takeback request
chess takeback accept
chess takeback reject
chess resign
```

For an LLM-vs-LLM game, use a separate LLM session for each color and specify its color on every command:

```text
chess --color white status
chess --color white wait
chess --color white move e2e4
chess --color white takeback request
chess --color white takeback accept
chess --color white takeback reject
chess --color white resign
```

Use `--color black` for the black session. Moves accept UCI or SAN notation. By default, `chess move` waits for the opponent's reply or another game event. Add `--no-wait` to submit your move and check the outcome later. A takeback request blocks new moves until the opponent accepts or rejects it.

The bundled `play-llm-chess` skill can handle the LLM side of a human game or one color in an LLM-vs-LLM game in Codex, Claude Code, or OpenCode. The command-line tool also works directly without the skill.

## Game scope

The server runs one game at a time. LLM Chess supports legal moves, castling, en passant, promotion, check, checkmate, draw detection, takeback requests from either side, and resignation. Restarting the server returns the game to setup.

## License

LLM Chess is licensed under the [GNU General Public License v3.0 or later](LICENSE).
