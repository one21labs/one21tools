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
 *   `xfam` is the MODEL ID that answered a cross-lineage lane in that round, read back from the
 *   lane rather than asserted (crosscheck.mjs owns that route and the family table).
 *   Omit it on rounds that had no foreign lane. The lane must land in the QUIET TAIL, not merely
 *   somewhere in the log: a foreign round that FOUND things witnesses that round, not the later
 *   quiet being called clean. This shipped in the weak form first ("one round carrying it is
 *   enough") and did the predictable damage inside a day — a foreign lane at round 4 let every
 *   later round inherit the credit, so round 5 was planned same-family WITH THE MECHANISM'S
 *   BLESSING. A check satisfiable once and then coasted on is a check the audited party satisfies
 *   once and then coasts on; that is not forgetfulness, it is the incentive the check was built
 *   against.
 *   RESIDUAL, stated because overstating it would be the same self-grading defect one level up:
 *   this field is written by the agent being audited, so it can be FORGED by typing a foreign
 *   model name. main() corroborates what it can — that a foreign lane is actually reachable on
 *   this machine — which turns free forgery into a claim contradicted by `crosscheck.mjs --list`.
 *   It cannot prove the lane was used. Only a committed artifact from the lane could, and that is
 *   not built. Treat CLEAN as "converged, and a foreign lane was available and claimed", not as
 *   proof one ran.
 * Exit 0 CLEAN | 1 EXHAUSTED | 2 RUNNING (another round is owed) | 3 malformed input
 *      | 4 FRAME-UNCHECKED (converged, but no round left the maker's family).
 */
import { readFileSync } from "node:fs";
import { familyOf, MAKER_FAMILY, availableLanes } from "./crosscheck.mjs";
import { integerFlag, positionals } from "./cli-flags.mjs";

export const EXIT = { CLEAN: 0, EXHAUSTED: 1, RUNNING: 2, MALFORMED: 3, "FRAME-UNCHECKED": 4 };

/**
 * Pure: did any round leave the maker's lineage? Takes the model id each round reported and asks
 * crosscheck.mjs's table — the family logic has ONE home and this is not a second copy of it.
 * An unplaceable id fails closed for the same reason it does there: an answer from a model we
 * cannot name is not evidence the lineage was left.
 */
export function isForeignFamily(fam) {
  return fam !== MAKER_FAMILY && fam !== "unknown";
}

export function crossFamilyLane(rounds) {
  // DERIVED from the plural, not a second scan. The two ran identical logic differing only in the
  // stop condition, which is the duplicated-logic class this file's own header argues against — and
  // they had already drifted: the singular assumed `rounds` was always an array while the plural
  // guarded with `?? []`. The advisory muda review caught it before merge.
  return crossFamilyLanes(rounds)[0] ?? null;
}

/**
 * EVERY foreign lane in `rounds`, in round order. crossFamilyLane returns the FIRST match and stops,
 * which is right for "is there one?" and wrong for describing what a log contains: the
 * FRAME-UNCHECKED message said "its ONLY foreign lane (X)" while calling crossFamilyLane, so a log
 * with two pre-tail lanes got a false sentence that also named the OLDEST — the one an operator is
 * least likely to be thinking of. Counting is a different question from existence, so it gets its
 * own function rather than a caller assuming the singular answer is exhaustive.
 */
export function crossFamilyLanes(rounds) {
  const out = [];
  for (const r of rounds ?? []) {
    const fam = familyOf(r?.xfam);
    if (isForeignFamily(fam)) out.push({ model: r.xfam, family: fam });
  }
  return out;
}

/**
 * Pure given `env`: the model id a LANE would answer as, which is what family placement needs.
 * A lane's NAME is not a model id, and conflating them inverted the rule: main() asked
 * `familyOf(lane.name)`, so `copilot` came back "unknown", and "unknown" !== the maker's family, so
 * copilot was counted as FOREIGN — the exact opposite of the polarity crossFamilyLane enforces one
 * screen above, and wrong in the one way that matters, because copilot's auto mode routes to a
 * model in the maker's own family on this machine. The custom lane names its model in the
 * environment; a built-in lane is identified by its own name.
 */
export function laneModelId(lane, env = process.env) {
  return lane?.custom ? (env.PDCA_CROSSCHECK_MODEL ?? "") : (lane?.name ?? "");
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
    // ...and the lane must witness the QUIET rounds, so the tail is what gets asked, not the log.
    // A foreign lane on a round that found things proves the foreign lane finds what this family
    // misses — which is an argument that the LATER same-family quiet is unwitnessed, not evidence
    // for it.
    // EVERY quiet round, not just one of them. crossFamilyLane is an EXISTENCE test, so asking it
    // over the whole tail reproduced the very shape this rule was written to kill, one level down:
    // one foreign quiet round blessed the remaining same-family quiet rounds. "Satisfy once and
    // coast" is the defect, and it does not stop being the defect because the window got smaller.
    // A cross-family review caught it inside the fix for it. Cost is real -- a K-round tail now
    // wants K foreign lanes -- and that IS the price of the claim: each quiet round is evidence
    // only for itself.
    const tail = rounds.slice(-quietRounds);
    const unwitnessed = tail.filter((r) => !crossFamilyLane([r])).length;
    const lane = unwitnessed === 0 ? crossFamilyLane(tail) : null;
    if (!lane) {
      // Says only what the code establishes, and says it about ALL of them. Two drafts of this
      // sentence each asserted something unchecked: first "on a round that DID find things" (the
      // lane scan never looks at findings), then "its ONLY foreign lane" (the scan returns the
      // first match and never counts). Both were caught by cross-family rounds, the second inside
      // the commit that fixed the first. Hence the plural helper — the quantifier now comes from
      // the data rather than from an assumption about it.
      const earlier = crossFamilyLanes(rounds.slice(0, -quietRounds));
      const why = earlier.length
        ? `its foreign lane${earlier.length > 1 ? "s" : ""} `
          + `(${[...new Set(earlier.map((l) => l.model))].join(", ")}) ran before the quiet tail, so `
          + `nothing outside ${MAKER_FAMILY} has seen the rounds now being called clean`
        : `no round recorded a lane outside ${MAKER_FAMILY} — the sweep audited its own family's work `
          + `and cannot settle that`;
      return { state: "FRAME-UNCHECKED",
               reason: `${quietRounds} consecutive rounds found nothing new, but ${why}. Run another `
                 + `round with a foreign-vendor lane (crosscheck.mjs); it must find nothing new, and `
                 + `log the model that answered as "xfam"`,
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
  const file = positionals(argv, ["max", "quiet-rounds"])[0];
  if (!file) {
    console.error(USAGE);
    return EXIT.MALFORMED;
  }
  // Flag parsing is NOT hand-rolled here: cli-flags.mjs is the one home, because the bare
  // `argv.indexOf` this replaced made `--max=2` miss the flag and run to the default cap instead.
  let max, quiet;
  try {
    max = integerFlag(argv, "max", DEFAULT_MAX_ROUNDS);
    quiet = integerFlag(argv, "quiet-rounds", 2);
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
  // Corroborate the log's cross-family claim against the machine (see RESIDUAL in the header).
  // sweepState stays PURE — no fs, no exec — so the check that needs the environment lives here.
  if (v.state === "CLEAN") {
    // ONE polarity rule, asked of a MODEL id — not a second rule keyed on lane names. The previous
    // form excluded `custom` by name, which locked the documented vendor-agnostic escape out of ever
    // corroborating: an adopter wiring PDCA_CROSSCHECK_CMD got FRAME-UNCHECKED telling them to run
    // `crosscheck.mjs --list`, which then listed their lane. The error contradicted itself.
    const foreign = availableLanes().some((l) => isForeignFamily(familyOf(laneModelId(l))));
    if (!foreign) {
      console.error(`sweep-state: FRAME-UNCHECKED — the round log claims a lane outside ${MAKER_FAMILY} `
        + `(${v.crossFamily.model}), but no lane placeable OUTSIDE ${MAKER_FAMILY} is reachable on this `
        + `machine, so that claim cannot be corroborated. Run \`node crosscheck.mjs --list\`; a lane `
        + `whose model cannot be placed does not count, and for a custom lane the model id comes from `
        + `$PDCA_CROSSCHECK_MODEL — set it if it is unset.`);
      return EXIT["FRAME-UNCHECKED"];
    }
  }
  if (v.state === "MALFORMED") {
    console.error(`sweep-state: ${v.reason}`);
    return EXIT.MALFORMED;
  }
  const detail = v.perRound.map((r) => `  round ${r.round}: ${r.total} finding(s), ${r.fresh} new`).join("\n");
  console.log(`sweep-state: ${v.state} — ${v.reason}\n${detail}\n${v.totalFindings} distinct finding(s) across ${v.rounds} round(s).`);
  return EXIT[v.state];
}

if (import.meta.url === `file://${process.argv[1]}`) process.exit(main(process.argv.slice(2)));
