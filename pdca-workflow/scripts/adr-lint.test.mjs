/*
 * adr-lint.test.mjs — proves adr-lint's decision logic (the poka-yoke for the poka-yoke).
 * Zero-dependency: node's built-in test runner + assert, so it runs with
 * `node --test pdca-workflow/scripts/*.test.mjs` (repo root) on any stack. Each case plants exactly one corpus defect
 * (or a clean corpus) and asserts the matching guard fires.
 */
import { test } from "node:test";
import assert from "node:assert/strict";
import { readFileSync, readdirSync } from "node:fs";
import { join } from "node:path";
import { fileURLToPath } from "node:url";
import { lint, manifestDrift } from "./adr-lint.mjs";
import { ADR_CHAR_BUDGET } from "./char-budget.mjs";

// The real ADR corpus as lint() consumes it (CRLF-normalized, matching adr-lint main() + charLen).
const ADR_DIR = fileURLToPath(new URL("../../docs/decisions/", import.meta.url));
const corpus = () =>
  readdirSync(ADR_DIR)
    .filter(f => /^\d{4}-.*\.md$/.test(f))
    .map(name => ({ name, text: readFileSync(join(ADR_DIR, name), "utf8").replace(/\r\n/g, "\n") }));

// An ADR body padded to a given char length, so a char-budget case is explicit (not line-count luck).
const padTo = (id, chars) => {
  const head = `\n# ${id} — A decision\n\n`;
  return head + "x".repeat(Math.max(0, chars - head.length)) + "\n";
};

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
  assert.deepEqual(lint({ files: clean() }).problems, []);
});

test("fires on missing frontmatter", () => {
  const files = [adr("0001-first.md", { frontmatter: "# 0001 — no frontmatter" })];
  const { problems } = lint({ files });
  assert.equal(problems.length, 1);
  assert.match(problems[0], /missing YAML frontmatter/);
});

test("fires on a bad/missing frontmatter id", () => {
  const files = [adr("0001-first.md", { id: "xx" })];
  assert.match(lint({ files }).problems[0], /bad\/missing frontmatter id/);
});

test("fires when the frontmatter id does not match the filename", () => {
  const files = [adr("0001-first.md", { id: "0009" })];
  assert.match(lint({ files }).problems[0], /id 0009 != filename/);
});

test("fires on a missing title and a missing summary", () => {
  const files = [adr("0001-first.md", { title: "", summary: "" })];
  const { problems } = lint({ files });
  assert.ok(problems.some(p => /missing frontmatter title/.test(p)));
  assert.ok(problems.some(p => /missing frontmatter summary/.test(p)));
});

test("fires on duplicate ids across files", () => {
  const files = [adr("0001-a.md"), adr("0001-b.md", { id: "0001" })];
  assert.ok(lint({ files }).problems.some(p => /Duplicate ADR ids: 0001/.test(p)));
});

test("fires when an ADR names a release version (version-agnostic)", () => {
  const files = [adr("0001-first.md", { body: "\n# 0001\n\n## Decision\nShip it in v1.2.0.\n" })];
  assert.match(lint({ files }).problems[0], /names a release version.*1\.2\.0/);
});

test("fires on a dangling cross-ADR cite", () => {
  const files = [adr("0001-first.md", { body: "\n# 0001\n\nSupersedes ADR 0099.\n" })];
  assert.match(lint({ files }).problems[0], /dangling ADR cite\(s\): 0099/);
});

test("fires on a dangling `superseded by NNNN` status pointer (the headline fold-cite)", () => {
  const files = [adr("0001-first.md", { status: "superseded by 0099" })];
  assert.match(lint({ files }).problems[0], /dangling ADR cite\(s\): 0099/);
});

test("a self-cite is not flagged as dangling", () => {
  const files = [adr("0001-first.md", { body: "\n# 0001 — see ADR 0001 above\n" })];
  assert.deepEqual(lint({ files }).problems, []);
});

test("a resolvable cross-ADR cite is not flagged", () => {
  const files = [adr("0001-a.md", { body: "\n# 0001\n\nBuilds on ADR 0002.\n" }), adr("0002-b.md")];
  assert.deepEqual(lint({ files }).problems, []);
});

