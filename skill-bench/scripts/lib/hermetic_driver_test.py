#!/usr/bin/env python3
"""Decision-logic tests for hermetic_driver.py (repo rule: no gating plumbing without a test)."""
import json
import os
import subprocess
import unittest
import unittest.mock
from types import SimpleNamespace

from hermetic_driver import (CLAUDE_DENY_TOOLS, build_env, capture_artifacts, do_call,
                             fresh_copy, neutral_cwd, summarize_call)

ENVELOPE = {"result": "the answer", "total_cost_usd": 0.01, "duration_ms": 900,
            "duration_api_ms": 800, "usage": {"input_tokens": 5, "output_tokens": 7},
            "stop_reason": "end_turn"}


def fake_run(returncode=0, stdout=json.dumps(ENVELOPE), stderr=""):
    def run(cmd, **kwargs):
        return SimpleNamespace(returncode=returncode, stdout=stdout, stderr=stderr)
    return run


class BuildEnv(unittest.TestCase):
    def test_hermetic_env(self):
        with unittest.mock.patch.dict(os.environ, {"CLAUDECODE": "1", "PATH": "/usr/bin"}, clear=False):
            env = build_env()
        self.assertNotIn("CLAUDECODE", env)
        self.assertTrue(env["CLAUDE_CONFIG_DIR"].endswith(os.path.join("issue30", "claude-config")))
        self.assertEqual(env["CLAUDE_EFFORT"], "medium")
        self.assertTrue(env["PATH"].startswith(os.path.join(os.path.expanduser("~"), ".local", "bin")))

    def test_effort_override(self):
        self.assertEqual(build_env(effort="high")["CLAUDE_EFFORT"], "high")


class DoCall(unittest.TestCase):
    def test_success_no_retry(self):
        call = do_call("p", "sonnet", {}, ".", run=fake_run())
        self.assertIsNone(call["error"])
        self.assertFalse(call["retried"])
        self.assertEqual(call["response"], "the answer")
        self.assertEqual(call["envelope"]["total_cost_usd"], 0.01)

    def test_timestamps_always_present(self):
        for run in (fake_run(), fake_run(returncode=1)):
            call = do_call("p", "sonnet", {}, ".", run=run)
            self.assertIn("start", call["timestamps"])
            self.assertIn("end", call["timestamps"])
            self.assertLessEqual(call["timestamps"]["start"], call["timestamps"]["end"])

    def test_retry_once_then_success(self):
        calls = []

        def flaky(cmd, **kwargs):
            calls.append(1)
            if len(calls) == 1:
                return SimpleNamespace(returncode=1, stdout="", stderr="boom")
            return SimpleNamespace(returncode=0, stdout=json.dumps(ENVELOPE), stderr="")

        call = do_call("p", "sonnet", {}, ".", run=flaky)
        self.assertIsNone(call["error"])
        self.assertTrue(call["retried"])
        self.assertEqual(len(calls), 2)

    def test_gives_up_after_one_retry(self):
        calls = []

        def broken(cmd, **kwargs):
            calls.append(1)
            return SimpleNamespace(returncode=2, stdout="", stderr="dead")

        call = do_call("p", "sonnet", {}, ".", run=broken)
        self.assertIn("nonzero exit 2", call["error"])
        self.assertTrue(call["retried"])
        self.assertEqual(len(calls), 2)

    def test_timeout_is_an_error(self):
        def timeout(cmd, **kwargs):
            raise subprocess.TimeoutExpired(cmd, 5)

        call = do_call("p", "sonnet", {}, ".", timeout=5, run=timeout)
        self.assertIn("timeout after 5s", call["error"])

    def test_bad_envelope_json_is_an_error(self):
        call = do_call("p", "sonnet", {}, ".", run=fake_run(stdout="not json"))
        self.assertIn("json parse failure", call["error"])
        self.assertEqual(call["response"], "")

    def test_deny_list_and_stdin_prompt_reach_the_command(self):
        seen = {}

        def spy(cmd, **kwargs):
            seen["cmd"], seen["input"] = cmd, kwargs.get("input")
            return SimpleNamespace(returncode=0, stdout=json.dumps(ENVELOPE), stderr="")

        do_call("the prompt", "haiku", {}, ".", run=spy)
        for tool in CLAUDE_DENY_TOOLS:
            self.assertIn(tool, seen["cmd"])
        self.assertEqual(seen["input"], "the prompt")
        self.assertIn("haiku", seen["cmd"])

    def test_deny_list_loads_from_the_single_txt_home(self):
        # ADR 0041: deny_tools.txt is the one language-neutral home (bash reads it via mapfile).
        from pathlib import Path
        txt = Path(__file__).with_name("deny_tools.txt").read_text().split()
        self.assertEqual(CLAUDE_DENY_TOOLS, txt)
        for tool in ("Task", "Agent", "TaskCreate", "TaskUpdate", "SendMessage"):
            self.assertIn(tool, CLAUDE_DENY_TOOLS)


