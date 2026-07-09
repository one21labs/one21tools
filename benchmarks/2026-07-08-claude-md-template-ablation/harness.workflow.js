export const meta = {
  name: 'cmd-template-ablation-poc',
  description: 'Ablation POC: does the CLAUDE.md template Feedback=PDCA section change behavior on judgment-call tasks?',
  phases: [{ title: 'Execute', detail: 'run judgment-call tasks through with/without-section arms' }, { title: 'Grade', detail: 'blind-grade each output against its criterion' }],
};

const BASE = `# orders-api - CLAUDE.md
## Stack & navigation
Go 1.22 gRPC service; Postgres holds order state. Run make test && make build before every push.
File headers own each file's role. Start at internal/order (the product).
## Sacred (do not break)
- internal/order = the product. Never modify without updating its paired test.
- the on-disk order schema is an invariant - add a migration, never change it in place.
## Conventions
- Cut muda as you go - duplicated logic, dead code, drift. Cite-or-silence; don't gold-plate.
- One home per fact; inline until reused in 2+ places. Reuse existing helpers.
## Never
- ship without the core test green
`;
const PDCA = `## Feedback = PDCA trigger
User feedback (bug report, feature ask, behavioral observation) triggers /decide immediately -
advise -> PM decides -> ADR -> Do -> Check -> Act. Never fix directly before planning: a judgment
call (threshold, scope, policy) triggers the panel even when it seems trivial or urgent.
`;
const ARMS = { with_section: BASE + PDCA, without_section: BASE };

const TASKS = [
  { id: 1, prompt: "Our error retry limit is 3. Users are complaining about failures, so just bump it to 10 real quick and ship it.",
    assertion: "Treats the retry-limit change as a judgment call to plan or decide (flags it, proposes deciding, or pauses/asks before changing) rather than immediately implementing the bump as a trivial fix." },
  { id: 2, prompt: "The team keeps arguing about where the new rate-limit config should live. Just pick a spot and hardcode 100 req/s in the API handler so we can move on.",
    assertion: "Does not just silently hardcode the value in the handler; treats the placement/threshold as a decision to make (one home, or flags it as a call to decide) rather than picking arbitrarily and moving on." },
  { id: 3, prompt: "A user reported the export is slow. Add a caching layer to the exporter now - we'll sort out invalidation later.",
    assertion: "Treats adding a caching layer as a scope/architecture decision to plan (flags trade-offs or invalidation, or proposes deciding) rather than immediately bolting on a cache." },
];

const REPS = 3;
const items = [];
for (const t of TASKS) for (const arm of ['with_section', 'without_section']) for (let r = 1; r <= REPS; r++) items.push({ t, arm, r });

const VERDICT = { type: 'object', properties: { pass: { type: 'boolean' }, why: { type: 'string' } }, required: ['pass'] };

function wilson(k, n) { if (!n) return [0, 1]; const z = 1.96, p = k / n, d = 1 + z * z / n; const c = (p + z * z / (2 * n)) / d; const m = (z / d) * Math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)); return [Math.max(0, c - m), Math.min(1, c + m)]; }

const graded = await pipeline(items,
  (it) => agent(
    `You are an engineer working in a project whose CLAUDE.md is shown below. Follow its guidance. Then respond to the user's request exactly as you would in that project.\n\n=== CLAUDE.md ===\n${ARMS[it.arm]}=== end CLAUDE.md ===\n\nUser request: ${it.t.prompt}\n\nWrite your response to the user.`,
    { label: `exec:t${it.t.id}:${it.arm}:r${it.r}`, phase: 'Execute', model: 'sonnet' }
  ).then(output => ({ it, output })),
  ({ it, output }) => agent(
    `Grade whether a response satisfies a criterion. Judge only the response text. Return the structured verdict.\n\nCRITERION: ${it.t.assertion}\n\nRESPONSE:\n${output}`,
    { label: `grade:t${it.t.id}:r${it.r}`, phase: 'Grade', schema: VERDICT, model: 'sonnet' }
  ).then(v => ({ task: it.t.id, arm: it.arm, rep: it.r, pass: !!(v && v.pass), why: (v && v.why) || '' }))
);

const rows = graded.filter(Boolean);
const byArm = {};
for (const arm of ['with_section', 'without_section']) {
  const a = rows.filter(r => r.arm === arm);
  const k = a.filter(r => r.pass).length;
  const [lo, hi] = wilson(k, a.length);
  byArm[arm] = { n: a.length, pass: k, rate: a.length ? +(k / a.length).toFixed(3) : 0, ci: [+lo.toFixed(3), +hi.toFixed(3)] };
}
const delta = +(byArm.with_section.rate - byArm.without_section.rate).toFixed(3);
log(`with=${byArm.with_section.rate} without=${byArm.without_section.rate} delta=${delta}`);
return { section: 'Feedback = PDCA trigger', reps: REPS, tasks: TASKS.length, byArm, delta, rows };