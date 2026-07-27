/*
 * scorecard.test.mjs — proves scorecard's decision logic (ADR 0079): the metrics-engine.md
 * required-cases matrix instantiated with this repo's config, plus scorecard-specific guards.
 * Run: node --test scripts/*.test.mjs from the repo root.
 */
import { test } from "node:test";
import assert from "node:assert/strict";
import { readFileSync, readdirSync } from "node:fs";
import { join } from "node:path";
import { parseAdrs, parseGateHits, analyze, countSessionLogLines, SCORECARD_CONFIG } from "./scorecard.mjs";

const TODAY = "2026-07-18";

// Synthetic ADR builder: `outcomes` is a list of verdict words (or raw line text).
const adrFile = (id, { status = "accepted", lite = false, date = "2026-06-01", act = true, outcomes = [] } = {}) => ({
  name: `${id}-x.md`,
  text: [
    "---", `id: ${id}`, `title: "t"`, `status: ${status}`, ...(lite ? ["tier: lite"] : []), `summary: "s"`, "---",
    `# ${id} — t`, ...(date ? [`- Date: ${date}`] : []),
    ...(act ? ["## Act (post-ship)", ...outcomes.map(o => `- [outcome] premise text — ${o}.`)] : []),
  ].join("\n"),
});

// A config where everything is instrumented and evaluable — for isolating single cases.
const bareConfig = (over = {}) => ({
  hitRate: { minSample: 2, fireAbove: 0.35, watchAbove: 0.2, triggerMsg: "hit" },
  stillOpenShare: { minSample: 2, watchAbove: 0.3, triggerMsg: "open" },
  coverage: { minSample: 1, watchAbove: 0.3, ageDays: 14, triggerMsg: "cov" },
  deferred: [],
  ...over,
});

test("hit-rate FIRES above fireAbove at/above minSample", () => {
  const adrs = parseAdrs([adrFile("0001", { outcomes: ["verified", "violated", "violated", "verified"] })]);
  const { rows, triggers } = analyze(adrs, bareConfig(), TODAY);
  assert.equal(rows[0].status, "FIRE");
  assert.ok(triggers.some(t => t.startsWith("FIRE hit-rate")));
});

test("hit-rate WATCH (not FIRE) in the (watchAbove, fireAbove] band", () => {
  const adrs = parseAdrs([adrFile("0001", { outcomes: ["violated", "verified", "verified", "verified"] })]);
  const { rows, triggers } = analyze(adrs, bareConfig(), TODAY); // 1/4 = 0.25
  assert.equal(rows[0].status, "WATCH");
  assert.ok(!triggers.some(t => t.startsWith("FIRE")));
});

test("still-open share WATCHes above its band; still-open never enters the hit-rate denominator", () => {
  const adrs = parseAdrs([adrFile("0001", { outcomes: ["verified", "verified", "still-open", "still-open"] })]);
  const { rows } = analyze(adrs, bareConfig(), TODAY);
  assert.equal(rows[0].detail, "0 violated / 2 verified; still-open excluded from denominator");
  assert.equal(rows[0].sample, 2); // survivorship guard: denominator is resolved-only
  assert.equal(rows[1].status, "WATCH"); // 2/4 = 0.5 > 0.3
});

test("silent all-clear ONLY when every metric evaluated and clear and nothing deferred", () => {
  const adrs = parseAdrs([adrFile("0001", { outcomes: ["verified", "verified", "verified"] })]);
  const clear = analyze(adrs, bareConfig(), TODAY);
  assert.equal(clear.verdictLine, "No threshold fired — all metrics evaluated and clear");
  // Same corpus, one instrument deferred: the aggregate must be PARTIAL, never all-clear.
  const partial = analyze(adrs, bareConfig({ deferred: [{ name: "defect-escape", reason: "r" }] }), TODAY);
  assert.match(partial.verdictLine, /^PARTIAL — 1 miss-class\(es\) uninstrumented/);
});

test("zero resolved outcomes -> hit-rate null, fires nothing", () => {
  const adrs = parseAdrs([adrFile("0001", { outcomes: [] })]);
  const { rows, triggers, verdictLine } = analyze(adrs, bareConfig(), TODAY);
  assert.equal(rows[0].value, null);
  assert.equal(triggers.length, 0);
  assert.notEqual(verdictLine, "No threshold fired — all metrics evaluated and clear");
});

