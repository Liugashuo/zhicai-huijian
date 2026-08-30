# -*- coding: utf-8 -*-
"""IQR 四分位距去极值 + 基准价测算。"""

from __future__ import annotations

from statistics import mean, median


def _quartiles(sorted_values: list[float]) -> tuple[float, float]:
    n = len(sorted_values)
    if n == 0:
        return 0.0, 0.0
    return sorted_values[n // 4], sorted_values[3 * n // 4]


def iqr_bounds(prices: list[float]) -> tuple[float, float, float, float]:
    s = sorted(prices)
    q1, q3 = _quartiles(s)
    iqr = q3 - q1
    lower = q1 - 1.5 * iqr
    upper = q3 + 1.5 * iqr
    return q1, q3, lower, upper


def filter_outliers(prices: list[float]) -> tuple[list[float], int, tuple[float, float, float, float]]:
    q1, q3, lower, upper = iqr_bounds(prices)
    valid = [p for p in prices if lower <= p <= upper]
    return valid, len(prices) - len(valid), (q1, q3, lower, upper)


def benchmark_metrics(prices: list[float]) -> dict[str, float | int]:
    prices = [float(p) for p in prices]
    if not prices:
        return {
            "benchmark_price": 0.0,
            "median_price": 0.0,
            "p25_price": 0.0,
            "p75_price": 0.0,
            "min_price": 0.0,
            "max_price": 0.0,
            "sample_count": 0,
            "outlier_count": 0,
        }
    valid, outlier_count, (q1, q3, _lower, _upper) = filter_outliers(prices)
    if not valid:
        valid = prices
    return {
        "benchmark_price": round(mean(valid), 2),
        "median_price": round(median(valid), 2),
        "p25_price": round(q1, 2),
        "p75_price": round(q3, 2),
        "min_price": round(min(valid), 2),
        "max_price": round(max(valid), 2),
        "sample_count": len(prices),
        "outlier_count": outlier_count,
    }
