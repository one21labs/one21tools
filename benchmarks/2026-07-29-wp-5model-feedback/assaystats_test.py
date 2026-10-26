#!/usr/bin/env python3
"""Decision-logic tests for assaystats.py.

The tail functions are checked against PUBLISHED critical values rather than another
implementation, because the whole point of hand-rolling them (stdlib-only constraint) is that
there is no scipy here to agree with.
"""
import unittest

import assaystats as S


class TestDistributions(unittest.TestCase):
    def test_betainc_symmetry_and_endpoints(self):
        self.assertAlmostEqual(S.betainc(0.5, 0.5, 0.5), 0.5, places=6)
        self.assertEqual(S.betainc(2, 3, 0.0), 0.0)
        self.assertEqual(S.betainc(2, 3, 1.0), 1.0)

    def test_t_tail_matches_published_critical_values(self):
        """t95 table entries must sit at p = 0.05 two-sided."""
        for df in (1, 2, 3, 4, 5, 10, 20, 30):
            self.assertAlmostEqual(S.t_two_sided_p(S.t95(df), df), 0.05, places=3,
                                   msg=f"df={df}")

    def test_t_tail_matches_one_sided_80_quantile(self):
        """t80 entries are the ONE-sided 80% quantile, i.e. two-sided p = 0.40."""
        for df in (4, 10, 20, 30):
            self.assertAlmostEqual(S.t_two_sided_p(S.t80(df), df), 0.40, places=3,
                                   msg=f"df={df}")

    def test_f_tail_matches_published_critical_values(self):
        """Published F(0.05) upper critical values."""
        for f, d1, d2 in ((2.866, 4, 20), (4.351, 1, 20), (3.098, 3, 20), (6.388, 4, 4),
                          (4.103, 2, 10), (2.901, 5, 15)):
            self.assertAlmostEqual(S.f_upper_p(f, d1, d2), 0.05, places=2,
                                   msg=f"F({d1},{d2})")

    def test_zero_and_infinite_statistics(self):
        self.assertAlmostEqual(S.t_two_sided_p(0.0, 10), 1.0, places=6)
        self.assertEqual(S.t_two_sided_p(float("inf"), 10), 0.0)
        self.assertEqual(S.f_upper_p(float("inf"), 4, 20), 0.0)


def _rows(spec):
    """spec: {(lane, arm): [scores]} -> flat graded rows."""
    return [{"lane": ln, "arm": a, "rep": i + 1, "score": v}
            for (ln, a), vals in spec.items() for i, v in enumerate(vals)]


class TestPooling(unittest.TestCase):
    def test_pooled_within_df_is_twenty_for_ten_cells_of_three(self):
        spec = {(ln, a): [0.5, 0.6, 0.7] for ln in "abcde" for a in ("bare", "wp")}
        _, df = S.pooled_within(S.cell_table(_rows(spec)))
        self.assertEqual(df, 20)

    def test_pooled_sd_recovers_known_value(self):
        spec = {("a", "bare"): [1.0, 2.0, 3.0], ("a", "wp"): [4.0, 5.0, 6.0]}
        s, df = S.pooled_within(S.cell_table(_rows(spec)))
        self.assertEqual(df, 4)
        self.assertAlmostEqual(s, 1.0, places=9)   # each cell has variance 1.0

    def test_zero_variance_cell_does_not_break_its_own_comparison(self):
        """THE degenerate case the July run produced in every cell: three identical reps.

        With its own df=4 variance this comparison is undefined; borrowing the pooled estimate
        from the other cells keeps it estimable, which is why model is a blocking factor here.
        """
        spec = {("flat", "bare"): [0.5, 0.5, 0.5], ("flat", "wp"): [0.7, 0.7, 0.7]}
        spec.update({(ln, a): [0.5, 0.55, 0.6] for ln in ("b", "c", "d") for a in ("bare", "wp")})
        eff = S.per_model_effects(S.cell_table(_rows(spec)))["flat"]
        self.assertAlmostEqual(eff["delta"], 0.2, places=6)
        self.assertEqual(eff["sd_control"], 0.0)
        self.assertIsNotNone(eff["ci95"][0], "pooled error term should keep the interval defined")
        self.assertIsNotNone(eff["mde80"])

    def test_no_variance_anywhere_yields_no_interval_not_infinite_significance(self):
        """If EVERY cell is flat there is genuinely no variance estimate. The honest output is
        'no interval', never a p-value of 0 implying infinite confidence."""
        spec = {(ln, a): [0.5, 0.5, 0.5] for ln in "abcde" for a in ("bare", "wp")}
        spec[("a", "wp")] = [0.9, 0.9, 0.9]
        eff = S.per_model_effects(S.cell_table(_rows(spec)))["a"]
        self.assertEqual(eff["ci95"], [None, None])
        self.assertIsNone(eff["p"])
        self.assertEqual(S.verdict(eff)["verdict"], "NO-INTERVAL")


