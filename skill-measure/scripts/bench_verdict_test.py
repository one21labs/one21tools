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
            gk += [cell(f"c{i}", "C", f"S{i}", [1, 1, 1, i % 2]), cell(f"b{i}", "B", f"S{i}", [1, 0, 0, 0])]
        flip = bs.verdict_flip(bs.clustered_delta(cl, "C", "B"), bs.clustered_delta(gk, "C", "B"))
        self.assertTrue(flip["flipped"])
        self.assertEqual(flip["judge_a_verdict"], "INCONCLUSIVE")   # a flat null: no interval width
        self.assertEqual(flip["judge_b_verdict"], "KEEP")           # +0.5/+0.75 alternating

    def test_summarize_generalizes_to_any_arm_pair(self):
        # --primary D,C (#180 arm-D grid): arm means infer from the cells, delta keys follow the pair
        import bench_verdict as bv
        cells = [cell("d1", "D", "S1", [1, 1, 1, 1]), cell("c1", "C", "S1", [1, 1, 0, 0]),
                 cell("a1", "A", "S1", [1, 0, 0, 0])]
        s = bv.summarize(cells, "D", "C")
        self.assertEqual(set(s["arm_means"]), {"C", "D"})  # the verdict pair, matched scenarios
        self.assertIn("D_minus_C", s)
        self.assertNotIn("D_minus_A", s)  # only the verdict pair's delta is reported
        self.assertAlmostEqual(s["D_minus_C"]["mean"], 0.5)

    def test_a_control_arm_A_keeps_its_verdict(self):
        # Round 4: with --primary C,A a legacy bare-mean f"{x}_minus_A" key overwrote the verdict.
        import bench_verdict as bv
        cells = [cell("c1", "C", "S1", [1, 1, 1, 1]), cell("a1", "A", "S1", [1, 0, 0, 0])]
        self.assertIn("verdict", bv.summarize(cells, "C", "A")["C_minus_A"])


