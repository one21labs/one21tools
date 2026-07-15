#!/usr/bin/env python3
"""#186 Phase-0 DoD check runner (pre-registration: README.md — frozen; ADR 0061).

Zero generation spend: reads the two frozen graded corpora, classifies items 1-2 dual-family
(claude sonnet + grok-4.5), applies the mechanical predicates for items 3-4, buckets
within-arm/within-corpus, and emits dod.jsonl + results.json.

Modes: `--classify` runs the classifier calls (resumable; per-cell records appended to
dod.jsonl as they land); `--aggregate` computes results.json from dod.jsonl. Pure decision
logic (predicates, three-state, H1) lives in module functions tested by dod_check_test.py.
"""
import argparse
import json
import re
import sys
import threading
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
sys.path.insert(0, str(REPO / "skill-bench" / "scripts" / "lib"))

CORPORA = {
    "outcome": HERE.parent / "2026-07-12-pdca-decide-outcome",
    "armd": HERE.parent / "2026-07-13-pdca-decide-armd",
}
THRESHOLD = 0.15
MIN_BUCKET = 5
MAX_SHARE = 0.90
HARD_PAIR = (3, 4)

CLASSIFIER_PROMPT = """You are classifying a decision record's stated content. Answer two \
independent boolean questions about it. Judge only what is stated; do not reward or penalize \
style.

Decision: {decision}

Stated assumptions:
{assumptions}

Stated risks:
{risks}

item1: Does at least one stated assumption or risk name a FALSIFIABLE SUBJECT-MATTER \
assumption — a premise about the decision's real-world costs, benefits, or mechanism that \
could later be shown true or false? Premises about process, tooling, measurement, formatting, \
or sequencing do NOT count.

item2: Does the record name at least one ACCEPTED FAILURE CLASS — a concrete way this \
decision could fail that the decider acknowledges and accepts proceeding despite?

Return JSON only: {{"item1": true/false, "why1": "<=20 words", "item2": true/false, \
"why2": "<=20 words"}}"""

CLASSIFIER_SCHEMA = {
    "type": "object",
    "properties": {
        "item1": {"type": "boolean"}, "why1": {"type": "string"},
        "item2": {"type": "boolean"}, "why2": {"type": "string"},
    },
    "required": ["item1", "why1", "item2", "why2"],
}


# --- frozen mechanical predicates (items 3-4) ---

def item3_criterion(criterion):
    """Falsifiable acceptance/reopen criterion: non-empty + a testability marker."""
    c = (criterion or "").strip()
    if not c:
        return False
    return bool(re.search(r"\d|>=|<=|>|<|%|\bif\b|\bwhen\b|\bunless\b|\breopen\b|\brevisit\b",
                          c, re.IGNORECASE))


def item4_rejected(options):
    """>=1 rejected alternative WITH a reason: a reject-marked entry carrying >=15 chars
    of substance beyond the marker."""
    for entry in options or []:
        m = re.search(r"reject\w*\b(.*)$", entry, re.IGNORECASE | re.DOTALL)
        if m and len(m.group(1).strip(" :—–-")) >= 15:
            return True
    return False


def render_prompt(norm):
    def numbered(xs):
        xs = [x for x in (xs or []) if str(x).strip()]
        return "\n".join(f"{i}. {x}" for i, x in enumerate(xs, 1)) if xs else "(none stated)"
    return CLASSIFIER_PROMPT.format(
        decision=(norm.get("decision") or "(none stated)").strip()[:2000],
        assumptions=numbered(norm.get("assumptions"))[:4000],
        risks=numbered(norm.get("risks"))[:4000])


# --- pure decision logic (tested) ---

def cell_dod(rec, family):
    v = rec["classifier"][family]
    return bool(v["item1"] and v["item2"] and rec["item3"] and rec["item4"])


def bucket_arm(cells, fm_key="fm_full"):
    """cells: list of dicts with dod_pass (agreed families) and fraction-met values.
    Returns the arm's three-state record."""
    included = [c for c in cells if not c["excluded"]]
    n_pass = [c for c in included if c["dod_pass"]]
    n_fail = [c for c in included if not c["dod_pass"]]
    out = {"n": len(cells), "excluded": len(cells) - len(included),
           "n_pass": len(n_pass), "n_fail": len(n_fail)}
    if not included:
        out.update(state="INCONCLUSIVE", delta=None)
        return out
    share = max(len(n_pass), len(n_fail)) / len(included)
    if min(len(n_pass), len(n_fail)) >= MIN_BUCKET and share <= MAX_SHARE:
        mean = lambda xs: sum(x[fm_key] for x in xs) / len(xs)  # noqa: E731
        out.update(state="TESTED",
                   delta=round(mean(n_pass) - mean(n_fail), 4),
                   mean_pass=round(mean(n_pass), 4), mean_fail=round(mean(n_fail), 4))
    else:
        out.update(state="INCONCLUSIVE", delta=None, skew=round(share, 3))
    return out


def corpus_verdict(arm_records):
    tested = {a: r for a, r in arm_records.items() if r["state"] == "TESTED"}
    if not tested:
        return "INCONCLUSIVE"
    if any(r["delta"] < THRESHOLD for r in tested.values()):
        return "FALSIFYING"
    return "SUPPORTED"


