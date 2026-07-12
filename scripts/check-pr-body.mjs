#!/usr/bin/env node
/*
 * check-pr-body.mjs — gate, two PR-description checks:
 * - ADR 0030: the body must record the pre-PR retrospect outcome as a line
 *   `Retrospective: run | unavailable | skipped-<reason>`. Checks PRESENCE of a well-formed
 *   line, NOT truth (no script can confirm a retrospect ran without re-running it — truth stays
 *   self-attested per ADR 0030).
 * - ADR 0054: the title must not close an issue the body declares `Partial: #NNN` — a
 *   closing-keyword title becomes the squash-commit subject on main and auto-closes the issue.
 *   Only the decidable contradiction denies; a closing title with a silent body PASSes
 *   (undecidable intent — ADR 0047 precondition ii).
 * The predicates (hasRetroLine, titleClosesDeclaredPartial) are pure and unit-tested
 * (check-pr-body.test.mjs); reading env + exit is the thin IO wrapper. Zero-dependency .mjs,
 * same constraint as the sibling gate scripts (adr-lint, check-workflow).
 *
 * Usage (gates.yml, pull_request only): PR_BODY + PR_TITLE set from the event, then
 * node scripts/check-pr-body.mjs
 * TESTING: node --test scripts/*.test.mjs
 */
import { fileURLToPath } from "node:url";

// Anchored to its own line: `Retrospective:` then run | unavailable | skipped-<non-space reason>,
// the value ending at whitespace or line end. Forgiving of a trailing comment after the value
// (`run (batch #40)`); rejects a prose mid-line mention, bare `skipped` (no reason), and `running`.
const RETRO_LINE = /^Retrospective:[ \t]*(run|unavailable|skipped-\S+)(?=\s|$)/m;

export const hasRetroLine = (body) => RETRO_LINE.test(body ?? "");

// GitHub's closing-keyword grammar (ADR 0054): `fix #12`, `Closes #34`, ... in the PR title.
const CLOSING_REF = /\b(close|closes|closed|fix|fixes|fixed|resolve|resolves|resolved)\s+#(\d+)/gi;
// Anchored to its own body line: `Partial: #NNN` = this PR does NOT fully close issue NNN.
const PARTIAL_LINE = /^Partial:[ \t]*#(\d+)(?=\s|$)/gm;

// Issue numbers the title claims to close that the body declares partial — the decidable
// contradiction ADR 0054 denies. Everything else (silent body, consistent declarations) passes.
export const titleClosesDeclaredPartial = (title, body) => {
  const titleCloses = new Set([...(title ?? "").matchAll(CLOSING_REF)].map((m) => m[2]));
  const bodyPartials = new Set([...(body ?? "").matchAll(PARTIAL_LINE)].map((m) => m[1]));
  return [...titleCloses].filter((n) => bodyPartials.has(n));
};

function main() {
  const problems = [];
  if (!hasRetroLine(process.env.PR_BODY)) {
    problems.push(
      "PR body is missing a `Retrospective: run | unavailable | skipped-<reason>` " +
      "line (ADR 0030). Add it to the PR description and re-run.",
    );
  }
  for (const n of titleClosesDeclaredPartial(process.env.PR_TITLE, process.env.PR_BODY)) {
    problems.push(
      `PR title closes #${n} but the body declares \`Partial: #${n}\` (ADR 0054). On squash-merge ` +
      `the title becomes the commit subject and auto-closes #${n} — reword the title (e.g. ` +
      `\`re #${n}\`) or drop the Partial line if the PR truly completes it.`,
    );
  }
  if (problems.length) {
    for (const p of problems) console.error(`check-pr-body: ${p}`);
    process.exit(1);
  }
  console.log("check-pr-body: Retrospective line present; no title/Partial contradiction.");
}

if (process.argv[1] === fileURLToPath(import.meta.url)) main();
