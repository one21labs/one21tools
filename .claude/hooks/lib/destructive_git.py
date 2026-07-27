#!/usr/bin/env python3
"""
Decision logic for ../destructive-git-guard.sh. Pure: runs nothing, reads nothing.

WHY THIS IS NOT BASH ANY MORE. The first version did the whole job in one regex over a
`sed`-extracted command string. A cross-family review (grok-4.5, 2026-07-27) found 27 ways past
it in a single pass. The two worst were not exotic:

  * `sed -n 's/.*"command"[^"]*"\\([^"]*\\)".*/\\1/p'` stops at the first raw quote, so ANY
    command containing one -- `echo "x"; git reset --hard HEAD~1` -- extracted as `echo \\` and
    the guard ALLOWED it. Every test in the suite was quote-free, so nothing caught it. That is
    the whole guard defeated by a character the agent types constantly.
  * `git stash drop` was denied whenever the WORKTREE was dirty. Dropping a stash entry cannot
    touch the worktree, so the predicate was simply wrong -- and the test suite asserted the
    wrong behaviour as correct, meaning a proper fix would have turned CI red.

Both are shapes bash makes easy and a parser makes hard. So parsing and deciding live here,
where they take inputs and return values and a test can drive them; the shell keeps only I/O.

THE PREDICATE STAYS MECHANICAL. "Is the worktree that this command will actually touch dirty"
is a fact git answers. Every guard in this repo that asked the agent to classify its own
situation has been evaded; the ones keyed on a countable fact have not.

FAIL-CLOSED, NARROWLY. Unparseable stdin does not mean "allow" -- it means the guard could not
see, and for THIS risk class the raw text is scanned instead. Absent machinery (no python3, no
git) still fails open, like every sibling guard: an unreadable environment must not become a
blanket block on git.

TESTING: destructive_git_test.py, invoked by ../test-destructive-git-guard.sh (which CI runs).
"""
import json
import os
import re
import shlex
import sys

# Wrappers that take a command as their tail. `git` hiding behind one of these is still `git`.
WRAPPERS = {"sudo", "doas", "env", "command", "nice", "ionice", "nohup", "stdbuf", "time",
            "xargs", "eval", "exec", "builtin"}
SHELLS = {"sh", "bash", "zsh", "dash", "ksh", "busybox"}
# git's own global options, before the subcommand. Those taking a separate argument matter:
# skipping the option without skipping its value would read the value as the subcommand.
GLOBAL_WITH_VALUE = {"-C", "-c", "--git-dir", "--work-tree", "--namespace", "--exec-path",
                     "--super-prefix"}
SEPARATORS = re.compile(r"&&|\|\||[;\n|]")
NESTED = re.compile(r"\$\(([^()]*)\)|`([^`]*)`")
# git clean's short flags. Bounded on purpose: an unbounded `-[a-z]*f` cluster also matches
# `-foobar`, and a guard that denies a command git itself would reject is a guard people route
# around -- the failure mode that ends with the hook disabled.
CLEAN_CLUSTER = re.compile(r"-[dfiqxXne]*f[dfiqxXne]*$")


def command_of(stdin_text):
    """(command, saw_valid_json). A list-valued command joins to argv; a missing one is empty.

    On unparseable input the RAW TEXT is returned as the command, so the destructive-verb scan
    still has something to match. Returning "" there would make malformed JSON a bypass valve.
    """
    try:
        doc = json.loads(stdin_text)
    except Exception:
        return (stdin_text, False)
    if not isinstance(doc, dict):
        return (stdin_text, False)
    tool_input = doc.get("tool_input")
    if not isinstance(tool_input, dict):
        return ("", True)
    cmd = tool_input.get("command")
    if cmd is None:
        return ("", True)
    if isinstance(cmd, list):
        return (" ".join(str(x) for x in cmd), True)
    if not isinstance(cmd, str):
        return (str(cmd), False)
    return (cmd, True)


