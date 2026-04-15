from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

try:
    import sqlite_vec  # noqa: F401
except ImportError:  # pragma: no cover - depends on native extension
    SQLITE_VEC_AVAILABLE = False
else:
    SQLITE_VEC_AVAILABLE = True

from sub_memory.config import Settings
from sub_memory.store import MemoryStore


class FakeEmbedder:
    dimension = 4

    _vectors = {
        "User: alpha\nAssistant: first": [1.0, 0.0, 0.0, 0.0],
        "User: beta\nAssistant: second": [0.9, 0.1, 0.0, 0.0],
        "User: gamma\nAssistant: third": [0.8, 0.2, 0.0, 0.0],
        "alpha": [1.0, 0.0, 0.0, 0.0],
        "beta": [0.9, 0.1, 0.0, 0.0],
        "gamma": [0.8, 0.2, 0.0, 0.0],
    }

    def embed_text(self, text: str) -> list[float]:
        return self._vectors[text]


@unittest.skipUnless(SQLITE_VEC_AVAILABLE, "sqlite-vec is required for this test")
class MemoryStoreTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.base_path = Path(self.temp_dir.name)
        self.settings = Settings(
            base_dir=self.base_path,
            db_path=self.base_path / "memory.db",
            openai_api_key=None,
            openai_model="gpt-5-mini",
            embedding_model_name="fake-embedder",
            sqlite_vec_path=None,
            recall_depth=2,
            recall_limit=6,
            compact_after_turns=4,
            compact_keep_recent_turns=2,
            compact_summary_char_limit=2400,
            metrics_log_path=self.base_path / ".sub-memory" / "metrics.jsonl",
            metrics_retention_days=30,
        )
        self.store = MemoryStore(self.settings, FakeEmbedder())

    def tearDown(self) -> None:
        self.store.close()
        self.temp_dir.cleanup()

    def test_store_recall_and_reinforce_flow(self) -> None:
        first = self.store.store_memory("alpha", "first")
        second = self.store.store_memory("beta", "second")
        third = self.store.store_memory("gamma", "third")

        self.assertEqual(self.store.count_nodes(), 3)
        self.assertIsNotNone(self.store.get_edge_weight(first["node_id"], second["node_id"]))
        self.assertIsNotNone(self.store.get_edge_weight(second["node_id"], third["node_id"]))

        recalled = self.store.recall_associated_memory("alpha", depth=2)
        recalled_ids = recalled["node_ids"]

        self.assertGreaterEqual(len(recalled_ids), 2)
        self.assertEqual(recalled_ids[0], first["node_id"])

        prior_weight = self.store.get_edge_weight(first["node_id"], second["node_id"])
        assert prior_weight is not None

        reinforced = self.store.reinforce_memory(recalled_ids[:2])
        self.assertEqual(reinforced["status"], "reinforced")

        updated_weight = self.store.get_edge_weight(first["node_id"], second["node_id"])
        assert updated_weight is not None
        self.assertAlmostEqual(updated_weight, prior_weight + 0.1, places=6)

    def test_dashboard_and_graph_queries(self) -> None:
        first = self.store.store_memory("alpha", "first")
        second = self.store.store_memory("beta", "second")
        self.store.store_memory("gamma", "third")

        dashboard = self.store.get_dashboard_stats()
        self.assertEqual(dashboard["node_count"], 3)
        self.assertGreaterEqual(dashboard["edge_count"], 2)
        self.assertEqual(len(dashboard["recent_memories"]), 3)

        memories = self.store.list_memories(query="beta")
        self.assertEqual(len(memories), 1)
        self.assertIn("beta", memories[0]["text"])

        detail = self.store.get_memory(second["node_id"])
        self.assertIsNotNone(detail)

        connected = self.store.get_connected_memories(second["node_id"])
        self.assertGreaterEqual(len(connected), 1)

        graph = self.store.get_graph_subtree(first["node_id"], depth=2, limit=10)
        self.assertEqual(graph["center_node_id"], first["node_id"])
        self.assertGreaterEqual(len(graph["nodes"]), 2)
        self.assertGreaterEqual(len(graph["edges"]), 1)
