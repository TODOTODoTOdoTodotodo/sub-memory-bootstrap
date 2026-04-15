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
.graph-shell {
  display: grid;
  grid-template-columns: minmax(0, 1.9fr) minmax(280px, 0.9fr);
  gap: 16px;
  align-items: start;
}
.graph-stage {
  position: relative;
}
.graph-toolbar {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
  align-items: center;
  margin-bottom: 12px;
}
.branch-controls {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
  margin: 6px 0 12px 0;
}
.branch-toggle {
  background: #f4ead6;
  color: #4c3d24;
  border-color: #d6c39f;
  padding: 7px 11px;
}
.branch-toggle[data-collapsed="true"] {
  background: #ead7b4;
  color: #3e301a;
}
.graph-toolbar label {
  display: flex;
  gap: 8px;
  align-items: center;
  color: #4f4738;
  font-size: 0.92rem;
}
.graph-sidebar {
  display: grid;
  gap: 12px;
}
.graph-detail {
  background: linear-gradient(180deg, #fffdf8, #f8f2e6);
}
.graph-kpis {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 10px;
}
.graph-kpi {
  border: 1px solid #e4d7bd;
  border-radius: 12px;
  padding: 12px;
  background: rgba(255, 255, 255, 0.72);
}
.graph-kpi strong {
  display: block;
  font-size: 1.2rem;
  margin-top: 6px;
}
.graph-legend {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
  margin-top: 10px;
}
.chip {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 6px 10px;
  border-radius: 999px;
  background: #f1e7d4;
  color: #514631;
  font-size: 0.85rem;
}
.chip::before {
  content: "";
  width: 8px;
  height: 8px;
  border-radius: 999px;
  background: currentColor;
}
.graph-empty {
  display: grid;
  place-items: center;
  min-height: 520px;
  color: #6b665a;
}
@media (max-width: 960px) {
  .graph-shell {
    grid-template-columns: 1fr;
  }
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

        def do_POST(self) -> None:  # noqa: N802
            parsed = urlparse(self.path)
            path = parsed.path

            if path.startswith("/api/neuralize/"):
                node_id = path.rsplit("/", 1)[-1]
                result = service.delete_memory(node_id)
                status = (
                    HTTPStatus.OK
                    if result.get("status") == "deleted"
                    else HTTPStatus.NOT_FOUND
                )
                self._send_json(result, status=status)
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

        def _send_json(
            self,
            payload: dict[str, Any],
            *,
            status: HTTPStatus = HTTPStatus.OK,
        ) -> None:
            raw = json.dumps(payload, ensure_ascii=False).encode("utf-8")
            self.send_response(status)
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
      <div style="display:flex;justify-content:space-between;gap:12px;align-items:center;flex-wrap:wrap;">
        <h2 style="margin:0;">기억 상세</h2>
        <button id="neuralizer-button" style="background:#5b1f25;border-color:#5b1f25;">Neuralizer</button>
      </div>
      <p class="muted">현재 기억 노드만 삭제합니다. 연결된 다른 기억은 남고, 이 노드와 이어진 엣지만 제거됩니다.</p>
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
    document.getElementById('neuralizer-button').addEventListener('click', async () => {{
      const ok = confirm('Neuralizer를 실행하면 현재 기억 노드만 삭제됩니다. 연결된 다른 기억은 남습니다. 계속할까요?');
      if (!ok) return;
      const response = await fetch('/api/neuralize/{node_id}', {{ method: 'POST' }});
      const data = await response.json();
      if (!response.ok) {{
        alert('Neuralizer 실패: ' + (data.status || 'unknown'));
        return;
      }}
      alert(`Neuralizer 완료. 제거된 연결 수: ${{data.deleted_connection_count}}`);
      window.location.href = '/ui/memories';
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
    <section class="graph-shell">
      <div class="card graph-stage">
        <div style="display:flex;justify-content:space-between;gap:12px;align-items:flex-start;flex-wrap:wrap;">
          <div>
            <h2 style="margin:0;">생각나무</h2>
            <p class="muted" style="margin:8px 0 0 0;">중앙 기억을 중심으로 가지를 정리해 연상 흐름이 보이도록 배치합니다.</p>
          </div>
          <div class="graph-toolbar">
            <label>Depth
              <select id="depth">
                <option value="2" selected>2</option>
                <option value="3">3</option>
              </select>
            </label>
            <label>Limit
              <select id="limit">
                <option value="20" selected>20</option>
                <option value="30">30</option>
                <option value="40">40</option>
              </select>
            </label>
            <button id="reload-graph" type="button">다시 그리기</button>
          </div>
          <div id="branch-controls" class="branch-controls"></div>
        </div>
        <svg id="graph" viewBox="0 0 1240 760"></svg>
      </div>
      <aside class="graph-sidebar">
        <section class="card graph-detail">
          <h3 style="margin-top:0;">선택 기억</h3>
          <div id="graph-detail">노드를 선택하면 여기에서 기억 내용을 더 자세히 볼 수 있습니다.</div>
        </section>
        <section class="card">
          <h3 style="margin-top:0;">구성 요약</h3>
          <div class="graph-kpis">
            <div class="graph-kpi"><div class="muted">노드 수</div><strong id="kpi-nodes">0</strong></div>
            <div class="graph-kpi"><div class="muted">연결 수</div><strong id="kpi-edges">0</strong></div>
            <div class="graph-kpi"><div class="muted">주요 가지</div><strong id="kpi-branches">0</strong></div>
            <div class="graph-kpi"><div class="muted">최대 깊이</div><strong id="kpi-depth">0</strong></div>
          </div>
          <div class="graph-legend">
            <span class="chip" style="color:#6e5431;">중심 기억</span>
            <span class="chip" style="color:#9d7f4c;">직접 연결</span>
            <span class="chip" style="color:#bca57b;">확장 기억</span>
          </div>
        </section>
      </aside>
    </section>
    """
    script = f"""
    const svg = document.getElementById('graph');
    const detail = document.getElementById('graph-detail');
    const depthInput = document.getElementById('depth');
    const limitInput = document.getElementById('limit');
    const reloadButton = document.getElementById('reload-graph');
    const branchControls = document.getElementById('branch-controls');
    let collapsedRoots = new Set();
    let selectedNodeId = null;

    function truncate(text, max = 72) {{
      const collapsed = (text || '').replaceAll(/\\s+/g, ' ').trim();
      if (collapsed.length <= max) return collapsed;
      return collapsed.slice(0, max - 1) + '…';
    }}

    function summarize(text) {{
      const preview = truncate(text, 180);
      return preview || '기억 내용이 비어 있습니다.';
    }}

    function updateDetail(node, branchSize = 0) {{
      if (!node) {{
        detail.innerHTML = '노드를 선택하면 여기에서 기억 내용을 더 자세히 볼 수 있습니다.';
        return;
      }}
      detail.innerHTML = `
        <div class="muted">depth ${{node.depth}} · branch ${{branchSize}} · ${{escapeHtml(node.timestamp || '시간 정보 없음')}}</div>
        <div style="font-size:1.05rem;font-weight:700;margin:10px 0 8px 0;">${{escapeHtml(truncate(node.text, 84))}}</div>
        <pre style="margin:0 0 12px 0;">${{escapeHtml(node.text || '')}}</pre>
        <a href="/ui/memories/${{node.node_id}}">상세 화면으로 이동</a>
      `;
    }}

    function computeLayout(nodes, centerId) {{
      const width = 1240;
      const height = 760;
      const centerX = width / 2;
      const centerY = height / 2;
      const columnGap = 230;
      const rowGap = 88;
      const positions = new Map();
      const byId = new Map(nodes.map(node => [node.node_id, node]));
      const childrenByParent = new Map();

      nodes.forEach((node) => {{
        const parentId = node.parent_id;
        if (!childrenByParent.has(parentId)) {{
          childrenByParent.set(parentId, []);
        }}
        childrenByParent.get(parentId).push(node);
      }});

      for (const children of childrenByParent.values()) {{
        children.sort((left, right) => {{
          if (left.depth !== right.depth) return left.depth - right.depth;
          return (right.text || '').length - (left.text || '').length;
        }});
      }}

      const rootChildren = (childrenByParent.get(centerId) || []).slice();
      rootChildren.sort((left, right) => (right.text || '').length - (left.text || '').length);
      const leftRoots = [];
      const rightRoots = [];
      rootChildren.forEach((node, index) => {{
        (index % 2 === 0 ? rightRoots : leftRoots).push(node);
      }});

      function countLeaves(nodeId) {{
        const children = childrenByParent.get(nodeId) || [];
        if (!children.length) return 1;
        return children.reduce((sum, child) => sum + countLeaves(child.node_id), 0);
      }}

      function assignBranch(branchNodes, side, startY) {{
        let cursorY = startY;
        const branchSizes = new Map();

        function place(node, anchorX, rootId) {{
          const children = childrenByParent.get(node.node_id) || [];
          const leafCount = countLeaves(node.node_id);
          const branchHeight = leafCount * rowGap;
          const nodeY = cursorY + branchHeight / 2;
          const nodeX = anchorX + (node.depth - 1) * columnGap * side;
          positions.set(node.node_id, {{ x: nodeX, y: nodeY }});
          branchSizes.set(node.node_id, leafCount);
          node.branch_root_id = rootId;

          if (!children.length) {{
            cursorY += rowGap;
            return;
          }}

          const start = cursorY;
          children.forEach((child) => place(child, anchorX, rootId));
          const end = cursorY - rowGap;
          positions.set(node.node_id, {{ x: nodeX, y: (start + end) / 2 }});
        }}

        branchNodes.forEach((branchRoot) => {{
          place(branchRoot, centerX + side * 190, branchRoot.node_id);
          cursorY += rowGap * 0.35;
        }});

        return branchSizes;
      }}

      positions.set(centerId, {{ x: centerX, y: centerY }});
      const leftLeafCount = leftRoots.reduce((sum, node) => sum + countLeaves(node.node_id), 0);
      const rightLeafCount = rightRoots.reduce((sum, node) => sum + countLeaves(node.node_id), 0);
      const leftStart = centerY - Math.max(0, leftLeafCount - 1) * rowGap / 2;
      const rightStart = centerY - Math.max(0, rightLeafCount - 1) * rowGap / 2;
      const branchSizes = new Map([[centerId, nodes.length - 1]]);

      for (const [nodeId, leafCount] of assignBranch(leftRoots, -1, leftStart)) {{
        branchSizes.set(nodeId, leafCount);
      }}
      for (const [nodeId, leafCount] of assignBranch(rightRoots, 1, rightStart)) {{
        branchSizes.set(nodeId, leafCount);
      }}

      positions.set(centerId, {{ x: centerX, y: centerY }});
      const centerNode = byId.get(centerId);
      if (centerNode) {{
        centerNode.branch_root_id = centerId;
      }}
      return {{ positions, byId, branchSizes, rootCount: rootChildren.length, rootChildren }};
    }}

    function isAncestor(possibleAncestorId, nodeId, byId) {{
      let current = byId.get(nodeId);
      while (current && current.parent_id) {{
        if (current.parent_id === possibleAncestorId) return true;
        current = byId.get(current.parent_id);
      }}
      return false;
    }}

    function visibleNodes(nodes, centerId) {{
      return nodes.filter((node) => {{
        if (node.node_id === centerId) return true;
        const rootId = node.branch_root_id || node.node_id;
        if (!collapsedRoots.has(rootId)) return true;
        return node.node_id === rootId;
      }});
    }}

    function renderBranchControls(layout) {{
      if (!layout.rootChildren.length) {{
        branchControls.innerHTML = '';
        return;
      }}
      branchControls.innerHTML = layout.rootChildren.map((node) => {{
        const preview = escapeHtml(truncate(node.text, 18));
        const collapsed = collapsedRoots.has(node.node_id);
        return `<button type="button" class="branch-toggle" data-root-id="${{node.node_id}}" data-collapsed="${{collapsed ? 'true' : 'false'}}">${{collapsed ? '펼치기' : '접기'}} · ${{preview}}</button>`;
      }}).join('');
      branchControls.querySelectorAll('.branch-toggle').forEach((button) => {{
        button.addEventListener('click', () => {{
          const rootId = button.getAttribute('data-root-id');
          if (!rootId) return;
          if (collapsedRoots.has(rootId)) {{
            collapsedRoots.delete(rootId);
          }} else {{
            collapsedRoots.add(rootId);
          }}
          loadGraph();
        }});
      }});
    }}

    function drawGraph(data) {{
      const nodes = data.nodes || [];
      const edges = data.edges || [];
      if (!nodes.length) {{
        svg.outerHTML = '<div class="card graph-empty">그래프를 표시할 기억이 없습니다.</div>';
        return;
      }}

      const center = nodes.find((node) => node.node_id === data.center_node_id) || nodes[0];
      const layout = computeLayout(nodes, center.node_id);
      renderBranchControls(layout);
      if (!selectedNodeId || !layout.byId.has(selectedNodeId)) {{
        selectedNodeId = center.node_id;
      }}
      const selectedNode = layout.byId.get(selectedNodeId) || center;
      const visible = visibleNodes(nodes, center.node_id);
      const visibleIds = new Set(visible.map((node) => node.node_id));
      const positions = layout.positions;
      const edgeMap = new Map(
        edges.map((edge) => [
          [edge.source_id, edge.target_id].sort().join('::'),
          edge,
        ])
      );

      document.getElementById('kpi-nodes').textContent = String(nodes.length);
      document.getElementById('kpi-edges').textContent = String(edges.length);
      document.getElementById('kpi-branches').textContent = String(layout.rootCount);
      document.getElementById('kpi-depth').textContent = String(
        nodes.reduce((maxDepth, node) => Math.max(maxDepth, node.depth || 0), 0)
      );

      const treeLines = nodes
        .filter((node) => node.parent_id && visibleIds.has(node.node_id) && visibleIds.has(node.parent_id))
        .map((node) => {{
          const from = positions.get(node.parent_id);
          const to = positions.get(node.node_id);
          const edge = edgeMap.get([node.parent_id, node.node_id].sort().join('::'));
          if (!from || !to) return '';
          const midX = from.x + (to.x - from.x) * 0.52;
          const stroke = Math.min(8, 2 + (edge?.weight || 0) * 1.4);
          const highlighted = selectedNode.node_id === node.node_id || selectedNode.node_id === node.parent_id || isAncestor(node.node_id, selectedNode.node_id, layout.byId) || isAncestor(node.parent_id, selectedNode.node_id, layout.byId);
          return `<path d="M ${{from.x}} ${{from.y}} C ${{midX}} ${{from.y}}, ${{midX}} ${{to.y}}, ${{to.x}} ${{to.y}}" stroke="${{highlighted ? '#7a5f36' : '#9d7f4c'}}" stroke-width="${{highlighted ? stroke + 1.2 : stroke}}" fill="none" stroke-linecap="round" opacity="${{highlighted ? '1' : '0.78'}}" />`;
        }})
        .join('');

      const secondaryLines = edges
        .filter((edge) => {{
          const source = layout.byId.get(edge.source_id);
          const target = layout.byId.get(edge.target_id);
          if (!source || !target) return false;
          if (!visibleIds.has(edge.source_id) || !visibleIds.has(edge.target_id)) return false;
          return source.parent_id !== edge.target_id && target.parent_id !== edge.source_id;
        }})
        .map((edge) => {{
          const from = positions.get(edge.source_id);
          const to = positions.get(edge.target_id);
          if (!from || !to) return '';
          return `<line x1="${{from.x}}" y1="${{from.y}}" x2="${{to.x}}" y2="${{to.y}}" stroke="#d9c6a1" stroke-width="1.5" stroke-dasharray="6 6" opacity="0.7" />`;
        }})
        .join('');

      const nodeMarkup = visible
        .map((node) => {{
          const pos = positions.get(node.node_id);
          if (!pos) return '';
          const isCenter = node.node_id === center.node_id;
          const isDirect = node.depth === 1;
          const isSelected = node.node_id === selectedNode.node_id;
          const isOnSelectedPath = isAncestor(node.node_id, selectedNode.node_id, layout.byId);
          const boxWidth = isCenter ? 244 : (isDirect ? 214 : 190);
          const boxHeight = isCenter ? 82 : 72;
          const x = pos.x - boxWidth / 2;
          const y = pos.y - boxHeight / 2;
          const fill = isSelected ? '#5f4728' : (isCenter ? '#7a5f36' : (isDirect ? '#e8d1a2' : '#fbf7ef'));
          const stroke = isSelected ? '#33230f' : (isOnSelectedPath ? '#8a6838' : (isCenter ? '#5b4526' : (isDirect ? '#b48847' : '#d7c4a0')));
          const title = escapeHtml(truncate(node.text, isCenter ? 56 : 42));
          const meta = isCenter ? '중심 기억' : (collapsedRoots.has(node.node_id) ? `depth ${{node.depth}} · 접힘` : `depth ${{node.depth}}`);
          const textColor = (isCenter || isSelected) ? '#fffdf8' : '#2b2419';
          return `
            <g class="graph-node" data-node-id="${{node.node_id}}" style="cursor:pointer;">
              <rect x="${{x}}" y="${{y}}" width="${{boxWidth}}" height="${{boxHeight}}" rx="20" fill="${{fill}}" stroke="${{stroke}}" stroke-width="${{isSelected ? 3 : (isCenter ? 2.4 : 1.4)}}"></rect>
              <text x="${{pos.x}}" y="${{y + 28}}" text-anchor="middle" font-size="12" fill="${{textColor}}" opacity="0.82">${{escapeHtml(meta)}}</text>
              <text x="${{pos.x}}" y="${{y + 50}}" text-anchor="middle" font-size="${{isCenter ? 16 : 14}}" font-weight="700" fill="${{textColor}}">${{title}}</text>
              <title>${{escapeHtml(summarize(node.text))}}</title>
            </g>
          `;
        }})
        .join('');

      svg.innerHTML = `<rect x="0" y="0" width="1240" height="760" fill="#fffdf8"></rect>${{secondaryLines}}${{treeLines}}${{nodeMarkup}}`;
      updateDetail(selectedNode, layout.branchSizes.get(selectedNode.node_id) || 0);
      svg.querySelectorAll('.graph-node').forEach((element) => {{
        element.addEventListener('click', () => {{
          const nodeId = element.getAttribute('data-node-id');
          const node = nodes.find((item) => item.node_id === nodeId);
          selectedNodeId = nodeId;
          updateDetail(node, layout.branchSizes.get(nodeId) || 0);
          drawGraph(data);
        }});
      }});
    }}

    async function loadGraph() {{
      const depth = depthInput.value;
      const limit = limitInput.value;
      const response = await fetch(`/api/graph/{node_id}?depth=${{encodeURIComponent(depth)}}&limit=${{encodeURIComponent(limit)}}`);
      const data = await response.json();
      drawGraph(data);
    }}

    reloadButton.addEventListener('click', loadGraph);
    loadGraph();
    function escapeHtml(text) {{
      return String(text ?? '')
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
