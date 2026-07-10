export const meta = {
  name: 'tiered-execution',
  description: 'Issue #41 tiered-agent execution benchmark: sonnet-solo vs haiku-solo vs tiered (sonnet orchestrator plans+validates, haiku worker implements, <=2 worker iterations)',
  phases: [
    { title: 'Plan', detail: 'tiered orchestrator writes a brief spec from the task (tiered arm only)' },
    { title: 'Execute', detail: 'solo agent, or tiered worker, produces the deliverable' },
    { title: 'Validate', detail: 'tiered orchestrator checks the worker deliverable, may redispatch once (tiered arm only)' },
  ],
};

// args = { arm: 'sonnet-solo'|'haiku-solo'|'tiered', reps, evals }. `evals` = [{skill, eval_id,
// prompt}, ...] from prep.py's evals_args.json -- PROMPT ONLY, no expectations (executors must
// never see grading criteria). Run once per arm (3 invocations total); the operator persists each
// run's returned `result` to outputs/<arm>.json (benchmarks/lib/README.md persist convention).
let A = args
if (typeof A === 'string') { try { A = JSON.parse(A) } catch (e) { A = {} } }
const arm = (A && A.arm) || ''
const reps = (A && A.reps) || 3
const evals = (A && Array.isArray(A.evals)) ? A.evals : []
if (!['sonnet-solo', 'haiku-solo', 'tiered'].includes(arm)) throw new Error(`unknown arm: ${arm}`)
log(`executor arm=${arm} evals=${evals.length} reps=${reps}`)

// Identical across all 3 arms -- the control here is ARM SYMMETRY, not tool-denial (ADR 0023's
// hermeticity requirement scopes to the control arm; ADR 0027 scoping note). No skill content is
// ever injected in any arm. The workflow subagent may technically retain tool access, so this
// instruction is the operative control, applied verbatim everywhere it is used below.
const NEUTRAL_FRAME = 'Respond directly from the request text below. Do not read files, search the repository, run commands, or use any tools -- answer using only the text given in this request.'

// budget.spent() is the only in-workflow token signal available (there is no Date.now() inside the
// Workflow runner; wall-clock is bracketed OUTSIDE, at invocation time -- see README "Cost/time
// capture"). Sampled once at the start and once at the end of this arm's whole pipeline run, so the
// delta is a PER-ARM AGGREGATE, not a per-cell figure -- pipeline() runs items concurrently, so a
// per-cell split would not be attributable. Recorded as such; never fabricated to false precision.
const tokensStart = budget.spent()

const items = []
for (const e of evals) for (let rep = 1; rep <= reps; rep++) items.push({ e, rep })

const VALIDATE_SCHEMA = {
  type: 'object',
  additionalProperties: false,
  properties: { ok: { type: 'boolean' }, corrections: { type: 'string' } },
  required: ['ok', 'corrections'],
}

const cellLabel = (prefix, it) => `${prefix}:${it.e.skill}.${it.e.eval_id}:${arm}:r${it.rep}`

let results
if (arm === 'sonnet-solo' || arm === 'haiku-solo') {
  const soloModel = arm === 'sonnet-solo' ? 'sonnet' : 'haiku'
  results = await pipeline(
    items,
    (it) => agent(`${NEUTRAL_FRAME}\n\nRequest:\n${it.e.prompt}`,
      { label: cellLabel('exec', it), phase: 'Execute', model: soloModel, effort: 'medium' })
      .then((out) => ({ skill: it.e.skill, eval_id: it.e.eval_id, arm, rep: it.rep, response: out || '' })),
  )
} else {
  // Tiered: orchestrator (sonnet) plans -> worker (haiku) implements -> orchestrator (sonnet)
  // validates against the ORIGINAL request and may redispatch the worker ONCE with corrections
  // (max 2 worker iterations). The final deliverable is always the worker's LAST output -- the
  // orchestrator never rewrites it (that would contaminate which tier produced the deliverable).
  const planPrompt = (it) => `${NEUTRAL_FRAME}\n\nYou are the PLANNING lead for a task a separate implementer will carry out. Read the request below and write a brief, concrete spec for the implementer: what to produce, the key constraints, and the shape of the deliverable. Do NOT produce the deliverable yourself -- write the spec only.\n\nRequest:\n${it.e.prompt}`
  const workPrompt = (it, spec, corrections) => `${NEUTRAL_FRAME}\n\nYou are the IMPLEMENTER. Follow the spec below to produce the deliverable for the original request.${corrections ? `\n\nA reviewer found problems with your PREVIOUS attempt and asked for these corrections -- address them:\n${corrections}` : ''}\n\nOriginal request:\n${it.e.prompt}\n\nSpec:\n${spec}\n\nWrite the deliverable directly (the finished output the requester asked for, not a plan or commentary about it).`
  const validatePrompt = (it, deliverable) => `${NEUTRAL_FRAME}\n\nYou are the REVIEWING lead. Judge whether the deliverable below actually satisfies the original request -- fully, concretely, and without gaps. Return ok=true only if it is genuinely ready to hand back as-is; ok=false with specific, actionable corrections otherwise.\n\nOriginal request:\n${it.e.prompt}\n\nDeliverable:\n${deliverable}`

  results = await pipeline(
    items,
    (it) => agent(planPrompt(it), { label: cellLabel('plan', it), phase: 'Plan', model: 'sonnet', effort: 'medium' })
      .then((spec) => ({ it, spec: spec || '' })),
    ({ it, spec }) => agent(workPrompt(it, spec, null), { label: cellLabel('work1', it), phase: 'Execute', model: 'haiku', effort: 'medium' })
      .then((out) => ({ it, spec, worker1: out || '' })),
    ({ it, spec, worker1 }) => agent(validatePrompt(it, worker1), { label: cellLabel('validate', it), phase: 'Validate', schema: VALIDATE_SCHEMA, model: 'sonnet', effort: 'medium' })
      .then((v) => {
        const ok = !!(v && v.ok)
        if (ok) {
          return { skill: it.e.skill, eval_id: it.e.eval_id, arm, rep: it.rep, response: worker1,
            iterations: 1, plan: spec, worker1, validate1: v || null, worker2: null }
        }
        const corrections = (v && v.corrections) || 'no specific corrections returned; try again from the spec.'
        return agent(workPrompt(it, spec, corrections), { label: cellLabel('work2', it), phase: 'Execute', model: 'haiku', effort: 'medium' })
          .then((out2) => ({ skill: it.e.skill, eval_id: it.e.eval_id, arm, rep: it.rep, response: out2 || worker1,
            iterations: 2, plan: spec, worker1, validate1: v || null, worker2: out2 || '' }))
      }),
  )
}

const tokensEnd = budget.spent()
const clean = results.filter(Boolean)
log(`arm=${arm} done: ${clean.length} cells`)
return { arm, reps, cells: clean.length, tokens_start: tokensStart, tokens_end: tokensEnd, records: clean }
