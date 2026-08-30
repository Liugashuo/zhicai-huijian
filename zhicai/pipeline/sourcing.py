# -*- coding: utf-8 -*-
"""任务一 · 自主寻源流水线：分析 -> 浏览器采集 -> 清洗 -> 基准测算。"""

from __future__ import annotations

from typing import Any

from ..agents import BenchmarkAgent, BrowserAgent, DataCleaningAgent, ProductAnalysisAgent
from ..agents.browser_driver import BrowserDriver, MockBrowserDriver
from ..core.pipeline import Pipeline
from ..core.state import StateManager
from ..db.benchmark_store import BenchmarkStore
from ..llm import LLM


class SourcingPipeline:
    def __init__(
        self,
        llm: LLM | None = None,
        store: BenchmarkStore | None = None,
        driver: BrowserDriver | None = None,
    ) -> None:
        self.llm = llm
        self.store = store
        self.driver = driver

    def run(
        self, product_name: str, target_count: int = 5, dataset: list[dict[str, Any]] | None = None
    ) -> dict[str, Any]:
        state = StateManager()
        state.set("product_name", product_name)
        state.set("target_count", target_count)
        driver = self.driver or MockBrowserDriver(dataset or [])
        agents = [
            ProductAnalysisAgent(self.llm),
            BrowserAgent(self.llm, driver=driver),
            DataCleaningAgent(self.llm),
            BenchmarkAgent(self.llm),
        ]
        results = Pipeline(state).execute(agents)

        if self.store is not None:
            analysis = state.get("product_analysis", {})
            benchmark = state.get("benchmark", {})
            pid = self.store.upsert_product(
                product_name, category=analysis.get("category"), platform=(analysis.get("sites") or [None])[0]
            )
            for item in benchmark.get("items", []):
                self.store.add_benchmark(
                    pid,
                    float(item.get("price", 0)),
                    platform=(analysis.get("sites") or [None])[0],
                    source_channel=item.get("source_channel", "DOM"),
                    source_url=item.get("url"),
                )

        return {"state": state, "results": results, "product_name": product_name}
