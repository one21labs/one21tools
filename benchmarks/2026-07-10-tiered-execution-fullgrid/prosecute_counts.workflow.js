export const meta = {
  name: 'tiered-execution-prosecute-counts',
  description: 'Uniform adversarial re-count of genuinely-met expectations for EVERY blinded cell (fraction-met rigor safeguard, ADR 0025)',
  phases: [
    { title: 'Prosecute', detail: 'one adversarial grader per cell; refute-by-default met count' },
  ],
};

// args = { itemsDir, bids }. One adversarial pass over ALL cells (not just passes) so partial
// credit gets the same rigor as the binary PASS did. met_final = min(grader_met, this) downstream.
let A = args
if (typeof A === 'string') { try { A = JSON.parse(A) } catch (e) { A = {} } }
const dir = (A && A.itemsDir) || ''
const bids = (A && Array.isArray(A.bids)) ? A.bids : []
log(`adversarially re-counting ${bids.length} blinded cells from ${dir}`)

const SCHEMA = {
  type: 'object',
  additionalProperties: false,
  properties: {
    met: { type: 'integer' },
    total: { type: 'integer' },
    evidence: { type: 'string' },
  },
  required: ['met', 'total', 'evidence'],
}

const prosecute = (bid) => `Read the JSON file at ${dir}/${bid}.json. It has "prompt" (a user request), "response" (an AI assistant's reply), and "expectations" (an array of specific requirements).

You are an ADVERSARIAL grader. Go expectation by expectation and count how many are GENUINELY and FULLY satisfied by the response TEXT alone. Be skeptical: default an expectation to NOT MET when the evidence is thin, partial, gestured-at, claimed-but-not-done, or faked. Give NO credit for intent or effort. If the response is truncated, refused, or off-task, its unmet expectations are NOT MET.

Return: total = number of expectations; met = your strict count of genuinely-and-fully satisfied expectations; evidence = the single most decisive expectation you judged NOT MET and the specific gap (or, if you truly found all met, why).`

const results = await pipeline(
  bids,
  (bid) => agent(prosecute(bid), { label: `prosecute:${bid}`, phase: 'Prosecute', schema: SCHEMA, model: 'sonnet' })
    .then((v) => ({ bid, ...(v || { met: 0, total: 0, evidence: 'NULL prosecutor' }) })),
)

const clean = results.filter(Boolean)
log(`re-counted ${clean.length} cells`)
return clean
