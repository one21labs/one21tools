# Pre-registration (2026-10-18, before any generation in this directory)

Goal (owner): fix the mixed terms in engineering-principles, run a bigger test, iterate until
>= 10% improvement.

Fixed instrument (never edited after this file; hashes in prompts.sha256): 13 prompts.
- DEV (iterate on these): ep1-ep6 (skills/engineering-principles/evals/evals.json 1-6).
- HOLDOUT (looked at once, at the end): ep7-ep10 + oos1-oos3 (ep-loophole-oos-hermetic).
Grading: sonnet, blind (arm withheld), grader + adversarial prosecutor, met_final = min.

What may change between rounds: ONLY the skill text's wording -- term choice, definitions,
ordering, plain rephrasing of rules that already exist. No new rules, no content aimed at a
specific eval's expectations. Prompts, expectations, grader prompts, model: frozen.

Metric: per-prompt mean fraction met over reps; effect = candidate - current, mean over prompts.
"10% improvement" = relative: mean(candidate) >= 1.10 * mean(current), on the HOLDOUT set.
Also reported: absolute points and 95% t CI of the per-prompt difference.

Rounds: at most 3 DEV rounds (current vs candidates, REPS=4). The best DEV candidate goes to
ONE HOLDOUT run (without / current / best, REPS=5). If it misses 10% on HOLDOUT, that is the
result: no re-tuning against HOLDOUT.
Known limits: single judge family; DEV is reused across rounds (selection bias, which HOLDOUT
exists to correct).