def h1_verdict(corpus_verdicts):
    vs = list(corpus_verdicts.values())
    if "FALSIFYING" in vs:
        return "FALSIFIED"
    if all(v == "SUPPORTED" for v in vs):
        return "SUPPORTED"
    return "INCONCLUSIVE"


# --- IO + runner ---

def load_corpus(path):
    cells = [json.loads(l) for l in (path / "graded" / "verdicts.jsonl").read_text(
        encoding="utf-8").splitlines() if l.strip()]
    amap = {}
    for line in (path / "graded" / "arm_map.tsv").read_text(encoding="utf-8").splitlines()[1:]:
        f = line.split("\t")
        amap[f[0]] = f[1]
    return cells, amap


def fraction_met(expectations, ids=None):
    xs = [e for e in expectations if ids is None or e["id"] in ids]
    return sum(1 for e in xs if e["met"]) / len(xs)


def classify(args):
    from judge import ClaudeJudge, GrokJudge
    judges = {"claude": ClaudeJudge(model="sonnet"), "grok": GrokJudge()}
    out_path = HERE / "dod.jsonl"
    done = set()
    if out_path.exists():
        for line in out_path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                r = json.loads(line)
                done.add((r["corpus"], r["bid"]))
    lock = threading.Lock()

    def run_cell(corpus, cell, arm):
        key = (corpus, cell["bid"])
        if key in done:
            return
        norm = cell["norm"]
        prompt = render_prompt(norm)
        cls = {}
        for fam, judge in judges.items():
            try:
                cls[fam] = judge.grade(prompt, CLASSIFIER_SCHEMA)
            except Exception as e:  # recorded, not silently dropped
                cls[fam] = {"error": str(e)[:500]}
        rec = {"corpus": corpus, "bid": cell["bid"], "arm": arm,
               "scenario": cell["scenario"],
               "item3": item3_criterion(norm.get("criterion")),
               "item4": item4_rejected(norm.get("options")),
               "classifier": cls,
               "fm_full": fraction_met(cell["expectations"]),
               "fm_hard": fraction_met(cell["expectations"], HARD_PAIR)}
        with lock:
            with open(out_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(rec) + "\n")
        print(f"[{corpus}/{cell['bid']}] item3={rec['item3']} item4={rec['item4']}", flush=True)

    tasks = []
    for corpus, path in CORPORA.items():
        cells, amap = load_corpus(path)
        for cell in cells:
            tasks.append((corpus, cell, amap[cell["bid"]]))
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        list(pool.map(lambda t: run_cell(*t), tasks))
    for fam, judge in judges.items():
        print(f"{fam}: calls={judge.calls} notional=${judge.cost_usd():.4f}")


def aggregate():
    recs = [json.loads(l) for l in (HERE / "dod.jsonl").read_text(
        encoding="utf-8").splitlines() if l.strip()]
    results = {"threshold": THRESHOLD, "min_bucket": MIN_BUCKET, "max_share": MAX_SHARE,
               "corpora": {}, "diagnostic_hard_pair": {}, "disagreements": [],
               "classifier_errors": []}
    for corpus in CORPORA:
        rows = [r for r in recs if r["corpus"] == corpus]
        by_arm, by_arm_diag = {}, {}
        for arm in sorted({r["arm"] for r in rows}):
            cells = []
            for r in (x for x in rows if x["arm"] == arm):
                errs = [f for f in ("claude", "grok") if "error" in r["classifier"][f]]
                if errs:
                    results["classifier_errors"].append(
                        {"corpus": corpus, "bid": r["bid"], "families": errs})
                    cells.append({"excluded": True, "dod_pass": None,
                                  "fm_full": r["fm_full"], "fm_hard": r["fm_hard"]})
                    continue
                votes = {f: cell_dod(r, f) for f in ("claude", "grok")}
                agree = votes["claude"] == votes["grok"]
                if not agree:
                    results["disagreements"].append(
                        {"corpus": corpus, "bid": r["bid"], "arm": arm, "votes": votes})
                cells.append({"excluded": not agree, "dod_pass": votes["claude"],
                              "fm_full": r["fm_full"], "fm_hard": r["fm_hard"]})
            by_arm[arm] = bucket_arm(cells, "fm_full")
            by_arm_diag[arm] = bucket_arm(cells, "fm_hard")
        results["corpora"][corpus] = {"arms": by_arm, "verdict": corpus_verdict(by_arm)}
        results["diagnostic_hard_pair"][corpus] = {
            "arms": by_arm_diag, "verdict": corpus_verdict(by_arm_diag)}
    results["h1"] = h1_verdict({c: v["verdict"] for c, v in results["corpora"].items()})
    results["h1_diagnostic_note"] = ("diagnostic informs a REOPEN only; never overrides "
                                     "the full-fraction kill (ADR 0061 1d)")
    (HERE / "results.json").write_text(json.dumps(results, indent=1), encoding="utf-8")
    print(json.dumps({"h1": results["h1"],
                      "corpora": {c: v["verdict"] for c, v in results["corpora"].items()},
                      "disagreements": len(results["disagreements"]),
                      "errors": len(results["classifier_errors"])}, indent=1))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--classify", action="store_true")
    ap.add_argument("--aggregate", action="store_true")
    ap.add_argument("--workers", type=int, default=4)
    args = ap.parse_args()
    if args.classify:
        classify(args)
    if args.aggregate:
        aggregate()
    if not (args.classify or args.aggregate):
        sys.exit("pass --classify and/or --aggregate")


if __name__ == "__main__":
    main()
