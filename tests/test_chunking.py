# -*- coding: utf-8 -*-
import unittest

from zhicai.algorithms.chunking import chunk_text, split_by_headings


class ChunkingTest(unittest.TestCase):
    def test_split_by_headings(self):
        sections = split_by_headings("一、概述\n内容A\n二、需求\n内容B")
        self.assertEqual(len(sections), 2)
        self.assertEqual(sections[0]["title"], "一、概述")

    def test_fixed_chunk(self):
        chunks = chunk_text("字" * 4500, chunk_size=2000, overlap=200)
        self.assertGreater(len(chunks), 1)
        self.assertLessEqual(max(len(c) for c in chunks), 2000)


if __name__ == "__main__":
    unittest.main()
