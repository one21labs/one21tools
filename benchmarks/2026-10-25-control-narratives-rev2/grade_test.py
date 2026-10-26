"""grade_one: a judge reply that is not a full grade is retried once, then becomes an error row,
never a crash and never a row of silent falses (#331 defect 3). The judge is the real
harness ClaudeJudge from judge_for (its parsing runs); only its CLI call is mocked. check_probed:
no judge grades without a NO-ACCESS sandbox probe. Needs the skill-measure lib."""
import json
import sys
import tempfile
import types
import unittest
from pathlib import Path
from unittest import mock

sys.modules.setdefault("grid", types.SimpleNamespace(  # grid reads the frozen evals at import
    EVALS={}, cap_hit=None, check_auth=None, check_harness=None))
import grade  # noqa: E402
import usage_guard  # noqa: E402  (on sys.path once grade has loaded the harness)

MODEL = "claude-opus-5-5"
CELL = {"cell": "c1", "skill": "control-narratives", "scenario": "control-narratives:E1",
        "model": MODEL, "arm": "without", "rep": 1, "response": "narrative"}
EV = {"task": "write it", "expectations": ["states the trip", "states the reset"]}
GOOD = json.dumps({"expectations": [{"id": 1, "met": True, "why": "quotes ```SP-1``` verbatim"},
                                    {"id": 2, "met": False, "why": ""}]})


def run(*replies):
    """grade_one over a judge whose successive CLI calls return `replies`."""
    envs = [{"result": t, "modelUsage": {MODEL: {}}, "total_cost_usd": 0.01} for t in replies]
    with mock.patch.object(usage_guard, "guarded_run", side_effect=envs), \
            mock.patch.dict(grade.EVALS, {CELL["scenario"]: EV}):
        judge = grade.judge_for(MODEL)
        return grade.grade_one(judge, MODEL, CELL), judge.calls


class CheckProbedTest(unittest.TestCase):
    def probed(self, *rows):
        with tempfile.TemporaryDirectory() as d:
            (Path(d) / "graded").mkdir()
            if rows:
                (Path(d) / "graded" / "sandbox-probe.jsonl").write_text(
                    "".join(json.dumps(r) + "\n" for r in rows))
            with mock.patch.object(grade, "HERE", Path(d)):
                grade.check_probed("copilot")

    def test_unprobed_or_leaking_judge_is_refused(self):
        for rows in ((), ({"judge": "copilot", "result": "LEAK"},),
                     ({"judge": "copilot", "result": "NO-ACCESS"}, {"judge": "copilot", "result": "LEAK"}),
                     ({"judge": "grok", "result": "NO-ACCESS"},)):
            with self.subTest(rows=rows), self.assertRaises(SystemExit):
                self.probed(*rows)

    def test_latest_no_access_probe_passes(self):
        self.probed({"judge": "copilot", "result": "LEAK"}, {"judge": "copilot", "result": "NO-ACCESS"})


class CappedRowTest(unittest.TestCase):
    def test_capped_reply_fails_every_expectation(self):
        with mock.patch.dict(grade.EVALS, {CELL["scenario"]: EV}):
            row = grade.capped_row(CELL)
        self.assertEqual((row["met"], row["cap_hit"], row["arm"]), ({1: False, 2: False}, True, "without"))


class ExclusionTest(unittest.TestCase):
    """aggregate.py and invented.py derive the graded cell set from this, not from a stale pass."""

    def test_capped_graded_error_and_short_excluded_good_graded(self):
        from capped import cap_hit as capped  # the real predicate (capped_test.py)
        rec = lambda err, text: {"summary": {"error": err}, "response": text}  # noqa: E731
        with mock.patch.object(grade, "cap_hit", capped):
            self.assertIsNone(grade.exclusion(rec("output hit the 32000-token cap", "x")))
            self.assertEqual(grade.exclusion(rec("timeout", "")), "timeout")
            self.assertIsNotNone(grade.exclusion(rec(None, "too short")))
            self.assertIsNone(grade.exclusion(rec(None, "The narrative. " * 40)))


class GradeOneTest(unittest.TestCase):
    def test_fence_inside_a_why_string_parses(self):
        res, calls = run(GOOD)
        self.assertEqual((res["row"]["met"], calls), ({1: True, 2: False}, 1))

    def test_retry_uses_the_second_reply(self):
        res, calls = run("not json", GOOD)
        self.assertEqual((res["row"]["met"], calls), ({1: True, 2: False}, 2))

    def test_bad_replies_are_error_rows_after_one_retry(self):
        partial = {"expectations": [{"id": 1, "met": True, "why": ""}]}
        no_id = {"expectations": [{"met": True, "why": ""}, {"id": 2, "met": False, "why": ""}]}
        for name, reply in (("non-JSON", "I cannot grade this."), ("JSON list", "[1, 2]"),
                            ("partial", json.dumps(partial)), ("missing id", json.dumps(no_id))):
            with self.subTest(name):
                res, calls = run(reply, reply)
                self.assertEqual((sorted(res), res["error"]["bid"], calls), (["error"], "c1", 2))


if __name__ == "__main__":
    unittest.main()