class TestBenchstatsBoundaries(unittest.TestCase):
    # Each assert pins a boundary a mutant once survived every suite on (2026-10 stats audit).
    def test_identical_cluster_deltas_keep_the_verdict_but_drop_the_power_figure(self):
        cells = [c for i in range(6) for c in (cell(f"c{i}", "C", f"S{i}", [1, 1, 1, 0]),
                                                cell(f"b{i}", "B", f"S{i}", [1, 0, 0, 0]))]
        v = bs.keep_verdict(bs.clustered_delta(cells, "C", "B"))
        self.assertEqual(v["verdict"], "KEEP")
        self.assertIsNone(v["mde80"])
        self.assertIn("zero", v["spread"])

    def test_verdict_is_monotone_as_one_identical_delta_grows(self):
        # A refusal at zero spread made more consistent evidence read weaker (round 3).
        same = [c for i in range(4) for c in (cell(f"c{i}", "C", f"S{i}", [1, 1, 0, 0]),
                                               cell(f"b{i}", "B", f"S{i}", [1, 0, 0, 0]))]
        bigger = same[:-2] + [cell("c3", "C", "S3", [1, 1, 1, 0]), cell("b3", "B", "S3", [1, 0, 0, 0])]
        self.assertEqual(bs.keep_verdict(bs.clustered_delta(same, "C", "B"))["verdict"], "KEEP")
        self.assertEqual(bs.keep_verdict(bs.clustered_delta(bigger, "C", "B"))["verdict"], "KEEP")

    def test_one_arm_scenarios_are_named_not_silently_dropped(self):
        cells = [cell("c1", "C", "S1", [1, 1, 0, 0]), cell("b1", "B", "S1", [1, 0, 0, 0]),
                 cell("c2", "C", "S2", [1, 1, 1, 0]), cell("b2", "B", "S2", [1, 0, 0, 0]),
                 cell("c3", "C", "S3", [1, 1, 1, 1]), cell("a3", "A", "S4", [0, 0, 0, 0])]
        d = bs.clustered_delta(cells, "C", "B")
        self.assertEqual(d["dropped_scenarios"], ["S3"])   # S4 carries neither arm: not dropped
        self.assertEqual(bs.keep_verdict(d)["dropped_scenarios"], ["S3"])
        full = [c for c in cells if c["scenario"] != "S3"]
        self.assertNotIn("dropped_scenarios", bs.keep_verdict(bs.clustered_delta(full, "C", "B")))

    def test_reported_arm_means_subtract_to_the_delta(self):
        # S1 has 3 C reps, S2 one: the all-cells arm_mean weighs S1 thrice and misses the delta.
        cells = ([cell(f"c1{r}", "C", "S1", [1, 1, 1, 1]) for r in range(3)]
                 + [cell("c2", "C", "S2", [1, 0, 0, 0]), cell("b1", "B", "S1", [1, 1, 0, 0]),
                    cell("b2", "B", "S2", [1, 1, 0, 0]), cell("c3", "C", "S3", [0, 0, 0, 0])])
        d = bs.clustered_delta(cells, "C", "B")
        self.assertAlmostEqual(d["arm_means"]["C"] - d["arm_means"]["B"], d["mean"])
        self.assertNotAlmostEqual(bs.arm_mean(cells, "C") - bs.arm_mean(cells, "B"), d["mean"])

    def test_verdict_boundaries(self):
        kv = lambda lo, hi, p=0.0: bs.keep_verdict(
            {"mean": (lo + hi) / 2, "ci95": [lo, hi], "n_clusters": 6}, p)["verdict"]
        self.assertEqual(kv(-0.20, -0.01), "HARMFUL")       # any upper bound below zero
        self.assertEqual(kv(-0.20, 0.0), "INCONCLUSIVE")    # touching zero is not clear of it
        self.assertEqual(kv(0.0, 0.40), "INCONCLUSIVE")     # lower bound must EXCEED the bar
        self.assertEqual(kv(0.10, 0.40, 0.10), "INCONCLUSIVE")
        self.assertEqual(kv(-0.50, 0.05, 0.10), "INCONCLUSIVE")  # lo outside the band: no CUT
        self.assertEqual(kv(-0.05, 0.05, 0.10), "CUT")
        v = bs.keep_verdict({"mean": 0.1, "ci95": [-0.1, 0.3], "n_clusters": 6})
        self.assertAlmostEqual(v["mde80"], (bs.t95(5) + bs.t80(5)) * 0.2 / bs.t95(5), places=3)

    def test_a_tied_scenario_is_not_a_win(self):
        d = {"mean": 0.1, "ci95": [0.05, 0.15], "per_scenario": {"S1": 0.0, "S2": 0.2}}
        self.assertEqual(bs.keep_verdict(d)["win_rate"], 0.5)

    def test_per_expectation_is_the_met_rate_per_arm(self):
        cells = [cell("c1", "C", "S1", [1, 1, 0, 0]), cell("c2", "C", "S2", [1, 0, 0, 0]),
                 cell("b1", "B", "S1", [0, 0, 0, 1])]
        pe = bs.per_expectation(cells)
        self.assertEqual(pe[1], {"B": 0, "C": 1})
        self.assertEqual(pe[2]["C"], 0.5)
        self.assertEqual(pe[4], {"B": 1, "C": 0})

    def test_divergence_counts_strictness_in_the_right_direction_and_kappa_at_full_agreement(self):
        lax = [cell("x", "C", "S1", [1, 1, 1, 1])]
        strict = [cell("x", "C", "S1", [1, 0, 0, 0])]
        dv = bs.divergence(strict, lax, "s", "l")
        self.assertEqual((dv["s_stricter_n"], dv["l_stricter_n"]), (3, 0))
        self.assertEqual(bs.divergence(lax, lax)["kappa"], 1.0)

    def test_sd_between_scales_by_root_g(self):
        self.assertAlmostEqual(bs.sd_between({"ci95": [-0.1, 0.1], "n_clusters": 4}),
                               0.1 / bs.t95(3) * 2)


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
        self.assertNotIn("a1", [r["bid"] for r in bs.top_cell_attribution(cells, "C", "B", 10)["top"]])

    def test_flip_means_the_verdict_changes_not_the_mean_sign(self):
        # Base KEEP over 3 clusters; dropping any one cell leaves 2 clusters (t=12.7) and the
        # verdict goes INCONCLUSIVE while the mean stays positive and unhalved. The mean-sign
        # rule called this stable.
        cells = [cell("c1", "C", "S1", [1, 1, 1, 0]), cell("b1", "B", "S1", [1, 0, 0, 0]),
                 cell("c2", "C", "S2", [1, 1, 1, 0]), cell("b2", "B", "S2", [1, 0, 0, 0]),
                 cell("c3", "C", "S3", [1, 1, 1, 1]), cell("b3", "B", "S3", [1, 0, 0, 0])]
        self.assertEqual(bs.keep_verdict(bs.clustered_delta(cells, "C", "B"))["verdict"], "KEEP")
        self.assertTrue(bs.top_cell_attribution(cells, "C", "B")["inspect"])

    def test_inspect_covers_every_cell_not_only_those_shown(self):
        cells = ([cell(f"c{s}{r}", "C", f"S{s}", [1, 1, 0, 0]) for s in (1, 2) for r in (1, 2, 3)]
                 + [cell("p11", "P", "S1", [1, 1, 0, 0]), cell("p12", "P", "S1", [1, 1, 0, 0]),
                    cell("p1z", "P", "S1", [0, 0, 0, 0])]
                 + [cell(f"p2{r}", "P", "S2", [1, 1, 0, 0]) for r in (1, 2, 3)])
        attr = bs.top_cell_attribution(cells, "C", "P", top_n=0)
        self.assertEqual(attr["top"], [])
        self.assertTrue(attr["inspect"])

    def test_practical_flag_reaches_the_cli(self):
        import subprocess
        r = subprocess.run([sys.executable, os.path.join(os.path.dirname(os.path.abspath(__file__)),
                            "bench_verdict.py"), "--help"], capture_output=True, text=True)
        self.assertIn("--practical", r.stdout)
        import bench_verdict as bv
        cells = [cell("c1", "C", "S1", [1, 1, 1, 0]), cell("b1", "B", "S1", [1, 0, 0, 0]),
                 cell("c2", "C", "S2", [1, 1, 1, 1]), cell("b2", "B", "S2", [1, 0, 0, 0])]
        self.assertEqual(bv.summarize(cells, "C", "B", 0.25)["C_minus_B"]["practical"], 0.25)