def tool_of(stdin_text):
    """The tool name, or "" when it cannot be read."""
    try:
        doc = json.loads(stdin_text)
        return str(doc.get("tool_name") or "") if isinstance(doc, dict) else ""
    except Exception:
        return ""


HEREDOC = re.compile(r"<<-?\s*(['\"]?)(\w+)\1")


def strip_heredocs(text):
    """Remove heredoc bodies. They are DATA the shell feeds to a program, never commands.

    Caught on this guard's first real use: a commit whose MESSAGE quoted `git reset --hard`
    (documenting a bypass, in the very commit fixing it) was denied. A guard that blocks writing
    about a command is the cry-wolf failure that ends with the guard switched off.
    """
    for _ in range(16):                                      # bounded; nested heredocs are rare
        m = HEREDOC.search(text)
        if not m:
            return text
        newline = text.find("\n", m.end())
        closer = None if newline == -1 else re.search(
            rf"^[ \t]*{re.escape(m.group(2))}[ \t]*$", text[newline + 1:], re.M)
        if closer is None:
            # NO OPENER WE CAN TRUST. `echo "use <<EOF to start" && git reset --hard` matches the
            # pattern inside a quoted string; truncating there would drop the real destructive
            # command that follows and ALLOW it. An unmatched `<<` is left alone -- the worst case
            # is scanning text that was data, which can only over-match, and over-matching still
            # has to get past the dirty-tree predicate.
            return text
        text = text[:m.start()] + text[newline + 1 + closer.end():]
    return text


def split_segments(text):
    """Command segments, with quoting respected.

    A plain split on `&&`/`;`/`|` also splits INSIDE a quoted argument, so
    `git commit -m "fixed by git reset --hard"` looked like a real reset. shlex with
    punctuation_chars emits the operators as their own tokens and leaves quoted runs whole.
    """
    try:
        lex = shlex.shlex(text, posix=True, punctuation_chars=True)
        lex.whitespace_split = True
        tokens = list(lex)
    except ValueError:
        return [seg.split() for seg in SEPARATORS.split(text)]
    segments, current = [], []
    for token in tokens:
        if token in ("&&", "||", ";", "|", "&", ";;", "\n"):
            segments.append(current)
            current = []
        else:
            current.append(token)
    segments.append(current)
    return segments


def _tokens(segment):
    """shlex where possible, whitespace where not. An unlexable segment must still be scanned."""
    try:
        return shlex.split(segment)
    except ValueError:
        return segment.split()


def _strip_prefix(tokens):
    """Drop `VAR=val` assignments, wrapper commands, and the wrappers' own flags."""
    i = 0
    while i < len(tokens):
        tok = tokens[i]
        if re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*=.*", tok):
            i += 1
        elif os.path.basename(tok) in WRAPPERS:
            i += 1
            while i < len(tokens) and tokens[i].startswith("-"):
                i += 1
        else:
            break
    return tokens[i:]


def _inner_commands(tokens):
    """Command strings nested inside this one: `sh -c '...'` and friends."""
    if not tokens or os.path.basename(tokens[0]) not in SHELLS:
        return []
    for i, tok in enumerate(tokens):
        # -c, and clusters like -lc / -ec that end in c.
        if tok == "-c" or (tok.startswith("-") and not tok.startswith("--") and tok.endswith("c")):
            if i + 1 < len(tokens):
                return [tokens[i + 1]]
    return []


def _split_globals(argv):
    """(worktree_override, subcommand_argv) for git's args, after skipping global options."""
    override, i = None, 0
    while i < len(argv):
        tok = argv[i]
        if tok in ("-C", "--work-tree") and i + 1 < len(argv):
            override = argv[i + 1]
            i += 2
        elif tok.startswith("--work-tree="):
            override = tok.split("=", 1)[1]
            i += 1
        elif tok in GLOBAL_WITH_VALUE:
            i += 2
        elif tok.startswith("--") and "=" in tok:
            i += 1
        elif tok.startswith("-") and tok not in ("--",):
            i += 1
        else:
            break
    return (override, argv[i:])


