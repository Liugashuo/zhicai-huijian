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
        return "high"
    if rate > 0.3 or rate < -0.3:
        return "medium"
    return "low"
