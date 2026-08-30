# -*- coding: utf-8 -*-
import unittest

from zhicai.core.llm import MockLLM
from zhicai.core.state import StateManager
from zhicai.agents.compliance import ComplianceAgent


class ComplianceTest(unittest.TestCase):
    def _run(self, text):
        state = StateManager()
        chunks = [{"chunk_id": "bid_p1_c1", "section_title": None, "content": text}]
        state.set("evidence", {"chunks": chunks, "by_id": {c["chunk_id"]: c for c in chunks}})
        return ComplianceAgent(MockLLM()).run(state).data

    def test_brand_exclusivity(self):
        out = self._run("须采用华为 XX 型号")
        dims = {f["dimension"] for f in out["findings"]}
        self.assertIn("brand_exclusivity", dims)

    def test_regional_discrimination(self):
        out = self._run("具有某市固定办公场所")
        self.assertIn("regional_discrimination", {f["dimension"] for f in out["findings"]})

    def test_qualification_barrier(self):
        out = self._run("注册资本不低于500万元")
        self.assertIn("qualification_barrier", {f["dimension"] for f in out["findings"]})

    def test_contract_terms(self):
        out = self._run("争议由采购人所在地法院管辖")
        self.assertIn("contract_terms", {f["dimension"] for f in out["findings"]})

    def test_score_positive(self):
        out = self._run("指定品牌，注册资本不低于500万元")
        self.assertGreater(out["score"], 0)


if __name__ == "__main__":
    unittest.main()
