# -*- coding: utf-8 -*-
"""真实浏览器驱动（Playwright + Edge CDP，即 browser-use 的底层引擎）。

- `BrowserDriver`：7 类原子动作统一接口；
- `PlaywrightBrowserDriver`：控制本机 Edge，实现截图 / 滚动 / 点击 / DOM 提取；
- 拟人化反检测策略：贝塞尔曲线鼠标轨迹、分段随机滚动、随机延迟。
"""

from __future__ import annotations

import base64
import random
import time
from abc import ABC, abstractmethod
from typing import Any

from ..config.settings import BROWSER_HEADLESS


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
    def screenshot(self) -> str:
        raise NotImplementedError

    @abstractmethod
    def execute(self, action: dict[str, Any]) -> dict[str, Any]:
        raise NotImplementedError

    def close(self) -> None:
        return None


_PRODUCT_JS = r"""
() => {
  const sels = ['[class*="product"]', '[class*="item"]', '[class*="goods"]', 'li[data-sku]'];
  for (const sel of sels) {
    const els = Array.from(document.querySelectorAll(sel)).filter(
      (e) => e.querySelector('img') && (e.innerText || '').trim()
    );
    if (els.length >= 2) {
      return els.slice(0, 20).map((e, i) => {
        const img = e.querySelector('img');
        const m = (e.innerText || '').match(/\d+(\.\d+)?/);
        return {
          index: i,
          title: (e.innerText || '').trim().slice(0, 80),
          price: m ? parseFloat(m[0]) : null,
          url: img ? (img.src || img.getAttribute('data-src')) : '',
          shop: '',
        };
      });
    }
  }
  return [];
}
"""

_CLICK_JS = r"""
(idx) => {
  const sels = ['[class*="product"]', '[class*="item"]', '[class*="goods"]', 'li[data-sku]'];
  for (const sel of sels) {
    const els = Array.from(document.querySelectorAll(sel)).filter(
      (e) => e.querySelector('img') && (e.innerText || '').trim()
    );
    if (els.length > idx) {
      els[idx].click();
      return true;
    }
  }
  return false;
}
"""

_DETAIL_JS = r"""
() => {
  const node = document.querySelector('h1, [class*="title"], [class*="name"]');
  const title = (node ? node.innerText : '') || '';
  const body = document.body.innerText || '';
  const m = body.match(/(?:¥|￥|\$)\s*(\d+(?:\.\d+)?)/);
  return {
    name: (title || '').trim(),
    price: m ? parseFloat(m[1]) : null,
    shop: '',
    sales: null,
    url: location.href,
    source_channel: 'DOM',
  };
}
"""


class PlaywrightBrowserDriver(BrowserDriver):
    """使用 Playwright 控制本机 Edge（CDP）的真实浏览器执行器。"""

    def __init__(self, headless: bool | None = None) -> None:
        from playwright.sync_api import sync_playwright

        self._headless = BROWSER_HEADLESS if headless is None else headless
        self._pw = sync_playwright().start()
        self._browser = self._pw.chromium.launch(channel="msedge", headless=self._headless)
        self._page = self._browser.new_page(viewport={"width": 1366, "height": 900})
        self._page_type = "search"
        self._products: list[dict[str, Any]] = []
        self._finished = False

    def close(self) -> None:
        try:
            self._browser.close()
        except Exception:  # noqa: BLE001
            pass
        try:
            self._pw.stop()
        except Exception:  # noqa: BLE001
            pass

    def open(self, url: str) -> None:
        self._page.goto(url, wait_until="domcontentloaded", timeout=30000)
        self._page_type = "search"
        self._products = []
        self._finished = False

    def current_url(self) -> str:
        return self._page.url

    def page_type(self) -> str:
        return "done" if self._finished else self._page_type

    def screenshot(self) -> str:
        b64 = base64.b64encode(self._page.screenshot(type="png")).decode("ascii")
        return "data:image/png;base64," + b64

    def execute(self, action: dict[str, Any]) -> dict[str, Any]:
        try:
            return self._execute(action)
        except Exception as exc:  # noqa: BLE001
            return {"ok": False, "action": action.get("action"), "error": f"{type(exc).__name__}: {exc}"}

    def _execute(self, action: dict[str, Any]) -> dict[str, Any]:
        kind = action.get("action")
        if kind == "scroll":
            for dy in segmented_scroll():
                self._page.mouse.wheel(0, dy)
                time.sleep(random.uniform(0.1, 0.4))
            return {"ok": True, "action": kind}
        if kind == "extract_products":
            self._products = self._page.evaluate(_PRODUCT_JS)
            return {"ok": True, "action": kind, "items": self._products}
        if kind == "click_product":
            idx = int(action.get("index", 0))
            ok = bool(self._page.evaluate(_CLICK_JS, idx))
            if ok:
                self._page.wait_for_load_state("domcontentloaded")
                self._page_type = "detail"
                return {"ok": True, "action": kind, "index": idx}
            return {"ok": False, "action": kind, "error": "未找到可点击商品"}
        if kind == "extract_detail":
            detail = self._page.evaluate(_DETAIL_JS)
            return {"ok": True, "action": kind, "detail": detail}
        if kind == "go_back":
            self._page.go_back(wait_until="domcontentloaded")
            self._page_type = "search"
            return {"ok": True, "action": kind}
        if kind == "wait":
            seconds = float(action.get("seconds", 1))
            time.sleep(seconds)
            return {"ok": True, "action": kind, "waited": seconds}
        if kind == "done":
            self._finished = True
            return {"ok": True, "action": kind}
        return {"ok": False, "action": kind, "error": "未知动作"}
