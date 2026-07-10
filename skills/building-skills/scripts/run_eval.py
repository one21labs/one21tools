#!/usr/bin/env python3
"""Run trigger evaluation for a skill description.

Tests whether a skill's description causes Claude to trigger (read the skill)
for a set of queries. Outputs results as JSON.

VENDORED from anthropics/skills (skill-creator/scripts/run_eval.py), clone dated 2026-07-09
(ADR 0033), plus:
  1. Five correctness fixes, each marked `# VENDORED (fix N of 5)` at its site. Fixes 1-3 are
     the stream patches (one21labs/one21tools:benchmarks/2026-07-07-toolkit-grid/trigger-kit/runner-patches.diff;
     filing them upstream is DEFERRED pending owner approval to post externally) -- unpatched,
     the stream loop hard-fails detection on the first non-Skill/Read tool call and closes the
     detection window at the first content_block_stop/message_stop, producing WRONG trigger
     counts: (1) an unrelated tool call no longer ends the run -- keep watching for a later
     Skill/Read; (2) the child no longer inherits/waits on the parent's stdin
     (`stdin=subprocess.DEVNULL`); (3) a non-matching completed tool block resets and keeps
     watching instead of returning. Fix (4) is TIMEOUT-AS-NULL: a query run that times out
     records None -- excluded from trigger_rate's denominator and from pass/fail, surfaced as a
     `timeouts` count per query and in the summary -- never a False (upstream scored a timeout
     as not-triggered, silently deflating rates under load). Fix (5) applies fixes 1+3 to the
     full-assistant-message FALLBACK branch too (issue #104): an unrelated tool_use no longer
     returns a terminal verdict -- only a positive match ends detection early.
  2. Pure, subprocess-free extractions so the fixed behavior is unit-testable
     (run_eval_test.py) without spawning `claude -p`: the per-line stream detection into
     `detect_trigger_line()`, the per-query/summary aggregation into `summarize_query()` /
     `summarize_results()`. `run_single_query()`/`run_eval()` call them with control flow
     otherwise unchanged.
  3. `parse_skill_md` vendored inline from skill-creator/scripts/utils.py -- this file has no
     package-relative import and runs standalone: `python3 run_eval.py ...`.

Linux/WSL-only (select.select() on a subprocess pipe fd; no Windows equivalent). See
skills/building-skills/references/description-ablation.md for the run protocol.
"""

import argparse
import json
import os
import select
import subprocess
import sys
import time
import uuid
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path
from typing import NamedTuple


# VENDORED: minimal inline copy of skill-creator/scripts/utils.py:parse_skill_md, so this file
# needs no `scripts.utils` package-relative import and runs as a standalone script.
def parse_skill_md(skill_path: Path) -> tuple[str, str, str]:
    """Parse a SKILL.md file, returning (name, description, full_content)."""
    content = (skill_path / "SKILL.md").read_text()
    lines = content.split("\n")

    if lines[0].strip() != "---":
        raise ValueError("SKILL.md missing frontmatter (no opening ---)")

    end_idx = None
    for i, line in enumerate(lines[1:], start=1):
        if line.strip() == "---":
            end_idx = i
            break

    if end_idx is None:
        raise ValueError("SKILL.md missing frontmatter (no closing ---)")

    name = ""
    description = ""
    frontmatter_lines = lines[1:end_idx]
    i = 0
    while i < len(frontmatter_lines):
        line = frontmatter_lines[i]
        if line.startswith("name:"):
            name = line[len("name:"):].strip().strip('"').strip("'")
        elif line.startswith("description:"):
            value = line[len("description:"):].strip()
            # Handle YAML multiline indicators (>, |, >-, |-)
            if value in (">", "|", ">-", "|-"):
                continuation_lines: list[str] = []
                i += 1
                while i < len(frontmatter_lines) and (frontmatter_lines[i].startswith("  ") or frontmatter_lines[i].startswith("\t")):
                    continuation_lines.append(frontmatter_lines[i].strip())
                    i += 1
                description = " ".join(continuation_lines)
                continue
            else:
                description = value.strip('"').strip("'")
        i += 1

    return name, description, content


def find_project_root() -> Path:
    """Find the project root by walking up from cwd looking for .claude/.

    Mimics how Claude Code discovers its project root, so the command file
    we create ends up where claude -p will look for it.
    """
    current = Path.cwd()
    for parent in [current, *current.parents]:
        if (parent / ".claude").is_dir():
            return parent
    return current


