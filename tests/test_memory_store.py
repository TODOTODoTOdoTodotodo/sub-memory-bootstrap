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


class LazyDimensionEmbedder(FakeEmbedder):
    @property
    def dimension(self) -> int:
        raise AssertionError("startup should not require embedder.dimension")


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

    def test_startup_does_not_force_embedder_dimension(self) -> None:
        store = MemoryStore(self.settings, LazyDimensionEmbedder())
        try:
            self.assertEqual(store.count_nodes(), 0)
        finally:
            store.close()
