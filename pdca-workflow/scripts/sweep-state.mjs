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
 * Usage: node sweep-state.mjs <rounds.jsonl> [--max <N>] [--quiet-rounds <K>]
 *   rounds.jsonl: one JSON object per line, appended as each round completes:
 *     {"round": 1, "ids": ["hook-lib-missing-test", "stale-judge-default"]}
 *   `ids` are stable slugs for VERIFIED findings only — an unverified finding is not a finding.
 *   An empty `ids` array is the normal shape of a quiet round and must still be logged.
 * Exit 0 CLEAN | 1 EXHAUSTED | 2 RUNNING (another round is owed) | 3 malformed input.
 */
import { readFileSync } from "node:fs";

export const EXIT = { CLEAN: 0, EXHAUSTED: 1, RUNNING: 2, MALFORMED: 3 };

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
    return { state: "CLEAN", reason: `${quietRounds} consecutive rounds found nothing new`,
             rounds: n, totalFindings, perRound };
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

function main(argv) {
  const file = argv.find((a) => !a.startsWith("--"));
  const num = (flag, dflt) => {
    const i = argv.indexOf(flag);
    return i === -1 ? dflt : Number(argv[i + 1]);
  };
  if (!file) {
    console.error(`usage: node sweep-state.mjs <rounds.jsonl> [--max <N>] [--quiet-rounds <K>]\n` +
      `  --max defaults to ${DEFAULT_MAX_ROUNDS}, --quiet-rounds to 2`);
    return EXIT.MALFORMED;
  }
  let rounds;
  try {
    rounds = readFileSync(file, "utf8").split("\n").filter((l) => l.trim()).map((l) => JSON.parse(l));
  } catch (e) {
    console.error(`sweep-state: cannot read round log ${file}: ${e.message}`);
    return EXIT.MALFORMED;
  }
  const v = sweepState(rounds, num("--max", DEFAULT_MAX_ROUNDS), num("--quiet-rounds", 2));
  if (v.state === "MALFORMED") {
    console.error(`sweep-state: ${v.reason}`);
    return EXIT.MALFORMED;
  }
  const detail = v.perRound.map((r) => `  round ${r.round}: ${r.total} finding(s), ${r.fresh} new`).join("\n");
  console.log(`sweep-state: ${v.state} — ${v.reason}\n${detail}\n${v.totalFindings} distinct finding(s) across ${v.rounds} round(s).`);
  return EXIT[v.state];
}

if (import.meta.url === `file://${process.argv[1]}`) process.exit(main(process.argv.slice(2)));
