#!/usr/bin/env python3
"""Decision-logic tests for blind.py (no gating plumbing without a test)."""
import json
import tempfile
import unittest
from pathlib import Path

from blind import assign_bids, capture_symmetry, write_blinded

RECS = [{"cell": "T1-A-r1", "arm": "A", "response": "x"},
        {"cell": "T1-C-r1", "arm": "C", "response": "y"}]


class AssignBids(unittest.TestCase):
    def test_deterministic_and_distinct(self):
        a = assign_bids(RECS, lambda r: r["cell"])
        b = assign_bids(RECS, lambda r: r["cell"])
        self.assertEqual([x[0] for x in a], [x[0] for x in b])
        self.assertNotEqual(a[0][0], a[1][0])
        self.assertEqual(len(a[0][0]), 12)

    def test_collision_raises(self):
        with self.assertRaises(ValueError):
            assign_bids(RECS, lambda r: "same-key")


class WriteBlinded(unittest.TestCase):
    def test_items_carry_no_arm_and_map_joins_back(self):
        with tempfile.TemporaryDirectory() as d:
            arm_map = write_blinded(RECS, d, lambda r: r["cell"],
                                    lambda r: {"response": r["response"]})
            items = sorted(Path(d, "items").glob("*.json"))
            self.assertEqual(len(items), 2)
            for p in items:
                self.assertNotIn("arm", json.loads(p.read_text()))
            self.assertEqual({m["arm"] for m in arm_map}, {"A", "C"})
            self.assertEqual({m["bid"] for m in arm_map},
                             {p.stem for p in items})

    def test_payload_leaking_arm_raises(self):
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaises(ValueError):
                write_blinded(RECS, d, lambda r: r["cell"], lambda r: dict(r))


class CaptureSymmetry(unittest.TestCase):
    def recs(self, arm, texts):
        return [{"arm": arm, "response": t} for t in texts]

    def test_arm_skewed_emptiness_flags(self):
        # The #185 shape: one arm drops captures, the others don't.
        full = "a substantive decision artifact with plenty of text " * 2
        recs = (self.recs("A", [full] * 4) + self.recs("C", [full] * 4)
                + self.recs("P", [full, full, full, ""]))
        sweep = capture_symmetry(recs, lambda r: r["response"])
        self.assertTrue(sweep["skewed"])
        self.assertEqual(sweep["arms"]["P"]["empty_n"], 1)
        self.assertEqual(sweep["arms"]["A"]["empty_n"], 0)

    def test_symmetric_arms_do_not_flag(self):
        full = "a substantive decision artifact with plenty of text " * 2
        recs = self.recs("A", [full] * 3) + self.recs("C", [full] * 3)
        sweep = capture_symmetry(recs, lambda r: r["response"])
        self.assertFalse(sweep["skewed"])
        self.assertEqual({a["empty_rate"] for a in sweep["arms"].values()}, {0.0})

    def test_median_len_and_counts(self):
        recs = self.recs("A", ["x" * 100, "x" * 200, "x" * 300])
        sweep = capture_symmetry(recs, lambda r: r["response"])
        self.assertEqual(sweep["arms"]["A"]["n"], 3)
        self.assertEqual(sweep["arms"]["A"]["median_len"], 200)


if __name__ == "__main__":
    unittest.main()
