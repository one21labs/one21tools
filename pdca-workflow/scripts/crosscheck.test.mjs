// Decision-logic tests for crosscheck.mjs (CLAUDE.md: no process script ships without one).
// The load-bearing case is verdictFor's same-family rejection — without it a foreign CLI that
// silently routes back to Claude reads as a passed cross-lineage check, which is the exact
// default-open failure ADR 0093 closes.
import { test } from "node:test";
import assert from "node:assert";
import {
  familyOf, parseGrok, parseCopilot, availableLanes, verdictFor, NO_LANE, MAKER_FAMILY,
} from "./crosscheck.mjs";

test("familyOf places every vendor the lanes can return", () => {
  assert.equal(familyOf("claude-haiku-4.5"), "anthropic");
  assert.equal(familyOf("grok-4.5-build"), "xai");
  assert.equal(familyOf("gpt-5-mini"), "openai");
  assert.equal(familyOf("gemini-3.6-flash"), "google");
  assert.equal(familyOf("kimi-k2.7-code"), "moonshot");
});

test("an unplaceable or missing model id is 'unknown', never foreign-by-default", () => {
  assert.equal(familyOf("some-internal-build-42"), "unknown");
  assert.equal(familyOf(null), "unknown");
  assert.equal(familyOf(""), "unknown");
});

test("parseGrok reads the answer and the model that produced it", () => {
  const { text, model } = parseGrok(JSON.stringify({
    text: "  the claim holds  ", stopReason: "EndTurn",
    modelUsage: { "grok-4.5-build": { inputTokens: 1 } },
  }));
  assert.equal(text, "the claim holds");
  assert.equal(model, "grok-4.5-build");
});

test("parseCopilot prefers the resolved auto model and skips non-JSON noise", () => {
  const stdout = [
    "not json at all",
    JSON.stringify({ type: "model.call_start", data: { model: "placeholder" } }),
    JSON.stringify({ type: "session.auto_mode_resolved", data: { chosenModel: "gpt-5-mini" } }),
    JSON.stringify({ type: "assistant.message", data: { content: "verdict: broken" } }),
  ].join("\n");
  const { text, model } = parseCopilot(stdout);
  assert.equal(model, "gpt-5-mini");
  assert.equal(text, "verdict: broken");
});

test("parseCopilot concatenates streamed deltas", () => {
  const stdout = [
    JSON.stringify({ type: "model.call_start", data: { model: "gpt-5-mini" } }),
    JSON.stringify({ type: "assistant.message_delta", data: { delta: "one " } }),
    JSON.stringify({ type: "assistant.message_delta", data: { delta: "two" } }),
  ].join("\n");
  assert.equal(parseCopilot(stdout).text, "one two");
});

test("a foreign CLI answering with a maker-family model is FRAME-UNCHECKED, not CHECKED", () => {
  const v = verdictFor({ lane: "copilot", model: "claude-haiku-4.5", text: "looks fine to me" });
  assert.equal(v.status, "FRAME-UNCHECKED");
  assert.equal(v.family, MAKER_FAMILY);
  assert.match(v.note, /maker's own family/);
  assert.match(v.note, /Pin a foreign model|PDCA_CROSSCHECK_CMD/);
});

test("a foreign model with an answer is CHECKED and carries the model that answered", () => {
  const v = verdictFor({ lane: "grok", model: "grok-4.5-build", text: "the second claim is false" });
  assert.equal(v.status, "CHECKED");
  assert.equal(v.model, "grok-4.5-build");
  assert.equal(v.text, "the second claim is false");
});

test("a foreign lane that returned nothing is FRAME-UNCHECKED", () => {
  assert.equal(verdictFor({ lane: "grok", model: "grok-4.5", text: "" }).status, "FRAME-UNCHECKED");
});

// Fail-closed on `unknown`. A custom lane names no model, so trusting a confident-looking answer
// from an unplaceable source would let `PDCA_CROSSCHECK_CMD='echo fine'` mint a CHECKED verdict —
// the forgery a cross-family reviewer found in the first cut of this file.
test("an answer from a model that cannot be placed is FRAME-UNCHECKED, not CHECKED", () => {
  const v = verdictFor({ lane: "custom", model: null, text: "fine" });
  assert.equal(v.status, "FRAME-UNCHECKED");
  assert.match(v.note, /PDCA_CROSSCHECK_MODEL/);
});

test("an unrecognized model id does not pass as foreign", () => {
  assert.equal(verdictFor({ lane: "custom", model: "internal-build-42", text: "looks right" }).status,
    "FRAME-UNCHECKED");
});

test("availableLanes finds a CLI via its env override even when PATH is empty", () => {
  const lanes = availableLanes({ GROK_BIN: "/opt/grok", PATH: "" }, () => null);
  assert.deepEqual(lanes.map((l) => l.name), ["grok"]);
  assert.equal(lanes[0].bin, "/opt/grok");
});

test("availableLanes finds a CLI on PATH and prefers the custom command first", () => {
  const lanes = availableLanes(
    { PDCA_CROSSCHECK_CMD: "my-llm --stdin", PATH: "/usr/bin" },
    (name) => (name === "copilot" ? "/usr/bin/copilot" : null));
  assert.deepEqual(lanes.map((l) => l.name), ["custom", "copilot"]);
});

test("no CLI anywhere yields no lanes, so the caller must report FRAME-UNCHECKED", () => {
  assert.deepEqual(availableLanes({ PATH: "", HOME: "/nonexistent" }, () => null), []);
});

test("the no-lane message names what was checked and prescribes a remedy", () => {
  assert.match(NO_LANE.note, /ADR 0093/);
  assert.match(NO_LANE.note, /GROK_BIN/);
  assert.match(NO_LANE.note, /PDCA_CROSSCHECK_CMD/);
  assert.match(NO_LANE.note, /Remedy:/);
});
