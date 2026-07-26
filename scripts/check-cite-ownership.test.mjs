/*
 * check-cite-ownership.test.mjs — proves the semantic cite gate's decision logic. The fixtures
 * are the REAL mis-cites this gate was built from (2026-07-25 sweep): the append-only doctrine
 * credited to ADR 0026 when 0041 owns it, and the eval-clustered CI credited to ADR 0025 when
 * 0019 owns it. Run: node --test scripts/*.test.mjs from the repo root.
 */
import { test } from "node:test";
import assert from "node:assert/strict";
import { ownsTerm, scanLine, walkLiveFiles, TERMS } from "./check-cite-ownership.mjs";

// --- ownsTerm -------------------------------------------------------------------------------

test("owns: the record states the term on its own account", () => {
  assert.equal(ownsTerm("Dated dirs are append-only measurement records — never retrofit.", "0041", "append-only"), true);
});

test("does NOT own: the record never states the term (the real ADR 0026 case)", () => {
  assert.equal(ownsTerm("Artifact format: flat CSV, JSONL, gzip retention of raw output.", "0026", "append-only"), false);
});

test("does NOT own: states the term only while crediting another record (the real ADR 0025 case)", () => {
  const t = "the eval-clustered CI (ADR 0019) width-warns everywhere, which is underpowered.";
  assert.equal(ownsTerm(t, "0025", "eval-clustered"), false);
});

test("owns: credits ITSELF next to the term", () => {
  assert.equal(ownsTerm("the eval-clustered CI (ADR 0019) is the headline verdict", "0019", "eval-clustered"), true);
});

test("owns: ONE bare statement outweighs an earlier credited mention", () => {
  const t = "the eval-clustered CI (ADR 0019) is the prior art.\nHere the eval-clustered CI is redefined.";
  assert.equal(ownsTerm(t, "0023", "eval-clustered"), true, "the second, uncredited mention is a claim of ownership");
});

test("does NOT own: EVERY mention credits another record", () => {
  const t = "the eval-clustered CI (ADR 0019) warns.\nAgain the eval-clustered CI (ADR 0019) applies.";
  assert.equal(ownsTerm(t, "0025", "eval-clustered"), false);
});

test("unknown id stays silent — adr-lint owns the dangling-cite check", () => {
  assert.equal(ownsTerm(null, "9999", "append-only"), true);
});

// --- scanLine -------------------------------------------------------------------------------

const owns = (id, term) => (term === "append-only" ? id === "0041" : id === "0019");

test("flags the real ADR 0070 line: `(ADR 0026/0041)` binds to the FIRST following cite", () => {
  const hits = scanLine("The append-only rule (ADR 0026/0041) freezes a dir at merge.", owns);
  assert.equal(hits.length, 1);
  assert.equal(hits[0].adr, "0026");
  assert.equal(hits[0].term, "append-only");
});

test("flags the possessive form with no following cite (the real ADR 0037 line)", () => {
  const hits = scanLine("- Enforced: this landing PR; ADR 0024's append-only rule + CLAUDE.md Shipping.", owns);
  assert.deepEqual(hits.map((h) => h.adr), ["0024"]);
});

test("clean when the bound cite owns the term", () => {
  assert.deepEqual(scanLine("The append-only rule (ADR 0041) freezes a dir at merge.", owns), []);
});

test("a FOLLOWING cite wins over a nearer PRECEDING one — two mechanisms, one line", () => {
  // The real ADR 0024:30 shape: without this rule it binds eval-clustered to 0023 and false-fires.
  const line = "- [checkable] the hermetic executor (ADR 0023) + eval-clustered CI (ADR 0019) exist.";
  assert.deepEqual(scanLine(line, owns), []);
});

test("a cite beyond the binding window is not bound to the term", () => {
  const far = "append-only immutability of dated records — empirical-evals.md:159; noted in ADR 0026 as silent.";
  assert.deepEqual(scanLine(far, owns), []);
});

