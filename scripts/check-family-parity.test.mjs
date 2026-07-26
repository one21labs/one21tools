// Cross-copy parity: pdca-workflow/scripts/crosscheck.mjs (JS) and
// skill-bench/scripts/lib/judge.py (Python) each carry a vendor-family table and a copilot JSONL
// parser. That duplication is STRUCTURAL, not debt — ADR 0050 forbids content dependencies between
// plugins, so neither may import the other, and the two are written in different languages. What
// the duplication does risk is silent divergence: a vendor pattern added on one side only, or a
// copilot event-schema change fixed in one file, would leave the other quietly mis-classifying a
// grader's family. That is the failure this file catches.
//
// Repo-instance tooling, deliberately NOT shipped with either plugin (same posture as
// check-restatement.mjs): it encodes the fact that this repo happens to host both copies.
// Behavioural comparison, not source parsing — the two implementations only have to AGREE.
// Muda-review finding on PR #298.
import { test } from "node:test";
import assert from "node:assert";
import { execFileSync } from "node:child_process";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";
import { familyOf, parseCopilot } from "../pdca-workflow/scripts/crosscheck.mjs";

const ROOT = join(dirname(fileURLToPath(import.meta.url)), "..");
const LIB = join(ROOT, "skill-bench", "scripts", "lib");

// Spans every family both tables claim, plus the cases that must NOT resolve to a vendor. EVERY
// alternative in either table needs its own id here: the first cut of this list exercised only the
// common branches, so the tables could differ on `\bo[0-9]` and bare `google` while the guard read
// green (muda-review, PR #298). A parity test that never reaches a branch does not guard it.
const MODEL_IDS = [
  "claude-haiku-4.5", "claude-opus-5", "anthropic/claude", "grok-4.5", "grok-4.5-build", "xai-1",
  "gpt-5-mini", "gpt-5.4", "openai-next", "o1-mini", "o3", "gemini-3.6-flash", "google-palm-2",
  "kimi-k2.7-code", "moonshot-v1", "house-model-7", "",
];

function pythonFamilies(ids) {
  const src = `import sys, json; sys.path.insert(0, ${JSON.stringify(LIB)}); import judge; `
    + `print(json.dumps([judge.family_of(i) for i in json.loads(sys.argv[1])]))`;
  return JSON.parse(execFileSync("python3", ["-c", src, JSON.stringify(ids)], { encoding: "utf8" }));
}

test("both plugins place every model id in the same vendor family", () => {
  const js = MODEL_IDS.map((id) => familyOf(id));
  assert.deepEqual(js, pythonFamilies(MODEL_IDS),
    "crosscheck.mjs and judge.py disagree on a vendor family — update BOTH tables");
});

test("an unplaceable id is 'unknown' on both sides, never a foreign family", () => {
  // The load-bearing agreement: 'unknown' is what makes both implementations fail closed.
  assert.equal(familyOf("house-model-7"), "unknown");
  assert.deepEqual(pythonFamilies(["house-model-7", ""]), ["unknown", "unknown"]);
});

test("both plugins read the same answer and model out of a copilot event stream", () => {
  const stdout = [
    "not json",
    JSON.stringify({ type: "model.call_start", data: { model: "placeholder" } }),
    JSON.stringify({ type: "session.auto_mode_resolved", data: { chosenModel: "gpt-5-mini" } }),
    JSON.stringify({ type: "assistant.message", data: { content: "the verdict" } }),
  ].join("\n");
  const js = parseCopilot(stdout);
  const src = `import sys, json; sys.path.insert(0, ${JSON.stringify(LIB)}); import judge; `
    + `t, m = judge.parse_copilot_jsonl(sys.argv[1]); print(json.dumps({"text": t, "model": m}))`;
  const py = JSON.parse(execFileSync("python3", ["-c", src, stdout], { encoding: "utf8" }));
  assert.deepEqual({ text: js.text, model: js.model }, py,
    "the copilot JSONL parsers have diverged — update BOTH");
});