HERE = os.path.dirname(os.path.abspath(__file__))


def bench_dir(d, rows, root_map=True):
    """Synthetic graded dir: rows = [(bid, arm, scenario, verdict-row-extras)]."""
    import json
    os.makedirs(os.path.join(d, "graded"), exist_ok=True)
    with open(os.path.join(d, "arm_map.tsv" if root_map else "graded/arm_map.tsv"), "w") as f:
        f.write("bid\tarm\tscenario\trep\n" + "".join(f"{b}\t{a}\t{s}\t1\n" for b, a, s, _ in rows))
    with open(os.path.join(d, "graded/verdicts.jsonl"), "w") as f:
        for b, _, s, extra in rows:
            f.write(json.dumps({"bid": b, "scenario": s, **extra}) + "\n")
    with open(os.path.join(d, "graded/keys.json"), "w") as f:
        json.dump({"S1": {}, "S2": {}}, f)


def exps(m):
    return {"norm": {"decision": "d"},
            "expectations": [{"id": i + 1, "met": bool(v)} for i, v in enumerate(m)]}


GRID = [("c1", "C", "S1", [1, 1, 1, 1]), ("b1", "B", "S1", [1, 0, 0, 0]),
        ("c2", "C", "S2", [1, 1, 1, 0]), ("b2", "B", "S2", [1, 1, 0, 0])]


