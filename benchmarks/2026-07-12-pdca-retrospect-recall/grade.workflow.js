export const meta = {
  name: 'retrospect-recall-grade',
  description: 'Normalize blinded I1 cells to neutral findings, map to seed keys, prosecute, and run the guess-the-arm audit',
  phases: [
    { title: 'Normalize', detail: 'neutral {claim, evidence} findings per cell (blind.py schema)' },
    { title: 'Grade', detail: 'map findings to the substrate seed key; judge non-seed findings' },
    { title: 'Prosecute', detail: 'adversarial re-judge of every found=true and every nonseed real/not' },
    { title: 'Audit', detail: 'guess-the-arm on the 8 sampled normalized cells' },
  ],
};

// args = { itemsDir, items: [{bid, substrate}], keys: {substrate: [seed key...]},
//          auditBids: [bid...] } — keys inlined by the operator (grade_run.py) because
// workflow scripts have no filesystem access.
let A = args
if (typeof A === 'string') { try { A = JSON.parse(A) } catch (e) { A = {} } }
const itemsDir = A.itemsDir
const items = Array.isArray(A.items) ? A.items : []
const KEYS = A.keys || {}
const auditBids = Array.isArray(A.auditBids) ? A.auditBids : []
log(`grading ${items.length} blinded cells; audit sample ${auditBids.length}`)

const NORM_SCHEMA = {
  type: 'object', additionalProperties: false,
  properties: { findings: { type: 'array', items: { type: 'object', additionalProperties: false,
    properties: { claim: { type: 'string' }, evidence: { type: 'string' } },
    required: ['claim', 'evidence'] } } },
  required: ['findings'],
}
const SEED_ITEM = { type: 'object', additionalProperties: false,
  properties: { class: { type: 'string' }, found: { type: 'boolean' },
    matched_claim: { type: 'string' }, why: { type: 'string' } },
  required: ['class', 'found', 'matched_claim', 'why'] }
const NONSEED_ITEM = { type: 'object', additionalProperties: false,
  properties: { claim: { type: 'string' }, real: { type: 'boolean' }, why: { type: 'string' } },
  required: ['claim', 'real', 'why'] }
const GRADE_SCHEMA = { type: 'object', additionalProperties: false,
  properties: { seeds: { type: 'array', items: SEED_ITEM },
    nonseed: { type: 'array', items: NONSEED_ITEM } },
  required: ['seeds', 'nonseed'] }
const AUDIT_SCHEMA = { type: 'object', additionalProperties: false,
  properties: { guess: { type: 'string', enum: ['A', 'C'] }, why: { type: 'string' } },
  required: ['guess', 'why'] }

const normalize = (bid) => `Read the JSON file at ${itemsDir}/${bid}.json (fields: substrate, response). The "response" is a review of a software project's recent work. Extract every DISTINCT problem/defect finding asserted in it into findings: one object per finding with "claim" (one-sentence neutral restatement) and "evidence" (the cite exactly as given: commit sha, file:line, file name, or "none"). Preserve every finding without judging merit; merge exact duplicates; strip all formatting, headers, role language, and improvement/fix proposals. If the response asserts no problems, return an empty findings array.`

const gradeP = (bid, sub, findings, key) => `You are grading a blinded review cell against a ground-truth key. NORMALIZED FINDINGS (the review's claims, neutral wording):
${JSON.stringify(findings)}

GROUND-TRUTH SEED KEY for substrate ${sub} (each seeded defect: its class, its plant site, and the found-iff predicate that defines a match):
${JSON.stringify(key)}

For EACH seed in the key, decide found (true/false): found=true ONLY if some finding satisfies the seed's found_iff predicate — the finding must cite the right site (the commit, or the file:line, or that file) AND name the defect's substance; a vague thematic mention without the cite does NOT count. Set matched_claim to the matching finding's claim (or "" if not found) and why to one sentence of justification.

Then list every finding that matched NO seed under nonseed, judging each real (a genuine defect a maintainer should fix, true) or not (invented, trivial-style noise, or wrong, false), with why. Judge strictly and literally.${key.length === 0 ? ' This substrate has ZERO seeds: every finding goes under nonseed.' : ''} Return seeds (same order as the key) and nonseed.`

