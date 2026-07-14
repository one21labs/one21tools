#!/usr/bin/env python3
"""Arm-D grid runner (issue #180, ADR 0057 routing; pre-registration: README.md — frozen).

72 cells = 8 scenarios x {A, C, D} x 3 reps, resumable (existing non-error output skipped).
Scenario bundles are REUSED read-only from the frozen I2 dir (../2026-07-12-pdca-decide-outcome);
every cell still runs in a fresh temp copy. Arm A and C are I2's arms verbatim (fresh re-run for
a same-run comparison). Arm D = two independent probe calls (premortem, assumption-hunt) on the
bundle, fresh and unprimed, then a decider call carrying both probe reports verbatim + arm A's
exact suffix. A D cell with fewer than 2 successful probe reports is an error cell (recorded,
resumable) — it is not arm D.

Modes: `--pilot` runs 3 D cells on B1 under the $8 pilot cap (stops the NEXT cell past cap);
default runs the full grid behind the cost gate (D estimate must be filled in metadata.json).
"""
import argparse
import json
import shutil
import subprocess
import sys
import tempfile
import threading
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
sys.path.insert(0, str(REPO / "skill-bench" / "scripts" / "lib"))
from cost_gate import gate  # noqa: E402
from hermetic_driver import build_env, do_call, summarize_call  # noqa: E402

I2 = HERE.parent / "2026-07-12-pdca-decide-outcome"
REPS = 3
MODEL = "sonnet"
ALLOW_AD = ("Read", "Grep", "Glob", "Bash", "Write", "Edit")
ALLOW_C = ("Skill", "Task", "Agent") + ALLOW_AD
EXTRA_AD = ("--permission-mode", "acceptEdits")
EXTRA_C = ("--plugin-dir", str(REPO / "pdca-workflow"), "--permission-mode", "acceptEdits")

# I2's scenario contexts verbatim (source: ../2026-07-12-pdca-decide-outcome/grid_i2.py).
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
C_SUFFIX = (" Run /decide on this call: follow the skill's full process and record the decision "
            "with rationale. When the process completes, output the final decision record text "
            "in your reply." + AUTHORITY)
# Arm D (pre-registered, FROZEN — README.md; iteration edits land here with a log entry).
PREMORTEM_SUFFIX = (
    " Do NOT decide this. Premortem only: assume a decision on this call shipped and FAILED "
    "six months later. Name the 2-3 most plausible failure classes that killed it — concrete "
    "mechanisms grounded in the materials here (cite the file or fact each rides on), not "
    "generic risks. One short paragraph each.")
ASSUMPTION_SUFFIX = (
    " Do NOT decide this. Assumption hunt only: list the realistic options for this call, and "
    "for EACH option name the single load-bearing dependency — the one premise that, if false, "
    "reverses the choice. State each as 'if X is false, option Y flips'. Ground each in the "
    "materials here; be terse.")
# Iteration 2 (README iteration log): integration requirement added — iteration-1 deciders
# deflected to process assumptions on backtests; the probes' substance never reached the record.
PROBE_BLOCK = ("\n\nBefore deciding, two independent probes examined the same materials without "
               "seeing each other or any draft decision. Weigh their reports:\n\n"
               "--- PREMORTEM PROBE ---\n{p1}\n\n--- ASSUMPTION PROBE ---\n{p2}\n\n"
               "Your decision record must state, for the option you choose: THE single "
               "load-bearing assumption — the one premise about the call's subject matter that, "
               "if false, reverses this decision — and the failure class you are accepting. "
               "Ground both in the substance of the call (never in process, tooling, or "
               "formatting concerns), drawing on the probe reports where they hold up. Now:")


def capture_artifacts(workdir, src):
    """Every .md the CELL created (absent from the source bundle) — deciders in ANY arm may
    write the decision to a file (e.g. a root DECISION.md) and reply with a pointer; the
    I2 lesson still holds in the other direction: never sweep pre-existing corpus files."""
    out = {}
    for p in Path(workdir).rglob("*.md"):
        rel = str(p.relative_to(workdir))
        if not (Path(src) / rel).exists():
            out[rel] = p.read_text(encoding="utf-8", errors="replace")[:20000]
    return out


def fresh_copy(src, cell):
    workdir = tempfile.mkdtemp(prefix=f"armd-{cell}-")
    shutil.rmtree(workdir)
    shutil.copytree(src, workdir, symlinks=True)
    return workdir


