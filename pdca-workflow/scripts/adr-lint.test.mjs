/*
 * adr-lint.test.mjs — proves adr-lint's decision logic (the poka-yoke for the poka-yoke).
 * Zero-dependency: node's built-in test runner + assert, so it runs with
 * `node --test pdca-workflow/scripts/*.test.mjs` (repo root) on any stack. Each case plants targeted
 * defect(s) — or runs a clean/real corpus — and asserts exactly the matching guard(s) fire.
 */
import { test } from "node:test";
import assert from "node:assert/strict";
import { readFileSync, readdirSync } from "node:fs";
import { join } from "node:path";
import { fileURLToPath } from "node:url";
import { lint, manifestDrift, agentProblems, decisionSetProblems, marginWarnings } from "./adr-lint.mjs";
import { ADR_CHAR_BUDGET, ADR_CHAR_MARGIN, AGENT_CHAR_BUDGET } from "./char-budget.mjs";
import { mkdtempSync, writeFileSync, rmSync } from "node:fs";
import { basename } from "node:path";

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
status: ${o.status ?? "accepted"}${o.tier ? `\ntier: ${o.tier}` : ""}
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

test("fires on an unpointed amendment (amender not cited back)", () => {
  const files = [
    adr("0001-a.md", { body: "\n# 0001\n\n## Decision\nThis amends ADR 0002's retention rule.\n" }),
    adr("0002-b.md"),
  ];
  assert.match(lint({ files }).problems.join("\n"), /0001-a\.md: amends ADR 0002.*does not cite 0001/);
});

test("a backlinked amendment passes", () => {
  const files = [
    adr("0001-a.md", { body: "\n# 0001\n\n## Decision\nThis amends ADR 0002's retention rule.\n" }),
    adr("0002-b.md", { body: "\n# 0002\n\n## Decision\nAmended by ADR 0001 (see there).\n" }),
  ];
  assert.deepEqual(lint({ files }).problems, []);
});

test("passive 'amended by' is not itself flagged as an amendment", () => {
  const files = [
    adr("0001-a.md", { body: "\n# 0001\n\n## Decision\nAmended by ADR 0002 later.\n" }),
    adr("0002-b.md"),
  ];
  assert.deepEqual(lint({ files }).problems, []);
});

