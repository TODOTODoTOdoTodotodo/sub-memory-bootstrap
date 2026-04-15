from __future__ import annotations

import argparse
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlparse

from sub_memory.config import Settings
from sub_memory.service import MemoryService


BASE_STYLE = """
body {
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
  margin: 0;
  background: #f5f2ea;
  color: #222;
}
header {
  padding: 18px 24px;
  background: linear-gradient(135deg, #d3c2a1, #f2ead9);
  border-bottom: 1px solid #cfbf9f;
}
nav a {
  margin-right: 14px;
  color: #2a2418;
  text-decoration: none;
  font-weight: 600;
}
main {
  padding: 24px;
}
.grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 16px;
}
.card {
  background: white;
  border: 1px solid #d9cfbb;
  border-radius: 14px;
  padding: 16px;
  box-shadow: 0 10px 30px rgba(67, 52, 20, 0.05);
}
.memory-list {
  display: grid;
  gap: 12px;
}
.memory-item {
  background: white;
  border: 1px solid #d9cfbb;
  border-radius: 12px;
  padding: 14px;
}
.muted {
  color: #6b665a;
  font-size: 0.92rem;
}
pre {
  white-space: pre-wrap;
  background: #fffdf8;
  border: 1px solid #e0d4bd;
  padding: 12px;
  border-radius: 10px;
}
input, button {
  font: inherit;
  padding: 10px 12px;
  border-radius: 10px;
  border: 1px solid #cdbb98;
}
button {
  cursor: pointer;
  background: #7a5f36;
  color: white;
}
svg {
  width: 100%;
  min-height: 520px;
  background: white;
  border: 1px solid #d9cfbb;
  border-radius: 14px;
}
"""


def _html_page(title: str, body: str, script: str = "") -> bytes:
    return f"""<!doctype html>
<html lang="ko">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{title}</title>
  <style>{BASE_STYLE}</style>
</head>
<body>
  <header>
    <h1 style="margin:0 0 10px 0;">[ㄱ] 기억 시각화</h1>
    <nav>
      <a href="/ui">Dashboard</a>
      <a href="/ui/memories">Search</a>
    </nav>
  </header>
  <main>{body}</main>
  <script>{script}</script>
</body>
</html>""".encode("utf-8")


def build_handler(service: MemoryService) -> type[BaseHTTPRequestHandler]:
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:  # noqa: N802
            parsed = urlparse(self.path)
            path = parsed.path
            query = parse_qs(parsed.query)

            if path == "/":
                self._redirect("/ui")
                return

            if path == "/api/status":
                self._send_json(service.get_dashboard_stats())
                return

            if path == "/api/memories":
                limit = _read_int(query.get("limit", ["50"])[0], 50)
                offset = _read_int(query.get("offset", ["0"])[0], 0)
                search_query = query.get("q", [""])[0] or None
                self._send_json(
                    {
                        "items": service.list_memories(
                            limit=limit,
                            offset=offset,
                            query=search_query,
                        )
                    }
                )
                return

            if path.startswith("/api/memories/"):
                node_id = path.rsplit("/", 1)[-1]
                memory = service.get_memory(node_id)
                if memory is None:
                    self.send_error(HTTPStatus.NOT_FOUND, "Memory not found")
                    return
                self._send_json(memory)
                return

            if path.startswith("/api/graph/"):
                node_id = path.rsplit("/", 1)[-1]
                depth = _read_int(query.get("depth", ["2"])[0], 2)
                limit = _read_int(query.get("limit", ["20"])[0], 20)
                self._send_json(
                    service.get_graph_subtree(node_id, depth=depth, limit=limit)
                )
                return

            if path == "/ui":
                self._send_html(_dashboard_page())
                return

            if path == "/ui/memories":
                self._send_html(_memories_page())
                return

            if path.startswith("/ui/memories/"):
                node_id = path.rsplit("/", 1)[-1]
                self._send_html(_memory_detail_page(node_id))
                return

            if path.startswith("/ui/graph/"):
                node_id = path.rsplit("/", 1)[-1]
                self._send_html(_graph_page(node_id))
                return

            self.send_error(HTTPStatus.NOT_FOUND, "Not found")

        def log_message(self, format: str, *args: Any) -> None:  # noqa: A003
            return

        def _send_html(self, content: bytes) -> None:
            self.send_response(HTTPStatus.OK)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(content)))
            self.end_headers()
            self.wfile.write(content)

        def _send_json(self, payload: dict[str, Any]) -> None:
            raw = json.dumps(payload, ensure_ascii=False).encode("utf-8")
            self.send_response(HTTPStatus.OK)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(raw)))
            self.end_headers()
            self.wfile.write(raw)

        def _redirect(self, location: str) -> None:
            self.send_response(HTTPStatus.FOUND)
            self.send_header("Location", location)
            self.end_headers()

    return Handler


