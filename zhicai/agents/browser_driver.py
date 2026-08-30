# -*- coding: utf-8 -*-
"""浏览器抽象层。

- `BrowserDriver`：7 类原子动作统一接口；
- `MockBrowserDriver`：基于内存数据集的确定性模拟（离线）；
- `BrowserUseDriver`：基于 browser-use（CDP）的真实浏览器执行器；
- 拟人化反检测策略：贝塞尔曲线鼠标轨迹、分段随机滚动、随机延迟。
"""

from __future__ import annotations

import asyncio
import math
import random
from abc import ABC, abstractmethod
from typing import Any


def bezier_curve(
    p0: tuple[float, float],
    p1: tuple[float, float],
    p2: tuple[float, float],
    p3: tuple[float, float],
    steps: int = 30,
) -> list[tuple[float, float]]:
    """三阶贝塞尔曲线插值，模拟人类手部不规则运动。"""
    out: list[tuple[float, float]] = []
    for i in range(steps + 1):
        t = i / steps
        mt = 1 - t
        x = mt**3 * p0[0] + 3 * mt**2 * t * p1[0] + 3 * mt * t**2 * p2[0] + t**3 * p3[0]
        y = mt**3 * p0[1] + 3 * mt**2 * t * p1[1] + 3 * mt * t**2 * p2[1] + t**3 * p3[1]
        out.append((round(x, 2), round(y, 2)))
    return out


def human_delay(min_s: float = 1.5, max_s: float = 3.5) -> float:
    """操作间随机延迟。"""
    return round(random.uniform(min_s, max_s), 2)


def segmented_scroll(steps: int = 5) -> list[int]:
    """分段随机滚动：多段距离随机 + 微停顿节奏。"""
    return [random.randint(120, 420) for _ in range(steps)]


class BrowserDriver(ABC):
    @abstractmethod
    def open(self, url: str) -> None:
        raise NotImplementedError

    @abstractmethod
    def current_url(self) -> str:
        raise NotImplementedError

    @abstractmethod
    def page_type(self) -> str:
        raise NotImplementedError

    @abstractmethod
    def screenshot(self) -> Any:
        raise NotImplementedError

    @abstractmethod
    def execute(self, action: dict[str, Any]) -> dict[str, Any]:
        raise NotImplementedError


class MockBrowserDriver(BrowserDriver):
    """基于内存数据集的确定性浏览器模拟。"""

    def __init__(self, dataset: list[dict[str, Any]]) -> None:
        self.dataset = dataset
        self._url = "about:blank"
        self._type = "search"
        self._current_index: int | None = None
        self._finished = False

    def open(self, url: str) -> None:
        self._url = url
        self._type = "search"
        self._finished = False
        self._current_index = None

    def current_url(self) -> str:
        return self._url

    def page_type(self) -> str:
        return "done" if self._finished else self._type

    def screenshot(self) -> str:
        return f"<shot:{self.page_type()}:idx={self._current_index}>"

    def execute(self, action: dict[str, Any]) -> dict[str, Any]:
        kind = action.get("action")
        if kind == "scroll":
            return {"ok": True, "action": kind}
        if kind == "extract_products":
            return {
                "ok": True,
                "action": kind,
                "items": [
                    {
                        "index": i,
                        "title": d["title"],
                        "price": d["price"],
                        "shop": d.get("shop"),
                        "sales": d.get("sales"),
                        "url": d.get("url"),
                    }
                    for i, d in enumerate(self.dataset)
                ],
            }
        if kind == "click_product":
            idx = int(action.get("index", 0))
            if 0 <= idx < len(self.dataset):
                self._current_index = idx
                self._type = "detail"
                return {"ok": True, "action": kind, "index": idx}
            return {"ok": False, "action": kind, "error": "index 越界"}
        if kind == "extract_detail":
            if self._current_index is None:
                return {"ok": False, "action": kind, "error": "当前不在详情页"}
            d = self.dataset[self._current_index]
            return {
                "ok": True,
                "action": kind,
                "detail": {
                    "name": d["title"],
                    "price": d["price"],
                    "shop": d.get("shop"),
                    "sales": d.get("sales"),
                    "url": d.get("url"),
                    "source_channel": "DOM",
                    "skus": d.get("skus", []),
                },
            }
        if kind == "go_back":
            self._type = "search"
            self._current_index = None
            return {"ok": True, "action": kind}
        if kind == "wait":
            return {"ok": True, "action": kind, "waited": action.get("seconds", 1)}
        if kind == "done":
            self._finished = True
            return {"ok": True, "action": kind}
        return {"ok": False, "action": kind, "error": "未知动作"}


