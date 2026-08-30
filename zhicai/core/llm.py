# -*- coding: utf-8 -*-
"""LLM 统一调用层。

AI/Python 分治：LLM 负责识别与判断，Python 负责流程与确定性算法。
默认提供 MockLLM 使系统可离线运行、可测试；真实环境可切换 OpenAI 兼容接口
（如 Ollama / vLLM 托管的 Qwen3）。
"""

from __future__ import annotations

import json
import re
from abc import ABC, abstractmethod
from typing import Any

from ..algorithms.json_repair import extract_json


class LLMProvider(ABC):
    """大模型抽象接口，所有语义判断都经由该接口，便于替换。"""

    @abstractmethod
    def complete(self, prompt: str, system: str | None = None) -> str:
        raise NotImplementedError

    def complete_json(self, prompt: str, system: str | None = None) -> Any:
        raw = self.complete(prompt, system)
        return extract_json(raw)

    # ---- 领域便捷方法（默认实现走 complete_json，真实模型无需重写） ----
    def classify_product(self, name: str) -> dict[str, Any]:
        return self.complete_json(f"对商品进行分类并提取检索关键词：{name}", "你是寻源分析专家")

    def decide_browser_action(self, context: dict[str, Any]) -> dict[str, Any]:
        return self.complete_json(json.dumps(context, ensure_ascii=False), "你是浏览器视觉决策 Agent")

    def extract_metadata(self, text: str) -> dict[str, Any]:
        return self.complete_json(f"提取招标元数据：{text}", "你是招投标信息抽取专家")

    def extract_items(self, text: str) -> list[dict[str, Any]]:
        return self.complete_json(f"提取报价条目：{text}", "你是报价单解析专家")

    def extract_sections(self, text: str) -> list[dict[str, Any]]:
        return self.complete_json(f"提取章节结构：{text}", "你是文档结构解析专家")

    def assess_quality(self, metrics: dict[str, Any]) -> str:
        return self.complete(json.dumps(metrics, ensure_ascii=False), "你是数据质量评估专家")

    def review_compliance(self, chunk: str, dimension: str) -> list[dict[str, Any]]:
        return self.complete_json(
            f"对以下文本做「{dimension}」维度的合规审查，仅输出违规项：\n{chunk}",
            "你是政府采购合规审查专家",
        )

    def summarize(self, payload: dict[str, Any]) -> str:
        return self.complete(json.dumps(payload, ensure_ascii=False), "你是采购风险研判总结专家")


class MockLLM(LLMProvider):
    """确定性 Mock 实现，保证离线可运行、测试可复现。"""

    def complete(self, prompt: str, system: str | None = None) -> str:
        return json.dumps({"note": "mock-llm", "system": system, "value": None}, ensure_ascii=False)

    def classify_product(self, name: str) -> dict[str, Any]:
        n = name or ""
        if any(k in n for k in ("电脑", "计算机", "笔记本", "台式机", "服务器", "打印机", "显示器", "CPU", "内存")):
            category, platforms = "电子", ["京东", "淘宝", "1688"]
        elif any(k in n for k in ("办公", "桌椅", "文具", "纸张", "硒鼓", "复印")):
            category, platforms = "办公", ["京东", "1688"]
        elif any(k in n for k in ("招标代理", "代理", "代维", "服务", "施工", "监理", "设计", "咨询")):
            category, platforms = "工程服务", ["行业门户"]
        else:
            category, platforms = "通用物资", ["京东", "淘宝", "拼多多", "1688"]
        return {
            "category": category,
            "keywords": [n],
            "platforms": platforms,
            "reasoning": "mock 关键词路由",
        }

    def decide_browser_action(self, context: dict[str, Any]) -> dict[str, Any]:
        page_type = context.get("page_type")
        collected = context.get("collected", 0)
        target = context.get("target", 5)
        if page_type == "search":
            if collected >= target:
                return {"action": "done", "reason": "采集目标达成"}
            if not context.get("products_extracted"):
                return {"action": "extract_products", "reason": "识别搜索页商品列表"}
            unvisited = context.get("unvisited", [])
            if unvisited:
                return {"action": "click_product", "index": unvisited[0]}
            return {"action": "done", "reason": "无更多商品可采集"}
        if page_type == "detail":
            return {"action": "extract_detail", "reason": "提取详情页字段"}
        return {"action": "done", "reason": "无可执行动作"}

    def assess_quality(self, metrics: dict[str, Any]) -> str:
        n = int(metrics.get("sample_count", 0))
        if n >= 5:
            return "样本充足，基准价具备市场参考意义。"
        if n >= 2:
            return "样本偏少，建议扩大采集范围后再研判。"
        return "样本不足，无法形成可靠基准价。"

    def extract_metadata(self, text: str) -> dict[str, Any]:
        def grab(*patterns: str) -> str | None:
            for p in patterns:
                m = re.search(p, text)
                if m:
                    return m.group(1).strip()
            return None

        return {
            "项目名称": grab(r"项目名称[:：]\s*([^\n]+)", r"采购项目[:：]\s*([^\n]+)"),
            "项目编号": grab(r"项目编号[:：]\s*([^\n]+)", r"招标编号[:：]\s*([^\n]+)"),
            "采购人": grab(r"采购人[:：]\s*([^\n]+)", r"采购单位[:：]\s*([^\n]+)"),
            "预算总额": grab(r"预算(?:总额|金额)[:：]\s*([^\n]+)"),
            "资质要求": grab(r"资质要求[:：]\s*([^\n]+)"),
        }

    def extract_items(self, text: str) -> list[dict[str, Any]]:
        from ..algorithms.extraction_rules import parse_line_items

        return parse_line_items(text)

    def extract_sections(self, text: str) -> list[dict[str, Any]]:
        from ..algorithms.chunking import split_by_headings

        return split_by_headings(text)

    def review_compliance(self, chunk: str, dimension: str) -> list[dict[str, Any]]:
        # Mock 不做语义判断，统一交给确定性规则引擎。
        return []

    def summarize(self, payload: dict[str, Any]) -> str:
        score = payload.get("score", 0)
        if score >= 70:
            return "存在显著异常风险，建议复核技术参数并开展市场比价。"
        if score >= 40:
            return "存在中等风险，建议对偏离项与合规问题逐项核实。"
        return "整体风险较低，未发现重大异常。"


class OpenAICompatibleLLM(LLMProvider):
    """OpenAI 兼容接口（Ollama / vLLM / 任意 base_url），用于接入真实 Qwen3。"""

    def __init__(self, base_url: str, model: str, api_key: str | None = None, temperature: float = 0.0) -> None:
        self.base_url = base_url
        self.model = model
        self.api_key = api_key
        self.temperature = temperature

    def complete(self, prompt: str, system: str | None = None) -> str:
        try:
            from openai import OpenAI
        except ImportError as exc:  # pragma: no cover
            raise RuntimeError("使用真实 LLM 需要安装 openai 包") from exc

        client = OpenAI(base_url=self.base_url, api_key=self.api_key or "EMPTY")
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})
        resp = client.chat.completions.create(model=self.model, messages=messages, temperature=self.temperature)
        return resp.choices[0].message.content or ""
