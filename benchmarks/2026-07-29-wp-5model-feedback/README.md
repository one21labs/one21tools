# writing-plans across five models, on one real plan (2026-07-29, THROWAWAY)

Owner-requested exploratory run on a throwaway branch. **Not a merge candidate**, and no verdict
here promotes a skill decision on its own.

## Question

Does loading the third-party skill `writing-plans` change the QUALITY OF FEEDBACK a model gives on
a real strategic planning document; does the size of that change differ by model; and how
consistent is each model from run to run? Direction unstated. A null is an equally valid outcome.

Owner framing, 29-Jul-2026: *"I want to see the difference writing-plans makes in terms of effect
size for each model type, and how consistent the output is with and without writing-plans... The
output I'm interested in is the quality of feedback on the plan document for each run."*

## Design

| | |
|---|---|
| Task | ONE task: read `plan.md`, "Give the author your feedback on this plan." |
| `plan.md` | frozen verbatim copy of the owner's active plan as it stood 29-Jul 10:47 |
| Lanes | `fable5` (claude-fable-5), `opus5` (claude-opus-5), `haiku45` (claude-haiku-4-5), `grok` (grok-4.5), `copilot` (copilot CLI, `--model auto`) |
| Arms | `bare` / `wp` (= `writing-plans` body prepended, frontmatter stripped) |
| Reps | 3 |
| Cells | 5 x 2 x 3 = 30 |
| DV | fraction of **20** pre-registered binary criteria met (`criteria.json`) |
| Judges | grok-4.5 and claude, independently, on blinded text |

`metadata.json` + `criteria.json` are the pre-registration of record, committed before any
generation cell ran (commit `7c02324`; per-cell UTC timestamps make the ordering checkable).

### Two model-roster corrections

- **There is no Haiku 5.** Haiku 4.5 is the latest, so that lane runs 4.5.
- **Copilot's `--model` is entitlement-gated on this account** and rejects every explicit id,
  including every spelling of haiku. Per owner direction the lane runs `auto` and records the
  answering model per cell. It resolved to `gpt-5-mini` on **all 6 cells**, so that lane's
  comparison is interpretable rather than confounded by routing.

### Choices that protect the comparison

- **Uniform prompt-prepend on every lane**, not each CLI's native system-prompt flag. Claude has
  `--append-system-prompt` and grok has `--rules`; copilot has no equivalent. A per-lane injection
  mechanism would confound exactly the cross-model effect-size comparison the run is for.
  *Labeled limitation:* this measures the skill body as prepended context.
- **No tools on any lane**, every cell from an empty scratch cwd outside the repo. Tool carve-outs
  are not equivalent across three CLIs, so live exploration would confound the model comparison
  with a CLI-plumbing comparison. *Labeled limitation:* measures feedback given fixed context,
  not tool-directed exploration.
- **Environment stripped.** The harness runs under Claude Code with `CLAUDE_EFFORT=xhigh`;
  inherited, that would have handed the three Claude lanes a reasoning budget grok and copilot
  never get. `clean_env()` strips it and pins effort to `medium`.
- **Prompt bytes asserted identical** within each arm across all lanes and reps, by recorded
  sha256 prefix.

## The instrument

`criteria.json` draft-1 (18 criteria) was **adversarially audited before any spend** on four
lenses — treatment bias, judgeability, ceiling/floor discrimination, and confounds/gaming — and
replaced by the hardened 20-criterion set. The audit found 6 drafts saturating in both arms, 4
mirroring the treatment's own checklist (which would have measured leakage, not quality), and 1
rigged against it.

The set is deliberately **two-sided**: C6 and C8 can only move *down* for the treatment
(inappropriate code-plan transfer; supplying a rewrite instead of feedback), and C11 (propose
something to CUT) runs against the skill's purely-additive doctrine. C7 is the upward mirror of
C6 so structural transfer can also be recorded when it is *right*.

Three pre-registered subsets are reported separately (`content_bearing`, `structure`, `task_fit`)
because **an effect present in the full set but absent in `content_bearing` is verbosity or
formatting transfer, not better feedback.**

### Blinding is load-bearing here

`writing-plans` does not merely advise — it **mandates** a self-identifying announcement
("Announce at start: 'I'm using the writing-plans skill…'"), plus `superpowers:` namespaces and a
`docs/superpowers/plans/` save path. `tells.py` strips identity tells only and grading **halts**
on any residual. Measured on the real run: the bare arm needed **no** stripping, while **7 of 15
treatment cells did** (929 chars: 5 announcements, 8 save-path references, 20 skill-name
mentions). Residual tells after stripping: **0 in both arms**.

Structural markers the skill encourages (checkbox syntax, `Consumes:`/`Produces:`) are
deliberately **not** stripped — that would delete real content — and are **measured** instead
(`markers.py`) so structural transfer can be separated from quality analytically. Consequence,
stated rather than hidden: a judge may still infer the arm from structure.

## Statistics, and why not five separate n=3 t-tests

