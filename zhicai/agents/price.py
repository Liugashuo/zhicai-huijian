# -*- coding: utf-8 -*-
"""任务二 Stage 4.5：价格偏离智能分析（PriceAgent）。"""

from __future__ import annotations

from typing import Any

from ..algorithms.deviation import deviation_rate, grade_deviation
from ..algorithms.iqr import benchmark_metrics
from ..algorithms.similarity import jaccard_similarity
from ..core.agent import BaseAgent
from ..core.state import StateManager
from ..core.task_result import TaskResult
from ..db.benchmark_store import BenchmarkStore

ACCESSORY_KEYWORDS = ("键鼠", "键盘", "鼠标", "打印机", "线缆", "硒鼓", "耗材", "墨盒", "复印纸", "配件")


class PriceAgent(BaseAgent):
    name = "PriceAgent"
    state_key = "price_analysis"

    def __init__(self, llm=None, store: BenchmarkStore | None = None, jaccard_threshold: float = 0.15) -> None:
        super().__init__(llm)
        self.store = store
        self.jaccard_threshold = jaccard_threshold

    def _match(self, name: str) -> list[float]:
        if self.store is None:
            return []
        rows = self.store.search(name)
        if rows:
            return [float(r["price"]) for r in rows]
        best: list[tuple[float, str]] = []
        for p in self.store.all_products():
            sim = jaccard_similarity(name, p["name"])
            if sim >= self.jaccard_threshold:
                best.append((sim, p["name"]))
        best.sort(reverse=True)
        prices: list[float] = []
        for _sim, pname in best[:3]:
            prices.extend(self.store.prices_for(pname))
        return prices

    def run(self, state: StateManager) -> TaskResult:
        extraction = state.require("extraction")
        items = list(extraction.get("items", []))
        analyses: list[dict[str, Any]] = []

        for item in items:
            name = item.get("name", "")
            bid_price = item.get("unit_price")
            is_accessory = any(k in name for k in ACCESSORY_KEYWORDS)
            if bid_price is None:
                analyses.append(
                    {
                        "name": name,
                        "bid_price": None,
                        "market_prices": [],
                        "grade": "unknown",
                        "note": "报价单未解析出单价",
                        "is_accessory": is_accessory,
                    }
                )
                continue
            bid_price = float(bid_price)
            prices = self._match(name)
            if not prices:
                analyses.append(
                    {
                        "name": name,
                        "bid_price": bid_price,
                        "market_prices": [],
                        "market_avg": None,
                        "deviation_rate": None,
                        "grade": "unknown",
                        "note": "无可比数据",
                        "is_accessory": is_accessory,
                    }
                )
                continue
            metrics = benchmark_metrics(prices)
            market_avg = float(metrics["benchmark_price"])
            rate = deviation_rate(bid_price, market_avg)
            grade = grade_deviation(rate)
            unbalanced = is_accessory and (rate is not None and rate > 0.3)
            analyses.append(
                {
                    "name": name,
                    "bid_price": bid_price,
                    "market_prices": prices,
                    "market_avg": market_avg,
                    "median_price": metrics["median_price"],
                    "deviation_rate": round(rate, 4) if rate is not None else None,
                    "grade": grade,
                    "is_accessory": is_accessory,
                    "unbalanced": unbalanced,
                    "note": "不平衡报价嫌疑" if unbalanced else "",
                }
            )

        return TaskResult.ok(self.name, analyses)
