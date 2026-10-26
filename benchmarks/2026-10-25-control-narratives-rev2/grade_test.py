"""grade_one: a judge reply that is not a full grade is retried once, then becomes an error row,
never a crash and never a row of silent falses (#331 defect 3). The judge is the real
IsolatedClaudeJudge (its parsing runs); only its CLI call is mocked. Needs the skill-measure lib."""
import json
import sys
import types
import unittest
from unittest import mock

sys.modules.setdefault("grid", types.SimpleNamespace(  # grid reads the frozen evals at import
    EVALS={}, cap_hit=None, check_auth=None, check_harness=None))
import grade  # noqa: E402

MODEL = "claude-opus-5-5"
CELL = {"cell": "c1", "skill": "control-narratives", "scenario": "control-narratives:E1",
        "model": MODEL, "arm": "without", "rep": 1, "response": "narrative"}
EV = {"task": "write it", "expectations": ["states the trip", "states the reset"]}
GOOD = json.dumps({"expectations": [{"id": 1, "met": True, "why": "quotes ```SP-1``` verbatim"},
                                    {"id": 2, "met": False, "why": ""}]})


def run(*replies):
    """grade_one over a judge whose successive CLI calls return `replies`."""
    envs = [{"result": t, "modelUsage": {MODEL: {}}, "total_cost_usd": 0.01} for t in replies]
    with mock.patch.object(grade.usage_guard, "guarded_run", side_effect=envs), \
            mock.patch.dict(grade.EVALS, {CELL["scenario"]: EV}):
        judge = grade.IsolatedClaudeJudge(MODEL)
        return grade.grade_one(judge, MODEL, CELL), judge.calls


class CappedRowTest(unittest.TestCase):
    def test_capped_reply_fails_every_expectation(self):
        with mock.patch.dict(grade.EVALS, {CELL["scenario"]: EV}):
            row = grade.capped_row(CELL)
        self.assertEqual((row["met"], row["cap_hit"], row["arm"]), ({1: False, 2: False}, True, "without"))


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
