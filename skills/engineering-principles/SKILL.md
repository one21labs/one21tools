---
name: engineering-principles
description: Use when planning or breaking down work, reviewing a design, analysing an incident or a recurring problem, or changing a value or rule that lives in more than one place. Four working rules that hold up under schedule pressure.
---

# Engineering principles

Four rules that change what gets built. Each matters most when someone is in a hurry or says the
question is already settled, because that is when it gets skipped.

## Approved is not the same as complete

When you are handed a plan that has "already been approved", check that it says what is in scope,
what the output or interface looks like, and how anyone will know it worked. If it does not, list
those gaps and put the tasks that close them ahead of the build tasks. Do not quietly pick a
format, a scope or a performance target yourself. Approval covers what the plan says, and a
silent choice ships a guess under someone else's sign-off.

## A person's mistake is not a root cause

When something failed because someone skipped a step or ran the wrong command, keep asking why
the system let that happen: why the step was manual, why nothing noticed the bad result. There is
usually more than one chain, so follow each. Fix the mechanism (a check in the pipeline, an alert
that reaches someone, a permission that should not exist) and not the person. Training and
reminders fail the same way next time. For each fix, say how the team will confirm it works, such
as injecting the failure and watching the alert fire.

## One definition per fact

A value or a rule is defined in one place, and everything else reads it or points to it. This
holds under time pressure too. Asked to update a value that is hardcoded in several files, define
it once and have the others use it, because the copies are what made the update risky. Keep that
change small, and leave unrelated improvements out of an urgent fix.

The same goes for documents. Pick the one home for each fact (the code, when the code enforces
it) and replace every other copy with a pointer. A copy "kept in sync" drifts. History belongs in
version control, not in the document.

## Time already spent is not a reason to finish

Scope the remaining work to the requirement that exists. If half-built generality goes beyond it,
such as extra formats, a plugin layer, or a framework for cases nobody has asked for, recommend
stopping and removing it. Do not schedule its completion or leave it dormant "for later". Say
plainly that the effort already spent does not change what is needed.
