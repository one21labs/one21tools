#!/usr/bin/env python3
"""Aggregate blind grader verdicts into a keep/cut verdict for the ablated section.

Inputs (in graded/):
  verdicts.json  -> {bid: {"pass": bool, "behavior": str, "evidence": str}}  (blind grader output)
  arm_map.json   -> {bid: {"task","arm","rep"}}

Method (ADR 0019): per task, pass-rate WITH minus WITHOUT = the section's marginal effect; each task
is one clustered observation (replicates within a task are correlated). Headline = the mean per-task
delta with a 95% CI across tasks, plus a Wilson CI on the win-proportion among non-tied tasks.

Keep/cut bar (ADR 0019 Tier 2): the section earns its always-loaded cost only if adding it moves the
delta beyond noise. CI on the mean delta excludes 0 and is positive -> KEEP. CI includes 0 -> CUT
CANDIDATE (no measurable benefit). <4 non-tied tasks -> width warning.
Writes results.jsonl (per-task rows + summary) for the snapshot; prints the verdict.
"""
import json, math, os, statistics

BASE = os.path.dirname(os.path.abspath(__file__))
G = os.path.join(BASE, "graded")
with open(os.path.join(G, "verdicts.json"), encoding="utf-8") as fh:
    verdicts = json.load(fh)
with open(os.path.join(G, "arm_map.json"), encoding="utf-8") as fh:
    arm_map = json.load(fh)


def wilson(k, n, z=1.96):
    if n == 0:
        return (0.0, 1.0)
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (max(0.0, c - h), min(1.0, c + h))


# group pass booleans by (task, arm)
cells = {}
for bid, meta in arm_map.items():
    v = verdicts.get(bid)
    if v is None:
        continue
    cells.setdefault((meta["task"], meta["arm"]), []).append(1 if v.get("pass") else 0)

tasks = sorted({t for (t, _) in cells})
rows, deltas, wins, losses, ties = [], [], 0, 0, 0
for t in tasks:
    w = cells.get((t, "with"), [])
    wo = cells.get((t, "without"), [])
    wr = sum(w) / len(w) if w else float("nan")
    wor = sum(wo) / len(wo) if wo else float("nan")
    delta = wr - wor
    deltas.append(delta)
    cls = "win" if delta > 0 else ("loss" if delta < 0 else "tie")
    wins += cls == "win"; losses += cls == "loss"; ties += cls == "tie"
    rows.append({"task": t, "with_n": len(w), "without_n": len(wo),
                 "with_pass_rate": round(wr, 3), "without_pass_rate": round(wor, 3),
                 "delta": round(delta, 3), "class": cls})

n = len(deltas)
mean_delta = statistics.fmean(deltas) if deltas else 0.0
sd = statistics.stdev(deltas) if n > 1 else 0.0
se = sd / math.sqrt(n) if n else 0.0
ci_lo, ci_hi = mean_delta - 1.96 * se, mean_delta + 1.96 * se
non_tied = wins + losses
wp_lo, wp_hi = wilson(wins, non_tied)

if non_tied < 4:
    warn = f"WIDTH WARNING: only {non_tied} non-tied tasks (<4 floor) — interval is wide, treat as directional."
else:
    warn = ""

if n and ci_lo > 0:
    verdict = "KEEP — adding the section improves judgment-call flagging beyond noise."
elif n and ci_hi < 0:
    verdict = "HARMFUL — the section REDUCES flagging (investigate)."
elif n and abs(mean_delta) < 0.05 and ci_lo <= 0 <= ci_hi:
    verdict = "CUT CANDIDATE — no measurable benefit (mean delta within noise of zero)."
else:
    verdict = "INCONCLUSIVE — CI straddles zero; add replicates/tasks or iterate the section."

summary = {"record": "summary", "tasks": n, "mean_delta": round(mean_delta, 3),
           "delta_ci95": [round(ci_lo, 3), round(ci_hi, 3)],
           "wins": wins, "losses": losses, "ties": ties,
           "win_proportion_ci95": [round(wp_lo, 3), round(wp_hi, 3)],
           "verdict": verdict, "warning": warn}

with open(os.path.join(BASE, "results.jsonl"), "w", encoding="utf-8") as fh:
    for r in rows:
        fh.write(json.dumps({"record": "task", **r}) + "\n")
    fh.write(json.dumps(summary) + "\n")

print("=== per-task (with - without) ===")
for r in rows:
    print(f"  {r['task']:22} with={r['with_pass_rate']:.2f} without={r['without_pass_rate']:.2f} "
          f"delta={r['delta']:+.2f} [{r['class']}]")
print(f"\nmean delta = {mean_delta:+.3f}  95% CI [{ci_lo:+.3f}, {ci_hi:+.3f}]  "
      f"(wins {wins} / losses {losses} / ties {ties})")
print(f"win-proportion 95% CI (non-tied) [{wp_lo:.2f}, {wp_hi:.2f}]")
if warn:
    print(warn)
print(f"\nVERDICT: {verdict}")
