#!/usr/bin/env python3
"""Decision-logic tests for the substrate adapter's pure functions (config build + output parse).
No promptfoo/network. CLAUDE.md: no script ships without a test of its decision logic."""
import os, stat, sys, tempfile, unittest

sys.path.insert(0, os.path.dirname(__file__))
import substrate as sub  # noqa: E402


class TestSubstrate(unittest.TestCase):
    def test_config_one_provider_per_spec(self):
        cfg = sub.build_promptfoo_config(["p0", "p1"], [{"name": "A", "exec": "bash a.sh"},
                                                        {"name": "C", "exec": "bash c.sh"}])
        self.assertEqual([p["label"] for p in cfg["providers"]], ["A", "C"])
        self.assertEqual(cfg["providers"][0]["id"], "exec: bash a.sh")
        self.assertEqual(len(cfg["tests"]), 2)
        self.assertEqual(cfg["tests"][1]["vars"]["text"], "p1")
        self.assertEqual(cfg["tests"][1]["vars"]["prompt_id"], 1)  # prompt_id rides in vars

    def test_parse_nested_results_schema(self):
        # promptfoo 0.121 shape: rows at results.results[], prompt_id echoed in vars
        obj = {"results": {"results": [
            {"provider": {"label": "C"}, "vars": {"prompt_id": 0}, "response": {"output": "hi"}},
            {"provider": {"id": "exec: x"}, "vars": {"prompt_id": 1}, "response": {"output": "yo"}},
        ]}}
        rows = sub.parse_promptfoo_output(obj)
        self.assertEqual(rows[0], {"prompt_id": 0, "arm": "C", "output": "hi"})
        self.assertEqual(rows[1]["arm"], "exec: x")
        self.assertEqual(rows[1]["prompt_id"], 1)

    def test_parse_flat_results_and_string_response(self):
        obj = {"results": [{"provider": "A", "response": "plain"}]}
        rows = sub.parse_promptfoo_output(obj)
        self.assertEqual(rows[0]["arm"], "A")
        self.assertEqual(rows[0]["output"], "plain")

    def test_unwrap_cli_output(self):
        self.assertEqual(sub.unwrap_cli_output('{"text": "hello"}'), "hello")      # grok envelope
        self.assertEqual(sub.unwrap_cli_output('{"result": "hi"}'), "hi")          # claude envelope
        self.assertEqual(sub.unwrap_cli_output("plain text"), "plain text")        # not JSON -> raw
        self.assertEqual(sub.unwrap_cli_output(""), "")                            # empty
        self.assertEqual(sub.unwrap_cli_output(None), "")                          # None -> ""
        self.assertEqual(sub.unwrap_cli_output('{"other": 1}'), '{"other": 1}')    # no text field -> raw

    def test_parse_unwraps_envelope_output(self):
        obj = {"results": {"results": [
            {"provider": {"label": "with"}, "vars": {"prompt_id": 0},
             "response": {"output": '{"text": "the answer"}'}}]}}
        self.assertEqual(sub.parse_promptfoo_output(obj)[0]["output"], "the answer")

    def test_make_substrate_dispatch(self):
        self.assertEqual(sub.make_substrate("native").name, "native")
        self.assertEqual(sub.make_substrate("promptfoo").name, "promptfoo")

    def test_promptfoo_substrate_is_version_pinned(self):
        # ADR 0058: a benchmark harness must not track a moving head (@latest)
        old = os.environ.pop("SKILL_BENCH_PROMPTFOO_BIN", None)
        try:
            s = sub.PromptfooSubstrate()
            self.assertIn(sub.PromptfooSubstrate.PIN, s.argv)
            self.assertNotIn("latest", " ".join(s.argv))
        finally:
            if old is not None:
                os.environ["SKILL_BENCH_PROMPTFOO_BIN"] = old


def _stub(body):
    """A stub CLI (python script) in a fresh temp dir; returns its argv."""
    d = tempfile.mkdtemp(prefix="stubcli-")
    p = os.path.join(d, "cli")
    with open(p, "w") as f:
        f.write("#!" + sys.executable + "\nimport os, sys, time\n" + body + "\n")
    os.chmod(p, os.stat(p).st_mode | stat.S_IEXEC)
    return [p]


class TestNativeSubstrate(unittest.TestCase):
    def _run(self, body, timeout=30):
        rows = sub.NativeSubstrate(workers=2, timeout=timeout).run(["p0"], [{"name": "A", "cmd": _stub(body)}])
        self.assertEqual(len(rows), 1)
        return rows[0]

    def test_success_row_carries_no_error(self):
        r = self._run('print(\'{"result": "ok", "is_error": false}\')')
        self.assertEqual(r["output"], "ok")
        self.assertNotIn("error", r)

    def test_nonzero_exit_is_an_error_row_not_an_output(self):
        # a usage-limited CLI: exit 1, empty stdout. Grading it would score a failure as quality.
        r = self._run('sys.stderr.write("usage limit reached"); sys.exit(1)')
        self.assertIn("exit 1", r["error"])
        self.assertIn("usage limit", r["error"])

    def test_envelope_is_error_is_an_error_row_even_at_exit_zero(self):
        r = self._run('print(\'{"result": "Credit balance is too low", "is_error": true}\')')
        self.assertIn("is_error", r["error"])

    def test_timeout_is_an_error_row_not_a_crash(self):
        # TimeoutExpired used to propagate and abort the run, losing every paid generation
        r = self._run("time.sleep(5)", timeout=0.5)
        self.assertIn("timeout", r["error"])

    def test_arms_run_outside_the_callers_project(self):
        # both arms must not auto-load the caller's CLAUDE.md / .claude/skills via cwd discovery
        proj = tempfile.mkdtemp(prefix="adopter-proj-")
        old = os.getcwd()
        os.chdir(proj)
        try:
            r = self._run("print(os.getcwd())")
        finally:
            os.chdir(old)
        cwd = os.path.realpath(r["output"])
        self.assertFalse(cwd.startswith(os.path.realpath(proj)), cwd)
        repo = os.path.realpath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
        self.assertFalse(cwd.startswith(repo + os.sep), cwd)


if __name__ == "__main__":
    unittest.main()