test("below minSample -> not evaluated, fires no pivot, and never folds into an all-clear", () => {
  const adrs = parseAdrs([adrFile("0001", { outcomes: ["violated"] })]); // 1/1 = 100% but n=1
  const cfg = bareConfig();
  cfg.hitRate.minSample = 5;
  const { rows, triggers, verdictLine } = analyze(adrs, cfg, TODAY);
  assert.match(rows[0].status, /^not evaluated/);
  assert.ok(!triggers.some(t => t.includes("hit")));
  assert.match(verdictLine, /^PARTIAL/);
});

test("row parsing anchors on line-start '- [outcome]' — prose/summary/indented mentions are not rows", () => {
  // Load-bearing fixture per metrics-engine.md's row-key discipline: a regression here blanks
  // (or over-fills) every row and silently kills the loop.
  const text = ['---', 'id: 0099', 'title: "t"', 'status: accepted',
    'summary: "prose mentioning [outcome] lines"', '---', '# t',
    'Prose discussing `- [outcome]` conventions is not a row.',
    '  - [outcome] indented, so not line-anchored — verified.'].join("\n");
  const [adr] = parseAdrs([{ name: "0099-x.md", text }]);
  assert.equal(adr.outcomes.length, 0);
});

test("ambiguous or missing verdict word -> unparsed: listed by adr:line, excluded from both denominators", () => {
  const file = adrFile("0001", { outcomes: ["verified", "verified"] });
  file.text += "\n- [outcome] shipped fine, all good.\n- [outcome] verified then violated on rerun.";
  const { rows, unparsed } = analyze(parseAdrs([file]), bareConfig(), TODAY);
  assert.deepEqual(unparsed.map(u => u.line), [12, 13]);
  assert.equal(rows[0].sample, 2); // hit-rate denominator: resolved only, unparsed excluded
  assert.equal(rows[1].sample, 2); // still-open-share denominator: classified only
});

test("word-boundary match: 'unverified' is not 'verified'", () => {
  const file = adrFile("0001", { outcomes: [] });
  file.text += "\n- [outcome] the claim stayed unverified.";
  const { unparsed } = analyze(parseAdrs([file]), bareConfig(), TODAY);
  assert.equal(unparsed.length, 1);
});

test("deferred instruments are always listed, regardless of trigger state", () => {
  const cfg = bareConfig({ deferred: SCORECARD_CONFIG.deferred });
  const { deferred, verdictLine } = analyze(parseAdrs([adrFile("0001", { outcomes: ["verified", "verified"] })]), cfg, TODAY);
  assert.equal(deferred.length, 3);
  assert.match(verdictLine, /3 miss-class\(es\) uninstrumented/);
});

test("coverage: aged Act-less full ADR is uncovered; young, lite, undated, non-accepted are not in the denominator", () => {
  const adrs = parseAdrs([
    adrFile("0001", { date: "2026-06-01", act: false }),            // aged, no Act -> uncovered
    adrFile("0002", { date: "2026-07-10", act: false }),            // younger than 14d -> excluded
    adrFile("0003", { lite: true, date: "2026-06-01", act: false }), // lite -> excluded
    adrFile("0004", { date: null, act: false }),                     // undated -> excluded, reported
    adrFile("0005", { status: "proposed", date: "2026-06-01", act: false }), // not accepted -> excluded
    adrFile("0006", { date: "2026-06-01", act: true, outcomes: ["verified", "verified"] }), // aged, covered
  ]);
  const cfg = bareConfig();
  const { rows } = analyze(adrs, cfg, TODAY);
  const cov = rows[2];
  assert.equal(cov.sample, 2);      // 0001 + 0006
  assert.equal(cov.value, 0.5);     // 0001 uncovered
  assert.match(cov.detail, /1 undated excluded/);
  const lite = rows[3];
  assert.equal(lite.value, 1 / 6);  // readout row
  assert.equal(lite.status, "readout");
});

