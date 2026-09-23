# LLM Connect Four

LLM과 커넥트 포를 두거나 두 LLM의 대국을 관전할 수 있습니다. 브라우저에서 대국을 시작한 뒤 사람은 화면의 판에서 열을 고르고, LLM은 `connect4` 명령어로 수를 둡니다.

판은 가로 7칸, 세로 6칸이며 빨강이 먼저 둡니다. 1~7번 열에 원반을 떨어뜨려 가로·세로·대각선으로 네 개를 이으면 승리합니다. 승자 없이 판이 가득 차면 무승부입니다. 참가자 이름, 무르기 요청, 기권, 새 대국도 지원합니다.

[English](README.md) · [저장소](https://github.com/hehee9/board-games-with-llm/tree/main/connect4) · [문제 제보](https://github.com/hehee9/board-games-with-llm/issues)

## 설치하고 시작하기

[INSTALL.md](INSTALL.md)에 GitHub 릴리스 또는 소스에서 설치하는 방법과 Codex·Claude Code·OpenCode용 `play-llm-connect4` 스킬 설치 방법이 있습니다. 설치 후 다음 명령으로 로컬 서버를 시작하세요.

```text
connect4 start
```

기본 주소는 `http://127.0.0.1:8767`이며 브라우저가 열립니다. 사람 대 LLM 또는 CLI 대 CLI를 선택하고, 사람으로 두는 경우 자신의 색을 고르세요. 빨강과 노랑의 이름은 선택해서 입력할 수 있습니다. 수가 놓일 때마다 브라우저에도 바로 반영됩니다. CLI 대 CLI에서는 두 색에 각각 독립된 LLM 세션을 사용합니다.

## 명령어로 두기

아래는 설치된 `connect4` 명령어의 예시입니다. 소스 폴더에서 실행할 때는 각 명령 앞에 `uv run`을 붙이세요. 전체 옵션은 `connect4 --help`에서 확인할 수 있습니다.

사람과 대국하는 LLM은 다음 명령을 사용할 수 있습니다.

```text
connect4 status
connect4 move 4
connect4 wait
connect4 takeback request
connect4 takeback accept
connect4 takeback reject
connect4 resign
```

`status`의 `legal_columns`에 나온 열 번호 중 하나를 선택해 두세요. `move`는 다음 행동 차례가 오거나 대국 상태가 바뀔 때까지 기다립니다. `move 4 --no-wait`는 수를 둔 직후 돌아옵니다. `wait`는 다음 차례, 무르기 응답, 대국 종료 또는 초기화를 기다립니다. 무르기는 상대가 수락하거나 거절해야 처리됩니다. 수락하면 요청자가 가장 최근에 둔 수와 그 뒤에 둔 수를 함께 되돌립니다.

### LLM끼리 대국하기

빨강과 노랑에 각각 독립된 세션을 사용합니다. 모든 참가자 명령에서 `connect4` 바로 뒤에 `--color red` 또는 `--color yellow`를 넣으세요.

```text
connect4 --color red status
connect4 --color red move 4
connect4 --color red wait
connect4 --color yellow status
connect4 --color yellow move 3 --no-wait
connect4 --color yellow takeback accept
connect4 --color red resign
```

각 세션에서 최신 상태를 확인하고 상대 세션의 무르기 요청에 응답하세요. 세션마다 대기 중인 `wait`는 하나만 두고, 대국이 초기화되면 `status`로 새 상태를 확인하세요.

## 라이선스

LLM Connect Four는 [GNU General Public License v3.0 이상](LICENSE)에 따라 배포하며, 원본 LLM Chess의 GPL 저작권 표시를 유지합니다.
