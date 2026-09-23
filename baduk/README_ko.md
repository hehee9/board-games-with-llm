# LLM Baduk

LLM과 바둑을 두거나 두 LLM의 대국을 관전할 수 있는 프로그램입니다. 브라우저에서 대국을 시작하고 사람은 바둑판에서, LLM은 `baduk` 명령어로 수를 둡니다.

9×9·13×13·19×19 바둑판을 선택할 수 있습니다. 돌 따내기, 패, 패스, 무르기, 기권을 지원합니다. 양쪽이 연달아 패스하면 계가를 시작하며, 한국식 집 계산을 적용하고 백에게 덤 6.5집을 줍니다.

[저장소](https://github.com/hehee9/board-games-with-llm/tree/main/baduk) · [문제 제보](https://github.com/hehee9/board-games-with-llm/issues)

## 설치하고 시작하기

명령어를 실행할 수 있는 LLM 에이전트에게 [GitHub 릴리스](https://github.com/hehee9/board-games-with-llm/releases) 주소를 전달하세요. 에이전트가 미리 빌드된 바둑 프로그램을 `uv`로 설치하고 명령어를 확인하며, 요청하면 Codex·Claude Code·OpenCode에서 사용할 `play-llm-baduk` 스킬도 설정할 수 있습니다.

다음 요청에서 `<release URL>`을 실제 릴리스 주소로 바꿔 전달하면 됩니다.

```text
Install and configure LLM Baduk from this GitHub Release: <release URL>. Read baduk/INSTALL.md from the same release tag, detect my operating system, install the play-llm-baduk skill for the assistant I use (Codex, Claude Code, or OpenCode), preserve unrelated commands and unmanaged skills, verify the CLI, and leave the server ready for a game.
```

전체 설치 절차와 소스에서 실행하는 방법은 [INSTALL.md](INSTALL.md)에 있습니다. 설치가 끝나면 서버가 실행된 상태로 남습니다. 나중에 다시 시작할 때는 다음 명령을 사용하세요.

```text
baduk start
```

## 대국하기

프로그램을 시작하면 브라우저가 열립니다. 언어, 대국 방식, 판 크기, 참가자 이름을 선택하세요. 사람과 LLM이 대국할 때는 자신의 돌 색을 고른 뒤 화면의 바둑판에서 수를 둡니다. LLM끼리 대국할 때는 브라우저에서 대국을 관전하고, 각 LLM은 별도의 명령어 세션을 사용합니다.

## 명령어로 두기

아래 예시는 설치된 `baduk` 명령어입니다. 전체 명령은 `baduk --help`에서 확인할 수 있습니다. 소스 폴더에서 실행할 때는 각 명령 앞에 `uv run`을 붙이세요(예: `uv run baduk status`).

사람과 대국하는 LLM은 다음 명령을 사용합니다.

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

좌표는 대문자 `A`부터 `T`까지 쓰되 `I`는 건너뜁니다. `move`는 기본적으로 상대의 응답을 기다리고, `--no-wait`를 붙이면 수를 둔 직후 돌아옵니다. 다음 행동 차례가 오거나 대국이 끝나거나 초기화될 때까지 기다리려면 `wait`를 사용하세요. `wait --after-revision N`은 `status`에 표시된 특정 리비전부터 변화를 기다립니다. 무르기를 요청한 뒤에는 상대가 수락하거나 거절해야 대국을 이어갈 수 있습니다.

양쪽이 연달아 패스하면 사석과 빅을 표시하고 점수를 확인합니다. 양쪽 모두 점수를 수락해야 대국이 끝납니다. 사람과 대국할 때는 `score accept`가 현재 리비전을 자동으로 사용하므로 `--revision N`은 선택 사항입니다. 계가를 멈추고 다시 두려면 `score resume`을 사용하세요.

### LLM끼리 대국하기

흑과 백에 각각 독립된 LLM 세션을 사용합니다. `status`, `wait`, 계가, 무르기, 기권을 포함해 **매 명령마다** `--color black` 또는 `--color white`를 붙이세요. 색상은 `baduk` 바로 뒤에 놓습니다.

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

세션마다 대기 중인 `wait`는 하나만 두고, 대국이 초기화되면 `status`로 상태를 새로 확인하세요. 무르기 요청은 상대 세션이 수락하거나 거절합니다. 계가 중 색상을 지정한 `score dead`, `score seki`, `score accept` 명령에는 해당 세션이 판과 점수를 검토한 `status`의 `--revision N`이 필요합니다. 그 사이 리비전이 바뀌었다면 최신 `status`를 확인하고 새 리비전을 사용하세요. 한쪽이 수락한 뒤 다른 쪽은 갱신된 점수를 다시 검토해야 합니다. 양쪽 모두 수락하면 대국이 끝나고, 의견이 다르면 `score resume`으로 대국을 이어갑니다.

## 라이선스

LLM Baduk은 [GNU General Public License v3.0 이상](LICENSE)에 따라 배포하며, 원본 LLM Chess의 GPL 저작권 표시를 유지합니다.
