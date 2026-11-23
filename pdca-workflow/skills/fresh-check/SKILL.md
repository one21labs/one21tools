---
name: fresh-check
description: Use when work is about to ship or be relied on and being wrong would be costly, such as a fix claimed to work, a design about to be accepted, or a change that is hard to reverse. A reviewer with no stake reproduces the claims and tries to break the work.
---

# Fresh check

Have a reviewer with no stake in the work check it before it ships.

The author of a change knows what it is supposed to do and reads it that way. A reviewer who
starts from the artifact alone reads what it actually does. That difference is the whole value,
so most of the steps below are about keeping the reviewer independent.

Use this when the result ships, is hard to undo, or other people will depend on it. Skip it for
small reversible changes, where your own tests are enough.

## Steps

1. List what must be true for the work to be right: each claim, and where it can be observed (a
   file, a command, an output). "The bug is fixed" becomes "running X on input Y now prints Z".
2. Start one fresh subagent as the reviewer. Give it the artifact (the diff, the document, the
   paths) and the claims. Do not give it your reasoning, your confidence, or what earlier checks
   found. A reviewer told what to conclude tends to conclude it.
3. Ask it to do two things, in this order:
   - Reproduce each claim against the real code and the real output. It should run the command
     and read the result, not infer from the source. It reports every claim as confirmed,
     refuted or could-not-check, with the file and line or the output as evidence.
   - Try to break the work: edge inputs (empty, boundary, oversized, malformed), assumptions that
     might be false, and any path where it produces a wrong result that looks right. It reports
     the most serious break first, with the smallest change that would close it.
4. Tell it to report only what it verified, and that "found nothing" is an acceptable answer.
   Without that, reviewers invent findings to seem useful.

## Using the result

- Check each finding yourself before acting on it, because reviewers are sometimes confidently
  wrong. Then fix the work, or answer the finding with evidence. A finding that is neither fixed
  nor answered means the work is not ready.
- A fix is new work that no reviewer has seen. After a substantial fix, run the check again with
  a new reviewer, and stop at the first round that changes nothing.
- A claim the reviewer could not check (no network, no way to run it) is unchecked, not passed.
- A reviewer that returns nothing checked nothing. Run it once more. If it fails again, report
  the work as unchecked.
- A reviewer running on the same model as the author shares its blind spots. This check does not
  cover claims about facts outside the repository or about the model's own judgment, so say so
  when the work rests on one.

If you cannot start subagents here, there is no independent reviewer to be had. Re-running the
claims yourself is still worth doing, but report it as a self-check, not as this check.

Tell the person what was checked, what was found and fixed, and what remains unchecked.
