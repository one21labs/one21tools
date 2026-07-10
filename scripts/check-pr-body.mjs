#!/usr/bin/env node
/*
 * check-pr-body.mjs — gate (ADR 0030): a PR body must record the pre-PR retrospect outcome as a
 * line `Retrospective: run | unavailable | skipped-<reason>`. Checks PRESENCE of a well-formed
 * line, NOT truth (no script can confirm a retrospect ran without re-running it — truth stays
 * self-attested per ADR 0030). The predicate (hasRetroLine) is pure and unit-tested
 * (check-pr-body.test.mjs); reading env + exit is the thin IO wrapper. Zero-dependency .mjs,
 * same constraint as the sibling gate scripts (adr-lint, check-workflow).
 *
 * Usage (gates.yml, pull_request only): PR_BODY set from the event, then node scripts/check-pr-body.mjs
 * TESTING: node --test scripts/*.test.mjs
 */
import { fileURLToPath } from "node:url";

// Anchored to its own line: `Retrospective:` then run | unavailable | skipped-<non-space reason>,
// the value ending at whitespace or line end. Forgiving of a trailing comment after the value
// (`run (batch #40)`); rejects a prose mid-line mention, bare `skipped` (no reason), and `running`.
const RETRO_LINE = /^Retrospective:[ \t]*(run|unavailable|skipped-\S+)(?=\s|$)/m;

export const hasRetroLine = (body) => RETRO_LINE.test(body ?? "");

function main() {
  if (!hasRetroLine(process.env.PR_BODY)) {
    console.error(
      "check-pr-body: PR body is missing a `Retrospective: run | unavailable | skipped-<reason>` " +
      "line (ADR 0030). Add it to the PR description and re-run.",
    );
    process.exit(1);
  }
  console.log("check-pr-body: Retrospective line present.");
}

if (process.argv[1] === fileURLToPath(import.meta.url)) main();
