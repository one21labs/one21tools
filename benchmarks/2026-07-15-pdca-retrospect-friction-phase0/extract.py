#!/usr/bin/env python3
"""ADR 0068 Phase-0: deterministic mechanical-ledger extract + curated-channel extract.

Ledger rule (frozen, mechanical): every tool_result with is_error=true in the parent
session transcript, deduplicated by normalized text, categorized by prefix:
  hook-denial       text starts with 'Denied:' or contains 'blocked by hook'
  permission-denial contains 'Permission for this action was denied'
  blocked           starts with '<tool_use_error>Blocked'
  nonzero-exit      starts with 'Exit code'
  tool-error        anything else
Curated channel: the prompt text of each retrospect agent spawn in the same session.
No judgment is applied here; classification happens in a separate blind step.
"""
import json, os, sys, hashlib, re

SESSIONS = [
    ("S1", "/home/user/.claude/projects/-home-user-projects/2cf8409f-dcec-4310-bad5-b9741ba2ce3a.jsonl"),
    ("S2", "/home/user/.claude/projects/-home-user-projects/6fa919ff-963c-40e5-9b3d-8656577cd7af.jsonl"),
    ("S3", "/home/user/.claude/projects/-home-user-projects/7e298aea-78ab-49c1-8008-029ee4422494.jsonl"),
    ("S4", "/home/user/.claude/projects/-home-user-projects/27f82199-98f4-4290-8d33-b995955558f4.jsonl"),
    ("S5", "/home/user/.claude/projects/-home-user-projects/5ae0f2fe-68ca-48cd-b923-f74bbd421dd0.jsonl"),
]

def block_text(b):
    c = b.get("content")
    if isinstance(c, str):
        return c
    if isinstance(c, list):
        return " ".join(str(x.get("text", "")) for x in c if isinstance(x, dict))
    return str(c)

def categorize(t):
    ts = t.strip()
    if ts.startswith("Denied:") or "blocked by hook" in ts.lower():
        return "hook-denial"
    if "Permission for this action was denied" in ts:
        return "permission-denial"
    if ts.startswith("<tool_use_error>Blocked"):
        return "blocked"
    if ts.startswith("Exit code"):
        return "nonzero-exit"
    return "tool-error"

def norm(t):
    # collapse whitespace, strip volatile bits (paths kept; line numbers/timestamps collapsed)
    t = re.sub(r"\s+", " ", t.strip())
    return t[:400]

out = {}
for sid, path in SESSIONS:
    tooluse = {}   # id -> (name, short input)
    ledger = {}    # normtext -> {count, category, tool, sample}
    curated = []
    for line in open(path, errors="replace"):
        try:
            rec = json.loads(line)
        except json.JSONDecodeError:
            continue
        msg = rec.get("message") or {}
        content = msg.get("content")
        if not isinstance(content, list):
            continue
        for b in content:
            if not isinstance(b, dict):
                continue
            if b.get("type") == "tool_use":
                inp = b.get("input") or {}
                brief = str(inp.get("command") or inp.get("file_path") or inp.get("prompt") or "")[:160]
                tooluse[b.get("id")] = (b.get("name"), brief)
                if b.get("name") in ("Agent", "Task"):
                    st = str(inp.get("subagent_type", "")).lower()
                    pr = str(inp.get("prompt", ""))
                    # KNOWN GAP (README Corrections log #2): this prompt-text heuristic
                    # false-positived on two build-spec prompts; spawns were re-verified by
                    # hand for the verdict. Untested — a Phase-1 extractor must not inherit
                    # it without a decision-logic test (CLAUDE.md Never rule).
                    if "retrospect" in st or ("retrospect" in pr.lower()[:600] and "friction" in pr.lower()):
                        curated.append({"ts": rec.get("timestamp"), "prompt": pr})
            elif b.get("type") == "tool_result" and b.get("is_error"):
                t = norm(block_text(b))
                name, brief = tooluse.get(b.get("tool_use_id"), ("?", ""))
                key = hashlib.sha1(t.encode()).hexdigest()[:10]
                if t in ledger:
                    ledger[t]["count"] += 1
                else:
                    ledger[t] = {"id": f"{sid}-L{len(ledger)+1:02d}", "count": 1,
                                 "category": categorize(t), "tool": name,
                                 "context": brief, "text": t}
    out[sid] = {
        "file": path,
        "ledger": sorted(ledger.values(), key=lambda x: x["id"]),
        "curated_spawns": curated,
        "n_ledger": len(ledger),
        "n_spawns": len(curated),
    }

with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "phase0_raw.json"), "w") as f:
    json.dump(out, f, indent=1)
for sid in out:
    print(sid, "ledger items:", out[sid]["n_ledger"], "| retrospect spawns:", out[sid]["n_spawns"])
