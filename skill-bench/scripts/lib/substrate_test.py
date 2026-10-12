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

    def test_a_failed_promptfoo_call_is_an_error_row_not_an_empty_output(self):
        # Round 4: each of these became {'output': ''} with no error and was graded as quality 0.
        obj = {"results": {"results": [
            {"provider": {"label": "C"}, "vars": {"prompt_id": 0},
             "response": {"error": "exec exit 1"}},
            {"provider": {"label": "C"}, "vars": {"prompt_id": 1}, "success": False,
             "error": "provider failed", "response": {"output": ""}},
            {"provider": {"label": "C"}, "vars": {"prompt_id": 2}},
            {"provider": {"label": "C"}, "vars": {"prompt_id": 3}, "success": True,
             "response": {"output": "fine"}},
        ]}}
        rows = sub.parse_promptfoo_output(obj)
        self.assertEqual([r.get("error") for r in rows],
                         ["exec exit 1", "provider failed", "no output", None])

    def test_promptfoo_runs_with_the_detached_env(self):
        # Round 5: the round-4 env fix covered native arms only; promptfoo inherited the session.
        from unittest import mock
        seen = {}

        def fake_run(cmd, **kw):
            seen.update(kw)
            raise RuntimeError("stop after capture")
        with mock.patch.object(sub.subprocess, "run", fake_run), \
                mock.patch.dict(os.environ, {"CLAUDECODE": "1", "CLAUDE_CODE_SESSION_ID": "p"}):
            with self.assertRaises(RuntimeError):
                sub.PromptfooSubstrate().run([{"id": "t", "prompt": "x"}],
                                             [{"name": "with", "cmd": ["true"]}])
        self.assertNotIn("CLAUDECODE", seen["env"])
        self.assertNotIn("CLAUDE_CODE_SESSION_ID", seen["env"])

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

    def test_an_unlaunchable_arm_is_an_error_row_not_a_crash(self):
        # Round 4: a relative argv (["./arm.sh"]) does not exist from the neutral cwd; the
        # FileNotFoundError escaped the pool and aborted the run.
        rows = sub.NativeSubstrate(workers=1).run(["p0"], [{"name": "A", "cmd": ["./arm.sh"]}])
        self.assertIn("launch failed", rows[0]["error"])

    def test_arms_do_not_inherit_the_parent_claude_session(self):
        # Round 4: inside a Claude Code session the child inherited its session id (hangs, exit
        # 1), synced skills and reminders. The filter is hermetic_driver.detached_env's.
        planted = {"CLAUDECODE": "1", "CLAUDE_CODE_SESSION_ID": "parent",
                   "CLAUDE_CODE_REMOTE_SESSION_ID": "parent", "CLAUDE_CODE_SYNC_SKILLS": "1",
                   "CLAUDE_CONFIG_DIR": "/nonexistent-cfg", "CLAUDE_CODE_OAUTH_TOKEN": "tok",
                   "SKILLBENCH_PLAIN": "kept"}
        old = {k: os.environ.get(k) for k in planted}
        os.environ.update(planted)
        try:
            r = self._run("import json; print(json.dumps(dict(os.environ)))")
        finally:
            for k, v in old.items():
                os.environ.pop(k) if v is None else os.environ.__setitem__(k, v)
        env = __import__("json").loads(r["output"])
        for k in ("CLAUDECODE", "CLAUDE_CODE_SESSION_ID", "CLAUDE_CODE_REMOTE_SESSION_ID",
                  "CLAUDE_CODE_SYNC_SKILLS", "CLAUDE_EFFORT"):
            self.assertNotIn(k, env)  # no session key, and no hermetic override
        self.assertEqual(env["CLAUDE_CONFIG_DIR"], "/nonexistent-cfg")  # the caller's own, kept
        self.assertEqual(env["CLAUDE_CODE_OAUTH_TOKEN"], "tok")  # the user's own login survives
        self.assertEqual(env["SKILLBENCH_PLAIN"], "kept")
        self.assertEqual(env["PATH"], os.environ["PATH"])


if __name__ == "__main__":
    unittest.main()
