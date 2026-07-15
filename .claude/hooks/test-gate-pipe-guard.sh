#!/usr/bin/env bash
# Decision-logic test for gate-pipe-guard.sh (this repo's copy: guards the repo-local
# gate scripts, excludes adr-lint.mjs -- that one is the plugin guard's job, see script header).
# Runnable on git-bash: `bash test-gate-pipe-guard.sh`.
set -u
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
HOOK="$HERE/gate-pipe-guard.sh"
pass=0; fail=0

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

# The two adversarial cases named explicitly in the review (adr-lint.mjs piped is OUT OF SCOPE
# for this repo guard -- see script header -- so it is correctly ALLOWED here; the plugin's own
# gate-pipe-guard.sh is what denies it, and that is covered by plugin-hooks/test-gate-pipe-guard.sh).
run_case "allow: adr-lint.mjs piped -- out of scope, plugin's job" 'node pdca-workflow/scripts/adr-lint.mjs docs | tail'                           allow
run_case "deny: cd && python3 invocation, redirect+pipe" 'cd x && python3 skills/building-skills/scripts/validate.py y 2>&1 | head'               deny
run_case "allow: bare substring in grep, not invoked"   'grep adr-lint.mjs file | head'                                                            allow
run_case "allow: quoted mention, not invoked"           'echo "validate.py" | x'                                                                   allow
run_case "deny: check-restatement.mjs piped"            'node scripts/check-restatement.mjs | tail'                                                deny
run_case "allow: check-restatement.mjs && no pipe"      'node scripts/check-restatement.mjs && echo ok'                                            allow
run_case "allow: check-workflow.mjs || no pipe"         'node scripts/check-workflow.mjs || echo fail'                                             allow
run_case "deny: check-workflow.mjs piped into tee"      'node scripts/check-workflow.mjs | tee log.txt'                                            deny
run_case "deny: run_eval.py piped"                      'python3 skills/building-skills/scripts/run_eval.py x | head'                              deny
run_case "deny: check-pr-body.mjs piped into grep"      'node scripts/check-pr-body.mjs | grep foo'                                                deny
run_case "deny: check-gate-tests.mjs piped"             'node scripts/check-gate-tests.mjs | tail'                                                 deny
run_case "allow: check-gate-tests.mjs bare invocation"  'node scripts/check-gate-tests.mjs'                                                        allow
run_case "allow: pipe in a later unrelated && segment" 'node scripts/check-restatement.mjs && echo done | wc -l'                                    allow
run_case "allow: empty command string"                  ''                                                                                          allow

out=$(printf '' | bash "$HOOK")
if printf '%s' "$out" | grep -q '"permissionDecision":"deny"'; then got=deny; else got=allow; fi
if [ "$got" = "allow" ]; then pass=$((pass+1)); printf 'PASS: %s\n' "allow: truly empty stdin fails open"
else fail=$((fail+1)); printf 'FAIL: %s (got %s)\n' "allow: truly empty stdin fails open" "$got"; fi

printf '\n%d passed, %d failed\n' "$pass" "$fail"
[ "$fail" -eq 0 ]
