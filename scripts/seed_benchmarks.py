# -*- coding: utf-8 -*-
"""向 SQLite 比价基准库写入演示行情数据。"""

from __future__ import annotations

import argparse

from zhicai.db.benchmark_store import BenchmarkStore


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default="output/benchmarks.sqlite")
    args = ap.parse_args()
    store = BenchmarkStore(args.db)
    samples = {
        "台式计算机": [4200, 4300, 4400, 4500, 4600],
        "笔记本电脑": [5500, 5600, 5700, 5800, 5900],
        "激光打印机": [1500, 1600, 1700, 1800],
    }
    for name, prices in samples.items():
        pid = store.upsert_product(name, category="电子", platform="京东")
        for price in prices:
            store.add_benchmark(pid, price, platform="京东", source_channel="DOM")
    print(f"已写入 {store.count_benchmarks()} 条行情数据")
    store.close()


if __name__ == "__main__":
    main()
