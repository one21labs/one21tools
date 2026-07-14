#!/usr/bin/env python3
"""Poker-arm grid runner (issue #185, ADR 0061; pre-registration: README.md — FROZEN).

72 cells = 8 scenarios x {A, C, P} x 3 reps, resumable (existing non-error output skipped).
Scenario bundles REUSED read-only from the frozen I2 dir; every call runs in its own fresh
temp copy (arm P's advisors each get a private copy — independence is the property under
test). Arm A and C are I2's arms verbatim. Arm P = framer (once per scenario, cached in
framers.json) -> 3 parallel advisors (strict JSON, one retry) -> mechanical reveal ->
round 2 only where round-1 spread >= 2 -> decider with the final anonymized table + arm A's
exact suffix. Fewer than 2 usable advisors = ERROR cell (recorded, resumable) — not arm P.

Modes: `--pilot` runs the B1 framer + 3 P cells under the $10 pilot cap (stops the NEXT
cell past cap); default runs the full grid behind the cost gate (P estimate must be filled
in metadata.json from the pilot).
"""
import argparse
import json
import re
import shutil
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
ALLOW_AP = ("Read", "Grep", "Glob", "Bash", "Write", "Edit")
ALLOW_C = ("Skill", "Task", "Agent") + ALLOW_AP
EXTRA_AP = ("--permission-mode", "acceptEdits")
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

# --- Arm P prompts (pre-registered, FROZEN — README.md) ---
FRAMER_SUFFIX = (
    " Do NOT decide or evaluate this. Enumerate the 2-4 realistic, mutually distinct options "
    "for this call, grounded in the materials here. Return JSON only: {\"options\": [{\"id\": "
    "\"O1\", \"label\": \"<short name>\", \"summary\": \"<=25 words, neutral description>\"}]}. "
    "No pros or cons, no recommendation, no ordering by preference.")
ADVISOR_SUFFIX = (
    "\n\nYou are one of three independent advisors estimating this call. Do NOT decide it. "
    "The candidate options:\n{options}\n\nFor EACH option return: score (an integer 1-5, where "
    "1 = clearly wrong to adopt and 5 = clearly right), a one-line crux (the single "
    "consideration that most drives your score), and THE reversing dependency (the one premise "
    "that, if false, reverses your score). Ground everything in the materials here. Return "
    "JSON only: {{\"estimates\": [{{\"id\": \"O1\", \"score\": 3, \"crux\": \"...\", "
    "\"dependency\": \"...\"}}]}} covering every option.")
ROUND2_SUFFIX = (
    "\n\nYou are one of three independent advisors. Round-1 estimates diverged on the options "
    "below (score spread >= 2). Your own round-1 estimates:\n{own}\n\nAll advisors' anonymized "
    "round-1 estimates and cruxes for the divergent options:\n{table}\n\nRe-estimate ONLY "
    "these divergent options, once — you may keep or change your scores. Return JSON only: "
    "{{\"estimates\": [{{\"id\": \"O1\", \"score\": 3, \"crux\": \"...\", \"dependency\": "
    "\"...\"}}]}} for the divergent options only.")
POKER_BLOCK = (
    "\n\nBefore deciding, three independent advisors estimated each candidate option on a 1-5 "
    "scale (1 = clearly wrong to adopt, 5 = clearly right), each with a one-line crux and the "
    "single premise that would reverse their score. Where estimates diverged (spread >= 2), a "
    "second round re-estimated after an anonymized reveal. The final table:\n\n{table}\n\nNow:")
RETRY_NOTE = ("\n\nYour previous reply was not valid JSON matching the required shape. "
              "Return ONLY the JSON object, nothing else.")


def strip_fence(s):
    s = (s or "").strip()
    if "```" in s:
        for seg in s.split("```"):
            seg = seg.strip()
            if seg.startswith("json"):
                seg = seg[4:].strip()
            if seg.startswith("{"):
                return seg
    m = re.search(r"\{.*\}", s, re.DOTALL)
    return m.group(0) if m else s


def parse_estimates(text, option_ids, subset=None):
    """Validated {id: {score, crux, dependency}} or None. subset limits required coverage."""
    try:
        obj = json.loads(strip_fence(text))
        out = {}
        for e in obj["estimates"]:
            if e["id"] in option_ids and isinstance(e["score"], int) and 1 <= e["score"] <= 5 \
                    and str(e.get("crux", "")).strip() and str(e.get("dependency", "")).strip():
                out[e["id"]] = {"score": e["score"], "crux": str(e["crux"]).strip(),
                                "dependency": str(e["dependency"]).strip()}
        need = set(subset if subset is not None else option_ids)
        return out if need <= set(out) else None
    except Exception:
        return None


def parse_options(text):
    try:
        obj = json.loads(strip_fence(text))
        opts = [{"id": str(o["id"]), "label": str(o["label"]).strip(),
                 "summary": str(o["summary"]).strip()}
                for o in obj["options"] if str(o.get("label", "")).strip()]
        return opts if 2 <= len(opts) <= 4 else None
    except Exception:
        return None


