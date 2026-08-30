# -*- coding: utf-8 -*-
import unittest

from zhicai.algorithms.deviation import deviation_rate, grade_deviation


class DeviationTest(unittest.TestCase):
    def test_rate(self):
        self.assertAlmostEqual(deviation_rate(150, 100), 0.5)

    def test_grade_high(self):
        self.assertEqual(grade_deviation(0.6), "high")

    def test_grade_medium_positive(self):
        self.assertEqual(grade_deviation(0.4), "medium")

    def test_grade_medium_negative(self):
        self.assertEqual(grade_deviation(-0.4), "medium")

    def test_grade_low(self):
        self.assertEqual(grade_deviation(0.1), "low")

    def test_grade_unknown(self):
        self.assertEqual(grade_deviation(None), "unknown")


if __name__ == "__main__":
    unittest.main()
