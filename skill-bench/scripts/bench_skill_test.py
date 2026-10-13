#!/usr/bin/env python3
"""Decision-logic tests for /bench-skill orchestration (grade_all + aggregate), with a FAKE judge
so no CLI/network runs. Proves the with/without delta + verdict math end-to-end offline."""
import os, sys, unittest

sys.path.insert(0, os.path.dirname(__file__))
import bench_skill as bs  # noqa: E402


class FakeJudge:
    """Returns a scripted met pattern per (task, output) so grading is deterministic."""
    name = "fake"

    def __init__(self, script):
        self.script = script  # dict: output -> list[bool]

    def grade(self, prompt, schema):
        # find which output is embedded in the prompt
        for out, mets in self.script.items():
            if out in prompt:
                return {"expectations": [{"id": i + 1, "met": m, "why": ""} for i, m in enumerate(mets)]}
        return {"expectations": []}


EVALS = [{"id": "t1", "task": "task one", "expectations": ["e1", "e2"]},
         {"id": "t2", "task": "task two", "expectations": ["e1", "e2"]}]


class TestBenchSkill(unittest.TestCase):
    def test_grade_all_rep_tagged_bids_are_unique(self):
        # ADR 0058: reps are distinct cells, never collapsed — a single pass can't
        # separate reliably-good from lucky
        judge = FakeJudge({"outA": [True, True], "outB": [False, False]})
        rows = [{"prompt_id": "t1", "arm": "with", "output": "outA", "rep": 1},
                {"prompt_id": "t1", "arm": "with", "output": "outB", "rep": 2}]
        cells, _ = bs.grade_all(rows, {e["id"]: e for e in EVALS}, judge)
        self.assertEqual({c["bid"] for c in cells}, {"t1:with:r1", "t1:with:r2"})
        self.assertEqual(len({c["bid"] for c in cells}), len(cells))

    def test_grade_all_maps_outputs_to_met(self):
        gen = [{"prompt_id": "t1", "arm": "with", "output": "GOOD1"},
               {"prompt_id": "t1", "arm": "without", "output": "BAD1"}]
        judge = FakeJudge({"GOOD1": [True, True], "BAD1": [True, False]})
        cells, _ = bs.grade_all(gen, {e["id"]: e for e in EVALS}, judge)
        self.assertEqual(cells[0]["met"], {1: True, 2: True})
        self.assertEqual(cells[1]["met"], {1: True, 2: False})
        self.assertEqual(cells[0]["arm"], "with")

    def test_aggregate_delta_and_keep_verdict(self):
        # with beats without on both tasks -> positive delta, KEEP
        cells = [
            {"bid": "t1:with", "arm": "with", "scenario": "t1", "met": {1: True, 2: True}},
            {"bid": "t1:without", "arm": "without", "scenario": "t1", "met": {1: True, 2: False}},
            {"bid": "t2:with", "arm": "with", "scenario": "t2", "met": {1: True, 2: True}},
            {"bid": "t2:without", "arm": "without", "scenario": "t2", "met": {1: False, 2: False}},
        ]
        agg = bs.aggregate(cells)
        self.assertEqual(agg["arm_means"]["with"], 1.0)
        self.assertEqual(agg["arm_means"]["without"], 0.25)
        self.assertEqual(agg["per_scenario"]["t1"], 0.5)
        self.assertEqual(agg["per_scenario"]["t2"], 1.0)
        # TWO scenarios cannot support KEEP however lopsided the means look: t(df=1) is 12.706, so
        # the interval is enormous. This asserted KEEP until 2026-07-27 — a claim off two data
        # points, which is the shape a reviewer rejects first.
        self.assertEqual(agg["with_minus_without"]["verdict"], "INCONCLUSIVE")

    def test_a_real_effect_reaches_keep_once_enough_scenarios_carry_it(self):
        # Same direction as above, at six scenarios with a consistent margin: now callable.
        cells = []
        for i in range(6):
            cells += [{"bid": f"t{i}:with", "arm": "with", "scenario": f"t{i}",
                       "met": {1: True, 2: True}},
                      {"bid": f"t{i}:without", "arm": "without", "scenario": f"t{i}",
                       "met": {1: True, 2: i == 0}}]
        v = bs.aggregate(cells)["with_minus_without"]
        self.assertEqual(v["verdict"], "KEEP")
        self.assertGreater(v["win_rate"], 0.6)

    def test_no_benefit_is_inconclusive_not_a_cut(self):
        # One scenario, identical arms. The old rule called this CUT-CANDIDATE off a zero point
        # estimate; with no interval it supports nothing. CUT requires an equivalence result.
        cells = [
            {"bid": "t1:with", "arm": "with", "scenario": "t1", "met": {1: True}},
            {"bid": "t1:without", "arm": "without", "scenario": "t1", "met": {1: True}},
        ]
        self.assertEqual(bs.aggregate(cells)["with_minus_without"]["verdict"], "INCONCLUSIVE")

    def test_an_ungradable_cell_is_recorded_and_excluded_never_scored_zero(self):
        # judge.met_map raises JudgeError on a malformed reply; one bad cell must neither end the
        # run nor enter the arm as a 0 (that charges a judge failure to the skill).
        from judge import JudgeError

        class Flaky(FakeJudge):
            def grade(self, prompt, schema):
                if "BROKEN" in prompt:
                    raise JudgeError("malformed judge reply")
                return super().grade(prompt, schema)
        gen = [{"prompt_id": "t1", "arm": "with", "output": "GOOD1"},
               {"prompt_id": "t1", "arm": "without", "output": "BROKEN", "rep": 2}]
        cells, errs = bs.grade_all(gen, {e["id"]: e for e in EVALS}, Flaky({"GOOD1": [True, True]}))
        self.assertEqual([c["bid"] for c in cells], ["t1:with:r1"])
        self.assertEqual([e["bid"] for e in errs], ["t1:without:r2"])

    def test_practical_bar_is_passed_through_and_arm_means_subtract_to_the_delta(self):
        cells = []
        for i in range(6):
            cells += [{"bid": f"t{i}:with", "arm": "with", "scenario": f"t{i}",
                       "met": {1: True, 2: True}},
                      {"bid": f"t{i}:without", "arm": "without", "scenario": f"t{i}",
                       "met": {1: True, 2: i == 0}}]
        cells.append({"bid": "t9:with", "arm": "with", "scenario": "t9", "met": {1: False, 2: False}})
        agg = bs.aggregate(cells, practical=0.3)
        v = agg["with_minus_without"]
        self.assertEqual(v["practical"], 0.3)
        self.assertEqual(v["verdict"], "INCONCLUSIVE")       # KEEP at 0.0, not at a 0.3 bar
        self.assertEqual(bs.aggregate(cells)["with_minus_without"]["verdict"], "KEEP")
        self.assertEqual(v["dropped_scenarios"], ["t9"])    # one-arm scenario named, not silent
        m = agg["arm_means"]
        self.assertAlmostEqual(m["with"] - m["without"], v["mean"], places=3)

    def test_practical_flag_reaches_the_cli(self):
        import subprocess
        r = subprocess.run([sys.executable, os.path.join(os.path.dirname(os.path.abspath(__file__)),
                            "bench_skill.py"), "--help"], capture_output=True, text=True)
        self.assertIn("--practical", r.stdout)

    def test_partial_judge_reply_is_excluded_not_defaulted_false(self):
        gen = [{"prompt_id": "t1", "arm": "with", "output": "PARTIAL"}]
        judge = FakeJudge({"PARTIAL": [True]})  # only 1 of 2 expectations returned
        cells, errs = bs.grade_all(gen, {e["id"]: e for e in EVALS}, judge)
        self.assertEqual(cells, [])  # a missing grade is a judge failure, never a quality 0
        self.assertEqual(len(errs), 1)

    def test_a_failed_generation_is_excluded_and_never_graded(self):
        # a usage-limited CLI exits 1 with empty stdout: grading "" scores the failure as quality
        class Spy(FakeJudge):
            calls = 0

            def grade(self, prompt, schema):
                Spy.calls += 1
                return super().grade(prompt, schema)
        gen = [{"prompt_id": "t1", "arm": "with", "output": "GOOD1"},
               {"prompt_id": "t1", "arm": "without", "output": "", "error": "exit 1: usage limit"}]
        cells, errs = bs.grade_all(gen, {e["id"]: e for e in EVALS}, Spy({"GOOD1": [True, True]}))
        self.assertEqual([c["bid"] for c in cells], ["t1:with:r1"])
        self.assertEqual(errs[0]["bid"], "t1:without:r1")
        self.assertIn("generation", errs[0]["error"])
        self.assertEqual(Spy.calls, 1)

    def test_report_carries_the_same_family_judge_caveat(self):
        import json, tempfile
        from unittest import mock

        class Sub:
            def run(self, prompts, arms):
                return [{"prompt_id": i, "arm": a["name"], "output": "GOOD1"}
                        for i in range(len(prompts)) for a in arms]
        judge = FakeJudge({"GOOD1": [True, True]})
        judge.fallback_note = "judge fell back to the generators' family"
        ev = tempfile.NamedTemporaryFile("w", suffix=".json", delete=False)
        json.dump(EVALS, ev)
        ev.close()
        out = ev.name + ".out"
        argv = ["bench_skill.py", "--evals", ev.name, "--with-cmd", '["x"]', "--without-cmd", '["y"]',
                "--reps", "1", "--yes", "--out", out]
        with mock.patch.object(bs, "make_substrate", lambda n: Sub()), \
                mock.patch.object(bs, "make_judge", lambda n: judge), \
                mock.patch.object(sys, "argv", argv), mock.patch("sys.stderr"):
            bs.main()
        self.assertEqual(json.load(open(out))["judge_fallback"], judge.fallback_note)

    def test_relative_arm_paths_are_refused_before_any_spend(self):
        # Round 4: arms run from an empty temp dir, so a relative skill path silently loaded
        # nothing (with=0, 0 errors) and a relative argv[0] crashed the run.
        import json, subprocess, tempfile
        with tempfile.TemporaryDirectory() as d:
            os.makedirs(os.path.join(d, "skills", "x"))
            open(os.path.join(d, "skills", "x", "SKILL.md"), "w").close()
            ev = os.path.join(d, "evals.json")
            json.dump(EVALS, open(ev, "w"))
            absolute = os.path.join(d, "skills", "x", "SKILL.md")
            self.assertEqual(bs.relative_path_args(["claude", "-p", "--file", absolute]), [])
            for cmd in (["claude", "-p", "--file", "skills/x/SKILL.md"], ["./arm.sh"]):
                r = subprocess.run([sys.executable, os.path.join(HERE, "bench_skill.py"),
                                    "--evals", ev, "--with-cmd", json.dumps(cmd),
                                    "--without-cmd", '["claude", "-p"]'],
                                   capture_output=True, text=True, cwd=d)
                self.assertNotEqual(r.returncode, 0)
                self.assertIn("make them absolute", r.stderr, cmd)
                self.assertIn(cmd[-1], r.stderr)
                self.assertNotIn("[cost]", r.stderr)  # refused before the spend estimate
        r = subprocess.run([sys.executable, os.path.join(HERE, "bench_skill.py"), "--help"],
                           capture_output=True, text=True)
        self.assertIn("must be absolute", r.stdout)

    def test_path_check_boundaries(self):
        # Round 5: a bare program name resolves via PATH, never the cwd; `--flag=value` and a
        # path-named flag's value are checked; a plain option value is never refused.
        import tempfile
        cwd = os.getcwd()
        with tempfile.TemporaryDirectory() as d:
            for name in ("claude", "sonnet", "myplug"):
                os.makedirs(os.path.join(d, name))
            os.chdir(d)
            try:
                self.assertEqual(bs.relative_path_args(["claude", "-p", "--model", "sonnet"]), [])
                self.assertEqual(bs.relative_path_args(["claude", "--plugin-dir=myplug"]),
                                 ["--plugin-dir=myplug"])
                self.assertEqual(bs.relative_path_args(["claude", "--plugin-dir", "myplug"]),
                                 ["myplug"])
                self.assertEqual(bs.relative_path_args(["claude", "--plugin-dir=/abs/x"]), [])
            finally:
                os.chdir(cwd)


HERE = os.path.dirname(os.path.abspath(__file__))


if __name__ == "__main__":
    unittest.main()
