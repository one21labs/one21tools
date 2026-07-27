/*
 * cli-flags.mjs — ARCHITECTURE ROLE: the ONE home for reading a flag off argv, for every CLI this
 * plugin ships. Three scripts hand-rolled this and the copies disagreed, which is the failure mode
 * the repo's poka-yoke doctrine names: delete the mirror, derive.
 *
 * WHY IT EXISTS — a cited scar, not a preference. `issue-hygiene.mjs` shipped a fail-open where a
 * value-less `--dormant-days` became NaN and every comparison against NaN was false, so the run
 * reported a clean backlog it never checked. That was fixed. The fix matched the one input a
 * reviewer had reproduced and left the ISOMORPHIC case live in the sibling CLI: `sweep-state.mjs`
 * still read `--max` with a bare `argv.indexOf`, so `--max=2` missed the flag entirely and the
 * sweep silently ran to a different cap than the operator asked for — on the one tool whose whole
 * job is to stop an agent misreporting sweep state. A cross-family review found it; three
 * same-family audit rounds did not, because each had verified the exemplar and stopped.
 * So the remedy is a shared parser, not a third patch: a class closed once cannot be reopened one
 * CLI at a time.
 *
 * BOTH SPELLINGS, AND LAST WINS. `--x 5` and `--x=5` are the same flag. Silently defaulting
 * because the caller typed the undocumented spelling is the fail-open above wearing a different
 * hat. When a flag appears more than once the LAST occurrence wins, matching shell convention and
 * every argument parser a caller has used; an earlier implementation let any `=` form beat a later
 * space form, which is order-blind and cannot be predicted from the command line as read.
 *
 * MALFORMED IS REJECTED, NEVER COERCED. There is no tier that guesses: a guessed threshold prints
 * a report against limits nobody asked for, and a cited report (ADR 0094) is then read as if it
 * answered the question. Errors name the flag, quote what arrived, and prescribe both spellings —
 * the house error-message standard.
 *
 * DESIGN CONSTRAINTS: zero dependencies, pure (argv in, value out, no fs and no process access),
 * so every branch is unit-testable without a subprocess.
 */

/**
 * Raw string value of `--name`, accepting `--name value` and `--name=value`. Returns undefined
 * when the flag is absent, and "" when it is present with an empty value (which callers must
 * treat as malformed, not as absent — the distinction is the whole point).
 * Last occurrence wins.
 */
export function flagValue(argv, name) {
  if (!Array.isArray(argv)) return undefined;
  const eqPrefix = `--${name}=`;
  let value;
  for (let i = 0; i < argv.length; i++) {
    const a = argv[i];
    if (typeof a !== "string") continue;
    if (a.startsWith(eqPrefix)) value = a.slice(eqPrefix.length);
    // A following token that is itself a flag is NOT this flag's value: `--a --b` means `--a` was
    // given no value, and swallowing `--b` would both lose that flag and hide the mistake.
    else if (a === `--${name}`) value = typeof argv[i + 1] === "string" && !argv[i + 1].startsWith("--") ? argv[i + 1] : "";
  }
  return value;
}

/**
 * A positive-number flag's value, or `dflt` when absent. Throws RangeError when present but not a
 * positive finite number.
 */
export function numericFlag(argv, name, dflt) {
  const raw = flagValue(argv, name);
  if (raw === undefined) return dflt;
  const n = raw === "" ? NaN : Number(raw);
  if (!Number.isFinite(n) || n <= 0) {
    throw new RangeError(`--${name} takes a positive number; got ${raw === "" ? "no value" : `"${raw}"`}. ` +
      `Pass one (--${name} ${dflt} or --${name}=${dflt}) or drop the flag for the default ${dflt}.`);
  }
  return n;
}

/**
 * A required string flag (a path, an id). Throws RangeError when absent or empty, so a caller
 * cannot proceed on undefined and fail later somewhere less legible.
 */
export function requiredFlag(argv, name, usage) {
  const raw = flagValue(argv, name);
  if (raw === undefined || raw === "") {
    throw new RangeError(`--${name} is required and takes a value (--${name} <value> or --${name}=<value>).` +
      (usage ? `\n${usage}` : ""));
  }
  return raw;
}
