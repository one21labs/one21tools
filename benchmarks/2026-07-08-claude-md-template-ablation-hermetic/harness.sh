#!/usr/bin/env bash
# Hermetic OFAT ablation of the CLAUDE.md-template "Feedback = PDCA trigger" section.
#
# Executor = hermetic `claude -p`. Three isolations make the control ("without") arm treatment-free
# (ADR 0023) — the in-harness subagent POC leaked on all three and was a CONFOUNDED NULL:
#   1. EXTERNAL cwd (outside any repo) -> no project CLAUDE.md walks into context.
#   2. Tools denied: Skill/Task (no plugin-skill invocation) + Read/Grep/Glob/Bash/Edit/Write
#      (no repo/file access). Pure-reasoning executor: it answers in text, which is what we grade.
#   3. User memory relocated: ~/.claude/CLAUDE.md loads regardless of cwd/CONFIG_DIR/HOME (verified);
#      opt-in relocation (HERMETIC_RELOCATE_USER_MEMORY=1) with a trap-restore. No-op on a fresh
#      cloud instance (no user CLAUDE.md there).
#
# BASE_SYS neutralizer (BOTH arms, identical): iteration-1 denied Write/Edit/Bash, so the executor
# refused to implement ("I lack tools, tell me your stack") and flagged in BOTH arms -> a ceiling
# that saturated 3/6 tasks at 1.00 (zero discriminating power). The neutralizer tells both arms to
# answer directly as text, freeing the baseline to implement so the section's effect is measurable.
# The ONLY between-arm difference remains --append-system-prompt with the section text (treatment).
# Prompt piped via STDIN so the variadic --disallowedTools (placed LAST) doesn't swallow it.
set -u
BASE="$(cd "$(dirname "$0")" && pwd)"
BASE_M="$(cygpath -m "$BASE" 2>/dev/null || echo "$BASE")"
TREATMENT="$(cat "$BASE/treatment.txt")"
OUT="${HERMETIC_OUT:-$BASE/outputs}"; mkdir -p "$OUT"
EMPTY="${HERMETIC_CWD:-/c/Users/ajmcc/AppData/Local/Temp/hx_ablation_cwd}"; mkdir -p "$EMPTY"
MODEL="${MODEL:-sonnet}"
REPS="${REPS:-3}"
MAXJ="${MAXJ:-5}"
DENY=(Skill Task Read Grep Glob Bash Edit Write WebFetch WebSearch NotebookEdit)
BASE_SYS="You are in a headless session with no file-system or code-execution tools; you cannot open the user's project or run anything. Respond in plain text."

# --- user-memory isolation (opt-in; trap guarantees restore) ---
LINK="$HOME/.claude/CLAUDE.md"; BAK="$LINK.hxbak"; RELOCATED=0
restore() { [ "$RELOCATED" = "1" ] && [ -e "$BAK" ] && mv "$BAK" "$LINK" && echo "[restored $LINK]"; }
trap restore EXIT INT TERM
if [ -e "$LINK" ]; then
  if [ "${HERMETIC_RELOCATE_USER_MEMORY:-0}" = "1" ]; then
    mv "$LINK" "$BAK" && RELOCATED=1 && echo "[relocated user CLAUDE.md for the run]"
  else
    echo "WARN: $LINK present and NOT relocated -> loads into BOTH arms. Set HERMETIC_RELOCATE_USER_MEMORY=1." >&2
  fi
fi

# tasks are the SSoT in tasks.json (one home; add a task there, not here)
declare -A TASKS
while IFS=$'\t' read -r id prompt; do
  [ -n "$id" ] && TASKS["$id"]="$prompt"
done < <(python -c "import json;[print(k+chr(9)+v) for k,v in json.load(open(r'$BASE_M/tasks.json')).items()]")

run_cell() {
  local id="$1" arm="$2" rep="$3"
  local out="$OUT/${id}.${arm}.${rep}.txt"
  local sys="$BASE_SYS"
  [ "$arm" = "with" ] && sys="$BASE_SYS"$'\n\n'"$TREATMENT"
  ( cd "$EMPTY" && printf '%s' "${TASKS[$id]}" | \
      CLAUDE_EFFORT=medium claude -p --model "$MODEL" --output-format text \
        --append-system-prompt "$sys" --disallowedTools "${DENY[@]}" ) > "$out" 2>"$out.err"
  echo "done ${id}.${arm}.${rep} ($(wc -c <"$out") bytes)"
}

echo "model=$MODEL reps=$REPS tasks=${#TASKS[@]} cells=$(( ${#TASKS[@]} * 2 * REPS )) out=$OUT"
for id in "${!TASKS[@]}"; do
  for arm in without with; do
    for rep in $(seq 1 "$REPS"); do
      run_cell "$id" "$arm" "$rep" &
      while [ "$(jobs -r | wc -l)" -ge "$MAXJ" ]; do wait -n; done
    done
  done
done
wait
echo "ALL DONE. outputs in $OUT"
