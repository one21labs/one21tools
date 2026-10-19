#!/usr/bin/env python3
"""Blind-grade outputs/: grader + independent adversarial prosecutor per cell (sonnet, claude -p).
Arm is withheld from both judges (bid = sha256(filename)[:12]); met_final = min(grader, prosecutor).
Prompts mirror benchmarks/2026-07-08-skills-hermetic/{grade,prosecute_counts}.workflow.js."""
import json, hashlib, os, glob, re, subprocess, csv, sys
from concurrent.futures import ThreadPoolExecutor

BASE = os.path.dirname(os.path.abspath(__file__))
G = os.path.join(BASE, "graded"); os.makedirs(G, exist_ok=True)
CWD = os.path.join(BASE, "cwd")
meta = json.load(open(os.path.join(BASE, "meta.json")))
DENY = ["Skill", "Task", "Read", "Grep", "Glob", "Bash", "Edit", "Write", "WebFetch", "WebSearch", "NotebookEdit"]

GRADE = """Below is a JSON object with "prompt" (a user request), "response" (an AI assistant's reply), and "expectations" (an array of specific requirements the response must satisfy).

Evaluate EACH expectation as MET or NOT MET, strictly and literally, using ONLY evidence in the response text. Do not give credit for intent, partial effort, or things the response merely gestures at. If the response is truncated, refused, or off-task, unmet expectations are NOT MET.

Return ONLY a JSON object {"total": int, "met": int, "evidence": str}: total = number of expectations; met = how many are MET; evidence = the single most decisive expectation that is NOT MET (quote the response gap), or if all met, the one closest to failing."""

PROSECUTE = """Below is a JSON object with "prompt" (a user request), "response" (an AI assistant's reply), and "expectations" (an array of specific requirements).

You are an ADVERSARIAL grader. Go expectation by expectation and count how many are GENUINELY and FULLY satisfied by the response TEXT alone. Be skeptical: default an expectation to NOT MET when the evidence is thin, partial, gestured-at, claimed-but-not-done, or faked. Give NO credit for intent or effort. If the response is truncated, refused, or off-task, its unmet expectations are NOT MET.

Return ONLY a JSON object {"total": int, "met": int, "evidence": str}: met = your strict count of genuinely-and-fully satisfied expectations; evidence = the most decisive expectation you judged NOT MET and the gap."""

def judge(instr, item):
    body = instr + "\n\n" + json.dumps({k: item[k] for k in ("prompt", "expectations", "response")}, indent=1)
    for _ in range(3):
        r = subprocess.run(["claude", "-p", "--model", "sonnet", "--output-format", "text",
                            "--disallowedTools", *DENY], input=body, cwd=CWD,
                           capture_output=True, text=True, timeout=900)
        m = re.search(r"\{.*\}", r.stdout, re.S)
        if m:
            try:
                v = json.loads(m.group(0))
                if isinstance(v.get("met"), int) and isinstance(v.get("total"), int) and v["total"] > 0:
                    return v
            except json.JSONDecodeError:
                pass
    return None

def cell(f):
    name = os.path.basename(f)[:-4]
    skill, eval_id, arm, rep = name.split(".")
    m = meta[f"{skill}.{eval_id}"]
    item = {"prompt": m["prompt"], "expectations": m["expectations"],
            "response": open(f, encoding="utf-8", errors="replace").read().strip()}
    bid = hashlib.sha256(name.encode()).hexdigest()[:12]
    g, p = judge(GRADE, item), judge(PROSECUTE, item)
    return {"bid": bid, "eval_id": eval_id, "arm": arm, "rep": rep, "grader": g, "prosecutor": p}

files = sorted(glob.glob(os.path.join(BASE, "outputs", "*.txt")))
with ThreadPoolExecutor(int(os.environ.get("MAXJ", "8"))) as ex:
    rows = list(ex.map(cell, files))
with open(os.path.join(G, "verdicts.jsonl"), "w") as fh:
    for r in rows:
        fh.write(json.dumps(r) + "\n")
bad = [r["bid"] for r in rows if not r["grader"] or not r["prosecutor"]]
print(f"graded {len(rows)} cells; judge failures: {len(bad)} {bad}")
