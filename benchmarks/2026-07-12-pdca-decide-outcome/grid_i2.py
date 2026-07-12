#!/usr/bin/env python3
"""Instrument 2 grid runner (issue #172, ADR 0052; pre-registration: README.md — frozen).

72 cells = 8 scenarios x 3 arms x 3 reps, serial, resumable (existing non-error output
skipped). Every cell runs in a FRESH copy of its scenario bundle (arm C writes decision
records into the workdir; a shared dir would leak one cell's decision into the next — pilot
finding). Gate precondition: cost_gate on one measured cost per arm (equal arm sizes make the
uniform mean the exact arm-mix projection) vs the owner-funded ceiling in metadata.json.
Runtime backstop halts on cumulative spend > ceiling (recorded halt; cells resume).

Arms (metadata.json): A bare; B = A + deliberation suffix at the pilot-measured budget;
C = /decide with the plugin loaded (--plugin-dir), panel tools allowed, task-list tools
denied, --permission-mode acceptEdits (bypassPermissions refused under root). Files a cell
writes under docs/decisions/ (or MEMO-adjacent) are captured into the record as artifacts.
"""
import json
import shutil
import subprocess
import sys
import tempfile
import threading
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "lib"))
from cost_gate import gate  # noqa: E402
from hermetic_driver import build_env, do_call, summarize_call  # noqa: E402

REPO = HERE.parents[1]
REPS = 3
MODEL = "sonnet"
ALLOW_AB = ("Read", "Grep", "Glob", "Bash", "Write", "Edit")
ALLOW_C = ("Skill", "Task", "Agent") + ALLOW_AB
EXTRA_AB = ("--permission-mode", "acceptEdits")
EXTRA_C = ("--plugin-dir", str(REPO / "pdca-workflow"), "--permission-mode", "acceptEdits")

SCENARIOS = {
    "B1": ("scenario-b1/snapshot", "Read ISSUE-41.md at the repository root — it poses a judgment call for this project: adopt tiered-agent execution for the plugin's Do phase?"),
    "B2": ("scenario-b1/snapshot", "Read ISSUE-41.md at the repository root. Focus ONLY on the execution-design call inside its pre-registered test plan: when the experiment runs, should it execute the full pre-registered grid, or pilot the most expensive arm first and stop early if the pre-registered decision gate is already decidable?"),
    "B3": ("scenario-b3/snapshot", "Read ISSUE-106.md at the repository root — it poses a judgment call for this project: after the duplicate-spend incident it describes, is a prose sync-before-spend rule enough, or should multi-session coordination be mechanized now, and how?"),
    "B4": ("scenario-b4/snapshot", "Read ISSUE-109.md at the repository root — it poses a judgment call for this project: proceed with the routing experiment it proposes (and under what conditions), or decline it?"),
    "S1": ("scenario-s1/workdir", "Read MEMO.md in this directory — it asks for a decision about the free-tier request limit."),
    "S2": ("scenario-s2/workdir", "Read MEMO.md in this directory — it asks for a decision about the service-migration scope."),
    "S3": ("scenario-s3/workdir", "Read MEMO.md in this directory — it asks for a decision about adopting the workflow framework."),
    "S4": ("scenario-s4/workdir", "Read MEMO.md in this directory — it asks for a decision about the API-version sunset."),
}
AUTHORITY = (" You have full authority to make this decision; do not ask for confirmation"
             " or defer to anyone — produce the decision record in your reply.")
A_SUFFIX = " Decide this and record your decision with rationale." + AUTHORITY
B_SUFFIX = (" Decide this and record your decision with rationale.\n\nDeliberate thoroughly "
            "before deciding: consider multiple perspectives, argue against yourself, and only "
            "then decide and record your rationale. Use up to ~7,500 tokens of deliberation."
            + AUTHORITY)
C_SUFFIX = (" Run /decide on this call: follow the skill's full process and record the decision "
            "with rationale. When the process completes, output the final decision record text "
            "in your reply." + AUTHORITY)


