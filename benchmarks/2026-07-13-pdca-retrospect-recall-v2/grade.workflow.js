export const meta = {
  name: 'retrospect-recall-v2-grade',
  description: 'Normalize blinded I1-v2 cells to neutral findings (remedy kept), map to seed keys with routing credit, prosecute, and run the guess-the-arm audit',
  phases: [
    { title: 'Normalize', detail: 'neutral {claim, evidence, remedy} findings per cell' },
    { title: 'Grade', detail: 'map findings to the seed key (found + routed per routing_key); judge non-seed findings' },
    { title: 'Prosecute', detail: 'adversarial re-judge of every found/routed=true and every nonseed real/not' },
    { title: 'Audit', detail: 'guess-the-arm on the 8 sampled normalized cells' },
  ],
};

// args = { itemsDir, items: [{bid, substrate}], keys: {substrate: [seed key...]},
//          auditBids: [bid...] } — keys carry found_iff AND routing_key (v2 delta 3).
let A = args
if (typeof A === 'string') { try { A = JSON.parse(A) } catch (e) { A = {} } }
const itemsDir = A.itemsDir
const items = Array.isArray(A.items) ? A.items : []
const KEYS = A.keys || {}
const auditBids = Array.isArray(A.auditBids) ? A.auditBids : []
log(`grading ${items.length} blinded v2 cells; audit sample ${auditBids.length}`)

const NORM_SCHEMA = {
  type: 'object', additionalProperties: false,
  properties: { findings: { type: 'array', items: { type: 'object', additionalProperties: false,
    properties: { claim: { type: 'string' }, evidence: { type: 'string' }, remedy: { type: 'string' } },
    required: ['claim', 'evidence', 'remedy'] } } },
  required: ['findings'],
}
const SEED_ITEM = { type: 'object', additionalProperties: false,
  properties: { class: { type: 'string' }, found: { type: 'boolean' }, routed: { type: 'boolean' },
    matched_claim: { type: 'string' }, why: { type: 'string' } },
  required: ['class', 'found', 'routed', 'matched_claim', 'why'] }
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

const normalize = (bid) => `Read the JSON file at ${itemsDir}/${bid}.json (fields: substrate, response). The "response" is a review of a software project's recent work. Extract every DISTINCT problem/defect finding asserted in it into findings: one object per finding with "claim" (one-sentence neutral restatement), "evidence" (the cite exactly as given: commit sha, file:line, file name, or "none"), and "remedy" (the fix/route the review proposes for it — which file, mechanism, or norm it says should change — one neutral sentence, or "none" if the review proposes nothing for this finding). Preserve every finding without judging merit; merge exact duplicates; strip all formatting, headers, and role/process language. If the response asserts no problems, return an empty findings array.`

const gradeP = (bid, sub, findings, key) => `You are grading a blinded review cell against a ground-truth key. NORMALIZED FINDINGS (the review's claims, neutral wording):
${JSON.stringify(findings)}

GROUND-TRUTH SEED KEY for substrate ${sub} (each seeded defect: its class, plant site, the found-iff predicate that defines a match, and the routing_key describing the correct remedy home):
${JSON.stringify(key)}

For EACH seed in the key decide: (1) found (true/false): found=true ONLY if some finding satisfies the seed's found_iff predicate — the finding must cite the right site (the commit, or the file:line, or that file) AND name the defect's substance; a vague thematic mention without the cite does NOT count. (2) routed (true/false): routed=true ONLY if found=true AND the matching finding's remedy (or claim) names the remedy home in the seed's routing_key in substance — the right file/mechanism/norm to change; a generic "fix it" or a wrong home does NOT count. Set matched_claim to the matching finding's claim (or "" if not found) and why to one sentence covering both judgments.

Then list every finding that matched NO seed under nonseed, judging each real (a genuine defect a maintainer should fix, true) or not (invented, trivial-style noise, or wrong, false), with why. Judge strictly and literally.${key.length === 0 ? ' This substrate has ZERO seeds: every finding goes under nonseed.' : ''} Return seeds (same order as the key) and nonseed.`

const prosecute = (bid, sub, findings, key, verdict) => `A first grader judged a blinded review cell. Your job: REFUTE its generous calls. NORMALIZED FINDINGS: ${JSON.stringify(findings)}
SEED KEY (substrate ${sub}): ${JSON.stringify(key)}
FIRST GRADER: ${JSON.stringify(verdict)}

Adversarially re-judge: (1) every seed the grader marked found=true — does the matched finding REALLY satisfy the found_iff predicate, with the right cite and the right substance? Default to found=false when the match is thin. (2) every seed the grader marked routed=true — does the finding's remedy REALLY name the routing_key's remedy home in substance? Default to routed=false when it is generic or aimed at the wrong home. Seeds the grader marked found=false stay false; routed can never be true where found is false (you only prosecute, never rescue). (3) every nonseed finding the grader called real=true — is it REALLY a genuine defect? Default to real=false when the evidence is thin; also re-check findings the grader called real=false and confirm or keep them false. Return the corrected seeds (same order) and nonseed arrays with your why on every item you changed (copy the grader's why where you agree).`

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
      // Per seed (ADR 0025 min rule): found iff BOTH found; routed iff found AND both routed.
      const seeds = (it.key || []).map((k, i) => {
        const g = it.grader && it.grader.seeds && it.grader.seeds[i]
        const pr = p && p.seeds && p.seeds[i]
        const found = !!(g && g.found) && !!(pr && pr.found)
        const routed = found && !!(g && g.routed) && !!(pr && pr.routed)
        const src = found ? g : (pr && !pr.found ? pr : g)
        return { class: k.class, found, routed, matched_claim: src ? src.matched_claim : '',
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
