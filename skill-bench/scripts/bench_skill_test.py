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
        cells = bs.grade_all(rows, {e["id"]: e for e in EVALS}, judge)
        self.assertEqual({c["bid"] for c in cells}, {"t1:with:r1", "t1:with:r2"})
        self.assertEqual(len({c["bid"] for c in cells}), len(cells))

    def test_grade_all_maps_outputs_to_met(self):
        gen = [{"prompt_id": "t1", "arm": "with", "output": "GOOD1"},
               {"prompt_id": "t1", "arm": "without", "output": "BAD1"}]
        judge = FakeJudge({"GOOD1": [True, True], "BAD1": [True, False]})
        cells = bs.grade_all(gen, {e["id"]: e for e in EVALS}, judge)
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
        self.assertEqual(agg["with_minus_without"]["verdict"], "KEEP")
        self.assertEqual(agg["per_scenario"]["t1"], 0.5)
        self.assertEqual(agg["per_scenario"]["t2"], 1.0)

    def test_aggregate_no_benefit_is_cut_candidate(self):
        cells = [
            {"bid": "t1:with", "arm": "with", "scenario": "t1", "met": {1: True}},
            {"bid": "t1:without", "arm": "without", "scenario": "t1", "met": {1: True}},
        ]
        self.assertEqual(bs.aggregate(cells)["with_minus_without"]["verdict"], "CUT-CANDIDATE")

    def test_missing_expectations_default_false(self):
        gen = [{"prompt_id": "t1", "arm": "with", "output": "PARTIAL"}]
        judge = FakeJudge({"PARTIAL": [True]})  # only 1 of 2 expectations returned
        cells = bs.grade_all(gen, {e["id"]: e for e in EVALS}, judge)
        self.assertEqual(cells[0]["met"], {1: True, 2: False})


if __name__ == "__main__":
    unittest.main()
