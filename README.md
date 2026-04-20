# [ㄱ] 로컬 기억 보조도구

`[ㄱ]`은 로컬 SQLite 벡터 저장소와 그래프 연상을 결합한 기억 보조도구입니다.  
대화와 작업 내용을 `memory.db`에 저장해 두고, 나중에 비슷한 질문이 들어오면 관련 기억을 다시 불러와 답변에 반영합니다.

영문 표기는 `Giyeok`을 권장합니다.

## 빠른 시작

가장 짧은 확인 경로는 아래입니다.

```bash
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install -e .
cp .env.example .env
mkdir -p ~/.codex/sub-memory
cp .env ~/.codex/sub-memory/.env
python3 skills/sub-memory-bootstrap/scripts/configure_codex_project.py --project-dir "$(pwd)"
skills/sub-memory-bootstrap/scripts/manage_mcp_daemon.sh start "$(pwd)"
skills/sub-memory-bootstrap/scripts/start_web_ui.sh "$(pwd)"
```

빠른 시작에서 확인해야 할 필수 항목은 아래 셋입니다.

- 공용 MCP 서버 시작: `skills/sub-memory-bootstrap/scripts/manage_mcp_daemon.sh start "$(pwd)"`
- Codex MCP 연결: `python3 skills/sub-memory-bootstrap/scripts/configure_codex_project.py --project-dir "$(pwd)"` 후 새 Codex 세션 시작
- Web UI 실행: `skills/sub-memory-bootstrap/scripts/start_web_ui.sh "$(pwd)"`

브라우저와 MCP endpoint는 아래를 사용합니다.

```text
MCP: http://127.0.0.1:8766/mcp
http://127.0.0.1:8765/ui
```

`sub-memory-bootstrap` 스킬을 쓰는 경우에는 아래처럼 요청하면 됩니다.

```text
sub-memory-bootstrap으로 현재 저장소를 설치하고 웹 UI를 실행한 뒤 브라우저에서 열 주소를 알려줘.
```

## 문서

- `docs/getting-started.md`
- `docs/usage-examples.md`
- `docs/giyeok-manual.md`
- `SKILL.md`
- `skills/sub-memory-bootstrap/`

## Codex Skill 설치

이 저장소는 루트에도 `SKILL.md`가 있어서 저장소 루트를 그대로 Codex skill로 설치할 수 있습니다.

`skill-installer`를 쓰는 경우에는 아래 둘 중 하나를 사용하면 됩니다.

```text
$skill-installer https://github.com/TODOTODoTOdoTodotodo/sub-memory-bootstrap/tree/main/skills/sub-memory-bootstrap
```

```text
$skill-installer https://github.com/TODOTODoTOdoTodotodo/sub-memory-bootstrap.git --path .
```

`--path .`로 설치하면 전체 레포가 skill 디렉터리에 들어갑니다.
`--path skills/sub-memory-bootstrap`로 설치하면 첫 bootstrap 실행 시
`$CODEX_HOME/repos/sub-memory-bootstrap`
또는 `~/.codex/repos/sub-memory-bootstrap` 아래에 전체 레포 checkout을 자동으로 받아 설치를 이어갑니다.

수동으로 설치하는 경우에는 저장소 루트를 `~/.codex/skills/sub-memory-bootstrap`에 복사하거나 링크하면 됩니다.

```bash
git clone https://github.com/TODOTODoTOdoTodotodo/sub-memory-bootstrap.git
mkdir -p ~/.codex/skills
cp -R sub-memory-bootstrap ~/.codex/skills/sub-memory-bootstrap
```

또는:

```bash
git clone https://github.com/TODOTODoTOdoTodotodo/sub-memory-bootstrap.git
mkdir -p ~/.codex/skills
ln -s "$(pwd)/sub-memory-bootstrap" ~/.codex/skills/sub-memory-bootstrap
```

## 구성

- `local_agent.py`: 실행 진입점
- `mcp_server.py`: MCP 서버 실행 진입점
- `sub_memory/agent.py`: OpenAI `Responses API` 기반 대화 루프
- `sub_memory/mcp_server.py`: 설치형 MCP 서버
- `sub_memory/service.py`: 공용 메모리 서비스 계층
- `sub_memory/store.py`: SQLite + `sqlite-vec` + `networkx` 기반 저장/회수/강화
- `sub_memory/tools.py`: tool schema와 디스패처
- `tests/`: 단위 테스트

## 요구 사항

- Python `3.10+`
- 로컬에서 로드 가능한 `sqlite-vec`
- `sub-memory-agent`를 쓸 경우 OpenAI API Key

macOS에서는 Python `3.11` 가상환경이 가장 안전합니다.

## 설치

```bash
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
pip install -e .
```

`.env`에서 필요한 값을 채웁니다.

```dotenv
OPENAI_API_KEY=sk-your-key
OPENAI_MODEL=gpt-5-mini
EMBEDDING_MODEL_NAME=all-MiniLM-L6-v2
SQLITE_VEC_PATH=
RECALL_DEPTH=2
RECALL_LIMIT=6
COMPACT_AFTER_TURNS=4
COMPACT_KEEP_RECENT_TURNS=2
COMPACT_SUMMARY_CHAR_LIMIT=2400
MEMORY_DB_PATH=memory.db
METRICS_LOG_PATH=.sub-memory/metrics.jsonl
METRICS_RETENTION_DAYS=30
```