test("no cite on the line means nothing to judge", () => {
  assert.deepEqual(scanLine("Dated dirs are append-only records.", owns), []);
});

test("reports every offending term occurrence on a line, not just the first", () => {
  const line = "append-only (ADR 0026) and eval-clustered (ADR 0025)";
  assert.deepEqual(scanLine(line, owns).map((h) => `${h.term}:${h.adr}`), ["append-only:0026", "eval-clustered:0025"]);
});

test("matching is case-insensitive on the term", () => {
  assert.deepEqual(scanLine("The Append-Only rule (ADR 0026).", owns).map((h) => h.adr), ["0026"]);
});

test("TERMS is scar-backed and non-empty — an empty list would make the gate vacuous", () => {
  assert.ok(TERMS.length >= 2);
  assert.ok(TERMS.includes("append-only") && TERMS.includes("eval-clustered"));
});

// --- walk -----------------------------------------------------------------------------------

const dirent = (name, dir = false) => ({ name, isDirectory: () => dir });

test("walk skips frozen dated benchmark dirs and the gate's own source", () => {
  const tree = {
    ".": [dirent("benchmarks", true), dirent("scripts", true), dirent("CLAUDE.md")],
    "benchmarks": [dirent("2026-07-10-frozen", true), dirent("lib", true), dirent("README.md")],
    "benchmarks/2026-07-10-frozen": [dirent("README.md")],
    "benchmarks/lib": [dirent("verdict.py")],
    "scripts": [dirent("check-cite-ownership.mjs"), dirent("check-cite-ownership.test.mjs"), dirent("scorecard.mjs")],
  };
  const readdir = (p) => {
    const k = p.replace(/\\/g, "/").replace(/^\.\//, "") || ".";
    if (!(k in tree)) { const e = new Error("ENOENT"); e.code = "ENOENT"; throw e; }
    return tree[k];
  };
  const files = walkLiveFiles(".", readdir).sort();
  assert.deepEqual(files, ["CLAUDE.md", "benchmarks/README.md", "benchmarks/lib/verdict.py", "scripts/scorecard.mjs"]);
});

test("walk tolerates a dir vanishing mid-walk but never the root", () => {
  const tree = { ".": [dirent("gone", true), dirent("CLAUDE.md")] };
  const readdir = (p) => {
    const k = p.replace(/\\/g, "/").replace(/^\.\//, "") || ".";
    if (!(k in tree)) { const e = new Error("ENOENT"); e.code = "ENOENT"; throw e; }
    return tree[k];
  };
  assert.deepEqual(walkLiveFiles(".", readdir), ["CLAUDE.md"]);
  assert.throws(() => walkLiveFiles("nowhere", readdir), /ENOENT/);
});

// --- credit on EITHER side (red-team round 3: the founding scar defeated the first predicate) --

test("does NOT own: the disclaiming credit PRECEDES the term (the real ADR 0025:13 shape)", () => {
  const t = "charges an artifact's benefit against its baseline via the ADR 0019 eval-clustered CI, but left the score unspecified.";
  assert.equal(ownsTerm(t, "0025", "eval-clustered"), false);
});

test("does NOT own: a credit 40+ chars out still disclaims (ADR 0025:16 shape, the window scar)", () => {
  const t = "The verdict is the eval-clustered mean delta (with - without) + 95% CI (ADR 0019); the KEEP bar is unchanged.";
  assert.equal(ownsTerm(t, "0025", "eval-clustered"), false);
});

test("owns: a SELF credit on either side is ownership, not a disclaimer", () => {
  assert.equal(ownsTerm("per ADR 0019 the eval-clustered CI is the headline.", "0019", "eval-clustered"), true);
  assert.equal(ownsTerm("the eval-clustered CI is the headline (ADR 0019).", "0019", "eval-clustered"), true);
});

test("owns: a far-away unrelated cite does not disclaim", () => {
  const t = "Dated dirs are append-only records." + " ".repeat(80) + "Separately, see ADR 0023 for formats.";
  assert.equal(ownsTerm(t, "0041", "append-only"), true);
});