def _dashboard_page() -> bytes:
    body = """
    <div class="grid" id="stats"></div>
    <section class="card" style="margin-top:16px;">
      <h2>최근 기억</h2>
      <div class="memory-list" id="recent-memories"></div>
    </section>
    """
    script = """
    fetch('/api/status').then(r => r.json()).then(data => {
      const stats = [
        ['전체 기억 수', data.node_count],
        ['전체 연결 수', data.edge_count],
        ['최근 24시간 저장 수', data.recent_24h_count],
        ['최근 7일 저장 수', data.recent_7d_count],
        ['평균 연결 수', data.average_connections],
        ['마지막 저장 시각', data.last_timestamp || '없음'],
      ];
      document.getElementById('stats').innerHTML = stats.map(([label, value]) =>
        `<div class="card"><div class="muted">${label}</div><div style="font-size:1.5rem;font-weight:700;margin-top:8px;">${value}</div></div>`
      ).join('');
      document.getElementById('recent-memories').innerHTML = (data.recent_memories || []).map(item =>
        `<div class="memory-item">
          <div class="muted">${item.timestamp} · 연결 ${item.connection_count}</div>
          <div style="margin:8px 0;">${escapeHtml(item.text.slice(0, 180))}</div>
          <a href="/ui/memories/${item.node_id}">상세 보기</a>
          <span style="margin:0 6px;">·</span>
          <a href="/ui/graph/${item.node_id}">생각나무</a>
        </div>`
      ).join('');
    });
    function escapeHtml(text) {
      return text
        .replaceAll('&', '&amp;')
        .replaceAll('<', '&lt;')
        .replaceAll('>', '&gt;');
    }
    """
    return _html_page("Dashboard", body, script)


def _memories_page() -> bytes:
    body = """
    <section class="card">
      <h2>기억 검색</h2>
      <form id="search-form" style="display:flex;gap:8px;flex-wrap:wrap;">
        <input id="query" name="q" placeholder="키워드로 검색" style="min-width:320px;flex:1;">
        <button type="submit">검색</button>
      </form>
    </section>
    <section class="memory-list" id="results" style="margin-top:16px;"></section>
    """
    script = """
    async function load(q='') {
      const url = '/api/memories' + (q ? `?q=${encodeURIComponent(q)}` : '');
      const data = await fetch(url).then(r => r.json());
      document.getElementById('results').innerHTML = (data.items || []).map(item =>
        `<div class="memory-item">
          <div class="muted">${item.timestamp} · 연결 ${item.connection_count}</div>
          <div style="margin:8px 0;">${escapeHtml(item.text.slice(0, 240))}</div>
          <a href="/ui/memories/${item.node_id}">상세 보기</a>
          <span style="margin:0 6px;">·</span>
          <a href="/ui/graph/${item.node_id}">생각나무</a>
        </div>`
      ).join('');
    }
    document.getElementById('search-form').addEventListener('submit', (event) => {
      event.preventDefault();
      load(document.getElementById('query').value.trim());
    });
    function escapeHtml(text) {
      return text
        .replaceAll('&', '&amp;')
        .replaceAll('<', '&lt;')
        .replaceAll('>', '&gt;');
    }
    load('');
    """
    return _html_page("Memory Search", body, script)


def _memory_detail_page(node_id: str) -> bytes:
    body = f"""
    <section class="card">
      <h2>기억 상세</h2>
      <div id="detail">불러오는 중...</div>
    </section>
    <section class="card" style="margin-top:16px;">
      <h2>직접 연결된 기억</h2>
      <div class="memory-list" id="connected"></div>
    </section>
    <p style="margin-top:16px;"><a href="/ui/graph/{node_id}">생각나무 보기</a></p>
    """
    script = f"""
    fetch('/api/memories/{node_id}').then(async (response) => {{
      if (!response.ok) {{
        document.getElementById('detail').innerText = '기억을 찾을 수 없습니다.';
        return;
      }}
      const data = await response.json();
      document.getElementById('detail').innerHTML = `
        <div class="muted">${{data.timestamp}}</div>
        <pre>${{escapeHtml(data.text)}}</pre>
      `;
      document.getElementById('connected').innerHTML = (data.connected_memories || []).map(item =>
        `<div class="memory-item">
          <div class="muted">${{item.timestamp}} · weight=${{item.weight}}</div>
          <div style="margin:8px 0;">${{escapeHtml(item.text.slice(0, 220))}}</div>
          <a href="/ui/memories/${{item.node_id}}">상세 보기</a>
          <span style="margin:0 6px;">·</span>
          <a href="/ui/graph/${{item.node_id}}">생각나무</a>
        </div>`
      ).join('');
    }});
    function escapeHtml(text) {{
      return text
        .replaceAll('&', '&amp;')
        .replaceAll('<', '&lt;')
        .replaceAll('>', '&gt;');
    }}
    """
    return _html_page("Memory Detail", body, script)


