#!/usr/bin/env node
/*
 * scorecard.mjs — ARCHITECTURE ROLE: the repo's Level-3 self-measurement read-out (ADR 0079),
 * the first runnable implementation of the analyze() contract in
 * pdca-workflow/skills/decide/references/metrics-engine.md. Repo-local by design: the shared
 * assumption register (docs/decisions/README.md) records that no runnable engine ships in the
 * plugin — a second consumer implements the contract in its own stack.
 *
 * Instruments (ADR 0079 (b)):
 * - assumption hit-rate: violated / (verified + violated) over `- [outcome]` lines in
 *   docs/decisions/*.md. FIRE/WATCH fire a /decide (a review) — exit stays 0, never a CI block.
 * - still-open share: still-open / all classified outcomes (assumptions minted, never resolved).
 * - outcome-audit coverage: accepted full-tier ADRs older than `ageDays` with no `## Act` are
 *   uncovered (Act-presence is the ship marker, so age is the mechanical proxy for
 *   shipped-but-unaudited). Lite share prints as a readout (lite ADRs carry no Act machinery).
 * - deferred instruments print NOT INSTRUMENTED every run and the aggregate verdict reads
 *   PARTIAL while any miss-class is uninstrumented — silence must never read as coverage.
 *
 * DESIGN CONSTRAINTS (inherited from adr-lint.mjs):
 * - Zero dependencies; parse/analyze are PURE (no fs/process/clock — `today` is injected) so the
 *   decision logic is unit-testable per CLAUDE.md's process-gating-script rule. main() is IO.
 * - Controlled outcome vocabulary (exactly one of verified|violated|still-open per line) is
 *   ENFORCED by adr-lint; here an unparseable line is NOT EVALUATED — listed by adr:line,
 *   excluded from every denominator, never silently dropped and never counted clean.
 * - Exit 0 whenever a report was produced, INCLUDING on FIRE/WATCH — the compass is not a CI
 *   gate (ADR 0079 (a)); do not wire this script into gates.yml. Exit 2 = unreadable dir.
 *
 * TESTING: scorecard.test.mjs (`node --test scripts/*.test.mjs` from the repo root).
 * Usage: node scripts/scorecard.mjs [decisionsDir]   (default: docs/decisions)
 */
import { readFileSync, readdirSync } from "node:fs";
import { join } from "node:path";
import { fileURLToPath } from "node:url";

export const SCORECARD_CONFIG = {
  // Bands are config, not engine (metrics-engine.md): dormant until variance justifies tuning.
  hitRate: { minSample: 5, fireAbove: 0.35, watchAbove: 0.20,
    triggerMsg: "run /decide: systematic premise failure (ADR 0079)" },
  stillOpenShare: { minSample: 5, watchAbove: 0.30,
    triggerMsg: "run /decide: uncheckable-claim drift (ADR 0079)" },
  coverage: { minSample: 5, watchAbove: 0.30, ageDays: 14,
    triggerMsg: "run /decide: outcome-audit coverage decay (ADR 0079)" },
  // Static NOT INSTRUMENTED list — printed every run so a green read-out can never imply
  // these miss-classes are measured (ADR 0079 BREAK-3 guard).
  deferred: [
    { name: "defect-escape", reason: "no mechanical defect marker (no label; squash repo has no reverts)" },
    { name: "owner-intervention rate", reason: "no correction taxonomy; classifying a correction is an LLM call" },
    { name: "summary-truthfulness spot-audit", reason: "reference-veracity ships first (narrower, recorded catch)" },
  ],
};

const OUTCOME_LINE = /^-\s*\[outcome\]\s*(.*)$/;
const VERDICT_WORDS = /\b(verified|violated|still-open)\b/g;

/**
 * Pure parse. `files` is [{ name, text }] for each NNNN-*.md. Returns per-ADR records with
 * classified outcome rows. A line's verdict is the single DISTINCT vocabulary word it carries;
 * zero or several distinct words => "unparsed" (fail-loud downstream).
 */
export function parseAdrs(files) {
  return files.map(({ name, text }) => {
    const fm = text.match(/^---\n([\s\S]*?)\n---/);
    const props = {};
    for (const line of (fm?.[1] ?? "").split("\n")) {
      const m = line.match(/^(\w+):\s*(.*)$/);
      if (m) props[m[1]] = m[2].trim().replace(/^"(.*)"$/, "$1");
    }
    const date = text.match(/^-\s*Date:\s*(\d{4}-\d{2}-\d{2})/m)?.[1] ?? null;
    const outcomes = [];
    text.split("\n").forEach((line, i) => {
      const m = line.match(OUTCOME_LINE);
      if (!m) return;
      const words = [...new Set([...m[1].matchAll(VERDICT_WORDS)].map(w => w[1]))];
      outcomes.push({ adr: name, line: i + 1, verdict: words.length === 1 ? words[0] : "unparsed" });
    });
    return {
      name, status: props.status ?? "", lite: props.tier === "lite",
      date, hasAct: /^## Act/m.test(text), outcomes,
    };
  });
}

const rate = (num, den) => (den === 0 ? null : num / den);

