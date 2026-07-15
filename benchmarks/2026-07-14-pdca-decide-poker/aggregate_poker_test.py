#!/usr/bin/env python3
"""Decision-logic tests for the verdict-bearing aggregation (bars, spreads, herding, split)."""
import unittest

import aggregate_poker as ag


def met(n_true):
    return {i: i <= n_true for i in (1, 2, 3, 4)}


def full_grid_met(p_score=4, c_score=4, a_score=2, reps=2):
    """met_by_bid + arm_map covering all 8 scenarios x 3 arms x reps (uniform scores).
    reps >= 2 so the outcome-spread bar is computable, as in the real grid."""
    met_by_bid, arm_map = {}, []
    for s in ag.SCENARIOS:
        for arm, score in (("P", p_score), ("C", c_score), ("A", a_score)):
            for rep in range(1, reps + 1):
                bid = f"{s}-{arm}-r{rep}"
                met_by_bid[bid] = met(score)
                arm_map.append({"bid": bid, "arm": arm, "scenario": s, "rep": str(rep)})
    return met_by_bid, arm_map


class MetricsFrom(unittest.TestCase):
    def test_fraction_and_hard_pair(self):
        m, amap = full_grid_met(p_score=3)  # exps 1-3 met, 4 not
        frac, hard = ag.metrics_from(m, amap)
        self.assertAlmostEqual(frac[("B1", "P")][0], 0.75)
        self.assertAlmostEqual(hard[("B1", "P")][0], 0.5)  # exp3 met, exp4 not

    def test_missing_bid_skipped(self):
        m, amap = full_grid_met()
        del m["B1-P-r1"], m["B1-P-r2"]
        frac, _ = ag.metrics_from(m, amap)
        self.assertNotIn(("B1", "P"), frac)


class OutcomeSpread(unittest.TestCase):
    def test_spread_across_reps(self):
        frac = {(s, "P"): [1.0, 0.5, 0.75] for s in ag.SCENARIOS}
        mean_spread, per = ag.outcome_spread(frac, "P")
        self.assertAlmostEqual(mean_spread, 0.5)
        self.assertAlmostEqual(per["B1"], 0.5)

    def test_single_rep_is_none(self):
        frac = {(s, "P"): [1.0] for s in ag.SCENARIOS}
        mean_spread, per = ag.outcome_spread(frac, "P")
        self.assertIsNone(mean_spread)
        self.assertIsNone(per["B1"])


class BarsOf(unittest.TestCase):
    def test_all_pass_when_p_matches_c_and_cheap(self):
        m, amap = full_grid_met(p_score=4, c_score=4)
        frac, hard = ag.metrics_from(m, amap)
        bars = ag.bars_of(frac, hard, {"P": 1.2, "C": 4.0})
        self.assertTrue(all(bars.values()), bars)

    def test_cost_bar_fails_over_70pct(self):
        m, amap = full_grid_met()
        frac, hard = ag.metrics_from(m, amap)
        bars = ag.bars_of(frac, hard, {"P": 3.0, "C": 4.0})
        self.assertFalse(bars["b_cost"])

    def test_quality_bar_fails_below_margin(self):
        # P misses exp 3+4 everywhere, C meets them: hard-pair delta -1.0
        m, amap = full_grid_met(p_score=2, c_score=4)
        frac, hard = ag.metrics_from(m, amap)
        bars = ag.bars_of(frac, hard, {"P": 1.2, "C": 4.0})
        self.assertFalse(bars["a_hard_pair_noninferior"])
        self.assertFalse(bars["d_full_noninferior"])

    def test_exact_margin_passes(self):
        # deltas of exactly -0.05 pass (>= per the frozen bar text) — build via mixed reps
        m, amap = full_grid_met(p_score=4, c_score=4)
        frac, hard = ag.metrics_from(m, amap)
        for s in ag.SCENARIOS:
            frac[(s, "P")] = [0.75]
            frac[(s, "C")] = [0.80]
            hard[(s, "P")] = [0.75]
            hard[(s, "C")] = [0.80]
        bars = ag.bars_of(frac, hard, {"P": 1.0, "C": 4.0})
        self.assertTrue(bars["a_hard_pair_noninferior"])
        self.assertTrue(bars["d_full_noninferior"])


class JudgeSplit(unittest.TestCase):
    def test_disagreement_is_not_met(self):
        opus = {"a": True, "b": True, "c": True, "d": True}
        grok = {"a": True, "b": True, "c": False, "d": True}
        split, eff = ag.judge_split(opus, grok)
        self.assertEqual(split, ["c"])
        self.assertFalse(eff["c"])
        self.assertTrue(eff["a"] and eff["b"] and eff["d"])

    def test_agreed_fail_stays_fail_no_split(self):
        opus = {"a": False}
        grok = {"a": False}
        split, eff = ag.judge_split(opus, grok)
        self.assertEqual(split, [])
        self.assertFalse(eff["a"])


class Herding(unittest.TestCase):
    def r(self, arm="P", divergent=("O1",), r1_scores=(5, 2, 3), deltas=(-2, 1, 0)):
        r1 = [{"O1": {"score": s, "crux": "x", "dependency": "y"}} for s in r1_scores]
        round2 = [{"advisor": k, "parsed": True, "deltas": {"O1": d}}
                  for k, d in enumerate(deltas)]
        return {"arm": arm, "summary": {"error": None},
                "poker": {"divergent": list(divergent), "round1": r1, "round2": round2}}

    def test_toward_mean_counting(self):
        # mean=10/3~3.33: advisor0 5->3 toward; advisor1 2->3 toward; advisor2 3->3 kept
        h = ag.herding_metrics([self.r()])
        self.assertEqual(h["toward_mean"], 2)
        self.assertEqual(h["kept"], 1)
        self.assertEqual(h["away_from_mean"], 0)
        self.assertEqual(h["fire_rate"], 1.0)

    def test_no_divergence_no_fire(self):
        h = ag.herding_metrics([self.r(divergent=())])
        self.assertEqual(h["round2_fired_cells"], 0)
        self.assertEqual(h["fire_rate"], 0.0)

    def test_non_p_and_error_cells_ignored(self):
        bad = self.r(arm="C")
        err = self.r()
        err["summary"]["error"] = "boom"
        h = ag.herding_metrics([bad, err])
        self.assertEqual(h["p_cells"], 0)


if __name__ == "__main__":
    unittest.main()
