# -*- coding: utf-8 -*-
"""确定性 MockLLM：保证系统可离线运行、测试可复现。"""

from __future__ import annotations

import re
from typing import Any

from .base import LLM


class MockLLM(LLM):
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
        return {"category": category, "keywords": [n], "platforms": platforms, "reasoning": "mock 关键词路由"}

    def decide_browser_action(
        self, context: dict[str, Any], screenshots: list[Any] | None = None
    ) -> dict[str, Any]:
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
