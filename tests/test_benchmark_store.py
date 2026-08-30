# -*- coding: utf-8 -*-
import tempfile
import unittest
from pathlib import Path

from zhicai.db.benchmark_store import BenchmarkStore


class BenchmarkStoreTest(unittest.TestCase):
    def test_upsert_and_search(self):
        with tempfile.TemporaryDirectory() as d:
            store = BenchmarkStore(Path(d) / "b.sqlite")
            pid = store.upsert_product("台式计算机", category="电子", platform="京东")
            store.add_benchmark(pid, 4200, platform="京东", source_channel="DOM")
            rows = store.search("台式计算机")
            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0]["price"], 4200)
            store.close()


if __name__ == "__main__":
    unittest.main()
