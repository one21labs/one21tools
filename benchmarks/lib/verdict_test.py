#!/usr/bin/env python3
"""Unit tests for verdict_of's decision logic (ADR 0024). Run: python -m unittest verdict_test."""
import unittest

from verdict import verdict_of


class VerdictOfTest(unittest.TestCase):
    def test_keep_when_ci_excludes_zero_and_positive(self):
        self.assertEqual(verdict_of(0.3, 0.1, 0.5, 4), "KEEP")

    def test_harmful_when_ci_excludes_zero_and_negative(self):
        self.assertEqual(verdict_of(-0.3, -0.5, -0.1, 4), "HARMFUL")

    def test_cut_candidate_when_ci_straddles_zero_and_mean_near_zero(self):
        self.assertEqual(verdict_of(0.01, -0.2, 0.2, 4), "CUT-CANDIDATE")

    def test_inconclusive_when_ci_straddles_zero_and_mean_not_near_zero(self):
        self.assertEqual(verdict_of(0.2, -0.1, 0.5, 4), "INCONCLUSIVE")

    def test_zero_n_is_inconclusive(self):
        self.assertEqual(verdict_of(0.0, 0.0, 0.0, 0), "INCONCLUSIVE")


if __name__ == "__main__":
    unittest.main()
