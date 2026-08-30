# -*- coding: utf-8 -*-
import unittest

from zhicai.algorithms.json_repair import extract_json, repair_json


class JsonRepairTest(unittest.TestCase):
    def test_repair_truncated_array(self):
        self.assertEqual(repair_json('{"a": [1, 2'), '{"a": [1, 2]}')

    def test_repair_unclosed_string(self):
        self.assertEqual(repair_json('{"name": "abc'), '{"name": "abc"}')

    def test_extract_from_prefix(self):
        self.assertEqual(extract_json('前缀文本 {"a": 1}'), {"a": 1})

    def test_extract_truncated(self):
        self.assertEqual(extract_json('{"items": [1,2,3'), {"items": [1, 2, 3]})


if __name__ == "__main__":
    unittest.main()