/**
 * Pure decision logic per the metrics-engine.md contract. `today` is an ISO date string —
 * injected, never read from the clock, so runs are reproducible and testable.
 * Returns { rows, triggers, unparsed, deferred, verdictLine }.
 */
export function analyze(adrs, config = SCORECARD_CONFIG, today) {
  const outcomes = adrs.flatMap(a => a.outcomes);
  const unparsed = outcomes.filter(o => o.verdict === "unparsed");
  const n = v => outcomes.filter(o => o.verdict === v).length;
  const verified = n("verified"), violated = n("violated"), stillOpen = n("still-open");

  const ageMs = config.coverage.ageDays * 86400e3;
  const aged = adrs.filter(a => a.status === "accepted" && !a.lite && a.date
    && (new Date(today) - new Date(a.date)) > ageMs);
  const uncovered = aged.filter(a => !a.hasAct);
  const undated = adrs.filter(a => a.status === "accepted" && !a.lite && !a.date);

  const rows = [];
  const triggers = [];
  // One shape for every gated ratio: sample-gate first (unknown != healthy), then bands.
  const gauge = (metric, num, den, { minSample, fireAbove, watchAbove, triggerMsg }, detail) => {
    const value = rate(num, den);
    let status;
    if (value === null) status = "null (zero denominator)";
    else if (den < minSample) status = `not evaluated (n=${den} < minSample ${minSample})`;
    else if (fireAbove !== undefined && value > fireAbove) { status = "FIRE"; triggers.push(`FIRE ${metric}: ${triggerMsg}`); }
    else if (value > watchAbove) { status = "WATCH"; triggers.push(`WATCH ${metric}: ${triggerMsg}`); }
    else status = "healthy";
    rows.push({ metric, value, sample: den, status, detail });
  };

  gauge("hit-rate (violated/resolved)", violated, verified + violated, config.hitRate,
    `${violated} violated / ${verified} verified; still-open excluded from denominator`);
  gauge("still-open share", stillOpen, verified + violated + stillOpen, config.stillOpenShare,
    `${stillOpen} still-open of ${verified + violated + stillOpen} classified`);
  gauge("outcome-audit coverage (uncovered share)", uncovered.length, aged.length, config.coverage,
    `${uncovered.length} of ${aged.length} accepted full ADRs older than ${config.coverage.ageDays}d lack ## Act`
    + (undated.length ? `; ${undated.length} undated excluded (not evaluated)` : ""));
  rows.push({
    metric: "lite share (readout, no band)", value: rate(adrs.filter(a => a.lite).length, adrs.length),
    sample: adrs.length, status: "readout",
    detail: `${adrs.filter(a => a.lite).length} lite of ${adrs.length} ADRs (lite carries no Act machinery)`,
  });

  // Aggregate verdict — gated, not an adjacent note: PARTIAL while any miss-class is
  // uninstrumented or any row is unevaluated; the bare all-clear exists only when every
  // metric was evaluated and clear AND nothing is deferred.
  const unevaluated = rows.filter(r => r.status.startsWith("not evaluated") || r.status.startsWith("null"));
  const parts = [];
  if (config.deferred.length) parts.push(`${config.deferred.length} miss-class(es) uninstrumented`);
  if (unevaluated.length) parts.push(`${unevaluated.length} metric(s) not evaluated`);
  if (unparsed.length) parts.push(`${unparsed.length} unparseable outcome line(s)`);
  const verdictLine = parts.length
    ? `PARTIAL — ${parts.join("; ")}${triggers.length ? `; ${triggers.length} trigger(s) fired` : ""}`
    : (triggers.length ? `${triggers.length} trigger(s) fired` : "No threshold fired — all metrics evaluated and clear");

  return { rows, triggers, unparsed, deferred: config.deferred, verdictLine };
}

function main(argv) {
  const dir = argv.slice(2).find(a => !a.startsWith("--")) ?? "docs/decisions";
  let files;
  try {
    files = readdirSync(dir)
      .filter(f => /^\d{4}-.*\.md$/.test(f))
      .map(name => ({ name, text: readFileSync(join(dir, name), "utf8").replace(/\r\n/g, "\n") }));
  } catch (e) {
    console.error(`scorecard: cannot read ${dir}/ (need NNNN-*.md ADR files): ${e.message}`);
    process.exit(2);
  }
  const { rows, triggers, unparsed, deferred, verdictLine } =
    analyze(parseAdrs(files), SCORECARD_CONFIG, new Date().toISOString().slice(0, 10));

  console.log(`scorecard — ${dir}/ (ADR 0079; compass, not a CI gate)`);
  for (const r of rows) {
    const val = r.value === null ? "n/a" : `${(r.value * 100).toFixed(1)}%`;
    console.log(`  ${r.metric}: ${val} [${r.status}] — ${r.detail}`);
  }
  for (const o of unparsed)
    console.log(`  UNPARSEABLE OUTCOME (not evaluated, excluded): ${o.adr}:${o.line}`);
  for (const d of deferred)
    console.log(`  NOT INSTRUMENTED: ${d.name} — ${d.reason}`);
  for (const t of triggers) console.log(`  TRIGGER: ${t}`);
  console.log(`verdict: ${verdictLine}`);
}

if (process.argv[1] === fileURLToPath(import.meta.url)) main(process.argv);
