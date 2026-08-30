# -*- coding: utf-8 -*-
import unittest

from zhicai.algorithms.similarity import jaccard_similarity, tokenize


class SimilarityTest(unittest.TestCase):
    def test_tokenize_mixed(self):
        tokens = tokenize("台式计算机 Dell-3020 16GB")
        self.assertIn("台式", tokens)
        self.assertIn("dell", tokens)
        self.assertIn("16", tokens)
        self.assertIn("3020", tokens)

    def test_jaccard_same(self):
        self.assertEqual(jaccard_similarity("台式计算机", "台式计算机"), 1.0)

    def test_jaccard_near_synonym(self):
        sim = jaccard_similarity("台式计算机", "台式机")
        self.assertGreaterEqual(sim, 0.15)

    def test_jaccard_unrelated(self):
        self.assertLess(jaccard_similarity("打印机", "网络线缆"), 0.15)


if __name__ == "__main__":
    unittest.main()
