# LLM Reversi

LLM과 리버시를 두거나 두 LLM의 대국을 관전할 수 있습니다. 브라우저에서 대국을 시작하고, 사람은 화면의 판에서 수를 두며 LLM은 `reversi` 명령어로 돌을 놓습니다.

8×8 판에서 흑이 먼저 둡니다. 상대 돌을 가로·세로·대각선으로 끼우면 그 사이의 돌이 뒤집힙니다. 둘 수 있는 자리가 없는 쪽의 차례는 자동으로 넘어갑니다. 양쪽 모두 둘 수 없으면 돌이 많은 쪽이 이기고, 돌 수가 같으면 무승부입니다.

[English](README.md) · [저장소](https://github.com/hehee9/board-games-with-llm/tree/main/reversi) · [문제 제보](https://github.com/hehee9/board-games-with-llm/issues)

## 설치하고 시작하기

소스 저장소를 받은 뒤 `reversi/` 폴더에서 실행하세요.

```text
uv sync
uv run reversi start
```

Python 3.11 이상과 [uv](https://docs.astral.sh/uv/getting-started/installation/)가 필요합니다. 실행하면 로컬 브라우저 페이지가 열립니다. Windows에서는 `start.cmd`로도 소스 버전을 시작할 수 있습니다. 휠 설치와 Codex·Claude Code·OpenCode용 스킬 설정은 [INSTALL.md](INSTALL.md)에 있습니다.

## 대국하기

브라우저에서 사람 대 LLM 또는 LLM 대 LLM을 선택하세요. 사람이 참여하면 돌 색을 고르고, 참가자 이름은 필요할 때 입력하면 됩니다. 사람은 화면의 판에서 두고, LLM끼리 대국하면 각 LLM이 별도의 명령어 세션으로 두는 동안 브라우저에서 수가 놓이는 모습을 바로 볼 수 있습니다.

좌표는 **왼쪽 위 A1**부터 **오른쪽 아래 H8**까지입니다. 현재 둘 수 있는 자리는 `status`에 표시됩니다. 둘 수 없는 쪽의 차례가 자동으로 넘어가므로 한쪽이 연달아 실제 수를 둘 수도 있습니다.

## 명령어로 두기

아래 예시는 설치된 `reversi` 명령어를 사용합니다. 소스 폴더에서 실행할 때는 `uv run reversi status`처럼 앞에 `uv run`을 붙이세요. 명령 형식은 `reversi --help`에서 볼 수 있습니다.

```text
reversi status
reversi move D3
reversi wait
reversi takeback request
reversi takeback accept
reversi takeback reject
reversi resign
```

`move`는 기본적으로 다음 행동을 할 때까지 기다립니다. 돌을 놓자마자 명령을 끝내려면 `--no-wait`를 붙이세요. `wait --after-revision N`은 `status`에 나온 리비전 이후의 변화를 기다립니다. 무르기는 상대가 수락해야 적용되며, 요청자가 마지막으로 실제로 둔 수의 직전 상태로 돌아갑니다. 그 수로 뒤집힌 돌과 자동으로 넘어간 차례도 함께 복원됩니다.

### LLM끼리 대국하기

흑과 백을 각각 독립된 LLM 세션에서 맡습니다. `status`, `wait`, 무르기, 기권을 포함해 **매 명령마다** `--color black` 또는 `--color white`를 `reversi` 바로 뒤에 붙이세요.

```text
reversi --color black status
reversi --color black move D3
reversi --color black wait
reversi --color white status
reversi --color white takeback accept
reversi --color black resign
```

세션마다 대기 중인 명령은 하나만 두세요. 대국이 초기화되면 `status`로 새 판을 확인한 뒤 계속합니다. 무르기 요청은 상대 색을 맡은 세션에서 수락하거나 거절합니다.

## 라이선스

LLM Reversi는 [GNU General Public License v3.0 이상](LICENSE)에 따라 배포하며, 원본 LLM Chess의 GPL 저작권 표시를 유지합니다.
