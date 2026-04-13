# Getting Started

이 문서는 GitHub 저장소 `sub-memory-bootstrap`을 clone한 뒤, `Codex`, `Gemini CLI`, `Claude Code`에 로컬 `stdio` MCP 서버로 연결하는 가장 짧은 시작 경로를 정리합니다.

범위는 로컬 설치와 CLI 연동까지입니다. 앱 연동(`ChatGPT 앱`, `Gemini 앱`, `Claude 앱`)은 현재 TODO로 남겨둡니다.

## 0. Codex에서 바로 시작

터미널형 에이전트 안에서 가장 짧게 시작하려면 아래 순서로 진행합니다.

### 0-1. skill-installer로 Codex skill 설치

Codex 안에서 `skill-installer`를 사용해 GitHub 저장소 경로로 `sub-memory-bootstrap` skill을 설치합니다.

예시:

```text
skill-installer를 사용해서 https://github.com/TODOTODoTOdoTodotodo/sub-memory-bootstrap/tree/main/sub-memory-bootstrap 경로의 skill을 설치해줘.
```

설치가 끝나면 Codex를 재시작합니다. 새 skill은 재시작 후 인식되는 것이 기준입니다.

### 0-2. Codex 새 세션 시작 후 설치 요청

Codex를 다시 시작한 뒤, `sub-memory`를 붙일 현재 저장소 루트에서 새 세션을 엽니다. 그 다음 아래처럼 요청합니다.

```text
sub-memory-bootstrap으로 현재 저장소를 설치하고 project-local Codex MCP 설정, AGENTS.md 규칙, 설치 검증까지 완료해줘.
```

이 단계가 끝나면 아래가 준비됩니다.

- `.venv`
- `.env`
- `.codex/config.toml`
- `AGENTS.md`

필요하면 이 시점에 저장소가 아직 없다면 아래처럼 받은 뒤 진행합니다.

```bash
git clone https://github.com/TODOTODoTOdoTodotodo/sub-memory-bootstrap.git
cd sub-memory-bootstrap
```

### 0-3. MCP 연결 확인

새 Codex 세션에서 `mcp status`를 확인했을 때 `sub_memory`가 보여야 합니다.

기대 상태 예시:

```text
sub_memory
  Tools: get_memory_status, recall_associated_memory, reinforce_memory, store_memory
```

연결 확인용 자연어 예시:

```text
sub_memory MCP 연결 상태를 확인하고 get_memory_status를 호출해서 현재 db_path와 node_count를 보여줘.
```

### 0-4. 최초 기억 확인

처음에는 `node_count = 0`일 수 있습니다. 그 상태에서 첫 기억을 하나 저장하고 바로 다시 조회해 보면 됩니다.

예시:

```text
이 내용을 기억으로 저장해. "이 저장소의 기본 목적은 Codex에서 sub_memory MCP로 세션 간 기억을 이어가는 것이다."
```

그 다음:

```text
방금 저장한 기억을 recall_associated_memory로 다시 찾아줘.
```

이 흐름이 되면 설치, 재시작, MCP 연결, 최초 기억 확인까지 끝난 상태입니다.

## 1. 준비 사항

- Python `3.10+`
- macOS 기준 권장 버전: `python3.11`
- 로컬에서 로드 가능한 `sqlite-vec`
- OpenAI API Key
  - `sub-memory-agent` 실행 시 필요
  - `sub-memory-mcp`만 사용할 때는 없어도 됨

## 2. 로컬 설치

먼저 GitHub 저장소를 clone 합니다.

```bash
git clone https://github.com/TODOTODoTOdoTodotodo/sub-memory-bootstrap.git
cd sub-memory-bootstrap
```

그 다음 저장소 루트에서 실행합니다.

```bash
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install -e .
cp .env.example .env
```

`.env` 파일에서 필요한 값을 채웁니다.

```dotenv
OPENAI_API_KEY=sk-your-key
OPENAI_MODEL=gpt-5-mini
EMBEDDING_MODEL_NAME=all-MiniLM-L6-v2
SQLITE_VEC_PATH=
RECALL_DEPTH=2
RECALL_LIMIT=6
MEMORY_DB_PATH=memory.db
COMPACT_AFTER_TURNS=4
COMPACT_KEEP_RECENT_TURNS=2
COMPACT_SUMMARY_CHAR_LIMIT=2400
```

compact 관련 기본값 의미:

- `COMPACT_AFTER_TURNS`
  - 이 횟수만큼 non-empty user turn이 쌓이면 오래된 세션 내용을 compact 후보로 봅니다.
- `COMPACT_KEEP_RECENT_TURNS`
  - compact 후에도 원문에 가깝게 남겨둘 최근 턴 수입니다.
- `COMPACT_SUMMARY_CHAR_LIMIT`
  - compact된 working summary의 최대 길이입니다.

## 3. 설치 확인

```bash
sub-memory-agent --help
sub-memory-mcp --help
python -m unittest discover -s tests
```

정상 설치되면 다음 두 엔트리포인트를 사용할 수 있습니다.

- `sub-memory-agent`
- `sub-memory-mcp`

## 4. 로컬 MCP 서버 실행

CLI 에이전트 연동은 `stdio` transport를 권장합니다.

```bash
sub-memory-mcp --base-dir <repo-root>
```

MCP 서버가 제공하는 tool:

- `recall_associated_memory`
- `store_memory`
- `reinforce_memory`
- `get_memory_status`

`sub-memory-agent`는 별도로 최근 세션 턴을 모두 길게 유지하지 않습니다.
대신 오래된 세션 내용을 짧은 working summary로 compact하고, 최근 몇 턴과 `memory.db` recall을 함께 사용합니다.
그래서 멀티턴이 길어져도 토큰 사용량을 비교적 낮게 유지할 수 있습니다.

