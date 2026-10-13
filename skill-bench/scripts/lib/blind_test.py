#!/usr/bin/env python3
"""Decision-logic tests for blind.py (no gating plumbing without a test)."""
import hashlib
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from blind import assign_bids, capture_symmetry, write_blinded

RECS = [{"cell": "T1-A-r1", "arm": "A", "response": "x"},
        {"cell": "T1-C-r1", "arm": "C", "response": "y"}]


class AssignBids(unittest.TestCase):
    def test_salted_ids_are_stable_per_salt_and_distinct(self):
        a = assign_bids(RECS, lambda r: r["cell"], salt="s")
        b = assign_bids(RECS, lambda r: r["cell"], salt="s")
        self.assertEqual([x[0] for x in a], [x[0] for x in b])
        self.assertNotEqual(a[0][0], a[1][0])
        self.assertEqual(len(a[0][0]), 12)

    def test_default_ids_cannot_be_recomputed_from_the_public_key(self):
        # The cell name carries the arm; an unsalted sha256 of it un-blinds every item offline.
        bid = assign_bids(RECS, lambda r: r["cell"])[0][0]
        self.assertNotEqual(bid, hashlib.sha256(b"T1-A-r1").hexdigest()[:12])
        self.assertNotEqual(bid, assign_bids(RECS, lambda r: r["cell"])[0][0])

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
            self.assertEqual([m["arm"] for m in arm_map], ["A", "C"])  # input order
            self.assertEqual({m["bid"] for m in arm_map},
                             {p.stem for p in items})
            self.assertEqual(os.listdir(d), ["items"])  # neither salt nor map beside the items

    def test_payload_keys_are_whitelisted(self):
        # A blacklist of "arm" alone let a renamed arm (or the arm-bearing cell name) through.
        for leak in (dict, lambda r: {"response": r["response"], "condition": r["arm"]},
                     lambda r: {"response": r["response"], "cell": r["cell"]}):
            with tempfile.TemporaryDirectory() as d:
                with self.assertRaises(ValueError):
                    write_blinded(RECS, d, lambda r: r["cell"], leak)

    def test_items_are_written_in_shuffled_order(self):
        recs = [{"cell": f"T1-{a}-r{i}", "arm": a, "response": "x"}
                for a in "AC" for i in range(20)]
        orders = set()
        for _ in range(3):
            with tempfile.TemporaryDirectory() as d:
                with patch("pathlib.Path.write_text", autospec=True) as w:
                    arm_map = write_blinded(recs, d, lambda r: r["cell"],
                                            lambda r: {"response": r["response"]})
                order = [c.args[0].stem for c in w.call_args_list]
                self.assertEqual(sorted(order), sorted(m["bid"] for m in arm_map))
                orders.add(tuple(order))
        self.assertNotIn(tuple(m["bid"] for m in arm_map), orders)

    def test_a_passed_salt_reproduces_the_bids(self):
        with tempfile.TemporaryDirectory() as d:
            a = write_blinded(RECS, d, lambda r: r["cell"], lambda r: {}, salt="s")
            b = write_blinded(RECS, d, lambda r: r["cell"], lambda r: {}, salt="s")
        self.assertEqual(a, b)


class BlindCellsTemplateRerun(unittest.TestCase):
    """templates/blind_cells.py re-run (the resumable path after regenerating ERROR cells) must
    keep every bid, or existing verdicts silently stop joining, and must leave no stale item."""

    def run_template(self, bench):
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "blind_cells", Path(__file__).resolve().parents[2] / "templates" / "blind_cells.py")
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        mod.HERE = Path(bench)
        with patch("sys.stdout"), patch("sys.stderr"):
            mod.main()
        return (Path(bench) / "arm_map.tsv").read_text(), \
            sorted(p.name for p in (Path(bench) / "graded" / "items").iterdir())

    def test_rerun_reproduces_the_same_bids_and_no_stale_items(self):
        with tempfile.TemporaryDirectory() as d:
            out = Path(d, "outputs")
            out.mkdir()
            for arm in "AC":
                out.joinpath(f"T1-{arm}.json").write_text(json.dumps(
                    {"cell": f"T1-{arm}-r1", "arm": arm, "scenario": "T1", "rep": 1,
                     "response": "a response long enough to pass the artifact check " * 2}))
            first = self.run_template(d)
            Path(d, "graded", "items", "stale.json").write_text("{}")
            Path(d, "graded", "error_cells.json").write_text('[{"cell": "T1-C-r1"}]')  # pre-regen
            second = self.run_template(d)
            self.assertEqual(first, second)
            self.assertEqual(json.loads(Path(d, "graded", "error_cells.json").read_text()), [])
            self.assertTrue(Path(d, "blind_salt.txt").exists())
            self.assertNotIn("blind_salt.txt", os.listdir(Path(d, "graded")))


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
        self.assertEqual(sweep["arms"]["P"]["excluded_n"], 1)
        self.assertEqual(sweep["arms"]["A"]["excluded_n"], 0)

    def test_any_exclusion_reason_counts_toward_skew(self):
        # Long replies excluded for other reasons (harness ERROR, failed artifact check, fake
        # tool-call markup) were invisible to an emptiness-only count.
        full = "a substantive decision artifact with plenty of text " * 2
        recs = self.recs("A", [full] * 4) + [{"arm": "C", "response": full, "err": i < 2}
                                             for i in range(4)]
        self.assertFalse(capture_symmetry(recs, lambda r: r["response"])["skewed"])
        sweep = capture_symmetry(recs, lambda r: r["response"], excluded_fn=lambda r: r.get("err"))
        self.assertTrue(sweep["skewed"])
        self.assertEqual(sweep["arms"]["C"]["excluded_rate"], 0.5)

    def test_symmetric_arms_do_not_flag(self):
        full = "a substantive decision artifact with plenty of text " * 2
        recs = self.recs("A", [full] * 3) + self.recs("C", [full] * 3)
        sweep = capture_symmetry(recs, lambda r: r["response"])
        self.assertFalse(sweep["skewed"])
        self.assertEqual({a["excluded_rate"] for a in sweep["arms"].values()}, {0.0})

    def test_median_len_and_counts(self):
        recs = self.recs("A", ["x" * 100, "x" * 200, "x" * 300])
        sweep = capture_symmetry(recs, lambda r: r["response"])
        self.assertEqual(sweep["arms"]["A"]["n"], 3)
        self.assertEqual(sweep["arms"]["A"]["median_len"], 200)


if __name__ == "__main__":
    unittest.main()
