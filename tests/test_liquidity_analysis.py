import unittest
from analysis.liquidity import exact_win_test


class ContrastTests(unittest.TestCase):
    def test_exact_tail_known_extremes(self):
        self.assertEqual(exact_win_test(0, 0), 1)
        self.assertEqual(exact_win_test(5, 0), 1/32)
        self.assertEqual(exact_win_test(0, 5), 1)
        self.assertEqual(exact_win_test(3, 3), 42/64)