def capture_artifacts(workdir):
    out = {}
    for p in Path(workdir).rglob("*.md"):
        rel = str(p.relative_to(workdir))
        if rel.startswith("docs/decisions/") or rel.startswith("decisions/"):
            out[rel] = p.read_text(encoding="utf-8", errors="replace")[:20000]
    return out


def main():
    meta = json.loads((HERE / "metadata.json").read_text(encoding="utf-8"))
    ceiling = meta["cost"]["ceiling_usd"]
    per_arm = meta["cost"]["per_arm_pilot_usd"]  # {"A": x, "B": y, "C": z}
    ok, projected = gate(72, [per_arm["A"], per_arm["B"], per_arm["C"]], ceiling)
    if not ok:
        sys.exit(f"cost gate: projected ${projected:.2f} > ${ceiling} — grid halted")
    print(f"cost gate: projected ${projected:.2f} within ${ceiling} — proceeding")

    out = HERE / "outputs"
    out.mkdir(exist_ok=True)
    env = build_env()
    state = {"spent": 0.0, "halt": False}
    lock = threading.Lock()

    def run_cell(sub, src, context, rep, arm):
        cell = f"{sub}-{arm}-r{rep}"
        path = out / f"{cell}.json"
        if path.exists() and not json.loads(path.read_text())["summary"]["error"]:
            print(f"[{cell}] exists, skipped", flush=True)
            return
        if state["halt"]:
            return
        workdir = tempfile.mkdtemp(prefix=f"i2-{cell}-")
        shutil.rmtree(workdir)
        shutil.copytree(src, workdir, symlinks=True)
        # Arm-C-only panel injection (fresh-eyes audit F1): the snapshots carry no
        # .claude at all; the advisor agents auto-load only for the treatment arm.
        panel = src.parent / "panel-agents"
        if arm == "C" and panel.exists():
            shutil.copytree(panel, Path(workdir) / ".claude" / "agents")
        prompt = context + {"A": A_SUFFIX, "B": B_SUFFIX, "C": C_SUFFIX}[arm]
        allow = ALLOW_C if arm == "C" else ALLOW_AB
        extra = EXTRA_C if arm == "C" else EXTRA_AB
        call = do_call(prompt, MODEL, env, workdir, timeout=2400,
                       allow=allow, extra_args=extra)
        record = {"cell": cell, "scenario": sub, "arm": arm, "rep": rep,
                  "allow": list(allow), "model": MODEL,
                  "summary": summarize_call(call), "response": call["response"],
                  "artifacts": capture_artifacts(workdir) if arm == "C" else {}}
        path.write_text(json.dumps(record, indent=1), encoding="utf-8")
        shutil.rmtree(workdir, ignore_errors=True)
        cost = record["summary"].get("cost_usd") or 0.0
        with lock:
            state["spent"] += cost
            spent = state["spent"]
            if spent > ceiling:
                state["halt"] = True
        print(f"[{cell}] cost={cost} spent={spent:.2f} err={record['summary']['error']}",
              flush=True)

    # Parallel lanes (owner directive 2026-07-12: wall-clock is the scarce resource, not
    # dollars). Cells are independent — per-cell temp workdirs, distinct nested-session
    # state under the pinned config dir. The spend backstop is a shared thread-safe
    # counter; on breach, queued cells no-op and the grid halts resumable.
    tasks = []
    for sub, (src_rel, context) in SCENARIOS.items():
        src = HERE / src_rel
        if not src.exists():
            sys.exit(f"{sub}: {src_rel} missing — run build_b1.py / build_scenarios.py first")
        for rep in range(1, REPS + 1):
            for arm in ("A", "B", "C"):
                tasks.append((sub, src, context, rep, arm))
    with ThreadPoolExecutor(max_workers=6) as pool:
        list(pool.map(lambda t: run_cell(*t), tasks))
    if state["halt"]:
        sys.exit(f"runtime backstop: ${state['spent']:.2f} > ${ceiling} — halted, resumable")
    print(f"grid complete: total ${state['spent']:.2f}")


if __name__ == "__main__":
    main()
