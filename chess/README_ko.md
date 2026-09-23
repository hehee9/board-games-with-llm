# LLM Chess

LLM Chess는 간편하게 LLM으로 체스 플레이가 가능하도록 만든 Skill 및 체스 프로그램입니다. 사람 vs LLM 대결과 LLM vs LLM 대결을 모두 지원하며, LLM은 CLI 환경에서 플레이하게 됩니다. 로컬 서버에서 게임 진행을 관리하며, 브라우저에서 LLM vs LLM 게임 관전도 가능합니다.

## 설치하기

권장 설치 방법은 LLM 에이전트에게 `hehee9/board-games-with-llm`의 GitHub Release URL을 제공하는 것입니다. 운영체제에 따라 `uv`를 사용해 릴리스 wheel 파일을 설치 및 검증한 후, 선택적으로 Codex 스킬까지 설정합니다.

다음은 예시 설치 프롬프트입니다. `<release URL>` 부분을 변경해 사용하세요:

```text
Install and configure LLM Chess from this GitHub Release: <release URL>. Read chess/INSTALL.md from the same release tag, detect my operating system, preserve unrelated commands and unmanaged skills, verify the CLI, and leave the server ready for a game.
```

전체 설치 절차는 [INSTALL.md](INSTALL.md)에서 확인할 수 있습니다.

## 게임 시작하기

프로그램을 시작하면 브라우저 URL이 자동으로 열립니다. 서버가 아직 실행 중이지 않다면 다음 명령어로 시작하세요:

```text
chess start
```

브라우저가 열리면 새 대국 설정에서 **인간 vs LLM** 또는 **LLM vs LLM** 모드를 선택합니다. LLM vs LLM 모드에서는 브라우저가 관전 화면이 되어 게임 상호작용이 불가능해집니다. UI의 언어 선택 또한 지원하며, 기본값은 브라우저 언어로 맞춰집니다.

인간 vs LLM 모드에서는 말을 선택한 뒤 이동할 위치를 클릭하거나, 말을 드래그하여 이동할 수 있습니다. 우측 화면에 현재 차례, 마지막 수, 수순 기록이 표시됩니다. 폰의 프로모션 4종(퀸/룩/비숍/나이트)을 지원하며, 상대방의 동의 시 **무르기** 또한 가능합니다. **기권**으로 즉시 게임을 포기할 수 있고, **새 대국**을 클릭하면 설정 화면으로 돌아갑니다.

## LLM CLI

LLM은 `chess --help`로 게임 조작 방법을 확인할 수 있습니다. 대표 명령어 목록은 다음과 같습니다:

```text
chess status
chess wait
chess move e7e5
chess takeback request
chess takeback accept
chess takeback reject
chess resign
```

`chess move`는 UCI 또는 SAN 표기법을 지원합니다. 기본적으로 상대가 수를 선택할 때까지 CLI가 사용 중 상태를 유지하지만, `--no-wait` 옵션으로 자신의 수만 둔 뒤 결과는 나중에 확인할 수도 있습니다.

LLM vs LLM 모드에서는 색상마다 독립된 세션을 하나씩 실행합니다. 매 명령 입력마다 해당 세션의 색을 지정해야 합니다.

```text
chess --color white status
chess --color white wait
chess --color white move e2e4
chess --color white takeback request
chess --color white takeback accept
chess --color white takeback reject
chess --color white resign
```

무르기 요청은 상대 세션이 수락하거나 거절할 때까지 새 수를 둘 수 없습니다.

Codex에서는 동봉된 `play-llm-chess` Skill로 빠르게 대국을 시작할 수 있으며, Skill이 없어도 CLI로 직접 사용할 수 있습니다.

## 게임 지원 범위

서버는 동시에 하나의 게임만 진행할 수 있습니다. 표준 체스 규칙에 따른 이동, 캐슬링, 앙파상, 프로모션, 체크, 체크메이트, 스테일메이트, 양측의 무르기 요청 및 기권을 지원합니다. 서버를 재시작하면 새로운 준비(setup) 상태로 시작됩니다.

## 라이선스

LLM Chess는 [GNU General Public License v3.0 이상](LICENSE)에 따라 배포됩니다.