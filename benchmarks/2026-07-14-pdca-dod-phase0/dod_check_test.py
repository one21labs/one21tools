#!/usr/bin/env python3
"""Decision-logic tests for the frozen Phase-0 predicates and verdict machinery."""
import unittest

import dod_check as d


class Item3Criterion(unittest.TestCase):
    def test_empty_fails(self):
        self.assertFalse(d.item3_criterion(""))
        self.assertFalse(d.item3_criterion(None))

    def test_vague_prose_fails(self):
        self.assertFalse(d.item3_criterion("We should monitor the situation closely."))

    def test_threshold_passes(self):
        self.assertTrue(d.item3_criterion("Adopt if error rate stays under 2% for 30 days."))

    def test_conditional_passes(self):
        self.assertTrue(d.item3_criterion("Reopen when a second incident of this class lands."))

    def test_comparator_passes(self):
        self.assertTrue(d.item3_criterion("Keep while p95 latency <= baseline."))


class Item4Rejected(unittest.TestCase):
    def test_no_options_fails(self):
        self.assertFalse(d.item4_rejected([]))
        self.assertFalse(d.item4_rejected(None))

    def test_unmarked_options_fail(self):
        self.assertFalse(d.item4_rejected(["Option A: migrate now", "Option B: wait"]))

    def test_bare_reject_marker_fails(self):
        self.assertFalse(d.item4_rejected(["REJECTED: B"]))

    def test_rejected_with_reason_passes(self):
        self.assertTrue(d.item4_rejected(
            ["REJECTED: full rewrite — costs a quarter and freezes feature work"]))

    def test_lowercase_inline_reject_passes(self):
        self.assertTrue(d.item4_rejected(
            ["We rejected the vendor option because the contract lock-in exceeds two years"]))


def cells(*specs):
    """spec: (dod_pass, fm, excluded=False)"""
    out = []
    for s in specs:
        p, fm = s[0], s[1]
        out.append({"dod_pass": p, "fm_full": fm, "fm_hard": fm,
                    "excluded": s[2] if len(s) > 2 else False})
    return out


class BucketArm(unittest.TestCase):
    def test_tested_delta(self):
        cs = cells(*[(True, 0.9)] * 6, *[(False, 0.5)] * 6)
        r = d.bucket_arm(cs)
        self.assertEqual(r["state"], "TESTED")
        self.assertAlmostEqual(r["delta"], 0.4)

    def test_thin_bucket_inconclusive(self):
        cs = cells(*[(True, 0.9)] * 20, *[(False, 0.5)] * 4)
        self.assertEqual(d.bucket_arm(cs)["state"], "INCONCLUSIVE")

    def test_skew_inconclusive(self):
        # 46 pass / 5 fail: both buckets >= 5 but share > 0.90
        cs = cells(*[(True, 0.9)] * 46, *[(False, 0.5)] * 5)
        self.assertEqual(d.bucket_arm(cs)["state"], "INCONCLUSIVE")

    def test_excluded_cells_leave_buckets(self):
        cs = cells(*[(True, 0.9)] * 6, *[(False, 0.5)] * 6, *[(None, 0.7, True)] * 3)
        r = d.bucket_arm(cs)
        self.assertEqual(r["excluded"], 3)
        self.assertEqual(r["n_pass"], 6)

    def test_all_excluded_inconclusive(self):
        cs = cells(*[(None, 0.7, True)] * 4)
        self.assertEqual(d.bucket_arm(cs)["state"], "INCONCLUSIVE")


class Verdicts(unittest.TestCase):
    T = {"state": "TESTED"}

    def test_any_tested_below_threshold_falsifies_corpus(self):
        arms = {"A": dict(self.T, delta=0.30), "C": dict(self.T, delta=0.10)}
        self.assertEqual(d.corpus_verdict(arms), "FALSIFYING")

    def test_all_tested_at_threshold_supports(self):
        arms = {"A": dict(self.T, delta=0.15), "C": dict(self.T, delta=0.40)}
        self.assertEqual(d.corpus_verdict(arms), "SUPPORTED")

    def test_no_tested_arm_inconclusive(self):
        arms = {"A": {"state": "INCONCLUSIVE", "delta": None}}
        self.assertEqual(d.corpus_verdict(arms), "INCONCLUSIVE")

    def test_inconclusive_arm_does_not_veto_tested(self):
        arms = {"A": dict(self.T, delta=0.20), "C": {"state": "INCONCLUSIVE", "delta": None}}
        self.assertEqual(d.corpus_verdict(arms), "SUPPORTED")

    def test_h1_falsified_by_either_corpus(self):
        self.assertEqual(d.h1_verdict({"a": "SUPPORTED", "b": "FALSIFYING"}), "FALSIFIED")

    def test_h1_supported_needs_both(self):
        self.assertEqual(d.h1_verdict({"a": "SUPPORTED", "b": "SUPPORTED"}), "SUPPORTED")
        self.assertEqual(d.h1_verdict({"a": "SUPPORTED", "b": "INCONCLUSIVE"}), "INCONCLUSIVE")


class CellDod(unittest.TestCase):
    def test_all_four_required(self):
        rec = {"item3": True, "item4": True,
               "classifier": {"claude": {"item1": True, "item2": True}}}
        self.assertTrue(d.cell_dod(rec, "claude"))
        rec["item4"] = False
        self.assertFalse(d.cell_dod(rec, "claude"))
        rec["item4"] = True
        rec["classifier"]["claude"]["item2"] = False
        self.assertFalse(d.cell_dod(rec, "claude"))


if __name__ == "__main__":
    unittest.main()
