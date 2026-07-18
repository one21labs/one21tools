/*
 * check-references.test.mjs — proves check-references' decision logic (ADR 0079: the
 * reference-veracity write-time gate). Run: node --test scripts/*.test.mjs from the repo root.
 */
import { test } from "node:test";
import assert from "node:assert/strict";
import { checkReferences } from "./check-references.mjs";

const changed = (...f) => f;

test("fires: URL added to a tracked corpus file with no audit-record touch", () => {
  const { problems } = checkReferences({
    addedByFile: { "docs/research/loop-engineering.md": ["| Foo (2026) | bar | https://example.com/post |"] },
    changedFiles: changed("docs/research/loop-engineering.md"),
  });
  assert.equal(problems.length, 1);
  assert.match(problems[0], /adds 1 external reference line\(s\)/);
});

test("clean: same addition WITH a sources/*reference-audit* touch in the change", () => {
  const { problems } = checkReferences({
    addedByFile: { "docs/research/loop-engineering.md": ["https://example.com/post"] },
    changedFiles: changed("docs/research/loop-engineering.md", "docs/research/sources/2026-07-19-reference-audit.md"),
  });
  assert.deepEqual(problems, []);
});

test("fires on arXiv ids and bare domains with a path, in docs/decisions too", () => {
  const { problems } = checkReferences({
    addedByFile: { "docs/decisions/0080-x.md": ["- grounded in arXiv:2607.14890", "- see anthropic.com/engineering/harness-design"] },
    changedFiles: changed("docs/decisions/0080-x.md"),
  });
  assert.equal(problems.length, 1);
  assert.match(problems[0], /adds 2 external reference line\(s\)/);
});

test("not a trigger: raw lane files under sources/ are the audit substrate, not citations", () => {
  const { problems } = checkReferences({
    addedByFile: { "docs/research/sources/2026-07-19-grok-lane.md": ["https://example.com/one", "https://example.com/two"] },
    changedFiles: changed("docs/research/sources/2026-07-19-grok-lane.md"),
  });
  assert.deepEqual(problems, []);
});

test("not external: repo-relative paths, file:line cites, script names, own-repo github links", () => {
  const { problems } = checkReferences({
    addedByFile: { "docs/decisions/0080-x.md": [
      "- see metrics-engine.md:28 and scripts/scorecard.mjs",
      "- per pdca-workflow/skills/decide/references/adr-template.md",
      "- merged in https://github.com/one21labs/one21tools/pull/242",
    ] },
    changedFiles: changed("docs/decisions/0080-x.md"),
  });
  assert.deepEqual(problems, []);
});

test("untracked paths (README, benchmarks, skills) never trigger", () => {
  const { problems } = checkReferences({
    addedByFile: {
      "README.md": ["https://example.com"],
      "benchmarks/2026-07-19-x/README.md": ["https://example.com"],
      "skills/foo/SKILL.md": ["arXiv:2602.12670"],
    },
    changedFiles: changed("README.md", "benchmarks/2026-07-19-x/README.md", "skills/foo/SKILL.md"),
  });
  assert.deepEqual(problems, []);
});

test("empty diff -> clean", () => {
  assert.deepEqual(checkReferences({ addedByFile: {}, changedFiles: [] }).problems, []);
});
