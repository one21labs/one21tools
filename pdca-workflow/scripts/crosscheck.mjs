#!/usr/bin/env node
// crosscheck.mjs — route a claim OUT of the maker's lineage (ADR 0093).
//
// `/verify` and `/red-team` refuse a claim about the Check loop itself: a spawned subagent is the
// maker's lineage by construction, so it cannot settle one. This script is the route they take
// instead. It resolves whichever foreign-vendor CLI this machine actually has, sends the claim,
// and reports which model answered. FRAME-UNCHECKED is then what comes back when no lane EXISTS —
// not what comes back because nobody looked.
//
// DESIGN DIRECTION — repo owner, 26-Jul-2026: "review that failure to converge and let's resolve
// it before we move on." Two cross-family reviewers had independently found that FRAME-UNCHECKED
// records a gap without holding it; the prior round closed that as out of scope rather than
// fixing it. The owner rejected that disposition. This script, the lineage check, and the
// adr-lint rung that requires the probe are Claude's implementation of that call. The per-call
// lineage check below is Claude's own idea rather than a requirement passed down (ADR 0085 marks
// both directions): it came out of measuring copilot's router, not from the brief.
//
// Lineage is verified per call, never assumed. A lane that cannot pin a model can answer from the
// maker's own family without saying so: github copilot's `auto` mode lists `claude-haiku-4.5`
// among its own candidates (`session.auto_mode_resolved`, measured 26-Jul-2026), and an unnoticed
// same-family answer is the precise failure ADR 0093 exists to close. So a foreign CLI that
// returns a Claude model is FRAME-UNCHECKED, exactly as if it were absent.
import { execFileSync } from "node:child_process";
import { existsSync, mkdtempSync, readFileSync, writeFileSync, rmSync } from "node:fs";
import { tmpdir } from "node:os";
import { join, delimiter } from "node:path";

/** Pure: the lineage this plugin runs inside. `$PDCA_MAKER_FAMILY` is a real override, not a
 *  comment — an adopter driving these skills from another vendor's host inverts which family is
 *  "the maker", and without the override this plugin would be Claude-shaped by construction. Must
 *  stay in step with judge.py's GENERATOR_FAMILY (scripts/check-family-parity.test.mjs). */
export function makerFamily(env = process.env) {
  return env.PDCA_MAKER_FAMILY || "anthropic";
}

export const MAKER_FAMILY = makerFamily();

// TWIN: skill-bench/scripts/lib/judge.py carries this table and parseCopilot's logic in Python.
// Neither may import the other (ADR 0050: plugins ship standalone, no content dependencies), so
// the copies are structural — change one, change both. scripts/check-family-parity.test.mjs fails
// the build if they drift.
const FAMILY_PATTERNS = [
  [/claude|anthropic/i, "anthropic"],
  [/grok|xai/i, "xai"],
  [/gpt|openai|\bo[0-9]/i, "openai"],
  [/gemini|google/i, "google"],
  [/kimi|moonshot/i, "moonshot"],
];

/** Pure: which vendor family a model id belongs to. Unrecognized ids are "unknown" — which is
 *  NOT treated as foreign, because an id we cannot place is an id we cannot vouch for. */
export function familyOf(modelId) {
  if (!modelId) return "unknown";
  for (const [re, fam] of FAMILY_PATTERNS) if (re.test(modelId)) return fam;
  return "unknown";
}

/** Pure given `pathEnv`: first executable named `name` on PATH, else null. */
export function whichSync(name, pathEnv = process.env.PATH ?? "") {
  for (const dir of pathEnv.split(delimiter)) {
    if (!dir) continue;
    const p = join(dir, name);
    if (existsSync(p)) return p;
  }
  return null;
}

