#!/usr/bin/env python3
"""
Decision-logic tests for destructive_git.py. Run: python3 destructive_git_test.py
Invoked by ../test-destructive-git-guard.sh, which CI runs via .claude/hooks/test-*.sh.

EVERY CASE BELOW EXISTS BECAUSE SOMETHING GOT PAST. The predecessor guard was a single bash
regex over a `sed`-extracted string; a cross-family review (grok-4.5, 2026-07-27) walked through
it in one pass and found 27 holes. Each is now a named case, because the review also made the
sharper point: the old suite's PASSES were all consistent with the guard being `exit 0`
unconditionally. Allow-assertions cannot evidence a guard works -- only denies can -- so the
deny cases here are the load-bearing ones and `test_module_is_not_a_stub` guards the floor.

git state is INJECTED rather than built on disk: the interesting cases are about which worktree
gets asked, and a fixture can only ever be one tree.
"""
import json
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from destructive_git import decide, command_of, git_calls   # noqa: E402

PROJECT = "/repo"
DIRTY = {PROJECT: [" M wip.txt", "?? new.txt"]}
CLEAN = {}
STASHED = {PROJECT: ["stash@{0}: WIP on main: abc123 x"]}

passes, failures = 0, []


def check(label, condition):
    global passes
    if condition:
        passes += 1
        print(f"PASS: {label}")
    else:
        failures.append(label)
        print(f"FAIL: {label}")


def verdict(command, status=None, stash=None, project=PROJECT, raw=None):
    payload = raw if raw is not None else json.dumps(
        {"tool_name": "Bash", "tool_input": {"command": command}})
    status = DIRTY if status is None else status
    stash = {} if stash is None else stash
    return decide(payload, project, lambda d: status.get(d), lambda d: stash.get(d))


def denies(label, command, **kw):
    check(label, verdict(command, **kw) is not None)


def allows(label, command, **kw):
    check(label, verdict(command, **kw) is None)


# --- The floor. If this fails, no allow-assertion below means anything. ---------------------
def test_module_is_not_a_stub():
    check("a plainly destructive command on a dirty tree denies (stub floor)",
          verdict("git reset --hard HEAD~1") is not None)


# --- 1. Command forms that discard work. Each of these was ALLOWED by the regex version. ----
def test_bypass_forms_all_deny():
    for label, cmd in [
        ("flag after the revision", "git reset HEAD~1 --hard"),
        ("git -C at another repo", "git -C /repo reset --hard"),
        ("-c before the subcommand", "git -c core.pager=cat reset --hard"),
        ("--git-dir before the subcommand", "git --git-dir=/repo/.git reset --hard"),
        ("env assignment prefix", "FOO=1 git reset --hard"),
        ("sudo prefix", "sudo git reset --hard"),
        ("absolute path to git", "/usr/bin/git reset --hard"),
        ("env wrapper", "env git reset --hard"),
        ("sh -c re-exec", "sh -c 'git reset --hard HEAD~1'"),
        ("bash -lc re-exec", 'bash -lc "git reset --hard"'),
        ("command substitution", "echo $(git reset --hard)"),
        ("backtick substitution", "echo `git reset --hard`"),
        ("xargs", "xargs git reset --hard"),
        ("eval", "eval git reset --hard"),
        ("checkout dot", "git checkout ."),
        ("checkout double-dash path", "git checkout -- file.txt"),
        ("checkout tree-ish then path", "git checkout HEAD -- file.txt"),
        ("bare restore is worktree by default", "git restore file.txt"),
        ("restore -W", "git restore -W file.txt"),
        ("switch --force", "git switch -f main"),
        ("switch --discard-changes", "git switch --discard-changes"),
        ("clean with -f not first", "git clean -d -f"),
        ("clean force cluster reordered", "git clean -xdf"),
        ("read-tree -u --reset", "git read-tree -u --reset HEAD"),
        ("submodule foreach carrying a reset", "git submodule foreach --recursive git reset --hard"),
        ("chained after another command", "cd /repo && git reset --hard HEAD~1"),
        # Second cross-family pass, after the rewrite. All four were ALLOWED by it.
        ("checkout of a path with no -- separator", "git checkout HEAD wip.txt"),
        ("checkout-index materialises over the worktree", "git checkout-index -f -a"),
        ("a quoted `<<` inside a string must not truncate the real command",
         'echo "use <<EOF to start" && git reset --hard'),
        ("an unterminated heredoc marker must not swallow what follows",
         "cat <<EOF && git reset --hard"),
    ]:
        denies(label, cmd)


# --- 2. The JSON extraction. The `sed` version failed open on every one of these. ------------
def test_json_extraction_cannot_be_used_as_a_bypass():
    # THE one that mattered: a quote anywhere in the command emptied the old extraction.
    raw = json.dumps({"tool_name": "Bash",
                      "tool_input": {"command": 'echo "x"; git reset --hard HEAD~1'}})
    check("an escaped quote in the command does not blind the guard",
          verdict(None, raw=raw) is not None)
    cmd, ok = command_of(raw)
    check("the parsed command survives the quote intact", ok and cmd.endswith("HEAD~1"))

    # A trailing sibling field named `command` won the old greedy match.
    raw = ('{"tool_name":"Bash","tool_input":{"command":"git reset --hard"},'
           '"command":"echo safe"}')
    check("a sibling `command` field does not shadow tool_input.command",
          verdict(None, raw=raw) is not None)

    raw = json.dumps({"tool_name": "Bash",
                      "tool_input": {"command": "git reset \\\n --hard"}})
    check("a line continuation inside the command still matches", verdict(None, raw=raw) is not None)

    raw = json.dumps({"tool_name": "Bash",
                      "tool_input": {"command": ["git", "reset", "--hard"]}})
    check("an argv-array command is joined, not skipped", verdict(None, raw=raw) is not None)

    # Unparseable input must not read as "nothing destructive here".
    check("malformed JSON falls back to scanning the raw text, not to allow",
          verdict(None, raw='{"tool_input": {"command": "git reset --hard"') is not None)

    check("a non-Bash tool is not this guard's business",
          verdict(None, raw=json.dumps({"tool_name": "Write",
                                        "tool_input": {"command": "git reset --hard"}})) is None)


