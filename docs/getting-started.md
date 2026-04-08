# Getting Started

이 문서는 `sub-memory`를 로컬에 설치하고, `Codex`, `Gemini CLI`, `Claude Code`에 로컬 `stdio` MCP 서버로 연결하는 가장 짧은 시작 경로를 정리합니다.

범위는 로컬 설치와 CLI 연동까지입니다. 앱 연동(`ChatGPT 앱`, `Gemini 앱`, `Claude 앱`)은 현재 TODO로 남겨둡니다.

## 1. 준비 사항

- Python `3.10+`
- macOS 기준 권장 버전: `python3.11`
- 로컬에서 로드 가능한 `sqlite-vec`
- OpenAI API Key
  - `sub-memory-agent` 실행 시 필요
  - `sub-memory-mcp`만 사용할 때는 없어도 됨

## 2. 로컬 설치

프로젝트 루트에서 실행합니다.

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
  - 이 횟수만큼 substantive turn이 쌓이면 오래된 세션 내용을 compact 후보로 봅니다.
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
sub-memory-mcp --base-dir /absolute/path/to/sub-memory
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

`~/.codex/config.toml`

```toml
[mcp_servers.sub_memory]
command = "/absolute/path/to/sub-memory/.venv/bin/sub-memory-mcp"
args = ["--base-dir", "/absolute/path/to/sub-memory"]
cwd = "/absolute/path/to/sub-memory"
enabled_tools = ["recall_associated_memory", "store_memory", "reinforce_memory", "get_memory_status"]
startup_timeout_sec = 30
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
      "command": "/absolute/path/to/sub-memory/.venv/bin/sub-memory-mcp",
      "args": ["--base-dir", "/absolute/path/to/sub-memory"],
      "cwd": "/absolute/path/to/sub-memory",
      "timeout": 30000
    }
  }
}
```

### Claude Code

```bash
claude mcp add --transport stdio sub-memory -- \
  /absolute/path/to/sub-memory/.venv/bin/sub-memory-mcp \
  --base-dir /absolute/path/to/sub-memory
```

## 6. 한 번에 처리하는 Codex Skill 제공 방식

Codex용 배포 저장소를 별도로 제공합니다.

- GitHub: `https://github.com/TODOTODoTOdoTodotodo/sub-memory-bootstrap`
- 목적: 로컬 설치, MCP 엔트리포인트 확인, CLI 설정 스니펫 생성까지 한 번에 처리

### Skill 설치

배포 저장소를 clone한 뒤, 전역 Codex skill 디렉터리로 복사하거나 심볼릭 링크를 겁니다.

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

## 7. 다음 문서

- [사용 예제](./usage-examples.md)
- 상위 요약: [README.md](../README.md)