// --- Gate-hit telemetry (ADR 0080) ---

test("parseGateHits: counts well-formed lines, flags malformed fail-loud, skips blanks", () => {
  const text = [
    "2026-07-19T01:00:00Z gate-hit adr-lint docs/decisions/0080-x.md",
    "",
    "2026-07-19T01:01:00Z gate-hit budget-edit-guard /some/CLAUDE.md",
    "2026-07-19T01:02:00Z gate-hit adr-lint",                       // context optional
    "not a gate hit line at all",                                   // malformed -> flagged
    "2026-07-19 gate-hit adr-lint x",                               // bad timestamp -> flagged
  ].join("\n");
  const g = parseGateHits(text);
  assert.equal(g.present, true);
  assert.equal(g.hits.length, 3);
  assert.deepEqual(g.hits.map(h => h.gate), ["adr-lint", "budget-edit-guard", "adr-lint"]);
  assert.deepEqual(g.malformed, [5, 6]);
});

test("gate-hits breakdown row: per-gate counts sorted desc; malformed lines fold into PARTIAL", () => {
  const text = [
    "2026-07-19T01:00:00Z gate-hit adr-lint a.md",
    "2026-07-19T01:01:00Z gate-hit adr-lint b.md",
    "2026-07-19T01:02:00Z gate-hit gate-pipe-guard validate.py",
    "garbage line",
  ].join("\n");
  const adrs = parseAdrs([adrFile("0001", { outcomes: ["verified", "verified"] })]);
  const { rows, verdictLine } = analyze(adrs, bareConfig(), TODAY, parseGateHits(text));
  const gh = rows[4];
  assert.equal(gh.status, "readout");
  assert.equal(gh.sample, 3);
  assert.equal(gh.detail, "adr-lint 2, gate-pipe-guard 1");
  assert.match(verdictLine, /1 unparseable gate-hit line\(s\)/); // fail-loud, never dropped
});

test("gate-hits breakdown row: a gate no wired guard emits is marked RETIRED, its history kept whole", () => {
  const text = [
    "2026-07-19T01:00:00Z gate-hit budget-edit-guard a.md",
    "2026-07-19T01:01:00Z gate-hit gate-pipe-guard validate.py",
    "2026-07-19T01:02:00Z gate-hit gate-pipe-guard adr-lint.mjs",
  ].join("\n");
  const adrs = parseAdrs([adrFile("0001", { outcomes: ["verified", "verified"] })]);
  // Only budget-edit-guard is still on disk to emit its own name.
  const live = { hooks: [], series: [], guardText: 'hook_gate_hit budget-edit-guard "$fp"\n' };
  const { rows } = analyze(adrs, bareConfig(), TODAY, parseGateHits(text), live);
  const gh = rows[4];
  assert.equal(gh.sample, 3);  // the append-only record is never trimmed
  assert.equal(gh.detail, "gate-pipe-guard 2 (RETIRED — no wired guard emits this name), budget-edit-guard 1");
});

test("gate-hits breakdown row: with no liveness read, no gate is claimed retired", () => {
  const text = "2026-07-19T01:00:00Z gate-hit gate-pipe-guard validate.py";
  const adrs = parseAdrs([adrFile("0001", { outcomes: ["verified", "verified"] })]);
  const { rows } = analyze(adrs, bareConfig(), TODAY, parseGateHits(text));
  assert.equal(rows[4].detail, "gate-pipe-guard 1");
});

test("absent gate-hits log: stated as a true zero, does not break the all-clear (readout, not uninstrumented)", () => {
  const adrs = parseAdrs([adrFile("0001", { outcomes: ["verified", "verified", "verified"] })]);
  const { rows, verdictLine } = analyze(adrs, bareConfig(), TODAY); // no 4th arg = absent log
  const gh = rows[4];
  assert.match(gh.detail, /no gate-hits log — zero hits since instrumentation/);
  assert.equal(verdictLine, "No threshold fired — all metrics evaluated and clear");
});

