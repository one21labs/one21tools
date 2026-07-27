/*
 * Decision-logic tests for cli-flags.mjs (CI: `node --test pdca-workflow/scripts/*.test.mjs`).
 *
 * These pin a CLASS, not an exemplar. Two live bugs motivated this file and they were the same
 * bug in two CLIs: a flag spelling that missed the lookup and fell through to a default, so the
 * run proceeded against limits nobody asked for. Every case below is written to fail if either
 * spelling stops reaching the same validation.
 */
import { test } from "node:test";
import assert from "node:assert/strict";
import { flagValue, numericFlag, requiredFlag } from "./cli-flags.mjs";

test("both spellings are the same flag", () => {
  assert.equal(flagValue(["--max", "3"], "max"), "3");
  assert.equal(flagValue(["--max=3"], "max"), "3");
  assert.equal(numericFlag(["--max", "3"], "max", 5), 3);
  assert.equal(numericFlag(["--max=3"], "max", 5), 3);
});

test("an absent flag takes the default; a present-but-empty one is malformed, not absent", () => {
  // The distinction is the whole point: treating "present with no value" as "absent" is the
  // fail-open that shipped - the run continues at a limit the caller never chose.
  assert.equal(numericFlag([], "max", 5), 5);
  assert.equal(numericFlag(["--other", "1"], "max", 5), 5);
  assert.throws(() => numericFlag(["--max"], "max", 5), RangeError);
  assert.throws(() => numericFlag(["--max="], "max", 5), RangeError);
});

test("LAST occurrence wins, whichever spelling it uses", () => {
  // An earlier implementation let any `=` form beat a later space form regardless of position,
  // which cannot be predicted from reading the command line.
  assert.equal(numericFlag(["--max", "3", "--max", "7"], "max", 5), 7);
  assert.equal(numericFlag(["--max=3", "--max=7"], "max", 5), 7);
  assert.equal(numericFlag(["--max=3", "--max", "7"], "max", 5), 7);
  assert.equal(numericFlag(["--max", "3", "--max=7"], "max", 5), 7);
});

test("a following flag is not swallowed as this flag's value", () => {
  // `--max --quiet-rounds 2` means --max got nothing. Swallowing the next flag would both lose
  // --quiet-rounds and hide the mistake behind a plausible-looking number.
  assert.equal(flagValue(["--max", "--quiet-rounds", "2"], "max"), "");
  assert.throws(() => numericFlag(["--max", "--quiet-rounds", "2"], "max", 5), RangeError);
  assert.equal(numericFlag(["--max", "--quiet-rounds", "2"], "quiet-rounds", 9), 2);
});

test("non-numeric and non-positive values are rejected, never coerced", () => {
  for (const bad of ["abc", "0", "-3", "NaN", "Infinity", " "]) {
    assert.throws(() => numericFlag([`--max=${bad}`], "max", 5), RangeError, `expected reject: ${bad}`);
    assert.throws(() => numericFlag(["--max", bad], "max", 5), RangeError, `expected reject: ${bad}`);
  }
});

test("the rejection message names the flag, quotes what arrived, and teaches both spellings", () => {
  try {
    numericFlag(["--dormant-days=soon"], "dormant-days", 21);
    assert.fail("expected a RangeError");
  } catch (e) {
    assert.match(e.message, /--dormant-days/);
    assert.match(e.message, /"soon"/);
    assert.match(e.message, /--dormant-days 21/);
    assert.match(e.message, /--dormant-days=21/);
  }
});

test("requiredFlag refuses to return undefined, so a caller cannot proceed on nothing", () => {
  assert.equal(requiredFlag(["--claim-file", "/tmp/x"], "claim-file"), "/tmp/x");
  assert.equal(requiredFlag(["--claim-file=/tmp/x"], "claim-file"), "/tmp/x");
  assert.throws(() => requiredFlag([], "claim-file"), RangeError);
  assert.throws(() => requiredFlag(["--claim-file"], "claim-file"), RangeError);
  assert.throws(() => requiredFlag(["--claim-file="], "claim-file"), RangeError);
});

test("a non-array or non-string argv entry cannot crash the parse", () => {
  assert.equal(flagValue(null, "max"), undefined);
  assert.equal(flagValue(undefined, "max"), undefined);
  assert.equal(numericFlag([null, 7, "--max", "3"], "max", 5), 3);
});

test("a flag whose name prefixes another is not confused with it", () => {
  // `--max` must not read `--max-rounds`'s value, in either spelling.
  assert.equal(numericFlag(["--max-rounds", "9", "--max", "3"], "max", 5), 3);
  assert.equal(numericFlag(["--max-rounds=9", "--max=3"], "max", 5), 3);
  assert.equal(numericFlag(["--max-rounds=9"], "max", 5), 5);
});
