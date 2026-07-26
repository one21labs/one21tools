/*
 * char-budget.mjs — SSoT for every doc char budget + the over-budget predicate (see ADR 0008).
 * One place to look, so the caps/predicate can't drift across modules. Consumers import from
 * here: adr-lint.mjs applies ADR_CHAR_BUDGET over the ADR corpus and runs oversizeDocs() +
 * oversizeAgents() over the named docs + agent prompts. This module owns the numbers + the check;
 * domain-specific corpus walks live with their domain.
 *
 * DESIGN CONSTRAINTS:
 * - Zero dependencies, plain `.mjs` run via `node` — same constraint as adr-lint.mjs (Node is the
 *   one runtime every consumer provably has). Runs in CI / a git hook / by hand on any stack.
 * - The predicate (overBudget) is pure so its decision logic is unit-testable, per "no
 *   process-gating script without a test of its decision logic." charLen + the corpus walks
 *   (oversizeDocs, oversizeAgents) are the IO; the walks are exercised on a fixture in the test.
 * - A cap's authoritative value lives ONCE here; doc-budgets.md's table may index the numbers for
 *   navigation, never as a second source, and prose elsewhere references this file.
 *
 * SEE ALSO: ../skills/decide/references/doc-budgets.md (the altitude ladder + token table).
 * TESTING: char-budget.test.mjs (`node --test pdca-workflow/scripts/*.test.mjs` from the repo root).
 *
 * Every relative path here resolves against the CURRENT WORKING DIRECTORY (Node's default for a
 * relative fs path) — never against this file's own location. Both invokers run from their own
 * repo root already: the in-repo gate (`node pdca-workflow/scripts/adr-lint.mjs docs/decisions`,
 * per .github/workflows/gates.yml) and a vendored consumer copy (`node scripts/adr-lint.mjs`, per
 * pdca-init's SKILL.md), whose flat `scripts/` sits one level deep rather than this plugin's
 * two-levels-deep `pdca-workflow/scripts/`.
 */
import { readFileSync, readdirSync } from "node:fs";
import { join } from "node:path";

// CRLF-normalized char length, so counts are checkout-agnostic (Windows core.autocrlf=true).
export const charLen = (relPath) =>
  readFileSync(relPath, "utf8").replace(/\r\n/g, "\n").length;

// Pure decision logic (unit-tested): over the cap = a violation.
export const overBudget = (chars, cap) => chars > cap;

// The named-doc char caps (SSoT; ~3,000 chars/page — doc-budgets.md owns the altitude + token
// table). Single named files go in DOC_BUDGETS; ADRs are a glob capped by the sibling
// ADR_CHAR_BUDGET below — same file, different shape. A consumer whose detail-home doc warrants a
// larger cap (e.g. a review-system reference) adds its entry here.
export const DOC_BUDGETS = {
  "CLAUDE.md": 6000, // ~2 pp, the always-loaded layer
  // SOURCE-REPO ONLY — prune this entry when vendoring. The path exists only where the plugin is
  // developed, not where it is installed, so in a consumer checkout it is inert (the walk is
  // ENOENT-tolerant). Kept here so the scaffold can't ship over the budget it teaches
  // (#164: two under-cap PRs merge-skewed it to 6047).
  "pdca-workflow/skills/pdca-init/references/claude-md-template.md": 6000,
};

// Single-decision ADR cap. Sized with SLACK above the ~6,000 the corpus historically ran at:
// ADRs are read on-demand (not always-loaded context), so the cap exists to stop unbounded
// bloat, never to force exact-fit word-golf — iterating prose against a tight cap is muda
// (owner, 16-Jul-2026: keep caps against bloat, sized generously).
export const ADR_CHAR_BUDGET = 9000;

// Advisory drafting margin for a full ADR (adr-template.md: draft below this so the `## Act`
// block appended at ship time still fits the cap). adr-lint WARNs — never fails — when a
// PR-ADDED full ADR (--new-adrs) exceeds it (ADR 0067); the legacy corpus is not swept.
export const ADR_CHAR_MARGIN = 8000;

// Lite-tier ADR cap (`tier: lite`). RAISED 1,500 -> 2,000 (ADR 0092) to buy room for the two
// fields that actually prevent churn — rejected alternatives and reopen-if — which the old shape
// dropped. Raising a cap to shrink a corpus is not a contradiction: lite is the DEFAULT tier
// (ADR 0062), and a 2,000-char record that carries the anti-churn fields displaces a ~5,600-char
// full one that was only full because lite could not hold them.
export const LITE_ADR_CHAR_BUDGET = 2000;

