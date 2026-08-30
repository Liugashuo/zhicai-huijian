# -*- coding: utf-8 -*-
"""价格偏离度量化与分级。"""

from __future__ import annotations


def deviation_rate(bid_price: float, market_avg: float) -> float | None:
    if not market_avg:
        return None
    return (float(bid_price) - float(market_avg)) / float(market_avg)


def grade_deviation(rate: float | None) -> str:
    if rate is None:
        return "unknown"
    if rate > 0.5:
        return "high"  # 异常高价 / 围标嫌疑
    if rate > 0.3 or rate < -0.3:
        return "medium"  # 偏离偏高 / 异常低价 / 不平衡报价嫌疑
    return "low"