// Char budget, not lines: a line cap is gameable by long lines (ADR 0008). No exemptions — an ADR
// over the cap is a violation. Decision logic unit-tested on synthetic input, then run over the
// real corpus (every ADR is under budget after 0006's rewrite -> no firing).
test("char budget: over the cap fires, at/under passes (decision logic)", () => {
  const at = (id, chars) => [adr(`${id}-x.md`, { id, body: padTo(id, chars) })];
  // An ADR over the cap -> violation.
  assert.match(lint({ files: at("9999", ADR_CHAR_BUDGET + 100), budget: ADR_CHAR_BUDGET }).problems[0],
    /chars > \d+-char budget/);
  // An ADR comfortably under the cap -> no char-budget problem.
  assert.deepEqual(
    lint({ files: at("9999", ADR_CHAR_BUDGET - 500), budget: ADR_CHAR_BUDGET }).problems, []);
  // (The strict at-cap boundary — overBudget(6000,6000)===false — is unit-tested in char-budget.test.mjs.)
});

test("no ADR exceeds the char budget on the real corpus", () => {
  const over = lint({ files: corpus() }).problems.filter(p => /char budget/.test(p));
  assert.deepEqual(over, []);
});

test("fires UNFALSIFIABLE when an ADR states no falsifiable criterion", () => {
  const files = [adr("0001-first.md", { noCriterion: true })];
  assert.match(lint({ files }).problems[0], /UNFALSIFIABLE/);
});

test("an [unverifiable] paired with a REOPEN-IF is revisitable, not UNFALSIFIABLE", () => {
  const files = [adr("0001-first.md", {
    noCriterion: true,
    body: "\n# 0001\n\n## Assumptions\n- [unverifiable] the market wants X — REOPEN-IF a user asks\n",
  })];
  assert.deepEqual(lint({ files }).problems, []);
});

test("an [unverifiable] with no REOPEN-IF is still UNFALSIFIABLE (no fake-criterion escape)", () => {
  const files = [adr("0001-first.md", {
    noCriterion: true,
    body: "\n# 0001\n\n## Assumptions\n- [unverifiable] the market wants X\n",
  })];
  assert.match(lint({ files }).problems[0], /UNFALSIFIABLE/);
});

test("a bare [unverifiable] with a stray REOPEN-IF elsewhere is still UNFALSIFIABLE (pairing is same-bullet)", () => {
  const files = [adr("0001-first.md", {
    noCriterion: true,
    body: "\n# 0001\n\n## Assumptions\n- [unverifiable] the market wants X\n\n## Revisit triggers\n- REOPEN-IF a user asks\n",
  })];
  assert.match(lint({ files }).problems[0], /UNFALSIFIABLE/);
});

test("an asterisk-marked criterion bullet is valid (markdown allows `*` and `-` list markers)", () => {
  const files = [adr("0001-first.md", {
    noCriterion: true,
    body: "\n# 0001\n\n## Assumptions\n* [checkable] it works — owner, verified\n",
  })];
  assert.deepEqual(lint({ files }).problems, []);
});

test("a prose mention of [checkable] is not a criterion bullet (presence, not substring)", () => {
  const files = [adr("0001-first.md", {
    noCriterion: true,
    body: "\n# 0001\n\nThe gate checks every [checkable] assumption it is given.\n",
  })];
  assert.match(lint({ files }).problems[0], /UNFALSIFIABLE/);
});

test("accumulates independent problems rather than stopping at the first", () => {
  const files = [adr("0001-a.md", { id: "0009", body: "\n# x ships v2.0.0, cites ADR 0077\n" })];
  const { problems } = lint({ files });
  // id!=filename + version + dangling cite = 3
  assert.equal(problems.length, 3);
});

// Marketplace<->plugin.json mirror (ADR 0011): a field stated in both homes must be identical.
test("manifestDrift: identical shared fields report no problems", () => {
  const pairs = [{ name: "p", entry: { description: "d" }, plugin: { description: "d", version: "1" } }];
  assert.deepEqual(manifestDrift(pairs), []);
});

test("manifestDrift: a drifted description fires", () => {
  const pairs = [{ name: "p", entry: { description: "a" }, plugin: { description: "b" } }];
  assert.match(manifestDrift(pairs)[0], /marketplace description drifts/);
});

test("manifestDrift: a field omitted from the marketplace entry is not drift (derive, don't mirror)", () => {
  const pairs = [{ name: "p", entry: {}, plugin: { description: "d", version: "1" } }];
  assert.deepEqual(manifestDrift(pairs), []);
});