class TestEffects(unittest.TestCase):
    def test_arm_main_effect_is_the_mean_of_per_model_deltas(self):
        spec = {}
        for i, ln in enumerate("abcde"):
            spec[(ln, "bare")] = [0.4, 0.5, 0.6]
            spec[(ln, "wp")] = [0.4 + i * 0.05, 0.5 + i * 0.05, 0.6 + i * 0.05]
        eff = S.arm_main_effect(S.cell_table(_rows(spec)))
        self.assertAlmostEqual(eff["delta"], 0.10, places=6)   # mean of 0,.05,.10,.15,.20
        self.assertEqual(eff["n_models"], 5)
        self.assertEqual(eff["df"], 20)

    def test_main_effect_is_better_powered_than_any_single_model(self):
        """The design's central claim: pooling across models detects a smaller effect than any
        one model's 3-vs-3 comparison can."""
        spec = {}
        for ln in "abcde":
            spec[(ln, "bare")] = [0.40, 0.50, 0.60]
            spec[(ln, "wp")] = [0.50, 0.60, 0.70]
        cells = S.cell_table(_rows(spec))
        main = S.arm_main_effect(cells)["mde80"]
        per = S.per_model_effects(cells)["a"]["mde80"]
        self.assertLess(main, per)
        # sqrt(2/15) / sqrt(2/3) = 0.4472. places=3 because both inputs are reported rounded.
        self.assertAlmostEqual(main / per, (2 / 15) ** 0.5 / (2 / 3) ** 0.5, places=3)

    def test_interaction_is_null_when_every_model_moves_alike(self):
        spec = {}
        for ln in "abcde":
            spec[(ln, "bare")] = [0.40, 0.50, 0.60]
            spec[(ln, "wp")] = [0.50, 0.60, 0.70]
        inter = S.interaction(S.cell_table(_rows(spec)))
        self.assertAlmostEqual(inter["F"], 0.0, places=6)
        self.assertAlmostEqual(inter["delta_spread"], 0.0, places=6)

    def test_interaction_fires_when_models_diverge(self):
        spec = {}
        for i, ln in enumerate("abcde"):
            spec[(ln, "bare")] = [0.50, 0.50, 0.50]
            spec[(ln, "wp")] = [0.50 + i * 0.10] * 3
        spec[("a", "bare")] = [0.48, 0.50, 0.52]     # inject a little error variance
        inter = S.interaction(S.cell_table(_rows(spec)))
        self.assertGreater(inter["F"], 4.0)
        self.assertLess(inter["p"], 0.05)
        self.assertAlmostEqual(inter["delta_spread"], 0.40, places=6)


class TestVerdict(unittest.TestCase):
    def _eff(self, delta, se, df=20):
        return S._interval(delta, se, df)

    def test_keep_requires_the_interval_to_clear_zero(self):
        self.assertEqual(S.verdict(self._eff(0.30, 0.05))["verdict"], "KEEP")

    def test_positive_point_estimate_alone_is_not_keep(self):
        """The rule this repo deleted: KEEP on mean>0 carried no error control at all."""
        self.assertEqual(S.verdict(self._eff(0.06, 0.05))["verdict"], "INCONCLUSIVE")

    def test_harmful_when_interval_is_wholly_negative(self):
        self.assertEqual(S.verdict(self._eff(-0.30, 0.05))["verdict"], "HARMFUL")

    def test_inconclusive_reason_states_what_was_detectable(self):
        why = S.verdict(self._eff(0.06, 0.05))["why"]
        self.assertIn("could only reliably detect", why)
        self.assertIn("does not establish its absence", why)

    def test_cut_needs_a_prereg_practical_bar_and_a_tight_interval(self):
        self.assertEqual(S.verdict(self._eff(0.0, 0.01), practical=0.10)["verdict"], "CUT")
        self.assertEqual(S.verdict(self._eff(0.0, 0.01))["verdict"], "INCONCLUSIVE")


class TestConsistency(unittest.TestCase):
    def test_reports_spread_per_cell(self):
        spec = {("a", "bare"): [0.4, 0.5, 0.9], ("a", "wp"): [0.6, 0.6, 0.6]}
        c = S.consistency(S.cell_table(_rows(spec)))
        self.assertAlmostEqual(c["a-bare"]["range"], 0.5, places=6)
        self.assertEqual(c["a-wp"]["sd"], 0.0)
        self.assertEqual(c["a-wp"]["range"], 0.0)


if __name__ == "__main__":
    unittest.main()
