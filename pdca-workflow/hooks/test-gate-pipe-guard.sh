#!/usr/bin/env bash
# Decision-logic test for plugin-hooks/gate-pipe-guard.sh (the pdca-workflow plugin's copy: only
# guards adr-lint.mjs). Runnable on git-bash: `bash test-gate-pipe-guard.sh`. Pipes synthetic
# PreToolUse stdin JSON at the hook and asserts allow/deny on stdout.
set -u
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
HOOK="$HERE/gate-pipe-guard.sh"
pass=0; fail=0

# $1 = case name, $2 = command string, $3 = "deny" or "allow"
run_case() {
  name="$1"; cmd="$2"; expect="$3"
  json=$(printf '{"tool_name":"Bash","tool_input":{"command":"%s"}}' "$cmd")
  out=$(printf '%s' "$json" | bash "$HOOK")
  if printf '%s' "$out" | grep -q '"permissionDecision":"deny"'; then got=deny; else got=allow; fi
  if [ "$got" = "$expect" ]; then
    pass=$((pass+1)); printf 'PASS: %s\n' "$name"
  else
    fail=$((fail+1)); printf 'FAIL: %s (expected %s, got %s) cmd=[%s] out=[%s]\n' "$name" "$expect" "$got" "$cmd" "$out"
  fi
}

run_case "deny: node + path invocation, piped"        'node pdca-workflow/scripts/adr-lint.mjs docs | tail'                       deny
run_case "deny: cd-chained invocation, piped"          'cd x && node pdca-workflow/scripts/adr-lint.mjs docs | tail'               deny
run_case "deny: piped into tee (no carve-out)"         'node pdca-workflow/scripts/adr-lint.mjs docs | tee out.log'                deny
run_case "allow: bare substring in grep, not invoked"  'grep adr-lint.mjs file | head'                                             allow
run_case "allow: quoted mention, not invoked"          'echo "adr-lint.mjs" | x'                                                   allow
run_case "allow: && after invocation, no pipe"         'node pdca-workflow/scripts/adr-lint.mjs docs && echo done'                 allow
run_case "allow: || after invocation, no pipe"         'node pdca-workflow/scripts/adr-lint.mjs docs || echo fail'                 allow
run_case "allow: bare invocation, no operator at all"  'node pdca-workflow/scripts/adr-lint.mjs docs'                              allow
run_case "allow: pipe in a LATER unrelated && segment" 'node pdca-workflow/scripts/adr-lint.mjs docs && echo done | wc -l'         allow
run_case "allow: unrelated command, no gate mentioned" 'cd x && echo hi | wc -l'                                                   allow
run_case "allow: out-of-scope gate (validate.py)"      'node skills/building-skills/scripts/validate.py x | head'                 allow
run_case "allow: empty command string"                 ''                                                                          allow

# Truly empty/malformed stdin (no JSON at all) must also fail open.
out=$(printf '' | bash "$HOOK")
if printf '%s' "$out" | grep -q '"permissionDecision":"deny"'; then got=deny; else got=allow; fi
if [ "$got" = "allow" ]; then pass=$((pass+1)); printf 'PASS: %s\n' "allow: truly empty stdin fails open"
else fail=$((fail+1)); printf 'FAIL: %s (got %s)\n' "allow: truly empty stdin fails open" "$got"; fi

printf '\n%d passed, %d failed\n' "$pass" "$fail"
[ "$fail" -eq 0 ]