const prosecute = (bid, sub, findings, key, verdict) => `A first grader judged a blinded review cell. Your job: REFUTE its generous calls. NORMALIZED FINDINGS: ${JSON.stringify(findings)}
SEED KEY (substrate ${sub}): ${JSON.stringify(key)}
FIRST GRADER: ${JSON.stringify(verdict)}

Adversarially re-judge: (1) every seed the grader marked found=true — does the matched finding REALLY satisfy the found_iff predicate, with the right cite and the right substance? Default to found=false when the match is thin. Seeds the grader marked found=false stay false (you only prosecute, never rescue). (2) every nonseed finding the grader called real=true — is it REALLY a genuine defect? Default to real=false when the evidence is thin; also re-check findings the grader called real=false and confirm or keep them false. Return the corrected seeds (same order) and nonseed arrays with your why on every item you changed (copy the grader's why where you agree).`

const audit = (bid, findings) => `Two systems produced review findings in this benchmark; after normalization to a neutral schema you must guess which produced this cell. Arm A = a bare general assistant asked to review a session for process problems. Arm C = a specialized retrospective-analysis skill with a method (git-signal sweep, friction cross-check, routed improvement homes). NORMALIZED FINDINGS for one cell: ${JSON.stringify(findings)}
Guess the arm (A or C) and say why. If nothing distinguishes them, still pick one and say the signal is absent.`

const results = await pipeline(
  items,
  (it) => agent(normalize(it.bid), { label: `norm:${it.bid}`, phase: 'Normalize', schema: NORM_SCHEMA, model: 'sonnet' })
    .then((n) => ({ ...it, findings: (n && n.findings) || [], key: KEYS[it.substrate] || [] })),
  (it) => agent(gradeP(it.bid, it.substrate, it.findings, it.key),
      { label: `grade:${it.bid}`, phase: 'Grade', schema: GRADE_SCHEMA, model: 'sonnet' })
    .then((v) => ({ ...it, grader: v })),
  (it) => agent(prosecute(it.bid, it.substrate, it.findings, it.key, it.grader),
      { label: `pros:${it.bid}`, phase: 'Prosecute', schema: GRADE_SCHEMA, model: 'sonnet' })
    .then((p) => {
      // met_final = min(grader, prosecutor) per seed (ADR 0025): found only if BOTH say found.
      const seeds = (it.key || []).map((k, i) => {
        const g = it.grader && it.grader.seeds && it.grader.seeds[i]
        const pr = p && p.seeds && p.seeds[i]
        const found = !!(g && g.found) && !!(pr && pr.found)
        const src = found ? g : (pr && !pr.found ? pr : g)
        return { class: k.class, found, matched_claim: src ? src.matched_claim : '',
                 why: src ? src.why : 'NULL verdict' }
      })
      const nonseed = (p && p.nonseed) || (it.grader && it.grader.nonseed) || []
      return { bid: it.bid, substrate: it.substrate, findings: it.findings, seeds, nonseed }
    })
)

const byBid = {}
for (const r of results.filter(Boolean)) byBid[r.bid] = r
const audits = await parallel(auditBids.map((bid) => () =>
  byBid[bid]
    ? agent(audit(bid, byBid[bid].findings), { label: `audit:${bid}`, phase: 'Audit', schema: AUDIT_SCHEMA, model: 'sonnet' })
        .then((a) => ({ bid, ...(a || { guess: 'A', why: 'NULL auditor' }) }))
    : null))

return { cells: results.filter(Boolean), audit: audits.filter(Boolean) }
