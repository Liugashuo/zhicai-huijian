# -*- coding: utf-8 -*-
"""任务一 Stage 3.2：VLM 自主驱动的浏览器 Agent。

闭环：截图感知 -> 上下文推理 -> 动作执行 -> 反馈更新。
保留最近 3 张截图与 20 条对话消息，旧上下文压缩为摘要。
"""

from __future__ import annotations

from typing import Any

from ..core.agent import BaseAgent
from ..core.state import StateManager
from ..core.task_result import TaskResult
from .browser_driver import BrowserDriver, MockBrowserDriver


class BrowserAgent(BaseAgent):
    name = "BrowserAgent"
    state_key = "sourced_items"

    def __init__(self, llm=None, driver: BrowserDriver | None = None, max_steps: int = 60) -> None:
        super().__init__(llm)
        self.driver = driver or MockBrowserDriver([])
        self.max_steps = max_steps

    def run(self, state: StateManager) -> TaskResult:
        product_name = state.require("product_name")
        analysis = state.get("product_analysis", {})
        target = int(state.get("target_count", 5))
        site = (analysis.get("sites") or ["京东"])[0]

        self.driver.open(f"{site} 搜索: {product_name}")
        collected: list[dict[str, Any]] = []
        visited: set[int] = set()
        search_items: list[dict[str, Any]] = []
        products_extracted = False
        history: list[dict[str, Any]] = []
        screenshots: list[str] = []

        for step in range(self.max_steps):
            context = {
                "page_type": self.driver.page_type(),
                "url": self.driver.current_url(),
                "collected": len(collected),
                "target": target,
                "products_extracted": products_extracted,
                "unvisited": [i for i in range(len(search_items)) if i not in visited],
                "visited": sorted(visited),
            }
            action = self.llm.decide_browser_action(context) if self.llm else {"action": "done"}
            feedback = self.driver.execute(action)
            screenshots.append(self.driver.screenshot())
            screenshots = screenshots[-3:]
            history.append({"step": step, "action": action, "feedback": feedback})
            history = history[-20:]

            kind = action.get("action")
            if kind == "extract_products":
                search_items = feedback.get("items", [])
                products_extracted = True
            elif kind == "click_product":
                visited.add(int(action.get("index", 0)))
            elif kind == "extract_detail":
                detail = feedback.get("detail")
                if detail:
                    collected.append(detail)
                self.driver.execute({"action": "go_back"})
            elif kind == "done":
                break

        return TaskResult.ok(
            self.name,
            {"items": collected, "steps": len(history), "history": history, "screenshots": len(screenshots)},
        )
