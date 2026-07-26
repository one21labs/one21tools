#!/usr/bin/env python3
"""Decision-logic tests for judge.py pure helpers (no CLI/network)."""
import os, sys, unittest

sys.path.insert(0, os.path.dirname(__file__))
import judge  # noqa: E402


def _which(available):
    """Stub for shutil.which: returns a fake path iff the name is in `available`."""
    return lambda name: ("/usr/bin/" + name) if name in available else None


class TestJudge(unittest.TestCase):
    def test_met_map_extracts_bools_by_id(self):
        v = {"expectations": [{"id": 1, "met": True, "why": "x"}, {"id": 2, "met": False, "why": "y"}]}
        self.assertEqual(judge.met_map(v), {1: True, 2: False})

    def test_met_map_empty(self):
        self.assertEqual(judge.met_map({}), {})

    def test_strip_fence_plain_json(self):
        self.assertEqual(judge.strip_json_fence('{"a": 1}'), '{"a": 1}')

    def test_strip_fence_json_block(self):
        s = 'Here you go:\n```json\n{"a": 1}\n```\ndone'
        self.assertEqual(judge.strip_json_fence(s), '{"a": 1}')

    def test_strip_fence_bare_block(self):
        self.assertEqual(judge.strip_json_fence("```\n[1,2]\n```"), "[1,2]")

    def test_make_judge_dispatch_and_names(self):
        # inject availability so this passes regardless of which CLIs the CI runner has
        both = _which({"grok", "claude"})
        self.assertEqual(judge.make_judge("grok", which=both).name, "grok-4.5")
        self.assertEqual(judge.make_judge("claude", which=both).name, "claude-opus-4-8")

    def test_auto_prefers_grok_cross_family(self):
        r, note = judge.resolve_judge("auto", which=_which({"grok", "claude"}))
        self.assertEqual(r, "grok")
        self.assertIsNone(note)

    def test_auto_falls_back_to_claude_with_caveat(self):
        r, note = judge.resolve_judge("auto", which=_which({"claude"}))
        self.assertEqual(r, "claude")
        self.assertIn("SAME-FAMILY", note)

    def test_auto_none_available_errors(self):
        with self.assertRaises(judge.JudgeError):
            judge.resolve_judge("auto", which=_which(set()))

    def test_explicit_grok_missing_errors_with_remedy(self):
        with self.assertRaises(judge.JudgeError) as cm:
            judge.resolve_judge("grok", which=_which({"claude"}))
        self.assertIn("GROK_BIN", str(cm.exception))

    def test_make_judge_auto_fallback_sets_note(self):
        j = judge.make_judge("auto", which=_which({"claude"}))
        self.assertEqual(j.name, "claude-opus-4-8")
        self.assertIn("SAME-FAMILY", j.fallback_note)

    def test_grok_timeout_raises_judge_error(self):
        # A judge timeout must surface as JudgeError like every other grade() failure mode —
        # a raw subprocess.TimeoutExpired escaping killed a resumable grading pass (PR #219).
        from unittest.mock import patch
        j = judge.GrokJudge(bin="/usr/bin/grok", timeout=1)
        with patch.object(judge.subprocess, "run",
                          side_effect=judge.subprocess.TimeoutExpired(cmd="grok", timeout=1)):
            with self.assertRaises(judge.JudgeError) as ctx:
                j.grade("prompt", {"type": "object"})
        self.assertIn("timeout", str(ctx.exception))

    def test_claude_timeout_raises_judge_error(self):
        from unittest.mock import patch
        j = judge.ClaudeJudge(timeout=1)
        with patch.object(judge.subprocess, "run",
                          side_effect=judge.subprocess.TimeoutExpired(cmd="claude", timeout=1)):
            with self.assertRaises(judge.JudgeError) as ctx:
                j.grade("prompt", {"type": "object"})
        self.assertIn("timeout", str(ctx.exception))

    # --- cross-family generalization (#296): any family, verified per call ---

    def test_family_of_places_each_shipped_vendor(self):
        self.assertEqual(judge.family_of("claude-haiku-4.5"), "anthropic")
        self.assertEqual(judge.family_of("grok-4.5"), "xai")
        self.assertEqual(judge.family_of("gpt-5-mini"), "openai")
        self.assertEqual(judge.family_of("gemini-3.6-flash"), "google")
        self.assertEqual(judge.family_of("kimi-k2.7-code"), "moonshot")

    def test_family_of_unplaceable_is_unknown_not_foreign(self):
        self.assertEqual(judge.family_of("house-model-7"), "unknown")
        self.assertEqual(judge.family_of(None), "unknown")

    def test_parse_copilot_jsonl_reads_answer_and_router_choice(self):
        import json as _j
        out = "\n".join([
            "noise that is not json",
            _j.dumps({"type": "model.call_start", "data": {"model": "placeholder"}}),
            _j.dumps({"type": "session.auto_mode_resolved", "data": {"chosenModel": "gpt-5-mini"}}),
            _j.dumps({"type": "assistant.message", "data": {"content": '{"expectations": []}'}}),
        ])
        text, model = judge.parse_copilot_jsonl(out)
        self.assertEqual(model, "gpt-5-mini")
        self.assertEqual(text, '{"expectations": []}')

    def _copilot_returning(self, model, content='{"expectations": []}'):
        """A CopilotJudge whose CLI answers with `model` — the router choice is the variable."""
        import json as _j
        from unittest.mock import patch
        out = "\n".join([
            _j.dumps({"type": "session.auto_mode_resolved", "data": {"chosenModel": model}}),
            _j.dumps({"type": "assistant.message", "data": {"content": content}}),
        ]) if model else _j.dumps({"type": "assistant.message", "data": {"content": content}})
        j = judge.CopilotJudge(bin="/usr/bin/copilot", env={})
        return j, patch.object(judge.subprocess, "run",
                               return_value=type("R", (), {"returncode": 0, "stdout": out, "stderr": ""}))

    def test_copilot_refuses_a_grade_its_router_sent_back_to_the_generator_family(self):
        # `auto` picks per call and its candidate set includes Claude — a silent same-family grade
        # would report the self-preference confound as an independent measurement.
        j, p = self._copilot_returning("claude-haiku-4.5")
        with p:
            with self.assertRaises(judge.JudgeError) as ctx:
                j.grade("prompt", {"type": "object"})
        self.assertIn("generator's own family", str(ctx.exception))

    def test_copilot_refuses_when_no_placeable_model_is_named(self):
        j, p = self._copilot_returning(None)
        with p:
            with self.assertRaises(judge.JudgeError):
                j.grade("prompt", {"type": "object"})

    def test_copilot_grades_when_the_router_stayed_cross_family(self):
        j, p = self._copilot_returning("gpt-5-mini")
        with p:
            self.assertEqual(j.grade("prompt", {"type": "object"}), {"expectations": []})
        self.assertEqual(j.last_model, "gpt-5-mini")

    def test_command_judge_needs_a_command(self):
        with self.assertRaises(judge.JudgeError) as ctx:
            judge.CommandJudge(env={})
        self.assertIn("SKILL_BENCH_JUDGE_CMD", str(ctx.exception))

    def test_command_judge_needs_a_declared_cross_family_model(self):
        # Unnamed or same-family: the report could not state whose judgement it carries.
        for model in (None, "claude-opus-5"):
            env = {"SKILL_BENCH_JUDGE_CMD": "my-llm"}
            if model:
                env["SKILL_BENCH_JUDGE_MODEL"] = model
            with self.assertRaises(judge.JudgeError) as ctx:
                judge.CommandJudge(env=env)
            self.assertIn("SKILL_BENCH_JUDGE_MODEL", str(ctx.exception))

    def test_command_judge_accepts_a_declared_foreign_model_and_names_the_run_after_it(self):
        j = judge.CommandJudge(env={"SKILL_BENCH_JUDGE_CMD": "my-llm",
                                    "SKILL_BENCH_JUDGE_MODEL": "gemini-3.6-flash"})
        self.assertEqual(j.name, "gemini-3.6-flash")

    def test_auto_prefers_the_adopter_configured_judge_over_a_discovered_cli(self):
        r, note = judge.resolve_judge("auto", which=_which({"grok", "claude"}),
                                      env={"SKILL_BENCH_JUDGE_CMD": "my-llm"})
        self.assertEqual((r, note), ("command", None))

    def test_auto_reaches_copilot_when_it_is_the_only_cross_family_cli(self):
        r, note = judge.resolve_judge("auto", which=_which({"copilot", "claude"}), env={})
        self.assertEqual((r, note), ("copilot", None))

    def test_auto_falls_back_to_claude_with_a_note_naming_every_way_to_restore_independence(self):
        r, note = judge.resolve_judge("auto", which=_which({"claude"}), env={})
        self.assertEqual(r, "claude")
        self.assertIn("SAME-FAMILY", note)
        self.assertIn("SKILL_BENCH_JUDGE_CMD", note)

    def test_an_explicit_unavailable_judge_names_its_own_remedy(self):
        with self.assertRaises(judge.JudgeError) as ctx:
            judge.resolve_judge("copilot", which=_which({"claude"}), env={})
        self.assertIn("COPILOT_BIN", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
