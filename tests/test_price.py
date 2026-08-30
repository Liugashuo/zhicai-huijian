# -*- coding: utf-8 -*-
import tempfile
import unittest
from pathlib import Path

from zhicai.agents.price import PriceAgent
from zhicai.core.state import StateManager
from zhicai.db.benchmark_store import BenchmarkStore
from zhicai.llm import MockLLM


class PriceTest(unittest.TestCase):
    def test_three_level_matching(self):
        with tempfile.TemporaryDirectory() as d:
            store = BenchmarkStore(Path(d) / "b.sqlite")
            pid = store.upsert_product("台式机", category="电子", platform="京东")
            for p in [4200, 4300, 4400]:
                store.add_benchmark(pid, p, platform="京东", source_channel="DOM")

            state = StateManager()
            state.set(
                "extraction",
                {
                    "items": [
                        {"name": "台式计算机", "quantity": 10, "unit": "台", "unit_price": 6800},
                        {"name": "神秘设备", "quantity": 1, "unit": "台", "unit_price": 999},
                    ]
                },
            )
            data = PriceAgent(MockLLM(), store=store).run(state).data
            matched = [x for x in data if x["name"] == "台式计算机"][0]
            unknown = [x for x in data if x["name"] == "神秘设备"][0]
            self.assertEqual(matched["grade"], "high")
            self.assertEqual(unknown["grade"], "unknown")
            store.close()


if __name__ == "__main__":
    unittest.main()
