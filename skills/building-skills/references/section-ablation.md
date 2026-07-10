# Section Ablation — which content earns its place

Read this when a skill is always-in-context (or near its char cap) and you need to know WHICH
content earns its place, not just whether the whole earns its cost — the deeper cut beyond
[empirical-evals.md](empirical-evals.md)'s whole-skill verdict.

For a skill that is always-in-context or near its char cap, measure WHICH content earns its
place, not just whether the whole does. Treat sections (or each references/*.md) as factors:
benchmark variants with one section removed per variant (one-factor-at-a-time), same eval
set, same replicates, and compare verdicts. A section whose removal moves the delta less
than the CI width is a cut candidate — the empirical form of "every char earns its place."
Full factorial designs over many sections multiply run cost fast; ablate the few sections
you actually doubt, and only for skills whose cost makes the answer worth buying.

The same method applies to **any always-loaded prose**, not just a SKILL.md — a repo `CLAUDE.md`
or the pdca-init `claude-md-template.md` it seeds. These pay their cost on EVERY request, so
ablation matters more; vary the prose per variant over a small task set the section targets.
**Hold the executor's base framing NEUTRAL** — prose ablation is framing-sensitive: a biased
framing swamps the treatment (one section measured +0.17/0.00/+0.375 across
tool-denied/implement-biased/neutral framings; ADR 0024). This is the VERIFY step of retrospect ->
PDCA: `/retrospect` proposes an always-loaded line, `/decide`'s verify runs the ablation, the same
bar decides — removal moving the delta less than the CI width means the line does not earn its cost
(cut or relocate to a gate/script); a line whose absence measurably drops the delta stays.
Add-what-recurs, cut-what-does-not: keep the always-loaded surface minimal.
