# -*- coding: utf-8 -*-
import unittest

from zhicai.agents.fusion import fuse_detail_data


class FusionTest(unittest.TestCase):
    def test_dom_priority_for_structured_fields(self):
        merged = fuse_detail_data({"name": "DOM名", "price": 100}, {"name": "VLM名", "price": 90})
        self.assertEqual(merged["name"], "DOM名")
        self.assertEqual(merged["price"], 100)

    def test_vlm_priority_for_visual_fields(self):
        merged = fuse_detail_data({"description": "DOM描述"}, {"description": "VLM描述"})
        self.assertEqual(merged["description"], "VLM描述")

    def test_price_cross_validation_flags_suspicious(self):
        merged = fuse_detail_data({"price": 100}, {"price": 200})
        self.assertTrue(merged.get("price_suspicious"))

    def test_no_suspicious_when_close(self):
        merged = fuse_detail_data({"price": 100}, {"price": 105})
        self.assertNotIn("price_suspicious", merged)


if __name__ == "__main__":
    unittest.main()