// Each lane: how to find its binary, how to invoke it, how to read back (text, model) from stdout.
// `envBin` exists for every lane because a CLI installed outside PATH is the common case (this
// machine's copilot lives under the VS Code server's globalStorage, not in /usr/local/bin).
export const LANES = [
  {
    name: "grok",
    envBin: "GROK_BIN",
    fallbacks: ["~/.grok/bin/grok"],
    // READ stays allowed on purpose. skill-bench's judge denies it because grading must be
    // hermetic; a cross-lineage CHECK is the opposite job — a foreign model that cannot open the
    // files is reduced to rhetoric about a claim blob, which is the appearance of a check rather
    // than one. Writes and shell stay denied: it inspects, it does not act.
    args: (file) => ["--prompt-file", file, "--output-format", "json",
      "--disallowed-tools", "Bash,Write,Edit"],
    parse: parseGrok,
  },
  {
    name: "copilot",
    envBin: "COPILOT_BIN",
    fallbacks: [],
    // JSONL rather than -s: the event stream is the only place the ANSWERING model is named, and
    // without that this lane cannot prove it left the maker's family.
    // Same stance as grok's: read to inspect, never act. Non-interactive mode needs
    // --allow-all-tools, so the acting tools are denied back off individually.
    args: (file, promptText) => ["-p", promptText, "--output-format", "json", "--allow-all-tools",
      "--deny-tool=shell", "--deny-tool=write", "--deny-tool=edit"],
    parse: parseCopilot,
  },
];

/** Pure: grok's single-envelope stdout -> {text, model}. */
export function parseGrok(stdout) {
  const env = JSON.parse(stdout);
  const model = Object.keys(env.modelUsage ?? {})[0] ?? null;
  return { text: (env.text ?? "").trim(), model };
}

/** Pure: copilot's JSONL event stream -> {text, model}. The model comes from whichever event
 *  names it (`auto` resolution or the model call itself); the text is the assistant's message. */
export function parseCopilot(stdout) {
  let model = null;
  const chunks = [];
  for (const line of stdout.split("\n")) {
    const s = line.trim();
    if (!s.startsWith("{")) continue;
    let ev;
    try { ev = JSON.parse(s); } catch { continue; }
    const d = ev.data ?? {};
    if (d.chosenModel) model = d.chosenModel;
    else if (d.model && !model) model = d.model;
    if (ev.type === "assistant.message" && typeof d.content === "string") chunks.push(d.content);
    else if (ev.type === "assistant.message_delta" && typeof d.delta === "string") chunks.push(d.delta);
  }
  return { text: chunks.join("").trim(), model };
}

/** Pure given `env` + `which`: the lanes usable on this machine, in preference order. A lane whose
 *  binary is absent is simply not listed — the caller distinguishes "no lane" from "same family". */
export function availableLanes(env = process.env, which = whichSync) {
  const out = [];
  if (env.PDCA_CROSSCHECK_CMD) {
    // The vendor-agnostic escape: any command reading the claim on stdin. An adopter whose foreign
    // model is behind a local server or an in-house wrapper wires it here rather than waiting for
    // a backend to ship.
    out.push({ name: "custom", bin: env.PDCA_CROSSCHECK_CMD, custom: true });
  }
  for (const lane of LANES) {
    const bin = env[lane.envBin]
      || which(lane.name, env.PATH ?? "")
      || lane.fallbacks.map((f) => f.replace("~", env.HOME ?? "")).find((f) => existsSync(f));
    if (bin) out.push({ ...lane, bin });
  }
  return out;
}

/** Pure: turn a lane's answer into the verdict the skills consume. CHECKED requires a POSITIVELY
 *  identified foreign family — an unplaceable or absent model id fails closed, because "the answer
 *  came from somewhere I cannot name" is not evidence the lineage was left. (Failing open on
 *  `unknown` would let `PDCA_CROSSCHECK_CMD='echo fine'` mint a CHECKED verdict.) */
