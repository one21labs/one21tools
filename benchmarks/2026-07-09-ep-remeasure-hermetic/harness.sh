#!/usr/bin/env bash
# ADR 0027 EP re-measure (issue #52): 3-arm hermetic executor.
# Same hermetic recipe as 2026-07-08-skills-hermetic/harness.sh (ADR 0023: external empty cwd,
# tool DENY list, user CLAUDE.md relocated, NEUTRAL framing, prompt via STDIN so the variadic
# --disallowedTools doesn't eat it). Differences: arms = without / with-old / with-new, and each
# with-arm appends its own treatments/<arm>.txt (body + 3 touched refs, ADR 0027 decision 2).
set -u
BASE="$(cd "$(dirname "$0")" && pwd)"
OUT="${HERMETIC_OUT:-$BASE/outputs}"; mkdir -p "$OUT"
EMPTY="${HERMETIC_CWD:-/c/Users/ajmcc/AppData/Local/Temp/hx_ep_remeasure_cwd}"; mkdir -p "$EMPTY"
MODEL="${MODEL:-sonnet}"; REPS="${REPS:-3}"; MAXJ="${MAXJ:-8}"
DENY=(Skill Task Read Grep Glob Bash Edit Write WebFetch WebSearch NotebookEdit)
BASE_SYS="You are in a headless session with no file-system or code-execution tools; you cannot open the user's project or run anything. Respond in plain text."

# user-memory isolation (opt-in; trap guarantees restore)
LINK="$HOME/.claude/CLAUDE.md"; BAK="$LINK.hxbak"; RELOCATED=0
restore(){ [ "$RELOCATED" = "1" ] && [ -e "$BAK" ] && mv "$BAK" "$LINK" && echo "[restored $LINK]"; }
trap restore EXIT INT TERM
[ -e "$BAK" ] && [ ! -e "$LINK" ] && mv "$BAK" "$LINK"   # self-heal a prior interrupted run
if [ -e "$LINK" ]; then
  if [ "${HERMETIC_RELOCATE_USER_MEMORY:-0}" = "1" ]; then mv "$LINK" "$BAK" && RELOCATED=1 && echo "[relocated user CLAUDE.md for the run]";
  else echo "WARN: $LINK present, not relocated -> loads into ALL arms. Set HERMETIC_RELOCATE_USER_MEMORY=1." >&2; fi
fi

run_cell(){
  local key="$1" arm="$2" rep="$3"
  local out="$OUT/${key}.${arm}.${rep}.txt"
  local sys="$BASE_SYS"
  [ "$arm" != "without" ] && sys="$BASE_SYS"$'\n\n'"$(cat "$BASE/treatments/${arm}.txt")"
  ( cd "$EMPTY" && CLAUDE_EFFORT=medium claude -p --model "$MODEL" --output-format text \
      --append-system-prompt "$sys" --disallowedTools "${DENY[@]}" < "$BASE/prompts/${key}.txt" ) \
      > "$out" 2>"$out.err"
  echo "done ${key}.${arm}.${rep} ($(wc -c <"$out") bytes)"
}

ncells=$(( $(wc -l < "$BASE/cells.tsv") * 3 * REPS ))
echo "model=$MODEL reps=$REPS cells=$ncells out=$OUT"
while IFS=$'\t' read -r key skill; do
  key="${key%$'\r'}"; skill="${skill%$'\r'}"   # defensive: tolerate CRLF cells.tsv
  [ -z "$key" ] && continue
  for arm in without with-old with-new; do
    for rep in $(seq 1 "$REPS"); do
      run_cell "$key" "$arm" "$rep" &
      while [ "$(jobs -r | wc -l)" -ge "$MAXJ" ]; do wait -n; done
    done
  done
done < "$BASE/cells.tsv"
wait
echo "ALL DONE. outputs in $OUT"
