#!/usr/bin/env python3
"""Pack a run's structured raw envelopes per ADR 0026 (run AFTER aggregate.py — aggregate
reads the raw envelopes directly; this step is storage hygiene, not analysis).

From <DIR>/outputs/*.json (CLI result envelopes + tiered *.trace.json):
- costs.csv — flat per-call record table (CSV per ADR 0026): key, arm, rep, role, model,
  tokens in/cache_create/cache_read/out, cost_usd, duration_ms. Solo cells = one 'solo' row;
  tiered cells = one row per plan/implement/validate call.
- traces.jsonl — the tiered validator verdicts (prose defects -> minified JSONL per ADR 0026).
- raw.tar.gz — every *.json envelope, then the plain copies are deleted. The .txt response
  texts stay plain on main: they are this benchmark's ADR 0023 audit sample (bounded corpus,
  every graded cell eyeball-readable), recorded as sample_rule in metadata.json.
Re-runnable after an escalation adds cells: existing costs.csv rows, traces.jsonl records and
raw.tar.gz members are carried over and the new envelopes merged in (never overwritten away).
Usage: DIR=prescreen python3 pack.py   (DIR relative to this file; default '.' = main run)
"""
import csv, glob, io, json, os, tarfile

BASE = os.path.dirname(os.path.abspath(__file__))
D = os.path.join(BASE, os.environ.get("DIR", "."))
OUT = os.path.join(D, "outputs")
FIELDS = ("input_tokens", "cache_creation_input_tokens", "cache_read_input_tokens", "output_tokens")


def usage_cols(u):
    return [(u or {}).get(f) or 0 for f in FIELDS]


rows, traces = [], []
if os.path.exists(os.path.join(D, "costs.csv")):
    with open(os.path.join(D, "costs.csv"), encoding="utf-8", newline="") as fh:
        rows = [list(r.values()) for r in csv.DictReader(fh)]
if os.path.exists(os.path.join(D, "traces.jsonl")):
    with open(os.path.join(D, "traces.jsonl"), encoding="utf-8") as fh:
        traces = [json.loads(l) for l in fh if l.strip()]
old_members = []
if os.path.exists(os.path.join(D, "raw.tar.gz")):
    with tarfile.open(os.path.join(D, "raw.tar.gz"), "r:gz") as tar:
        old_members = [(m, tar.extractfile(m).read()) for m in tar.getmembers() if m.isfile()]
envelopes = sorted(glob.glob(os.path.join(OUT, "*.json")))
for f in envelopes:
    name = os.path.basename(f)[:-5]
    with open(f, encoding="utf-8") as fh:
        d = json.load(fh)
    if name.endswith(".trace"):
        key, rep = d["key"], d["rep"]
        for c in d["calls"]:
            rows.append([key, "tiered", rep, c["role"], c["model"], *usage_cols(c.get("usage")),
                         round(c.get("cost_usd") or 0, 6), c.get("duration_ms") or 0])
        traces.append({"key": key, "rep": rep, "cycles": d["cycles"],
                       "internal_pass": d["internal_pass"], "verdicts": d["verdicts"]})
    else:
        parts = name.split(".")
        if len(parts) != 4:
            continue
        key, arm, rep = ".".join(parts[:2]), parts[2], parts[3]
        rows.append([key, arm, rep, "solo", arm, *usage_cols(d.get("usage")),
                     round(d.get("total_cost_usd") or 0, 6), d.get("duration_ms") or 0])

with open(os.path.join(D, "costs.csv"), "w", encoding="utf-8", newline="") as fh:
    w = csv.writer(fh)
    w.writerow(["key", "arm", "rep", "role", "model", "tok_in", "tok_cache_create",
                "tok_cache_read", "tok_out", "cost_usd", "duration_ms"])
    w.writerows(rows)
if traces:
    with open(os.path.join(D, "traces.jsonl"), "w", encoding="utf-8") as fh:
        for t in traces:
            fh.write(json.dumps(t, separators=(",", ":")) + "\n")

with tarfile.open(os.path.join(D, "raw.tar.gz"), "w:gz") as tar:
    for m, data in old_members:
        tar.addfile(m, io.BytesIO(data))
    for f in envelopes:
        tar.add(f, arcname=os.path.join("outputs", os.path.basename(f)))
for f in envelopes:
    os.remove(f)

meta = {"sample_rule": "every cell's response .txt stays plain on main (bounded corpus, all "
                       "graded cells eyeball-readable); structured envelopes/traces -> "
                       "costs.csv (+ traces.jsonl) with raw JSON in raw.tar.gz (ADR 0023/0026)",
        "envelopes_archived": len(old_members) + len(envelopes), "cost_rows": len(rows),
        "traces": len(traces)}
with open(os.path.join(D, "metadata.json"), "w", encoding="utf-8") as fh:
    json.dump(meta, fh, indent=1)
print(f"packed {len(envelopes)} envelopes -> raw.tar.gz; costs.csv {len(rows)} rows; "
      f"traces.jsonl {len(traces)}")