At 3 vs 3 the smallest reliably detectable effect is **3.03 standard deviations** (two-sided 95%,
80% power, df=4) — about four times Cohen's "large". Worse, three identical rep scores give a cell
a standard deviation of exactly 0, which the July 2026 run of this benchmark family produced in
*every* cell, and a t-test on a zero variance estimate reports infinite significance for any
difference at all.

`assaystats.py` therefore treats **model as a blocking factor** and pools within-cell variance
across all ten cells, giving **df=20** instead of df=4:

- the per-model detectable effect falls from 3.03 to **2.40** pooled SDs;
- the skill's average effect across models is testable at **1.08** pooled SDs;
- a zero-variance cell no longer breaks its own comparison.

Each cell's own SD is still reported separately, as the consistency deliverable.

**Every comparison reports its own `mde80`** — the smallest difference it would call reliably. A
result below its own `mde80` means the design was underpowered for the effect it saw, *not* that
the effect is absent. "Not significant at n=3, therefore negligible" is affirming the null and is
not a conclusion this design supports.

## Kill conditions (pre-registered)

| condition | rule |
|---|---|
| ceiling | bare mean >= 0.80 -> instrument INSENSITIVE, a null is not evidence of no effect |
| floor | bare mean <= 0.20 -> criteria too hard to discriminate |
| correctness | no arm promoted if its mean false-assertion count exceeds the other's |
| judge flip | verdicts differing between judges -> EXPLORATORY, nothing promoted |
| blinding | any residual arm tell halts grading outright |
| copilot routing | if `auto` varies within the lane, that lane is descriptive only |
| length | if correlation(score, length) > 0.5, arm delta additionally reported length-restricted |

## Reproduce

```bash
python3 generate.py --pilot          # 5 bare cells -> pilot-outputs/  (saturation + cost screen)
python3 generate.py                  # 30 cells     -> outputs/        (cost-gated, resumable)
python3 grade.py --judges grok       # -> graded/cells-grok.jsonl   + blinding-audit.json
python3 grade.py --judges claude     # -> graded/cells-claude.jsonl
python3 analyze.py                   # -> results.json + results.txt
python3 -m unittest tells_test assaystats_test markers_test
```

## A defect this run found in shipped code

Tool-denial flags are **not portable** across these three CLIs, and the pilot caught two lanes
running unsandboxed. Measured with a planted-file probe:

- **grok's `--disallowed-tools` is a no-op.** A probe cell read the planted file and returned its
  contents — both with grok's real lowercase tool names (`read_file`, `list_dir`, `grep`,
  `run_terminal_command`) and with the CamelCase names `skill-bench/scripts/lib/judge.py` passes.
  The allow-list form `--tools todo_write` does hold.
- **copilot's bare `--available-tools` did not strip tools** either, and `--available-tools=none`
  merely pushed the model onto `curl file://`. `--excluded-tools=` with the full vocabulary holds.
- **claude's `--disallowedTools` with `deny_tools.txt` does hold** (probe: "CANNOT READ"). The
  three Claude lanes were never affected.

**This is live in the shipped library**: `lib/judge.py`'s `GrokJudge` and `CopilotJudge` both
claim a hermetic sandbox their flags do not deliver. For pure-text grading the practical exposure
is low, but the stated guarantee is false. Out of scope for this throwaway branch — flagged for
the owner.

Cells now record tool activity per cell (copilot invocation count, claude `num_turns`) so
hermeticity is evidenced rather than assumed.

## Cost

Generation: **$4.36** measured over 30 cells against a $25 pre-registered ceiling (fable5 ~$0.29,
opus5 ~$0.26, haiku45 ~$0.03 per cell; grok and copilot are subscription-billed and report no
per-call figure). Pilot: $0.78 across two rounds.

## Results (run 2026-07-29; 30 cells, 0 ERROR cells, blinding clean)

**`writing-plans` made feedback WORSE on this task, and both judges agree exactly.**

| | grok judge | claude judge |
|---|---|---|
| skill effect, averaged over 5 models | **-0.090** [-0.151, -0.029] p=0.006 | **-0.090** [-0.141, -0.039] p=0.0015 |
| verdict | **HARMFUL** | **HARMFUL** |
| mde80 for that comparison | 0.086 | 0.072 |
| pooled within-cell SD | 0.0801 (df=20) | 0.0671 (df=20) |

Cross-judge agreement **0.917** over 600 criterion-cells; no verdict flip, so the headline is
judge-robust.

### Quality by model (judge-robust, very strong)

| model | grok judge | claude judge |
|---|---|---|
| opus5 | 0.942 | 0.942 |
| grok | 0.925 | 0.900 |
| fable5 | 0.875 | 0.867 |
| haiku45 | 0.717 | 0.717 |
| copilot (`gpt-5-mini`) | 0.333 | 0.317 |

Model main effect F(4,20) = 60.2 / 87.2, p ~ 0. The models differ far more from each other than
the skill moves any of them.

### Per-model skill effect — NOT judge-robust, treat as exploratory

| model | grok delta | claude delta |
|---|---|---|
| copilot | **-0.200 HARMFUL** | **-0.367 HARMFUL** |
| haiku45 | **-0.167 HARMFUL** | -0.067 INCONCLUSIVE |
| fable5 | -0.117 INCONCLUSIVE | -0.067 INCONCLUSIVE |
| grok | +0.017 INCONCLUSIVE | +0.033 INCONCLUSIVE |
| opus5 | +0.017 INCONCLUSIVE | +0.017 INCONCLUSIVE |

