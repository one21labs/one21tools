# Token/Format Efficiency: Two Cost Surfaces

## Why Efficiency Is First-Class Here

This repo is the main workflow people use to run agentic loops, so every inefficiency compounds
across every user x every iteration. Two levers are first-class, not optional:

- **Context minimalism** — fewer always-loaded tokens via SSoT + progressive disclosure (this
  reference plus SKILL.md's Core Principles).
- **Execution tiering** — cheap/fast models do the bulk work each iteration; reserve the top tier
  for orchestration and judgment (see [subagents.md](subagents.md), "Model Tiering").

This is the one home for the efficiency rationale; other skills cross-reference it, never restate.

## The Two Surfaces

Format choice is a lever for one cost surface only. Confusing the two wastes effort optimizing
the wrong thing.

| Surface | What lives here | Governed by | The only lever |
|---------|------------------|-------------|-----------------|
| Always-loaded CONTEXT | SKILL.md / CLAUDE.md bodies | Char budget (`pdca-workflow/scripts/char-budget.mjs`) | **Cut** content: SSoT + progressive disclosure |
| Stored / agent-read ARTIFACTS | Data files, tool outputs, subagent results | No fixed cap — cost is per-read | **Format** choice (this reference) |

Reformatting SKILL.md/CLAUDE.md prose into a denser data format does not reduce its always-loaded
cost — that surface is bounded by the char cap and reduced only by removing content (see
SKILL.md's Core Principles: Smallest High-Signal Tokens, Progressive Disclosure). Format choice
only pays off for artifacts an agent reads on demand: the more times a format is re-read, the more
a per-read format saving compounds — CLAUDE.md is read once per session, a data file may be read
many times.

## Format Efficiency for Stored Structured Data

Measured token ratios against a pretty-printed JSON baseline (1.0x), for arrays of records:

| Data shape | Best format | Ratio vs pretty-json | Why |
|------------|-------------|----------------------|-----|
| Uniform flat records (same keys, scalar values) | TSV/CSV | **0.45x** | Header written once; no per-record key repetition |
| Uniform flat records | YAML block | 0.80x | Keys repeated per record — not worth switching for this shape |
| Uniform flat records | Minified JSON | 0.82x | Same key-repetition tax as YAML; roughly ties it |
| Text-heavy records (long free-text fields) | JSONL | ~0.92x | Text dominates the byte count; format overhead is noise |

Rules of thumb:
- **Uniform flat records -> TSV/CSV.** The only shape where format switching yields a real win
  (~2x over pretty-json), because the header amortizes across all rows.
- **YAML and minified JSON land within ~2 points of each other for records** (0.80x vs 0.82x) —
  neither is worth migrating to for record data. Reserve YAML for nested, human-EDITED config
  (its win there is editability, not tokens).
- **Text-heavy records: don't bother reformatting.** Prose bytes dominate; keep JSONL (or
  pretty-json if the consumer is human) for safe round-tripping.
- **Never trade machine round-trip safety for marginal byte savings.** A format that is ambiguous
  to parse back (unescaped delimiters in CSV, YAML's typing quirks) can cost more in reconstruction
  and silent corruption than it saves in tokens. Verify round-trip before adopting a denser format
  for anything machine-consumed downstream.

## Prose Density: Dense, Not Caveman

For prose (SKILL.md bodies, CLAUDE.md, subagent reports), the goal is the smallest **high-signal**
tokens — not the fewest tokens outright.

- **Dense-but-well-formed beats compressed.** Full sentences with articles, verbs, and referents
  intact parse reliably. Dropping grammar ("caveman" compression: stripping articles, pronouns,
  connectives) saves few tokens but raises misread risk — the reader (model or human) spends more
  reconstructing intent than the compression saved.
  - Bad: `add auth check bef req proc, fail closed`
  - Good: `Add an auth check before request processing; fail closed.`
  - The good version is barely longer and removes ambiguity about what fails closed and when.
- **The bigger lever is cutting, not compressing.** One paragraph removed via SSoT (state a fact
  once, reference it elsewhere) saves more than compressing ten paragraphs into telegraphese. Apply
  SSoT and progressive disclosure first; only tighten wording on what's left.
- **Signal-per-token, not tokens-per-fact.** A sentence that trades clarity for brevity and forces
  a re-read or a wrong inference has negative signal-per-token, even though it measured fewer
  tokens.

## Applying This

1. Identify which surface you're optimizing: always-loaded (cut) or stored/agent-read (format).
2. For stored structured data: check the data shape against the table above before picking a
   format. Default to JSONL/pretty-json unless the shape is uniform flat records.
3. For prose in either surface: tighten wording only after cutting via SSoT; never sacrifice
   grammar for token count.
