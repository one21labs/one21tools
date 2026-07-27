/*
 * Decision-logic tests for sweep-state.mjs (CI: `node --test pdca-workflow/scripts/*.test.mjs`).
 * The load-bearing property is that CLEAN is hard to reach and EXHAUSTED cannot be mistaken for
 * it — so most of these cases are attempts to get a CLEAN verdict that has not been earned.
 */
import { test } from "node:test";
import assert from "node:assert/strict";
import { sweepState, EXIT, DEFAULT_MAX_ROUNDS, crossFamilyLane, isForeignFamily, laneModelId } from "./sweep-state.mjs";
import { familyOf } from "./crosscheck.mjs";

// Rounds default to carrying a foreign-lane model id, so the CONVERGENCE cases below vary only
// what they mean to vary. `bare()` is the round with no cross-family lane, used by the cases that
// test the frame check itself.
const r = (...ids) => ({ ids, xfam: "grok-4.5-build" });
const bare = (...ids) => ({ ids });

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
  assert.notEqual(EXIT["FRAME-UNCHECKED"], 0);
  // Every state distinct, so a caller switching on the code cannot conflate two outcomes. The
  // count is asserted so ADDING a state without deciding its exit code fails here first.
  assert.equal(new Set(Object.values(EXIT)).size, 5);
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

test("convergence alone is NOT clean: a sweep that never left the maker's family is FRAME-UNCHECKED", () => {
  // The scar this pins: a three-round sweep of this repo ran every lane same-family while the
  // prose rule to use a foreign one existed in two places. A rule the agent classifies its own way
  // is a rule the agent can exempt itself from, so the verdict has to hold it instead.
  const converged = [bare("a"), bare(), bare()];
  assert.equal(sweepState(converged, 5).state, "FRAME-UNCHECKED");
  assert.notEqual(EXIT["FRAME-UNCHECKED"], 0);
});

test("a foreign lane INSIDE the quiet tail earns CLEAN", () => {
  const rounds = [bare("a"), { ids: [], xfam: "grok-4.5" }, bare()];
  const v = sweepState(rounds, 5);
  assert.equal(v.state, "CLEAN");
  assert.equal(v.crossFamily.family, "xai");
  assert.match(v.reason, /cross-checked by grok-4\.5/);
});

test("a foreign lane BEFORE the quiet tail does not launder the tail", () => {
  // The scar, one day after the weak version shipped: this repo's round 4 ran a grok lane and
  // found 8 things; the check then read as satisfied FOREVER, so round 5 was planned same-family
  // with the mechanism's approval. A lane that found things witnesses that round, not the later
  // quiet. Mutation check: revert the tail slice in sweepState and this goes green.
  const rounds = [bare("a"), { ids: ["b"], xfam: "grok-4.5" }, bare(), bare()];
  const v = sweepState(rounds, 6);
  assert.equal(v.state, "FRAME-UNCHECKED");
  // The message must say WHICH failure this is, or the operator re-reads it as "you never ran one".
  assert.match(v.reason, /before the quiet tail/);
  // ...and must NOT claim anything crossFamilyLane does not check: an all-quiet log with a
  // round-1 lane hits this same branch, so a "that round found things" clause would be false.
  assert.doesNotMatch(v.reason, /DID find things/);
  assert.match(v.reason, /grok-4\.5/);
  assert.match(v.reason, /Run another round/);
});

test("the tail rule scales with --quiet-rounds rather than assuming 2", () => {
  // A 3-round tail must be witnessed inside those 3, not by a lane 4 rounds back.
  const late = [bare("a"), bare(), bare(), { ids: [], xfam: "grok-4.5" }];
  assert.equal(sweepState(late, 6, 3).state, "CLEAN");
  const early = [{ ids: ["a"], xfam: "grok-4.5" }, bare(), bare(), bare()];
  assert.equal(sweepState(early, 6, 3).state, "FRAME-UNCHECKED");
  // THE DISCRIMINATING CASE, and the reason the two above are not enough on their own: put the
  // lane where last-3 and last-2 DISAGREE. Above, `late` is inside both windows and `early` is
  // outside both, so hardcoding the lane slice to 2 passed all of them — a cross-family review
  // caught that, and mutating only the lane slice confirmed it: 23/23 green with the parameter
  // ignored. Here the lane sits at n-3, so a hardcoded 2 reports FRAME-UNCHECKED and only the
  // parameterised slice reports CLEAN.
  const straddle = [bare("a"), { ids: [], xfam: "grok-4.5" }, bare(), bare()];
  assert.equal(sweepState(straddle, 6, 3).state, "CLEAN", "lane at n-3 is inside a 3-round tail");
  assert.equal(sweepState(straddle, 6, 2).state, "FRAME-UNCHECKED", "...and outside a 2-round one");
});

test("a same-family or unplaceable model id does NOT satisfy the check", () => {
  // copilot's auto mode routes to claude-haiku-4.5 on this machine, so a lane that ran but landed
  // in-family is the exact case that must not pass - and an id we cannot place fails closed too.
  assert.equal(sweepState([bare("a"), { ids: [], xfam: "claude-haiku-4.5" }, bare()], 5).state, "FRAME-UNCHECKED");
  assert.equal(sweepState([bare("a"), { ids: [], xfam: "some-local-model" }, bare()], 5).state, "FRAME-UNCHECKED");
  assert.equal(sweepState([bare("a"), { ids: [], xfam: "" }, bare()], 5).state, "FRAME-UNCHECKED");
});

test("a lane is placed by its MODEL id, not its lane name", () => {
  // The scar: main() asked familyOf(lane.name). `copilot` is not a model id, so it came back
  // "unknown", and the test was `!== MAKER_FAMILY` — so an unplaceable lane counted as FOREIGN,
  // inverting the rule crossFamilyLane enforces. copilot's auto mode routes in-family here, so
  // this is the case that must not pass.
  assert.equal(isForeignFamily(familyOf(laneModelId({ name: "grok" }))), true);
  assert.equal(isForeignFamily(familyOf(laneModelId({ name: "copilot" }))), false);
  // The custom lane names its model in the environment — excluding it BY NAME locked the
  // documented vendor-agnostic escape out of ever corroborating a clean sweep.
  const custom = { name: "custom", custom: true };
  assert.equal(isForeignFamily(familyOf(laneModelId(custom, { PDCA_CROSSCHECK_MODEL: "gpt-5" }))), true);
  assert.equal(isForeignFamily(familyOf(laneModelId(custom, { PDCA_CROSSCHECK_MODEL: "claude-opus-5" }))), false);
  assert.equal(isForeignFamily(familyOf(laneModelId(custom, {}))), false);   // unset id cannot vouch
});

test("crossFamilyLane reads the family table rather than keeping a second copy", () => {
  assert.equal(crossFamilyLane([{ ids: [], xfam: "gpt-5" }]).family, "openai");
  assert.equal(crossFamilyLane([{ ids: [], xfam: "gemini-3-pro" }]).family, "google");
  assert.equal(crossFamilyLane([{ ids: [] }]), null);
});

test("the frame check does not mask EXHAUSTED or RUNNING - a budget outcome is still a budget outcome", () => {
  // FRAME-UNCHECKED only ever replaces CLEAN. A sweep still owing rounds must say so, or the new
  // state would let an unfinished sweep hide behind an independence complaint.
  assert.equal(sweepState([bare("a")], 5).state, "RUNNING");
  assert.equal(sweepState([bare("a"), bare("b")], 2).state, "EXHAUSTED");
});
