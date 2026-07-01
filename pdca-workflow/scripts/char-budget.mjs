/*
 * char-budget.mjs — SSoT for every doc char budget + the over-budget predicate (see ADR 0008).
 * One place to look, so the caps/predicate can't drift across modules. Consumers import from
 * here: adr-lint.mjs applies ADR_CHAR_BUDGET over the ADR corpus and runs oversizeDocs() over the
 * named docs. This module owns the numbers + the check; domain-specific corpus walks live with
 * their domain.
 *
 * DESIGN CONSTRAINTS:
 * - Zero dependencies, plain `.mjs` run via `node` — same constraint as adr-lint.mjs (Node is the
 *   one runtime every consumer provably has). Runs in CI / a git hook / by hand on any stack.
 * - The predicate (overBudget) is pure so its decision logic is unit-testable, per "no
 *   process-gating script without a test of its decision logic." charLen / oversizeDocs are the IO.
 * - A literal cap number lives ONCE here; doc prose references this file, never re-states the int.
 *
 * SEE ALSO: ../skills/decide/references/doc-budgets.md (the altitude ladder + token table).
 * TESTING: char-budget.test.mjs (`node --test "scripts/*.test.mjs"`).
 */
import { readFileSync } from "node:fs";
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

// Guard: no budgeted doc exceeds its cap. Returns "path:chars/cap" per violation.
export function oversizeDocs() {
  const out = [];
  for (const [path, cap] of Object.entries(DOC_BUDGETS)) {
    const n = charLen(path);
    if (overBudget(n, cap)) out.push(`${path}:${n}/${cap}`);
  }
  return out;
}