class BrowserUseDriver(BrowserDriver):
    """基于 browser-use（CDP）的真实浏览器执行器。

    需要安装 `browser-use` 并配置一个通过 CDP 暴露的浏览器（或让 browser-use 启动）。
    拟人化策略（贝塞尔曲线、分段滚动、随机延迟）在动作执行时叠加。

    注意：browser-use 的 API 随版本演进，实际部署时请按所安装版本微调页面操作细节。
    """

    def __init__(self, headless: bool = False, cdp_url: str | None = None, user_data_dir: str | None = None) -> None:
        try:
            from browser_use import Browser, BrowserConfig  # noqa: F401
        except ImportError as exc:  # pragma: no cover
            raise RuntimeError("使用真实浏览器需要先安装 browser-use") from exc

        self._headless = headless
        self._cdp_url = cdp_url
        self._user_data_dir = user_data_dir
        self._browser = None
        self._page = None

    def _ensure_browser(self) -> None:
        if self._browser is not None:
            return
        from browser_use import Browser, BrowserConfig

        config = BrowserConfig(headless=self._headless, cdp_url=self._cdp_url, user_data_dir=self._user_data_dir)
        self._browser = Browser(config=config)
        asyncio.get_event_loop().run_until_complete(self._browser.start())
        self._page = asyncio.get_event_loop().run_until_complete(self._browser.get_current_page())

    def open(self, url: str) -> None:
        self._ensure_browser()
        asyncio.get_event_loop().run_until_complete(self._page.goto(url))

    def current_url(self) -> str:
        self._ensure_browser()
        return str(self._page.url)

    def page_type(self) -> str:
        # 真实环境可由 VLM 判断；此处做简易 URL 启发式。
        url = self.current_url()
        if "detail" in url or "item" in url:
            return "detail"
        return "search"

    def screenshot(self) -> str:
        self._ensure_browser()
        b64 = asyncio.get_event_loop().run_until_complete(self._page.screenshot(type="png"))
        return "data:image/png;base64," + __import__("base64").b64encode(b64).decode()

    def execute(self, action: dict[str, Any]) -> dict[str, Any]:
        self._ensure_browser()
        kind = action.get("action")
        if kind == "scroll":
            for dy in segmented_scroll():
                self._page.mouse.wheel(0, dy)
                asyncio.get_event_loop().run_until_complete(asyncio.sleep(random.uniform(0.1, 0.4)))
            return {"ok": True, "action": kind}
        if kind == "click_product":
            return {"ok": False, "action": kind, "error": "需结合页面元素定位实现，请按 browser-use 版本联调"}
        if kind == "extract_products" or kind == "extract_detail":
            return {"ok": False, "action": kind, "error": "需接入 VLM 结构化提取，请按 browser-use 版本联调"}
        if kind == "go_back":
            asyncio.get_event_loop().run_until_complete(self._page.go_back())
            return {"ok": True, "action": kind}
        if kind == "wait":
            seconds = float(action.get("seconds", 1))
            asyncio.get_event_loop().run_until_complete(asyncio.sleep(seconds))
            return {"ok": True, "action": kind}
        if kind == "done":
            return {"ok": True, "action": kind}
        return {"ok": False, "action": kind, "error": "未知动作"}