## 5. CLI 연동

### Codex

예시는 `<repo-root>` 자리만 각자의 clone 경로로 바꿔 넣으면 됩니다.

```toml
[mcp_servers.sub_memory]
command = "<repo-root>/.venv/bin/sub-memory-mcp"
args = ["--base-dir", "<repo-root>"]
cwd = "<repo-root>"
enabled_tools = ["recall_associated_memory", "store_memory", "reinforce_memory", "get_memory_status"]
startup_timeout_sec = 90
tool_timeout_sec = 120
```

권장 초기 설정:

- 먼저 `get_memory_status`, `recall_associated_memory`만 열어 읽기 위주로 검증
- 검증 후 `store_memory`, `reinforce_memory`까지 확장

### Gemini CLI

`.gemini/settings.json`

```json
{
  "mcpServers": {
    "sub_memory": {
      "command": "<repo-root>/.venv/bin/sub-memory-mcp",
      "args": ["--base-dir", "<repo-root>"],
      "cwd": "<repo-root>",
      "timeout": 30000
    }
  }
}
```

### Claude Code

```bash
claude mcp add --transport stdio sub-memory -- \
  <repo-root>/.venv/bin/sub-memory-mcp \
  --base-dir <repo-root>
```

## 6. 한 번에 처리하는 Codex Skill 제공 방식

Codex용 배포 저장소를 별도로 제공합니다.

- GitHub: `https://github.com/TODOTODoTOdoTodotodo/sub-memory-bootstrap`
- 목적: 로컬 설치, MCP 엔트리포인트 확인, CLI 설정 스니펫 생성까지 한 번에 처리

### Skill 설치

배포 저장소를 clone한 뒤, 전역 Codex skill 디렉터리로 복사하거나 심볼릭 링크를 겁니다. 이 저장소에는 앱 본체와 skill이 같이 들어 있으므로 별도 본체 저장소를 추가로 받을 필요는 없습니다.

```bash
git clone https://github.com/TODOTODoTOdoTodotodo/sub-memory-bootstrap.git
cd sub-memory-bootstrap
mkdir -p ~/.codex/skills
cp -R sub-memory-bootstrap ~/.codex/skills/
```

또는:

```bash
git clone https://github.com/TODOTODoTOdoTodotodo/sub-memory-bootstrap.git
cd sub-memory-bootstrap
mkdir -p ~/.codex/skills
ln -s "$(pwd)/sub-memory-bootstrap" ~/.codex/skills/sub-memory-bootstrap
```

`CODEX_HOME`를 따로 쓰는 환경이라면 `~/.codex/skills` 대신 `$CODEX_HOME/skills` 아래에 두면 됩니다.

### Skill이 하는 일

- `scripts/bootstrap_local.sh`로 로컬 설치 자동화
- `scripts/configure_codex_project.py`로 project-local `.codex/config.toml` 생성
- `AGENTS.md`에 `sub_memory` 사용 규칙 managed block 반영
  - 답변 전 `recall_associated_memory`
  - 답변 후 `store_memory`
  - 필요 시 `reinforce_memory`
  - 긴 멀티턴에서는 compact summary로 active thread 축약
- `scripts/render_cli_snippets.py`로 현재 경로 기준 절대경로 설정 스니펫 생성
- `sub-memory-agent --help`, `sub-memory-mcp --help`, 테스트 명령으로 기본 검증 유도

### Skill 사용 예시

Codex에서 아래처럼 요청하면 됩니다.

```text
Use sub-memory-bootstrap to install this repo locally and generate Codex, Gemini CLI, and Claude Code MCP config snippets.
```

또는:

```text
Use sub-memory-bootstrap to validate the local setup and tell me the exact sub-memory-mcp path for this repo.
```

한글로는 아래처럼 요청해도 됩니다.

```text
sub-memory-bootstrap을 사용해서 이 저장소를 로컬에 설치하고 Codex, Gemini CLI, Claude Code용 MCP 설정 스니펫을 현재 머신 경로 기준으로 작성해줘.
```

```text
sub-memory-bootstrap으로 현재 설치 상태를 점검하고, 이 저장소에서 실제로 실행되는 sub-memory-mcp 경로를 알려줘.
```

Skill 실행이 끝나면 아래 두 파일이 준비됩니다.

- project-local Codex MCP 등록: `.codex/config.toml`
- 새 세션용 사용 규칙: `AGENTS.md`

따라서 `sub-memory-bootstrap`으로 온보딩한 뒤에는 저장소 루트에서 새 Codex 세션을 시작하는 것이 가장 안정적입니다.

## 7. 동일 설치를 맞추는 방법

다른 사람의 에이전트에서도 최대한 같은 설치 상태를 맞추려면 아래 기준을 공유합니다.

1. 같은 Git commit 또는 tag를 사용합니다.
2. 같은 Python 버전(`python3.11`)을 사용합니다.
3. bootstrap 스크립트를 기준 설치 경로로 사용합니다.
4. `.env`의 핵심 설정값을 맞춥니다.
5. 테스트 명령으로 설치 확인을 끝냅니다.

예:

```bash
git clone https://github.com/TODOTODoTOdoTodotodo/sub-memory-bootstrap.git
cd sub-memory-bootstrap
git checkout <commit-or-tag>
./sub-memory-bootstrap/scripts/bootstrap_local.sh .
python -m unittest discover -s tests
```

중요한 점은 “같은 로컬 경로”가 아니라 “같은 저장소 버전 + 같은 설정”입니다.

## 8. 다음 문서

- [사용 예제](./usage-examples.md)
- 상위 요약: [README.md](../README.md)