// WIP cap on the WHOLE decision corpus (ADR 0092). Per-file caps bound each record but not the
// count, so the corpus grew to 428,269 chars while every file passed. Owner-set at 200,000 and
// MET by compaction (194,883 achieved, 54% cut) — not aspirational. From here growth is PAID FOR
// by compacting or superseding, never granted. The point is not inference cost (an unread record
// costs no tokens) — holding a record costs drift-maintenance, retrieval noise and triage
// forever, so the cap forces "does this earn its carrying cost?" instead of deferring it. A lite
// record spends a fraction of a full one, so the cheapest way to stay under is the tier ADR 0062
// already made the default.
export const ADR_CORPUS_BUDGET = 200000;

// Agent prompt files (pdca-workflow/agents/*.md) — a lean-prompt guard (ADR 0009); a glob capped by
// this sibling budget, same shape as the ADR corpus. Slack above the ~3,000 the prompts run at,
// for the same no-word-golf reason as the ADR cap.
export const AGENT_CHAR_BUDGET = 3500;

// Shared per-file check — one loop body, so the "path:chars/cap" report format cannot diverge
// between the doc and agent walks. ENOENT-tolerant like the directory walks below: a budgeted doc
// that doesn't exist (e.g. no CLAUDE.md yet) has nothing to over-budget-check, so it's skipped, not
// a crash.
const pushIfOver = (relPath, cap, out) => {
  let n;
  try { n = charLen(relPath); }
  catch (e) { if (e.code === "ENOENT") return; throw e; }
  if (overBudget(n, cap)) out.push(`${relPath}:${n}/${cap}`);
};

// Guard: no budgeted doc exceeds its cap. Returns "path:chars/cap" per violation.
export function oversizeDocs() {
  const out = [];
  for (const [path, cap] of Object.entries(DOC_BUDGETS)) pushIfOver(path, cap, out);
  return out;
}

// Guard: no agent prompt in `dir` (CWD-relative) exceeds AGENT_CHAR_BUDGET. An ABSENT dir is
// tolerated — a consumer may have no agents — but ONLY ENOENT: any other readdir failure throws,
// so the gate cannot go silently vacuous. `dir` is injectable so the test can prove positive
// detection on a fixture. Returns "path:chars/cap" per violation.
export function oversizeAgents(dir = "pdca-workflow/agents") {
  const out = [];
  let names;
  try { names = readdirSync(dir); }
  catch (e) { if (e.code === "ENOENT") return out; throw e; }
  for (const f of names.filter((f) => f.endsWith(".md"))) pushIfOver(`${dir}/${f}`, AGENT_CHAR_BUDGET, out);
  return out;
}

// Guard: each agent prompt's frontmatter `name:` matches its filename (mirrors adr-lint's
// id-matches-filename check — so a renamed or malformed advisor a Panel: line refers to cannot
// silently drift). Every caller passes dir explicitly (no default), ENOENT-tolerant like
// oversizeAgents. One message per mismatch.
export function agentNameMismatches(dir) {
  const out = [];
  let names;
  try { names = readdirSync(dir); }
  catch (e) { if (e.code === "ENOENT") return out; throw e; }
  for (const f of names.filter((f) => f.endsWith(".md"))) {
    const fm = readFileSync(join(dir, f), "utf8").match(/^---\n([\s\S]*?)\n---/);
    const nameLine = fm && fm[1].match(/^name:\s*(.*)$/m);
    const name = nameLine ? nameLine[1].trim() : null;
    const expected = f.replace(/\.md$/, "");
    if (name !== expected) out.push(`${dir}/${f}: name '${name ?? "(none)"}' != '${expected}'`);
  }
  return out;
}

/**
 * Corpus WIP cap (ADR 0092). PURE over `sizes` (an array of per-record char counts) so the
 * decision logic is testable without a corpus on disk. Returns null when under, else the
 * overage plus what it costs in records — the remedy is compaction, never "drop the record you
 * are adding", so the message names the trade rather than the violation.
 */
export function corpusOverage(sizes, cap = ADR_CORPUS_BUDGET) {
  const total = sizes.reduce((a, b) => a + b, 0);
  if (total <= cap) return null;
  const over = total - cap;
  return { total, cap, over,
    remedy: `compact or supersede ~${over} chars (about ${Math.ceil(over / LITE_ADR_CHAR_BUDGET)} lite-record equivalents) before adding — a corpus is inventory, and this cap makes the carrying cost payable instead of deferred` };
}
