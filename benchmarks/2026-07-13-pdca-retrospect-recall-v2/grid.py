#!/usr/bin/env python3
"""Instrument 1 v2 grid runner (issue #177, ADR 0024/0052; pre-registration: README.md, frozen).

Successor to ../2026-07-12-pdca-retrospect-recall/grid.py (frozen; never edited). Same protocol:
48 counted cells = 8 substrates x 2 arms x 3 reps, SERIAL (ADR 0033's pin), sonnet both arms
(ADR 0006), symmetric tool carve-out allow=(Read,Grep,Glob,Bash) both arms -- the treatment is
content only (ADR 0023). Same prompts as v1 (only the substrates changed). Poka-yoke: the full
grid refuses to start unless the cost gate passes on REAL pilot-measured cell costs, and halts
mid-run if cumulative spend crosses the ceiling (runtime backstop; the gate is the
projection-time stop). Cells are resumable: an existing non-error output file is skipped.

v2 adds two pre-grid, pre-registered modes (README.md items 4 and the pilot line), both capped
at $10 with a STOP-NEXT-CELL backstop (checked BEFORE each cell runs, not after -- these modes
are cheap enough that pre-checking is the tighter poka-yoke) and excluded from the counted 48:

    --pilot       1 A + 1 C rep on T1 -> pilot-outputs/T1-{A,C}-r1.json (prices the harder
                  substrates; the full grid's cost gate reads these files for its measured costs)
    --prescreen   1 A rep on EACH of the 6 seeded substrates -> prescreen-outputs/{sub}-A-r1.json
                  (README item 4's saturation check: raw recall >= 0.75 on this rep means the
                  substrate needs hardening or dropping before the grid runs)

No flag runs the full 48-cell grid; it requires pilot-outputs/T1-{A,C}-r1.json to already exist
(run --pilot first) since the cost gate is gated on REAL measured cost, never a guess.
"""
import argparse
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parents[1]
# The shared bench lib moved to skill-bench/scripts/lib on this branch; benchmarks/lib (where
# v1's grid.py still points) is now empty. Point at the real location.
sys.path.insert(0, str(REPO_ROOT / "skill-bench" / "scripts" / "lib"))
from cost_gate import gate  # noqa: E402
from hermetic_driver import build_env, do_call, summarize_call  # noqa: E402

SUBSTRATES = ["T1", "T2", "T3", "T4", "T5", "T6", "C1", "C2"]
SEEDED = ["T1", "T2", "T3", "T4", "T5", "T6"]
ARMS = ("A", "C")
REPS = 3
ALLOW = ("Read", "Grep", "Glob", "Bash")
MODEL = "sonnet"
PRE_GRID_CAP_USD = 10.0  # pilot + prescreen combined ceiling (excluded from the counted 48)

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
        "ones) -- also written at friction.md:\n" + friction_text.strip() + "\n\n"
        "Analyze per your method and output your findings."
    )


def _cell_call(sub, arm, env):
    repo = HERE / "substrates" / sub / "repo"
    if not repo.exists():
        sys.exit(f"substrate {sub} missing -- run build_substrates.py first")
    if arm == "A":
        return do_call(ARM_A_PROMPT, MODEL, env, str(repo), allow=ALLOW)
    friction = (repo / "friction.md").read_text(encoding="utf-8")
    return do_call(arm_c_prompt(friction), MODEL, env, str(repo), allow=ALLOW,
                   extra_args=("--append-system-prompt", RETRO_AGENT_SP))


def run_capped(cells, env, cap_usd, label, start_spent=0.0):
    """Run [(cell_name, sub, arm, rep, out_path), ...] under a stop-NEXT-cell cap: checked before
    each cell starts (not after it spends), so a run never begins a cell it cannot afford."""
    spent = start_spent
    for cell_name, sub, arm, rep, path in cells:
        if path.exists() and not json.loads(path.read_text())["summary"]["error"]:
            print(f"[{cell_name}] exists, skipped")
            continue
        if spent >= cap_usd:
            print(f"{label}: stop-next-cell -- spent ${spent:.2f} >= cap ${cap_usd:.2f}, "
                  f"halting before {cell_name}")
            break
        call = _cell_call(sub, arm, env)
        record = {"cell": cell_name, "substrate": sub, "arm": arm, "rep": rep,
                  "allow": list(ALLOW), "model": MODEL,
                  "summary": summarize_call(call), "response": call["response"]}
        path.write_text(json.dumps(record, indent=1), encoding="utf-8")
        cost = record["summary"].get("cost_usd") or 0.0
        spent += cost
        print(f"[{cell_name}] cost={cost} spent={spent:.2f} err={record['summary']['error']}")
    return spent


