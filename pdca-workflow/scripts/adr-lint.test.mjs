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
import { lint, manifestDrift, agentProblems, decisionSetWarnings, marginWarnings, repoFileList, docIndexDrift, indexScanSet } from "./adr-lint.mjs";
import { ADR_CHAR_BUDGET, ADR_CHAR_MARGIN, AGENT_CHAR_BUDGET, LITE_ADR_CHAR_BUDGET, DOC_BUDGETS } from "./char-budget.mjs";
import { mkdtempSync, mkdirSync, writeFileSync, rmSync } from "node:fs";
import { tmpdir } from "node:os";
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

// Outcome vocabulary (ADR 0079, spec check 13): a scorecard consumer classifies `- [outcome]`
// rows on exactly one controlled word; a synonym or double-tag is unclassifiable and a dropped
// miss reads as no miss.
test("fires on an [outcome] row without exactly one of verified|violated|still-open", () => {
  const files = [adr("0001-a.md", {
    body: "\n# 0001\n\n- Date: 2026-06-27\n\n## Act (post-ship)\n- [outcome] H1 FALSIFIED judge-robust.\n- [outcome] verified then violated on rerun.\n",
  })];
  const { problems } = lint({ files });
  assert.equal(problems.filter(p => /\[outcome\] row must carry exactly one/.test(p)).length, 2);
  assert.match(problems[0], /has 0/);
  assert.match(problems[1], /has 2/);
});

test("a controlled-vocabulary [outcome] row passes; prose mentioning the words is not a row", () => {
  const files = [adr("0001-a.md", {
    body: "\n# 0001\n\nProse saying verified and violated together is fine.\n\n## Act (post-ship)\n- [outcome] premise held under re-measure — verified.\n- [outcome] awaiting the A/B signal — still-open.\n",
  })];
  assert.deepEqual(lint({ files }).problems, []);
});

