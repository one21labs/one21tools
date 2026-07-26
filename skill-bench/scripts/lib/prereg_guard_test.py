#!/usr/bin/env python3
"""Decision-logic tests for prereg_guard. The fixtures are the ACTUAL drafts from 26-Jul-2026 --
a guard against self-favouring designs is worth nothing if it does not fire on the designs that
caused it."""
import os, sys, unittest

sys.path.insert(0, os.path.dirname(__file__))
import prereg_guard as pg  # noqa: E402


class TestPreregGuard(unittest.TestCase):
    def test_the_v3_draft_that_gave_ties_to_its_own_author_is_rejected(self):
        # Real numbers: 10 clusters, sd_hi 0.26, +/-0.05 equivalence margin awarding the tie to
        # `ours`. Half-width is 0.186 -- 3.7x the margin -- so the branch could never fire.
        problems = pg.check({"clusters": 10, "sd_hi": 0.26, "equivalence_margin": 0.05,
                             "author_arms": ["ours"], "losing_outcomes": ["ours"]})
        self.assertEqual(len(problems), 1)
        self.assertIn("UNREACHABLE", problems[0])
        self.assertIn("104", problems[0])  # the honest cost of the claim, in clusters

    def test_the_v2_draft_where_the_authors_arm_could_not_lose_is_rejected(self):
        # v2 cancelled the head-to-head: `ours` appeared only against `ours+mechanism`, so no
        # branch recorded it losing.
        problems = pg.check({"clusters": 10, "sd_hi": 0.26, "equivalence_margin": None,
                             "author_arms": ["ours"], "losing_outcomes": []})
        self.assertEqual(len(problems), 1)
        self.assertIn("NO", problems[0])
        self.assertIn("ours", problems[0])

    def test_a_design_that_states_a_reachable_margin_and_a_loss_path_passes(self):
        self.assertEqual(pg.check({"clusters": 104, "sd_hi": 0.26, "equivalence_margin": 0.05,
                                   "author_arms": ["ours"], "losing_outcomes": ["ours"]}), [])

    def test_omitting_the_numbers_fails_rather_than_passing_silently(self):
        # The cheapest way past a guard like this is to leave the field out.
        self.assertTrue(pg.check({"author_arms": [], "losing_outcomes": []}))
        self.assertTrue(any("author_arms unstated" in p
                            for p in pg.check({"clusters": 10, "sd_hi": 0.2})))

    def test_a_design_with_no_authored_arm_is_not_burdened(self):
        # Third-party vs bare: ordinary designer bias, already handled by blinding.
        self.assertEqual(pg.check({"clusters": 4, "sd_hi": 0.2, "author_arms": [],
                                   "losing_outcomes": []}), [])

    def test_the_t_table_has_one_home_and_agrees_with_it_at_every_df(self):
        # The copied table shipped missing df 21-24 and 26-29, falling back to 1.96 there — the
        # exact bug this guard exists downstream of — and the fixtures below never reached those
        # df, so it read green. Sweep EVERY df rather than sampling.
        import benchstats
        for df in range(1, 40):
            self.assertEqual(pg.t95(df), benchstats.t95(df), f"t95 disagrees at df={df}")

    def test_half_width_uses_the_small_cluster_t_not_the_normal(self):
        # With z=1.96 the v3 margin would look 21% closer to reachable than it is.
        self.assertAlmostEqual(pg.half_width(10, 0.26), 2.262 * 0.26 / (10 ** 0.5), places=6)
        self.assertEqual(pg.half_width(1, 0.2), float("inf"))

    def test_clusters_needed_reports_the_real_price_of_an_equivalence_claim(self):
        # 45, not the 46 first written here by hand: the hand computation stepped G by 2 and
        # overshot. The guard exists precisely because these numbers are not eyeballable.
        self.assertEqual(pg.clusters_needed(0.05, 0.17), 45)
        self.assertEqual(pg.clusters_needed(0.05, 0.26), 104)
        self.assertIsNone(pg.clusters_needed(0.001, 0.26))


if __name__ == "__main__":
    unittest.main()
