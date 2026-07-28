#!/usr/bin/env python3
"""Decision-logic tests for the bench-verdict math + judge-divergence (CLAUDE.md: never ship a
process-gating script without a test of its decision logic). Pure/offline; no judge calls."""
import os, pathlib, sys, unittest

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

    def test_every_registered_judge_backend_is_reachable_from_both_CLIs(self):
        # A backend in judge.BACKENDS that argparse rejects is a backend nobody can use. Adding
        # `copilot` and `command` to the registry left both entry points' hard-coded choices
        # behind, so both were unreachable until a review caught it; the choices are now derived
        # from the registry and this test is what keeps them derived.
        import subprocess
        import judge
        here = os.path.dirname(os.path.abspath(__file__))
        for script in ("bench_verdict.py", "bench_skill.py"):
            for name in judge.BACKENDS:
                r = subprocess.run([sys.executable, os.path.join(here, script), "--judge", name],
                                   capture_output=True, text=True)
                self.assertNotIn("invalid choice", r.stderr,
                                 f"{script} rejects registered backend {name!r}")

    def test_ci_uses_the_small_cluster_t_multiplier_not_the_normal_one(self):
        # The interval width was never exercised: clustered_delta's construction had no test, and
        # keep_verdict's tests hand-fed synthetic ci95 dicts, so a flat 1.96 shipped unnoticed
        # across every benchmark this repo ran (all clustered on 4-6 evals, where 1.96 understates
        # the interval by 31-62%). Pin the multiplier at the cluster counts actually used.
        self.assertAlmostEqual(bs.t95(3), 3.182)    # G=4: 62% wider than 1.96
        self.assertAlmostEqual(bs.t95(5), 2.571)    # G=6: 31% wider
        self.assertAlmostEqual(bs.t95(30), 2.042)
        self.assertAlmostEqual(bs.t95(99), bs.Z95)  # beyond the table, t and z agree

    def test_ci_width_matches_a_hand_computed_four_cluster_interval(self):
        # Four clusters, control flat at 0.25, treatment 0.25/0.50/0.75/1.00 -> per-scenario
        # deltas 0.0, 0.25, 0.50, 0.75. mean 0.375, stdev 0.32275, se 0.16137.
        #   t(df=3) = 3.182 -> half-width 0.5135 -> CI [-0.138, 0.888], spans zero -> WEAK
        #   old z  = 1.960 -> half-width 0.3163 -> CI [ 0.059, 0.691], clears zero -> "STRONG"
        # Same data, opposite confidence label. This fixture is the regression itself.
        treatment = [[1, 0, 0, 0], [1, 1, 0, 0], [1, 1, 1, 0], [1, 1, 1, 1]]
        cells = []
        for i, t_met in enumerate(treatment):
            cells.append(cell(f"c{i}", "C", f"S{i}", t_met))
            cells.append(cell(f"b{i}", "B", f"S{i}", [1, 0, 0, 0]))
        d = bs.clustered_delta(cells, "C", "B")
        self.assertEqual(d["n_clusters"], 4)
        self.assertAlmostEqual(d["t_crit"], 3.182)
        self.assertAlmostEqual(d["mean"], 0.375)
        half = (d["ci95"][1] - d["ci95"][0]) / 2
        self.assertAlmostEqual(half, 0.5135, places=3)
        self.assertEqual(bs.keep_verdict(d)["verdict"], "INCONCLUSIVE")
        # And the old multiplier really would have said otherwise — not a hypothetical.
        self.assertGreater(d["mean"] - bs.Z95 * (half / d["t_crit"]), 0)

    def test_a_single_cluster_yields_no_interval_rather_than_a_fabricated_one(self):
        cells = [cell("c", "C", "S1", [1, 1, 1, 1]), cell("b", "B", "S1", [0, 0, 0, 0])]
        d = bs.clustered_delta(cells, "C", "B")
        self.assertEqual(d["n_clusters"], 1)
        self.assertNotEqual(d["ci95"][0], d["ci95"][0])  # NaN: one cluster carries no width
        self.assertEqual(bs.keep_verdict(d)["verdict"], "INCONCLUSIVE")
        self.assertIsNone(bs.keep_verdict(d)["half_width"])
        self.assertIsNone(bs.keep_verdict(d)["mde80"])

    def test_the_interval_decides_the_verdict_never_the_point_estimate(self):
        # The regression this replaces: KEEP on mean>0 alone fires about half the time under a
        # true null, so it carried no error control. Each case below returned KEEP before.
        clears = {"mean": 0.2, "ci95": [0.05, 0.35]}
        self.assertEqual(bs.keep_verdict(clears)["verdict"], "KEEP")
        for spans in ({"mean": 0.01, "ci95": [-0.15, 0.17], "n_clusters": 6},
                      {"mean": 0.20, "ci95": [-0.10, 0.50], "n_clusters": 6}):
            v = bs.keep_verdict(spans)
            self.assertEqual(v["verdict"], "INCONCLUSIVE")
            self.assertIn("reliably call a difference of", v["why"])
        # Without n_clusters no power figure is computable, and the message says so rather than
        # printing a number it cannot stand behind.
        bare = bs.keep_verdict({"mean": 0.01, "ci95": [-0.15, 0.17]})
        self.assertIsNone(bare["mde80"])
        self.assertIn("no stated power", bare["why"])
        below = {"mean": -0.3, "ci95": [-0.5, -0.1]}
        self.assertEqual(bs.keep_verdict(below)["verdict"], "HARMFUL")
        # A negative point estimate whose interval spans zero is NOT evidence of harm.
        self.assertEqual(bs.keep_verdict({"mean": -0.1, "ci95": [-0.3, 0.1]})["verdict"],
                         "INCONCLUSIVE")

    def test_half_width_and_mde80_are_reported_separately_because_they_differ(self):
        # A true effect equal to the half-width clears zero only ~half the time, so half-width is
        # a 50%-power figure and is NOT a minimum detectable effect. Reporting only it overstates
        # the design by ~40%. mde80 is the number an observed mean should be compared against.
        v = bs.keep_verdict({"mean": 0.01, "ci95": [-0.18, 0.20], "n_clusters": 6})
        self.assertAlmostEqual(v["half_width"], 0.19, places=3)
        self.assertGreater(v["mde80"], v["half_width"])
        self.assertAlmostEqual(v["mde80"] / v["half_width"], 1.36, places=1)
        self.assertLess(abs(v["mean"]), v["mde80"])        # underpowered, not "no effect"
        self.assertIn("reliably call", v["why"])

    def test_a_pre_registered_practical_bar_raises_the_verdict_above_bare_significance(self):
        # Owner requirement: "the effect size to be significant, so that the skill is CLEARLY
        # better". A real but trivial difference must not read KEEP against a bar of 0.10.
        trivial = {"mean": 0.06, "ci95": [0.02, 0.10]}      # significant, but small
        self.assertEqual(bs.keep_verdict(trivial)["verdict"], "KEEP")            # bar 0 (default)
        v = bs.keep_verdict(trivial, practical=0.10)
        self.assertEqual(v["verdict"], "INCONCLUSIVE")
        self.assertIn("practical bar", v["why"])
        self.assertEqual(v["practical"], 0.10)
        big = {"mean": 0.40, "ci95": [0.30, 0.50]}
        self.assertEqual(bs.keep_verdict(big, practical=0.10)["verdict"], "KEEP")

    def test_win_rate_catches_a_mean_carried_by_one_scenario(self):
        # Owner requirement: "clearly better, MOST OF THE TIME". One huge win plus three losses
        # can clear the bar on the mean while losing 75% of scenarios.
        lopsided = {"mean": 0.2, "ci95": [0.05, 0.35],
                    "per_scenario": {"S1": 1.0, "S2": -0.1, "S3": -0.1, "S4": -0.1}}
        v = bs.keep_verdict(lopsided)
        self.assertEqual(v["verdict"], "KEEP")
        self.assertEqual(v["win_rate"], 0.25)
        consistent = {"mean": 0.2, "ci95": [0.05, 0.35],
                      "per_scenario": {"S1": 0.2, "S2": 0.25, "S3": 0.15, "S4": 0.2}}
        self.assertEqual(bs.keep_verdict(consistent)["win_rate"], 1.0)
        # Same verdict either way, and NO warning threshold: over 6-8 scenarios win_rate is a
        # coin-flip count with no interval, so any cutoff would be exactly the arbitrary constant
        # this rule was written to delete. It is a prompt to read attribution, not a criterion.
        self.assertEqual(bs.keep_verdict(consistent)["verdict"], "KEEP")
        self.assertNotIn("why", v)

    def test_the_published_sizing_table_matches_what_clusters_for_actually_returns(self):
        # references/pre-registration.md prints a scenario-count table at sd=0.24. Nothing tied
        # the table to the function, so a constant change would have silently rotted it (advisory
        # review, PR #318). This is that tie: change clusters_for and this fails, not the doc.
        sd = 0.24
        for target, at80, at50 in ((0.40, 5, 4), (0.25, 10, 7), (0.15, 23, 13),
                                   (0.10, 46, 25), (0.05, 181, 89)):
            self.assertEqual(bs.clusters_for(sd, target), at80, f"80% row for {target}")
            self.assertEqual(bs.clusters_for(sd, target, power=0.50), at50, f"50% row for {target}")

    def test_the_t_tables_have_no_gaps_that_silently_fall_back_to_the_asymptote(self):
        # A sparse table serves the asymptote on its gaps. Both quantile families DECREASE toward
        # it, so every gap under-states the multiplier: t95's gap widens no interval, t80's gap
        # relaxes clusters_for and returns fewer scenarios than the requested power needs. That
        # was live until 2026-07-27 — _T80 skipped df 11,13,14,16-19,21-24,26-29 and the published
        # 0.15 row read 22 where df=21 gives 23. Monotonicity is what proves no gap remains.
        for df in range(1, 30):
            self.assertGreaterEqual(bs.t80(df), bs.t80(df + 1), f"t80 not decreasing at df={df}")
            self.assertGreaterEqual(bs.t95(df), bs.t95(df + 1), f"t95 not decreasing at df={df}")
        self.assertGreater(bs.t80(30), bs.Z80)     # still above the asymptote at the table's end
        self.assertGreater(bs.t95(30), bs.Z95)
        self.assertEqual(bs.t80(99), bs.Z80)       # beyond the table, the asymptote is correct
        self.assertEqual(bs.t95(99), bs.Z95)

    def test_the_published_verdict_table_matches_what_keep_verdict_can_emit(self):
        # cost-and-verdict.md reproduces the verdict table on purpose (it is the contract a reader
        # checks a result against). A self-granted restatement exception needs a guard or it rots
        # silently on the next threshold change (advisory review, PR #318). This is that guard:
        # the doc's verdict vocabulary must be exactly what the implementation can produce.
        doc = (pathlib.Path(__file__).resolve().parents[1]
               / "skills/bench/references/cost-and-verdict.md").read_text(encoding="utf8")
        emitted = {
            bs.keep_verdict({"mean": 0.3, "ci95": [0.1, 0.5], "n_clusters": 6})["verdict"],
            bs.keep_verdict({"mean": -0.3, "ci95": [-0.5, -0.1], "n_clusters": 6})["verdict"],
            bs.keep_verdict({"mean": 0.01, "ci95": [-0.04, 0.06], "n_clusters": 6},
                            practical=0.10)["verdict"],
            bs.keep_verdict({"mean": 0.01, "ci95": [-0.3, 0.32], "n_clusters": 6})["verdict"],
        }
        self.assertEqual(emitted, {"KEEP", "HARMFUL", "CUT", "INCONCLUSIVE"})
        for word in emitted:
            self.assertIn(f"| {word} |", doc, f"{word} is emitted but absent from the doc table")
        # And nothing the doc names can be unreachable: NO-DATA is emitted but is an error state,
        # not a verdict row, so the table must not claim it.
        self.assertNotIn("| NO-DATA |", doc)
        self.assertNotIn("CUT-CANDIDATE", doc.split("## Reading it honestly")[0])

    def test_cut_requires_an_equivalence_result_not_a_point_estimate_near_zero(self):
        # The only honest route to "this skill is not worth keeping": the whole interval inside
        # the practical band, so the data SUPPORT no-difference rather than failing to find one.
        tight_null = {"mean": 0.01, "ci95": [-0.04, 0.06]}
        self.assertEqual(bs.keep_verdict(tight_null, practical=0.10)["verdict"], "CUT")
        # Same point estimate, wide interval: underpowered, NOT equivalent. This is the exact
        # pair the deleted rule could not tell apart.
        wide_null = {"mean": 0.01, "ci95": [-0.30, 0.32]}
        self.assertEqual(bs.keep_verdict(wide_null, practical=0.10)["verdict"], "INCONCLUSIVE")
        # Unreachable without a bar: nothing is provably smaller than nothing.
        self.assertEqual(bs.keep_verdict(tight_null)["verdict"], "INCONCLUSIVE")

    def test_clusters_for_sizes_a_run_from_a_measured_prior(self):
        # sd_between recovers the spread from a completed run; clusters_for turns it into the
        # scenario count the next run needs. Both halves of "power the design" (ADR 0065).
        done = {"mean": 0.438, "ci95": [0.186, 0.690], "n_clusters": 6}
        sd = bs.sd_between(done)
        self.assertAlmostEqual(sd, 0.240, places=2)
        # Default is 80% power. Sizing at 50% (target == half-width) roughly HALVES the answer,
        # which is the under-sizing a cross-family review caught: such a design succeeds on a
        # coin flip. Both are available; the honest default is the one that works.
        self.assertGreater(bs.clusters_for(sd, 0.25), bs.clusters_for(sd, 0.25, power=0.50))
        self.assertGreaterEqual(bs.clusters_for(sd, 0.25, power=0.50) * 2,
                                bs.clusters_for(sd, 0.25) - 2)
        self.assertGreater(bs.clusters_for(sd, 0.05), 100)     # a small effect stays expensive
        self.assertIsNone(bs.clusters_for(sd, 0.0))            # no target -> no answer
        self.assertIsNone(bs.clusters_for(float("nan"), 0.1))  # no prior -> no answer
        # An unsupported power level is REFUSED, never silently served another level's answer:
        # power=0.90 once returned 0.80's count, mis-sizing a study inside the sizing function.
        for bad in (0.90, 0.65, 0.95, 0):
            with self.assertRaises(ValueError):
                bs.clusters_for(sd, 0.1, power=bad)
        self.assertNotEqual(bs.sd_between({"ci95": [float("nan")] * 2, "n_clusters": 1}),
                            bs.sd_between({"ci95": [float("nan")] * 2, "n_clusters": 1}))  # NaN

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
        # The load-bearing #172 finding: null under one judge, positive under another. This used
        # ONE scenario until 2026-07-27, so the "flip" it proved was two point estimates with no
        # interval between them — the diagnostic demonstrating itself on data that can support no
        # verdict. Six scenarios, so judge B genuinely clears and judge A genuinely does not.
        cl, gk = [], []
        for i in range(6):
            cl += [cell(f"c{i}", "C", f"S{i}", [1, 0, 0, 0]), cell(f"b{i}", "B", f"S{i}", [1, 0, 0, 0])]
            gk += [cell(f"c{i}", "C", f"S{i}", [1, 1, 1, 0]), cell(f"b{i}", "B", f"S{i}", [1, 0, 0, 0])]
        flip = bs.verdict_flip(bs.clustered_delta(cl, "C", "B"), bs.clustered_delta(gk, "C", "B"))
        self.assertTrue(flip["flipped"])
        self.assertEqual(flip["judge_a_verdict"], "INCONCLUSIVE")   # a flat null: no interval width
        self.assertEqual(flip["judge_b_verdict"], "KEEP")           # +0.5 every scenario

    def test_summarize_generalizes_to_any_arm_pair(self):
        # --primary D,C (#180 arm-D grid): arm means infer from the cells, delta keys follow the pair
        import bench_verdict as bv
        cells = [cell("d1", "D", "S1", [1, 1, 1, 1]), cell("c1", "C", "S1", [1, 1, 0, 0]),
                 cell("a1", "A", "S1", [1, 0, 0, 0])]
        s = bv.summarize(cells, "D", "C")
        self.assertEqual(set(s["arm_means"]), {"A", "C", "D"})
        self.assertIn("D_minus_C", s)
        self.assertIn("D_minus_A", s)
        self.assertAlmostEqual(s["D_minus_C"]["mean"], 0.5)


