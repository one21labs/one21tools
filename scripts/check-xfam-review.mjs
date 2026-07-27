#!/usr/bin/env node
/*
 * check-xfam-review.mjs — GATE: the branch's shipped diff must have been shown to a model outside
 * the maker's vendor family, and the artifact proving it must be committed.
 *
 * WHY THIS EXISTS, stated plainly because the honest version is unflattering. Over one session the
 * agent maintaining this repo was asked FOUR times by the owner to run a cross-family review. Each
 * time it had a reason the rule did not apply: the work was "a sweep round, not my own work"; a
 * mechanism it had built accepted a foreign lane logged ANYWHERE in a run log, so one early lane
 * excused every later one; a rule scoped to "audit rounds" did not fire on an ad-hoc task. Three
 * emphatic prose rules in CLAUDE.md instructing exactly this all lost. One non-emphatic MECHANISM
 * — a pre-edit deny on a char budget — bound instantly and was never once evaded.
 *
 * So this is not prose. The trigger is a DIFF EXISTING, which the agent cannot reclassify, and the
 * failure is a red gate rather than a note in a report.
 *
 * WHAT IT PROVES, AND WHAT IT CANNOT. It proves an artifact exists, that it is bound by hash to the
 * diff being shipped, and that the model named in it is placeable OUTSIDE the maker's family. It
 * does NOT prove the prompt was adversarial, that the reviewer saw the whole invariant, that the
 * findings were acted on, or that a human read any of it. Calling that "cross-family review" would
 * be marketing; it is cross-family INVOCATION LOGGING, and the difference matters enough to say in
 * the file rather than only in a commit message. Its value is that skipping now costs something and
 * leaves a trace, where before it cost nothing and left none.
 *
 * THE RESIDUAL, which cannot be closed from inside: the artifact is written by the audited agent,
 * so it can be forged by hand. Nothing here detects that. What raises the price is that forging is
 * an explicit act with a committed artifact attached, rather than an omission nobody can see. The
 * control that would actually bind — the gate config living where the agent may propose but not
 * merge — is branch protection, and that is the owner's to hold, not this script's.
 *
 * ARTIFACT: docs/pdca/xfam/<sha>.md, where <sha> is this script's own hash of the shipped diff.
 * First line must be a header naming the model:  `xfam-model: <model-id>`
 * The rest is the raw reviewer output, committed verbatim.
 *
 * Exit 0 = covered · 1 = not covered / no foreign model · 2 = cannot determine (bad range, no git).
 * TESTING: check-xfam-review.test.mjs (`node --test scripts/*.test.mjs`).
 * Usage: node scripts/check-xfam-review.mjs [baseRef] [headRef]   (default: origin/main HEAD)
 */
import { createHash } from "node:crypto";
import { execFileSync } from "node:child_process";
import { readFileSync, existsSync, readdirSync } from "node:fs";
import { join } from "node:path";
import { fileURLToPath } from "node:url";
import { familyOf, MAKER_FAMILY } from "../pdca-workflow/scripts/crosscheck.mjs";

export const ARTIFACT_DIR = "docs/pdca/xfam";

/**
 * Pure: the hash a diff is filed under. Normalises line endings and drops git's `index <sha>..`
 * lines, which change on every rebase without the CONTENT changing — keying on them would expire
 * a perfectly good review every time the branch was rebased, and a gate that cries wolf on a
 * no-op is a gate people learn to re-run until it passes.
 */
export function diffHash(diffText) {
  const normalised = String(diffText ?? "")
    .replace(/\r\n/g, "\n")
    .split("\n")
    .filter((l) => !l.startsWith("index ") && !l.startsWith("similarity index "))
    .join("\n")
    .trim();
  return createHash("sha256").update(normalised).digest("hex").slice(0, 16);
}

/**
 * Pure: does this artifact text name a model OUTSIDE the maker's family?
 * An unplaceable id is NOT foreign — same polarity as everywhere else in this repo: an id we
 * cannot name is not evidence the lineage was left.
 */
export function artifactModel(text) {
  // THE FIRST NON-EMPTY LINE, not any line. The header comment has always said "first line" while
  // the regex carried /m and accepted the marker anywhere in the file -- so a reviewer's own prose
  // mentioning `xfam-model:` mid-document would satisfy the gate. A doc-drift lane found the two
  // disagreeing; the doc was the version worth keeping, because a marker that can appear anywhere
  // can appear by accident.
  const first = String(text ?? "").split("\n").find((l) => l.trim() !== "") ?? "";
  const m = first.match(/^\s*xfam-model:\s*(\S+)/);
  if (!m) return { model: null, family: null, foreign: false, reason: "no `xfam-model:` header line" };
  const family = familyOf(m[1]);
  if (family === MAKER_FAMILY) {
    return { model: m[1], family, foreign: false, reason: `${m[1]} is ${family} — the maker's own family` };
  }
  if (family === "unknown") {
    return { model: m[1], family, foreign: false, reason: `${m[1]} cannot be placed in any known vendor family` };
  }
  return { model: m[1], family, foreign: true, reason: `${m[1]} (${family})` };
}

/**
 * Pure decision: given the shipped diff and the artifacts on disk, is it covered?
 * `artifacts` is [{ name, text }].
 */
