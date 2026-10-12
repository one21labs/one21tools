#!/usr/bin/env python3
"""Decision-logic tests for usage_guard (ADR 0099): when to pause, when to resume, and that a
limit-rejected call waits and is re-issued instead of becoming an ERROR cell."""
import json
import os
import sys
import unittest
from types import SimpleNamespace

sys.path.insert(0, os.path.dirname(__file__))
import usage_guard  # noqa: E402
from usage_guard import UsageGate, decide, guarded_run, parse_stream, streaming  # noqa: E402

NOW = 1_000_000


def info(five=0.1, seven=0.02, status="allowed", reset5=NOW + 3600, reset7=NOW + 86400):
    return {"status": status, "resetsAt": reset5, "rateLimitType": "five_hour",
            "unifiedWindows": {"five_hour": {"utilization": five, "resetsAt": reset5},
                               "seven_day": {"utilization": seven, "resetsAt": reset7}}}


def stream(*events):
    return "\n".join(json.dumps(e) for e in events)


RESULT = {"type": "result", "result": "ok", "total_cost_usd": 0.01}


class Decide(unittest.TestCase):
    def test_below_threshold_runs(self):
        self.assertFalse(decide(info(five=0.79), 0.8, NOW)["pause"])

    def test_at_threshold_pauses_until_reset_plus_buffer(self):
        d = decide(info(five=0.80), 0.8, NOW)
        self.assertTrue(d["pause"])
        self.assertEqual(d["resume_at"], NOW + 3600 + usage_guard.RESUME_BUFFER_S)

    def test_both_windows_hot_waits_for_the_later_reset(self):
        d = decide(info(five=0.9, seven=0.85), 0.8, NOW)
        self.assertEqual(d["resume_at"], NOW + 86400 + usage_guard.RESUME_BUFFER_S)

    def test_rejected_pauses_even_when_threshold_disabled(self):
        d = decide(info(five=0.5, status="rejected"), 1.01, NOW)
        self.assertTrue(d["pause"])
        self.assertIn("REJECTED", d["why"])

    def test_a_window_already_reset_does_not_pause(self):
        self.assertFalse(decide(info(five=0.95, reset5=NOW - 1), 0.8, NOW)["pause"])

    def test_no_signal_never_pauses(self):
        self.assertFalse(decide(None, 0.8, NOW)["pause"])
        self.assertFalse(decide({"status": "allowed"}, 0.8, NOW)["pause"])


class Parse(unittest.TestCase):
    def test_stream_yields_envelope_and_last_rate_limit(self):
        out = stream({"type": "system"}, {"type": "rate_limit_event", "rate_limit_info": info(0.3)},
                     {"type": "rate_limit_event", "rate_limit_info": info(0.4)}, RESULT)
        env, i = parse_stream(out)
        self.assertEqual(env["result"], "ok")
        self.assertEqual(i["unifiedWindows"]["five_hour"]["utilization"], 0.4)

    def test_plain_json_body_still_parses(self):
        env, i = parse_stream(json.dumps({"result": "x", "total_cost_usd": 0}))
        self.assertEqual(env["result"], "x")
        self.assertIsNone(i)

    def test_garbage_is_no_envelope(self):
        self.assertEqual(parse_stream("not json\n{broken"), (None, None))

    def test_streaming_rewrites_format_and_keeps_trailing_args_last(self):
        cmd = streaming(["claude", "-p", "--output-format", "json", "--append-system-prompt", "SP"])
        self.assertEqual(cmd[2:5], ["--output-format", "stream-json", "--verbose"])
        self.assertEqual(cmd[-2:], ["--append-system-prompt", "SP"])


class Gate(unittest.TestCase):
    def make(self):
        clock = {"t": NOW}
        slept = []

        def sleep(s):
            slept.append(s)
            clock["t"] += s
        return UsageGate(threshold=0.8, sleep=sleep, now=lambda: clock["t"], log=lambda m: None), \
            clock, slept

    def test_no_pause_no_wait(self):
        g, _, slept = self.make()
        g.observe(info(0.5))
        self.assertEqual(g.wait(), 0)
        self.assertEqual(slept, [])

    def test_hot_window_blocks_until_reset_then_clears(self):
        g, clock, slept = self.make()
        g.observe(info(0.85))
        waited = g.wait()
        self.assertGreaterEqual(clock["t"], NOW + 3600 + usage_guard.RESUME_BUFFER_S)
        self.assertEqual(waited, sum(slept))
        self.assertTrue(all(s <= 300 for s in slept))  # wakes in chunks, never one long sleep
        self.assertEqual(g.wait(), 0)


class GuardedRun(unittest.TestCase):
    def test_rejected_call_waits_and_is_reissued(self):
        clock = {"t": NOW}
        g = UsageGate(threshold=0.8, sleep=lambda s: clock.__setitem__("t", clock["t"] + s),
                      now=lambda: clock["t"], log=lambda m: None)
        calls = []

        def run(cmd, **kw):
            calls.append(cmd)
            if len(calls) == 1:
                return SimpleNamespace(returncode=1, stderr="", stdout=stream(
                    {"type": "rate_limit_event", "rate_limit_info": info(1.0, status="rejected")}))
            return SimpleNamespace(returncode=0, stderr="", stdout=stream(RESULT))
        env = guarded_run(["claude", "-p", "--output-format", "json"], timeout=5,
                          error=RuntimeError, gate=g, run=run)
        self.assertEqual(env["result"], "ok")
        self.assertEqual(len(calls), 2)
        self.assertGreaterEqual(clock["t"], NOW + 3600)

    def test_ordinary_failure_raises_without_waiting(self):
        g = UsageGate(threshold=0.8, sleep=lambda s: self.fail("must not sleep"), log=lambda m: None)
        run = lambda cmd, **kw: SimpleNamespace(returncode=2, stderr="boom", stdout="")  # noqa: E731
        with self.assertRaises(RuntimeError) as e:
            guarded_run(["claude", "-p"], timeout=5, error=RuntimeError, gate=g, run=run)
        self.assertIn("claude exit 2: boom", str(e.exception))


if __name__ == "__main__":
    unittest.main()
