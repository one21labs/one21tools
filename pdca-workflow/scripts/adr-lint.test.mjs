/*
 * adr-lint.test.mjs — proves adr-lint's decision logic (the poka-yoke for the poka-yoke).
 * Zero-dependency: node's built-in test runner + assert, so it runs with
 * `node --test "scripts/*.test.mjs"` on any stack. Each case plants exactly one corpus defect
 * (or a clean corpus) and asserts the matching guard fires.
 */
import { test } from "node:test";
import assert from "node:assert/strict";
import { lint } from "./adr-lint.mjs";

// Build an ADR file { name, text } with valid frontmatter by default; override to plant a defect.
// A valid-by-default ADR carries a falsifiable criterion (a `- [checkable]` bullet) so the
// criterion-minting gate passes; pass { noCriterion: true } to plant the UNFALSIFIABLE defect.
function adr(name, o = {}) {
  const id = o.id ?? name.slice(0, 4);
  const fm = o.frontmatter ?? `---
id: ${id}
title: "${o.title ?? "A decision"}"
status: ${o.status ?? "accepted"}
summary: "${o.summary ?? "A one-line summary"}"
---`;
  const body = o.body ?? `\n# ${id} — A decision\n\n- Date: 2026-06-27\n`;
  const criterion = o.noCriterion ? "" : "\n- [checkable] it works — owner, verified\n";
  return { name, text: fm + body + criterion };
}

const clean = () => [adr("0001-first.md"), adr("0002-second.md")];

test("clean corpus reports no problems", () => {
  assert.deepEqual(lint({ files: clean(), budget: 70 }).problems, []);
});

test("fires on missing frontmatter", () => {
  const files = [adr("0001-first.md", { frontmatter: "# 0001 — no frontmatter" })];
  const { problems } = lint({ files, budget: 70 });
  assert.equal(problems.length, 1);
  assert.match(problems[0], /missing YAML frontmatter/);
});

test("fires on a bad/missing frontmatter id", () => {
  const files = [adr("0001-first.md", { id: "xx" })];
  assert.match(lint({ files, budget: 70 }).problems[0], /bad\/missing frontmatter id/);
});

test("fires when the frontmatter id does not match the filename", () => {
  const files = [adr("0001-first.md", { id: "0009" })];
  assert.match(lint({ files, budget: 70 }).problems[0], /id 0009 != filename/);
});

test("fires on a missing title and a missing summary", () => {
  const files = [adr("0001-first.md", { title: "", summary: "" })];
  const { problems } = lint({ files, budget: 70 });
  assert.ok(problems.some(p => /missing frontmatter title/.test(p)));
  assert.ok(problems.some(p => /missing frontmatter summary/.test(p)));
});

test("fires on duplicate ids across files", () => {
  const files = [adr("0001-a.md"), adr("0001-b.md", { id: "0001" })];
  assert.ok(lint({ files, budget: 70 }).problems.some(p => /Duplicate ADR ids: 0001/.test(p)));
});

test("fires when an ADR names a release version (version-agnostic)", () => {
  const files = [adr("0001-first.md", { body: "\n# 0001\n\n## Decision\nShip it in v1.2.0.\n" })];
  assert.match(lint({ files, budget: 70 }).problems[0], /names a release version.*1\.2\.0/);
});

test("fires on a dangling cross-ADR cite", () => {
  const files = [adr("0001-first.md", { body: "\n# 0001\n\nSupersedes ADR 0099.\n" })];
  assert.match(lint({ files, budget: 70 }).problems[0], /dangling ADR cite\(s\): 0099/);
});

test("fires on a dangling `superseded by NNNN` status pointer (the headline fold-cite)", () => {
  const files = [adr("0001-first.md", { status: "superseded by 0099" })];
  assert.match(lint({ files, budget: 70 }).problems[0], /dangling ADR cite\(s\): 0099/);
});

test("a self-cite is not flagged as dangling", () => {
  const files = [adr("0001-first.md", { body: "\n# 0001 — see ADR 0001 above\n" })];
  assert.deepEqual(lint({ files, budget: 70 }).problems, []);
});

test("a resolvable cross-ADR cite is not flagged", () => {
  const files = [adr("0001-a.md", { body: "\n# 0001\n\nBuilds on ADR 0002.\n" }), adr("0002-b.md")];
  assert.deepEqual(lint({ files, budget: 70 }).problems, []);
});

test("fires when an ADR exceeds the line budget", () => {
  const files = clean();
  assert.match(lint({ files, budget: 3 }).problems[0], /lines > 3-line budget/);
});

test("fires UNFALSIFIABLE when an ADR states no falsifiable criterion", () => {
  const files = [adr("0001-first.md", { noCriterion: true })];
  assert.match(lint({ files, budget: 70 }).problems[0], /UNFALSIFIABLE/);
});

test("an [unverifiable] paired with a REOPEN-IF is revisitable, not UNFALSIFIABLE", () => {
  const files = [adr("0001-first.md", {
    noCriterion: true,
    body: "\n# 0001\n\n## Assumptions\n- [unverifiable] the market wants X — REOPEN-IF a user asks\n",
  })];
  assert.deepEqual(lint({ files, budget: 70 }).problems, []);
});

test("an [unverifiable] with no REOPEN-IF is still UNFALSIFIABLE (no fake-criterion escape)", () => {
  const files = [adr("0001-first.md", {
    noCriterion: true,
    body: "\n# 0001\n\n## Assumptions\n- [unverifiable] the market wants X\n",
  })];
  assert.match(lint({ files, budget: 70 }).problems[0], /UNFALSIFIABLE/);
});

test("a bare [unverifiable] with a stray REOPEN-IF elsewhere is still UNFALSIFIABLE (pairing is same-bullet)", () => {
  const files = [adr("0001-first.md", {
    noCriterion: true,
    body: "\n# 0001\n\n## Assumptions\n- [unverifiable] the market wants X\n\n## Revisit triggers\n- REOPEN-IF a user asks\n",
  })];
  assert.match(lint({ files, budget: 70 }).problems[0], /UNFALSIFIABLE/);
});

test("an asterisk-marked criterion bullet is valid (markdown allows `*` and `-` list markers)", () => {
  const files = [adr("0001-first.md", {
    noCriterion: true,
    body: "\n# 0001\n\n## Assumptions\n* [checkable] it works — owner, verified\n",
  })];
  assert.deepEqual(lint({ files, budget: 70 }).problems, []);
});

test("a prose mention of [checkable] is not a criterion bullet (presence, not substring)", () => {
  const files = [adr("0001-first.md", {
    noCriterion: true,
    body: "\n# 0001\n\nThe gate checks every [checkable] assumption it is given.\n",
  })];
  assert.match(lint({ files, budget: 70 }).problems[0], /UNFALSIFIABLE/);
});

test("accumulates independent problems rather than stopping at the first", () => {
  const files = [adr("0001-a.md", { id: "0009", body: "\n# x ships v2.0.0, cites ADR 0077\n" })];
  const { problems } = lint({ files, budget: 70 });
  // id!=filename + version + dangling cite = 3
  assert.equal(problems.length, 3);
});
