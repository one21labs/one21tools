# Trigger-testing kit — findings (2026-07-07)

Query sets: 8 should-fire + 8 adjacent should-not-fire per skill (fresh-authored).
Runner: skill-creator's run_eval.py + 3 local patches (runner-patches.diff — file upstream):
1. Hard-fail on any first non-Skill/Read tool call -> keep watching instead.
2. Child inherits parent stdin (3s stall) -> stdin=DEVNULL.
3. Detection window closes at first message_stop -> reset and keep watching.

Environment finding: nested `claude -p` sessions inherit the container's ~16 built-in
skills; an organic "review this code for quality" query fires the REAL `code-review`
skill over the planted description. Absolute trigger rates measured here are therefore
competitive rates, not isolated ones. Description-ABLATION A/B remains valid (identical
competitor field per variant). Use --description on the runner for variants.
