# sub-memory-bootstrap

`sub-memory-bootstrap`은 로컬 `sub-memory` 프로젝트를 빠르게 온보딩하기 위한 Codex skill 배포 저장소입니다.

이 skill은 다음 작업을 한 번에 도와줍니다.

- 로컬 `sub-memory` 체크아웃 검증
- Python 가상환경 및 의존성 설치
- 설치 상태 확인
- project-local Codex MCP 등록 작성
- `AGENTS.md`에 `sub_memory` 사용 규칙 반영
- Codex, Gemini CLI, Claude Code용 MCP 설정 스니펫 생성
- 긴 멀티턴 세션에서 compact summary + `sub_memory` recall 흐름 사용 규칙 반영

실제 skill 본체는 [`sub-memory-bootstrap/`](./sub-memory-bootstrap) 디렉터리에 있습니다.

## 이 저장소의 용도

이 저장소는 메인 `sub-memory` 프로젝트를 이미 로컬에 받아둔 상태에서, 아래 항목을 한 번에 끝내고 싶을 때 사용합니다.

- 로컬 설치
- 로컬 `stdio` MCP 서버 검증
- project-scoped Codex 온보딩
- CLI 연동용 설정 스니펫 생성

현재 범위:

- 로컬 설치
- 로컬 stdio MCP
- project-local `.codex/config.toml`
- `AGENTS.md` 규칙 업데이트
- CLI 설정 가이드

현재 범위 밖:

- ChatGPT 앱 연동
- Gemini 앱 연동
- Claude 앱 원격 연동

## 저장소 구조

```text
.
├── README.md
├── LICENSE
└── sub-memory-bootstrap/
    ├── SKILL.md
    ├── scripts/
    │   ├── bootstrap_local.sh
    │   ├── configure_codex_project.py
    │   └── render_cli_snippets.py
    └── templates/
        └── AGENTS.default.md
```

## Codex에 skill 설치

저장소를 clone 합니다.

```bash
git clone https://github.com/TODOTODoTOdoTodotodo/sub-memory-bootstrap.git
cd sub-memory-bootstrap
```

Codex skill 디렉터리에 복사:

```bash
mkdir -p ~/.codex/skills
cp -R sub-memory-bootstrap ~/.codex/skills/
```

또는 심볼릭 링크:

```bash
mkdir -p ~/.codex/skills
ln -s "$(pwd)/sub-memory-bootstrap" ~/.codex/skills/sub-memory-bootstrap
```

`CODEX_HOME`를 따로 쓰는 환경이라면 `~/.codex/skills` 대신 `$CODEX_HOME/skills`에 두면 됩니다.

## skill이 하는 일

이 skill은 크게 세 단계를 처리합니다.

1. 대상 저장소가 실제 `sub-memory` 프로젝트인지 확인
2. 로컬 bootstrap 실행 + project-local Codex 온보딩 완료
3. 현재 머신 경로 기준 MCP 설정 스니펫 출력

### bootstrap 스크립트

아래처럼 메인 `sub-memory` 저장소 경로를 넘겨 실행합니다.

```bash
./sub-memory-bootstrap/scripts/bootstrap_local.sh /absolute/path/to/sub-memory
```

수행 내용:

- `.venv` 생성
- `requirements.txt` 설치
- editable install 수행
- `.env`가 없으면 `.env.example` 기준으로 생성
- project-local `sub_memory` MCP 등록용 `.codex/config.toml` 작성
- 필요하면 기본 `AGENTS.md` 템플릿 생성
- `AGENTS.md`에 `sub_memory` 사용 규칙 반영
  - 답변 전 recall
  - substantive turn 후 store
  - 필요 시 reinforce
  - 긴 멀티턴 세션은 compact summary 기반으로 이어가기

### project-local Codex 등록

```bash
python3 ./sub-memory-bootstrap/scripts/configure_codex_project.py \
  --project-dir /absolute/path/to/sub-memory
```

수행 내용:

- `/absolute/path/to/sub-memory/.codex/config.toml` 생성 또는 갱신
- `/absolute/path/to/sub-memory/AGENTS.md` 생성 또는 갱신
- 기존 파일의 unrelated content는 보존

### 설정 스니펫 생성기

```bash
python3 ./sub-memory-bootstrap/scripts/render_cli_snippets.py \
  --project-dir /absolute/path/to/sub-memory
```

출력 대상:

- Codex
- Gemini CLI
- Claude Code
- project-scoped Codex 등록 정보

## 예시 프롬프트

Codex에서 설치 후 아래처럼 요청하면 됩니다.

```text
Use sub-memory-bootstrap to install this repo locally and generate Codex, Gemini CLI, and Claude Code MCP config snippets.
```

```text
Use sub-memory-bootstrap to validate the local setup and tell me the exact sub-memory-mcp path for this repo.
```

```text
Use sub-memory-bootstrap to inspect this repo, verify the local install path, and draft a short onboarding note for another engineer.
```

## 한국어 예시

```text
sub-memory-bootstrap을 사용해서 이 저장소를 로컬에 설치하고 Codex, Gemini CLI, Claude Code용 MCP 설정 스니펫을 현재 머신 경로 기준으로 작성해줘.
```

```text
sub-memory-bootstrap으로 기존 설치 상태를 점검하고, 이 저장소에서 실제로 실행되는 sub-memory-mcp 경로를 알려줘.
```

```text
sub-memory-bootstrap으로 로컬 stdio MCP 서버가 바로 쓸 수 있는 상태인지 확인하고, project-local Codex 설정과 AGENTS.md까지 준비해줘.
```

## 대상 프로젝트 조건

이 skill은 메인 `sub-memory` 저장소를 대상으로 설계되어 있습니다. 대상 프로젝트에는 아래 파일이 있어야 합니다.

- `requirements.txt`
- `pyproject.toml`
- `mcp_server.py`
- `.env.example`

이 저장소는 `sub-memory` 애플리케이션 자체를 담고 있지 않습니다.  
Codex 온보딩 레이어만 배포합니다.

## 라이선스

MIT. 자세한 내용은 [LICENSE](./LICENSE)를 참고하세요.