The model x arm interaction is **not judge-robust**: F(4,20)=2.42 p=0.082 (grok, not significant)
versus F(4,20)=8.69 p=0.0003 (claude, significant). Per the pre-registered kill condition, the
per-model ranking is **exploratory** and is not promoted.

### Consistency (run-to-run SD over 3 reps)

Most consistent: `opus5` and `grok` (SD 0.03-0.06 in both arms). Least consistent: **`haiku45`
under the treatment** — SD 0.202 with runs of 0.750 / 0.400 / 0.750 (grok judge), against a bare
SD of 0.050. On the claude judge `haiku45` bare was *perfectly* consistent (SD 0.000) and the
treatment took it to SD 0.144. **The skill destabilised the smallest model markedly** while
leaving the larger ones' consistency unchanged.

### Mechanism (both judges, cell-cited)

The largest single driver is **C6, inappropriate transfer of code-plan conventions**: bare 1.00 ->
wp 0.60 (grok), 0.87 -> 0.53 (claude). **7 of 15 treatment cells** demanded that a strategic
governance plan adopt test-first cycles, 2-5 minute task granularity, per-step code blocks, or
file-by-file decomposition. Judge-quoted example (`copilot-wp-r3`): *"For each task: include exact
files to create/modify, failing tests (code), run commands, minimal implementation (code),
expected pytest/git output"* — asked of P1-P3, which are decisions, not code.

The second driver is **crowding out**: C15 (engage with the plan's open decisions on their merits)
falls 0.80 -> 0.47 (grok) and 0.93 -> 0.67 (claude), and mechanical grounding drops too —
distinct plan identifiers cited 20.2 -> 18.3, density per 1k chars 11.4 -> 9.1. Meanwhile the
skill's own vocabulary arrives: `TDD` in 5/15 treatment cells, `failing test` 4/15, `bite-sized`
4/15, `pytest` 3/15, distinct treatment markers 0.13 -> 2.53.

Subsets confirm the harm is in **content, not form**: `content_bearing` -0.067 (grok) / **-0.121
HARMFUL** (claude), while `structure` is flat-to-positive (-0.083 / +0.050). The skill did add
structure; it subtracted engagement.

### THE load-bearing limitation: a ceiling on the upside

The pre-registered ceiling condition **FIRES** on the grok judge (bare-arm mean 0.803 >= 0.80) and
narrowly misses on claude (0.793). Per lane, upward headroom was **0.067 for fable5 and opus5 and
0.083 for grok** — far below the per-model mde80 of 0.161-0.193.

**So for the three strongest models an IMPROVEMENT was undetectable by construction.** Their flat
results must be read as "no benefit large enough to fit in the remaining 7-12 points", *not* as
"no benefit". The design could detect harm on those lanes and did; it could not have detected
help. A fair test of the upside needs a harder task or a lower baseline.

Length fires its flag too (r = 0.75 > 0.5) but cannot explain the result: the correlation is
driven by *between-model* differences (copilot 668 chars scoring 0.32; grok 9.7k chars scoring
0.91), and within the arm contrast length **rose** (+205 chars) while score **fell**.

### Sample size, answered from the measured variance

Measured pooled within-cell SD is 0.067-0.080 — genuinely non-zero, unlike July's 0.000, so here
reps *do* buy power.

| question | reps needed | reps run |
|---|---|---|
| the average effect across 5 models (-0.090) | **3** | 3 |
| the same effect for ONE model | **13** | 3 |
| half that effect (0.05), pooled | 9 | 3 |
| half that effect (0.05), one model | 41 | 3 |

**3 reps was exactly sufficient for the pooled question and roughly a quarter of what the
per-model question needs.** The observed -0.090 exceeds the pooled mde80 (0.072-0.086) but sits
below the per-model mde80 (0.161-0.193), which is precisely why the interaction is not
judge-robust.

Raw records: `outputs/`, `pilot-outputs/`, `graded/`, `results.json`, `results.txt`.

## Restore note (26-Oct-2026)

Restored to main as the record (#331). This supersedes the "THROWAWAY" and "Not a merge
candidate" wording of lines 1-3, and "this throwaway branch" at line 148.

The scripts import `skill-bench/scripts/lib` (`generate.py:37`, `grade.py:22`), which left main
with ADR 0102, so the commit that lands this dir cannot run it. `8bb1b8b`, the commit it was
restored from, is on no branch. To reproduce, copy this dir into `benchmarks/` in a checkout of
`bd3ebd9` (#321): its `skill-bench/` is byte-identical to `8bb1b8b`'s.

Why the bulk stays: `outputs/` and `pilot-outputs/` are the graded cells, so a re-grade or a
judge audit reads them, not the summary. `treatments/writing-plans.SKILL.md` is the exact text
the treatment arm received, which a replay sends byte for byte; `treatments/provenance.json`
records where it came from but cannot reproduce it if upstream changes.
