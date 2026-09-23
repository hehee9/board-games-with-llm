# LLM Reversi

Play Reversi against an LLM, or watch two independent LLM sessions play each other. Start a game in your browser; human players use the board, while LLMs place discs through the `reversi` command-line tool.

The 8×8 board starts with Black. A move brackets and flips opposing discs in any of eight directions. If a player has no legal move, their turn passes automatically. When neither player can move, the player with more discs wins; equal counts are a draw.

[한국어](README_ko.md) · [Repository](https://github.com/hehee9/board-games-with-llm/tree/main/reversi) · [Issues](https://github.com/hehee9/board-games-with-llm/issues)

## Install and start

From a source checkout, open the `reversi/` folder and run:

```text
uv sync
uv run reversi start
```

This requires Python 3.11 or newer and [uv](https://docs.astral.sh/uv/getting-started/installation/). Starting the app opens the local browser page. On Windows, `start.cmd` also starts the source version. See [INSTALL.md](INSTALL.md) for wheel installation and assistant skill setup for Codex, Claude Code, or OpenCode.

## Play

In the browser, choose human-vs-LLM or LLM-vs-LLM, choose the human's color when applicable, and optionally enter player names. In a human-vs-LLM game, play your moves on the board. In an LLM-vs-LLM game, the browser displays moves live while each LLM uses its own command-line session.

Coordinates run from **A1 at the upper-left** to **H8 at the lower-right**. The current `status` lists legal moves. The game skips a turn automatically when that player has no legal move, so the same player can make consecutive actual moves.

## Command-line play

These examples use the installed `reversi` command. From source, prefix commands with `uv run`, such as `uv run reversi status`. Run `reversi --help` for command syntax.

```text
reversi status
reversi move D3
reversi wait
reversi takeback request
reversi takeback accept
reversi takeback reject
reversi resign
```

`move` waits until the next action by default. Add `--no-wait` to return immediately after placing a disc. `wait --after-revision N` waits for a change after the revision shown by `status`. A takeback request needs the opponent's approval; acceptance restores the position before the requester's last actual move, including any flips and automatic passes.

### Two LLMs

Use independent sessions for Black and White. Put `--color black` or `--color white` before **every** participant command, including `status`, `wait`, takebacks, and resignation:

```text
reversi --color black status
reversi --color black move D3
reversi --color black wait
reversi --color white status
reversi --color white takeback accept
reversi --color black resign
```

Keep one pending wait per session. After a game reset, run `status` to read the new position before continuing. Each session handles only its own color; a takeback request is answered by the other session.

## License

LLM Reversi is licensed under the [GNU General Public License v3.0 or later](LICENSE), preserving GPL attribution from the original LLM Chess application.
