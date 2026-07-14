export const meta = {
  name: 'decide-poker-grade',
  description: 'Normalize blinded poker-grid cells (#185) to the neutral schema, grade the 4-expectation rubric, prosecute, and run the guess-the-arm audit',
  phases: [
    { title: 'Normalize', detail: 'neutral decision schema per cell (blind.py); only stage that sees raw output' },
    { title: 'Grade', detail: '4 pre-registered expectations per cell (backtest or synthetic key)' },
    { title: 'Prosecute', detail: 'adversarial re-judge of every met=true; met_final = min (ADR 0025)' },
    { title: 'Audit', detail: 'guess-the-arm (A/C/P) on 9 sampled normalized cells' },
  ],
};

// args = { itemsDir, items: [{bid, scenario}], keys: {scenario: key}, auditBids: [...] }
let A = args
if (typeof A === 'string') { try { A = JSON.parse(A) } catch (e) { A = {} } }
const itemsDir = A.itemsDir
const items = Array.isArray(A.items) ? A.items : []
const KEYS = A.keys || {}
const auditBids = Array.isArray(A.auditBids) ? A.auditBids : []
log(`grading ${items.length} blinded decision cells; audit sample ${auditBids.length}`)

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
const EXP_ITEM = { type: 'object', additionalProperties: false,
  properties: { id: { type: 'integer' }, met: { type: 'boolean' }, why: { type: 'string' } },
  required: ['id', 'met', 'why'] }
const GRADE_SCHEMA = { type: 'object', additionalProperties: false,
  properties: { expectations: { type: 'array', items: EXP_ITEM } },
  required: ['expectations'] }
const AUDIT_SCHEMA = { type: 'object', additionalProperties: false,
  properties: { guess: { type: 'string', enum: ['A', 'C', 'P'] }, why: { type: 'string' } },
  required: ['guess', 'why'] }

const normalize = (bid) => `Read the JSON file at ${itemsDir}/${bid}.json (fields: scenario, response). The "response" is a decision artifact (possibly with appended recorded files). Extract it into the neutral schema: decision (one sentence), options (each option considered, one line each, prefix rejected ones "REJECTED: <option> — <reason>"), criterion (the stated acceptance/reopen/success criterion, or "none"), risks (named risks), assumptions (named assumptions). Neutral wording; strip ALL formatting, section headers, and any role/process language (panels, advisors, scores, estimation rounds, skills, record-format names). Do not judge quality; preserve content faithfully.`

const rubricFor = (key) => key.type === 'backtest'
  ? `EXPECTATIONS (backtest; the decision's real outcome is known to you as the key below — the decider could not know it):
1. Enumerates >=2 real options including a rejected alternative with a reason.
2. States a falsifiable acceptance/reopen criterion (a concrete condition that would revisit or refute the decision).
3. Surfaces THE load-bearing assumption — met ONLY if the stated assumptions/risks include the one in the key ("assumption_that_broke"/"assumption_tested"), in substance if not wording.
4. Anticipates the failure class that actually occurred (key "failure_class") — met ONLY if a stated risk/criterion/assumption names that failure mode in substance.
KEY: ${JSON.stringify(key.outcome_key)}
The question as faced: ${key.question}`
  : `EXPECTATIONS (synthetic; the scenario contains a planted trap named in the key — the decider was not told):
1. Enumerates >=2 real options including a rejected alternative with a reason.
2. States a falsifiable acceptance/reopen criterion (a concrete condition that would revisit or refute the decision).
3. Meets the scenario-specific expectations in the key ("expectations" — judge them as a whole; met if the decision substantively satisfies at least 2 of the 3).
4. Handles the planted trap (key "trap"): the decision does NOT anchor on it / adopt it uncritically; explicit pushback or correct discounting counts as met.
KEY: ${JSON.stringify({ shape: key.shape, trap: key.trap, expectations: key.expectations })}`

const gradeP = (norm, key) => `You are grading a blinded decision artifact (normalized to a neutral schema) against pre-registered expectations. Judge each expectation strictly and literally from the normalized content ONLY.

NORMALIZED DECISION: ${JSON.stringify(norm)}

${rubricFor(key)}

Return expectations: [{id: 1..4, met, why}] — met=true only on clear evidence in the normalized content; vague gestures are NOT met.`

const prosecute = (norm, key, verdict) => `A first grader judged a blinded decision artifact. Your job: REFUTE its generous calls. Re-judge every expectation the grader marked met=true — default to met=false when the evidence is thin, indirect, or requires charity. Expectations the grader marked met=false stay false (you prosecute, never rescue). Copy the grader's why where you agree; write your own where you overturn.

NORMALIZED DECISION: ${JSON.stringify(norm)}

${rubricFor(key)}

FIRST GRADER: ${JSON.stringify(verdict)}
Return the corrected expectations array (same ids).`

const audit = (norm) => `Three systems produced decision artifacts in this benchmark; after normalization you must guess which produced this one. Arm A = a bare assistant asked to decide and give rationale. Arm C = a structured multi-agent decision panel (advisors, an accountable decider, a records process). Arm P = a decider that received three independent advisors' numeric 1-5 estimates per option (with cruxes and reversing dependencies, plus a convergence round where estimates diverged) before deciding. NORMALIZED DECISION: ${JSON.stringify(norm)}
Guess the arm (A, C, or P) and say why. If nothing distinguishes them, still pick one and say the signal is absent.`

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
      const finalExp = [1, 2, 3, 4].map((id) => {
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
