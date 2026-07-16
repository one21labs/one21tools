#!/usr/bin/env node
/*
 * check-pr-body.mjs — gate, one PR-description check:
 * - ADR 0054: the title must not close an issue the body declares `Partial: #NNN` — a
 *   closing-keyword title becomes the squash-commit subject on main and auto-closes the issue.
 *   Only the decidable contradiction denies; a closing title with a silent body PASSes
 *   (undecidable intent — ADR 0047 precondition ii).
 * The predicate (titleClosesDeclaredPartial) is pure and unit-tested (check-pr-body.test.mjs);
 * reading env + exit is the thin IO wrapper. Zero-dependency .mjs, same constraint as the
 * sibling gate scripts (adr-lint, check-workflow).
 *
 * Usage (gates.yml, pull_request only): PR_BODY + PR_TITLE set from the event, then
 * node scripts/check-pr-body.mjs
 * TESTING: node --test scripts/*.test.mjs
 */
import { fileURLToPath } from "node:url";

// GitHub's closing-keyword grammar (ADR 0054): keyword, optional colon, then #NNN —
// `fix #12`, `Fixes: #34`, `Closes:#10` all close; no separator at all (`Fixes#164`) does not.
const CLOSING_REF = /\b(close|closes|closed|fix|fixes|fixed|resolve|resolves|resolved)(?:\s*:\s*|\s+)#(\d+)/gi;

// Strip fenced code + HTML comments so a `Partial:` inside an example never denies (ADR 0054).
const stripFences = (s) =>
  (s ?? "")
    .replace(/```[\s\S]*?```/g, "")
    .replace(/~~~[\s\S]*?~~~/g, "")
    .replace(/<!--[\s\S]*?-->/g, "");

// A body line beginning `Partial:` (case-insensitive) declares every #NNN in its remainder —
// `Partial: #NNN` = this PR does NOT fully close issue NNN. Tolerant of comma lists, trailing
// punctuation, and case.
const PARTIAL_LINE = /^partial:(.*)$/gim;
const partialsFrom = (body) => {
  const nums = new Set();
  for (const line of stripFences(body).matchAll(PARTIAL_LINE))
    for (const r of line[1].matchAll(/#(\d+)/g)) nums.add(r[1]);
  return nums;
};

// Issue numbers the title claims to close that the body declares partial — the decidable
// contradiction ADR 0054 denies. Everything else (silent body, consistent declarations) passes.
export const titleClosesDeclaredPartial = (title, body) => {
  const titleCloses = new Set([...(title ?? "").matchAll(CLOSING_REF)].map((m) => m[2]));
  const bodyPartials = partialsFrom(body);
  return [...titleCloses].filter((n) => bodyPartials.has(n));
};

function main() {
  const problems = [];
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
  console.log("check-pr-body: no title/Partial contradiction.");
}

if (process.argv[1] === fileURLToPath(import.meta.url)) main();
