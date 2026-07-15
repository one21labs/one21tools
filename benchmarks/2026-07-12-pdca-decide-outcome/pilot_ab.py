#!/usr/bin/env python3
"""Price arms A and B (one cell each on B1) so the $300 gate projects the true arm mix —
equal arm sizes make cost_gate's uniform mean over [cA, cB, cC] exactly 24*(cA+cB+cC).
Tool allowance and permission mode match arm C exactly minus the panel machinery
(Skill/Task/Agent), so the treatment difference is structure only (ADR 0023 symmetry).
Arm B's deliberation budget = arm C's faithful pilot cell output-token spend (metadata).
"""
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "lib"))
from hermetic_driver import build_env, do_call, summarize_call  # noqa: E402

SNAP = HERE / "scenario-b1" / "snapshot"
OUT = HERE / "pilot-outputs"
ALLOW = ("Read", "Grep", "Glob", "Bash", "Write", "Edit")
EXTRA = ("--permission-mode", "acceptEdits")

BASE = ("Read ISSUE-41.md at the repository root — it poses a judgment call for this project "
        "(adopt tiered-agent execution for the plugin's Do phase?) with an owner-drafted test "
        "plan. Decide this and record your decision with rationale.")
B_SUFFIX = ("\n\nDeliberate thoroughly before deciding: consider multiple perspectives, argue "
            "against yourself, and only then decide and record your rationale. Use up to "
            "~7,500 tokens of deliberation.")


def run(cell, prompt):
    call = do_call(prompt, "sonnet", build_env(), str(SNAP), timeout=1200,
                   allow=ALLOW, extra_args=EXTRA)
    rec = {"cell": cell, "arm": cell.split("-")[1], "allow": list(ALLOW),
           "summary": summarize_call(call), "response": call["response"]}
    (OUT / f"{cell}.json").write_text(json.dumps(rec, indent=1), encoding="utf-8")
    print(f"[{cell}] cost={rec['summary'].get('cost_usd')} err={rec['summary']['error']}")


if __name__ == "__main__":
    run("b1-A-r0", BASE)
    run("b1-B-r0", BASE + B_SUFFIX)
