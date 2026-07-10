#!/usr/bin/env python3
"""Decision-logic tests for hermetic_driver.py (repo rule: no gating plumbing without a test)."""
import json
import os
import subprocess
import unittest
from types import SimpleNamespace
from unittest import mock

from hermetic_driver import (CLAUDE_DENY_TOOLS, build_env, do_call, neutral_cwd,
                             summarize_call)

ENVELOPE = {"result": "the answer", "total_cost_usd": 0.01, "duration_ms": 900,
            "duration_api_ms": 800, "usage": {"input_tokens": 5, "output_tokens": 7},
            "stop_reason": "end_turn"}


def fake_run(returncode=0, stdout=json.dumps(ENVELOPE), stderr=""):
    def run(cmd, **kwargs):
        return SimpleNamespace(returncode=returncode, stdout=stdout, stderr=stderr)
    return run


class BuildEnv(unittest.TestCase):
    def test_hermetic_env(self):
        with mock.patch.dict(os.environ, {"CLAUDECODE": "1", "PATH": "/usr/bin"}, clear=False):
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


if __name__ == "__main__":
    unittest.main()
