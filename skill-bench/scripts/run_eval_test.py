#!/usr/bin/env python3
"""run_eval_test.py -- decision-logic test for the vendored run_eval.py's fixed detection and
aggregation (ADR 0033; "never ship a process-gating script without a test of its decision
logic" -- the trigger runner is a measurement instrument, not a process gate, but the fixed
detection IS the trigger count, so it gets the same discipline). Zero-dependency: stdlib
unittest. Run: python run_eval_test.py  (or: python -m unittest run_eval_test) from this dir.

Covers the pure, subprocess-free extractions -- detect_trigger_line() (run_single_query's
per-line stream loop) and summarize_query()/summarize_results() (run_eval's aggregation) --
against the 5 vendored fixes (3 stream patches + timeout-as-null + the fallback-branch
patch, issue #104) plus a clean no-trigger stream. main()/run_single_query()'s IO (spawning `claude -p`) is untested here by design: it
needs a live WSL Claude session, which is exactly what these extractions avoid.
"""
import json
import unittest
from pathlib import Path

from run_eval import DetectState, detect_trigger_line, summarize_query, summarize_results


def sse(event: dict) -> str:
    """A stream-json line: {"type": "stream_event", "event": {...}}."""
    return json.dumps({"type": "stream_event", "event": event})


def block_start(tool_name: str) -> str:
    return sse({"type": "content_block_start",
                "content_block": {"type": "tool_use", "name": tool_name, "id": "x"}})


def block_delta(partial_json: str) -> str:
    return sse({"type": "content_block_delta",
                "delta": {"type": "input_json_delta", "partial_json": partial_json}})


def block_stop() -> str:
    return sse({"type": "content_block_stop"})


def message_stop() -> str:
    return sse({"type": "message_stop"})


def result_line() -> str:
    return json.dumps({"type": "result"})


def assistant_message(*tool_calls: tuple[str, dict]) -> str:
    """A fallback-path line: a full assistant message carrying tool_use content items."""
    content = [{"type": "tool_use", "name": name, "input": tool_input, "id": "x"}
               for name, tool_input in tool_calls]
    return json.dumps({"type": "assistant", "message": {"content": content}})


def feed(lines: list[str], clean_name: str) -> bool:
    """Run detect_trigger_line() over `lines` the way run_single_query's loop does: thread
    state, return on the first non-None verdict. Falls through to state.triggered (always False
    -- no keep-watching path sets it) if the stream ends undetected, matching
    run_single_query's post-loop `return state.triggered`."""
    state = DetectState(pending_tool_name=None, accumulated_json="", triggered=False)
    for line in lines:
        state, verdict = detect_trigger_line(line, clean_name, state)
        if verdict is not None:
            return verdict
    return state.triggered


class UnrelatedToolCallPatch(unittest.TestCase):
    """Fix 1 of 5: an unrelated first tool call must not end detection (upstream: `return
    False` at the first non-Skill/Read content_block_start)."""

    def test_unrelated_call_then_matching_skill_still_triggers(self):
        clean_name = "building-skills-skill-abc123"
        lines = [
            block_start("Bash"),          # unrelated -- upstream would return False here
            block_stop(),
            block_start("Skill"),
            block_delta(f'{{"skill":"{clean_name}"}}'),
        ]
        self.assertTrue(feed(lines, clean_name))

    def test_unrelated_call_alone_does_not_trigger(self):
        clean_name = "building-skills-skill-abc123"
        lines = [block_start("Bash"), block_stop(), result_line()]
        self.assertFalse(feed(lines, clean_name))


class WrongToolBlockPatch(unittest.TestCase):
    """Fix 3 of 5: a completed tool block that doesn't match resets pending state and keeps
    watching (upstream: `return clean_name in accumulated_json` / `return False` at the first
    content_block_stop / message_stop, closing the detection window)."""

    def test_non_matching_block_resets_then_later_block_triggers(self):
        clean_name = "building-skills-skill-abc123"
        lines = [
            block_start("Skill"),
            block_delta('{"skill":"some-other-skill"}'),  # accumulated, but not clean_name
            block_stop(),                                  # fix 3: reset, keep watching
            block_start("Skill"),
            block_delta(f'{{"skill":"{clean_name}"}}'),
        ]
        self.assertTrue(feed(lines, clean_name))

    def test_non_matching_block_resets_state_fields(self):
        clean_name = "building-skills-skill-abc123"
        state = DetectState(pending_tool_name=None, accumulated_json="", triggered=False)
        for line in [block_start("Skill"), block_delta('{"skill":"other"}')]:
            state, verdict = detect_trigger_line(line, clean_name, state)
            self.assertIsNone(verdict)
        state, verdict = detect_trigger_line(block_stop(), clean_name, state)
        self.assertIsNone(verdict)
        self.assertIsNone(state.pending_tool_name)
        self.assertEqual(state.accumulated_json, "")

    def test_message_stop_also_resets_instead_of_closing(self):
        clean_name = "building-skills-skill-abc123"
        lines = [
            block_start("Skill"),
            block_delta('{"skill":"some-other-skill"}'),
            message_stop(),         # fix 3 covers this branch too
            block_start("Skill"),
            block_delta(f'{{"skill":"{clean_name}"}}'),
        ]
        self.assertTrue(feed(lines, clean_name))