def _destructive(argv):
    """(kind, verb) for a git subcommand argv, or (None, None).

    kind is "worktree" when the command can discard uncommitted changes, or "stash" when it
    discards stash entries -- a DIFFERENT thing needing a different predicate. Conflating the two
    is exactly what made the first version deny `git stash drop` over an unrelated dirty file.
    """
    if not argv:
        return (None, None)
    verb, rest = argv[0], argv[1:]
    has = lambda *names: any(t in names for t in rest)      # noqa: E731 - full-token match only

    if verb == "reset":
        return ("worktree", "reset --hard") if has("--hard", "--merge") else (None, None)
    if verb == "clean":
        if has("-n", "--dry-run"):
            return (None, None)                              # deletes nothing; denying it lies
        forced = has("--force") or any(CLEAN_CLUSTER.fullmatch(t) for t in rest)
        return ("worktree", "clean --force") if forced else (None, None)
    if verb == "checkout":
        # `checkout -- <path>`, `checkout .`, `checkout <tree> -- <path>` all overwrite files --
        # and so does `git checkout HEAD wip.txt`, with no `--` anywhere. Two or more non-option
        # arguments means a tree-ish plus a pathspec, which is a worktree overwrite whatever the
        # separator. A single argument is an ordinary branch switch and stays allowed.
        args = [t for t in rest if not t.startswith("-")]
        if has("-f", "--force") or has("--") or (rest and rest[0] == ".") or len(args) >= 2:
            return ("worktree", "checkout")
        return (None, None)
    if verb == "checkout-index":
        return ("worktree", "checkout-index") if has("-f", "--force", "-a", "--all", "-u") else (None, None)
    if verb == "restore":
        # The DEFAULT target is the worktree. Only --staged alone leaves files untouched.
        staged_only = has("--staged", "-S") and not has("--worktree", "-W")
        return (None, None) if staged_only else ("worktree", "restore")
    if verb == "switch":
        return ("worktree", "switch --force") if has("-f", "--force", "--discard-changes") else (None, None)
    if verb == "read-tree":
        return ("worktree", "read-tree -u --reset") if has("-u") and has("--reset") else (None, None)
    if verb == "stash":
        return ("stash", f"stash {rest[0]}") if rest and rest[0] in ("drop", "clear") else (None, None)
    return (None, None)


def git_calls(command, project_dir):
    """Every git invocation in the command, as {"kind","verb","worktree"}.

    `cd` in an earlier segment moves the worktree for later ones, so segments are walked in
    order. Nested `sh -c '...'`, `$(...)` and backticks are re-scanned: the first version anchored
    on git being at the start of a segment, and `sh -c 'git reset --hard'` walked straight past.
    """
    found, cwd = [], project_dir
    pending = [command]
    seen = 0
    while pending and seen < 64:                             # bounded: no runaway on odd input
        # A backslash-newline is a line continuation, not a statement break. Splitting on the
        # newline first would leave `git reset \` in one segment and `--hard` in the next, and
        # the destructive flag would never be seen next to its verb.
        current = re.sub(r"\\[ \t]*\n", " ", strip_heredocs(pending.pop(0)))
        seen += 1
        for match in NESTED.finditer(current):
            pending.append(match.group(1) or match.group(2) or "")
        for raw in split_segments(NESTED.sub(" ", current)):
            tokens = _strip_prefix(raw)
            if not tokens:
                continue
            pending.extend(_inner_commands(tokens))
            if os.path.basename(tokens[0]) == "cd" and len(tokens) > 1:
                cwd = tokens[1] if os.path.isabs(tokens[1]) else os.path.join(cwd, tokens[1])
                continue
            if os.path.basename(tokens[0]) != "git":
                continue
            argv = tokens[1:]
            # `git submodule foreach ... git reset --hard`: the payload git is another call.
            for i, tok in enumerate(argv):
                if i > 0 and os.path.basename(tok) == "git":
                    pending.append(" ".join(argv[i:]))
                    argv = argv[:i]
                    break
            override, sub = _split_globals(argv)
            kind, verb = _destructive(sub)
            if not kind:
                continue
            target = override or cwd
            if not os.path.isabs(target):
                target = os.path.join(cwd, target)
            found.append({"kind": kind, "verb": verb, "worktree": os.path.normpath(target)})
    return found


