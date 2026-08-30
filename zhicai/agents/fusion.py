# -*- coding: utf-8 -*-
"""VLM/DOM 字段可信度融合（fuse_detail_data）。

结构化字段 DOM 优先、VLM 补充；视觉字段 VLM 优先；价格字段交叉验证。
"""

from __future__ import annotations

from typing import Any

_STRUCT_FIELDS = ("name", "price", "shop", "sales", "sku", "url")
_VISUAL_FIELDS = ("description", "promotion")


def _num(value: Any) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def fuse_detail_data(dom: dict[str, Any] | None, vlm: dict[str, Any] | None) -> dict[str, Any]:
    dom = dom or {}
    vlm = vlm or {}
    merged: dict[str, Any] = {}

    for key in _STRUCT_FIELDS:
        if dom.get(key) not in (None, ""):
            merged[key] = dom[key]
        elif vlm.get(key) not in (None, ""):
            merged[key] = vlm[key]

    for key in _VISUAL_FIELDS:
        if vlm.get(key) not in (None, ""):
            merged[key] = vlm[key]
        elif dom.get(key) not in (None, ""):
            merged[key] = dom[key]

    dom_price = _num(dom.get("price"))
    vlm_price = _num(vlm.get("price"))
    if dom_price is not None and vlm_price is not None and dom_price:
        if abs(dom_price - vlm_price) / dom_price > 0.15:
            merged["price_suspicious"] = True
            merged["price_dom"] = dom_price
            merged["price_vlm"] = vlm_price

    return merged