test("no unpointed amendment on the real corpus", () => {
  const hits = lint({ files: corpus() }).problems.filter(p => /unpointed amendment/.test(p));
  assert.deepEqual(hits, []);
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

// Lite tier (`tier: lite`): a SETTLED decision — exempt from the criterion gate, held to the
// lite budget, and REJECTED if it smuggles in a revisit trigger (must graduate to a full ADR).
test("lite: a settled decision without a criterion passes", () => {
  const files = [adr("0001-first.md", {
    tier: "lite", noCriterion: true,
    body: "\n# 0001 — a settled call\n\nDecision + why. Enforced: some.test.mjs.\n",
  })];
  assert.deepEqual(lint({ files }).problems, []);
});

test("lite: a REOPEN-IF must graduate to a full ADR", () => {
  const files = [adr("0001-first.md", {
    tier: "lite", noCriterion: true,
    body: "\n# 0001\n\nDecision. REOPEN-IF: usage grows.\n",
  })];
  assert.match(lint({ files }).problems[0], /graduate it to a full ADR/);
});

test("lite: an [unverifiable] bullet or Revisit triggers section must graduate", () => {
  const withBullet = [adr("0001-a.md", {
    tier: "lite", noCriterion: true,
    body: "\n# 0001\n\n- [unverifiable] this holds\n",
  })];
  assert.match(lint({ files: withBullet }).problems[0], /graduate/);
  const withSection = [adr("0002-b.md", {
    tier: "lite", noCriterion: true,
    body: "\n# 0002\n\n## Revisit triggers\n- something changes\n",
  })];
  assert.match(lint({ files: withSection }).problems[0], /graduate/);
});

test("lite: held to the lite budget while a full ADR of the same size passes", () => {
  const big = padTo("0001", 2000);
  const lite = [adr("0001-a.md", { tier: "lite", noCriterion: true, body: big })];
  assert.match(lint({ files: lite }).problems[0], /lite budget/);
  const full = [adr("0001-a.md", { body: big })];
  assert.deepEqual(lint({ files: full }).problems, []);
});

test("lite: still subject to version-agnostic and dangling-cite guards", () => {
  const files = [adr("0001-a.md", {
    tier: "lite", noCriterion: true,
    body: "\n# 0001\n\nShipped in v1.2.3 per ADR 0099.\n",
  })];
  const { problems } = lint({ files });
  assert.ok(problems.some(p => /release version/.test(p)));
  assert.ok(problems.some(p => /dangling ADR cite/.test(p)));
});

// Decision-set connectivity (ADR 0051): multiple new ADRs in one change must form one connected
// undirected cite graph; fewer than two new ADRs = nothing to check.
test("decision-set: absent, empty, or singleton new-ADR list reports nothing (fail open)", () => {
  const files = clean();
  assert.deepEqual(decisionSetProblems([], files), []);
  assert.deepEqual(decisionSetProblems(["0001"], files), []);
  assert.deepEqual(decisionSetProblems(["docs/decisions/0001-first.md"], files), []);
});

test("decision-set: the real 0047-0050 corpus set passes (the precedent that pinned the connectivity bar)", () => {
  assert.deepEqual(decisionSetProblems(["0047", "0048", "0049", "0050"], corpus()), []);
});

test("decision-set: two new ADRs sharing no cite fail, naming the stranded id", () => {
  const problems = decisionSetProblems(["0001", "0002"], clean());
  assert.equal(problems.length, 1);
  assert.match(problems[0], /not one connected decision set/);
  assert.match(problems[0], /unconnected: 0002/);
});

test("decision-set: a one-directional cite connects (the bar is undirected, not mutual)", () => {
  const files = [
    adr("0001-a.md", { body: "\n# 0001\n\n- Date: 2026-06-27\n\nExtends ADR 0002.\n" }),
    adr("0002-b.md"),
  ];
  assert.deepEqual(decisionSetProblems(["0001", "0002"], files), []);
});

test("decision-set: two internally-linked pairs with no bridge are two sets and fail; self-cites don't count", () => {
  const files = [
    adr("0001-a.md", { body: "\n# 0001\n\nSee ADR 0002.\n" }),
    adr("0002-b.md", { body: "\n# 0002\n\nSee ADR 0001.\n" }),
    adr("0003-c.md", { body: "\n# 0003\n\nSee ADR 0004.\n" }),
    adr("0004-d.md", { body: "\n# 0004\n\nSee ADR 0004.\n" }),
  ];
  const problems = decisionSetProblems(["0001", "0002", "0003", "0004"], files);
  assert.equal(problems.length, 1);
});

test("decision-set: file paths from a CI diff resolve to ids (posix or windows separators)", () => {
  const problems = decisionSetProblems(
    ["docs/decisions/0001-first.md", "docs\\decisions\\0002-second.md"], clean());
  assert.equal(problems.length, 1); // parsed as 0001 + 0002, which share no cite
});

// Agent homes (ADR 0028): both agent dirs get the budget + name-matches-filename checks, and a
// defect surfaces as a formatted lint problem (the integration adr-lint's exit code rides on).
const AGENT_ROOT = fileURLToPath(new URL("../../", import.meta.url));

test("agentProblems formats mismatch and over-budget defects as lint problems", () => {
  const abs = mkdtempSync(join(AGENT_ROOT, "tmp-agent-lint-fixture-"));
  const dir = basename(abs); // ROOT-relative, as char-budget.mjs expects
  try {
    writeFileSync(join(abs, "good.md"), "---\nname: good\ndescription: x\n---\nbody\n");
    writeFileSync(join(abs, "bad.md"), "---\nname: wrong\ndescription: x\n---\nbody\n");
    writeFileSync(join(abs, "huge.md"), `---\nname: huge\ndescription: x\n---\n${"x".repeat(AGENT_CHAR_BUDGET + 1)}\n`);
    const problems = agentProblems([dir]);
    assert.ok(problems.some(p => p.startsWith("agent name mismatch: ") && p.includes("bad.md")), problems.join("; "));
    assert.ok(problems.some(p => p.startsWith("agent over budget: ") && p.includes("huge.md")), problems.join("; "));
    assert.equal(problems.filter(p => p.includes("good.md")).length, 0);
  } finally {
    rmSync(abs, { recursive: true, force: true });
  }
});

test("agentProblems tolerates absent dirs (a consumer may have neither agent home)", () => {
  assert.deepEqual(agentProblems(["no-such-dir-a", "no-such-dir-b"]), []);
});

test("both real agent homes are clean (the corpus the gate actually runs on)", () => {
  assert.deepEqual(agentProblems(), []);
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

// --- marginWarnings (ADR 0067): advisory drafting-margin WARN on NEW full ADRs only ---
const marginFixture = (id, chars, lite = false) => ({
  name: `${id}-x.md`,
  text: `---\nid: ${id}\ntitle: "t"\nstatus: accepted\n${lite ? "tier: lite\n" : ""}summary: "s"\n---\n`
    .padEnd(chars, "y"),
});

test("margin: a new full ADR past the margin warns, naming the file and the margin", () => {
  const files = [marginFixture("0001", ADR_CHAR_MARGIN + 200)];
  const warns = marginWarnings(["docs/decisions/0001-x.md"], files);
  assert.equal(warns.length, 1);
  assert.match(warns[0], /0001-x\.md/);
  assert.match(warns[0], /drafting margin/);
});

test("margin: at or under the margin, no warning", () => {
  const files = [marginFixture("0001", ADR_CHAR_MARGIN)];
  assert.deepEqual(marginWarnings(["0001"], files), []);
});

test("margin: a lite ADR is exempt (own cap, no Act machinery)", () => {
  const files = [marginFixture("0001", ADR_CHAR_MARGIN + 200, true)];
  assert.deepEqual(marginWarnings(["0001"], files), []);
});

test("margin: an over-margin ADR NOT in the new set stays quiet (legacy corpus not swept)", () => {
  const files = [marginFixture("0001", ADR_CHAR_MARGIN + 200), marginFixture("0002", ADR_CHAR_MARGIN + 200)];
  const warns = marginWarnings(["0002"], files);
  assert.equal(warns.length, 1);
  assert.match(warns[0], /0002-x\.md/);
});
