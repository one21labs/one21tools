#!/usr/bin/env bash
# EP loophole OOS hermetic retest (issue #31 item 5). Runs INSIDE WSL Debian (this machine's
# verified-today hermetic recipe — supersedes the git-bash/Windows-cwd recipe used by
# 2026-07-08-skills-hermetic / 2026-07-09-ep-remeasure-hermetic, whose external-but-Windows cwd
# still let project CLAUDE.md discovery leak via cwd traversal). Differences from that recipe:
#   - CLAUDE_CONFIG_DIR points at a dedicated clean config dir (credentials only, no project/skill
#     state) instead of relocating ~/.claude/CLAUDE.md in place — no trap/restore needed, the
#     control arm simply never sees a config dir with anything to leak.
#   - EMPTY cwd is a WSL-native scratch dir OUTSIDE any repo (not just outside THIS repo) — cwd
#     traversal on the Windows side could still reach a parent CLAUDE.md; a WSL scratch dir has no
#     such ancestor.
#   - PATH is prepended with ~/.local/bin so `claude` resolves inside the clean config context.
# Unchanged: tool DENY list (ADR 0023), NEUTRAL base framing, prompt via STDIN (the variadic
# --disallowedTools last, so it doesn't eat the prompt), 2 arms x 3 evals x 3 reps.
set -u
BASE="$(cd "$(dirname "$0")" && pwd)"
OUT="${HERMETIC_OUT:-$BASE/outputs}"; mkdir -p "$OUT"
EMPTY="${HERMETIC_CWD:-$HOME/hx_ep_oos_cwd}"; mkdir -p "$EMPTY"
export CLAUDE_CONFIG_DIR="${CLAUDE_CONFIG_DIR:-$HOME/issue30/claude-config}"
export PATH="$HOME/.local/bin:$PATH"
MODEL="${MODEL:-sonnet}"; REPS="${REPS:-3}"; MAXJ="${MAXJ:-8}"
DRYRUN="${DRYRUN:-0}"
DENY=(Skill Task Read Grep Glob Bash Edit Write WebFetch WebSearch NotebookEdit)
BASE_SYS="You are in a headless session with no file-system or code-execution tools; you cannot open the user's project or run anything. Respond in plain text."

run_cell(){
  local key="$1" skill="$2" arm="$3" rep="$4"
  local out="$OUT/${key}.${arm}.${rep}.txt"
  local sys="$BASE_SYS"
  [ "$arm" = "with" ] && sys="$BASE_SYS"$'\n\n'"$(cat "$BASE/treatments/with.txt")"
  if [ "$DRYRUN" = "1" ]; then
    echo "[dry-run] ${key}.${arm}.${rep} <- $BASE/prompts/${key}.txt (sys ${#sys} chars) -> $out"
    return
  fi
  ( cd "$EMPTY" && CLAUDE_EFFORT=medium claude -p --model "$MODEL" --output-format text \
      --append-system-prompt "$sys" --disallowedTools "${DENY[@]}" < "$BASE/prompts/${key}.txt" ) \
      > "$out" 2>"$out.err"
  echo "done ${key}.${arm}.${rep} ($(wc -c <"$out") bytes)"
}

ncells=$(( $(wc -l < "$BASE/cells.tsv") * 2 * REPS ))
echo "model=$MODEL reps=$REPS cells=$ncells out=$OUT dryrun=$DRYRUN config_dir=$CLAUDE_CONFIG_DIR cwd=$EMPTY"

# Interleave arms in run order (load pairing): for each eval, submit rep 1's without+with pair
# before rep 2's, etc., instead of running one arm's 3 reps as a block — keeps each paired rep
# adjacent in submission order so a temporal drift in model load affects both arms of a pair
# similarly rather than concentrating on one arm's block.
while IFS=$'\t' read -r key skill; do
  key="${key%$'\r'}"; skill="${skill%$'\r'}"   # defensive: tolerate CRLF cells.tsv
  [ -z "$key" ] && continue
  for rep in $(seq 1 "$REPS"); do
    for arm in without with; do
      run_cell "$key" "$skill" "$arm" "$rep" &
      while [ "$(jobs -r | wc -l)" -ge "$MAXJ" ]; do wait -n; done
    done
  done
done < "$BASE/cells.tsv"
wait
echo "ALL DONE. outputs in $OUT"
