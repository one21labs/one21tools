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
        self.assertEqual(judge.met_map(v, 2), {1: True, 2: False})
        self.assertEqual(judge.met_map(v), {1: True, 2: False})

    def test_met_map_strict_refuses_every_reply_that_is_not_a_grade(self):
        # Each of these scored as a real all-false (or, for "false", a TRUE) grade with 0 errors.
        bad = [{}, [], "x", {"expectations": []},
               {"expectations": [{"id": 1, "met": True}]},                       # partial
               {"expectations": [{"id": "1", "met": True}, {"id": "2", "met": True}]},
               {"expectations": [{"id": 1, "met": "false"}, {"id": 2, "met": True}]},
               {"expectations": [{"id": 1, "met": True}, {"id": 1, "met": True}]},  # dup id
               {"expectations": [{"id": 1, "met": True}, {"id": 3, "met": True}]},
               {"expectations": [{"id": 1, "met": 1}, {"id": 2, "met": True}]}]
        for v in bad:
            with self.assertRaises(judge.JudgeError, msg=repr(v)):
                judge.met_map(v, 2)

    def test_met_map_legacy_form_counts_only_literal_true(self):
        # Frozen dated-dir callers pass no n; they keep running, but a string is never met.
        self.assertEqual(judge.met_map({}), {})
        self.assertEqual(judge.met_map({"expectations": [{"id": 1, "met": "false"}]}), {1: False})

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

    def _claude_call(self, model="opus", served=("claude-opus-5-5",), caller_env=None, **kw_judge):
        """Run one ClaudeJudge.grade against a stubbed subprocess.run; -> (judge, argv, kwargs).
        `caller_env` replaces the config-dir variables the caller's shell carries (none by
        default)."""
        import json as _j
        from unittest.mock import patch
        env = {"type": "result", "result": '{"expectations": []}', "total_cost_usd": 0.5,
               "usage": {"input_tokens": 10}, "modelUsage": {m: {} for m in served}}
        seen = {}

        def run(cmd, **kw):
            seen["cmd"], seen["kw"] = cmd, kw
            return type("R", (), {"returncode": 0, "stdout": _j.dumps(env), "stderr": ""})
        parent = {"CLAUDE_CODE_SESSION_ID": "parent", "CCR_TOKEN": "x", "CLAUDECODE": "1"}
        with patch.dict(os.environ, parent), patch.object(judge.subprocess, "run", run):
            for k in ("SKILL_BENCH_CONFIG_DIR", "CLAUDE_CONFIG_DIR"):
                os.environ.pop(k, None)
            os.environ.update(caller_env or {})
            j = judge.ClaudeJudge(model=model, **kw_judge)
            j.grade("prompt", {"type": "object"})
        return j, seen["cmd"], seen["kw"]

    def test_claude_judge_runs_isolated_from_the_parent_session_and_checkout(self):
        j, cmd, kw = self._claude_call()
        for k in ("CLAUDE_CODE_SESSION_ID", "CCR_TOKEN", "CLAUDECODE"):
            self.assertNotIn(k, kw["env"])
        repo = os.path.realpath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
        self.assertFalse(os.path.realpath(kw["cwd"]).startswith(repo + os.sep))
        self.assertEqual(os.listdir(kw["cwd"]), [])
        self.assertEqual(cmd[cmd.index("--tools") + 1], "")
        for flag in ("--disable-slash-commands", "--strict-mcp-config"):
            self.assertIn(flag, cmd)
        self.assertNotIn("prompt", " ".join(cmd))  # prompt on stdin, not argv
        self.assertIn("prompt", kw["input"])

    def test_claude_judge_uses_the_callers_login_not_the_repo_private_config_dir(self):
        # build_env's fallback ($HOME/issue30/claude-config) exists only on this repo's machine;
        # forced on an adopter it made every judge call exit 1 unauthenticated (24/24 NO-DATA).
        _, _, kw = self._claude_call()
        self.assertNotIn("CLAUDE_CONFIG_DIR", kw["env"])              # CLI default login
        _, _, kw = self._claude_call(caller_env={"CLAUDE_CONFIG_DIR": "/opt/cc-config"})
        self.assertEqual(kw["env"]["CLAUDE_CONFIG_DIR"], "/opt/cc-config")  # the caller's own

    def test_claude_judge_config_dir_is_explicit_arg_then_skill_bench_var(self):
        _, _, kw = self._claude_call(caller_env={"SKILL_BENCH_CONFIG_DIR": "/clean",
                                                 "CLAUDE_CONFIG_DIR": "/opt/cc-config"})
        self.assertEqual(kw["env"]["CLAUDE_CONFIG_DIR"], "/clean")
        _, _, kw = self._claude_call(caller_env={"SKILL_BENCH_CONFIG_DIR": "/clean"},
                                     config_dir="/empty")   # g8-shortfall/grade.py's form
        self.assertEqual(kw["env"]["CLAUDE_CONFIG_DIR"], "/empty")

    def test_claude_judge_reports_the_model_that_served_it_not_the_alias(self):
        j, _, _ = self._claude_call(served=("claude-opus-5-5",))
        self.assertEqual(j.name, "claude-opus-5-5")
        self.assertEqual(j.real_cost_usd, 0.5)
        self.assertGreater(j.cost_usd(), 0)  # unpriced served id falls back to the default row

    def test_claude_judge_pinned_model_refuses_a_different_server(self):
        with self.assertRaises(judge.JudgeError):
            self._claude_call(model="claude-opus-5-5", served=("claude-sonnet-5",))

    def _grok_returning(self, served):
        """A GrokJudge whose CLI envelope says `served` (a tuple of model ids) answered."""
        import json as _j
        from unittest.mock import patch
        env = {"structuredOutput": {"expectations": []}}
        if served is not None:
            env["modelUsage"] = {m: {} for m in served}
        r = type("R", (), {"returncode": 0, "stdout": _j.dumps(env), "stderr": ""})
        return judge.GrokJudge(bin="/usr/bin/grok"), patch.object(judge.subprocess, "run",
                                                                  return_value=r)

    def test_grok_runs_from_an_empty_cwd(self):
        j, p = self._grok_returning(("grok-4.5",))
        with p as run:
            j.grade("prompt", {"type": "object"})
        self.assertEqual(os.listdir(run.call_args.kwargs["cwd"]), [])

    def test_grok_sandbox_is_an_allow_list_not_the_no_op_deny_flag(self):
        # Planted-file probe, 29-Jul-2026: grok ignored --disallowed-tools; --tools held.
        j, p = self._grok_returning(("grok-4.5",))
        with p as run:
            j.grade("prompt", {"type": "object"})
        cmd = run.call_args.args[0]
        self.assertNotIn("--disallowed-tools", cmd)
        self.assertEqual(cmd[cmd.index("--tools") + 1], judge.GROK_TOOLS)

    def test_grok_reports_the_model_that_served_it(self):
        j, p = self._grok_returning(("grok-4.5-build",))
        with p:
            self.assertEqual(j.grade("prompt", {"type": "object"}), {"expectations": []})
        self.assertEqual(j.name, "grok-4.5-build")

    def test_grok_refuses_a_grade_it_cannot_show_left_the_generator_family(self):
        # The model is not pinned: a grok call served by a Claude model (or naming none) was
        # reported as grok-4.5 and counted as an independent cross-family grade.
        for served in (("claude-opus-5-5",), ("grok-4.5", "claude-haiku-4.5"), ("house-7",),
                       (), None):
            j, p = self._grok_returning(served)
            with p:
                with self.assertRaises(judge.JudgeError, msg=repr(served)):
                    j.grade("prompt", {"type": "object"})
            self.assertEqual(j.name, "grok-4.5", "a refused call must not rename the judge")

    def test_cached_judge_carries_the_name_it_is_given_never_a_backend(self):
        self.assertEqual(judge.CachedJudge().name, "cached")
        self.assertEqual(judge.CachedJudge("claude-opus-4-8").name, "claude-opus-4-8")
        self.assertEqual(judge.CachedJudge().cost_usd(), 0.0)

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

    def test_copilot_sandbox_is_an_explicit_allow_list(self):
        # Planted-file probe, 24-Oct-2026: a bare --available-tools leaked the file; =sql held.
        j, p = self._copilot_returning("gpt-5-mini")
        with p as run:
            j.grade("prompt", {"type": "object"})
        cmd = run.call_args.args[0]
        self.assertIn("--available-tools=sql", cmd)
        self.assertNotIn("--available-tools", cmd)

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