def _graph_page(node_id: str) -> bytes:
    body = """
    <section class="card">
      <h2>생각나무</h2>
      <p class="muted">중앙 기억에서 연결된 주변 기억을 2단계까지 시각화합니다.</p>
      <svg id="graph" viewBox="0 0 1000 700"></svg>
    </section>
    """
    script = f"""
    fetch('/api/graph/{node_id}?depth=2&limit=20').then(r => r.json()).then(data => {{
      const svg = document.getElementById('graph');
      const nodes = data.nodes || [];
      const edges = data.edges || [];
      if (!nodes.length) {{
        svg.outerHTML = '<div class="card">그래프를 표시할 기억이 없습니다.</div>';
        return;
      }}
      const center = nodes.find(n => n.node_id === data.center_node_id) || nodes[0];
      const width = 1000;
      const height = 700;
      const cx = width / 2;
      const cy = height / 2;
      const positions = new Map();
      positions.set(center.node_id, {{x: cx, y: cy}});
      const others = nodes.filter(n => n.node_id !== center.node_id);
      others.forEach((node, index) => {{
        const ring = node.depth === 1 ? 180 : 300;
        const angle = (Math.PI * 2 * index) / Math.max(1, others.length);
        positions.set(node.node_id, {{
          x: cx + Math.cos(angle) * ring,
          y: cy + Math.sin(angle) * ring,
        }});
      }});
      const lineMarkup = edges.map(edge => {{
        const a = positions.get(edge.source_id);
        const b = positions.get(edge.target_id);
        if (!a || !b) return '';
        const stroke = Math.min(8, 1 + edge.weight * 1.5);
        return `<line x1="${{a.x}}" y1="${{a.y}}" x2="${{b.x}}" y2="${{b.y}}" stroke="#9d7f4c" stroke-width="${{stroke}}" opacity="0.6" />`;
      }}).join('');
      const nodeMarkup = nodes.map(node => {{
        const pos = positions.get(node.node_id);
        const radius = node.node_id === center.node_id ? 38 : (node.depth === 1 ? 28 : 22);
        const fill = node.node_id === center.node_id ? '#7a5f36' : (node.depth === 1 ? '#c8aa73' : '#ebe0c8');
        const preview = escapeHtml(node.text.slice(0, 64));
        return `
          <a href="/ui/memories/${{node.node_id}}">
            <circle cx="${{pos.x}}" cy="${{pos.y}}" r="${{radius}}" fill="${{fill}}" stroke="#5a4727" stroke-width="1.5"></circle>
            <text x="${{pos.x}}" y="${{pos.y + 4}}" text-anchor="middle" font-size="12" fill="${{node.node_id === center.node_id ? 'white' : '#2b2419'}}">${{node.depth}}</text>
            <title>${{preview}}</title>
          </a>
        `;
      }}).join('');
      svg.innerHTML = lineMarkup + nodeMarkup;
    }});
    function escapeHtml(text) {{
      return text
        .replaceAll('&', '&amp;')
        .replaceAll('<', '&lt;')
        .replaceAll('>', '&gt;');
    }}
    """
    return _html_page("Association Graph", body, script)


def _read_int(raw: str, default: int) -> int:
    try:
        return int(raw)
    except ValueError:
        return default


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="sub-memory read-only web UI")
    parser.add_argument(
        "--base-dir",
        default=str(Path.cwd()),
        help="Project directory containing .env and memory.db.",
    )
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    settings = Settings.from_env(Path(args.base_dir))
    service = MemoryService.from_settings(settings)
    handler = build_handler(service)
    server = ThreadingHTTPServer((args.host, args.port), handler)
    print(f"sub-memory web UI listening on http://{args.host}:{args.port}/ui")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        return 0
    finally:
        server.server_close()
        service.close()


if __name__ == "__main__":
    raise SystemExit(main())