def run_d_cell(context, env, workdir):
    """Two independent probes (parallel, same bundle, unprimed) then the decider."""
    with ThreadPoolExecutor(max_workers=2) as pool:
        f1 = pool.submit(do_call, context + PREMORTEM_SUFFIX, MODEL, env, workdir,
                         1800, allow=ALLOW_AD, extra_args=EXTRA_AD)
        f2 = pool.submit(do_call, context + ASSUMPTION_SUFFIX, MODEL, env, workdir,
                         1800, allow=ALLOW_AD, extra_args=EXTRA_AD)
        p1, p2 = f1.result(), f2.result()
    if p1["error"] or p2["error"]:
        return None, p1, p2
    prompt = context + PROBE_BLOCK.format(p1=p1["response"], p2=p2["response"]) + A_SUFFIX
    call = do_call(prompt, MODEL, env, workdir, 2400, allow=ALLOW_AD, extra_args=EXTRA_AD)
    return call, p1, p2


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pilot", action="store_true", help="3 D cells on B1 under the pilot cap")
    args = ap.parse_args()

    meta = json.loads((HERE / "metadata.json").read_text(encoding="utf-8"))
    ceiling = meta["cost"]["ceiling_usd"]
    out = HERE / ("pilot-outputs" if args.pilot else "outputs")
    out.mkdir(exist_ok=True)
    env = build_env()
    state = {"spent": 0.0, "halt": False}
    lock = threading.Lock()
    cap = meta["cost"]["pilot_cap_usd"] if args.pilot else ceiling

    if not args.pilot:
        per = meta["cost"]["per_arm_estimate_usd"]
        if per["D"] is None:
            sys.exit("cost gate: metadata per_arm_estimate_usd.D is null — run --pilot first")
        ok, projected = gate(72, [per["A"], per["C"], per["D"]], ceiling)
        if not ok:
            sys.exit(f"cost gate: projected ${projected:.2f} > ${ceiling} — grid halted")
        print(f"cost gate: projected ${projected:.2f} within ${ceiling} — proceeding")

    def run_cell(sub, src, context, rep, arm):
        cell = f"{sub}-{arm}-r{rep}"
        path = out / f"{cell}.json"
        if path.exists() and not json.loads(path.read_text())["summary"]["error"]:
            print(f"[{cell}] exists, skipped", flush=True)
            return
        if state["halt"]:
            return
        workdir = fresh_copy(src, cell)
        probes = {}
        if arm == "D":
            call, p1, p2 = run_d_cell(context, env, workdir)
            probes = {"premortem": summarize_call(p1) | {"response": p1["response"]},
                      "assumption": summarize_call(p2) | {"response": p2["response"]}}
            if call is None:
                call = {"response": "", "envelope": None, "duration_s": 0.0, "retried": False,
                        "error": "probe failure: " + (p1["error"] or p2["error"] or "?"),
                        "timestamps": {}}
        else:
            panel = src.parent / "panel-agents"
            if arm == "C" and panel.exists():
                shutil.copytree(panel, Path(workdir) / ".claude" / "agents")
            prompt = context + (C_SUFFIX if arm == "C" else A_SUFFIX)
            allow = ALLOW_C if arm == "C" else ALLOW_AD
            extra = EXTRA_C if arm == "C" else EXTRA_AD
            call = do_call(prompt, MODEL, env, workdir, timeout=2400,
                           allow=allow, extra_args=extra)
        summary = summarize_call(call)
        probe_cost = sum((probes.get(k) or {}).get("cost_usd") or 0.0 for k in probes)
        summary["cell_cost_usd"] = (summary.get("cost_usd") or 0.0) + probe_cost
        # Artifacts captured for EVERY arm: A/D deciders may also write their decision to a
        # file and reply with a pointer (defect found post-grading iteration 1: 4 cells graded
        # on a stub while the written decision was lost with the workdir; run log 2026-07-13).
        record = {"cell": cell, "scenario": sub, "arm": arm, "rep": rep, "model": MODEL,
                  "summary": summary, "response": call["response"], "probes": probes,
                  "artifacts": capture_artifacts(workdir, src)}
        path.write_text(json.dumps(record, indent=1), encoding="utf-8")
        shutil.rmtree(workdir, ignore_errors=True)
        with lock:
            state["spent"] += summary["cell_cost_usd"]
            spent = state["spent"]
            if spent > cap:
                state["halt"] = True
        print(f"[{cell}] cost={summary['cell_cost_usd']:.3f} spent={spent:.2f} "
              f"err={summary['error']}", flush=True)

    tasks = []
    if args.pilot:
        src = I2 / SCENARIOS["B1"][0]
        for rep in range(1, 4):
            tasks.append(("B1", src, SCENARIOS["B1"][1], rep, "D"))
    else:
        for sub, (src_rel, context) in SCENARIOS.items():
            src = I2 / src_rel
            if not src.exists():
                sys.exit(f"{sub}: {src_rel} missing from the frozen I2 dir")
            for rep in range(1, REPS + 1):
                for arm in ("A", "C", "D"):
                    tasks.append((sub, src, context, rep, arm))
    with ThreadPoolExecutor(max_workers=2 if args.pilot else 6) as pool:
        list(pool.map(lambda t: run_cell(*t), tasks))
    if state["halt"]:
        sys.exit(f"backstop: ${state['spent']:.2f} > ${cap} — halted, resumable")
    print(f"{'pilot' if args.pilot else 'grid'} complete: total ${state['spent']:.2f}")


if __name__ == "__main__":
    main()
