# -*- coding: utf-8 -*-
"""任务一 Stage 3.5：智能化数据甄别（IQR 去极值 + 三级去重 + 来源标记）。"""

from __future__ import annotations

from typing import Any

from ..algorithms.iqr import iqr_bounds
from ..core.agent import BaseAgent
from ..core.state import StateManager
from ..core.task_result import TaskResult


class DataCleaningAgent(BaseAgent):
    name = "DataCleaningAgent"
    state_key = "cleaned_items"

    def run(self, state: StateManager) -> TaskResult:
        sourced = state.get("sourced_items", {})
        items = list(sourced.get("items", []))
        prices = [float(x.get("price", 0)) for x in items]
        q1, q3, lower, upper = iqr_bounds(prices)

        seen_pid: set[str] = set()
        seen_url: set[str] = set()
        seen_name: set[str] = set()
        cleaned: list[dict[str, Any]] = []
        outlier_count = 0

        for item in items:
            price = float(item.get("price", 0))
            if not (lower <= price <= upper):
                outlier_count += 1
                continue
            pid = str(item.get("product_id") or "")
            url = str(item.get("url") or "")
            name = str(item.get("name") or "")
            if pid and pid in seen_pid:
                continue
            if url and url in seen_url:
                continue
            if name and name in seen_name:
                continue
            seen_pid.add(pid)
            seen_url.add(url)
            seen_name.add(name)
            cleaned.append(item)

        return TaskResult.ok(
            self.name,
            {"items": cleaned, "outlier_count": outlier_count, "iqr_bounds": [q1, q3, lower, upper]},
        )
