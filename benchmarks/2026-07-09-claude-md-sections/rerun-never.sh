#!/usr/bin/env bash
# Never-section-only re-run (issue #72, ADR 0034) -- adapted from harness.sh to run JUST the 5
# `never.*` cells (n1_ci_gate, n2_coverage_threshold, n3_lint_rule, n4_min_hook,
# n4b_min_hook_elicitable) x 2 arms x 3 reps = 30 cells, under the redesigned tasks.json criteria.
# Reuses harness.sh's executor recipe verbatim (same deny list, same flags, same neutral BASE_SYS,
# same --append-system-prompt-carries-the-treatment with/without split) with two hermeticity
# adaptations for running this on a machine where harness.sh's Windows-specific recipe doesn't
# apply, matching the 2026-07-10-tiered-execution/harness.py precedent:
#   1. CLAUDE_CONFIG_DIR=$HOME/issue30/claude-config (a clean, credentials-only config) instead of
#      relocating the user's ~/.claude/CLAUDE.md -- no relocate/restore trap needed.
#   2. An empty scratch cwd OUTSIDE any repo checkout. CLAUDE_CONFIG_DIR does not stop project-level
#      CLAUDE.md auto-discovery by cwd traversal -- verified empirically (see
#      2026-07-10-tiered-execution/harness.py's header comment for the transcript numbers); running
#      from inside this repo's worktree would leak this project's CLAUDE.md into both arms.
# Run INSIDE WSL Debian (the hermetic CLAUDE_CONFIG_DIR only exists there):
#   wsl -d Debian -- bash /mnt/c/Users/ajmcc/projects/wt-never/benchmarks/2026-07-09-claude-md-sections/rerun-never.sh
set -u
BASE="$(cd "$(dirname "$0")" && pwd)"
OUT="${HERMETIC_OUT:-$BASE/rerun-outputs}"; mkdir -p "$OUT"
EMPTY="${HERMETIC_CWD:-$HOME/hx_never_rerun_cwd}"; mkdir -p "$EMPTY"
MODEL="${MODEL:-sonnet}"; REPS="${REPS:-3}"; MAXJ="${MAXJ:-8}"
DENY=(Skill Task Read Grep Glob Bash Edit Write WebFetch WebSearch NotebookEdit)
BASE_SYS="You are in a headless session with no file-system or code-execution tools; you cannot open the user's project or run anything. Respond in plain text."
CELLS="${HERMETIC_CELLS:-$BASE/rerun-cells.tsv}"

export PATH="$HOME/.local/bin:$PATH"
export CLAUDE_CONFIG_DIR="$HOME/issue30/claude-config"
unset CLAUDECODE

run_cell(){
  local key="$1" section="$2" arm="$3" rep="$4"
  local out="$OUT/${key}.${arm}.${rep}.txt"
  local sys="$BASE_SYS"
  [ "$arm" = "with" ] && sys="$BASE_SYS"$'\n\n'"$(cat "$BASE/treatments/${section}.txt")"
  ( cd "$EMPTY" && CLAUDE_EFFORT=medium claude -p --model "$MODEL" --output-format text \
      --append-system-prompt "$sys" --disallowedTools "${DENY[@]}" < "$BASE/prompts/${key}.txt" ) \
      > "$out" 2>"$out.err"
  echo "done ${key}.${arm}.${rep} ($(wc -c <"$out") bytes)"
}

ncells=$(( $(wc -l < "$CELLS") * 2 * REPS ))
echo "model=$MODEL reps=$REPS cells=$ncells out=$OUT cwd=$EMPTY config_dir=$CLAUDE_CONFIG_DIR"
while IFS=$'\t' read -r key section; do
  key="${key%$'\r'}"; section="${section%$'\r'}"   # defensive: tolerate CRLF cells.tsv
  [ -z "$key" ] && continue
  for arm in without with; do
    for rep in $(seq 1 "$REPS"); do
      run_cell "$key" "$section" "$arm" "$rep" &
      while [ "$(jobs -r | wc -l)" -ge "$MAXJ" ]; do wait -n; done
    done
  done
done < "$CELLS"
wait
echo "ALL DONE. outputs in $OUT"
