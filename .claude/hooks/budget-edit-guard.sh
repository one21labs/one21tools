#!/usr/bin/env bash
# PreToolUse hook (matcher: Edit|Write) for THIS REPO's .claude/settings.json: the PREVENT rung
# for char budgets (ADR 0060; ladder: ADR 0047). Computes the file's PROJECTED post-edit size and
# DENIES an Edit/Write that would land over its cap, reporting cap/current/projected/headroom —
# the over-budget edit becomes impossible instead of detected by the post-edit lint or CI.
#
# Caps come from their one homes at fire time — pdca-workflow/scripts/char-budget.mjs (node
# import) for the doc/ADR/agent classes, skills/building-skills/scripts/validate.py (python
# import: caps, R4 body math, TOC_RE) for SKILL.md bodies and skill references (#255) — no
# duplicated numbers or counting logic. BUDGET_GUARD_CAPS_JSON overrides caps for tests/consumers
# without node; skill-class sizing still imports validate.py (that class fails open without it).
# Size math mirrors charLen (CRLF normalized). Lite ADRs (`tier: lite` in the RESULTING text) get
# the lite cap. Fails OPEN on any parse/import error — a broken hook must never block edits.
#
# liveness: per-event-exempt -- a deny fires only on an over-cap edit attempt, which may
# legitimately never occur in a window (ADR 0086 (b)). Canaries: one per case-arm file class
# (the documented coverage list -- the #255 gap was exactly a missing class); tiny env caps
# force the deny path. Declaration grammar home: scripts/check-gate-tests.mjs.
# canary: {"event":"PreToolUse","tool":"Write","env":{"BUDGET_GUARD_CAPS_JSON":"{\"doc\":10,\"adr\":10,\"lite\":10,\"agent\":10,\"skill\":10,\"ref\":10,\"refToc\":10}"},"stdin":{"tool_name":"Write","tool_input":{"file_path":"__FIXTURE__/CLAUDE.md","content":"content well over a ten char cap"}},"expect":{"deny":true}}
# canary: {"event":"PreToolUse","tool":"Write","env":{"BUDGET_GUARD_CAPS_JSON":"{\"doc\":10,\"adr\":10,\"lite\":10,\"agent\":10,\"skill\":10,\"ref\":10,\"refToc\":10}"},"stdin":{"tool_name":"Write","tool_input":{"file_path":"__FIXTURE__/docs/decisions/0001-canary.md","content":"content well over a ten char cap"}},"expect":{"deny":true}}
# canary: {"event":"PreToolUse","tool":"Write","env":{"BUDGET_GUARD_CAPS_JSON":"{\"doc\":10,\"adr\":10,\"lite\":10,\"agent\":10,\"skill\":10,\"ref\":10,\"refToc\":10}"},"stdin":{"tool_name":"Write","tool_input":{"file_path":"__FIXTURE__/pdca-workflow/agents/pm.md","content":"content well over a ten char cap"}},"expect":{"deny":true}}
# canary: {"event":"PreToolUse","tool":"Write","env":{"BUDGET_GUARD_CAPS_JSON":"{\"doc\":10,\"adr\":10,\"lite\":10,\"agent\":10,\"skill\":10,\"ref\":10,\"refToc\":10}"},"copy":["skills/building-skills/scripts/validate.py"],"stdin":{"tool_name":"Write","tool_input":{"file_path":"__FIXTURE__/skills/foo/SKILL.md","content":"---\nname: foo\ndescription: d\n---\n\nThis body is definitely longer than ten characters."}},"expect":{"deny":true}}
# canary: {"event":"PreToolUse","tool":"Write","env":{"BUDGET_GUARD_CAPS_JSON":"{\"doc\":10,\"adr\":10,\"lite\":10,\"agent\":10,\"skill\":10,\"ref\":10,\"refToc\":10}"},"copy":["skills/building-skills/scripts/validate.py"],"stdin":{"tool_name":"Write","tool_input":{"file_path":"__FIXTURE__/skills/foo/references/r.md","content":"A reference body with no table of contents and well over ten characters."}},"expect":{"deny":true}}
input=$(cat)
fp=$(printf '%s' "$input" | sed -n 's/.*"file_path"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/p')
# Normalize JSON-escaped Windows backslashes first — both sibling hooks do this and regression-test
# it; this one never got that half, so a backslash path matched no arm and the PREVENT rung skipped.
fp=$(printf '%s' "$fp" | sed 's/\\\\/\//g; s/\\/\//g')
# Normalize to absolute BEFORE the case arms. Every arm below is written `*/dir/...`, which needs
# a literal `/` ahead of `dir`, so a repo-relative file_path fell straight through to exit 0 and
# the PREVENT rung never ran. Latent rather than live — Claude Code passes absolute paths — but a
# guard with a path shape that silently skips is the class this repo keeps finding.
case "$fp" in /*) ;; "") ;; *) fp="${CLAUDE_PROJECT_DIR:-.}/$fp" ;; esac
export BUDGET_GUARD_FP="$fp"   # the python body must see the NORMALIZED path too:
                               # normalizing only for the case filter left Edit on a
                               # relative path reading an empty file and allowing.
case "$fp" in
  */CLAUDE.md|CLAUDE.md|*/docs/decisions/*.md|*/pdca-workflow/agents/*.md|*claude-md-template.md) ;;
  */skills/*/SKILL.md|*/skills/*/references/*.md) ;;
  *) exit 0 ;;
esac

root="${CLAUDE_PROJECT_DIR:-.}"
export VP_PATH="$root/skills/building-skills/scripts/validate.py"
caps="${BUDGET_GUARD_CAPS_JSON:-}"
if [ -z "$caps" ]; then
  export CB_PATH="$root/pdca-workflow/scripts/char-budget.mjs"
  caps=$(node --input-type=module -e "
    const m = await import('file://' + process.env.CB_PATH);
    console.log(JSON.stringify({doc: m.DOC_BUDGETS['CLAUDE.md'], adr: m.ADR_CHAR_BUDGET,
      lite: m.LITE_ADR_CHAR_BUDGET, agent: m.AGENT_CHAR_BUDGET}));" 2>/dev/null) || exit 0
  # Skill-class caps live in validate.py (ADR 0009) — same live-import rule. On bridge failure,
  # keep the node caps: the doc/ADR/agent classes stay guarded; skill-class lookups then miss
  # their keys and fail open in the main block.
  export CB_CAPS_JSON="$caps"
  merged=$(python3 - 2>/dev/null <<'BRIDGE'
import importlib.util, json, os
spec = importlib.util.spec_from_file_location("v", os.environ["VP_PATH"])
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
c = json.loads(os.environ["CB_CAPS_JSON"])
c.update(skill=mod.BODY_MAX_CHARS, ref=mod.REFERENCE_MAX_CHARS, refToc=mod.REFERENCE_TOC_THRESHOLD)
print(json.dumps(c))
BRIDGE
) && caps="$merged"
fi
export BUDGET_GUARD_CAPS_JSON="$caps"
export HOOK_INPUT="$input"
python3 - <<'PYEOF'
import json, os, re, sys
try:
    hook = json.loads(os.environ["HOOK_INPUT"])
    ti = hook.get("tool_input") or {}
    # The NORMALIZED path from the shell, not the raw one: normalizing only for the case filter
    # left an Edit on a relative path opening nothing (cwd != project root), yielding empty
    # current text, so `old not in cur` short-circuited to allow. Write hid it, because Write
    # never reads the file — which is why the first regression fixture passed while Edit stayed
    # bypassable.
    fp = os.environ.get("BUDGET_GUARD_FP") or ti.get("file_path") or ""
    caps = json.loads(os.environ["BUDGET_GUARD_CAPS_JSON"])
    def norm(s):
        return s.replace("\r\n", "\n")
    try:
        cur = norm(open(fp, encoding="utf-8").read())
    except OSError:
        cur = ""
    if "content" in ti:  # Write
        out = norm(ti["content"])
    else:                # Edit
        old, new = norm(ti.get("old_string") or ""), norm(ti.get("new_string") or "")
        if not old or old not in cur:
            sys.exit(0)  # the Edit itself will fail; not this hook's job
        out = cur.replace(old, new) if ti.get("replace_all") else cur.replace(old, new, 1)
    def vp_mod():
        # validate.py owns the R4 body math and TOC_RE — import, never mirror (poka-yoke:
        # a local copy would silently drift when validate.py's rules change).
        import importlib.util
        spec = importlib.util.spec_from_file_location("v", os.environ["VP_PATH"])
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod
    size_out, size_cur, unit, hint = len(out), len(cur), "chars", ""
    if re.search(r"docs/decisions/[^/]+\.md$", fp):
        cap = caps["lite"] if re.search(r"^tier:\s*lite\s*$", out[:800], re.M) else caps["adr"]
    elif re.search(r"pdca-workflow/agents/[^/]+\.md$", fp):
        cap = caps["agent"]
    elif re.search(r"skills/[^/]+/SKILL\.md$", fp):
        cap, vp = caps["skill"], vp_mod()
        size_out, size_cur, unit = vp.skill_body_chars(out), vp.skill_body_chars(cur), "body chars"
    elif re.search(r"skills/[^/]+/references/[^/]+\.md$", fp):
        cap = caps["ref"]
        if not vp_mod().TOC_RE.search(out) and caps["refToc"] < cap:
            cap = caps["refToc"]
            if size_out <= caps["ref"]:
                hint = f" Adding '## Table of Contents' raises the cap to {caps['ref']}."
    elif fp.endswith("CLAUDE.md") or fp.endswith("claude-md-template.md"):
        cap = caps["doc"]
    else:
        sys.exit(0)  # case-glob over-match (e.g. a nested references/ dir) — not an enforced class
    # Deny only when the edit lands over cap AND does not shrink the file — an over-cap file
    # being cut toward compliance must never be trapped by its own guard.
    if size_out > cap and size_out > size_cur:
        # Gate-hit telemetry (ADR 0080): observability only, never in the failure path — the
        # deny below must print even if this append fails. Line format home: scorecard.mjs
        # parseGateHits; docs/pdca marker check per ADR 0071, never mkdir.
        try:
            from datetime import datetime, timezone
            pdca = os.path.join(os.environ.get("CLAUDE_PROJECT_DIR", "."), "docs", "pdca")
            if os.path.isdir(pdca):
                with open(os.path.join(pdca, "gate-hits.txt"), "a", encoding="utf-8") as lf:
                    lf.write(datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
                             + f" gate-hit budget-edit-guard {fp}\n")
        except Exception:
            pass
        reason = (f"budget-edit-guard (ADR 0060): this edit lands {fp} at {size_out} {unit}, over its "
                  f"{cap} cap (current {size_cur}, headroom {max(0, cap - size_cur)}, edit adds "
                  f"{size_out - size_cur:+d}). Measure first; cut muda elsewhere in the file to fit "
                  f"(doc-budgets.md 'Editing a budgeted doc')." + hint)
        print(json.dumps({"hookSpecificOutput": {"hookEventName": "PreToolUse",
              "permissionDecision": "deny", "permissionDecisionReason": reason}}))
except Exception:
    sys.exit(0)  # fail open
PYEOF
exit 0
