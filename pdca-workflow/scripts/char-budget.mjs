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
 * TESTING: char-budget.test.mjs (`node --test "scripts/*.test.mjs"`).
 */
import { readFileSync, readdirSync } from "node:fs";
import { join } from "node:path";
import { fileURLToPath } from "node:url";

// Repo root (this file lives at <root>/pdca-workflow/scripts/).
const ROOT = fileURLToPath(new URL("../../", import.meta.url));

// CRLF-normalized char length, so counts are checkout-agnostic (Windows core.autocrlf=true).
export const charLen = (relPath) =>
  readFileSync(join(ROOT, relPath), "utf8").replace(/\r\n/g, "\n").length;

// Pure decision logic (unit-tested): over the cap = a violation.
export const overBudget = (chars, cap) => chars > cap;

// The named-doc char caps (SSoT; ~3,000 chars/page — doc-budgets.md owns the altitude + token
// table). Single named files go in DOC_BUDGETS; ADRs are a glob capped by the sibling
// ADR_CHAR_BUDGET below — same file, different shape. A consumer whose detail-home doc warrants a
// larger cap (e.g. a review-system reference) adds its entry here.
export const DOC_BUDGETS = {
  "CLAUDE.md": 6000, // ~2 pp, the always-loaded layer
};

// Single-decision ADR norm (~2 pp). No exemptions — every ADR is held to the cap (ADR 0008 chose
// rewrite-under-budget over a grandfather allowlist for this small corpus).
export const ADR_CHAR_BUDGET = 6000;

// Agent prompt files (pdca-workflow/agents/*.md) — a lean-prompt guard (ADR 0009); a glob capped by
// this sibling budget, same shape as the ADR corpus.
export const AGENT_CHAR_BUDGET = 3000;

// Shared per-file check — one loop body, so the "path:chars/cap" report format cannot diverge
// between the doc and agent walks.
const pushIfOver = (relPath, cap, out) => {
  const n = charLen(relPath);
  if (overBudget(n, cap)) out.push(`${relPath}:${n}/${cap}`);
};

// Guard: no budgeted doc exceeds its cap. Returns "path:chars/cap" per violation.
export function oversizeDocs() {
  const out = [];
  for (const [path, cap] of Object.entries(DOC_BUDGETS)) pushIfOver(path, cap, out);
  return out;
}

// Guard: no agent prompt in `dir` (ROOT-relative) exceeds AGENT_CHAR_BUDGET. An ABSENT dir is
// tolerated — a consumer may have no agents — but ONLY ENOENT: any other readdir failure throws,
// so the gate cannot go silently vacuous. `dir` is injectable so the test can prove positive
// detection on a fixture. Returns "path:chars/cap" per violation.
export function oversizeAgents(dir = "pdca-workflow/agents") {
  const out = [];
  let names;
  try { names = readdirSync(join(ROOT, dir)); }
  catch (e) { if (e.code === "ENOENT") return out; throw e; }
  for (const f of names.filter((f) => f.endsWith(".md"))) pushIfOver(`${dir}/${f}`, AGENT_CHAR_BUDGET, out);
  return out;
}
