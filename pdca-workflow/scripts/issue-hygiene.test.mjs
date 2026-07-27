/*
 * Decision-logic tests for issue-hygiene.mjs (CI: `node --test pdca-workflow/scripts/*.test.mjs`).
 * The properties worth pinning are the ones that decide whether a human is shown a proposal at
 * all: a threshold that silently never fires makes the script look clean while the backlog rots,
 * which is the same silent-coverage class ADR 0086 names for guards.
 */
import { test } from "node:test";
import assert from "node:assert/strict";
import { spawnSync } from "node:child_process";
import { fileURLToPath } from "node:url";
import { detect, checklistProgress, numericFlag, DEFAULTS } from "./issue-hygiene.mjs";

const SCRIPT = fileURLToPath(new URL("./issue-hygiene.mjs", import.meta.url));

const NOW = "2026-07-26T00:00:00Z";
const daysAgo = (n) => new Date(Date.parse(NOW) - n * 86400000).toISOString();
const kinds = (r, k) => r.findings.filter((f) => f.kind === k);

test("an issue untouched past the dormancy threshold is flagged, with the day count", () => {
  const r = detect([{ number: 1, title: "old thing", updatedAt: daysAgo(30) }], { now: NOW });
  assert.equal(kinds(r, "dormant").length, 1);
  assert.equal(kinds(r, "dormant")[0].days, 30);
});

test("an issue inside the threshold is not flagged", () => {
  const r = detect([{ number: 1, title: "fresh thing", updatedAt: daysAgo(3) }], { now: NOW });
  assert.equal(kinds(r, "dormant").length, 0);
});

test("the dormancy boundary is inclusive, so an issue exactly at the threshold still surfaces", () => {
  const r = detect([{ number: 1, title: "x", updatedAt: daysAgo(DEFAULTS.dormantDays) }], { now: NOW });
  assert.equal(kinds(r, "dormant").length, 1);
});

test("a missing updatedAt is skipped rather than treated as infinitely old", () => {
  const r = detect([{ number: 1, title: "no timestamp" }], { now: NOW });
  assert.equal(kinds(r, "dormant").length, 0);
});

test("a multi-item checklist is reported as a tracking issue whatever its tick state", () => {
  const body = "- [x] one\n- [x] two\n- [x] three\n- [ ] four\n- [ ] five\n";
  const r = detect([{ number: 9, title: "tracker", body, updatedAt: daysAgo(1) }], { now: NOW });
  assert.equal(kinds(r, "tracking").length, 1);
  assert.match(kinds(r, "tracking")[0].note, /3\/5/);
});

test("a tracking issue with ZERO ticks still reports — the motivating case had 13 boxes, none ticked", () => {
  // The failure being caught is a direction shipping without its box being ticked, so the tick
  // state is exactly what cannot be trusted as the trigger. A threshold here would stay silent.
  const body = Array.from({ length: 13 }, (_, i) => `- [ ] direction ${i + 1}`).join("\n");
  const r = detect([{ number: 236, title: "research agenda", body, updatedAt: daysAgo(1) }], { now: NOW });
  assert.equal(kinds(r, "tracking").length, 1);
  assert.equal(kinds(r, "tracking")[0].done, 0);
  assert.equal(kinds(r, "tracking")[0].total, 13);
});

test("a short checklist is a note, not a tracking issue", () => {
  const body = "- [x] a\n- [ ] b\n- [ ] c\n";
  const r = detect([{ number: 9, title: "small", body, updatedAt: daysAgo(1) }], { now: NOW });
  assert.equal(kinds(r, "tracking").length, 0);
});

test("bodies with no checklist read as null, never as an empty tracking issue", () => {
  assert.equal(checklistProgress("- [x] a\n- [x] b\n"), null);
  assert.equal(checklistProgress("no boxes here"), null);
  assert.equal(checklistProgress(undefined), null);
});

test("checklist detection tolerates indentation and asterisk bullets", () => {
  const p = checklistProgress("  * [x] a\n\t- [X] b\n* [ ] c\n- [ ] d\n- [ ] e\n");
  assert.deepEqual({ done: p.done, total: p.total }, { done: 2, total: 5 });
});

test("no overlap/duplicate signal ships — it was measured at ~4% precision and dropped", () => {
  // Two issues that share most of their title words must still produce no pairing finding: the
  // detector was removed on evidence, and a silent re-introduction would revive the noise.
  const r = detect([
    { number: 1, title: "always-loaded skill description budget owner", updatedAt: daysAgo(1) },
    { number: 2, title: "skill description budget for always-loaded context", updatedAt: daysAgo(1) },
  ], { now: NOW });
  assert.deepEqual(r.findings, []);
});