def decide(stdin_text, project_dir, status_fn, stash_fn):
    """None to allow, or the deny reason.

    status_fn(dir) -> list of `git status --porcelain` lines for that worktree.
    stash_fn(dir)  -> list of `git stash list` lines.
    Either may return None to mean "cannot tell", which ALLOWS: a guard that blocks when it
    cannot see the tree is a guard that blocks in every fresh checkout.
    """
    tool = tool_of(stdin_text)
    if tool and tool != "Bash":
        return None
    command, parsed = command_of(stdin_text)
    if not command.strip():
        return None
    if parsed:
        calls = git_calls(command, project_dir)
    else:
        # FAIL-CLOSED SCAN. `command` is the raw payload, so git is buried in JSON punctuation and
        # is never the first token of anything. Strip the punctuation and re-read from each `git`
        # onward. Over-matching here is the safe direction: the dirty-tree predicate still has to
        # agree before anything is denied.
        scrubbed = re.sub(r"[{}\[\]\",:]", " ", command)
        calls = []
        for tail in re.split(r"\bgit\b", scrubbed)[1:]:
            calls.extend(git_calls("git " + tail, project_dir))
    for call in calls:
        if call["kind"] == "worktree":
            dirty = status_fn(call["worktree"])
            if not dirty:
                continue                                     # nothing uncommitted: nothing to lose
            sample = " ".join(dirty[:5])
            return (f"Denied: `{call['verb']}` discards uncommitted work and {call['worktree']} is "
                    f"NOT clean -- {len(dirty)} path(s) would be lost, e.g. {sample}. If the goal "
                    f"is to undo a COMMIT, use `git reset --soft HEAD~1` (keeps everything staged) "
                    f"or `git reset HEAD~1` (keeps the working tree); both undo the commit without "
                    f"touching your files. If you genuinely mean to discard, commit or stash first "
                    f"so it is recoverable, then re-run. Scar: 60 lines of a security-hook fix were "
                    f"lost this way on 2026-07-27, and the commit that followed would have claimed "
                    f"fixes it no longer contained.")
        if call["kind"] == "stash":
            entries = stash_fn(call["worktree"])
            if not entries:
                continue                                     # no stash: nothing to drop
            return (f"Denied: `{call['verb']}` discards {len(entries)} stash entr(y/ies) in "
                    f"{call['worktree']}, and a dropped stash is not in the reflog by name. Run "
                    f"`git stash list` to see them, `git stash show -p stash@{{0}}` to read one, and "
                    f"`git stash pop` to restore rather than delete. If you truly want it gone, "
                    f"apply it first so the content is in the tree, then re-run.")
    return None


def _git_lines(directory, *args):
    """Real git state, or None when the directory is not a readable repo (-> allow)."""
    import subprocess
    try:
        out = subprocess.run(["git", "-C", directory, *args], capture_output=True, text=True,
                             timeout=10)
    except Exception:
        return None
    if out.returncode != 0:
        return None
    return [line for line in out.stdout.splitlines() if line.strip()]


if __name__ == "__main__":
    # The shell shim pipes the hook payload here and prints whatever comes back. Emitting the
    # WHOLE response as JSON from python is deliberate: the predecessor built the response by
    # string-concatenating a reason into a JSON literal and stripping quotes out of it to keep
    # that legal, which is the same class of bug as the sed extraction it also used.
    project = sys.argv[1] if len(sys.argv) > 1 else os.getcwd()
    why = decide(sys.stdin.read(), os.path.abspath(project),
                 lambda d: _git_lines(d, "status", "--porcelain"),
                 lambda d: _git_lines(d, "stash", "list"))
    if why:
        print(json.dumps({"hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": why}}))

