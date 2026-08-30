# -*- coding: utf-8 -*-
"""SQLite 比价基准库：products 与 price_benchmarks 两张表。"""

from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


class BenchmarkStore:
    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(str(self.path))
        self._conn.row_factory = sqlite3.Row
        self._init_schema()

    def _init_schema(self) -> None:
        self._conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                category TEXT,
                platform TEXT,
                url TEXT,
                created_at TEXT
            );
            CREATE TABLE IF NOT EXISTS price_benchmarks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                product_id INTEGER NOT NULL,
                price REAL NOT NULL,
                platform TEXT,
                source_channel TEXT,
                source_url TEXT,
                captured_at TEXT,
                FOREIGN KEY(product_id) REFERENCES products(id)
            );
            """
        )
        self._conn.commit()

    def close(self) -> None:
        self._conn.close()

    def upsert_product(
        self, name: str, category: str | None = None, platform: str | None = None, url: str | None = None
    ) -> int:
        row = self._conn.execute(
            "SELECT id FROM products WHERE name = ? AND platform IS ?", (name, platform)
        ).fetchone()
        now = datetime.now(timezone.utc).isoformat()
        if row:
            return int(row["id"])
        cur = self._conn.execute(
            "INSERT INTO products(name, category, platform, url, created_at) VALUES(?,?,?,?,?)",
            (name, category, platform, url, now),
        )
        self._conn.commit()
        return int(cur.lastrowid)

    def add_benchmark(
        self,
        product_id: int,
        price: float,
        platform: str | None = None,
        source_channel: str | None = None,
        source_url: str | None = None,
    ) -> int:
        cur = self._conn.execute(
            "INSERT INTO price_benchmarks(product_id, price, platform, source_channel, source_url, captured_at) "
            "VALUES(?,?,?,?,?,?)",
            (product_id, float(price), platform, source_channel, source_url, datetime.now(timezone.utc).isoformat()),
        )
        self._conn.commit()
        return int(cur.lastrowid)

    def search(self, name: str, limit: int = 20) -> list[dict[str, Any]]:
        prefix = (name or "")[:10]
        rows = self._conn.execute(
            """
            SELECT p.name, b.price, b.platform, b.source_channel, b.source_url
            FROM price_benchmarks b JOIN products p ON p.id = b.product_id
            WHERE p.name LIKE ?
            ORDER BY b.price
            LIMIT ?
            """,
            (f"%{prefix}%", limit),
        ).fetchall()
        return [dict(r) for r in rows]

    def all_products(self) -> list[dict[str, Any]]:
        rows = self._conn.execute("SELECT * FROM products").fetchall()
        return [dict(r) for r in rows]

    def prices_for(self, name: str, limit: int = 100) -> list[float]:
        rows = self.search(name, limit=limit)
        return [float(r["price"]) for r in rows]

    def count_benchmarks(self) -> int:
        return int(self._conn.execute("SELECT COUNT(*) FROM price_benchmarks").fetchone()[0])
