export const meta = {
  name: 'ep-loophole-oos-retest',
  description: 'Out-of-sample retest: does the engineering-principles loophole fix (PR #27) generalize to fresh SSoT/waste scenarios?',
  phases: [{ title: 'Execute', detail: 'fresh SSoT/waste tasks, with-skill vs without-skill' }, { title: 'Grade', detail: 'blind-grade each output' }],
}

const SKILL_DIR = 'C:/Users/ajmcc/projects/worktrees/one21tools-main/skills/engineering-principles';
const WITH_PREFIX = `You are an engineer. BEFORE responding, read and apply the principles in these files:
- ${SKILL_DIR}/SKILL.md
- ${SKILL_DIR}/references/ssot-enforcement.md
- ${SKILL_DIR}/references/waste-identification.md
Apply them to the request below.\n\n`;
const WITHOUT_PREFIX = `You are an engineer. Respond to the request below.\n\n`;

// Fresh (out-of-sample) tasks in the loophole areas PR #27 fixed: SSoT enforcement + waste (sunk cost, premature abstraction).
const TASKS = [
  { id: 1, area: 'ssot', prompt: "The API version string 'v4' needs to appear in the docs, the client config, and the server route prefix. Just set all three to v4 so they match and we ship.",
    assertion: "Flags the value being duplicated across three homes as the real problem (proposes a single source others derive from / one home), rather than just editing all three copies to match." },
  { id: 2, area: 'sunk-cost', prompt: "We spent two sprints building our custom in-memory cache. Benchmarks show it's actually slower than just using the standard library map, but we should keep it since we already invested the effort. Agree?",
    assertion: "Rejects sunk cost as a reason to keep the slower custom cache (the past effort is spent regardless); recommends the faster stdlib option on current merits, not the invested effort." },
  { id: 3, area: 'premature-abstraction', prompt: "There's one exporter today. Let's build a generic plugin framework now so future devs can add more exporter formats without touching core code.",
    assertion: "Identifies the plugin framework as premature abstraction / speculative generality for a single current use (inline until a 2nd real use exists), rather than endorsing building the framework now." },
];

const REPS = 3;
const items = [];
for (const t of TASKS) for (const arm of ['with_skill', 'without_skill']) for (let r = 1; r <= REPS; r++) items.push({ t, arm, r });
const VERDICT = { type: 'object', properties: { pass: { type: 'boolean' }, why: { type: 'string' } }, required: ['pass'] };
function wilson(k, n) { if (!n) return [0, 1]; const z = 1.96, p = k / n, d = 1 + z * z / n; const c = (p + z * z / (2 * n)) / d; const m = (z / d) * Math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)); return [Math.max(0, c - m), Math.min(1, c + m)]; }

const graded = await pipeline(items,
  (it) => agent(
    `${it.arm === 'with_skill' ? WITH_PREFIX : WITHOUT_PREFIX}Request: ${it.t.prompt}\n\nWrite your response.`,
    { label: `exec:t${it.t.id}:${it.arm}:r${it.r}`, phase: 'Execute' }
  ).then(output => ({ it, output })),
  ({ it, output }) => agent(
    `Grade whether a response satisfies a criterion. Judge only the response text. Return the structured verdict.\n\nCRITERION: ${it.t.assertion}\n\nRESPONSE:\n${output}`,
    { label: `grade:t${it.t.id}:r${it.r}`, phase: 'Grade', schema: VERDICT }
  ).then(v => ({ task: it.t.id, area: it.t.area, arm: it.arm, rep: it.r, pass: !!(v && v.pass) }))
);
const rows = graded.filter(Boolean);
const byArm = {};
for (const arm of ['with_skill', 'without_skill']) {
  const a = rows.filter(r => r.arm === arm); const k = a.filter(r => r.pass).length; const [lo, hi] = wilson(k, a.length);
  byArm[arm] = { n: a.length, pass: k, rate: a.length ? +(k / a.length).toFixed(3) : 0, ci: [+lo.toFixed(3), +hi.toFixed(3)] };
}
const delta = +(byArm.with_skill.rate - byArm.without_skill.rate).toFixed(3);
log(`with=${byArm.with_skill.rate} without=${byArm.without_skill.rate} delta=${delta}`);
return { test: 'ep loophole out-of-sample retest (PR #27)', reps: REPS, tasks: TASKS.length, byArm, delta, rows };