class DetectState(NamedTuple):
    """Trigger-detection state threaded across detect_trigger_line() calls (VENDORED: extracted
    so the patched stream-detection logic is a pure, unit-testable function)."""
    pending_tool_name: str | None
    accumulated_json: str
    triggered: bool


def detect_trigger_line(
    line: str, clean_name: str, state: DetectState
) -> tuple[DetectState, bool | None]:
    """VENDORED: the per-line trigger-detection step extracted from run_single_query's stream
    loop, byte-faithful to its logic (including stream fixes 1 and 3, see module docstring)
    so it can be unit-tested without spawning `claude -p`. Returns (next_state, verdict):
    verdict is None to keep reading more lines, or True/False when the caller should return
    immediately -- callers must thread next_state back into the next call.
    """
    line = line.strip()
    if not line:
        return state, None

    try:
        event = json.loads(line)
    except json.JSONDecodeError:
        return state, None

    pending_tool_name = state.pending_tool_name
    accumulated_json = state.accumulated_json

    # Early detection via stream events
    if event.get("type") == "stream_event":
        se = event.get("event", {})
        se_type = se.get("type", "")

        if se_type == "content_block_start":
            cb = se.get("content_block", {})
            if cb.get("type") == "tool_use":
                tool_name = cb.get("name", "")
                if tool_name in ("Skill", "Read"):
                    pending_tool_name = tool_name
                    accumulated_json = ""
                # VENDORED (fix 1 of 5): an unrelated tool call no longer ends the run; keep
                # watching for a later Skill/Read (upstream hard-failed here with `return False`).

        elif se_type == "content_block_delta" and pending_tool_name:
            delta = se.get("delta", {})
            if delta.get("type") == "input_json_delta":
                accumulated_json += delta.get("partial_json", "")
                if clean_name in accumulated_json:
                    return DetectState(pending_tool_name, accumulated_json, state.triggered), True

        elif se_type in ("content_block_stop", "message_stop"):
            if pending_tool_name:
                if clean_name in accumulated_json:
                    return DetectState(pending_tool_name, accumulated_json, state.triggered), True
                # VENDORED (fix 3 of 5): a non-matching completed tool block resets and keeps
                # watching, instead of upstream's unconditional `return clean_name in
                # accumulated_json` (content_block_stop) / `return False` (message_stop).
                pending_tool_name = None
                accumulated_json = ""

        return DetectState(pending_tool_name, accumulated_json, state.triggered), None

    # Fallback: full assistant message
    if event.get("type") == "assistant":
        message = event.get("message", {})
        for content_item in message.get("content", []):
            if content_item.get("type") != "tool_use":
                continue
            tool_name = content_item.get("name", "")
            tool_input = content_item.get("input", {})
            if tool_name == "Skill" and clean_name in tool_input.get("skill", ""):
                return DetectState(pending_tool_name, accumulated_json, True), True
            if tool_name == "Read" and clean_name in tool_input.get("file_path", ""):
                return DetectState(pending_tool_name, accumulated_json, True), True
            # VENDORED (fix 5 of 5): an unrelated tool_use keeps watching -- scan the rest of
            # this message and later lines (pre-fix, the branch returned a terminal verdict at
            # the FIRST tool_use, scoring exploration-first sessions False; issue #104).
        return state, None

    if event.get("type") == "result":
        return state, state.triggered

    return state, None