def load_pilot_costs():
    """Real measured per-cell costs from --pilot's output, in (A, C) order -- the full grid's
    cost gate is priced on these, never a hardcoded guess (the harder v2 substrates make v1's
    $0.3755 pilot figure stale)."""
    pdir = HERE / "pilot-outputs"
    costs = []
    for arm in ("A", "C"):
        p = pdir / f"T1-{arm}-r1.json"
        if not p.exists():
            return None
        rec = json.loads(p.read_text(encoding="utf-8"))
        c = rec["summary"].get("cost_usd")
        if rec["summary"]["error"] or c is None:
            return None
        costs.append(c)
    return costs


def do_pilot():
    out = HERE / "pilot-outputs"
    out.mkdir(exist_ok=True)
    env = build_env()
    cells = [(f"T1-{arm}-r1", "T1", arm, 1, out / f"T1-{arm}-r1.json") for arm in ARMS]
    spent = run_capped(cells, env, PRE_GRID_CAP_USD, "pilot")
    print(f"pilot complete: total ${spent:.2f} (cap ${PRE_GRID_CAP_USD:.2f})")


def do_prescreen():
    out = HERE / "prescreen-outputs"
    out.mkdir(exist_ok=True)
    env = build_env()
    cells = [(f"{sub}-A-r1", sub, "A", 1, out / f"{sub}-A-r1.json") for sub in SEEDED]
    spent = run_capped(cells, env, PRE_GRID_CAP_USD, "prescreen")
    print(f"prescreen complete: total ${spent:.2f} (cap ${PRE_GRID_CAP_USD:.2f}) -- README item 4's "
          f"saturation check (raw recall >= 0.75 -> harden or drop) is scored from these cells, "
          f"not run here")


def do_grid():
    meta = json.loads((HERE / "metadata.json").read_text(encoding="utf-8"))
    ceiling = meta["cost"]["ceiling_usd"]
    cells_total = meta["cells"]["counted"]

    pilot_costs = load_pilot_costs()
    if pilot_costs is None:
        sys.exit("full grid needs REAL measured pilot costs -- run `python3 grid.py --pilot` "
                 "first (writes pilot-outputs/T1-{A,C}-r1.json)")
    ok, projected = gate(cells_total, pilot_costs, ceiling)
    if not ok:
        sys.exit(f"cost gate: projected ${projected:.2f} > ceiling ${ceiling} -- grid halted")
    print(f"cost gate: projected ${projected:.2f} within ${ceiling} (pilot costs {pilot_costs}) "
          f"-- proceeding")

    out = HERE / "outputs"
    out.mkdir(exist_ok=True)
    env = build_env()
    spent = 0.0
    for sub in SUBSTRATES:
        repo = HERE / "substrates" / sub / "repo"
        if not repo.exists():
            sys.exit(f"substrate {sub} missing -- run build_substrates.py first")
        for rep in range(1, REPS + 1):
            for arm in ARMS:
                cell = f"{sub}-{arm}-r{rep}"
                path = out / f"{cell}.json"
                if path.exists() and not json.loads(path.read_text())["summary"]["error"]:
                    print(f"[{cell}] exists, skipped")
                    continue
                call = _cell_call(sub, arm, env)
                record = {"cell": cell, "substrate": sub, "arm": arm, "rep": rep,
                          "allow": list(ALLOW), "model": MODEL,
                          "summary": summarize_call(call), "response": call["response"]}
                path.write_text(json.dumps(record, indent=1), encoding="utf-8")
                cost = (record["summary"].get("cost_usd") or 0.0)
                spent += cost
                print(f"[{cell}] cost={cost} spent={spent:.2f} err={record['summary']['error']}")
                if spent > ceiling:
                    sys.exit(f"runtime backstop: cumulative ${spent:.2f} > ceiling ${ceiling} "
                             f"-- halted, partial grid recorded (a recorded halt, not a loss)")
    print(f"grid complete: total ${spent:.2f}")


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--pilot", action="store_true", help="1 A + 1 C rep on T1, $10 cap")
    p.add_argument("--prescreen", action="store_true",
                   help="1 A rep on each of T1-T6, $10 cap")
    args = p.parse_args()
    if args.pilot and args.prescreen:
        sys.exit("--pilot and --prescreen are mutually exclusive")
    if args.pilot:
        do_pilot()
    elif args.prescreen:
        do_prescreen()
    else:
        do_grid()


if __name__ == "__main__":
    main()
