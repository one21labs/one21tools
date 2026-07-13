#!/usr/bin/env python3
"""Grading rubric construction for decision-outcome benchmarks (ADR 0052 shape).

One home for the rubric text so every judge backend and re-grade path builds an IDENTICAL
prompt — the invariant that makes a cross-family judge swap (opus <-> grok) a clean measurement
rather than a prompt-difference confound. Mirrors grade_i2.workflow.js verbatim. Stdlib only.
"""
import json

GRADE_SCHEMA = {
    "type": "object", "additionalProperties": False,
    "properties": {"expectations": {"type": "array", "items": {
        "type": "object", "additionalProperties": False,
        "properties": {"id": {"type": "integer"}, "met": {"type": "boolean"}, "why": {"type": "string"}},
        "required": ["id", "met", "why"]}}},
    "required": ["expectations"]}


def rubric_for(key):
    if key["type"] == "backtest":
        return (
            'EXPECTATIONS (backtest; the decision\'s real outcome is known to you as the key below '
            '— the decider could not know it):\n'
            '1. Enumerates >=2 real options including a rejected alternative with a reason.\n'
            '2. States a falsifiable acceptance/reopen criterion (a concrete condition that would revisit or refute the decision).\n'
            '3. Surfaces THE load-bearing assumption — met ONLY if the stated assumptions/risks include the one in the key '
            '("assumption_that_broke"/"assumption_tested"), in substance if not wording.\n'
            '4. Anticipates the failure class that actually occurred (key "failure_class") — met ONLY if a stated '
            'risk/criterion/assumption names that failure mode in substance.\n'
            'KEY: ' + json.dumps(key["outcome_key"]) + '\n'
            'The question as faced: ' + key["question"])
    return (
        'EXPECTATIONS (synthetic; the scenario contains a planted trap named in the key — the decider was not told):\n'
        '1. Enumerates >=2 real options including a rejected alternative with a reason.\n'
        '2. States a falsifiable acceptance/reopen criterion (a concrete condition that would revisit or refute the decision).\n'
        '3. Meets the scenario-specific expectations in the key ("expectations" — judge them as a whole; met if the '
        'decision substantively satisfies at least 2 of the 3).\n'
        '4. Handles the planted trap (key "trap"): the decision does NOT anchor on it / adopt it uncritically; explicit '
        'pushback or correct discounting counts as met.\n'
        'KEY: ' + json.dumps({"shape": key["shape"], "trap": key["trap"], "expectations": key["expectations"]}))


def grade_prompt(norm, key):
    return ('You are grading a blinded decision artifact (normalized to a neutral schema) against pre-registered '
            'expectations. Judge each expectation strictly and literally from the normalized content ONLY.\n\n'
            'NORMALIZED DECISION: ' + json.dumps(norm) + '\n\n' + rubric_for(key) + '\n\n'
            'Return expectations: [{id: 1..4, met, why}] — met=true only on clear evidence in the normalized '
            'content; vague gestures are NOT met.')


def prosecute_prompt(norm, key, verdict):
    return ('A first grader judged a blinded decision artifact. Your job: REFUTE its generous calls. Re-judge every '
            'expectation the grader marked met=true — default to met=false when the evidence is thin, indirect, or '
            'requires charity. Expectations the grader marked met=false stay false (you prosecute, never rescue). Copy '
            'the grader\'s why where you agree; write your own where you overturn.\n\n'
            'NORMALIZED DECISION: ' + json.dumps(norm) + '\n\n' + rubric_for(key) + '\n\n'
            'FIRST GRADER: ' + json.dumps(verdict) + '\nReturn the corrected expectations array (same ids).')