// Real-corpus regression (adr-lint.test.mjs corpus() convention): pins today's mined values so a
// parser regression that blanks rows or reclassifies outcomes fails loudly. Recompute on corpus change.
// Deliberately pinned to the live corpus: it catches an unintended outcome-label change. Update
// the numbers ONLY alongside a deliberate corpus edit, and say which in the commit — the
// 2026-07-26: the ADR 0092 compaction cut most `## Act` blocks along with the process machinery
// they belonged to, so the sample dropped 19 -> 7. The metric is now n=7 (see ADR 0092).
test("real corpus: 6 verified / 1 violated / 2 still-open / 0 unparsed; hit-rate 1/7 evaluated", () => {
  const dir = "docs/decisions";
  const files = readdirSync(dir).filter(f => /^\d{4}-.*\.md$/.test(f))
    .map(name => ({ name, text: readFileSync(join(dir, name), "utf8").replace(/\r\n/g, "\n") }));
  const { rows, unparsed } = analyze(parseAdrs(files), SCORECARD_CONFIG, TODAY);
  assert.equal(unparsed.length, 0);
  assert.equal(rows[0].sample, 7);
  assert.ok(Math.abs(rows[0].value - 1 / 7) < 1e-9);
  assert.equal(rows[0].status, "healthy"); // 14.3%
  assert.equal(rows[1].sample, 9);         // 6 + 1 + 2 classified
});

// ---- ADR 0086 guard-liveness readout -------------------------------------------------------

const LIVE_HOOKS = [
  { path: "h/exempt.sh", classification: "per-event-exempt" },
  { path: "h/coupled.sh", classification: "boundary-coupled" },
];
const series = (over = {}) => ({
  series: "session-end", guard: "h/coupled.sh", wired: true, evaluated: true,
  expected: 3, observed: 0, detail: "d", ...over,
});
const cleanAdrs = () => parseAdrs([adrFile("0001", { outcomes: ["verified", "verified", "verified"] })]);

test("liveness: wired + expected>0 + observed=0 is NOT FIRING — row, trigger, and verdict part", () => {
  const { rows, triggers, verdictLine } = analyze(cleanAdrs(), bareConfig(), TODAY, parseGateHits(null),
    { hooks: LIVE_HOOKS, series: [series()] });
  const row = rows.find(r => r.metric === "liveness: session-end");
  assert.equal(row.status, "NOT FIRING");
  assert.equal(row.display, "0 observed / 3 expected");
  assert.ok(triggers.some(t => t.startsWith("NOT-FIRING liveness session-end")));
  assert.match(verdictLine, /1 wired guard\(s\) NOT FIRING/);
});

test("liveness: nonzero observed is a readout, never a flag; so is unwired", () => {
  const { rows: r1, triggers: t1 } = analyze(cleanAdrs(), bareConfig(), TODAY, parseGateHits(null),
    { hooks: LIVE_HOOKS, series: [series({ observed: 1 })] });
  assert.equal(r1.find(r => r.metric === "liveness: session-end").status, "readout");
  assert.ok(!t1.some(t => t.startsWith("NOT-FIRING")));
  const { rows: r2 } = analyze(cleanAdrs(), bareConfig(), TODAY, parseGateHits(null),
    { hooks: LIVE_HOOKS, series: [series({ wired: false })] });
  assert.equal(r2.find(r => r.metric === "liveness: session-end").status, "readout");
});

test("liveness: zero expected boundaries is a readout — absence of the boundary is not guard death", () => {
  const { triggers } = analyze(cleanAdrs(), bareConfig(), TODAY, parseGateHits(null),
    { hooks: LIVE_HOOKS, series: [series({ expected: 0 })] });
  assert.ok(!triggers.some(t => t.startsWith("NOT-FIRING")));
});

test("liveness: an unevaluated series reads not-evaluated and forces PARTIAL — unknown is never healthy", () => {
  const { rows, verdictLine } = analyze(cleanAdrs(), bareConfig(), TODAY, parseGateHits(null),
    { hooks: LIVE_HOOKS, series: [series({ evaluated: false, reason: "gh unavailable" })] });
  assert.match(rows.find(r => r.metric === "liveness: session-end").status, /not evaluated \(gh unavailable\)/);
  assert.match(verdictLine, /PARTIAL/);
});