export function coverage(diffText, artifacts) {
  const hash = diffHash(diffText);
  if (!String(diffText ?? "").trim()) {
    return { ok: true, hash, reason: "empty diff — nothing shipped, nothing to review" };
  }
  const hit = (artifacts ?? []).find((a) => a.name === `${hash}.md`);
  if (!hit) {
    return { ok: false, hash, reason: `no artifact ${ARTIFACT_DIR}/${hash}.md for the shipped diff` };
  }
  const m = artifactModel(hit.text);
  if (!m.foreign) return { ok: false, hash, reason: `artifact ${hash}.md does not name a foreign model: ${m.reason}` };
  return { ok: true, hash, model: m.model, family: m.family, reason: `reviewed by ${m.model} (${m.family})` };
}

function main(argv) {
  const base = argv[2] || "origin/main";
  const head = argv[3] || "HEAD";
  let diff;
  try {
    // The artifact directory is EXCLUDED from the hashed diff. Without this the gate is
    // unsatisfiable: the artifact lives on the branch, so committing it changes the diff, which
    // changes the required hash, which demands a new artifact -- a loop with no fixed point (a
    // cross-family review measured 6 commits producing 6 new hashes, never converging). A gate an
    // honest actor CANNOT satisfy does not produce compliance, it produces evasion, which is the
    // opposite of the point.
    diff = execFileSync("git", ["diff", `${base}...${head}`, "--", ".", `:(exclude)${ARTIFACT_DIR}`],
      { encoding: "utf8", maxBuffer: 256 << 20 });
  } catch (e) {
    console.error(`check-xfam-review: cannot diff ${base}...${head}: ${e.message}. `
      + `Pass an existing base and head (usage: node scripts/check-xfam-review.mjs [base] [head]).`);
    process.exit(2);
  }
  // ARTIFACTS COME FROM THE REVIEWED COMMIT, not the working tree. On a pull_request event CI's
  // worktree is a MERGE of the PR into its base, so a worktree read would accept an artifact that
  // exists on base -- or only in the merge result -- and is absent from the very commit whose diff
  // was hashed. The gate would then certify "this head was reviewed" on evidence the head does not
  // contain. A cross-family review of the head.sha wiring found it. Falls back to the worktree only
  // when the ref cannot be read as a tree (a plain local run with uncommitted artifacts).
  // AN ABSENT DIRECTORY IS NOT AN UNREADABLE REF. The first version wrapped both cases in one
  // try/catch and fell back to the working tree whenever ls-tree failed for ANY reason -- and
  // ls-tree fails with "Not a valid object name" simply because the directory does not exist at
  // that commit yet, which is true of every branch cut before the gate shipped. An internal lane
  // proved the consequence: a hand-written, NEVER-COMMITTED artifact naming a foreign model made
  // the gate pass, defeating the one property the whole design rests on. So the ref is resolved
  // first: if head is a real commit, the tree is the only source of truth and a missing directory
  // means zero artifacts. The worktree fallback survives only for a ref git cannot resolve at all.
  let headResolves = true;
  try {
    execFileSync("git", ["rev-parse", "--verify", `${head}^{commit}`],
      { encoding: "utf8", stdio: ["ignore", "pipe", "ignore"] });
  } catch { headResolves = false; }

  let artifacts = [];
  if (headResolves) {
    try {
      const listed = execFileSync("git", ["ls-tree", "--name-only", `${head}:${ARTIFACT_DIR}`],
        { encoding: "utf8", stdio: ["ignore", "pipe", "ignore"] });
      artifacts = listed.split("\n").filter((f) => f.endsWith(".md")).map((f) => ({
        name: f,
        text: execFileSync("git", ["show", `${head}:${ARTIFACT_DIR}/${f}`],
          { encoding: "utf8", maxBuffer: 64 << 20 }),
      }));
    } catch { artifacts = []; }          // no such path at head: nothing was committed, full stop
  } else {
    artifacts = existsSync(ARTIFACT_DIR)
      ? readdirSync(ARTIFACT_DIR).filter((f) => f.endsWith(".md"))
          .map((f) => ({ name: f, text: readFileSync(join(ARTIFACT_DIR, f), "utf8") }))
      : [];
  }
  const v = coverage(diff, artifacts);
  if (v.ok) {
    console.log(`check-xfam-review: ${base}...${head} — ${v.reason} (${v.hash}).`);
    process.exit(0);
  }
  console.error(`check-xfam-review: ${v.reason}.`);
  console.error(
    `\nThe diff being shipped has not been shown to a model outside ${MAKER_FAMILY}. To clear this:\n` +
    `  1. node pdca-workflow/scripts/crosscheck.mjs --list      # what foreign lane this machine has\n` +
    `  2. review \`git diff ${base}...${head}\` with it, CHUNKED under ~14KB per prompt (a larger\n` +
    `     prompt is offloaded to a file the reviewer then cannot open, and it silently reviews nothing)\n` +
    `  3. commit its raw output to ${ARTIFACT_DIR}/${v.hash}.md, first line \`xfam-model: <model-id>\`\n\n` +
    `This gate exists because the prose version of this rule lost four times in one session while a\n` +
    `mechanical one has never been evaded. It proves the call happened — not that it was good.`);
  process.exit(1);
}

if (process.argv[1] === fileURLToPath(import.meta.url)) main(process.argv);
