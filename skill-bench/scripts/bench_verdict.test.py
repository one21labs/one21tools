#!/usr/bin/env python3
"""Decision-logic tests for the bench-verdict math + judge-divergence (CLAUDE.md: never ship a
process-gating script without a test of its decision logic). Pure/offline; no judge calls."""
import os, sys, unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "lib"))
import benchstats as bs  # noqa: E402


def cell(bid, arm, scn, m):
    return {"bid": bid, "arm": arm, "scenario": scn, "met": dict(zip((1, 2, 3, 4), m))}


class TestVerdictMath(unittest.TestCase):
    def test_fraction_and_arm_mean(self):
        cells = [cell("a", "C", "S1", [1, 1, 0, 0]), cell("b", "C", "S2", [1, 1, 1, 1])]
        self.assertEqual(bs.fraction_met(cells[0]["met"]), 0.5)
        self.assertEqual(bs.arm_mean(cells, "C"), 0.75)

    def test_clustered_delta_is_mean_of_per_scenario(self):
        cells = [cell("c1", "C", "S1", [1, 1, 1, 1]), cell("b1", "B", "S1", [1, 1, 0, 0]),
                 cell("c2", "C", "S2", [1, 0, 0, 0]), cell("b2", "B", "S2", [1, 1, 1, 0])]
        d = bs.clustered_delta(cells, "C", "B")
        self.assertEqual(d["per_scenario"]["S1"], 0.5)   # 1.0 - 0.5
        self.assertEqual(d["per_scenario"]["S2"], -0.5)  # 0.25 - 0.75
        self.assertEqual(d["mean"], 0.0)
        self.assertEqual(d["n_clusters"], 2)

    def test_keep_verdict_direction_and_confidence(self):
        pos = {"mean": 0.2, "ci95": [0.05, 0.35]}
        self.assertEqual(bs.keep_verdict(pos)["verdict"], "KEEP")
        self.assertEqual(bs.keep_verdict(pos)["confidence"], "strong")  # CI clears zero
        weak = {"mean": 0.01, "ci95": [-0.15, 0.17]}
        self.assertEqual(bs.keep_verdict(weak)["verdict"], "KEEP")
        self.assertEqual(bs.keep_verdict(weak)["confidence"], "weak")   # CI spans zero
        neg = {"mean": -0.1, "ci95": [-0.3, 0.1]}
        self.assertEqual(bs.keep_verdict(neg)["verdict"], "CUT-CANDIDATE")

    def test_divergence_counts_and_kappa(self):
        base = [cell("x", "C", "S1", [1, 1, 1, 1]), cell("y", "B", "S1", [1, 1, 1, 1])]
        strict = [cell("x", "C", "S1", [1, 1, 0, 0]), cell("y", "B", "S1", [1, 0, 0, 0])]
        dv = bs.divergence(base, strict, "base", "grok")
        self.assertEqual(dv["n"], 8)
        self.assertEqual(dv["base_stricter_n"], 0)    # baseline never stricter than the strict judge
        self.assertEqual(dv["grok_stricter_n"], 5)    # 5 met->unmet
        self.assertEqual(dv["base_met_rate"], 1.0)
        self.assertEqual(dv["grok_met_rate"], 0.375)

    def test_verdict_flip_detects_direction_change(self):
        # The load-bearing #172 finding: null under one judge, positive under another.
        cl = [cell("c", "C", "S1", [1, 0, 0, 0]), cell("b", "B", "S1", [1, 0, 0, 0])]   # C-B = 0
        gk = [cell("c", "C", "S1", [1, 1, 1, 0]), cell("b", "B", "S1", [1, 0, 0, 0])]   # C-B = +0.5
        flip = bs.verdict_flip(bs.clustered_delta(cl, "C", "B"), bs.clustered_delta(gk, "C", "B"))
        self.assertTrue(flip["flipped"])
        self.assertEqual(flip["judge_a_verdict"], "CUT-CANDIDATE")
        self.assertEqual(flip["judge_b_verdict"], "KEEP")


if __name__ == "__main__":
    unittest.main()
