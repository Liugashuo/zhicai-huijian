# -*- coding: utf-8 -*-
import unittest

from zhicai.algorithms.extraction_rules import parse_line_items


class ExtractionRulesTest(unittest.TestCase):
    def test_normal_line(self):
        items = parse_line_items("台式计算机 10 台 6800 68000")
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]["quantity"], 10)
        self.assertEqual(items[0]["unit_price"], 6800)
        self.assertTrue(items[0]["verified"])

    def test_subtotal_as_unit_price_trap(self):
        items = parse_line_items("某配件 3 个 100 100")
        self.assertEqual(len(items), 1)
        self.assertTrue(items[0]["trap"])
        self.assertEqual(items[0]["subtotal"], 300.0)

    def test_ignore_irrelevant(self):
        items = parse_line_items("价格分未采用低价优先法，技术分权重 80%")
        self.assertEqual(items, [])


if __name__ == "__main__":
    unittest.main()
