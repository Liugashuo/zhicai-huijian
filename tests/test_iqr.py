# -*- coding: utf-8 -*-
import unittest

from zhicai.algorithms.iqr import benchmark_metrics, filter_outliers, iqr_bounds


class IQRTest(unittest.TestCase):
    def test_filter_outliers(self):
        prices = [100, 101, 102, 103, 104, 500]
        valid, removed, _ = filter_outliers(prices)
        self.assertEqual(removed, 1)
        self.assertNotIn(500, valid)

    def test_benchmark_metrics(self):
        m = benchmark_metrics([10, 20, 30, 40])
        self.assertEqual(m["sample_count"], 4)
        self.assertEqual(m["median_price"], 25.0)
        self.assertAlmostEqual(m["benchmark_price"], 25.0)

    def test_bounds_sorted(self):
        q1, q3, lo, hi = iqr_bounds([1, 2, 3, 4, 5])
        self.assertLessEqual(lo, hi)
        self.assertEqual(q1, 2)
        self.assertEqual(q3, 4)


if __name__ == "__main__":
    unittest.main()
