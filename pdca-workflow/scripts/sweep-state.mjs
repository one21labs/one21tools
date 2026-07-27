#!/usr/bin/env node
/*
 * sweep-state.mjs — ARCHITECTURE ROLE: make the `sweep` skill's stop decision mechanical, so the
 * one claim that matters cannot be made by narration.
 *
 * An iterated audit has exactly two ways to stop, and they mean opposite things:
 *   CLEAN      — consecutive rounds found nothing new. The surface is as clean as this method sees.
 *   EXHAUSTED  — the iteration cap was reached before the quiet tail was earned. Unknown
 *                remaining. This is a BUDGET outcome, not a quality one.
 * Reporting the second as the first is the failure the skill exists to prevent, and it is a
 * failure a summarizing agent is under constant pressure to commit. So the verdict is computed
 * here from the round log instead: exit 0 means CLEAN and nothing else does.
 *
 * NEWNESS IS COMPUTED, NOT DECLARED. Each round reports the finding ids it saw; this script
 * dedupes every id against ALL ids seen in every previous round, not against the ones that were
 * fixed. Deduping against the fixed set never converges — a finding judged not-real resurfaces
 * every round and keeps resetting the quiet counter forever.
 *
 * DESIGN CONSTRAINTS: zero dependencies; sweepState() is PURE (takes the parsed round list, no
 * fs) so the decision logic is unit-testable, matching check-restatement.mjs's detect()/main()
 * split. main() is the thin IO wrapper.
 *
 * A CLEAN VERDICT IS SELF-REFERENTIAL UNTIL A FOREIGN LANE SAYS OTHERWISE. A sweep run by the
 * maker's own model family, over the maker's own work, is exactly the claim class ADR 0093 refuses
 * to let a sibling settle: a fresh same-family agent is uncontaminated by the reasoning but shares
 * the priors, so it audits inside the frame and cannot see the frame. So CLEAN additionally
 * requires that at least one round recorded a lane from another vendor family; without it the
 * verdict is FRAME-UNCHECKED, which is honest rather than passing.
 * Scar (2026-07-26): a three-round sweep of this repo ran every lane same-family. The prose rule
 * to use a foreign lane existed, in the skill AND in the operator's own standing notes, and lost
 * to habit twice in one session — because a lane that AGREES reads as success and a lane that
 * contradicts reads as failure, so skipping it is self-serving, not forgetful. ADR 0047: a
 * decidable requirement does not get to live in prose.
 *
 * Usage: node sweep-state.mjs <rounds.jsonl> [--max <N>] [--quiet-rounds <K>]
 *   rounds.jsonl: one JSON object per line, appended as each round completes:
 *     {"round": 1, "ids": ["hook-lib-missing-test"], "xfam": "grok-4.5-build"}
 *   `ids` are stable slugs for VERIFIED findings only — an unverified finding is not a finding.
 *   An empty `ids` array is the normal shape of a quiet round and must still be logged.
 *   `xfam` is the MODEL ID that actually answered a cross-lineage lane in that round, read back
 *   from the lane rather than asserted (crosscheck.mjs owns that route and the family table).
 *   Omit it on rounds that had no foreign lane; one round carrying it is enough for the sweep.
 * Exit 0 CLEAN | 1 EXHAUSTED | 2 RUNNING (another round is owed) | 3 malformed input
 *      | 4 FRAME-UNCHECKED (converged, but no round left the maker's family).
 */
import { readFileSync } from "node:fs";
import { familyOf, MAKER_FAMILY } from "./crosscheck.mjs";
import { numericFlag } from "./cli-flags.mjs";

export const EXIT = { CLEAN: 0, EXHAUSTED: 1, RUNNING: 2, MALFORMED: 3, "FRAME-UNCHECKED": 4 };

/**
 * Pure: did any round leave the maker's lineage? Takes the model id each round reported and asks
 * crosscheck.mjs's table — the family logic has ONE home and this is not a second copy of it.
 * An unplaceable id fails closed for the same reason it does there: an answer from a model we
 * cannot name is not evidence the lineage was left.
 */
export function crossFamilyLane(rounds) {
  for (const r of rounds) {
    const fam = familyOf(r?.xfam);
    if (fam !== MAKER_FAMILY && fam !== "unknown") return { model: r.xfam, family: fam };
  }
  return null;
}

// The cap when the operator names none. It lives HERE and not in the skill prose: the skill used
// to state "no cap given = 5" while this script NaN'd without `--max` and exited MALFORMED, so the
// promise and the behaviour disagreed and only the behaviour ran. Five is chosen to be the same
// order as the quiet tail it must exceed — a cap below `quietRounds + 1` can never reach CLEAN.
export const DEFAULT_MAX_ROUNDS = 5;

/**
 * Pure verdict on a sweep's round log.
 * @param {Array<{round:number, ids:string[]}>} rounds - in execution order
 * @param {number} max - the iteration cap the operator stated BEFORE starting
 * @param {number} quietRounds - consecutive no-new-findings rounds required to call it clean
 */
