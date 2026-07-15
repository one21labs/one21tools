#!/usr/bin/env python3
"""ADR 0068 Phase-0: build the blind classification pool.

Curated items = bullet/numbered lines in the friction/summary section of each
retrospect spawn prompt (mechanical parse: lines starting with '-' or 'N.').
Pool = curated + ledger items, channel-stripped, shuffled with seed 68.
"""
import json, os, re, random

base = os.path.dirname(os.path.abspath(__file__))
d = json.load(open(os.path.join(base, "phase0_raw.json")))

pool = []
key = {}  # blind id -> (session, channel, orig id)

for sid, s in d.items():
    for it in s["ledger"]:
        pool.append({"orig": (sid, "ledger", it["id"]),
                     "text": f"[tool event, count={it['count']}, tool={it['tool']}] {it['text']}"
                             + (f" || command/context: {it['context']}" if it["context"] else "")})
    seen = set()

    def add(item):
        item = re.sub(r"\s+", " ", item).strip()
        if len(item) < 30:
            return
        k = item[:80]
        if k in seen:
            return  # same item repeated across spawns in one session
        seen.add(k)
        pool.append({"orig": (sid, "curated", f"{sid}-C{len(seen):02d}"), "text": item})

    for spawn in s["curated_spawns"]:
        p = spawn["prompt"]
        # format A: markdown bullets / numbered lines
        for m in re.finditer(r"(?m)^(?:- |\d{1,2}\. )(.+(?:\n(?![-\d]|\n).+)*)", p):
            add(m.group(1))
        # format B: inline 'Session friction observed: (1) ... (2) ...'
        fm = re.search(r"Session friction observed[:\s]*(.*)", p, re.S)
        if fm:
            tail = fm.group(1)
            parts = re.split(r"\(\d{1,2}\)\s", tail)
            if len(parts) > 1:
                for part in parts[1:]:
                    # stop an item at a paragraph break (next instruction block)
                    add(part.split("\n\n")[0])
            elif tail.strip().lower().startswith("none"):
                pass  # curated channel explicitly reported no friction

random.seed(68)
random.shuffle(pool)
blind = []
for i, p in enumerate(pool, 1):
    bid = f"ITEM-{i:03d}"
    key[bid] = p["orig"]
    blind.append({"id": bid, "text": p["text"]})

json.dump(blind, open(os.path.join(base, "phase0_blind_pool.json"), "w"), indent=1)
json.dump({k: list(v) for k, v in key.items()}, open(os.path.join(base, "phase0_key.json"), "w"), indent=1)
from collections import Counter
c = Counter(v[1] for v in key.values())
print("pool size:", len(blind), dict(c))
c2 = Counter((v[0], v[1]) for v in key.values())
for k in sorted(c2): print(k, c2[k])
