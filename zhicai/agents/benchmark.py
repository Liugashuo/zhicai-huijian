# -*- coding: utf-8 -*-
"""任务一 Stage 3.5：基准价测算 + AI 定性评估。"""

from __future__ import annotations

from typing import Any

from ..algorithms.iqr import benchmark_metrics
from ..core.agent import BaseAgent
from ..core.state import StateManager
from ..core.task_result import TaskResult


class BenchmarkAgent(BaseAgent):
    name = "BenchmarkAgent"
    state_key = "benchmark"

    def run(self, state: StateManager) -> TaskResult:
        cleaned = state.get("cleaned_items", {})
        items = list(cleaned.get("items", []))
        prices = [float(x.get("price", 0)) for x in items]
        metrics = benchmark_metrics(prices)
        assessment = self.llm.assess_quality(metrics) if self.llm else ""
        return TaskResult.ok(self.name, {"metrics": metrics, "ai_assessment": assessment, "items": items})
