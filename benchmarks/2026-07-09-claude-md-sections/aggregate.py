#!/usr/bin/env python3
"""Per-section KEEP/CUT verdict for the CLAUDE.md-section ablation.

Each task is graded against its SINGLE pass_criterion (ADR 0019 binary), 3 reps/arm. Per-task delta =
mean(pass WITH) - mean(pass WITHOUT); per-section headline = mean per-task delta + 95% CI clustered
over the section's tasks (each task = one observation). KEEP if the CI excludes 0 and is positive
(ADR 0024). Reads graded/arm_map.tsv (bid<TAB>key<TAB>section<TAB>task_id<TAB>arm<TAB>rep) plus any
graded/arm_map-*.tsv extensions (same schema; a re-run's rows under a fresh bid namespace, issue
#72 -- a later-loaded row for the SAME (section,task_id,arm,rep) slot SUPERSEDES the original row
for cell aggregation, it does not add a second observation; a slot with no extension is untouched)
+ graded/verdicts.jsonl (minified, one {bid,pass,met,total,evidence} per line = grade.workflow.js's
returned array). Writes results.jsonl (minified).
"""
import glob, json, math, os, statistics, sys

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(BASE, "..", "lib"))
from verdict import verdict_of  # ADR 0026 shared lib; dedup of the verbatim-duplicate def (#43, #57)

G = os.path.join(BASE, "graded")

def load_arm_map_rows(path):
    """Parse one arm_map TSV (header row then bid key section task_id arm rep) into a row list."""
    rows = []
    with open(path, encoding="utf-8", newline="") as fh:
        header = fh.readline().rstrip("\n").split("\t")
        for line in fh:
            cells = line.rstrip("\n").split("\t")
            if len(cells) != len(header):
                continue
            rows.append(dict(zip(header, cells)))
    return rows


# arm_map.tsv: header row then bid  key  section  task_id  arm  rep
arm_map_rows = load_arm_map_rows(os.path.join(G, "arm_map.tsv"))

# arm_map extensions (issue #72): a re-run of a subset of cells (new task ids, or a redesigned
# task under a fresh bid namespace to avoid colliding with the original run's bids) adds its rows
# via a SEPARATE dated graded/arm_map-*.tsv file instead of touching the original arm_map.tsv --
# mirrors the verdicts-*-regrade.jsonl overlay convention below (append-only, every file stays
# committed). Loaded in sorted-filename order AFTER the base file so supersession (below) is
# deterministic.
for am in sorted(glob.glob(os.path.join(G, "arm_map-*.tsv"))):
    arm_map_rows += load_arm_map_rows(am)

arm_map = {r["bid"]: r for r in arm_map_rows}   # bid -> row, for verdict/evidence lookup by bid

# Slot supersession: a (section, task_id, arm, rep) SLOT identifies one cell observation. A
# same-task_id re-run (a redesigned pass_criterion under the same task id, e.g. ADR 0034) reuses a
# slot under a NEW bid -- because it was loaded after the base file, it OVERWRITES that slot here,
# so cell aggregation counts exactly one observation per slot (the newest), never blending an
# old-criteria pass/fail with a new-criteria one. A slot with no re-run is untouched. A brand-new
# task id (no prior slot) simply adds one.
slot_bid = {}
for r in arm_map_rows:
    slot_bid[(r["section"], r["task_id"], r["arm"], r["rep"])] = r["bid"]

# verdicts.jsonl: one {bid, pass, met, total, evidence} per line
verdicts = {}
with open(os.path.join(G, "verdicts.jsonl"), encoding="utf-8") as fh:
    for line in fh:
        line = line.strip()
        if not line:
            continue
        v = json.loads(line)
        verdicts[v["bid"]] = v

