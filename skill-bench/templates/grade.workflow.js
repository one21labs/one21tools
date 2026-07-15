// Canonical grading-workflow TEMPLATE (#170) — normalize -> grade -> prosecute -> audit,
// the blinded pipeline audited across I2/armd/poker. COPY into a dated benchmark dir and
// adapt every ADAPT comment. Requires the Claude Code Workflow tool (#170 hard problem 3);
// without it, grade serially via `claude -p` per cell with the same prompts.
//
// The shape you keep: only the Normalize stage ever sees raw output (format is an arm tell —
// blinding lives in the schema); every grader met=true is prosecuted and met_final is the
// MIN of grader and prosecutor (ADR 0025); the guess-the-arm audit validates the blinding.
export const meta = {
  name: 'grade-blinded-cells',
  description: 'Normalize blinded cells to a neutral schema, grade pre-registered expectations, prosecute, guess-the-arm audit',
  phases: [
    { title: 'Normalize', detail: 'neutral schema per cell; only stage that sees raw output' },
    { title: 'Grade', detail: 'pre-registered expectations per cell' },
    { title: 'Prosecute', detail: 'adversarial re-judge of every met=true; met_final = min (ADR 0025)' },
    { title: 'Audit', detail: 'guess-the-arm on the sampled normalized cells' },
  ],
};

// args = { itemsDir, items: [{bid, scenario}], keys: {scenario: key}, auditBids: [...] }
let A = args
if (typeof A === 'string') { try { A = JSON.parse(A) } catch (e) { A = {} } }
const itemsDir = A.itemsDir
const items = Array.isArray(A.items) ? A.items : []
const KEYS = A.keys || {}
const auditBids = Array.isArray(A.auditBids) ? A.auditBids : []
log(`grading ${items.length} blinded cells; audit sample ${auditBids.length}`)

// ADAPT: the neutral schema for YOUR artifact type (decision schema shown — blind.py's
// NEUTRAL_DECISION_PROMPT convention; for review findings use the array schema instead).
const NORM_SCHEMA = {
  type: 'object', additionalProperties: false,
  properties: {
    decision: { type: 'string' },
    options: { type: 'array', items: { type: 'string' } },
    criterion: { type: 'string' },
    risks: { type: 'array', items: { type: 'string' } },
    assumptions: { type: 'array', items: { type: 'string' } },
  },
  required: ['decision', 'options', 'criterion', 'risks', 'assumptions'],
}
const EXP_IDS = [1, 2, 3, 4] // ADAPT: your pre-registered expectation ids
const EXP_ITEM = { type: 'object', additionalProperties: false,
  properties: { id: { type: 'integer' }, met: { type: 'boolean' }, why: { type: 'string' } },
  required: ['id', 'met', 'why'] }
const GRADE_SCHEMA = { type: 'object', additionalProperties: false,
  properties: { expectations: { type: 'array', items: EXP_ITEM } },
  required: ['expectations'] }
const AUDIT_SCHEMA = { type: 'object', additionalProperties: false,
  properties: { guess: { type: 'string', enum: ['A', 'C'] }, why: { type: 'string' } }, // ADAPT arms
  required: ['guess', 'why'] }

const normalize = (bid) => `Read the JSON file at ${itemsDir}/${bid}.json (fields: scenario, response). The "response" is a decision artifact (possibly with appended recorded files). Extract it into the neutral schema: decision (one sentence), options (each option considered, one line each, prefix rejected ones "REJECTED: <option> — <reason>"), criterion (the stated acceptance/reopen/success criterion, or "none"), risks (named risks), assumptions (named assumptions). Neutral wording; strip ALL formatting, section headers, and any role/process language. Do not judge quality; preserve content faithfully.`

// ADAPT: the rubric — pre-registered, one per scenario key; judge strictly from normalized
// content only. Keep the "met=true only on clear evidence" bar.
const rubricFor = (key) => `EXPECTATIONS:
1. ...
2. ...
KEY: ${JSON.stringify(key)}`

const gradeP = (norm, key) => `You are grading a blinded artifact (normalized to a neutral schema) against pre-registered expectations. Judge each expectation strictly and literally from the normalized content ONLY.

NORMALIZED: ${JSON.stringify(norm)}

${rubricFor(key)}

Return expectations: [{id, met, why}] — met=true only on clear evidence; vague gestures are NOT met.`

const prosecute = (norm, key, verdict) => `A first grader judged a blinded artifact. Your job: REFUTE its generous calls. Re-judge every expectation the grader marked met=true — default to met=false when the evidence is thin, indirect, or requires charity. Expectations the grader marked met=false stay false (you prosecute, never rescue). Copy the grader's why where you agree; write your own where you overturn.

NORMALIZED: ${JSON.stringify(norm)}

${rubricFor(key)}

FIRST GRADER: ${JSON.stringify(verdict)}
Return the corrected expectations array (same ids).`

// ADAPT: describe each arm neutrally so the auditor has a fair guess.
const audit = (norm) => `Systems produced artifacts in this benchmark; after normalization you must guess which produced this one. Arm A = <bare baseline>. Arm C = <treatment>. NORMALIZED: ${JSON.stringify(norm)}
Guess the arm and say why. If nothing distinguishes them, still pick one and say the signal is absent.`

const results = await pipeline(
  items,
  (it) => agent(normalize(it.bid), { label: `norm:${it.bid}`, phase: 'Normalize', schema: NORM_SCHEMA, model: 'sonnet' })
    .then((n) => ({ ...it, norm: n || { decision: '', options: [], criterion: 'none', risks: [], assumptions: [] }, key: KEYS[it.scenario] })),
  (it) => agent(gradeP(it.norm, it.key), { label: `grade:${it.bid}`, phase: 'Grade', schema: GRADE_SCHEMA, model: 'opus' })
    .then((v) => ({ ...it, grader: v })),
  (it) => agent(prosecute(it.norm, it.key, it.grader), { label: `pros:${it.bid}`, phase: 'Prosecute', schema: GRADE_SCHEMA, model: 'opus' })
    .then((p) => {
      const g = (it.grader && it.grader.expectations) || []
      const pr = (p && p.expectations) || []
      const finalExp = EXP_IDS.map((id) => {
        const gv = g.find((e) => e.id === id), pv = pr.find((e) => e.id === id)
        const met = !!(gv && gv.met) && !!(pv && pv.met)
        const src = met ? gv : (pv && !pv.met ? pv : gv)
        return { id, met, why: src ? src.why : 'NULL verdict' }
      })
      return { bid: it.bid, scenario: it.scenario, norm: it.norm, expectations: finalExp }
    })
)

const byBid = {}
for (const r of results.filter(Boolean)) byBid[r.bid] = r
const audits = await parallel(auditBids.map((bid) => () =>
  byBid[bid]
    ? agent(audit(byBid[bid].norm), { label: `audit:${bid}`, phase: 'Audit', schema: AUDIT_SCHEMA, model: 'sonnet' })
        .then((a) => ({ bid, ...(a || { guess: 'A', why: 'NULL auditor' }) }))
    : null))

return { cells: results.filter(Boolean), audit: audits.filter(Boolean) }
