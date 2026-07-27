#!/usr/bin/env node
/*
 * issue-hygiene.mjs — ARCHITECTURE ROLE: the mechanical half of ADR 0094. The retrospect agent
 * runs this and cites its output, so backlog hygiene stops depending on someone remembering to
 * look. ADR 0083 established the shape for git custodial state and set the reopen condition this
 * fires: a sweep that misses visible cruft promotes one rung, from a prompt bullet to a script
 * whose output must be cited.
 *
 * IT PROPOSES; IT NEVER ACTS. Nothing here closes, retitles, relabels or edits an issue — it
 * reads a JSON dump and prints signals. Issues are the work-state home (ADR 0021), so closing one
 * destroys state no other record holds; that call stays the owner's. The script takes no network
 * access and has no `gh` dependency for exactly this reason: it cannot mutate what it cannot reach.
 *
 * ONLY MEASURED SIGNALS SHIP. Each signal below was checked against the real backlog before it
 * was kept. A duplicate/batching detector by title-and-body token overlap was DROPPED on that
 * check: ranking every pair by overlap put the one known batching pair 27th of 55, behind 26
 * unrelated pairs, so any threshold that caught it would bury it in noise (~4% precision). The
 * couplings worth batching in this repo are semantic — "these two experiments share an eval
 * battery" — and no token metric recovers that. A signal that fires mostly on noise trains people
 * to skip the whole report, which is worse than not shipping it (ADR 0094's Rejected list).
 *
 * DESIGN CONSTRAINTS: zero dependencies; detect() is PURE (no fs, no clock — `now` is injected)
 * so the decision logic is unit-testable, matching check-restatement.mjs's detect()/main() split.
 * main() is the thin IO wrapper.
 *
 * Usage:
 *   gh issue list --state open --limit 200 \
 *     --json number,title,body,updatedAt | node issue-hygiene.mjs
 *   node issue-hygiene.mjs <dump.json> [--dormant-days N] [--tracking-min N]
 * Always exits 0 unless the run could not be made at all — an unreadable dump or a malformed
 * threshold flag: a proposal list is not a gate verdict, and an advisory script that can fail a
 * build teaches people to stop running it.
 */
import { readFileSync } from "node:fs";

export const DEFAULTS = { dormantDays: 21, trackingMin: 5 };

/**
 * Checklist state of an issue body, or null when it carries no tracking checklist.
 * `min` boxes are required before a body counts as tracking: two or three checkboxes are a note.
 */
export function checklistProgress(body, min = DEFAULTS.trackingMin) {
  const boxes = String(body || "").match(/^[ \t]*[-*][ \t]+\[[ xX]\]/gm);
  if (!boxes || boxes.length < min) return null;
  const done = boxes.filter((b) => /\[[xX]\]/.test(b)).length;
  return { done, total: boxes.length, frac: done / boxes.length };
}

/**
 * Pure signal pass over an open-issue dump.
 *
 * `tracking` is an INVENTORY, not an alarm: it reports every multi-item tracking issue and its
 * tick state every run. That is deliberate. The failure it exists to catch is a tracking issue
 * whose directions ship without anyone ticking the box or re-reading the title — so the tick
 * state is exactly the thing that CANNOT be trusted as a trigger, and a threshold on it would
 * have stayed silent through the case that motivated this script (13 boxes, 0 ticked, one
 * direction already shipped). Reporting it costs one line and puts a human's eyes on the gap.
 *
 * @param {Array<{number:number,title:string,body?:string,updatedAt?:string}>} issues
 * @param {{now:string|Date, dormantDays?:number, trackingMin?:number}} opts
 */
export function detect(issues, opts = {}) {
  const { dormantDays, trackingMin } = { ...DEFAULTS, ...opts };
  const now = new Date(opts.now ?? Date.now());
  if (!Array.isArray(issues)) throw new TypeError("issues must be an array");
  const findings = [];

  for (const i of issues) {
    const age = i.updatedAt ? Math.floor((now - new Date(i.updatedAt)) / 86400000) : null;
    if (age !== null && age >= dormantDays) {
      findings.push({ kind: "dormant", number: i.number, title: i.title, days: age,
        note: `no activity in ${age} days — still wanted, or answered elsewhere?` });
    }
    const cl = checklistProgress(i.body, trackingMin);
    if (cl) {
      findings.push({ kind: "tracking", number: i.number, title: i.title,
        done: cl.done, total: cl.total,
        note: `${cl.done}/${cl.total} items ticked — check the remaining scope against the title, ` +
              "and whether any unticked item has already shipped" });
    }
  }
  return { open: issues.length, findings };
}

/**
 * A threshold flag's value, or `dflt` when the flag is absent. A missing or malformed value is
 * rejected rather than coerced: `Number(undefined)` is NaN, every comparison against NaN is false,
 * and the run would then report a clean backlog it never checked.
 *
 * BOTH SPELLINGS REACH THE SAME VALIDATION. `--x=5` is not the documented form, but an exact-token
 * lookup would let it miss the flag entirely and fall through to `dflt` — a report printed against
 * thresholds the caller did not ask for, which is the same fail-open the NaN check above closes.
 * Silently defaulting is the failure; rejecting an unparseable value is not.
 */
export function numericFlag(argv, name, dflt) {
  const eq = argv.find((a) => a.startsWith(`--${name}=`));
  const i = argv.indexOf(`--${name}`);
  if (eq === undefined && i === -1) return dflt;
  const raw = eq !== undefined ? eq.slice(`--${name}=`.length) : argv[i + 1];
  const n = raw === "" ? NaN : Number(raw);
  if (!Number.isFinite(n) || n <= 0) {
    throw new RangeError(`--${name} takes a positive number; got ${raw === undefined || raw === "" ? "no value" : `"${raw}"`}. ` +
      `Pass one (--${name} ${dflt}, or --${name}=${dflt}) or drop the flag for the default ${dflt}.`);
  }
  return n;
}

function main(argv) {
  let dormantDays, trackingMin;
  try {
    dormantDays = numericFlag(argv, "dormant-days", DEFAULTS.dormantDays);
    trackingMin = numericFlag(argv, "tracking-min", DEFAULTS.trackingMin);
  } catch (e) {
    console.error(`issue-hygiene: ${e.message}`);
    return 1;
  }
  const file = argv.find((a) => !a.startsWith("--") && !/^[\d.]+$/.test(a));
  let issues;
  try {
    issues = JSON.parse(readFileSync(file ?? 0, "utf8"));
  } catch (e) {
    console.error(`issue-hygiene: cannot read the issue dump (${e.message}). Pipe it in:\n` +
      "  gh issue list --state open --limit 200 --json number,title,body,updatedAt | node issue-hygiene.mjs");
    return 1;
  }
  const r = detect(issues, { now: new Date(), dormantDays, trackingMin });
  for (const f of r.findings) console.log(`  [${f.kind}] #${f.number} ${f.title}\n      ${f.note}`);
  const by = (k) => r.findings.filter((f) => f.kind === k).length;
  console.log(`issue-hygiene: ${r.open} open — ${by("dormant")} dormant, ${by("tracking")} tracking issue(s). ` +
    "Signals only: nothing here closes, retitles or re-scopes an issue — those stay owner calls (ADR 0094).");
  return 0;
}

if (import.meta.url === `file://${process.argv[1]}`) process.exit(main(process.argv.slice(2)));
