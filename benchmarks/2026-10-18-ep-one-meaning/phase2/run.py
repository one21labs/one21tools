#!/usr/bin/env python3
"""run.py ROUND ARMS(comma) PROMPTSET(dev|holdout) REPS -> rounds/ROUND/{outputs,verdicts.jsonl}.
Arm 'without' = no skill; any other arm = treatments/<arm>.txt appended to the system prompt."""
import json, os, re, subprocess, sys, hashlib
from concurrent.futures import ThreadPoolExecutor
BASE = os.path.dirname(os.path.abspath(__file__)); CWD = os.path.join(BASE, "cwd")
rnd, arms, pset, reps = sys.argv[1], sys.argv[2].split(","), sys.argv[3], int(sys.argv[4])
R = os.path.join(BASE, "rounds", rnd); O = os.path.join(R, "outputs"); os.makedirs(O, exist_ok=True)
meta = json.load(open(os.path.join(BASE, "meta.json")))
keys = [k for k, v in meta.items() if v["set"] == pset]
DENY = ["Skill", "Task", "Read", "Grep", "Glob", "Bash", "Edit", "Write", "WebFetch", "WebSearch", "NotebookEdit"]
BASE_SYS = "You are in a headless session with no file-system or code-execution tools; you cannot open the user's project or run anything. Respond in plain text."
GRADE = open(os.path.join(BASE, "grade_prompt.txt")).read().split("=====\n")
# Arms byte-identical to a phase-1 treatment live there only (one home); sha pins: treatments.sha256.
SHARED = {"current": "../phase1/treatments/with-current.txt", "v0-glossary": "../phase1/treatments/with-plain.txt"}
treatment = lambda arm: os.path.join(BASE, SHARED[arm]) if arm in SHARED else os.path.join(BASE, "treatments", arm + ".txt")

def claude(args, stdin):
    env = dict(os.environ, CLAUDE_EFFORT="medium")
    r = subprocess.run(["claude", "-p", "--model", "sonnet", "--output-format", "text", *args,
                        "--disallowedTools", *DENY], input=stdin, cwd=CWD, env=env,
                       capture_output=True, text=True, timeout=1200)
    return r.stdout

def gen(cell):
    k, arm, rep = cell; out = os.path.join(O, f"{k}.{arm}.{rep}.txt")
    if os.path.exists(out) and os.path.getsize(out) > 200: return
    sys_p = BASE_SYS if arm == "without" else BASE_SYS + "\n\n" + open(treatment(arm)).read()
    for _ in range(3):
        txt = claude(["--append-system-prompt", sys_p], meta[k]["prompt"])
        if len(txt) > 200: break
    open(out, "w").write(txt)

def judge(instr, item):
    body = instr + "\n\n" + json.dumps(item, indent=1)
    for _ in range(3):
        m = re.search(r"\{.*\}", claude([], body), re.S)
        try:
            v = json.loads(m.group(0)) if m else None
            if v and isinstance(v.get("met"), int) and v.get("total"): return v
        except json.JSONDecodeError: pass
    return None

def grade(cell):
    k, arm, rep = cell
    item = {"prompt": meta[k]["prompt"], "expectations": meta[k]["expectations"],
            "response": open(os.path.join(O, f"{k}.{arm}.{rep}.txt")).read().strip()}
    g, p = judge(GRADE[0], item), judge(GRADE[1], item)
    return {"bid": hashlib.sha256(f"{rnd}{k}{arm}{rep}".encode()).hexdigest()[:12], "key": k, "arm": arm,
            "rep": rep, "grader": g, "prosecutor": p}

cells = [(k, a, r) for k in keys for a in arms for r in range(1, reps + 1)]
with ThreadPoolExecutor(8) as ex: list(ex.map(gen, cells))
with ThreadPoolExecutor(8) as ex: rows = list(ex.map(grade, cells))
with open(os.path.join(R, "verdicts.jsonl"), "w") as fh:
    for r in rows: fh.write(json.dumps(r) + "\n")
print(f"{rnd}: {len(cells)} cells, judge failures {sum(1 for r in rows if not r['grader'] or not r['prosecutor'])}")