def run_single_query(
    query: str,
    skill_name: str,
    skill_description: str,
    timeout: int,
    project_root: str,
    model: str | None = None,
) -> bool | None:
    """Run a single query and return whether the skill was triggered.

    Creates a command file in .claude/commands/ so it appears in Claude's
    available_skills list, then runs `claude -p` with the raw query.
    Uses --include-partial-messages to detect triggering early from
    stream events (content_block_start) rather than waiting for the
    full assistant message, which only arrives after tool execution.

    VENDORED (fix 4 of 5): returns None -- not False -- when the query TIMES OUT, so a
    timeout is a null measurement, never a not-triggered verdict.
    """
    unique_id = uuid.uuid4().hex[:8]
    clean_name = f"{skill_name}-skill-{unique_id}"
    project_commands_dir = Path(project_root) / ".claude" / "commands"
    command_file = project_commands_dir / f"{clean_name}.md"

    try:
        project_commands_dir.mkdir(parents=True, exist_ok=True)
        # Use YAML block scalar to avoid breaking on quotes in description
        indented_desc = "\n  ".join(skill_description.split("\n"))
        command_content = (
            f"---\n"
            f"description: |\n"
            f"  {indented_desc}\n"
            f"---\n\n"
            f"# {skill_name}\n\n"
            f"This skill handles: {skill_description}\n"
        )
        command_file.write_text(command_content)

        cmd = [
            "claude",
            "-p", query,
            "--output-format", "stream-json",
            "--verbose",
            "--include-partial-messages",
        ]
        if model:
            cmd.extend(["--model", model])

        # Remove CLAUDECODE env var to allow nesting claude -p inside a
        # Claude Code session. The guard is for interactive terminal conflicts;
        # programmatic subprocess usage is safe.
        env = {k: v for k, v in os.environ.items() if k != "CLAUDECODE"}

        process = subprocess.Popen(
            cmd,
            stdin=subprocess.DEVNULL,  # VENDORED (fix 2 of 5): don't inherit/wait on parent stdin
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            cwd=project_root,
            env=env,
        )

        state = DetectState(pending_tool_name=None, accumulated_json="", triggered=False)
        start_time = time.time()
        buffer = ""
        # VENDORED (fix 4 of 5): True only when the clock expires; every completed exit
        # (process ended, stream EOF, verdict returned) clears it.
        timed_out = True

        try:
            while time.time() - start_time < timeout:
                if process.poll() is not None:
                    remaining = process.stdout.read()
                    if remaining:
                        buffer += remaining.decode("utf-8", errors="replace")
                    timed_out = False  # VENDORED (fix 4 of 5): process completed
                    break

                ready, _, _ = select.select([process.stdout], [], [], 1.0)
                if not ready:
                    continue

                chunk = os.read(process.stdout.fileno(), 8192)
                if not chunk:
                    timed_out = False  # VENDORED (fix 4 of 5): stream EOF, a completed run
                    break
                buffer += chunk.decode("utf-8", errors="replace")

                while "\n" in buffer:
                    line, buffer = buffer.split("\n", 1)
                    # VENDORED: per-line detection extracted to detect_trigger_line() (pure,
                    # unit-tested in run_eval_test.py) -- this loop only threads state/verdict.
                    state, verdict = detect_trigger_line(line, clean_name, state)
                    if verdict is not None:
                        return verdict
        finally:
            # Clean up process on any exit path (return, exception, timeout)
            if process.poll() is None:
                process.kill()
                process.wait()

        if timed_out:
            return None  # VENDORED (fix 4 of 5): timeout -> null, excluded from the rate
        return state.triggered
    finally:
        if command_file.exists():
            command_file.unlink()


def summarize_query(
    query: str, triggers: list, should_trigger: bool, trigger_threshold: float
) -> dict:
    """VENDORED (fix 4 of 5): the per-query record, extracted pure from run_eval's aggregation
    loop so timeout-as-null is unit-testable. A None entry in `triggers` is a TIMED-OUT run:
    excluded from trigger_rate's denominator and from pass/fail, counted in `timeouts` (upstream
    scored it False, deflating the rate). If every run timed out there is NO measurement:
    trigger_rate and pass are None, never a fail-by-default."""
    completed = [t for t in triggers if t is not None]
    timeouts = len(triggers) - len(completed)
    if completed:
        trigger_rate = sum(completed) / len(completed)
        if should_trigger:
            did_pass = trigger_rate >= trigger_threshold
        else:
            did_pass = trigger_rate < trigger_threshold
    else:
        trigger_rate = None
        did_pass = None
    return {
        "query": query,
        "should_trigger": should_trigger,
        "trigger_rate": trigger_rate,
        "triggers": sum(completed),
        "runs": len(triggers),
        "completed_runs": len(completed),
        "timeouts": timeouts,
        "pass": did_pass,
    }


def summarize_results(results: list[dict]) -> dict:
    """VENDORED (fix 4 of 5): the summary block, extracted pure. An all-timeout query
    (pass None) counts as neither passed nor failed; `timeouts` totals every timed-out run so
    a load-compromised run is loudly visible."""
    return {
        "total": len(results),
        "passed": sum(1 for r in results if r["pass"] is True),
        "failed": sum(1 for r in results if r["pass"] is False),
        "timeouts": sum(r["timeouts"] for r in results),
    }