export function sweepState(rounds, max, quietRounds = 2) {
  if (!Array.isArray(rounds) || !Number.isInteger(max) || max < 1) {
    return { state: "MALFORMED", reason: "rounds must be an array and max a positive integer" };
  }
  if (!Number.isInteger(quietRounds) || quietRounds < 1) {
    return { state: "MALFORMED", reason: "quietRounds must be a positive integer" };
  }
  const seen = new Set();
  const perRound = [];
  for (const r of rounds) {
    if (!r || !Array.isArray(r.ids)) {
      return { state: "MALFORMED", reason: `round ${perRound.length + 1} has no ids array` };
    }
    const fresh = r.ids.filter((id) => !seen.has(id));
    for (const id of r.ids) seen.add(id);
    perRound.push({ round: perRound.length + 1, total: r.ids.length, fresh: fresh.length, freshIds: fresh });
  }
  const n = perRound.length;
  const totalFindings = seen.size;
  // A quiet TAIL, not a quiet count anywhere: the rounds that must be empty are the LAST ones,
  // because a fix applied in round 3 can introduce a defect that only round 4 can see.
  const tail = perRound.slice(-quietRounds);
  const quiet = n >= quietRounds && tail.every((r) => r.fresh === 0);
  if (quiet) {
    // Convergence is necessary but not sufficient: a sweep that never left the maker's family has
    // shown its own lanes found nothing new, which is a weaker claim than "clean" (ADR 0093).
    const lane = crossFamilyLane(rounds);
    if (!lane) {
      return { state: "FRAME-UNCHECKED",
               reason: `${quietRounds} consecutive rounds found nothing new, but no round recorded a `
                 + `lane outside ${MAKER_FAMILY} — the sweep audited its own family's work and cannot `
                 + `settle that. Run one round with a foreign-vendor lane (crosscheck.mjs) and log the `
                 + `model that answered as "xfam"`,
               rounds: n, totalFindings, perRound };
    }
    return { state: "CLEAN",
             reason: `${quietRounds} consecutive rounds found nothing new, cross-checked by ${lane.model} (${lane.family})`,
             rounds: n, totalFindings, perRound, crossFamily: lane };
  }
  if (n >= max) {
    const lastFresh = perRound[n - 1]?.fresh ?? 0;
    // The skill relays this reason verbatim, so it has to fit both shapes the cap can end in:
    // findings still arriving, or a last round that was quiet but too short to earn the tail.
    const how = lastFresh > 0
      ? `with findings still arriving (round ${n} found ${lastFresh} new)`
      : `short of the quiet tail of ${quietRounds} (round ${n} found 0 new)`;
    return { state: "EXHAUSTED",
             reason: `cap of ${max} rounds reached ${how} — remaining defects UNKNOWN, not zero`,
             rounds: n, totalFindings, perRound };
  }
  return { state: "RUNNING", reason: `round ${n + 1} of at most ${max} is owed`,
           rounds: n, totalFindings, perRound };
}

const USAGE = `usage: node sweep-state.mjs <rounds.jsonl> [--max <N>] [--quiet-rounds <K>]\n` +
  `  --max defaults to ${DEFAULT_MAX_ROUNDS}, --quiet-rounds to 2 (both accept --flag=N too)`;

function main(argv) {
  const file = argv.find((a) => !a.startsWith("--"));
  if (!file) {
    console.error(USAGE);
    return EXIT.MALFORMED;
  }
  // Flag parsing is NOT hand-rolled here: cli-flags.mjs is the one home, because the bare
  // `argv.indexOf` this replaced made `--max=2` miss the flag and run to the default cap instead.
  let max, quiet;
  try {
    max = numericFlag(argv, "max", DEFAULT_MAX_ROUNDS);
    quiet = numericFlag(argv, "quiet-rounds", 2);
  } catch (e) {
    console.error(`sweep-state: ${e.message}\n${USAGE}`);
    return EXIT.MALFORMED;
  }
  let rounds;
  try {
    rounds = readFileSync(file, "utf8").split("\n").filter((l) => l.trim()).map((l) => JSON.parse(l));
  } catch (e) {
    console.error(`sweep-state: cannot read round log ${file}: ${e.message}`);
    return EXIT.MALFORMED;
  }
  const v = sweepState(rounds, max, quiet);
  if (v.state === "MALFORMED") {
    console.error(`sweep-state: ${v.reason}`);
    return EXIT.MALFORMED;
  }
  const detail = v.perRound.map((r) => `  round ${r.round}: ${r.total} finding(s), ${r.fresh} new`).join("\n");
  console.log(`sweep-state: ${v.state} — ${v.reason}\n${detail}\n${v.totalFindings} distinct finding(s) across ${v.rounds} round(s).`);
  return EXIT[v.state];
}

if (import.meta.url === `file://${process.argv[1]}`) process.exit(main(process.argv.slice(2)));
