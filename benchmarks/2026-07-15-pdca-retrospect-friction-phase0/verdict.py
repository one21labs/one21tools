#!/usr/bin/env python3
"""ADR 0068 Phase-0 final aggregation.

Per session: agreed (pass A AND pass B) FINDING-GRADE ledger items whose tool event occurred
BEFORE the session's last genuine retrospect spawn (a ledger built at retrospect time could
only contain events up to that point), coverage-checked against the curated channel.
S5's spawns 1/2 were build-spec agents (false positives of the spawn detector), so S5's
curated channel is spawn 0 only — which carried no friction summary.
"""
import json, os, re, hashlib

S = os.path.dirname(os.path.abspath(__file__))
raw = json.load(open(f"{S}/phase0_raw.json"))
key = json.load(open(f"{S}/phase0_key.json"))
pool = {p["id"]: p["text"] for p in json.load(open(f"{S}/phase0_blind_pool.json"))}

# last GENUINE retrospect spawn ts per session (S5: spawn 0 only)
CUTOFF = {
    "S1": "2026-07-15T17:41:05.246Z",
    "S2": "2026-07-15T03:15:40.749Z",
    "S3": "2026-07-15T00:55:02.363Z",
    "S4": "2026-07-14T22:58:12.841Z",
    "S5": "2026-07-14T04:58:44.595Z",
}

# per-session dual-pass grades (F = FINDING-GRADE), transcribed from the 10 classifier outputs
GRADES = {
 "S1_A": {"ITEM-004","ITEM-068","ITEM-075","ITEM-052","ITEM-064","ITEM-009","ITEM-037","ITEM-088","ITEM-071"},
 "S1_B": {"ITEM-004","ITEM-068","ITEM-075","ITEM-052","ITEM-064","ITEM-009","ITEM-088","ITEM-071"},
 "S2_A": {"ITEM-011","ITEM-033","ITEM-030","ITEM-003","ITEM-005","ITEM-077","ITEM-042","ITEM-061","ITEM-066","ITEM-067"},
 "S2_B": {"ITEM-011","ITEM-033","ITEM-030","ITEM-003","ITEM-005","ITEM-077","ITEM-042","ITEM-061","ITEM-066","ITEM-067"},
 "S3_A": {"ITEM-055","ITEM-013","ITEM-081"},
 "S3_B": {"ITEM-055","ITEM-040","ITEM-013","ITEM-081"},
 "S4_A": {"ITEM-043","ITEM-041","ITEM-089","ITEM-065","ITEM-072","ITEM-048","ITEM-057","ITEM-035","ITEM-091","ITEM-023","ITEM-084","ITEM-078"},
 "S4_B": {"ITEM-043","ITEM-041","ITEM-089","ITEM-065","ITEM-072","ITEM-048","ITEM-057","ITEM-035","ITEM-091","ITEM-023","ITEM-078"},
 "S5_A": {"ITEM-090","ITEM-029","ITEM-020","ITEM-073","ITEM-063","ITEM-032","ITEM-001","ITEM-028"},
 "S5_B": {"ITEM-073","ITEM-063","ITEM-032","ITEM-001","ITEM-044"},
}

# COVERAGE: curated items that semantically cover a ledger item's friction class, judged
# with quotes (recorded here as the audit trail). None = omitted.
COVERED_BY = {
    "S1-L02": "S1-C02 (gate-pipe-guard denial, 'second occurrence this session')",   # pipe x3
    "S2-L01": "S2-C07 (gh issue view --json quirk, 'already in memory/conventions')",
    "S2-L02": "S2-C02 (advisor agents not registered as spawnable types)",
    "S2-L03": "S2-C02 (advisor agents not registered as spawnable types)",
    "S2-L04": "S2-C02 (advisor agents not registered as spawnable types)",
    "S2-L06": "S2-C06 (empirical-evals.md 16 chars over its 12000 cap)",
    "S4-L05": "S4-C01 (Edit-before-Read blocks ... MEMORY.md named explicitly)",     # ebr MEMORY.md
}

def item_ts(sid, oid):
    # recover the ledger event's first-seen timestamp by re-scanning the transcript
    path = raw[sid]["file"]
    target = next(it for it in raw[sid]["ledger"] if it["id"] == oid)
    norm_target = target["text"]
    for line in open(path, errors="replace"):
        if '"is_error"' not in line and "is_error" not in line:
            continue
        try:
            rec = json.loads(line)
        except json.JSONDecodeError:
            continue
        msg = rec.get("message") or {}
        c = msg.get("content")
        if not isinstance(c, list):
            continue
        for b in c:
            if isinstance(b, dict) and b.get("type") == "tool_result" and b.get("is_error"):
                t = b.get("content")
                if isinstance(t, list):
                    t = " ".join(str(x.get("text", "")) for x in t if isinstance(x, dict))
                t = re.sub(r"\s+", " ", str(t).strip())[:400]
                if t == norm_target:
                    return rec.get("timestamp")
    return None

sessions_pass = 0
report = {}
for sid in ["S1", "S2", "S3", "S4", "S5"]:
    agree = GRADES[f"{sid}_A"] & GRADES[f"{sid}_B"]
    ledger_fg = [(bid, key[bid][2]) for bid in sorted(agree) if key[bid][0] == sid and key[bid][1] == "ledger"]
    rows = []
    for bid, oid in ledger_fg:
        ts = item_ts(sid, oid)
        before = ts is not None and ts <= CUTOFF[sid]
        covered = None
        for k, v in COVERED_BY.items():
            if k.startswith(f"{sid}-") and k == oid:
                covered = v
        rows.append({"blind": bid, "orig": oid, "ts": ts, "before_retro": before,
                     "covered_by": covered, "text": pool[bid][:120]})
    omitted = [r for r in rows if r["before_retro"] and not r["covered_by"]]
    verdict = len(omitted) >= 1
    sessions_pass += verdict
    report[sid] = {"agreed_fg_total": len(agree), "ledger_fg": rows,
                   "omitted_before_retro": len(omitted), "session_pass": verdict}
print(json.dumps(report, indent=1))
print(f"\nFROZEN QUESTION: ledger surfaced >=1 curated-omitted finding-grade item in "
      f"{sessions_pass}/5 sessions (threshold 3) -> {'PASS' if sessions_pass >= 3 else 'NULL'}")
json.dump(report, open(f"{S}/phase0_final.json", "w"), indent=1)
