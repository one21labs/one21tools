# Metrics engine — `analyze()` contract (spec)

Metrics are a PDCA trigger: a usage signal crossing a threshold should *fire a `/decide`*,
not be eyeballed. This is the **generic engine contract** — the pure decision logic that maps raw
analytics into fired triggers. It is shipped as a spec, not runnable code, because the runnable
form is doubly project-specific (your stack + your analytics provider). You implement `analyze()`
in your stack against this contract; the thresholds, event names, and windows are **your config**,
not part of the engine.

The engine is a **process-gating script**, so per the poka-yoke rule it must ship with a
decision-logic test — the "required cases" matrix below is that test, threshold-independent.

## Shape
```
analyze(signals, config) -> { rows, triggers, ... }
```
- `signals` — the raw provider responses (a breakdown + the conversion pair, below).
- `config` — project-supplied (see "Config"). The engine reads thresholds from here; it hardcodes
  none.
- returns the report `rows` + the `triggers` that fired (each a human string naming the review to
  run, or an all-clear / not-evaluated note).

## The three disciplines (the generic core — get these right)
1. **Decouple windows by metric nature.** A **ratio** that stabilizes fast (e.g. which gate users
   hit most) queries a *short* window for fast iteration; a **rare count** (e.g. a conversion) that
   cannot resolve in a short window queries a *long rolling* window. Same engine, two windows —
   don't force one window on both.
2. **Sample-gate every rate, and `unknown != healthy`.** Below a minimum sample, a rate is noise:
   report it but do **not** evaluate it — state "unknown" / "not evaluated", never "healthy". One
   sale must not fire a pricing pivot.
3. **Never print all-clear on an unevaluated metric.** "No threshold fired" means *all metrics were
   evaluated and clear*. If a metric was left unevaluated (below sample), say so instead — silence
   that reads as health is a defect.

## Config (project supplies all of it)
```
ratioMetric: { event, dimension, window, threshold, triggerMsg }
  # e.g. event "Gate Hit", dimension "feature", window 7d, threshold 50 (% of total),
  #      triggerMsg "run gating review on <dimension value>"
convMetric:  { numeratorEvent, denominator, window, minSample, fireBelow, watchBelow, triggerMsg }
  # e.g. numerator "Pro Activated", denominator visitors, window 30d, minSample 200,
  #      fireBelow 0.5 (%), watchBelow 1.0 (%)
```
Thresholds/events/windows/minSample are domain. The engine logic (ratio over a breakdown, the
two-tier FIRE/WATCH band, the sample gate, the unknown-vs-healthy invariant) is generic.

## Required decision-logic cases (the test matrix — threshold-independent)
A correct `analyze()` must exhibit all of these; instantiate them in your test framework with your
own thresholds:
- ratio trigger **FIRES** when the top dimension's share exceeds `threshold`.
- conversion **FIRES** below `fireBelow` (at/above `minSample`).
- conversion **WATCH** (not FIRE) in the `[fireBelow, watchBelow)` band.
- **silent** ("No threshold fired") only when every metric was evaluated and clear.
- zero denominator → conversion is **null**, fires nothing.
- below `minSample` → conversion **not evaluated**, fires no pivot.
- below `minSample` → output **never** says "No threshold fired" (unknown != healthy).
- the breakdown row key is parsed from the provider's dimension field, not a literal `property`
  key — a regression here blanks every row and silently kills the loop (the load-bearing fixture).

## Wiring
`/decide` step 1 (Inherit) runs the project's metrics command — named in CLAUDE.md, e.g.
`metrics command: <project supplies>` — before any **gating or conversion** judgment call, and
includes the fired triggers in the panel. No metrics command configured = skip the step (the
engine is opt-in).

## Epistemic routing — DERIVED / CITED / MEASURED (doctrine, not a classifier)

Route a claim BEFORE spending on measurement. DERIVED (follows logically from structure or an
existing strong result) needs no fresh run. CITED (an external reference) needs a fetch-verified
source — verification costs minutes; a benchmark costs hours and dollars — with the transfer
caveat that external magnitudes are their-harness-relative. MEASURE only a claim that is
behavioral + transfer-doubtful + decision-changing — the one domain where first-principles
intuition demonstrably fails. A wide-CI null does NOT override a strong derivation: record it
contested-underpowered, not settled. Every MEASURE names its gating decision before spend —
measurement without a decision it can change is spend without a customer. This is judgment
text for the `/decide` Inherit step, not a classifier to build.

## Provider notes (Plausible, as one example)
The reference implementation used the Plausible Stats API v1: a `/breakdown` keyed by `event:props:<dim>`
(the row key is the dimension's last segment, **not** a `property` field) for the ratio, and two
`/aggregate` calls (a custom event count + visitors) for the conversion pair. GA4 / PostHog /
Mixpanel expose the same two shapes (a grouped breakdown + an aggregate) behind a different client —
swap the fetch layer, keep `analyze()`. Keep the provider fetch in a thin adapter so a provider
change never touches the decision logic.