class TestTopCellAttribution(unittest.TestCase):
    # #191 item 3: a bar read must not rest on a handful of (possibly infrastructure-broken) cells.
    def test_zero_cell_that_carries_the_delta_flags_inspect(self):
        # The #185 shape: arms tie everywhere except one zero-scored capture failure in P,
        # which single-handedly manufactures the whole C-P gap.
        cells = ([cell(f"c{s}{r}", "C", f"S{s}", [1, 1, 0, 0]) for s in (1, 2) for r in (1, 2, 3)]
                 + [cell("p11", "P", "S1", [1, 1, 0, 0]), cell("p12", "P", "S1", [1, 1, 0, 0]),
                    cell("p1z", "P", "S1", [0, 0, 0, 0])]   # capture failure graded as quality 0
                 + [cell(f"p2{r}", "P", "S2", [1, 1, 0, 0]) for r in (1, 2, 3)])
        attr = bs.top_cell_attribution(cells, "C", "P", top_n=2)
        self.assertTrue(attr["inspect"])
        self.assertEqual(attr["top"][0]["bid"], "p1z")
        self.assertTrue(attr["top"][0]["flips_or_halves"])

    def test_balanced_cells_do_not_flag(self):
        cells = [cell("c1", "C", "S1", [1, 1, 1, 0]), cell("c2", "C", "S2", [1, 1, 1, 0]),
                 cell("c3", "C", "S3", [1, 1, 1, 0]), cell("c4", "C", "S4", [1, 1, 1, 0]),
                 cell("b1", "B", "S1", [1, 1, 0, 0]), cell("b2", "B", "S2", [1, 1, 0, 0]),
                 cell("b3", "B", "S3", [1, 1, 0, 0]), cell("b4", "B", "S4", [1, 1, 0, 0])]
        attr = bs.top_cell_attribution(cells, "C", "B")
        self.assertAlmostEqual(attr["base_mean"], 0.25)
        self.assertFalse(attr["inspect"])

    def test_other_arms_excluded_and_top_n_respected(self):
        cells = [cell("c1", "C", "S1", [1, 1, 1, 1]), cell("b1", "B", "S1", [1, 0, 0, 0]),
                 cell("c2", "C", "S2", [1, 1, 1, 1]), cell("b2", "B", "S2", [1, 0, 0, 0]),
                 cell("a1", "A", "S1", [0, 0, 0, 0])]
        attr = bs.top_cell_attribution(cells, "C", "B", top_n=2)
        self.assertEqual(len(attr["top"]), 2)
        self.assertNotIn("a1", [r["bid"] for r in attr["top"]])


if __name__ == "__main__":
    unittest.main()
