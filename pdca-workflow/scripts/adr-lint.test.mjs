/*
 * adr-lint.test.mjs — proves adr-lint's decision logic (the poka-yoke for the
 * poka-yoke). Zero-dependency: node's built-in test runner + assert, so it runs
 * with `node --test scripts/` on any stack. Each case plants exactly one ledger
 * defect and asserts the matching check fires (and that a clean ledger is silent).
 *
 * Run: node --test "scripts/*.test.mjs"
 */
import { test } from "node:test";
import assert from "node:assert/strict";
import { lint } from "./adr-lint.mjs";

// A clean two-ADR ledger, indexed, within budget. Helpers below mutate copies.
const clean = () => ({
  files: ["0001-a.md", "0002-b.md"],
  indexLinks: [["0001", "0001-a.md"], ["0002", "0002-b.md"]],
  lineCounts: { "0001-a.md": 40, "0002-b.md": 55 },
  budget: 70,
});

test("clean ledger reports no problems", () => {
  assert.deepEqual(lint(clean()).problems, []);
});

test("fires on a duplicate ADR ID on disk", () => {
  const l = clean();
  l.files = ["0001-a.md", "0001-b.md"];
  l.indexLinks = [["0001", "0001-a.md"], ["0001", "0001-b.md"]];
  l.lineCounts = { "0001-a.md": 40, "0001-b.md": 40 };
  const { problems } = lint(l);
  assert.equal(problems.length, 1);
  assert.match(problems[0], /Duplicate ADR IDs/);
});

test("fires when an ADR file is not linked in INDEX.md", () => {
  const l = clean();
  l.indexLinks = [["0001", "0001-a.md"]]; // 0002 unindexed
  const { problems } = lint(l);
  assert.equal(problems.length, 1);
  assert.match(problems[0], /not linked in INDEX\.md/);
  assert.match(problems[0], /0002-b\.md/);
});

test("fires when an INDEX link points to a missing file", () => {
  const l = clean();
  l.indexLinks.push(["0003", "0003-ghost.md"]); // no such file on disk
  const { problems } = lint(l);
  assert.equal(problems.length, 1);
  assert.match(problems[0], /broken or label != file/);
});

test("fires when an INDEX link label does not match its filename", () => {
  const l = clean();
  l.indexLinks = [["0001", "0001-a.md"], ["0009", "0002-b.md"]]; // label 0009 != file 0002
  const { problems } = lint(l);
  assert.equal(problems.length, 1);
  assert.match(problems[0], /broken or label != file/);
});

test("fires when an ADR exceeds the line budget", () => {
  const l = clean();
  l.lineCounts["0002-b.md"] = 71; // > 70
  const { problems } = lint(l);
  assert.equal(problems.length, 1);
  assert.match(problems[0], /over the 70-line budget/);
  assert.match(problems[0], /0002-b\.md:71/);
});

test("budget is configurable (50 trips the otherwise-fine 55-line ADR)", () => {
  const l = clean();
  l.budget = 50;
  const { problems } = lint(l);
  assert.equal(problems.length, 1);
  assert.match(problems[0], /over the 50-line budget/);
});

test("accumulates independent problems rather than stopping at the first", () => {
  const l = clean();
  l.files = ["0001-a.md", "0001-b.md"]; // dup id
  l.indexLinks = []; // both unindexed
  l.lineCounts = { "0001-a.md": 99, "0001-b.md": 40 }; // one over budget
  const { problems } = lint(l);
  assert.equal(problems.length, 3);
});