test("liveness: per-event-exempt guards are listed as exempt, never silence-inferred dead", () => {
  const { rows, triggers, verdictLine } = analyze(cleanAdrs(), bareConfig(), TODAY, parseGateHits(null),
    { hooks: LIVE_HOOKS, series: [series({ observed: 2 })] });
  const exempt = rows.find(r => r.metric.startsWith("liveness-exempt"));
  assert.equal(exempt.status, "readout");
  assert.match(exempt.detail, /h\/exempt\.sh/);
  assert.ok(!triggers.some(t => t.includes("exempt")));
  // Fully declared + evaluated + clear: the all-clear line survives liveness being present.
  assert.equal(verdictLine, "No threshold fired — all metrics evaluated and clear");
});

test("liveness: an undeclared wired guard is stated as rung NONE and forces PARTIAL, never presented as watched", () => {
  const hooks = [...LIVE_HOOKS, { path: "h/mystery.sh", classification: null }];
  const { rows, verdictLine } = analyze(cleanAdrs(), bareConfig(), TODAY, parseGateHits(null),
    { hooks, series: [series({ observed: 2 })] });
  const row = rows.find(r => r.metric.startsWith("liveness UNDECLARED"));
  assert.match(row.detail, /h\/mystery\.sh — NOT watched/);
  assert.match(verdictLine, /1 wired guard\(s\) undeclared for liveness/);
});

test("liveness: a boundary-coupled guard with NO configured series is surfaced, not silently dropped", () => {
  // Before this check the hook produced zero rows of any kind — its declaration read as watched
  // while nothing watched it (the ADR 0086 (e) failure mode, one level up).
  const hooks = [...LIVE_HOOKS, { path: "h/forgotten.sh", classification: "boundary-coupled" }];
  const { rows, verdictLine } = analyze(cleanAdrs(), bareConfig(), TODAY, parseGateHits(null),
    { hooks, series: [series({ observed: 2 })] });
  const row = rows.find(r => r.metric.startsWith("liveness UNDECLARED"));
  assert.match(row.detail, /h\/forgotten\.sh \(declared boundary-coupled, no configured series\)/);
  assert.match(verdictLine, /1 wired guard\(s\) undeclared for liveness/);
});

test("liveness: a boundary-coupled guard WITH its series stays out of the unwatched list", () => {
  const { rows } = analyze(cleanAdrs(), bareConfig(), TODAY, parseGateHits(null),
    { hooks: LIVE_HOOKS, series: [series({ observed: 2 })] });
  assert.equal(rows.find(r => r.metric.startsWith("liveness UNDECLARED")), undefined);
});

test("countSessionLogLines: pattern + since filter on ISO-stamped lines; null text is zero", () => {
  const log = [
    "2026-07-18T10:00:00Z session-end clear",
    "2026-07-21T10:00:00Z session-end logout",
    "2026-07-22T10:00:00Z skill-spawn retrospect",
    "2026-07-23T10:00:00Z agent-spawn pdca-workflow:retrospect",
    "garbage line",
  ].join("\n");
  assert.equal(countSessionLogLines(log, /^session-end /, "2026-07-20"), 1);
  assert.equal(countSessionLogLines(log, /^session-end /, ""), 2);
  assert.equal(countSessionLogLines(log, /^(skill-spawn|agent-spawn) \S*retrospect$/, "2026-07-20"), 2);
  assert.equal(countSessionLogLines(null, /x/, ""), 0);
});

test("gate-hits RETIRED matches whole names, not substrings — a short name is not live by accident", () => {
  // `includes` answers "does this character sequence appear anywhere", which is a different
  // question: `hit` and `gate` are substrings of `hook_gate_hit budget-edit-guard`, so under
  // substring matching a deleted short-named gate reads as live forever — the readout's own
  // failure mode one level down.
  const guardText = 'hook_gate_hit budget-edit-guard "$fp"';
  const emitted = new Set(guardText.match(/[A-Za-z0-9_.-]+/g) ?? []);
  const retired = (g) => !emitted.has(g);
  assert.equal(retired("hit"), true);
  assert.equal(retired("gate"), true);
  assert.equal(retired("budget-edit-guard"), false);
  assert.equal(retired("gate-pipe-guard"), true);
});
