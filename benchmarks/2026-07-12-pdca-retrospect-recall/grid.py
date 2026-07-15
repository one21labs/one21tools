#!/usr/bin/env python3
"""Instrument 1 grid runner (issue #172, ADR 0052; pre-registration: README.md, frozen).

48 cells = 8 substrates x 2 arms x 3 reps, SERIAL (ADR 0033's pin), sonnet both arms
(ADR 0006), symmetric tool carve-out allow=(Read,Grep,Glob,Bash) both arms — the treatment
is content only (ADR 0023). Poka-yoke: refuses to start unless the cost gate passes on the
pilot-measured cell cost, and halts mid-run if cumulative spend crosses the ceiling
(runtime backstop; the gate is the projection-time stop). Cells are resumable: an existing
non-error output file is skipped, so a crashed run continues instead of re-spending.
"""
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "lib"))
from cost_gate import gate  # noqa: E402
from hermetic_driver import build_env, do_call, summarize_call  # noqa: E402

REPO_ROOT = HERE.parents[1]
SUBSTRATES = ["T1", "T2", "T3", "T4", "T5", "T6", "C1", "C2"]
ARMS = ("A", "C")
REPS = 3
ALLOW = ("Read", "Grep", "Glob", "Bash")
MODEL = "sonnet"
PILOT_CELL_COSTS = [0.3755]  # faithful arm-C cell, ../2026-07-12-pdca-plumbing-pilot/

RETRO_AGENT_SP = (REPO_ROOT / "pdca-workflow" / "agents" / "retrospect.md").read_text(
    encoding="utf-8").split("---", 2)[2].strip()

ARM_A_PROMPT = (
    "Review this session for process problems: transcript at `transcript.md`, session log "
    "at `docs/pdca/session-log.txt`, friction list at `friction.md`; the git history is "
    "this repo. Report each problem with its evidence."
)


def arm_c_prompt(friction_text):
    return (
        "Git range: origin/main...HEAD in this repository (the current working directory).\n\n"
        "Session friction from the orchestrator (my perception; cross-check the git-visible "
        "ones) — also written at friction.md:\n" + friction_text.strip() + "\n\n"
        "Analyze per your method and output your findings."
    )


def main():
    meta = json.loads((HERE / "metadata.json").read_text(encoding="utf-8"))
    ceiling = meta["cost"]["ceiling_usd"]
    cells_total = meta["grid"]["cells"]
    ok, projected = gate(cells_total, PILOT_CELL_COSTS, ceiling)
    if not ok:
        sys.exit(f"cost gate: projected ${projected:.2f} > ceiling ${ceiling} — grid halted")
    print(f"cost gate: projected ${projected:.2f} within ${ceiling} — proceeding")

    out = HERE / "outputs"
    out.mkdir(exist_ok=True)
    env = build_env()
    spent = 0.0
    for sub in SUBSTRATES:
        repo = HERE / "substrates" / sub / "repo"
        if not repo.exists():
            sys.exit(f"substrate {sub} missing — run build_substrates.py first")
        friction = (repo / "friction.md").read_text(encoding="utf-8")
        for rep in range(1, REPS + 1):
            for arm in ARMS:
                cell = f"{sub}-{arm}-r{rep}"
                path = out / f"{cell}.json"
                if path.exists() and not json.loads(path.read_text())["summary"]["error"]:
                    print(f"[{cell}] exists, skipped")
                    continue
                if arm == "A":
                    call = do_call(ARM_A_PROMPT, MODEL, env, str(repo), allow=ALLOW)
                else:
                    call = do_call(arm_c_prompt(friction), MODEL, env, str(repo), allow=ALLOW,
                                   extra_args=("--append-system-prompt", RETRO_AGENT_SP))
                record = {"cell": cell, "substrate": sub, "arm": arm, "rep": rep,
                          "allow": list(ALLOW), "model": MODEL,
                          "summary": summarize_call(call), "response": call["response"]}
                path.write_text(json.dumps(record, indent=1), encoding="utf-8")
                cost = (record["summary"].get("cost_usd") or 0.0)
                spent += cost
                print(f"[{cell}] cost={cost} spent={spent:.2f} err={record['summary']['error']}")
                if spent > ceiling:
                    sys.exit(f"runtime backstop: cumulative ${spent:.2f} > ceiling ${ceiling} "
                             f"— halted, partial grid recorded (a recorded halt, not a loss)")
    print(f"grid complete: total ${spent:.2f}")


if __name__ == "__main__":
    main()
