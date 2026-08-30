# -*- coding: utf-8 -*-
"""任务一 Stage 3.1：商品属性智能分析（寻源策略生成）。"""

from __future__ import annotations

from typing import Any

from ..config.sites import sites_for_category
from ..core.agent import BaseAgent
from ..core.state import StateManager
from ..core.task_result import TaskResult


class ProductAnalysisAgent(BaseAgent):
    name = "ProductAnalysisAgent"
    state_key = "product_analysis"

    def run(self, state: StateManager) -> TaskResult:
        name = state.require("product_name")
        analysis = self.llm.classify_product(name) if self.llm else {"category": "通用物资", "keywords": [name]}
        analysis["product_name"] = name
        analysis["sites"] = [s.name for s in sites_for_category(analysis.get("category", "通用物资"))]
        return TaskResult.ok(self.name, analysis)
