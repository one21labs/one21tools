#!/usr/bin/env python3
"""Unit tests for verdict_of's and merge_verdict's decision logic (ADR 0024, ADR 0027).
Run: python -m unittest verdict_test."""
import unittest

from verdict import merge_verdict, verdict_of


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


class MergeVerdictTest(unittest.TestCase):
    def test_bs_iter2_weak_confidence_cost_up_reverts_to_no_merge(self):
        # benchmarks/2026-07-09-bs-iter2-remeasure: diff mean +0.002, CI [-0.137, +0.140],
        # +187 always-loaded chars. aggregate.py printed "MERGE (weak)"; the settled ADR 0027
        # bar (cost prong, ADR 0024 step 2d) says NO MERGE — issue #142.
        self.assertEqual(merge_verdict(0.002, -0.137, 0.140, 6, 187), (False, None))

    def test_ep_remeasure_weak_confidence_cost_down_still_merges(self):
        # benchmarks/2026-07-09-ep-remeasure-hermetic: diff mean +0.174, CI [-0.028, +0.376],
        # body chars 5464 -> 4012 (-1452 always-loaded). Cost prong clears (cost DOWN), so the
        # weak-confidence merge stands — the clean-win case the cost prong must not break.
        self.assertEqual(merge_verdict(0.174, -0.028, 0.376, 6, -1452), (True, "weak"))

    def test_strong_confidence_merges_regardless_of_cost(self):
        # CI excludes 0 -> "strong" confidence is not contingent on the cost prong.
        self.assertEqual(merge_verdict(0.3, 0.1, 0.5, 6, 50), (True, "strong"))

    def test_mean_not_positive_is_no_merge_regardless_of_cost(self):
        self.assertEqual(merge_verdict(-0.1, -0.3, 0.1, 6, -100), (False, None))

    def test_zero_n_is_no_merge(self):
        self.assertEqual(merge_verdict(0.3, 0.1, 0.5, 0, -50), (False, None))

    def test_weak_confidence_cost_flat_still_merges(self):
        # chars_delta == 0 is not a rise; the cost prong only reverts on chars_delta > 0.
        self.assertEqual(merge_verdict(0.1, -0.05, 0.25, 6, 0), (True, "weak"))


if __name__ == "__main__":
    unittest.main()