export function verdictFor({ lane, model, text }) {
  const family = familyOf(model);
  if (family === MAKER_FAMILY) {
    return {
      status: "FRAME-UNCHECKED", lane, model, family,
      note: `${lane} answered with ${model}, which is the maker's own family (${MAKER_FAMILY}); `
        + `the claim did not leave the lineage. Pin a foreign model on that CLI, or set `
        + `$PDCA_CROSSCHECK_CMD to a checker you can pin.`,
    };
  }
  if (family === "unknown") {
    return {
      status: "FRAME-UNCHECKED", lane, model, family,
      note: `${lane} answered but named no model this script can place (${model ?? "no model id"}), `
        + `so the answer cannot be shown to come from outside ${MAKER_FAMILY}. Set `
        + `$PDCA_CROSSCHECK_MODEL to the model id your lane actually uses.`,
    };
  }
  if (!text) {
    return { status: "FRAME-UNCHECKED", lane, model, family, note: `${lane} returned no answer.` };
  }
  return { status: "CHECKED", lane, model, family, text };
}

export const NO_LANE = {
  status: "FRAME-UNCHECKED", lane: null, model: null, family: null,
  note: "No cross-lineage checker is reachable on this machine (ADR 0093). Checked for: "
    + "$PDCA_CROSSCHECK_CMD, grok (PATH or $GROK_BIN), copilot (PATH or $COPILOT_BIN). "
    + "Remedy: install one of those CLIs, or point $PDCA_CROSSCHECK_CMD at any command that "
    + "reads the claim on stdin and answers on stdout — an in-house wrapper or a local model "
    + "server both qualify. Until then this claim class goes unchecked, which is the honest "
    + "result, not a passing one.",
};

function runLane(lane, claim, timeoutMs) {
  if (lane.custom) {
    return { text: execFileSync("sh", ["-c", lane.bin], { input: claim, encoding: "utf8", timeout: timeoutMs }).trim(),
      model: process.env.PDCA_CROSSCHECK_MODEL ?? null };
  }
  const dir = mkdtempSync(join(tmpdir(), "crosscheck-"));
  const file = join(dir, "claim.txt");
  writeFileSync(file, claim);
  try {
    const stdout = execFileSync(lane.bin, lane.args(file, claim),
      { encoding: "utf8", timeout: timeoutMs, maxBuffer: 32 * 1024 * 1024 });
    return lane.parse(stdout);
  } finally {
    rmSync(dir, { recursive: true, force: true });
  }
}

function main(argv) {
  const listOnly = argv.includes("--list");
  const lanes = availableLanes();
  if (listOnly) {
    if (!lanes.length) { console.log("(none)"); console.error(NO_LANE.note); process.exit(3); }
    for (const l of lanes) console.log(`${l.name}\t${l.bin}`);
    return;
  }
  const i = argv.indexOf("--claim-file");
  if (i === -1 || !argv[i + 1]) {
    console.error("usage: crosscheck.mjs --claim-file <path> [--timeout <seconds>] | --list");
    process.exit(2);
  }
  const claim = readFileSync(argv[i + 1], "utf8");
  const t = argv.indexOf("--timeout");
  const timeoutMs = (t === -1 ? 300 : Number(argv[t + 1])) * 1000;

  if (!lanes.length) { console.log(JSON.stringify(NO_LANE, null, 2)); process.exit(3); }

  const failures = [];
  for (const lane of lanes) {
    let answer;
    try {
      answer = runLane(lane, claim, timeoutMs);
    } catch (e) {
      // First line only: a failed lane echoes its whole argv, and the argv contains the claim.
      failures.push(`${lane.name}: ${String(e.message).split("\n")[0].slice(0, 160)}`);
      continue;
    }
    const v = verdictFor({ lane: lane.name, model: answer.model, text: answer.text });
    if (v.status === "CHECKED") { console.log(JSON.stringify(v, null, 2)); return; }
    failures.push(`${lane.name}: ${v.note}`);
  }
  console.log(JSON.stringify({ ...NO_LANE, note: NO_LANE.note + " Lanes tried: " + failures.join(" | ") }, null, 2));
  process.exit(3);
}

if (import.meta.url === `file://${process.argv[1]}`) main(process.argv.slice(2));
