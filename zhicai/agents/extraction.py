# -*- coding: utf-8 -*-
"""任务二 Stage 4.4：LLM 三轮结构化提取（元数据 / 产品条目 / 章节结构）+ 确定性兜底。"""

from __future__ import annotations

from typing import Any

from ..algorithms.extraction_rules import parse_line_items
from ..core.agent import BaseAgent
from ..core.state import StateManager
from ..core.task_result import TaskResult


def _merge_items(*item_lists: list[dict[str, Any]]) -> list[dict[str, Any]]:
    merged: dict[tuple[str, float], dict[str, Any]] = {}
    for items in item_lists:
        for item in items:
            key = (str(item.get("name", "")), float(item.get("quantity", 0)))
            if key not in merged or item.get("verified", False):
                merged[key] = item
    return list(merged.values())


class ExtractionAgent(BaseAgent):
    name = "ExtractionAgent"
    state_key = "extraction"

    def run(self, state: StateManager) -> TaskResult:
        document = state.require("document")
        text = document.get("text", "")

        metadata = self.llm.extract_metadata(text[:5000]) if self.llm else {}
        llm_items = self.llm.extract_items(text) if self.llm else []
        rule_items = parse_line_items(text)
        items = _merge_items(rule_items, llm_items)
        sections = self.llm.extract_sections(text[:6000]) if self.llm else []

        return TaskResult.ok(self.name, {"metadata": metadata, "items": items, "sections": sections})