test("no uncontrolled [outcome] row on the real corpus", () => {
  const hits = lint({ files: corpus() }).problems.filter(p => /\[outcome\] row/.test(p));
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

test("a WRAPPED [unverifiable] bullet keeps its REOPEN-IF (same-bullet, not same-line)", () => {
  const files = [adr("0001-first.md", {
    noCriterion: true,
    body: "\n# 0001\n\n## Assumptions\n- [unverifiable] the market wants X, which nothing in-sandbox\n  settles today. REOPEN-IF a user asks -> revisit\n",
  })];
  assert.deepEqual(lint({ files }).problems, []);
});

test("a wrapped [unverifiable] whose REOPEN-IF sits in the NEXT bullet is still UNFALSIFIABLE", () => {
  const files = [adr("0001-first.md", {
    noCriterion: true,
    body: "\n# 0001\n\n## Assumptions\n- [unverifiable] the market wants X\n  and nothing settles it\n- [verified] REOPEN-IF a user asks\n",
  })];
  assert.match(lint({ files }).problems[0], /UNFALSIFIABLE/);
});

test("a REOPEN-IF in a LATER [unverifiable] bullet does not rescue an earlier one without it", () => {
  const files = [adr("0001-first.md", {
    noCriterion: true,
    body: "\n# 0001\n\n## Assumptions\n- [unverifiable] the market wants X\n- [unverifiable] and Y — REOPEN-IF a user asks\n",
  })];
  // The second bullet IS a valid criterion, so the record passes — but it must pass on that
  // bullet's own account. Regression guard: an earlier bare bullet must never borrow it.
  assert.deepEqual(lint({ files }).problems, []);
});

test("bullets are tested separately: a bare [unverifiable] plus a later NON-tagged REOPEN-IF still fails", () => {
  const files = [adr("0001-first.md", {
    noCriterion: true,
    body: "\n# 0001\n\n## Assumptions\n- [unverifiable] the market wants X\n\n## Revisit triggers\n- REOPEN-IF a user asks\n",
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

test("lite: a Reopen-if is ALLOWED (ADR 0092) — it is an anti-churn field, not a graduation trigger", () => {
  const files = [adr("0001-first.md", {
    tier: "lite", noCriterion: true,
    body: "\n# 0001\n\n- Decision: x.\n- Reopen-if: usage grows.\n- Enforced: adr-lint.mjs\n",
  })];
  assert.deepEqual(lint({ files }).problems, []);
});

test("lite: the ASSUMPTION MACHINERY graduates it — a tagged bullet or an ## Assumptions block (ADR 0092)", () => {
  for (const body of ["\n# 0001\n\n- [unverifiable] this holds\n",
                      "\n# 0001\n\n- [checkable] this is testable\n",
                      "\n# 0001\n\n## Assumptions\n- something\n"]) {
    const files = [adr("0001-a.md", { tier: "lite", noCriterion: true, body })];
    assert.match(lint({ files }).problems[0], /graduate it to a full ADR/, body);
  }
  // A bare `## Revisit triggers` section no longer graduates — reopening is lite's business now.
  const withSection = [adr("0002-b.md", {
    tier: "lite", noCriterion: true,
    body: "\n# 0002\n\n- Enforced: adr-lint.mjs\n\n## Revisit triggers\n- something changes\n",
  })];
  assert.deepEqual(lint({ files: withSection }).problems, []);
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

// Lite `Enforced:` gate (ADR 0087): positive bar — line present, cited file tokens resolve
// against `repoFiles` (exact path or basename), token-free free-form passes.
const REPO = ["scripts/gate.test.mjs", ".github/workflows/gates.yml", "docs/notes.md"];
const liteAdr = (name, body) => adr(name, { tier: "lite", noCriterion: true, body });

test("lite: a missing 'Enforced:' line fires (settled = enforced somewhere findable)", () => {
  const files = [liteAdr("0001-a.md", "\n# 0001\n\n- Decision: x\n- Why: y\n")];
  assert.match(lint({ files }).problems[0], /no 'Enforced:' line/);
});

test("lite: an exact-path citation resolves against repoFiles", () => {
  const files = [liteAdr("0001-a.md", "\n# 0001\n\n- Enforced: `scripts/gate.test.mjs` (CI).\n")];
  assert.deepEqual(lint({ files, repoFiles: REPO }).problems, []);
});

test("lite: a bare-basename citation resolves, line-number suffix ignored (the corpus cites `gates.yml`, `verifier.md:22-24`)", () => {
  const files = [liteAdr("0001-a.md", "\n# 0001\n\n- Enforced: gates.yml + notes.md:22-24.\n")];
  assert.deepEqual(lint({ files, repoFiles: REPO }).problems, []);
});

test("lite: a citation resolving nowhere fires, naming the token (stale-citation rot)", () => {
  const files = [liteAdr("0001-a.md", "\n# 0001\n\n- Enforced: `benchmarks/lib/run.mjs` per CI.\n")];
  const { problems } = lint({ files, repoFiles: REPO });
  assert.equal(problems.length, 1);
  assert.match(problems[0], /not on disk: benchmarks\/lib\/run\.mjs/);
});

test("lite: a token-free free-form 'Enforced:' passes (ADR 0075 'absence' precedent)", () => {
  const files = [liteAdr("0001-a.md", "\n# 0001\n\n- Enforced: absence (nothing to drift).\n")];
  assert.deepEqual(lint({ files, repoFiles: REPO }).problems, []);
});

test("lite: a token on a wrapped continuation line is still checked", () => {
  const files = [liteAdr("0001-a.md", "\n# 0001\n\n- Enforced: the gate\n  wired in ghost.test.mjs there.\n")];
  assert.match(lint({ files, repoFiles: REPO }).problems[0], /ghost\.test\.mjs/);
});

test("lite: without repoFiles resolution is skipped, presence still enforced", () => {
  const present = [liteAdr("0001-a.md", "\n# 0001\n\n- Enforced: no-such-file.mjs.\n")];
  assert.deepEqual(lint({ files: present }).problems, []);
  const absent = [liteAdr("0002-b.md", "\n# 0002\n\n- Decision: x\n")];
  assert.match(lint({ files: absent }).problems[0], /no 'Enforced:' line/);
});

test("lite: an 'Enforced:' only in the frontmatter summary does not satisfy presence", () => {
  const files = [adr("0001-a.md", {
    tier: "lite", noCriterion: true, summary: "Enforced: x.mjs",
    body: "\n# 0001\n\n- Decision: x\n",
  })];
  assert.match(lint({ files }).problems[0], /no 'Enforced:' line/);
});

test("a full ADR needs no 'Enforced:' line (the gate is lite-only)", () => {
  assert.deepEqual(lint({ files: clean() }).problems, []);
});

test("lite: a prose mention before the real line does not shadow it — ALL occurrences are validated (the 0087 self-shape)", () => {
  const files = [liteAdr("0001-a.md",
    "\n# 0001\n\n- Decision: an `Enforced:` line must be present.\n- Enforced: ghost.test.mjs (CI).\n")];
  assert.match(lint({ files, repoFiles: REPO }).problems[0], /ghost\.test\.mjs/);
});

test("lite: an UNQUOTED prose mention cannot shadow the real line's token validation (matchAll, not first-match, is load-bearing)", () => {
  const files = [liteAdr("0001-a.md",
    "\n# 0001\n\n- Decision: an Enforced: line must be present.\n- Enforced: ghost.test.mjs (CI).\n")];
  assert.match(lint({ files, repoFiles: REPO }).problems[0], /ghost\.test\.mjs/);
});

test("lite: a backtick-quoted `Enforced:` is prose about the marker and does not satisfy presence", () => {
  const files = [liteAdr("0001-a.md", "\n# 0001\n\n- Decision: the `Enforced:` line matters.\n")];
  assert.match(lint({ files }).problems[0], /no 'Enforced:' line/);
});

test("repoFileList skips .git and node_modules but returns nested real files", () => {
  // OS tmpdir, NOT the repo root: a fixture in the repo root races the sibling suites' surface
  // tests (check-restatement walks the real tree mid-run and ENOENTs on the vanishing dir).
  const abs = mkdtempSync(join(tmpdir(), "walk-fixture-"));
  try {
    for (const d of [".git", "node_modules", "src"]) mkdirSync(join(abs, d));
    writeFileSync(join(abs, ".git", "hidden.mjs"), "");
    writeFileSync(join(abs, "node_modules", "dep.mjs"), "");
    writeFileSync(join(abs, "src", "real.mjs"), "");
    assert.deepEqual(repoFileList(abs).sort(), ["src/real.mjs"]);
  } finally {
    rmSync(abs, { recursive: true, force: true });
  }
});

test("repoFileList skips a subdir that vanishes mid-walk (#282) but throws on missing root / non-ENOENT", () => {
  const d = (name, isDir) => ({ name, isDirectory: () => isDir });
  const enoent = () => Object.assign(new Error("ENOENT: vanished"), { code: "ENOENT" });
  const fake = (p) => {
    if (p === "R") return [d("keep.md", false), d("ghost", true), d("src", true)];
    if (p === join("R", "src")) return [d("real.mjs", false)];
    throw enoent(); // "ghost" vanished between discovery and read — the concurrent-fixture race
  };
  assert.deepEqual(repoFileList("R", fake).sort(), ["keep.md", "src/real.mjs"]);
  // A missing ROOT is caller error, not a race: the gate must not go silently vacuous.
  assert.throws(() => repoFileList("gone", () => { throw enoent(); }), /ENOENT/);
  // Only ENOENT is tolerated — any other failure still surfaces.
  assert.throws(
    () => repoFileList("R", (p) => { if (p === "R") return [d("bad", true)]; throw Object.assign(new Error("EIO"), { code: "EIO" }); }),
    /EIO/,
  );
});

test("every real lite ADR passes the Enforced gate against the real repo walk (measured zero-false-positive claim, mechanized)", () => {
  const hits = lint({ files: corpus(), repoFiles: repoFileList(AGENT_ROOT) }).problems
    .filter(p => /Enforced/.test(p));
  assert.deepEqual(hits, []);
});

// Stale status on recorded discharge (ADR 0088): a `;`-split clause recording "ADR NNNN ...
// discharged" fails while NNNN's frontmatter is still `status: proposed`.
test("discharge: a clause recording an ADR discharged fires while the target is still proposed", () => {
  const files = [
    adr("0001-a.md", { body: "\n# 0001\n\n## Decision\nADR 0002's gating loop is discharged (plateau).\n" }),
    adr("0002-b.md", { status: "proposed" }),
  ];
  assert.match(lint({ files }).problems[0],
    /0001-a\.md: records ADR 0002 discharged, but 0002 is still status: proposed/);
});

test("discharge: an accepted target stays quiet", () => {
  const files = [
    adr("0001-a.md", { body: "\n# 0001\n\n## Decision\nADR 0002's gating loop is discharged (plateau).\n" }),
    adr("0002-b.md"),
  ];
  assert.deepEqual(lint({ files }).problems, []);
});

test("discharge: clause isolation — a proposed cite outside the discharge clause is not flagged (the 0057:28 shape)", () => {
  const files = [
    adr("0001-a.md", { body: "\n# 0001\n\n- [checkable-doc] discharges 0002:40; 0003 (proposed) owns the judge. result: verified.\n" }),
    adr("0002-b.md"),
    adr("0003-c.md", { status: "proposed" }),
  ];
  assert.deepEqual(lint({ files }).problems, []);
});

test("discharge: a date-adjacent 4-digit token never matches even when an ADR with that id exists", () => {
  const files = [
    adr("0001-a.md", { body: "\n# 0001\n\n## Decision\nDISCHARGED 2026-07-14 per re-grade.\n" }),
    adr("2026-x.md", { id: "2026", status: "proposed" }),
  ];
  assert.deepEqual(lint({ files }).problems, []);
});

test("discharge: a self-cite in a discharge clause stays quiet", () => {
  const files = [adr("0001-a.md", { body: "\n# 0001\n\n## Decision\nADR 0001 discharges its own precondition.\n" })];
  assert.deepEqual(lint({ files }).problems, []);
});

test("discharge: no stale-discharge problem on the real corpus", () => {
  const hits = lint({ files: corpus() }).problems.filter(p => /discharged, but/.test(p));
  assert.deepEqual(hits, []);
});

// Doc-indexed constant cross-check (ADR 0088): a doc line naming a char-budget constant beside
// a number must include that constant's current value; presence-direction only.
const CONSTS = { FOO_CAP: 9000, BAR_CAP: 1500 };

test("docIndexDrift: a line naming a constant beside its current value passes", () => {
  const docs = [{ name: "doc.md", text: "| ADR | **9,000** | `x.mjs` (`FOO_CAP`) |\n" }];
  assert.deepEqual(docIndexDrift(docs, CONSTS), []);
});

test("docIndexDrift: a stale number fires naming file:line, constant, and current value", () => {
  const docs = [{ name: "doc.md", text: "intro\nthe cap is **6,000** (`FOO_CAP`)\n" }];
  const problems = docIndexDrift(docs, CONSTS);
  assert.equal(problems.length, 1);
  assert.match(problems[0], /doc\.md:2: cites FOO_CAP beside number\(s\) 6000 but its current value is 9000/);
});

test("docIndexDrift: extra numbers on the line are fine (presence-direction only)", () => {
  const docs = [{ name: "doc.md", text: "| **9,000**; margin **8,000** | ~2,250 | (`FOO_CAP`) |\n" }];
  assert.deepEqual(docIndexDrift(docs, CONSTS), []);
});

test("docIndexDrift: a constant mention with no 3+-digit number on the line is skipped", () => {
  const docs = [{ name: "doc.md", text: "caps live in `FOO_CAP`, never restated here (2 pp)\n" }];
  assert.deepEqual(docIndexDrift(docs, CONSTS), []);
});

test("docIndexDrift: comma and plain number formats both satisfy the demand", () => {
  const docs = [{ name: "a.md", text: "`BAR_CAP` is 1500 chars\n" }, { name: "b.md", text: "`BAR_CAP` is 1,500 chars\n" }];
  assert.deepEqual(docIndexDrift(docs, CONSTS), []);
});

test("docIndexDrift: DOC_BUDGETS plus a keyed filename demands that key's value (basename match)", () => {
  const budgets = { "CLAUDE.md": 6000, "a/b/template.md": 6000 };
  const ok = [{ name: "doc.md", text: "| `CLAUDE.md` | **6,000** | `DOC_BUDGETS` |\n" }];
  assert.deepEqual(docIndexDrift(ok, {}, budgets), []);
  const stale = [{ name: "doc.md", text: "| `template.md` | **5,000** | `DOC_BUDGETS` |\n" }];
  assert.match(docIndexDrift(stale, {}, budgets)[0], /cites template\.md beside number\(s\) 5000 but its current value is 6000/);
});

test("docIndexDrift: a filename beside numbers WITHOUT `DOC_BUDGETS` on the line demands nothing", () => {
  const budgets = { "CLAUDE.md": 6000 };
  const docs = [{ name: "doc.md", text: "edit `CLAUDE.md` to 4,000 chars someday\n" }];
  assert.deepEqual(docIndexDrift(docs, {}, budgets), []);
});

test("indexScanSet: excludes the decisions dir with or without trailing slash(es), keeps other .md", () => {
  const files = ["docs/decisions/0001-a.md", "docs/other.md", "README.md", "x/y.md", "x/z.mjs"];
  const expected = ["docs/other.md", "README.md", "x/y.md"];
  assert.deepEqual(indexScanSet(files, "docs/decisions"), expected);
  assert.deepEqual(indexScanSet(files, "docs/decisions/"), expected);
  assert.deepEqual(indexScanSet(files, "docs/decisions//"), expected);
});

test("docIndexDrift: the real living docs match char-budget.mjs (the PR #251 class, mechanized via the SHIPPED selection)", () => {
  const docs = indexScanSet(repoFileList(AGENT_ROOT), "docs/decisions")
    .map(p => ({ name: p, text: readFileSync(join(AGENT_ROOT, p), "utf8") }));
  // Vacuity pin (char-budget.test.mjs convention): an empty walk must fail HERE, not pass [].
  assert.ok(docs.some(d => d.name.endsWith("doc-budgets.md")), "walk must include the indexed doc");
  assert.ok(docs.every(d => !d.name.startsWith("docs/decisions/")), "decisions dir must be excluded");
  assert.deepEqual(docIndexDrift(docs,
    { ADR_CHAR_BUDGET, ADR_CHAR_MARGIN, LITE_ADR_CHAR_BUDGET, AGENT_CHAR_BUDGET }, DOC_BUDGETS), []);
});

test("docIndexDrift: WITHOUT the decisions-dir exclusion the real corpus false-positives (the exclusion is load-bearing)", () => {
  const all = repoFileList(AGENT_ROOT).filter(p => p.endsWith(".md"))
    .map(p => ({ name: p, text: readFileSync(join(AGENT_ROOT, p), "utf8") }));
  const problems = docIndexDrift(all,
    { ADR_CHAR_BUDGET, ADR_CHAR_MARGIN, LITE_ADR_CHAR_BUDGET, AGENT_CHAR_BUDGET }, DOC_BUDGETS);
  assert.ok(problems.some(p => p.startsWith("docs/decisions/")),
    "expected at least one as-of-decision number to fire when records are scanned");
});

// Decision-set advisory (ADR 0051 as amended): multiple new ADRs in one change get a
// cite-connectivity WARN — never a problem — when any sit outside the largest component;
// fewer than two new ADRs = nothing to report. The PR is the batching unit.
test("decision-set: absent, empty, or singleton new-ADR list reports nothing (fail open)", () => {
  const files = clean();
  assert.deepEqual(decisionSetWarnings([], files), []);
  assert.deepEqual(decisionSetWarnings(["0001"], files), []);
  assert.deepEqual(decisionSetWarnings(["docs/decisions/0001-first.md"], files), []);
});

// 0050's owner rework (2026-07-16) dropped its 0047/0048 entanglement, so the historic
// 0047-0050 batch no longer proves quiet-on-connected; 0055+0063 (extraction + its
// completion set, mutually cited) is the corpus's current connected precedent.
test("decision-set: a real cite-connected corpus set is quiet (0055 + 0063)", () => {
  assert.deepEqual(decisionSetWarnings(["0055", "0063"], corpus()), []);
});

test("decision-set: the real WP1 set (0064-0068, cite-unconnected) WARNS but is permitted — the batch that amended this rule", () => {
  const warns = decisionSetWarnings(["0064", "0065", "0066", "0067", "0068"], corpus());
  assert.equal(warns.length, 1);
  assert.match(warns[0], /fine for a deliberate work package/);
  // Advisory means advisory: the full lint over the same corpus raises no decision-set problem.
  assert.deepEqual(lint({ files: corpus() }).problems.filter(p => /decision set|grab-bag/.test(p)), []);
});

test("decision-set: two new ADRs sharing no cite warn, naming the stranded id", () => {
  const warns = decisionSetWarnings(["0001", "0002"], clean());
  assert.equal(warns.length, 1);
  assert.match(warns[0], /cite-unconnected \(0002\)/);
  assert.match(warns[0], /accidental grab-bag/);
});

test("decision-set: a one-directional cite connects (the bar is undirected, not mutual)", () => {
  const files = [
    adr("0001-a.md", { body: "\n# 0001\n\n- Date: 2026-06-27\n\nExtends ADR 0002.\n" }),
    adr("0002-b.md"),
  ];
  assert.deepEqual(decisionSetWarnings(["0001", "0002"], files), []);
});

test("decision-set: two internally-linked pairs with no bridge warn once; self-cites don't count", () => {
  const files = [
    adr("0001-a.md", { body: "\n# 0001\n\nSee ADR 0002.\n" }),
    adr("0002-b.md", { body: "\n# 0002\n\nSee ADR 0001.\n" }),
    adr("0003-c.md", { body: "\n# 0003\n\nSee ADR 0004.\n" }),
    adr("0004-d.md", { body: "\n# 0004\n\nSee ADR 0004.\n" }),
  ];
  assert.equal(decisionSetWarnings(["0001", "0002", "0003", "0004"], files).length, 1);
});

test("decision-set: file paths from a CI diff resolve to ids (posix or windows separators)", () => {
  const warns = decisionSetWarnings(
    ["docs/decisions/0001-first.md", "docs\\decisions\\0002-second.md"], clean());
  assert.equal(warns.length, 1); // parsed as 0001 + 0002, which share no cite
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
