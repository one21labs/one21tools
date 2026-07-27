/*
 * Decision-logic tests for sweep-state.mjs (CI: `node --test pdca-workflow/scripts/*.test.mjs`).
 * The load-bearing property is that CLEAN is hard to reach and EXHAUSTED cannot be mistaken for
 * it — so most of these cases are attempts to get a CLEAN verdict that has not been earned.
 */
import { test } from "node:test";
import assert from "node:assert/strict";
import { sweepState, EXIT, DEFAULT_MAX_ROUNDS } from "./sweep-state.mjs";

const r = (...ids) => ({ ids });

test("two consecutive empty rounds after findings is CLEAN", () => {
  const v = sweepState([r("a", "b"), r("c"), r(), r()], 10);
  assert.equal(v.state, "CLEAN");
  assert.equal(v.totalFindings, 3);
});

test("hitting the cap with findings still arriving is EXHAUSTED, never CLEAN", () => {
  const v = sweepState([r("a"), r("b"), r("c")], 3);
  assert.equal(v.state, "EXHAUSTED");
  assert.match(v.reason, /still arriving \(round 3 found 1 new\)/);
  assert.match(v.reason, /UNKNOWN, not zero/);
});

test("EXHAUSTED on a quiet last round says so — the skill relays this reason verbatim", () => {
  const v = sweepState([r("a"), r()], 2);
  assert.equal(v.state, "EXHAUSTED");
  assert.doesNotMatch(v.reason, /still arriving/);
  assert.match(v.reason, /short of the quiet tail of 2 \(round 2 found 0 new\)/);
  assert.match(v.reason, /UNKNOWN, not zero/);
});

test("the quiet rounds must be the TAIL — an empty round mid-run does not count", () => {
  // Round 2 found nothing; round 3's fix-induced defect proves why a mid-run gap is not clean.
  const v = sweepState([r("a"), r(), r("b")], 10);
  assert.equal(v.state, "RUNNING");
});

test("one quiet round is not enough at the default K=2", () => {
  const v = sweepState([r("a"), r()], 10);
  assert.equal(v.state, "RUNNING");
});

test("a repeat of an already-seen finding is not new — it cannot reset the quiet counter", () => {
  // 'a' was judged not-real in round 1 and keeps being re-reported. Deduping against the FIXED
  // set instead of the SEEN set would make this run forever.
  const v = sweepState([r("a"), r("a"), r("a")], 10);
  assert.equal(v.state, "CLEAN");
  assert.equal(v.totalFindings, 1);
  assert.deepEqual(v.perRound.map((x) => x.fresh), [1, 0, 0]);
});

test("a genuinely new finding in the last round blocks CLEAN even after a quiet stretch", () => {
  const v = sweepState([r("a"), r(), r(), r("b")], 10);
  assert.equal(v.state, "RUNNING");
});

test("cap reached exactly as the tail goes quiet is CLEAN, not EXHAUSTED", () => {
  // Quiet wins over the cap: the cap only decides an UNFINISHED sweep.
  const v = sweepState([r("a"), r(), r()], 3);
  assert.equal(v.state, "CLEAN");
});

test("zero rounds is RUNNING, not CLEAN — a sweep that never ran found nothing by not looking", () => {
  const v = sweepState([], 5);
  assert.equal(v.state, "RUNNING");
  assert.equal(v.totalFindings, 0);
});

test("a cap of 1 with a single quiet round cannot be CLEAN at K=2 — it is EXHAUSTED", () => {
  const v = sweepState([r()], 1);
  assert.equal(v.state, "EXHAUSTED");
});

test("K is configurable and a stricter K demands a longer quiet tail", () => {
  assert.equal(sweepState([r("a"), r(), r()], 10, 3).state, "RUNNING");
  assert.equal(sweepState([r("a"), r(), r(), r()], 10, 3).state, "CLEAN");
});

test("malformed input is its own state, never a silent CLEAN", () => {
  assert.equal(sweepState([{ nope: 1 }], 5).state, "MALFORMED");
  assert.equal(sweepState("not an array", 5).state, "MALFORMED");
  assert.equal(sweepState([r()], 0).state, "MALFORMED");
  assert.equal(sweepState([r()], 5, 0).state, "MALFORMED");
});

test("exit codes: only CLEAN is 0, so a caller cannot treat exhaustion as success", () => {
  assert.equal(EXIT.CLEAN, 0);
  assert.notEqual(EXIT.EXHAUSTED, 0);
  assert.notEqual(EXIT.RUNNING, 0);
  assert.notEqual(EXIT.MALFORMED, 0);
  assert.equal(new Set(Object.values(EXIT)).size, 4);
});

test("omitting --max uses the script's own default, never NaN", () => {
  // The skill used to promise "no cap given = 5" while main() passed NaN, so the run exited
  // MALFORMED instead of honouring the documented default. The constant is the one home now;
  // this pins that it is a usable cap, not just a number that exists.
  assert.equal(Number.isInteger(DEFAULT_MAX_ROUNDS), true);
  assert.notEqual(sweepState([r("a")], DEFAULT_MAX_ROUNDS).state, "MALFORMED");
  assert.equal(sweepState([r("a")], NaN).state, "MALFORMED");
});

test("the default cap can actually reach CLEAN - a cap below the quiet tail never could", () => {
  // A cap of 2 with a quiet tail of 2 can only ever report EXHAUSTED or CLEAN by luck; the
  // default must leave room for at least one finding round before the tail.
  assert.ok(DEFAULT_MAX_ROUNDS > 2, "default cap must exceed the default quiet tail of 2");
  const rounds = [r("a"), r(), r()];
  assert.equal(sweepState(rounds, DEFAULT_MAX_ROUNDS).state, "CLEAN");
});