설정 의미:

- `OPENAI_API_KEY`
  - `sub-memory-agent` 실행 시 필요
- `RECALL_DEPTH`, `RECALL_LIMIT`
  - 한 번에 가져올 연관 기억 범위 조절
- `COMPACT_AFTER_TURNS`
  - 몇 턴 후 오래된 세션 내용을 compact 대상으로 볼지 결정
- `COMPACT_KEEP_RECENT_TURNS`
  - compact 후에도 최근 원문으로 남길 턴 수
- `COMPACT_SUMMARY_CHAR_LIMIT`
  - compact summary 최대 길이
- `METRICS_LOG_PATH`
  - memory contribution 및 토큰 인사이트 로그 경로
- `METRICS_RETENTION_DAYS`
  - 메트릭 로그 보관 기간

## 실행

대화형 실행:

```bash
sub-memory-agent
```

또는:

```bash
python local_agent.py
```

단일 프롬프트 실행:

```bash
sub-memory-agent --once "지난번 출장 관련 TODO 기억나?"
```

종료 명령은 `exit`, `quit`입니다.

## 동작 방식

1. 사용자 입력이 들어오면 먼저 `recall_associated_memory`를 실행합니다.
2. 회수된 기억을 현재 턴의 컨텍스트에 주입한 뒤 모델 응답을 생성합니다.
3. 답변이 끝나면 현재 대화를 `store_memory`로 저장합니다.
4. 실제로 도움이 된 과거 기억이 있다면 `reinforce_memory`로 연결 강도를 높입니다.
5. 멀티턴이 길어지면 오래된 세션 내용은 compact summary로 줄이고, 최근 몇 턴과 `memory.db` recall만 유지해 토큰 사용을 낮춥니다.

즉, `[ㄱ]`은 전체 원문 대화를 무한히 계속 싣는 대신:

- 최근 대화는 짧게 유지하고
- 오래된 세션은 compact하고
- 장기 맥락은 필요할 때 다시 recall하는 방식으로 동작합니다

## MCP 서버

권장 방식은 `~/.codex/sub-memory`를 기준으로 공용 MCP 데몬을 한 번 띄우고,
각 세션은 동일한 `streamable-http` endpoint를 바라보게 하는 것입니다.

```bash
skills/sub-memory-bootstrap/scripts/manage_mcp_daemon.sh start "$(pwd)"
```

상태 확인과 종료:

```bash
skills/sub-memory-bootstrap/scripts/manage_mcp_daemon.sh status "$(pwd)"
skills/sub-memory-bootstrap/scripts/manage_mcp_daemon.sh stop "$(pwd)"
```

기본 endpoint:

```text
http://127.0.0.1:8766/mcp
```

노출되는 MCP tools:

- `recall_associated_memory`
- `store_memory`
- `reinforce_memory`
- `get_memory_status`

`sub-memory-bootstrap` 스킬을 사용하면 아래까지 한 번에 준비할 수 있습니다.

- project-local `.codex/config.toml`
- `AGENTS.md`의 `sub_memory` 사용 규칙
- CLI 연동용 설정 스니펫

## 웹 시각화 MVP

기본 뼈대 화면은 아래 명령으로 실행합니다.

```bash
mkdir -p ~/.codex/sub-memory
cp .env ~/.codex/sub-memory/.env
sub-memory-web --base-dir ~/.codex/sub-memory
```

기본 주소:

```text
http://127.0.0.1:8765/ui
```

현재 제공 화면:

- Dashboard
- Memory Search
- Memory Detail
- Association Graph

`Memory Detail` 화면에는 `Neuralizer` 버튼이 있습니다.
이 기능은 현재 기억 노드만 삭제하고, 연결된 다른 기억은 남긴 채 해당 노드와 이어진 엣지만 제거합니다.

## Codex 예시

```toml
[mcp_servers.sub_memory]
url = "http://127.0.0.1:8766/mcp"
enabled_tools = ["recall_associated_memory", "store_memory", "reinforce_memory", "get_memory_status"]
startup_timeout_sec = 30
tool_timeout_sec = 120
```

## Gemini CLI 예시

```json
{
  "mcpServers": {
    "sub_memory": {
      "url": "http://127.0.0.1:8766/mcp",
      "timeout": 30000
    }
  }
}
```

## Claude Code 예시

```bash
claude mcp add --transport http sub-memory http://127.0.0.1:8766/mcp
```

## 테스트

```bash
python -m unittest discover -s tests
```

## 메트릭 로그

`[ㄱ]`은 기본적으로 아래 경로에 JSONL 메트릭 로그를 남깁니다.

```text
.sub-memory/metrics.jsonl
```

여기에는 두 종류가 쌓입니다.

- `agent_turn`
  - `local_agent` 기준 입력/출력 토큰, recall 크기, session context 크기
- `mcp_*`
  - `sub-memory-mcp` 기준 recall/store/reinforce/status 호출량과 memory contribution 크기

개인용 기본 보관 기간은 30일입니다.

요약 예시:

```bash
python scripts/summarize_metrics.py --path .sub-memory/metrics.jsonl
```

## 참고

- 일반 사용자용 설명: `docs/giyeok-manual.md`
- 설치와 첫 실행: `docs/getting-started.md`
- 실전 프롬프트 예시: `docs/usage-examples.md`
- Codex 온보딩 스킬: `skills/sub-memory-bootstrap/`