# Dated verdict overlays supersede the original verdicts per bid: verdicts-*-regrade.jsonl
# (issues #49/#50, recalibrated never criteria + the prosecutor-evidence fix) and
# verdicts-*-neverrerun.jsonl (issue #72, the ADR 0034 never-task re-run's fresh bids -- these
# never collide with an original bid, so "supersede" here just means "add", per bid; the SLOT
# supersession that matters for the redesigned n1/n2/n3/n4 task ids is handled above via
# slot_bid). Every file stays committed, append-only per ADR 0019.
for rg in sorted(glob.glob(os.path.join(G, "verdicts-*.jsonl"))):
    with open(rg, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                v = json.loads(line)
                verdicts[v["bid"]] = v


# per (section, task, arm) -> list of 1/0 (pass) over reps. One bid per (section,task_id,arm,rep)
# SLOT (slot_bid, resolved above) -- never the raw arm_map -- so a re-run's superseding bid
# contributes exactly one observation to the cell, not an extra one alongside the row it replaced.
cell = {}
for (section, task_id, arm, rep), bid in slot_bid.items():
    v = verdicts.get(bid)
    if v is None:
        continue
    cell.setdefault((section, task_id, arm), []).append(1 if v.get("pass") else 0)

sections = sorted({s for (s, _, _) in cell})
rows, summaries, all_d = [], [], []
for sec in sections:
    tasks = sorted({t for (s, t, _) in cell if s == sec})
    deltas, w, l, t = [], 0, 0, 0
    for tk in tasks:
        wi = cell.get((sec, tk, "with"), []); wo = cell.get((sec, tk, "without"), [])
        wr = statistics.fmean(wi) if wi else float("nan")
        wor = statistics.fmean(wo) if wo else float("nan")
        d = wr - wor
        deltas.append(d); all_d.append(d)
        cls = "win" if d > 1e-9 else ("loss" if d < -1e-9 else "tie")
        w += cls == "win"; l += cls == "loss"; t += cls == "tie"
        rows.append({"record": "task", "section": sec, "task_id": tk, "with": round(wr, 3),
                     "without": round(wor, 3), "delta": round(d, 3), "class": cls})
    n = len(deltas); mean = statistics.fmean(deltas) if n else 0.0
    sd = statistics.stdev(deltas) if n > 1 else 0.0; se = sd / math.sqrt(n) if n else 0.0
    lo, hi = mean - 1.96 * se, mean + 1.96 * se
    summaries.append({"record": "section", "section": sec, "tasks": n, "mean_delta": round(mean, 3),
                      "delta_ci95": [round(lo, 3), round(hi, 3)], "wins": w, "losses": l, "ties": t,
                      "verdict": verdict_of(mean, lo, hi, n), "ci_halfwidth": round(1.96 * se, 3)})

N = len(all_d); om = statistics.fmean(all_d) if N else 0.0
osd = statistics.stdev(all_d) if N > 1 else 0.0; ose = osd / math.sqrt(N) if N else 0.0
olo, ohi = om - 1.96 * ose, om + 1.96 * ose
overall = {"record": "overall", "tasks": N, "mean_delta": round(om, 3),
           "delta_ci95": [round(olo, 3), round(ohi, 3)], "verdict": verdict_of(om, olo, ohi, N)}

with open(os.path.join(BASE, "results.jsonl"), "w", encoding="utf-8", newline="") as fh:
    for r in rows + summaries + [overall]:
        fh.write(json.dumps(r, separators=(",", ":")) + "\n")

for s in summaries:
    print(f"\n=== {s['section']} ===")
    for r in [r for r in rows if r["section"] == s["section"]]:
        print(f"  {r['task_id']:<24} with={r['with']:.2f} without={r['without']:.2f} "
              f"delta={r['delta']:+.2f} [{r['class']}]")
    print(f"  mean {s['mean_delta']:+.3f} CI [{s['delta_ci95'][0]:+.3f},{s['delta_ci95'][1]:+.3f}] "
          f"({s['wins']}W/{s['losses']}L/{s['ties']}T) -> {s['verdict']}")
print(f"\n=== OVERALL === mean {overall['mean_delta']:+.3f} "
      f"CI [{overall['delta_ci95'][0]:+.3f},{overall['delta_ci95'][1]:+.3f}] -> {overall['verdict']}")
