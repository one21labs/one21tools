#!/usr/bin/env bash
# PreToolUse hook (matcher: Edit|Write) for THIS REPO's .claude/settings.json: the PREVENT rung
# for char budgets (ADR 0060; ladder: ADR 0047). Computes the file's PROJECTED post-edit size and
# DENIES an Edit/Write that would land over its cap, reporting cap/current/projected/headroom —
# the over-budget edit becomes impossible instead of detected by the post-edit lint or CI.
#
# Caps come from their one homes at fire time — pdca-workflow/scripts/char-budget.mjs (node
# import) for the doc/ADR/agent classes, skills/building-skills/scripts/validate.py (python
# import) for SKILL.md bodies and skill references (#255) — no duplicated numbers.
# BUDGET_GUARD_CAPS_JSON overrides for tests/consumers without node.
# Size math mirrors charLen (CRLF normalized). Lite ADRs (`tier: lite` in the RESULTING text) get
# the lite cap. Fails OPEN on any parse/import error — a broken hook must never block edits.
input=$(cat)
fp=$(printf '%s' "$input" | sed -n 's/.*"file_path"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/p')
case "$fp" in
  */CLAUDE.md|CLAUDE.md|*/docs/decisions/*.md|*/pdca-workflow/agents/*.md|*claude-md-template.md) ;;
  */skills/*/SKILL.md|*/skills/*/references/*.md) ;;
  *) exit 0 ;;
esac

root="${CLAUDE_PROJECT_DIR:-.}"
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
  export VP_PATH="$root/skills/building-skills/scripts/validate.py" CB_CAPS_JSON="$caps"
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
    fp = ti.get("file_path") or ""
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
    def body_chars(t):
        # Mirrors validate.py R4: name/description lines excluded; extra frontmatter counts.
        m = re.match(r"^---\n(.*?)\n---", t, re.DOTALL)
        if not m:
            return len(t)
        fm = m.group(1).strip().split("\n")
        return len(t[m.end():].strip()) + len("\n".join(fm[2:]).strip())
    toc_re = re.compile(r"(?im)^##\s*(table of contents|toc|contents)\b")  # = validate.py TOC_RE
    size_out, size_cur, unit, hint = len(out), len(cur), "chars", ""
    if re.search(r"docs/decisions/[^/]+\.md$", fp):
        cap = caps["lite"] if re.search(r"^tier:\s*lite\s*$", out[:800], re.M) else caps["adr"]
    elif re.search(r"pdca-workflow/agents/[^/]+\.md$", fp):
        cap = caps["agent"]
    elif re.search(r"skills/[^/]+/SKILL\.md$", fp):
        cap = caps["skill"]
        size_out, size_cur, unit = body_chars(out), body_chars(cur), "body chars"
    elif re.search(r"skills/[^/]+/references/[^/]+\.md$", fp):
        cap = caps["ref"]
        if not toc_re.search(out) and caps["refToc"] < cap:
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
