export const meta = {
  name: 'skills-hermetic-grade',
  description: 'Blind-grade skill-benchmark outputs against each eval\'s expectations, with an adversarial prosecutor pass on each PASS',
  phases: [
    { title: 'Grade', detail: 'one blind grader per output; all-expectations-met = pass' },
    { title: 'Verify', detail: 'prosecutor refutes each PASS' },
  ],
};

// args = { itemsDir, bids }. Each grader READS <itemsDir>/<bid>.json (prompt, expectations, response)
// — ARM withheld. May arrive as a JSON string; parse defensively.
let A = args
if (typeof A === 'string') { try { A = JSON.parse(A) } catch (e) { A = {} } }
const dir = (A && A.itemsDir) || ''
const bids = (A && Array.isArray(A.bids)) ? A.bids : []
log(`grading ${bids.length} blinded skill outputs from ${dir}`)

const SCHEMA = {
  type: 'object',
  additionalProperties: false,
  properties: {
    pass: { type: 'boolean' },
    met: { type: 'integer' },
    total: { type: 'integer' },
    evidence: { type: 'string' },
  },
  required: ['pass', 'met', 'total', 'evidence'],
}

const grade = (bid) => `Read the JSON file at ${dir}/${bid}.json. It has: "prompt" (a user request), "response" (an AI assistant's reply), and "expectations" (an array of specific requirements the response must satisfy).

Evaluate EACH expectation as MET or NOT MET, strictly and literally, using ONLY evidence in the response text. Do not give credit for intent, partial effort, or things the response merely gestures at. If the response is truncated, refused, or off-task, unmet expectations are NOT MET.

Return: total = number of expectations; met = how many are MET; pass = true ONLY if met == total (every expectation satisfied); evidence = the single most decisive expectation that is NOT MET (quote the response gap), or if all met, the expectation that was closest to failing and why it still passed.`

const prosecute = (bid) => `Read the JSON file at ${dir}/${bid}.json (fields "prompt", "response", "expectations"). A first grader judged that the response satisfies ALL expectations. Your job: REFUTE it.

Go expectation by expectation and hunt for ANY that is not genuinely, fully satisfied by the response text — a requirement the response skipped, only partially did, faked, or claimed without doing. Be adversarial; default to NOT MET when the evidence is thin.
Return: total, met (your count of genuinely-met), pass = true ONLY if you also find all expectations met, evidence = the decisive gap you found (or, if truly none, why the PASS holds).`

const results = await pipeline(
  bids,
  (bid) => agent(grade(bid), { label: `grade:${bid}`, phase: 'Grade', schema: SCHEMA, model: 'sonnet' })
    .then((v) => ({ bid, ...(v || { pass: false, met: 0, total: 0, evidence: 'NULL grader' }) })),
  (v) => (v && v.pass)
    ? agent(prosecute(v.bid), { label: `verify:${v.bid}`, phase: 'Verify', schema: SCHEMA, model: 'sonnet' })
        .then((pv) => ({ ...v, pass: !!(pv && pv.pass), met: pv ? pv.met : v.met, prosecutor: pv || null }))
    : v,
)

const clean = results.filter(Boolean)
const passes = clean.filter((r) => r.pass).length
log(`graded ${clean.length}; final PASS ${passes} / FAIL ${clean.length - passes}`)
return clean