# --- 3. WHICH tree gets asked. The regex version always asked the project dir. ---------------
def test_the_predicate_follows_the_command_not_the_project():
    other = "/other"
    denies("cd elsewhere then reset denies on THAT tree's dirt",
           f"cd {other} && git reset --hard", status={other: [" M their-wip.txt"]})
    allows("cd elsewhere then reset allows when THAT tree is clean, though the project is dirty",
           f"cd {other} && git reset --hard", status=DIRTY)
    denies("git -C picks the target tree", f"git -C {other} reset --hard",
           status={other: [" M their-wip.txt"]})
    allows("git -C at a clean tree allows while the project is dirty",
           f"git -C {other} reset --hard", status=DIRTY)
    check("the deny names the tree it actually checked",
          other in (verdict(f"cd {other} && git reset --hard",
                            status={other: [" M their-wip.txt"]}) or ""))


# --- 4. Denying the harmless is how a guard gets disabled. -----------------------------------
def test_it_does_not_cry_wolf():
    allows("stash drop with an EMPTY stash discards nothing", "git stash drop", stash={})
    allows("stash clear with an empty stash discards nothing", "git stash clear", stash={})
    allows("clean --dry-run deletes nothing", "git clean -f --dry-run")
    allows("clean -n deletes nothing", "git clean -f -n")
    allows("--hardcore is not --hard", "git reset --hardcore")
    allows("dropdown is not drop", "git stash dropdown", stash=STASHED)
    allows("restore --staged leaves the worktree alone", "git restore --staged file.txt")
    allows("a mention inside a grep pattern is not an invocation",
           "grep -r 'git reset --hard' docs")
    # Caught on this guard's FIRST real use: it denied the commit that was fixing it, because the
    # message documented the bypasses. Writing about a command is not running it.
    allows("a commit message quoting the command is data, not an invocation",
           'git commit -m "closed the hole where echo \\"x\\" && git reset --hard slipped past"')
    allows("a heredoc body is data the shell feeds to a program",
           "git commit -F - <<'EOF'\nfixed: sh -c 'git reset --hard' walked past the anchor\nEOF")
    allows("a heredoc body cannot hide behind && either",
           "git commit -F - <<'EOF'\na && git reset --hard b\nEOF")
    denies("a real command AFTER a heredoc still counts",
           "git commit -F - <<'EOF'\nnotes\nEOF\ngit reset --hard")
    for label, cmd in [("reset --soft", "git reset --soft HEAD~1"),
                       ("plain reset", "git reset HEAD~1"),
                       ("status", "git status"),
                       ("commit", "git commit -m x"),
                       ("stash push SAVES work", "git stash push -m wip"),
                       ("stash pop RESTORES work", "git stash pop")]:
        allows(f"{label} must be allowed", cmd)
    allows("a clean tree has nothing to lose", "git reset --hard HEAD~1", status=CLEAN)
    allows("clean -fd on a clean tree", "git clean -fd", status=CLEAN)
    check("an unreadable tree allows rather than blocking every checkout",
          decide(json.dumps({"tool_name": "Bash", "tool_input": {"command": "git reset --hard"}}),
                 PROJECT, lambda d: None, lambda d: None) is None)


# --- 5. stash drop is about STASH ENTRIES. The old guard keyed it to worktree dirt, and the
# old test asserted that mistake as correct -- so fixing the product would have failed CI. ----
def test_stash_uses_the_stash_predicate():
    allows("a dirty worktree is not a reason to block stash drop",
           "git stash drop", status=DIRTY, stash={})
    denies("a non-empty stash IS a reason to block stash drop",
           "git stash drop", status=CLEAN, stash=STASHED)
    reason = verdict("git stash drop", status=CLEAN, stash=STASHED) or ""
    check("the stash deny talks about stash entries, not worktree paths",
          "stash" in reason and "wip.txt" not in reason)


# --- 6. The deny must PRESCRIBE and must be derived, not hardcoded (house standard). ---------
def test_the_deny_prescribes_from_real_state():
    unique = "zz-unique-fixture-9f3a.txt"
    reason = verdict("git reset --hard HEAD~1", status={PROJECT: [f" M {unique}"]}) or ""
    check("the deny names the non-destructive alternative", "reset --soft" in reason)
    check("the deny names what would actually be lost, read from the tree", unique in reason)
    check("the deny names the verb it matched", "reset --hard" in reason)


def test_parsing_is_bounded():
    check("a pathological nest terminates", isinstance(git_calls("$(" * 50, PROJECT), list))
    check("an unlexable segment is still scanned",
          verdict("git reset --hard 'unclosed") is not None)


for fn in [v for k, v in sorted(globals().items()) if k.startswith("test_")]:
    fn()

print(f"\n{passes} passed, {len(failures)} failed")
if failures:
    print("failed: " + "; ".join(failures))
sys.exit(1 if failures else 0)
