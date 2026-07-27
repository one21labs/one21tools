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
 * - gate hits by gate (ADR 0080): the local gate hooks append one line per FIRING (deny/exit-2)
 *   to docs/pdca/gate-hits.txt; parseGateHits below is the line format's ONE home (hooks cite
 *   it). Readout only — no bands until variance is known (ADR 0080 (d)); a malformed line is
 *   fail-loud (listed, folds into PARTIAL); an ABSENT log post-ship is a true zero, stated. Counts
 *   are lifetime, so hits from a gate no wired guard can still emit are marked RETIRED — a deleted
 *   guard must never read as one that catches things.
 * - guard-liveness readout (ADR 0086): for guards DECLARED boundary-coupled (the `# liveness:`
 *   header line each wired hook carries; grammar home: check-gate-tests.mjs), compare an
 *   independently logged expected series against the guard's observed firings — wired +
 *   expected>0 + observed=0 prints NOT FIRING. Guards declared per-event-exempt are listed,
 *   never silence-inferred dead (a deny guard at zero hits is healthy); wired guards with NO
 *   valid declaration are listed as rung NONE — never presented as watched (ADR 0086 (e)).
 *   Readout only, never a gate; an unavailable count source prints not-evaluated, never zero.
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
import { readFileSync, readdirSync, existsSync } from "node:fs";
import { join } from "node:path";
import { execFileSync } from "node:child_process";
import { fileURLToPath } from "node:url";
import { HOOK_REGISTRATIONS, LIVENESS_CLASSES, extractRegisteredHooksDetailed, parseLivenessDeclaration } from "./check-gate-tests.mjs";

