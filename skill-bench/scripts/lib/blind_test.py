#!/usr/bin/env python3
"""Decision-logic tests for blind.py (no gating plumbing without a test)."""
import json
import tempfile
import unittest
from pathlib import Path

from blind import assign_bids, write_blinded

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


if __name__ == "__main__":
    unittest.main()
