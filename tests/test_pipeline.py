# -*- coding: utf-8 -*-
import tempfile
import unittest
from pathlib import Path

from zhicai.db.benchmark_store import BenchmarkStore
from zhicai.llm import MockLLM
from zhicai.pipeline import RiskPipeline, SourcingPipeline

ROOT = Path(__file__).resolve().parents[1]
SAMPLE_BID_TXT = ROOT / "examples" / "sample_bid.txt"


class PipelineTest(unittest.TestCase):
    def test_risk_pipeline_end_to_end(self):
        with tempfile.TemporaryDirectory() as d:
            store = BenchmarkStore(Path(d) / "b.sqlite")
            for name, prices in {"台式计算机": [4200, 4300, 4400], "键鼠套装": [80, 90, 100]}.items():
                pid = store.upsert_product(name, category="电子", platform="京东")
                for p in prices:
                    store.add_benchmark(pid, p, platform="京东", source_channel="DOM")
            out = RiskPipeline(MockLLM(), store=store).run(str(SAMPLE_BID_TXT))
            self.assertTrue(all(r.is_ok for r in out["results"]))
            self.assertIn("report", out)
            self.assertGreater(out["report"]["score"], 0)
            self.assertGreater(len(out["report"]["findings"]), 0)
            store.close()

    def test_sourcing_pipeline_end_to_end(self):
        dataset = [
            {"title": "台式计算机 A", "price": 4200, "shop": "京东", "url": "u1"},
            {"title": "台式计算机 B", "price": 4400, "shop": "淘宝", "url": "u2"},
            {"title": "台式计算机 C", "price": 4600, "shop": "1688", "url": "u3"},
        ]
        out = SourcingPipeline(MockLLM()).run("台式计算机", target_count=3, dataset=dataset)
        self.assertTrue(all(r.is_ok for r in out["results"]))
        self.assertEqual(len(out["state"].get("benchmark", {}).get("items", [])), 3)


if __name__ == "__main__":
    unittest.main()
