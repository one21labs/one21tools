/*
 * check-restatement.test.mjs — decision-logic test for check-restatement.mjs (ADR 0046; "no
 * process-gating script without a test of its decision logic"). Pins: a >=window shared word
 * span across two files is flagged; below-window, fenced-code, frontmatter, and ADR-metadata
 * duplication is not; allowlisted pairs are excluded; and the deployed gate passes on the
 * repo itself — the surface a consumer invokes (gates.yml).
 */
import { test } from "node:test";
import assert from "node:assert/strict";
import { spawnSync } from "node:child_process";
import { fileURLToPath } from "node:url";
import { detect, allowed, WINDOW } from "./check-restatement.mjs";

const SPAN = "the quick brown fox jumps over the lazy dog again and again today"; // 13 words
// Seed goes LAST, immediately before any appended payload — the differing word breaks the
// shared run at the boundary so filler text never merges into an adjacent pinned span.
const filler = (seed) => `\nunrelated prose that shares nothing with its sibling text block ${seed}.\n`;

test("a shared span at/above the window is flagged with both locations", () => {
  const spans = detect([
    { name: "a.md", text: `# A${filler("alpha")}${SPAN}\n` },
    { name: "b.md", text: `# B${filler("beta")}${SPAN}\n` },
  ]);
  assert.equal(spans.length, 1);
  assert.ok(spans[0].words >= WINDOW);
  assert.match(spans[0].a + spans[0].b, /a\.md:\d+/);
  assert.match(spans[0].a + spans[0].b, /b\.md:\d+/);
});

test("a shared run below the window is not flagged", () => {
  const short = SPAN.split(" ").slice(0, WINDOW - 1).join(" ");
  const spans = detect([
    { name: "a.md", text: `${filler("alpha")}${short}\n` },
    { name: "b.md", text: `${filler("beta")}${short}\n` },
  ]);
  assert.deepEqual(spans, []);
});

test("identical fenced code blocks are not flagged (commands legitimately repeat)", () => {
  const code = "```bash\n" + SPAN + "\n" + SPAN + "\n```\n";
  const spans = detect([
    { name: "a.md", text: `${filler("alpha")}${code}` },
    { name: "b.md", text: `${filler("beta")}${code}` },
  ]);
  assert.deepEqual(spans, []);
});

test("identical YAML frontmatter and ADR metadata field lines are not flagged", () => {
  const fm = "---\nid: 0001\ntitle: same title words repeated for everyone here\n---\n";
  const meta = "- Date: 2026-07-10\n- Owner: PM\n- Panel: lean-process-engineer, process-economist, session-operator, plugin-adopter over and over\n";
  const spans = detect([
    { name: "docs/decisions/0001-a.md", text: fm + meta + filler("alpha") },
    { name: "docs/decisions/0002-b.md", text: fm + meta + filler("beta") },
  ]);
  assert.deepEqual(spans, []);
});

test("an allowlisted pair is excluded; the same span elsewhere is not", () => {
  const files = [
    { name: ".claude/agents/one.md", text: filler("alpha") + SPAN },
    { name: ".claude/agents/two.md", text: filler("beta") + SPAN },
    { name: "docs/other.md", text: filler("gamma") + SPAN },
  ];
  const spans = detect(files);
  // agents<->agents allowlisted; agents<->docs/other.md is NOT.
  assert.ok(spans.length === 2);
  assert.ok(spans.every(s => s.pair.includes("docs/other.md")));
  assert.ok(allowed(".claude/agents/one.md", ".claude/agents/two.md"));
  assert.ok(!allowed(".claude/agents/one.md", "docs/other.md"));
});

test("recall regression: a real #88-class verbatim restatement is caught", () => {
  // The pre-cleanup corpus's duplicated evals-protocol sentence (issue #88, Cleanup A).
  const real = "a fresh claude b writes the expectations not the skill's author an author grades their own intent a fresh instance grades the artifact";
  const spans = detect([
    { name: "skills/x/references/evaluation-patterns.md", text: filler("alpha") + real },
    { name: "skills/x/references/empirical-evals.md", text: filler("beta") + real },
  ]);
  assert.equal(spans.length, 1);
});

test("surface: the deployed gate passes on the repo itself", () => {
  const script = fileURLToPath(new URL("./check-restatement.mjs", import.meta.url));
  const root = fileURLToPath(new URL("..", import.meta.url));
  const r = spawnSync(process.execPath, [script, root], { encoding: "utf8" });
  assert.equal(r.status, 0, r.stdout + r.stderr);
  assert.match(r.stdout, /no cross-file restatement/);
});
