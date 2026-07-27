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

    def test_judge_both_availability_derives_from_the_registry(self):
        # `both` reads its baseline half off committed files, so the only live requirement is a
        # judge from another family. A hard-coded pair silently degrades the machine whose only
        # cross-family judge is copilot or command, and gates on a claude CLI the mode never calls.
        import bench_verdict as bv

        def only(*bins):
            return lambda b: f"/usr/bin/{b}" if b in bins else None

        self.assertTrue(bv.both_available(only("copilot"), {}))
        self.assertTrue(bv.both_available(only(), {"SKILL_BENCH_JUDGE_CMD": "my-judge"}))
        self.assertTrue(bv.both_available(only("grok"), {}))
        self.assertFalse(bv.both_available(only("claude"), {}))  # same family as the baseline
        self.assertFalse(bv.both_available(only(), {}))

    def test_judge_both_with_cache_emits_divergence_with_no_judge_cli_reachable(self):
        # RUNS main() as a subprocess against a real committed benchmark dir with PATH stripped of
        # every judge CLI. An earlier version of this test re-derived main's if-condition in the
        # test body, so reverting the production guard left it green - it asserted a boolean it had
        # just computed. This one fails if the guard regresses, because it reads the actual report.
        import os, subprocess, sys, json as _json
        here = os.path.dirname(os.path.abspath(__file__))
        bench = os.path.abspath(os.path.join(here, "..", "..", "benchmarks", "2026-07-12-pdca-decide-outcome"))
        if not os.path.isdir(bench):
            self.skipTest("benchmark dir absent")
        r = subprocess.run(
            [sys.executable, os.path.join(here, "bench_verdict.py"), "--dir", bench,
             "--judge", "both", "--cache", os.path.join(bench, "graded", "verdicts.jsonl")],
            capture_output=True, text=True, timeout=120,
            env={"PATH": "/usr/bin:/bin", "HOME": os.environ.get("HOME", "/tmp")})
        self.assertEqual(r.returncode, 0, f"stderr: {r.stderr[-500:]}")
        report = _json.loads(r.stdout)
        self.assertIn("divergence", report)       # the whole point of --judge both
        self.assertIn("verdict_flip", report)          # sibling of divergence, not nested
        self.assertIn("kappa", report["divergence"])
        self.assertNotIn("degraded", report)      # nothing to degrade: no live re-grade was needed
        # And the run must not name a judge that never answered.
        self.assertEqual(report["judge"], "cached")

    def test_a_reachable_judge_cannot_put_its_name_on_a_cache_run_it_did_not_grade(self):
        # The previous fix only bit when NO judge CLI existed. With one reachable, a --cache run
        # that makes zero calls was still labelled with the live judge's model id - so setting an
        # env var for a program that is never executed changed the report. This runs the path
        # where make_judge SUCCEEDS, which is the branch the no-CLI test cannot reach.
        import os, subprocess, sys, json as _json
        here = os.path.dirname(os.path.abspath(__file__))
        bench = os.path.abspath(os.path.join(here, "..", "..", "benchmarks", "2026-07-12-pdca-decide-outcome"))
        if not os.path.isdir(bench):
            self.skipTest("benchmark dir absent")
        r = subprocess.run(
            [sys.executable, os.path.join(here, "bench_verdict.py"), "--dir", bench,
             "--judge", "both", "--cache", os.path.join(bench, "graded", "verdicts.jsonl")],
            capture_output=True, text=True, timeout=120,
            env={"PATH": "/usr/bin:/bin", "HOME": os.environ.get("HOME", "/tmp"),
                 "SKILL_BENCH_JUDGE_CMD": "/bin/false",      # resolvable, and never executed
                 "SKILL_BENCH_JUDGE_MODEL": "grok-4.5"})
        self.assertEqual(r.returncode, 0, f"stderr: {r.stderr[-500:]}")
        report = _json.loads(r.stdout)
        self.assertEqual(report["judge"], "cached")
        self.assertEqual(report["notional_cost_usd"]["judge_calls"], 0)
        self.assertEqual(report["notional_cost_usd"]["judge_calls"], 0)   # cache reuse: nothing ran
        self.assertEqual(report["notional_cost_usd"]["usd"], 0.0)

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
        self.assertEqual(bs.keep_verdict(d)["confidence"], "weak")
        # And the old multiplier really would have said otherwise — not a hypothetical.
        self.assertGreater(d["mean"] - bs.Z95 * (half / d["t_crit"]), 0)

    def test_a_single_cluster_yields_no_interval_rather_than_a_fabricated_one(self):
        cells = [cell("c", "C", "S1", [1, 1, 1, 1]), cell("b", "B", "S1", [0, 0, 0, 0])]
        d = bs.clustered_delta(cells, "C", "B")
        self.assertEqual(d["n_clusters"], 1)
        self.assertNotEqual(d["ci95"][0], d["ci95"][0])  # NaN: one cluster carries no width
        self.assertEqual(bs.keep_verdict(d)["confidence"], "weak")

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