class MatchingSkillBlock(unittest.TestCase):
    def test_matching_skill_tool_call_triggers(self):
        clean_name = "building-skills-skill-abc123"
        lines = [block_start("Skill"), block_delta(f'{{"skill":"{clean_name}"}}')]
        self.assertTrue(feed(lines, clean_name))

    def test_matching_read_tool_call_triggers(self):
        clean_name = "building-skills-skill-abc123"
        lines = [block_start("Read"), block_delta(f'{{"file_path":"skills/{clean_name}/SKILL.md"}}')]
        self.assertTrue(feed(lines, clean_name))


class FallbackMessagePatch(unittest.TestCase):
    """Fix 5 of 5: the full-assistant-message fallback must not return a terminal verdict on
    the first unrelated tool_use (issue #104) -- only a positive match ends detection early;
    an unmatched message keeps watching."""

    def test_unrelated_then_matching_tool_in_same_message_triggers(self):
        clean_name = "building-skills-skill-abc123"
        line = assistant_message(("Bash", {"command": "ls"}),
                                 ("Skill", {"skill": clean_name}))
        self.assertTrue(feed([line], clean_name))

    def test_unrelated_message_then_matching_message_triggers(self):
        clean_name = "building-skills-skill-abc123"
        lines = [assistant_message(("Bash", {"command": "ls"})),
                 assistant_message(("Skill", {"skill": clean_name}))]
        self.assertTrue(feed(lines, clean_name))

    def test_unrelated_tools_only_is_not_triggered(self):
        clean_name = "building-skills-skill-abc123"
        lines = [assistant_message(("Bash", {"command": "ls"})), result_line()]
        self.assertFalse(feed(lines, clean_name))

    def test_matching_read_in_second_position_triggers(self):
        clean_name = "building-skills-skill-abc123"
        line = assistant_message(("Grep", {"pattern": "x"}),
                                 ("Read", {"file_path": f"skills/{clean_name}/SKILL.md"}))
        self.assertTrue(feed([line], clean_name))


class NoTriggerStream(unittest.TestCase):
    def test_full_stream_with_no_matching_tool_call_is_not_triggered(self):
        clean_name = "building-skills-skill-abc123"
        lines = [
            block_start("Bash"),
            block_delta('{"command":"ls"}'),
            block_stop(),
            block_start("Grep"),
            block_delta('{"pattern":"foo"}'),
            block_stop(),
            result_line(),
        ]
        self.assertFalse(feed(lines, clean_name))

    def test_empty_and_malformed_lines_are_skipped(self):
        clean_name = "building-skills-skill-abc123"
        lines = ["", "   ", "not json{{{", result_line()]
        self.assertFalse(feed(lines, clean_name))


class TimeoutAsNull(unittest.TestCase):
    """Fix 4 of 5: a timed-out run records None -- excluded from trigger_rate's denominator and
    from pass/fail, surfaced as a timeouts count (upstream scored a timeout as False, silently
    deflating rates under load). Exercised on summarize_query()/summarize_results(), the pure
    extraction of run_eval's aggregation."""

    def test_timed_out_run_is_excluded_from_the_rate(self):
        r = summarize_query("q", [True, None, False], should_trigger=True, trigger_threshold=0.5)
        self.assertEqual(r["trigger_rate"], 0.5)  # 1 trigger / 2 COMPLETED runs, not /3
        self.assertEqual(r["completed_runs"], 2)
        self.assertEqual(r["runs"], 3)
        self.assertEqual(r["timeouts"], 1)
        self.assertTrue(r["pass"])

    def test_timeout_is_not_scored_as_not_triggered(self):
        # Upstream's False-scoring would read [True, None] as rate 0.5; as null it is 1.0.
        r = summarize_query("q", [True, None], True, 0.5)
        self.assertEqual(r["trigger_rate"], 1.0)
        self.assertTrue(r["pass"])

    def test_all_runs_timed_out_is_no_measurement_not_a_fail(self):
        r = summarize_query("q", [None, None], True, 0.5)
        self.assertIsNone(r["trigger_rate"])
        self.assertIsNone(r["pass"])
        self.assertEqual(r["timeouts"], 2)
        self.assertEqual(r["completed_runs"], 0)

    def test_no_timeouts_matches_upstream_scoring(self):
        r = summarize_query("q", [True, False], True, 0.5)
        self.assertEqual(r["trigger_rate"], 0.5)
        self.assertEqual(r["timeouts"], 0)
        self.assertTrue(r["pass"])

    def test_summary_surfaces_timeouts_and_null_passes(self):
        results = [summarize_query("a", [True], True, 0.5),        # pass
                   summarize_query("b", [None, None], True, 0.5),  # all-timeout: neither
                   summarize_query("c", [True], False, 0.5)]       # fail (fired, shouldn't)
        s = summarize_results(results)
        self.assertEqual(s, {"total": 3, "passed": 1, "failed": 1, "timeouts": 2})

    def test_run_single_query_timeout_path_returns_none(self):
        # Source-level guard (like the stdin one below): the timeout sentinel in
        # run_single_query must return None, not fall through to state.triggered.
        source = Path(__file__).with_name("run_eval.py").read_text(encoding="utf-8")
        self.assertRegex(source, r"if timed_out:\n\s+return None")


class StdinDevnullRegression(unittest.TestCase):
    """(iv) cheap regression guard for the stdin=DEVNULL fix (not exercised by
    detect_trigger_line -- it lives in run_single_query's subprocess.Popen call). Reading the
    source is far cheaper than spawning a real `claude -p` child to prove it doesn't stall."""

    def test_subprocess_popen_passes_stdin_devnull(self):
        source = Path(__file__).with_name("run_eval.py").read_text(encoding="utf-8")
        self.assertIn("stdin=subprocess.DEVNULL", source)


if __name__ == "__main__":
    unittest.main()