export const SCORECARD_CONFIG = {
  // Bands are config, not engine (metrics-engine.md): dormant until variance justifies tuning.
  hitRate: { minSample: 5, fireAbove: 0.35, watchAbove: 0.20,
    triggerMsg: "run /decide: systematic premise failure (ADR 0079)" },
  stillOpenShare: { minSample: 5, watchAbove: 0.30,
    triggerMsg: "run /decide: uncheckable-claim drift (ADR 0079)" },
  coverage: { minSample: 5, watchAbove: 0.30, ageDays: 14,
    triggerMsg: "run /decide: outcome-audit coverage decay (ADR 0079)" },
  // Boundary-coupled liveness comparisons (ADR 0086 (a)) main() knows how to count. The
  // per-guard CLASSIFICATION lives in each hook's `# liveness:` header (its one home); this
  // table only parameterizes the expected/observed sources for the boundary-coupled ones.
  // muda-review is a workflow guard, not a hook, so its classification is declared here.
  liveness: [
    { series: "session-end", guard: ".claude/hooks/session-end-log.sh",
      wiredSince: "2026-07-20",  // ADR 0081 wiring landed on main 2026-07-20T05:36Z (b3afdb8)
      expectedDesc: "distinct Claude-Session commit trailers in window",
      observedDesc: "session-end lines" },
    { series: "retrospect-spawn", guard: "pdca-workflow/hooks/spawn-log.sh",
      wiredSince: "2026-07-20",  // retrospect arm + Retrospect-Run token shipped with ADR 0081
      expectedDesc: "distinct Retrospect-Run commit trailers",
      observedDesc: "retrospect skill-spawn/agent-spawn lines" },
    { series: "muda-review", guard: ".github/workflows/claude-review.yml",
      wiredSince: "2026-07-20",  // first observed advisory comment 2026-07-20T06:31Z
      expectedDesc: "merged PRs in window",
      observedDesc: "merged PRs carrying a github-actions[bot] advisory comment" },
  ],
  // Static NOT INSTRUMENTED list — printed every run so a green read-out can never imply
  // these miss-classes are measured (ADR 0079 BREAK-3 guard).
  deferred: [
    { name: "defect-escape", reason: "no mechanical ESCAPE marker — gate-hits measure the caught side only (ADR 0080); squash repo has no reverts" },
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

// ONE home of the gate-hits line format (ADR 0080 (c)) — every gate hook cites this. A line is
// `<ISO-8601 UTC> gate-hit <gate-name> <context…>`; context is free text to end of line.
const GATE_HIT_LINE = /^(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z) gate-hit (\S+)(?: (.*))?$/;

/**
 * Pure parse of docs/pdca/gate-hits.txt. `text` null/undefined = file absent (post-ship that is
 * a TRUE zero — the hooks log every fire — distinct from uninstrumented). Blank lines skipped;
 * any other non-matching line is malformed: fail-loud downstream, never dropped.
 */
export function parseGateHits(text) {
  if (text === null || text === undefined) return { present: false, hits: [], malformed: [] };
  const hits = [], malformed = [];
  text.replace(/\r\n/g, "\n").split("\n").forEach((line, i) => {
    if (!line.trim()) return;
    const m = line.match(GATE_HIT_LINE);
    if (m) hits.push({ date: m[1], gate: m[2], context: m[3] ?? "" });
    else malformed.push(i + 1);
  });
  return { present: true, hits, malformed };
}

/**
 * Pure count of session-log lines whose ISO timestamp is >= `since` (lexicographic on ISO-8601)
 * and whose post-timestamp remainder matches `pattern`. null/absent text counts zero.
 */
export function countSessionLogLines(text, pattern, since = "") {
  if (!text) return 0;
  return text.replace(/\r\n/g, "\n").split("\n").filter(l => {
    const m = l.match(/^(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z) (.*)$/);
    return m && m[1] >= since && pattern.test(m[2]);
  }).length;
}

/**
 * Pure decision logic per the metrics-engine.md contract. `today` is an ISO date string —
 * injected, never read from the clock, so runs are reproducible and testable.
 * Returns { rows, triggers, unparsed, gateHits, deferred, verdictLine }. `gateHits` is a
 * parseGateHits() result; omitted = absent log (backward-compatible). `liveness` (ADR 0086),
 * when provided, is { hooks: [{path, classification}], guardText: <every wired guard's text,
 * concatenated — the retired-gate-name source>, series: [{series, guard, wired, expected,
 * observed, evaluated, reason?, detail}] } — counts are INJECTED (main computes them) so this
 * stays clock/fs/network-free.
 */
export function analyze(adrs, config = SCORECARD_CONFIG, today, gateHits = parseGateHits(null), liveness = null) {
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
  // Gate hits by gate (ADR 0080 (d)): readout, no bands until variance is known. `display`
  // overrides the % formatting in main — this is a count, not a rate.
  const byGate = {};
  for (const h of gateHits.hits) byGate[h.gate] = (byGate[h.gate] ?? 0) + 1;
  // The log is append-only and lifetime, so a DELETED guard keeps its historical hits forever and
  // reads as one that still catches things. Every emitter names itself as a literal in its own
  // text, so a gate name absent from every wired guard can no longer fire: mark it, never drop it
  // (the log is the record). No liveness read = no wired-guard text = no retirement claimed.
  // Membership is by TOKEN, not substring. `includes` answers "does this character sequence
  // appear anywhere", which is a different question: a short gate name like `hit` or `gate` is a
  // substring of `hook_gate_hit budget-edit-guard`, so it would read as live forever no matter
  // which guard emitted it — the readout's own failure mode, one level down. So the wired text is
  // TOKENISED on the identifier character class and membership is asked of the token set: a name
  // counts as emitted only when it appears as a whole token. (Not a `\b` search, which is weaker.
  // The example first given here was false: `_` IS a word character, so `\bhit\b` does NOT match
  // inside `hook_gate_hit`. The true one is `\bedit\b`, which DOES match inside `budget-edit-guard`
  // — so a deleted gate named `edit` would read as live forever. The tokenizer keeps
  // `budget-edit-guard` whole and answers "is one of these", not "appears somewhere".)
  const emitted = liveness?.guardText == null ? null
    : new Set(liveness.guardText.match(/[A-Za-z0-9_.-]+/g) ?? []);
  const retired = (g) => emitted != null && !emitted.has(g);
  rows.push({
    metric: "gate hits by gate (lifetime readout, no band)", value: null, display: `${gateHits.hits.length} hit(s)`,
    sample: gateHits.hits.length, status: "readout",
    detail: gateHits.present
      ? (gateHits.hits.length
        ? Object.entries(byGate).sort((a, b) => b[1] - a[1])
          .map(([g, n]) => `${g} ${n}${retired(g) ? " (RETIRED — no wired guard emits this name)" : ""}`).join(", ")
        : "log present, zero hits")
      : "no gate-hits log — zero hits since instrumentation (ADR 0080), not uninstrumented",
  });

  // Guard-liveness readout (ADR 0086): NOT FIRING only on wired + expected>0 + observed=0;
  // per-event-exempt guards are listed, never silence-inferred; undeclared wired guards are
  // stated as rung NONE, never presented as watched (0086 (e)).
  let notFiring = [], undeclaredGuards = [];
  if (liveness) {
    for (const s of liveness.series) {
      let status;
      if (!s.evaluated) status = `not evaluated (${s.reason ?? "source unavailable"})`;
      else if (s.wired && s.expected > 0 && s.observed === 0) { status = "NOT FIRING"; notFiring.push(s.series); }
      else status = "readout";
      rows.push({
        metric: `liveness: ${s.series}`, value: null,
        display: s.evaluated ? `${s.observed} observed / ${s.expected} expected` : "n/a",
        sample: s.evaluated ? s.expected : 0, status,
        detail: `${s.guard}${s.detail ? ` — ${s.detail}` : ""}`,
      });
      if (status === "NOT FIRING") triggers.push(
        `NOT-FIRING liveness ${s.series}: wired guard, ${s.expected} expected boundary event(s), zero observed — root-cause before trusting green (ADR 0086)`);
    }
    const exempt = liveness.hooks.filter(h => h.classification === "per-event-exempt").map(h => h.path);
    if (exempt.length) rows.push({
      metric: "liveness-exempt guards (declared per-event, ADR 0086 (b))", value: null,
      display: `${exempt.length} guard(s)`, sample: exempt.length, status: "readout",
      detail: `zero hits is a legitimate state for: ${exempt.join(", ")}`,
    });
    // A guard declared boundary-coupled but absent from the configured series produces NO row of
    // any kind — more silent than "undeclared", because the declaration reads as watched while
    // nothing watches. Counted with the undeclared: rung NONE either way (ADR 0086 (e)).
    const seriesGuards = new Set(liveness.series.map(s => s.guard));
    const unwatchedCoupled = liveness.hooks
      .filter(h => h.classification === "boundary-coupled" && !seriesGuards.has(h.path))
      .map(h => `${h.path} (declared boundary-coupled, no configured series)`);
    undeclaredGuards = [
      ...liveness.hooks.filter(h => !LIVENESS_CLASSES.includes(h.classification)).map(h => h.path),
      ...unwatchedCoupled,
    ];
    if (undeclaredGuards.length) rows.push({
      metric: "liveness UNDECLARED wired guards (rung NONE, ADR 0086 (e))", value: null,
      display: `${undeclaredGuards.length} guard(s)`, sample: undeclaredGuards.length, status: "readout",
      detail: `${undeclaredGuards.join(", ")} — NOT watched; their silence is unjudged`,
    });
  }

  // Aggregate verdict — gated, not an adjacent note: PARTIAL while any miss-class is
  // uninstrumented or any row is unevaluated; the bare all-clear exists only when every
  // metric was evaluated and clear AND nothing is deferred.
  const unevaluated = rows.filter(r => r.status.startsWith("not evaluated") || r.status.startsWith("null"));
  const parts = [];
  if (config.deferred.length) parts.push(`${config.deferred.length} miss-class(es) uninstrumented`);
  if (unevaluated.length) parts.push(`${unevaluated.length} metric(s) not evaluated`);
  if (unparsed.length) parts.push(`${unparsed.length} unparseable outcome line(s)`);
  if (gateHits.malformed.length) parts.push(`${gateHits.malformed.length} unparseable gate-hit line(s)`);
  if (notFiring.length) parts.push(`${notFiring.length} wired guard(s) NOT FIRING`);
  if (undeclaredGuards.length) parts.push(`${undeclaredGuards.length} wired guard(s) undeclared for liveness`);
  const verdictLine = parts.length
    ? `PARTIAL — ${parts.join("; ")}${triggers.length ? `; ${triggers.length} trigger(s) fired` : ""}`
    : (triggers.length ? `${triggers.length} trigger(s) fired` : "No threshold fired — all metrics evaluated and clear");

  return { rows, triggers, unparsed, gateHits, deferred: config.deferred, verdictLine };
}

/**
 * IO half of the liveness readout (ADR 0086): enumerate wired hooks + their declared
 * classifications + their text (the gate-hits readout's retired-name source), and count each
 * boundary-coupled series' expected/observed from its
 * INDEPENDENT source (git trailers, the session log, the GitHub API). Every count failure
 * degrades to evaluated:false for THAT series — an unavailable source must read as
 * not-evaluated, never as a zero.
 */
function collectLiveness(root, seriesConfig) {
  const read = (rel) => { try { return readFileSync(join(root, rel), "utf8"); } catch { return null; } };
  const regs = HOOK_REGISTRATIONS.flatMap(({ path, pluginRoot }) => {
    const text = read(path);
    return text == null ? [] : extractRegisteredHooksDetailed(text, pluginRoot);
  });
  const texts = new Map([...new Set(regs.map(r => r.path))].map(path => [path, read(path) ?? ""]));
  const hooks = [...texts].map(([path, text]) => ({ path, classification: parseLivenessDeclaration(text) }));
  const wiredPaths = new Set(hooks.map(h => h.path));
  const sessionLog = read("docs/pdca/session-log.txt");
  const git = (...args) => execFileSync("git", args, { cwd: root, encoding: "utf8", stdio: ["pipe", "pipe", "pipe"] });
  const distinctTrailers = (key, since) => new Set(
    git("log", `--since=${since}`, `--format=%(trailers:key=${key},valueonly)`)
      .split("\n").map(s => s.trim()).filter(Boolean)).size;

  const series = [];
  for (const s of seriesConfig) {
    const base = { series: s.series, guard: s.guard };
    try {
      if (s.series === "session-end") {
        series.push({ ...base, wired: wiredPaths.has(s.guard), evaluated: true,
          expected: distinctTrailers("Claude-Session", s.wiredSince),
          observed: countSessionLogLines(sessionLog, /^session-end /, s.wiredSince),
          detail: `${s.observedDesc} vs ${s.expectedDesc} since ${s.wiredSince}` });
      } else if (s.series === "retrospect-spawn") {
        series.push({ ...base, wired: wiredPaths.has(s.guard), evaluated: true,
          expected: distinctTrailers("Retrospect-Run", s.wiredSince),
          observed: countSessionLogLines(sessionLog, /^(skill-spawn|agent-spawn) \S*retrospect$/, s.wiredSince),
          detail: `${s.observedDesc} vs ${s.expectedDesc} since ${s.wiredSince}` });
      } else if (s.series === "muda-review") {
        const gh = (...args) => execFileSync("gh", args, { cwd: root, encoding: "utf8", stdio: ["pipe", "pipe", "pipe"] });
        const mergedNums = new Set(JSON.parse(gh("pr", "list", "--state", "merged", "--limit", "200",
          "--search", `merged:>=${s.wiredSince}`, "--json", "number")).map(p => p.number));
        if (mergedNums.size >= 200) {
          // Fail-loud, never silently truncate (this module's own doctrine): a saturated query
          // cap means the denominator is unknown, not 200.
          series.push({ ...base, evaluated: false, reason: "merged-PR query cap (200) saturated — denominator unknown" });
          continue;
        }
        // --paginate concatenates page arrays back-to-back; splice them into one array (this
        // gh version has no --slurp).
        const commented = new Set(JSON.parse(gh("api", "--paginate",
          `repos/one21labs/one21tools/issues/comments?since=${s.wiredSince}T00:00:00Z&per_page=100`)
          .replace(/\]\s*\[/g, ","))
          .filter(c => c?.user?.login === "github-actions[bot]")
          .map(c => Number((c.issue_url ?? "").split("/").pop()))
          .filter(n => mergedNums.has(n)));
        series.push({ ...base, wired: existsSync(join(root, s.guard)), evaluated: true,
          expected: mergedNums.size, observed: commented.size,
          detail: `${s.observedDesc} vs ${s.expectedDesc} since ${s.wiredSince}` });
      } else {
        series.push({ ...base, evaluated: false, reason: "no counter implemented for this series" });
      }
    } catch {
      series.push({ ...base, evaluated: false, reason: "count source unavailable (git/gh query failed)" });
    }
  }
  return { hooks, guardText: [...texts.values()].join("\n"), series };
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
  // Gate-hits log lives beside the decisions dir (docs/decisions -> docs/pdca, ADR 0080 (c)).
  let gateHitsText = null;
  try { gateHitsText = readFileSync(join(dir, "..", "pdca", "gate-hits.txt"), "utf8"); } catch { /* absent = true zero */ }
  // Liveness inputs (ADR 0086): repo root sits two levels above the decisions dir.
  let liveness = null;
  try { liveness = collectLiveness(join(dir, "..", ".."), SCORECARD_CONFIG.liveness); } catch { liveness = null; }
  const { rows, triggers, unparsed, gateHits, deferred, verdictLine } =
    analyze(parseAdrs(files), SCORECARD_CONFIG, new Date().toISOString().slice(0, 10), parseGateHits(gateHitsText), liveness);

  console.log(`scorecard — ${dir}/ (ADR 0079; compass, not a CI gate)`);
  for (const r of rows) {
    const val = r.display ?? (r.value === null ? "n/a" : `${(r.value * 100).toFixed(1)}%`);
    console.log(`  ${r.metric}: ${val} [${r.status}] — ${r.detail}`);
  }
  for (const o of unparsed)
    console.log(`  UNPARSEABLE OUTCOME (not evaluated, excluded): ${o.adr}:${o.line}`);
  for (const n of gateHits.malformed)
    console.log(`  UNPARSEABLE GATE-HIT LINE (excluded): gate-hits.txt:${n}`);
  for (const d of deferred)
    console.log(`  NOT INSTRUMENTED: ${d.name} — ${d.reason}`);
  for (const t of triggers) console.log(`  TRIGGER: ${t}`);
  console.log(`verdict: ${verdictLine}`);
}

if (process.argv[1] === fileURLToPath(import.meta.url)) main(process.argv);
