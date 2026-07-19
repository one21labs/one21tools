#!/usr/bin/env bash
# ep-slim-remeasure 3-arm hermetic executor (issue #248). Same hermetic recipe as
# 2026-07-18-ep-partition/harness.sh (ADR 0023: external empty cwd, tool DENY list, user
# CLAUDE.md relocated, NEUTRAL framing, prompt via STDIN so the variadic --disallowedTools
# doesn't eat it). Arms = without / with-full / with-slim; PILOT runs a fixed 2-cell smoke test
# (eval 5 without rep1, eval 5 with-slim rep1) into pilot-outputs/ and stops, before grid spend.
set -u
BASE="$(cd "$(dirname "$0")" && pwd)"
OUT="${HERMETIC_OUT:-$BASE/outputs}"; mkdir -p "$OUT"
EMPTY="${HERMETIC_CWD:-/tmp/claude-1000/hx_ep_slim_cwd}"; mkdir -p "$EMPTY"
if [ -e "$EMPTY/CLAUDE.md" ]; then
  echo "FATAL: $EMPTY/CLAUDE.md exists -- hermetic cwd must be empty of CLAUDE.md" >&2
  exit 1
fi
MODEL="${MODEL:-sonnet}"; REPS="${REPS:-3}"; MAXJ="${MAXJ:-8}"
ARMS=(without with-full with-slim)
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
  local key="$1" arm="$2" rep="$3" outdir="$4"
  local out="$outdir/${key}.${arm}.${rep}.txt"
  local sys="$BASE_SYS"
  [ "$arm" != "without" ] && sys="$BASE_SYS"$'\n\n'"$(cat "$BASE/treatments/${arm}.txt")"
  ( cd "$EMPTY" && CLAUDE_EFFORT=medium claude -p --model "$MODEL" --output-format text \
      --append-system-prompt "$sys" --disallowedTools "${DENY[@]}" < "$BASE/prompts/${key}.txt" ) \
      > "$out" 2>"$out.err"
  echo "done ${key}.${arm}.${rep} ($(wc -c <"$out") bytes)"
}

if [ "${PILOT:-0}" = "1" ]; then
  PILOT_OUT="$BASE/pilot-outputs"; mkdir -p "$PILOT_OUT"
  echo "PILOT: 2 cells (eval 5 without rep 1, eval 5 with-slim rep 1) -> $PILOT_OUT"
  run_cell "engineering-principles.5" "without" "1" "$PILOT_OUT"
  run_cell "engineering-principles.5" "with-slim" "1" "$PILOT_OUT"
  echo "PILOT DONE. review $PILOT_OUT before running the full grid."
  exit 0
fi

ncells=$(( $(wc -l < "$BASE/cells.tsv") * ${#ARMS[@]} * REPS ))
echo "model=$MODEL reps=$REPS arms=${ARMS[*]} cells=$ncells out=$OUT"
while IFS=$'\t' read -r key skill; do
  key="${key%$'\r'}"; skill="${skill%$'\r'}"   # defensive: tolerate CRLF cells.tsv
  [ -z "$key" ] && continue
  for arm in "${ARMS[@]}"; do
    for rep in $(seq 1 "$REPS"); do
      run_cell "$key" "$arm" "$rep" "$OUT" &
      while [ "$(jobs -r | wc -l)" -ge "$MAXJ" ]; do wait -n; done
    done
  done
done < "$BASE/cells.tsv"
wait
echo "ALL DONE. outputs in $OUT"
