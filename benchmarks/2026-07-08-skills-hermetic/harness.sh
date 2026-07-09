#!/usr/bin/env bash
# Hermetic skill benefit-benchmark: does each SKILL.md measurably beat its no-skill baseline?
# (ADR 0024 justification bar; ADR 0023 hermetic executor; ADR 0019 verdict.)
#
# Executor = hermetic `claude -p`: external cwd (no project CLAUDE.md) + Skill/Task/Read/Grep/Glob/
# Bash/Edit/Write denied (no plugin-skill invocation, no repo access) + user ~/.claude/CLAUDE.md
# relocated (trap-restore). NEUTRAL base framing (ADR 0024: prose ablation is framing-sensitive).
# The ONLY between-arm difference: the "with" arm gets --append-system-prompt = the SKILL.md BODY
# (treatments/<skill>.txt); "without" gets only the neutral framing. Prompt piped via STDIN so the
# variadic --disallowedTools (LAST) doesn't eat it. Graded blind against each eval's expectations.
set -u
BASE="$(cd "$(dirname "$0")" && pwd)"
OUT="${HERMETIC_OUT:-$BASE/outputs}"; mkdir -p "$OUT"
EMPTY="${HERMETIC_CWD:-/c/Users/ajmcc/AppData/Local/Temp/hx_skills_cwd}"; mkdir -p "$EMPTY"
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
  else echo "WARN: $LINK present, not relocated -> loads into BOTH arms. Set HERMETIC_RELOCATE_USER_MEMORY=1." >&2; fi
fi

run_cell(){
  local key="$1" skill="$2" arm="$3" rep="$4"
  local out="$OUT/${key}.${arm}.${rep}.txt"
  local sys="$BASE_SYS"
  [ "$arm" = "with" ] && sys="$BASE_SYS"$'\n\n'"$(cat "$BASE/treatments/${skill}.txt")"
  ( cd "$EMPTY" && CLAUDE_EFFORT=medium claude -p --model "$MODEL" --output-format text \
      --append-system-prompt "$sys" --disallowedTools "${DENY[@]}" < "$BASE/prompts/${key}.txt" ) \
      > "$out" 2>"$out.err"
  echo "done ${key}.${arm}.${rep} ($(wc -c <"$out") bytes)"
}

ncells=$(( $(wc -l < "$BASE/cells.tsv") * 2 * REPS ))
echo "model=$MODEL reps=$REPS cells=$ncells out=$OUT"
while IFS=$'\t' read -r key skill; do
  key="${key%$'\r'}"; skill="${skill%$'\r'}"   # defensive: tolerate CRLF cells.tsv
  [ -z "$key" ] && continue
  for arm in without with; do
    for rep in $(seq 1 "$REPS"); do
      run_cell "$key" "$skill" "$arm" "$rep" &
      while [ "$(jobs -r | wc -l)" -ge "$MAXJ" ]; do wait -n; done
    done
  done
done < "$BASE/cells.tsv"
wait
echo "ALL DONE. outputs in $OUT"