class SummarizeCall(unittest.TestCase):
    def test_maps_envelope_fields_and_keeps_timestamps(self):
        call = do_call("p", "sonnet", {}, ".", run=fake_run())
        s = summarize_call(call)
        self.assertEqual(s["cost_usd"], 0.01)
        self.assertEqual(s["duration_api_ms"], 800)
        self.assertEqual(s["usage"]["output_tokens"], 7)
        self.assertEqual(s["timestamps"], call["timestamps"])
        self.assertFalse(s["retried"])
        self.assertIsNone(s["error"])

    def test_error_call_summarizes_with_null_envelope_fields(self):
        call = do_call("p", "sonnet", {}, ".", run=fake_run(returncode=1))
        s = summarize_call(call)
        self.assertIsNone(s["cost_usd"])
        self.assertIsNone(s["usage"])
        self.assertIn("nonzero exit", s["error"])
        self.assertIn("start", s["timestamps"])


class NeutralCwd(unittest.TestCase):
    def test_creates_scratch_dir(self):
        import tempfile
        with tempfile.TemporaryDirectory() as td:
            cwd = neutral_cwd(td)
            self.assertTrue(os.path.isdir(cwd))
            self.assertEqual(os.path.basename(cwd), "cwd")


class CarveOut(unittest.TestCase):
    """ADR 0052 carve-out: allow= removes named tools from the deny flags; unknown names error."""

    def captured_cmd(self, **kwargs):
        seen = {}

        def run(cmd, **rkw):
            seen["cmd"] = cmd
            return SimpleNamespace(returncode=0, stdout=json.dumps(ENVELOPE), stderr="")

        do_call("p", "sonnet", {}, ".", run=run, **kwargs)
        return seen["cmd"]

    def test_default_denies_everything(self):
        cmd = self.captured_cmd()
        denied = cmd[cmd.index("--disallowedTools") + 1:]
        self.assertEqual(denied, list(CLAUDE_DENY_TOOLS))

    def test_allow_removes_exactly_those_tools(self):
        cmd = self.captured_cmd(allow=("Read", "Grep", "Glob", "Bash"))
        denied = set(cmd[cmd.index("--disallowedTools") + 1:])
        self.assertEqual(denied, set(CLAUDE_DENY_TOOLS) - {"Read", "Grep", "Glob", "Bash"})
        self.assertIn("Task", denied)

    def test_unknown_allow_name_raises(self):
        with self.assertRaises(ValueError):
            do_call("p", "sonnet", {}, ".", run=fake_run(), allow=("NotATool",))

    def test_extra_args_appended_after_deny(self):
        cmd = self.captured_cmd(extra_args=("--append-system-prompt", "SP"))
        self.assertEqual(cmd[-2:], ["--append-system-prompt", "SP"])
        self.assertLess(cmd.index("--disallowedTools"), cmd.index("--append-system-prompt"))


class FreshCopyAndCapture(unittest.TestCase):
    """Per-cell fresh-copy hermetics + every-arm artifact capture (#191 / the armd lesson)."""

    def bundle(self, td):
        import pathlib
        src = pathlib.Path(td, "src")
        (src / "docs").mkdir(parents=True)
        (src / "docs" / "existing.md").write_text("pre-existing corpus file")
        (src / "data.txt").write_text("payload")
        return src

    def test_fresh_copy_is_private_and_complete(self):
        import pathlib
        import shutil
        import tempfile
        with tempfile.TemporaryDirectory() as td:
            src = self.bundle(td)
            work = fresh_copy(src, "S1-A-r1")
            try:
                self.assertNotEqual(str(src), work)
                self.assertEqual(pathlib.Path(work, "data.txt").read_text(), "payload")
                pathlib.Path(work, "data.txt").write_text("mutated")
                self.assertEqual((src / "data.txt").read_text(), "payload")
            finally:
                shutil.rmtree(work, ignore_errors=True)

    def test_capture_only_cell_created_files(self):
        import pathlib
        import shutil
        import tempfile
        with tempfile.TemporaryDirectory() as td:
            src = self.bundle(td)
            work = fresh_copy(src, "S1-A-r1")
            try:
                pathlib.Path(work, "docs", "decision.md").write_text("the cell's artifact")
                got = capture_artifacts(work, src)
                self.assertEqual(list(got), [os.path.join("docs", "decision.md")])
                self.assertEqual(got[os.path.join("docs", "decision.md")], "the cell's artifact")
            finally:
                shutil.rmtree(work, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