def run_eval(
    eval_set: list[dict],
    skill_name: str,
    description: str,
    num_workers: int,
    timeout: int,
    project_root: Path,
    runs_per_query: int = 1,
    trigger_threshold: float = 0.5,
    model: str | None = None,
) -> dict:
    """Run the full eval set and return results."""
    results = []

    with ProcessPoolExecutor(max_workers=num_workers) as executor:
        future_to_info = {}
        for item in eval_set:
            for run_idx in range(runs_per_query):
                future = executor.submit(
                    run_single_query,
                    item["query"],
                    skill_name,
                    description,
                    timeout,
                    str(project_root),
                    model,
                )
                future_to_info[future] = (item, run_idx)

        query_triggers: dict[str, list[bool | None]] = {}  # VENDORED (fix 4 of 5): None = timeout
        query_items: dict[str, dict] = {}
        for future in as_completed(future_to_info):
            item, _ = future_to_info[future]
            query = item["query"]
            query_items[query] = item
            if query not in query_triggers:
                query_triggers[query] = []
            try:
                query_triggers[query].append(future.result())
            except Exception as e:
                print(f"Warning: query failed: {e}", file=sys.stderr)
                query_triggers[query].append(False)

    for query, triggers in query_triggers.items():
        # VENDORED (fix 4 of 5): aggregation extracted to summarize_query() (pure, unit-tested
        # in run_eval_test.py) -- a None trigger (timeout) is excluded from the rate there.
        results.append(summarize_query(
            query, triggers, query_items[query]["should_trigger"], trigger_threshold))

    return {
        "skill_name": skill_name,
        "description": description,
        "results": results,
        "summary": summarize_results(results),  # VENDORED (fix 4 of 5): surfaces timeouts
    }


def main():
    parser = argparse.ArgumentParser(description="Run trigger evaluation for a skill description")
    parser.add_argument("--eval-set", required=True, help="Path to eval set JSON file")
    parser.add_argument("--skill-path", required=True, help="Path to skill directory")
    parser.add_argument("--description", default=None, help="Override description to test")
    parser.add_argument("--num-workers", type=int, default=10, help="Number of parallel workers")
    parser.add_argument("--timeout", type=int, default=30, help="Timeout per query in seconds")
    parser.add_argument("--runs-per-query", type=int, default=3, help="Number of runs per query")
    parser.add_argument("--trigger-threshold", type=float, default=0.5, help="Trigger rate threshold")
    parser.add_argument("--model", default=None, help="Model to use for claude -p (default: user's configured model)")
    parser.add_argument("--verbose", action="store_true", help="Print progress to stderr")
    args = parser.parse_args()

    eval_set = json.loads(Path(args.eval_set).read_text())
    skill_path = Path(args.skill_path)

    if not (skill_path / "SKILL.md").exists():
        print(f"Error: No SKILL.md found at {skill_path}", file=sys.stderr)
        sys.exit(1)

    name, original_description, content = parse_skill_md(skill_path)
    description = args.description or original_description
    project_root = find_project_root()

    if args.verbose:
        print(f"Evaluating: {description}", file=sys.stderr)

    output = run_eval(
        eval_set=eval_set,
        skill_name=name,
        description=description,
        num_workers=args.num_workers,
        timeout=args.timeout,
        project_root=project_root,
        runs_per_query=args.runs_per_query,
        trigger_threshold=args.trigger_threshold,
        model=args.model,
    )

    if args.verbose:
        summary = output["summary"]
        # VENDORED (fix 4 of 5): timeouts reported loudly; a null pass (all runs timed out)
        # prints NULL, and the rate denominator is completed runs, not submitted runs.
        print(f"Results: {summary['passed']}/{summary['total']} passed"
              f" ({summary['timeouts']} timeouts)", file=sys.stderr)
        for r in output["results"]:
            status = "PASS" if r["pass"] is True else ("FAIL" if r["pass"] is False else "NULL")
            rate_str = f"{r['triggers']}/{r['completed_runs']}"
            timeout_str = f" timeouts={r['timeouts']}" if r["timeouts"] else ""
            print(f"  [{status}] rate={rate_str}{timeout_str} expected={r['should_trigger']}: {r['query'][:70]}", file=sys.stderr)

    print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()