def render_options(options):
    return "\n".join(f"{o['id']}: {o['label']} — {o['summary']}" for o in options)


def render_reveal_table(options, r1, divergent):
    lines = []
    for o in options:
        if o["id"] not in divergent:
            continue
        lines.append(f"{o['id']}: {o['label']}")
        for i, est in enumerate(r1, 1):
            e = est.get(o["id"])
            if e:
                lines.append(f"  Advisor {i}: score {e['score']} — {e['crux']}")
    return "\n".join(lines)


def render_final_table(options, final, r2_ids):
    lines = []
    for o in options:
        mark = " (re-estimated in round 2)" if o["id"] in r2_ids else ""
        lines.append(f"{o['id']}: {o['label']} — {o['summary']}{mark}")
        for i, est in enumerate(final, 1):
            e = est.get(o["id"])
            if e:
                lines.append(f"  Advisor {i}: score {e['score']} | crux: {e['crux']} | "
                             f"reverses if false: {e['dependency']}")
    return "\n".join(lines)


def fresh_copy(src, tag):
    workdir = tempfile.mkdtemp(prefix=f"poker-{tag}-")
    shutil.rmtree(workdir)
    shutil.copytree(src, workdir, symlinks=True)
    return workdir


def capture_artifacts(workdir, src):
    """Every .md the CELL created (absent from the source bundle) — armd defect lesson:
    capture for EVERY arm; never sweep pre-existing corpus files."""
    out = {}
    for p in Path(workdir).rglob("*.md"):
        rel = str(p.relative_to(workdir))
        if not (Path(src) / rel).exists():
            out[rel] = p.read_text(encoding="utf-8", errors="replace")[:20000]
    return out


def json_call(prompt, env, src, tag, timeout, parse):
    """One hermetic call in a private bundle copy; one full retry on parse failure.
    Returns (parsed_or_None, [call, ...])."""
    calls = []
    for attempt, p in enumerate((prompt, prompt + RETRY_NOTE)):
        workdir = fresh_copy(src, f"{tag}-a{attempt}")
        call = do_call(p, MODEL, env, workdir, timeout, allow=ALLOW_AP, extra_args=EXTRA_AP)
        shutil.rmtree(workdir, ignore_errors=True)
        calls.append(call)
        if not call["error"]:
            parsed = parse(call["response"])
            if parsed is not None:
                return parsed, calls
    return None, calls


def get_framer(scenario, context, src, env, lock):
    """One framer call per scenario, serialized (a same-scenario race would mint two option
    sets). Always returns the cached cost so every P cell amortizes framer/REPS honestly."""
    path = HERE / "framers.json"
    with lock:
        cache = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
        if scenario not in cache:
            parsed, calls = json_call(context + FRAMER_SUFFIX, env, src,
                                      f"framer-{scenario}", 900, parse_options)
            cost = sum(summarize_call(c).get("cost_usd") or 0.0 for c in calls)
            if parsed is None:
                sys.exit(f"framer failed for {scenario} after retry — infrastructure, aborting")
            cache[scenario] = {"options": parsed, "cost_usd": round(cost, 4)}
            path.write_text(json.dumps(cache, indent=1), encoding="utf-8")
        return cache[scenario]["options"], cache[scenario]["cost_usd"]