class TestLoadDirAndCache(unittest.TestCase):
    def test_load_dir_records_error_and_malformed_rows_instead_of_crashing_or_scoring(self):
        import tempfile
        import bench_verdict as bv
        with tempfile.TemporaryDirectory() as d:
            bench_dir(d, [(b, a, s, exps(m)) for b, a, s, m in GRID]
                      + [("e1", "C", "S1", {"error": "judge exit 1"}),            # template error row
                         ("m1", "B", "S1", {"norm": {}, "expectations": [{"id": 1, "met": True}]})])
            cells, baseline, _, berrs, missing = bv.load_dir(d)
        self.assertEqual(missing, [])
        self.assertEqual({c["bid"] for c in cells}, {"c1", "b1", "c2", "b2", "m1"})  # m1 has a norm
        self.assertEqual({c["bid"] for c in baseline}, {"c1", "b1", "c2", "b2"})
        self.assertEqual({e["bid"] for e in berrs}, {"e1", "m1"})

    def test_load_dir_reads_the_legacy_graded_arm_map(self):
        import tempfile
        import bench_verdict as bv
        with tempfile.TemporaryDirectory() as d:
            bench_dir(d, [(b, a, s, exps(m)) for b, a, s, m in GRID], root_map=False)
            self.assertEqual(len(bv.load_dir(d)[1]), 4)

    def test_cache_judge_name_is_what_the_cache_says_or_cached(self):
        import bench_verdict as bv
        self.assertEqual(bv.cache_judge_name([{"judge": "grok-4.5"}] * 2), "grok-4.5")
        for rows in ([], [{}], [{"judge": "grok-4.5"}, {}], [{"judge": "a"}, {"judge": "b"}],
                     [{"judge": 7}]):
            self.assertEqual(bv.cache_judge_name(rows), "cached", repr(rows))

    def test_cached_rows_go_through_the_strict_met_map(self):
        import bench_verdict as bv
        cells = [{"bid": b, "arm": a, "scenario": s} for b, a, s, _ in GRID[:3]]
        cache = [{"bid": "c1", **exps([1, 1, 1, 1])},
                 {"bid": "b1", "expectations": [{"id": 1, "met": "false"}]},   # string met
                 {"bid": "c2", "error": "timeout"}]
        out, errs = bv.regrade(None, cells, {}, 1, cache=cache)
        self.assertEqual([c["bid"] for c in out], ["c1"])
        self.assertEqual({e["bid"] for e in errs}, {"b1", "c2"})

    def test_a_cell_with_no_verdict_row_or_no_cache_row_is_a_named_error(self):
        # Round 4: a scenario whose rows were absent was skipped silently — its arm dropped, the
        # verdict moved (INCONCLUSIVE -> KEEP on an 8-cell fixture) and errors read 0.
        import tempfile
        import bench_verdict as bv
        with tempfile.TemporaryDirectory() as d:
            bench_dir(d, [(b, a, s, exps(m)) for b, a, s, m in GRID])
            with open(os.path.join(d, "arm_map.tsv"), "a") as f:
                f.write("x9\tB\tS3\t1\n")                     # in the map, never graded
            cells, _, _, _, missing = bv.load_dir(d)
        self.assertEqual(missing, [{"bid": "x9", "error": "no graded/verdicts.jsonl row"}])
        cache = [{"bid": b, **exps(m)} for b, _, _, m in GRID if b != "b2"]
        out, errs = bv.regrade(None, cells, {}, 1, cache=cache)
        self.assertEqual(errs, [{"bid": "b2", "error": "no --cache row"}])
        self.assertEqual(bv.summarize(out, "C", "B")["C_minus_B"]["dropped_scenarios"], ["S2"])
        rep = self._run_cached("auto", drop=("b2",), extra_map="x9\tB\tS3\t1\n")
        self.assertEqual(rep["errors"], 2)
        self.assertEqual({e["bid"] for e in rep["error_cells"]}, {"b2", "x9"})
        self.assertEqual(rep["regraded"]["C_minus_B"]["dropped_scenarios"], ["S2"])

    def test_a_pre_12_oct_met_dict_cache_still_reads(self):
        # Round 5: committed --cells-out files (e.g. 2026-07-14 grok-cells.jsonl) carry `met` only.
        import bench_verdict as bv
        cells = [{"bid": b, "arm": a, "scenario": s} for b, a, s, _ in GRID[:2]]
        cache = [{"bid": "c1", "met": {"1": True, "2": True, "3": False, "4": True}},
                 {"bid": "b1", "met": {"1": True}}]   # partial: still refused
        out, errs = bv.regrade(None, cells, {}, 1, cache=cache)
        self.assertEqual([c["bid"] for c in out], ["c1"])
        self.assertEqual(out[0]["met"], {1: True, 2: True, 3: False, 4: True})
        self.assertEqual([e["bid"] for e in errs], ["b1"])

    def test_cells_out_reads_back_as_a_cache_carrying_its_judge(self):
        # Round 4: --cells-out wrote {met:{..}} with no judge, which --cache could not read.
        import json, tempfile
        with tempfile.TemporaryDirectory() as t:
            first = os.path.join(t, "first.jsonl")
            rep1 = self._run_cached("grok", cache_judge="grok-4.5", cells_out=first)
            with open(first) as f:
                rows = [json.loads(line) for line in f]
            self.assertEqual(len(rows), 4)
            # `met` stays for the frozen consumers (2026-07-14 aggregate_poker.py reads r["met"])
            self.assertEqual(set(rows[0]), {"bid", "arm", "scenario", "judge", "met",
                                            "expectations"})
            self.assertEqual({r["judge"] for r in rows}, {"grok-4.5"})
            self.assertEqual(rows[0]["expectations"][0], {"id": 1, "met": True})
            rep2 = self._run_cached("both", cache_file=first)
        self.assertEqual(rep2["judge"], "grok-4.5")
        self.assertIn("divergence", rep2)
        self.assertEqual(rep2["regraded"], rep1["regraded"])

    def _run_cached(self, judge_arg, cache_judge=None, drop=(), extra_map="", cells_out=None,
                    cache_file=None):
        """bench_verdict --cache with stub grok AND claude on PATH that fail if ever called."""
        import json, subprocess, tempfile
        with tempfile.TemporaryDirectory() as d:
            bench_dir(d, [(b, a, s, exps(m)) for b, a, s, m in GRID])
            with open(os.path.join(d, "arm_map.tsv"), "a") as f:
                f.write(extra_map)
            bindir = os.path.join(d, "bin")
            os.makedirs(bindir)
            for cli in ("grok", "claude"):
                with open(os.path.join(bindir, cli), "w") as f:
                    f.write("#!/bin/sh\necho live call >&2\nexit 1\n")
                os.chmod(os.path.join(bindir, cli), 0o755)
            cache = cache_file or os.path.join(d, "cache.jsonl")
            with open(cache, "a") as f:
                for b, _, _, m in ([] if cache_file else GRID):
                    if b in drop:
                        continue
                    row = {"bid": b, **exps(m)}
                    if cache_judge:
                        row["judge"] = cache_judge
                    f.write(json.dumps(row) + "\n")
            env = {k: v for k, v in os.environ.items()
                   if k not in ("SKILL_BENCH_JUDGE_CMD", "GROK_BIN", "COPILOT_BIN")}
            env["PATH"] = bindir + os.pathsep + env.get("PATH", "")
            r = subprocess.run([sys.executable, os.path.join(HERE, "bench_verdict.py"), "--dir", d,
                                "--judge", judge_arg, "--cache", cache,
                                *(["--cells-out", cells_out] if cells_out else [])],
                               capture_output=True, text=True, env=env)
            self.assertEqual(r.returncode, 0, r.stderr)
            return json.loads(r.stdout)

    def test_a_cache_is_never_labelled_with_a_live_backends_name(self):
        # grok and claude both reachable: the label was grok-4.5 / claude-opus-4-8, whichever
        # CLI resolved, regardless of who produced the cached grades.
        for arg in ("auto", "grok", "claude"):
            rep = self._run_cached(arg)
            self.assertEqual(rep["judge"], "cached", arg)
            self.assertEqual(rep["notional_cost_usd"]["judge_calls"], 0)
        self.assertEqual(self._run_cached("auto", "claude-opus-4-8")["judge"], "claude-opus-4-8")

    def test_both_on_a_cache_needs_the_cache_to_name_a_cross_family_judge(self):
        for unproven in (None, "claude-opus-4-8"):
            rep = self._run_cached("both", unproven)
            self.assertIn("degraded", rep)
            self.assertNotIn("divergence", rep)
        rep = self._run_cached("both", "grok-4.5")
        self.assertEqual(rep["judge"], "grok-4.5")
        self.assertEqual(rep["baseline_judge"], "committed")  # no judge recorded for the baseline
        self.assertIn("divergence", rep)


if __name__ == "__main__":
    unittest.main()