test("thresholds are configurable — a stricter one silences, a looser one surfaces", () => {
  const issues = [{ number: 1, title: "x", updatedAt: daysAgo(10) }];
  assert.equal(kinds(detect(issues, { now: NOW, dormantDays: 30 }), "dormant").length, 0);
  assert.equal(kinds(detect(issues, { now: NOW, dormantDays: 5 }), "dormant").length, 1);
});

test("one issue can carry two different signals without either suppressing the other", () => {
  const body = "- [x] a\n- [x] b\n- [ ] c\n- [ ] d\n- [ ] e\n";
  const r = detect([{ number: 1, title: "t", body, updatedAt: daysAgo(40) }], { now: NOW });
  assert.equal(kinds(r, "dormant").length, 1);
  assert.equal(kinds(r, "tracking").length, 1);
});

test("an empty backlog is a clean result, not an error", () => {
  const r = detect([], { now: NOW });
  assert.deepEqual(r, { open: 0, findings: [] });
});

test("a non-array dump is rejected loudly rather than read as zero issues", () => {
  assert.throws(() => detect(null, { now: NOW }), TypeError);
  assert.throws(() => detect({ issues: [] }, { now: NOW }), TypeError);
});

test("a threshold flag given no value is rejected, never coerced to NaN", () => {
  // NaN inverts both signals at once — nothing is ever dormant, and any single checkbox reads as
  // a tracking issue — so a disarmed run prints exactly what a clean backlog prints.
  assert.throws(() => numericFlag(["--dormant-days"], "dormant-days", DEFAULTS.dormantDays),
    /--dormant-days takes a positive number; got no value/);
  assert.throws(() => numericFlag(["--tracking-min"], "tracking-min", DEFAULTS.trackingMin),
    /--tracking-min takes a positive number; got no value/);
});

test("a non-numeric or non-positive threshold is rejected, and the message prescribes the fix", () => {
  // Asserts the two things the message must carry - the bad value and a usable remedy - not its
  // punctuation, so extending the remedy (as the = spelling did) is not a test failure.
  assert.throws(() => numericFlag(["--dormant-days", "soon"], "dormant-days", 21),
    /got "soon".*--dormant-days 21/s);
  assert.throws(() => numericFlag(["--tracking-min", "0"], "tracking-min", 5), /got "0"/);
  assert.throws(() => numericFlag(["--dormant-days", "-3"], "dormant-days", 21), /got "-3"/);
});

test("an absent flag takes the default and a good value is read as given", () => {
  assert.equal(numericFlag([], "dormant-days", DEFAULTS.dormantDays), DEFAULTS.dormantDays);
  assert.equal(numericFlag(["--tracking-min", "3"], "tracking-min", DEFAULTS.trackingMin), 3);
});

test("a malformed flag exits non-zero and prints no report — the retrospect agent cites this output", () => {
  const p = spawnSync(process.execPath, [SCRIPT, "--dormant-days"], { input: "[]", encoding: "utf8" });
  assert.equal(p.status, 1);
  assert.equal(p.stdout, "");
  assert.match(p.stderr, /--dormant-days takes a positive number/);
});

test("the --flag=value spelling reaches the same validation, never a silent default", () => {
  // An exact-token lookup misses `--x=5` entirely and falls through to the default, so the report
  // prints against thresholds the caller did not ask for - the same fail-open the NaN check closes,
  // and one the retrospect agent would cite as if it answered the question asked (ADR 0094).
  assert.equal(numericFlag(["--dormant-days=5"], "dormant-days", 21), 5);
  assert.equal(numericFlag(["--tracking-min=9"], "tracking-min", 5), 9);
  assert.throws(() => numericFlag(["--dormant-days=abc"], "dormant-days", 21), RangeError);
  assert.throws(() => numericFlag(["--dormant-days="], "dormant-days", 21), RangeError);
  assert.throws(() => numericFlag(["--dormant-days=0"], "dormant-days", 21), RangeError);
  assert.throws(() => numericFlag(["--dormant-days=-3"], "dormant-days", 21), RangeError);
});

test("the rejection message teaches BOTH spellings, so a caller who used = is not left guessing", () => {
  try {
    numericFlag(["--dormant-days=x"], "dormant-days", 21);
    assert.fail("expected a RangeError");
  } catch (e) {
    assert.match(e.message, /--dormant-days 21/);
    assert.match(e.message, /--dormant-days=21/);
  }
});