def run_p_cell(scenario, context, src, env, framer_lock):
    """Returns (call_dict_or_error_stub, poker_record, cell_extra_cost)."""
    options, framer_cost = get_framer(scenario, context, src, env, framer_lock)
    ids = [o["id"] for o in options]
    adv_prompt = context + ADVISOR_SUFFIX.format(options=render_options(options))

    with ThreadPoolExecutor(max_workers=3) as pool:
        futs = [pool.submit(json_call, adv_prompt, env, src, f"{scenario}-adv{i}",
                            1200, lambda t: parse_estimates(t, ids)) for i in range(3)]
        r1_results = [f.result() for f in futs]
    r1 = [r for r, _ in r1_results]
    adv_cost = sum(summarize_call(c).get("cost_usd") or 0.0
                   for _, cs in r1_results for c in cs)
    usable = [i for i, r in enumerate(r1) if r is not None]
    if len(usable) < 2:
        return None, {"options": options, "usable_advisors": len(usable)}, adv_cost + framer_cost / REPS

    r1u = [r1[i] for i in usable]
    spread = {oid: max(e[oid]["score"] for e in r1u) - min(e[oid]["score"] for e in r1u)
              for oid in ids}
    divergent = sorted([oid for oid, sp in spread.items() if sp >= 2])

    final = [dict(e) for e in r1u]
    r2_records, r2_cost = [], 0.0
    if divergent:
        table = render_reveal_table(options, r1u, divergent)
        with ThreadPoolExecutor(max_workers=3) as pool:
            futs = []
            for k, est in enumerate(r1u):
                own = json.dumps({oid: est[oid] for oid in divergent})
                prompt = context + ROUND2_SUFFIX.format(own=own, table=table)
                futs.append(pool.submit(json_call, prompt, env, src,
                                        f"{scenario}-r2adv{k}", 900,
                                        lambda t: parse_estimates(t, ids, subset=divergent)))
            r2_results = [f.result() for f in futs]
        for k, (parsed, calls) in enumerate(r2_results):
            r2_cost += sum(summarize_call(c).get("cost_usd") or 0.0 for c in calls)
            deltas = {}
            if parsed:
                for oid in divergent:
                    deltas[oid] = parsed[oid]["score"] - r1u[k][oid]["score"]
                    final[k][oid] = parsed[oid]
            r2_records.append({"advisor": k, "parsed": parsed is not None, "deltas": deltas,
                               "estimates": parsed})

    decider_workdir = fresh_copy(src, f"{scenario}-decider")
    prompt = context + POKER_BLOCK.format(
        table=render_final_table(options, final, set(divergent))) + A_SUFFIX
    call = do_call(prompt, MODEL, env, decider_workdir, 2400, allow=ALLOW_AP, extra_args=EXTRA_AP)
    artifacts = capture_artifacts(decider_workdir, src)
    shutil.rmtree(decider_workdir, ignore_errors=True)
    poker = {"options": options, "usable_advisors": len(usable),
             "round1": r1u, "reveal_spread": spread, "divergent": divergent,
             "round2": r2_records, "final": final}
    extra = adv_cost + r2_cost + framer_cost / REPS
    return (call, artifacts), poker, extra


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pilot", action="store_true", help="B1 framer + 3 P cells under the pilot cap")
    args = ap.parse_args()

    meta = json.loads((HERE / "metadata.json").read_text(encoding="utf-8"))
    ceiling = meta["cost"]["ceiling_usd"]
    out = HERE / ("pilot-outputs" if args.pilot else "outputs")
    out.mkdir(exist_ok=True)
    env = build_env()
    state = {"spent": 0.0, "halt": False}
    lock = threading.Lock()
    framer_lock = threading.Lock()
    cap = meta["cost"]["pilot_cap_usd"] if args.pilot else ceiling

    if not args.pilot:
        per = meta["cost"]["per_arm_estimate_usd"]
        if per["P"] is None:
            sys.exit("cost gate: metadata per_arm_estimate_usd.P is null — run --pilot first")
        ok, projected = gate(72, [per["A"], per["C"], per["P"]], ceiling)
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
        poker, extra_cost, artifacts = {}, 0.0, {}
        if arm == "P":
            res, poker, extra_cost = run_p_cell(sub, context, src, env, framer_lock)
            if res is None:
                call = {"response": "", "envelope": None, "duration_s": 0.0, "retried": False,
                        "error": f"advisor floor: {poker['usable_advisors']}/3 usable",
                        "timestamps": {}}
            else:
                call, artifacts = res
        else:
            workdir = fresh_copy(src, cell)
            panel = src.parent / "panel-agents"
            if arm == "C" and panel.exists():
                shutil.copytree(panel, Path(workdir) / ".claude" / "agents")
            prompt = context + (C_SUFFIX if arm == "C" else A_SUFFIX)
            allow = ALLOW_C if arm == "C" else ALLOW_AP
            extra = EXTRA_C if arm == "C" else EXTRA_AP
            call = do_call(prompt, MODEL, env, workdir, timeout=2400,
                           allow=allow, extra_args=extra)
            artifacts = capture_artifacts(workdir, src)
            shutil.rmtree(workdir, ignore_errors=True)
        summary = summarize_call(call)
        summary["cell_cost_usd"] = (summary.get("cost_usd") or 0.0) + extra_cost
        record = {"cell": cell, "scenario": sub, "arm": arm, "rep": rep, "model": MODEL,
                  "summary": summary, "response": call["response"], "poker": poker,
                  "artifacts": artifacts}
        path.write_text(json.dumps(record, indent=1), encoding="utf-8")
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
            tasks.append(("B1", src, SCENARIOS["B1"][1], rep, "P"))
    else:
        for sub, (src_rel, context) in SCENARIOS.items():
            src = I2 / src_rel
            if not src.exists():
                sys.exit(f"{sub}: {src_rel} missing from the frozen I2 dir")
            for rep in range(1, REPS + 1):
                for arm in ("A", "C", "P"):
                    tasks.append((sub, src, context, rep, arm))
    with ThreadPoolExecutor(max_workers=2 if args.pilot else 4) as pool:
        list(pool.map(lambda t: run_cell(*t), tasks))
    if state["halt"]:
        sys.exit(f"backstop: ${state['spent']:.2f} > ${cap} — halted, resumable")
    print(f"{'pilot' if args.pilot else 'grid'} complete: total ${state['spent']:.2f}")


if __name__ == "__main__":
    main()
