#!/usr/bin/env bash
# Tiered-execution benchmark (issue #41): single hermetic entry point for ALL arms.
#
# Arms: haiku | sonnet | opus (solo: one `claude -p` per cell) and tiered (dispatched to
# tiered.py: Sonnet plans+validates, Haiku implements, <=3 cycles). Hermetic executor per
# ADR 0023, unchanged from 2026-07-08-skills-hermetic: external empty cwd (no project
# CLAUDE.md), Skill/Task/file/exec tools denied, user ~/.claude/CLAUDE.md relocated
# (trap-restore), NEUTRAL framing identical for every call in every arm (the between-arm
# difference is the agent configuration only). Tasks are text-artifact-shaped, so the full
# tool-deny carries over — no tool-using variant needed.
#
# Usage: KEYS=<file> ARMS="haiku sonnet opus tiered" REPS=3 bash harness.sh
# Cell outputs: outputs/<key>.<arm>.<rep>.json (full CLI JSON: result + usage + cost) and
# .txt (the response text, the graded+auditable raw); tiered adds .trace.json (per-call log).
set -u
BASE="$(cd "$(dirname "$0")" && pwd)"
OUT="${OUT:-$BASE/outputs}"; mkdir -p "$OUT"
EMPTY="${HERMETIC_CWD:-/tmp/hx_tiered_cwd}"; mkdir -p "$EMPTY"
KEYS="${KEYS:-$BASE/tasks.txt}"; ARMS="${ARMS:-haiku sonnet opus tiered}"
REPS="${REPS:-3}"; MAXJ="${MAXJ:-8}"
DENY=(Skill Task Read Grep Glob Bash Edit Write WebFetch WebSearch NotebookEdit)
BASE_SYS="You are in a headless session with no file-system or code-execution tools; you cannot open the user's project or run anything. Respond in plain text."

# user-memory isolation (opt-in; trap guarantees restore) — same mechanism as skills-hermetic
LINK="$HOME/.claude/CLAUDE.md"; BAK="$LINK.hxbak"; RELOCATED=0
restore(){ [ "$RELOCATED" = "1" ] && [ -e "$BAK" ] && mv "$BAK" "$LINK" && echo "[restored $LINK]"; }
trap restore EXIT INT TERM
[ -e "$BAK" ] && [ ! -e "$LINK" ] && mv "$BAK" "$LINK"   # self-heal a prior interrupted run
if [ -e "$LINK" ]; then
  if [ "${HERMETIC_RELOCATE_USER_MEMORY:-0}" = "1" ]; then mv "$LINK" "$BAK" && RELOCATED=1 && echo "[relocated user CLAUDE.md for the run]";
  else echo "WARN: $LINK present, not relocated -> loads into EVERY arm. Set HERMETIC_RELOCATE_USER_MEMORY=1." >&2; fi
fi

run_cell(){
  local key="$1" arm="$2" rep="$3"
  local stem="$OUT/${key}.${arm}.${rep}"
  [ -s "$stem.txt" ] && { echo "skip ${key}.${arm}.${rep} (exists)"; return; }
  if [ "$arm" = "tiered" ]; then
    HERMETIC_CWD="$EMPTY" OUT="$OUT" python3 "$BASE/tiered.py" "$key" "$rep" >"$stem.log" 2>&1
  else
    ( cd "$EMPTY" && CLAUDE_EFFORT=medium timeout 900 claude -p --model "$arm" --output-format json \
        --append-system-prompt "$BASE_SYS" --disallowedTools "${DENY[@]}" < "$BASE/prompts/${key}.txt" ) \
        > "$stem.json" 2>"$stem.err"
    python3 -c "import json,sys;
d=json.load(open('$stem.json')); open('$stem.txt','w',encoding='utf-8').write(d.get('result') or '')" \
      || echo "EXTRACT-FAIL ${key}.${arm}.${rep}" >&2
  fi
  echo "done ${key}.${arm}.${rep} ($(wc -c <"$stem.txt" 2>/dev/null || echo 0) bytes)"
}

echo "keys=$KEYS arms=[$ARMS] reps=$REPS out=$OUT"
while IFS= read -r key; do
  key="${key%$'\r'}"; [ -z "$key" ] && continue
  for arm in $ARMS; do
    for rep in $(seq 1 "$REPS"); do
      run_cell "$key" "$arm" "$rep" &
      while [ "$(jobs -r | wc -l)" -ge "$MAXJ" ]; do wait -n; done
    done
  done
done < "$KEYS"
wait
echo "ALL DONE. outputs in $OUT"
