# 2026-10-18 engineering-principles: STE100 / one-word-one-meaning rewrite — VERDICT: DO NOT ADOPT

Owner question 18-Oct: how much would rewriting the repo in ASD-STE100 improve performance and
token efficiency? Follow-ups: rewrite one skill with one word, one meaning and compare; then fix
the mixed terms, run a bigger test, and iterate until a 10% improvement shows. Result: STE100
costs tokens, and no rewrite of `engineering-principles` beat the current text on held-out
prompts. The one candidate that cleared 10% on the tuning prompts (+17.4%) scored −2.1% on the
held-out set, so its gain was fit to the tuning prompts.

## Result

### 1. Token cost of STE100 (`ste-samples/`)

Three real passages rewritten to STE100 rules (articles kept, full sentences, approved words,
one instruction per sentence). Characters are the repo's budget unit (~4 per token); the
tokenizer download was blocked by the session's network policy.

| sample | source | chars before | chars after | change |
|---|---|---|---|---|
| A | CLAUDE.md Muda block | 1,034 | 1,504 | +45% |
| B | building-skills, Description as Instruction | 1,246 | 1,507 | +21% |
| C | ADR 0081 Decision | 934 | 1,270 | +36% |
| all | | 3,214 | 4,281 | **+33%** |

The repo's terse register is what STE100 forbids, so the rewrite grows text. At +33% the
always-loaded layer (CLAUDE.md + skill frontmatter, ~2,250 tokens) gains ~750 tokens per session,
and CLAUDE.md (5,995 of its 6,000-char cap at the time) would fail `adr-lint`.

### 2. One-word-one-meaning pilot (`phase1/`, tuning prompts ep1-ep6, 3 reps)

| arm | fraction met | d vs without [95% t CI] |
|---|---|---|
| without | 0.320 | |
| current | 0.581 | +0.261 [+0.029, +0.494] |
| plain (terms unified + glossary) | 0.619 | +0.298 [−0.025, +0.621] |

plain − current: +0.037 [−0.110, +0.184]. Not distinguishable.

### 3. Iteration (`phase2/`, pre-registration `phase2/prereg.md`)

| round | prompts | arm vs current | relative | 95% CI (abs) |
|---|---|---|---|---|
| r1 (4 reps) | dev ep1-ep6 | v0-glossary | −0.2% | [−0.100, +0.097] |
| r1 | dev | v1-terms (terms unified, no glossary) | +7.0% | [−0.069, +0.152] |
| r2 (4 reps) | dev | v1-terms | −0.6% | [−0.096, +0.088] |
| r2 | dev | v2-verbs (v1 + "remove" and "list a gap" defined) | +17.4% | [−0.144, +0.374] |
| **h1 (5 reps)** | **holdout ep7-ep10, oos1-oos3** | **v2-verbs** | **−2.1%** | **[−0.045, +0.012]** |

On holdout, without scored 0.633, current 0.757 and v2-verbs 0.741. v2's dev gain came almost
entirely from ep4 (current 0.20, v2 0.80). The holdout prompt on the same theme (oos3, premature
plugin framework) scored 0 in every arm. Per the pre-registration, the holdout run was the one
final read; no round tuned against it.

## How to read it

- **What it supports:** for this skill, unifying terms and defining verbs does not move quality
  on unseen prompts. The holdout CI rules out a +10% effect. The skill itself still beats
  without on holdout (+0.124), so the instrument can see a skill effect.
- **What it does not support:** a claim that plain wording never helps. One skill, 13 prompts,
  and one judge family.
- **The open hypothesis:** rules phrased as "no X" may be read as "make X smaller or faster".
  The v2 definition of "remove" moved ep4 but nothing on holdout. It needs fresh prompts, not
  more rounds on these.

## Limits

- Generators and judges were all sonnet (single family); the grok co-judge was not installed.
- No user-level CLAUDE.md existed in the run container, so no arm loaded user memory; the
  harness's relocation switch had nothing to move.
- The pre-registration files were written before each phase's generation but are first
  committed here with the results, so git does not timestamp them ahead of the runs.
  `phase2/prompts.sha256` fixes the instrument; `sha256sum -c` passes on the committed files.
- Not scaffolded from `skill-bench/templates/`: phase 1 adapts the ep-slim-remeasure harness,
  and phase 2 is a standalone `claude -p` runner (`phase2/run.py`). The grader and prosecutor
  prompts mirror `benchmarks/2026-07-08-skills-hermetic/grade.workflow.js`, and
  met_final = min(grader, prosecutor).
- h1: 8 of the 15 oos3 cells got no parseable prosecutor JSON. All 8 were cells the grader
  already scored 0 (one-expectation prompt), so min() is unchanged and they are excluded from
  the table above.
- Treatment = SKILL.md body + 3 references (ssot-enforcement, design-review,
  root-cause-analysis), the ep-slim-remeasure construction at HEAD 84629e3. The shipped skill's
  other references were absent in every arm. `treatments.sha256` pins every treatment's bytes;
  phase 2's `current` and `v0-glossary` arms are byte-identical to phase 1's `with-current` and
  `with-plain`, so `phase2/run.py` reads those files rather than a second copy.

## Reproduce

```
cd phase1 && bash harness.sh && python3 grade.py && python3 aggregate.py
cd phase2 && python3 run.py r1 current,v0-glossary,v1-terms dev 4 && python3 report.py r1 current
python3 run.py r2 current,v1-terms,v2-verbs dev 4 && python3 report.py r2 current
python3 run.py h1 without,current,v2-verbs holdout 5 && python3 report.py h1 current
```
