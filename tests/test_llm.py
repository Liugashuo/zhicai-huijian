# -*- coding: utf-8 -*-
import os
import unittest
from unittest import mock

from zhicai.llm import MockLLM, build_llm

try:
    from langchain_core.language_models.fake_chat_models import GenericFakeChatModel
    from langchain_core.messages import AIMessage

    HAVE_LANGCHAIN = True
except ImportError:  # pragma: no cover
    HAVE_LANGCHAIN = False


class MockLLMTest(unittest.TestCase):
    def setUp(self):
        self.llm = MockLLM()

    def test_classify_product(self):
        out = self.llm.classify_product("台式计算机")
        self.assertEqual(out["category"], "电子")
        self.assertIn("keywords", out)

    def test_decide_browser_action(self):
        out = self.llm.decide_browser_action({"page_type": "search", "collected": 0, "target": 5})
        self.assertEqual(out["action"], "extract_products")

    def test_extract_metadata(self):
        out = self.llm.extract_metadata("项目名称：某项目\n预算总额：100万元")
        self.assertEqual(out["项目名称"], "某项目")

    def test_extract_items_delegates_to_rules(self):
        out = self.llm.extract_items("台式计算机 10 台 6800 68000")
        self.assertEqual(len(out), 1)
        self.assertTrue(out[0]["verified"])

    def test_extract_sections(self):
        out = self.llm.extract_sections("一、概述\n内容A\n二、需求\n内容B")
        self.assertGreaterEqual(len(out), 1)

    def test_assess_quality(self):
        self.assertIn("样本", self.llm.assess_quality({"sample_count": 5}))

    def test_review_compliance_empty(self):
        self.assertEqual(self.llm.review_compliance("任意文本", "brand_exclusivity"), [])

    def test_summarize(self):
        self.assertIn("风险", self.llm.summarize({"score": 80}))


class BuildLLMTest(unittest.TestCase):
    def test_build_llm_returns_mock_without_env(self):
        with mock.patch.dict(os.environ, {}, clear=True):
            self.assertIsInstance(build_llm(), MockLLM)


@unittest.skipUnless(HAVE_LANGCHAIN, "需要安装 langchain-core")
class LangChainLLMTest(unittest.TestCase):
    def test_json_roundtrip(self):
        from zhicai.llm.langchain_llm import LangChainLLM

        model = GenericFakeChatModel(
            messages=iter([AIMessage(content='{"category": "电子", "keywords": ["电脑"], "reasoning": "ok"}')])
        )
        llm = LangChainLLM(model)
        self.assertEqual(llm.classify_product("电脑")["category"], "电子")

    def test_truncated_json_repaired(self):
        from zhicai.llm.langchain_llm import LangChainLLM

        model = GenericFakeChatModel(messages=iter([AIMessage(content='{"category": "电子", "keywords": [')]))
        llm = LangChainLLM(model)
        self.assertEqual(llm.classify_product("电脑")["category"], "电子")


if __name__ == "__main__":
    unittest.main()
