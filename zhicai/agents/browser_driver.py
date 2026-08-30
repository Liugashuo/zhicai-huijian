# -*- coding: utf-8 -*-
"""浏览器抽象层：真实环境可替换为 browser-use (CDP)，离线用 Mock 驱动。"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


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
                    {"index": i, "title": d["title"], "price": d["price"], "shop": d.get("shop"),
                     "sales": d.get("sales"), "url": d.get("url")}
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
