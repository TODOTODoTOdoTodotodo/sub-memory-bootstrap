# [ㄱ] 로컬 기억 보조도구

`[ㄱ]`은 로컬 SQLite 벡터 저장소와 그래프 연상을 결합한 기억 보조도구입니다.  
대화와 작업 내용을 `memory.db`에 저장해 두고, 나중에 비슷한 질문이 들어오면 관련 기억을 다시 불러와 답변에 반영합니다.

영문 표기는 `Giyeok`을 권장합니다.

이 저장소에는 두 가지가 함께 들어 있습니다.

- `sub_memory` 본체 코드
- Codex 온보딩용 `sub-memory-bootstrap` skill

즉, 이 저장소 하나만 clone하면 로컬 설치와 Codex MCP 온보딩까지 모두 처리할 수 있습니다.

## 문서

- `docs/getting-started.md`
- `docs/usage-examples.md`
- `docs/giyeok-manual.md`
- `sub-memory-bootstrap/`

## 구성

- `local_agent.py`: 실행 진입점
- `mcp_server.py`: MCP 서버 실행 진입점
- `sub_memory/agent.py`: OpenAI `Responses API` 기반 대화 루프
- `sub_memory/mcp_server.py`: 설치형 MCP 서버
- `sub_memory/service.py`: 공용 메모리 서비스 계층
- `sub_memory/store.py`: SQLite + `sqlite-vec` + `networkx` 기반 저장/회수/강화
- `sub_memory/tools.py`: tool schema와 디스패처
- `tests/`: 단위 테스트
- `sub-memory-bootstrap/`: Codex skill과 bootstrap 스크립트

## 요구 사항

- Python `3.10+`
- 로컬에서 로드 가능한 `sqlite-vec`
- `sub-memory-agent`를 쓸 경우 OpenAI API Key

macOS에서는 Python `3.11` 가상환경이 가장 안전합니다.

## 설치

프로젝트 루트에서:

```bash
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
pip install -e .
```

또는 Codex skill bootstrap으로 한 번에:

```bash
./sub-memory-bootstrap/scripts/bootstrap_local.sh .
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

로컬 CLI 에이전트 연동은 `stdio` transport를 권장합니다.

```bash
sub-memory-mcp --base-dir /absolute/path/to/repo
```

노출되는 MCP tools:

- `recall_associated_memory`
- `store_memory`
- `reinforce_memory`
- `get_memory_status`

`sub-memory-bootstrap` 스킬 또는 bootstrap 스크립트를 사용하면 아래까지 한 번에 준비할 수 있습니다.

- project-local `.codex/config.toml`
- `AGENTS.md`의 `sub_memory` 사용 규칙
- CLI 연동용 설정 스니펫

## Codex 예시

```toml
[mcp_servers.sub_memory]
command = "/absolute/path/to/repo/.venv/bin/sub-memory-mcp"
args = ["--base-dir", "/absolute/path/to/repo"]
cwd = "/absolute/path/to/repo"
enabled_tools = ["recall_associated_memory", "store_memory", "reinforce_memory", "get_memory_status"]
startup_timeout_sec = 90
tool_timeout_sec = 120
```

## Gemini CLI 예시

```json
{
  "mcpServers": {
    "sub_memory": {
      "command": "/absolute/path/to/repo/.venv/bin/sub-memory-mcp",
      "args": ["--base-dir", "/absolute/path/to/repo"],
      "cwd": "/absolute/path/to/repo",
      "timeout": 30000
    }
  }
}
```

## Claude Code 예시

```bash
claude mcp add --transport stdio sub-memory -- \
  /absolute/path/to/repo/.venv/bin/sub-memory-mcp \
  --base-dir /absolute/path/to/repo
```

## Codex skill

이 저장소에는 Codex용 온보딩 skill도 포함되어 있습니다.

- skill 경로: `sub-memory-bootstrap/`
- 역할:
  - 로컬 설치 점검
  - project-local MCP 등록
  - `AGENTS.md` 규칙 반영
  - 설정 스니펫 출력

전역 설치 예시:

```bash
mkdir -p ~/.codex/skills
ln -s "$(pwd)/sub-memory-bootstrap" ~/.codex/skills/sub-memory-bootstrap
```

## 테스트

```bash
python -m unittest discover -s tests
```

## 참고

- 일반 사용자용 설명: `docs/giyeok-manual.md`
- 설치와 첫 실행: `docs/getting-started.md`
- 실전 프롬프트 예시: `docs/usage-examples.md`
- Codex 온보딩 스킬: `sub-memory-bootstrap/`
