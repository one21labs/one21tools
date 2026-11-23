---
name: advise
description: Use when weighing a contested judgment call, such as a design, scope, threshold or sequencing decision with a real trade-off, before acting on it. Gets two independent opposing views and reports what they changed.
---

# Advise

Get two independent views on a decision that has a real trade-off, before you commit to it.

Measured against one careful pass by a single agent, independent advisors did not choose better
options. They were better at anticipating how the chosen option would fail. So use this where
being wrong is expensive, and skip it for routine calls: it costs two extra agents.

If the decision turns on what a person prefers (a name, wording, appetite for risk) and they can
be asked, ask them. Advisors cannot settle a preference.

## Steps

1. Write the question as one sentence, with the options you see. A vague question gets vague
   advice and points the advisors at the wrong thing.
2. State your own answer before anyone else weighs in: "My pick: <option>, which depends on
   <assumption>." Saying it first gives you something to compare against. A pick you only hold in
   your head gets quietly rewritten by the advice.
3. Start two advisors at the same time, as fresh subagents, each arguing a different side as
   strongly as the facts allow. If the project defines its own advisor agents, choose the two
   most likely to disagree. Give each the question and the files it needs. Do not give them your
   pick or any hint of the answer you hope for, because an advisor who knows the preferred answer
   tends to return it.
4. Ask each for three things: a recommendation; the cost, risk and value behind it, grounded in
   the actual code or output with file and line; and the one assumption the recommendation
   depends on.
5. Set the advisors' model when you start them. Left unset they inherit the session's model,
   which usually costs more than this needs.

## Report

Give the person both recommendations as returned. Then say in one line what they did to your
pick: changed it, added a risk you will now act on, or nothing. You decide; the advisors advise.

If both advisors agree, treat that as a sign the question may be framed wrong: there may be no
real trade-off, or both may have missed the same thing. Say so; do not report agreement as
confirmation.

An advisor that returns nothing (a crash, a timeout, a usage limit) gave no advice. Run it again
once. If it fails again, say that side went unheard.

If you cannot start subagents here, do not argue both sides yourself. In measurement one agent
arguing with itself anticipated failures worse than an agent that did not try. Tell the person
that independent views were not available, and decide the ordinary way.
