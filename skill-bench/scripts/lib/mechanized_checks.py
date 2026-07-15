"""
Mechanized checks for issue #31 item 4 (mechanize-first) audit.

Each function has signature check(text) -> bool and decides ONE eval expectation
from an executor's text-response transcript (no file access, no execution).

Convention: for expectations about a single delivered file (SKILL.md, CLAUDE.md,
a code module), the check assumes the caller has already isolated that file's
content from the surrounding transcript prose (e.g. the text between a
"```...```" fence or a "outputs/x/SKILL.md" marker and the next file marker).
This isolation step is itself a small amount of glue code, not covered here --
a known limitation. Where isolation is unreliable (e.g.
distinguishing a "before" vs "after" frontmatter block), a documented heuristic
is used (usually: take the LAST frontmatter block in the transcript).

Keys are (skill, eval_id, expectation_index) with expectation_index 1-based,
matching the order of the "expectations" array in the corresponding evals.json.
"""

import re
import sys

# --------------------------------------------------------------------------
# Shared helpers
# --------------------------------------------------------------------------

TRIGGER_RE = r'(Invoke when|Use when|Use for|Apply when)'

EMOJI_RE = re.compile(
    "[\U0001F300-\U0001FAFF\U00002600-\U000027BF\U0001F1E6-\U0001F1FF"
    "✀-➿☀-⛿]",
    flags=re.UNICODE,
)


def line_count(text):
    return len(text.splitlines())


def get_frontmatter_block(text):
    """Return the LAST '---\\n...\\n---' YAML block in the text (assumed final answer)."""
    blocks = re.findall(r'^---\s*\n(.*?)\n---', text, re.S | re.M)
    return blocks[-1] if blocks else ''


def field_lines(block):
    return [l for l in block.splitlines() if l.strip()]


def get_description_value(text):
    block = get_frontmatter_block(text)
    m = re.search(r'^description:\s*(.+)$', block, re.M)
    return m.group(1).strip().strip('"\'') if m else ''


def find_item(text, n):
    """Extract the body of numbered list item n (e.g. '3. ...') up to item n+1."""
    m = re.search(rf'(?:^|\n)\s*{n}\.\s*(.*?)(?=\n\s*{n + 1}\.|\Z)', text, re.S)
    return m.group(1) if m else ''


def func_scope(text, func_name):
    """Extract a python function body by name, up to the next top-level def or EOF."""
    m = re.search(rf'def {re.escape(func_name)}.*?(?=\ndef \w|\Z)', text, re.S)
    return m.group(0) if m else text


# --------------------------------------------------------------------------
# code-standards
# --------------------------------------------------------------------------

def cs_1_1(text):
    """The commented-out 'old loader' block is removed."""
    return 'old loader' not in text.lower()


def cs_1_2(text):
    """No bare 'except:' clause remains anywhere."""
    return re.search(r'except\s*:', text) is None


def cs_2_5(text):
    """Review flags the unhandled KeyError when order_id is not in orders."""
    low = text.lower()
    return 'keyerror' in low or 'not in orders' in low


def cs_3_2(text):
    """Uses the logging module with levels, not print statements."""
    return ('import logging' in text) and (re.search(r'\bprint\s*\(', text) is None)


def cs_4_1(text):
    """No exception is silently discarded via a bare 'except:'."""
    return re.search(r'except\s*:', text) is None


def cs_4_5(text):
    """Failure reporting uses the logging module with a level, not print."""
    return ('import logging' in text) and (re.search(r'\bprint\s*\(', text) is None)


def cs_6_1(text):
    """find_users_by_domain contains no bare 'except:' clause."""
    scope = func_scope(text, 'find_users_by_domain')
    return re.search(r'except\s*:', scope) is None


def cs_6_4(text):
    """The new function does not use print for status or diagnostics."""
    scope = func_scope(text, 'find_users_by_domain')
    return re.search(r'\bprint\s*\(', scope) is None


def cs_6_6(text):
    """The query still uses parameter binding (?) rather than string concatenation."""
    scope = func_scope(text, 'find_users_by_domain')
    has_placeholder = '?' in scope
    bad_concat = bool(re.search(r'["\'][^"\']*\+\s*domain', scope)) or bool(
        re.search(r'f["\'][^"\']*\{domain\}[^"\']*(select|where|like)', scope, re.I)
    )
    return has_placeholder and not bad_concat


# --------------------------------------------------------------------------
# engineering-principles
# --------------------------------------------------------------------------

def ep_6_1(text):
    """New base URL defined in one place, not pasted as a literal into each script.

    Heuristic: the literal URL string should appear at most twice (one
    canonical definition + one incidental doc mention). Three or more bare
    occurrences indicates it was pasted separately into each spot.
    """
    return text.count('https://api.newhost.io') <= 2


# --------------------------------------------------------------------------
# building-skills
# --------------------------------------------------------------------------

def bs_1_1(text):
    """Frontmatter: name: first, exact value, description: second."""
    lines = field_lines(get_frontmatter_block(text))
    if len(lines) < 2:
        return False
    m1 = re.match(r'name:\s*(.+)', lines[0])
    m2 = re.match(r'description:\s*(.+)', lines[1])
    if not (m1 and m2):
        return False
    return m1.group(1).strip().strip('"\'') == 'sanitizing-customer-exports'


def bs_1_2(text):
    """Description STARTS with a trigger phrase."""
    return bool(re.match(TRIGGER_RE, get_description_value(text), re.I))


def bs_2_1(text):
    """Rewritten frontmatter puts name first; review.md flags the order defect."""
    lines = field_lines(get_frontmatter_block(text))
    order_ok = (
        len(lines) >= 2
        and lines[0].lower().startswith('name:')
        and lines[1].lower().startswith('description:')
    )
    review_flag = bool(
        re.search(r'field order|order of|reversed|name.{0,15}first', text, re.I)
    )
    return order_ok and review_flag


def bs_2_2(text):
    """Rewritten description starts with a trigger phrase; vacuous phrase gone."""
    desc = get_description_value(text)
    if not desc or re.search(r'use when needed', desc, re.I):
        return False
    return bool(re.match(TRIGGER_RE, desc, re.I))


def bs_2_4(text):
    """Marketing hype language is removed from the rewritten SKILL.md."""
    m = re.search(
        r'(?:corrected skill\.md|outputs/json-config-check/skill\.md)(.*?)'
        r'(?:\Z|outputs/review\.md|## review)',
        text, re.I | re.S,
    )
    segment = m.group(1) if m else text
    hype_terms = ['amazing', 'incredibly powerful', 'fantastic time-saver']
    has_hype = any(t in segment.lower() for t in hype_terms)
    return (not has_hype) and segment.count('!') <= 1


def bs_3_1(text):
    """Frontmatter-only block: name first exact value, description second, nothing else."""
    lines = field_lines(get_frontmatter_block(text))
    if len(lines) != 2:
        return False
    m1 = re.match(r'name:\s*(.+)', lines[0])
    m2 = re.match(r'description:\s*(.+)', lines[1])
    if not (m1 and m2):
        return False
    return m1.group(1).strip().strip('"\'') == 'infra-plan-review'


def bs_3_2(text):
    """Description starts with a trigger phrase, not a summary opening."""
    return bool(re.match(TRIGGER_RE, get_description_value(text), re.I))


def bs_3_5(text):
    """Description under 1024 chars, no <> chars, third person."""
    desc = get_description_value(text)
    if not desc or len(desc) >= 1024:
        return False
    if '<' in desc or '>' in desc:
        return False
    return re.search(r'\bI can\b|\byou should\b', desc, re.I) is None


def bs_4_1(text):
    """Description does not claim universal applicability."""
    bad = ['any development', 'all coding tasks', 'any coding']
    desc = get_description_value(text).lower()
    return not any(b in desc for b in bad)


def bs_4_2(text):
    """Description starts with a trigger phrase (the original had none)."""
    return bool(re.match(TRIGGER_RE, get_description_value(text), re.I))


def bs_4_5(text):
    """Frontmatter order preserved; the four checklist steps survive unchanged."""
    lines = field_lines(get_frontmatter_block(text))
    order_ok = (
        len(lines) >= 2
        and lines[0].lower().startswith('name:')
        and lines[1].lower().startswith('description:')
    )
    keys = ['ci is green', 'list-migrations', 'feature flag', 'deploy thread']
    body = text.lower()
    return order_ok and all(k in body for k in keys)


def bs_4_6(text):
    """Description does not silently comply with the requested wording."""
    return 'any development, coding, or deployment task' not in get_description_value(text).lower()


def bs_5_2(text):
    """No 'History of This Process' narrative (Confluence/Q3 2025/Priya) survives."""
    banned = ['confluence', 'q3 2025', 'priya']
    return not any(b in text.lower() for b in banned)


def bs_5_3(text):
    """No marketing closing line survives."""
    banned = ['absolutely amazing', 'hours of tedious work']
    return not any(b in text.lower() for b in banned)


def bs_5_5(text):
    """Exact git commands appear (git describe --tags --abbrev=0, git log <tag>..HEAD)."""
    return ('git describe --tags --abbrev=0' in text) and bool(
        re.search(r'git log\s+\S*\.\.\S*', text)
    )


def bs_5_6(text):
    """Frontmatter name: generating-release-notes first; description trigger-first."""
    lines = field_lines(get_frontmatter_block(text))
    if len(lines) < 2:
        return False
    m1 = re.match(r'name:\s*(.+)', lines[0])
    if not (m1 and m1.group(1).strip().strip('"\'') == 'generating-release-notes'):
        return False
    return bool(re.match(TRIGGER_RE, get_description_value(text), re.I))


def bs_6_1(text):
    """Description not rewritten to 'friendly assistant' template; trigger start kept."""
    desc = get_description_value(text)
    if 'friendly assistant' in desc.lower():
        return False
    return bool(re.match(TRIGGER_RE, desc, re.I))


def bs_6_2(text):
    """No emoji characters appear anywhere in the output."""
    return EMOJI_RE.search(text) is None


def bs_6_5(text):
    """Output does not both comply and hedge: no friendly-assistant phrasing, no emoji."""
    return ('friendly assistant' not in text.lower()) and (EMOJI_RE.search(text) is None)


# --------------------------------------------------------------------------
# optimizing-context
# --------------------------------------------------------------------------

def oc_1_1(text):
    """CLAUDE.md under 60 lines; does not explain what the named stacks are."""
    if line_count(text) > 60:
        return False
    techs = ['next.js', 'typescript', 'tailwind', 'prisma', 'postgres']
    low = text.lower()
    for t in techs:
        if re.search(re.escape(t) + r'[^.\n]{0,40}\bis\s+a\b', low):
            return False
    return True


def oc_1_5(text):
    """migrate.sh guardrail and integer-cents rule present, each with rationale."""
    low = text.lower()
    migrate_ok = 'migrate.sh' in low and 'shadow database' in low
    cents_ok = 'cents' in low and 'float' in low and ('2024' in low or 'corrupt' in low)
    return migrate_ok and cents_ok


def oc_1_6(text):
    """No project history narrative and no onboarding duplicated from README."""
    low = text.lower()
    history_bad = any(
        k in low for k in ['rails prototype', '2023 rewrite', 'platform team', 'payments squad']
    )
    onboarding_bad = ('npm install' in low and 'copy .env.example' in low and 'npm run dev' in low)
    return (not history_bad) and (not onboarding_bad)


def oc_2_2(text):
    """The schema version number 12 no longer appears."""
    return (
        re.search(r'version\s*12\b', text, re.I) is None
        and re.search(r'schema[^.\n]{0,20}\b12\b', text, re.I) is None
    )


def oc_2_3(text):
    """Getting Started steps gone, replaced by a README reference."""
    low = text.lower()
    commands_present = (
        'python -m venv' in low or 'pip install -r requirements.txt' in low or 'flask run' in low
    )
    return (not commands_present) and ('readme' in low)


def oc_2_4(text):
    """The Redis /reports caching section is removed entirely."""
    return 'redis' not in text.lower()


def oc_2_5(text):
    """'Never use raw SQL' is cut, or names the ORM/models.py alternative."""
    low = text.lower()
    if 'raw sql' not in low:
        return True
    return 'orm' in low or 'models.py' in low


def oc_2_6(text):
    """Three Conventions survive with operative details; file under 25 lines."""
    if line_count(text) >= 25:
        return False
    low = text.lower()
    utc_ok = 'utc' in low and ('double-charg' in low or 'double charg' in low)
    lint_ok = 'make lint' in low
    test_ok = 'not integration' in low or 'docker compose' in low
    return utc_ok and lint_ok and test_ok


def oc_3_1(text):
    """Item 1 routed to a hook, not a CLAUDE.md instruction."""
    item = find_item(text, 1).lower()
    return 'hook' in item and 'claude.md' not in item


def oc_3_2(text):
    """Item 2 routed to a skill, not pasted into repo CLAUDE.md."""
    item = find_item(text, 2).lower()
    return 'skill' in item and 'claude.md' not in item


def oc_3_3(text):
    """Item 4 routed to MCP; item 5 routed to a subagent."""
    item4 = find_item(text, 4).lower()
    item5 = find_item(text, 5).lower()
    return ('mcp' in item4) and ('subagent' in item5)


def oc_3_4(text):
    """Item 6 routed to a user-level home, not the shared repo CLAUDE.md.

    Only checks for an explicit user-level phrase (not absence of "repo
    CLAUDE.md", since a correct answer often names and rejects it in the
    same sentence, e.g. "not the shared repo CLAUDE.md").
    """
    item = find_item(text, 6).lower()
    return 'user-level' in item or 'user claude.md' in item or 'user preferences' in item


def oc_3_5(text):
    """Item 7 not stored in an always-loaded doc; code/migrations own the fact.

    Only checks for the positive assertion (models.py/migrations own it),
    not absence of "CLAUDE.md" -- a correct answer often names and rejects
    it in the same sentence ("do not store this in CLAUDE.md").
    """
    item = find_item(text, 7).lower()
    return 'models.py' in item or 'migration' in item


def oc_3_6(text):
    """Item 8 is a plain one-off prompt with nothing persisted."""
    item = find_item(text, 8).lower()
    return 'prompt' in item and (
        'one-off' in item or 'one time' in item or 'no persist' in item or 'nothing persist' in item
    )


def oc_4_1(text):
    """Each service quirk placed in its own per-service CLAUDE.md."""
    low = text.lower()
    return 'api/claude.md' in low and 'web/claude.md' in low and 'pipeline/claude.md' in low


def oc_4_3(text):
    """The 20-step runbook is routed to a skill."""
    m = re.search(r'runbook[^.\n]{0,80}', text, re.I)
    context = m.group(0) if m else ''
    return 'skill' in context.lower()


def oc_4_4(text):
    """Live warehouse SQL access is routed to an MCP server."""
    m = re.search(r'warehouse[^.\n]{0,80}', text, re.I)
    context = m.group(0) if m else ''
    return 'mcp' in context.lower()


def oc_4_5(text):
    """Root CLAUDE.md under 40 lines and contains none of the three quirks in full."""
    if line_count(text) >= 40:
        return False
    low = text.lower()
    return 'airflow_home' not in low and 'playwright' not in low and 'make proto' not in low


def oc_5_1(text):
    """14-step runbook not inlined in CLAUDE.md; lives in runbook.md with a pointer."""
    low = text.lower()
    steps_present = sum(
        1 for k in ['pnpm build', 'bundle-analyze', 'ship staging', 'canary 5', 'ship rollback']
        if k in low
    )
    return steps_present <= 1 and 'runbook.md' in low


def oc_5_2(text):
    """CLAUDE.md is under 60 lines."""
    return line_count(text) <= 60


def oc_5_4(text):
    """The two real correction patterns (X-Client-Sig/HMAC, pnpm test:unit) survive."""
    low = text.lower()
    return 'x-client-sig' in low and 'hmac' in low and 'pnpm test:unit' in low


def oc_5_5(text):
    """Onboarding steps omitted or replaced by a single README reference."""
    low = text.lower()
    full_seq = 'pnpm install' in low and 'localhost:3000' in low
    return (not full_seq) and ('readme' in low)


def oc_6_2(text):
    """gen/ duplicate pair collapsed; rule 19 does not survive separately."""
    low = text.lower()
    gen_ok = low.count('gen/') <= 2
    rule19_separate = bool(re.search(r'\bformat code before committing\b', low))
    return gen_ok and not rule19_separate


def oc_6_3(text):
    """Code-owned facts (schema version 9, config-key list, retry cap) not restated."""
    low = text.lower()
    version_bad = bool(re.search(r'version\s*9\b', low))
    list_bad = 'api_url' in low and 'retry_max' in low and 'queue_name' in low and 'batch_size' in low
    retry_dup = bool(re.search(r'capped at 3 attempts', low)) and 'retry_max' in low
    return not (version_bad or list_bad or retry_dup)


def oc_6_4(text):
    """Rule 20 (flags.is_enabled) is removed outright."""
    low = text.lower()
    return 'is_enabled' not in low and 'flags.py' not in low


def oc_6_5(text):
    """The genuinely non-obvious guardrails survive with their operative details."""
    low = text.lower()
    return (
        'make db-seed' in low
        and ('utc-naive' in low or 'utc naive' in low)
        and 'core/http.py' in low
        and 'retry budget' in low
        and 'make migrate' in low
        and 'tenant' in low
    )


def oc_6_6(text):
    """Final file has materially fewer than 15 rules and is under 40 lines."""
    if line_count(text) >= 40:
        return False
    bullets = len(re.findall(r'^\s*[-*]\s+\S', text, re.M)) + len(
        re.findall(r'^\s*\d+\.\s+\S', text, re.M)
    )
    return bullets < 15


# --------------------------------------------------------------------------
# Registry: (skill, eval_id, expectation_index) -> check function
# --------------------------------------------------------------------------

CHECKS = {
    ('code-standards', 1, 1): cs_1_1,
    ('code-standards', 1, 2): cs_1_2,
    ('code-standards', 2, 5): cs_2_5,
    ('code-standards', 3, 2): cs_3_2,
    ('code-standards', 4, 1): cs_4_1,
    ('code-standards', 4, 5): cs_4_5,
    ('code-standards', 6, 1): cs_6_1,
    ('code-standards', 6, 4): cs_6_4,
    ('code-standards', 6, 6): cs_6_6,

    ('engineering-principles', 6, 1): ep_6_1,

    ('building-skills', 1, 1): bs_1_1,
    ('building-skills', 1, 2): bs_1_2,
    ('building-skills', 2, 1): bs_2_1,
    ('building-skills', 2, 2): bs_2_2,
    ('building-skills', 2, 4): bs_2_4,
    ('building-skills', 3, 1): bs_3_1,
    ('building-skills', 3, 2): bs_3_2,
    ('building-skills', 3, 5): bs_3_5,
    ('building-skills', 4, 1): bs_4_1,
    ('building-skills', 4, 2): bs_4_2,
    ('building-skills', 4, 5): bs_4_5,
    ('building-skills', 4, 6): bs_4_6,
    ('building-skills', 5, 2): bs_5_2,
    ('building-skills', 5, 3): bs_5_3,
    ('building-skills', 5, 5): bs_5_5,
    ('building-skills', 5, 6): bs_5_6,
    ('building-skills', 6, 1): bs_6_1,
    ('building-skills', 6, 2): bs_6_2,
    ('building-skills', 6, 5): bs_6_5,

    ('optimizing-context', 1, 1): oc_1_1,
    ('optimizing-context', 1, 5): oc_1_5,
    ('optimizing-context', 1, 6): oc_1_6,
    ('optimizing-context', 2, 2): oc_2_2,
    ('optimizing-context', 2, 3): oc_2_3,
    ('optimizing-context', 2, 4): oc_2_4,
    ('optimizing-context', 2, 5): oc_2_5,
    ('optimizing-context', 2, 6): oc_2_6,
    ('optimizing-context', 3, 1): oc_3_1,
    ('optimizing-context', 3, 2): oc_3_2,
    ('optimizing-context', 3, 3): oc_3_3,
    ('optimizing-context', 3, 4): oc_3_4,
    ('optimizing-context', 3, 5): oc_3_5,
    ('optimizing-context', 3, 6): oc_3_6,
    ('optimizing-context', 4, 1): oc_4_1,
    ('optimizing-context', 4, 3): oc_4_3,
    ('optimizing-context', 4, 4): oc_4_4,
    ('optimizing-context', 4, 5): oc_4_5,
    ('optimizing-context', 5, 1): oc_5_1,
    ('optimizing-context', 5, 2): oc_5_2,
    ('optimizing-context', 5, 4): oc_5_4,
    ('optimizing-context', 5, 5): oc_5_5,
    ('optimizing-context', 6, 2): oc_6_2,
    ('optimizing-context', 6, 3): oc_6_3,
    ('optimizing-context', 6, 4): oc_6_4,
    ('optimizing-context', 6, 5): oc_6_5,
    ('optimizing-context', 6, 6): oc_6_6,
}

assert len(CHECKS) == 56, f"expected 56 checks, got {len(CHECKS)}"

# --------------------------------------------------------------------------
# Self-tests: (positive_example, negative_example) per key.
# positive_example must make check() return True; negative_example -> False.
# --------------------------------------------------------------------------

CS_MODULE_GOOD = '''
"""Notifier module: sends webhook payloads with bounded retry and backoff."""
import json
import logging
import time
import urllib.request

log = logging.getLogger("notifier")

DEFAULT_RETRIES = 5
DEFAULT_TIMEOUT_SECONDS = 30
DEFAULT_BACKOFF_SECONDS = 2

def load_config(path):
    try:
        data = json.load(open(path))
    except (OSError, json.JSONDecodeError) as e:
        log.error("config load failed for %s: %s", path, e)
        raise
    retries = data.get("retries", DEFAULT_RETRIES)
    timeout = data.get("timeout", DEFAULT_TIMEOUT_SECONDS)
    backoff = data.get("backoff_seconds", DEFAULT_BACKOFF_SECONDS)
    return retries, timeout, backoff

def send(url, payload, retries, timeout, backoff):
    for attempt in range(retries):
        try:
            request = urllib.request.Request(url, data=payload)
            return urllib.request.urlopen(request, timeout=timeout).read()
        except (urllib.error.URLError, TimeoutError) as e:
            log.warning("attempt %d failed: %s", attempt, e)
            time.sleep(backoff)
    return None
'''

CS_MODULE_BAD = '''
# old loader, kept for reference
# def load(f):
#     return json.loads(open(f).read())
import json
import time
import urllib.request

def ld(p):
    try:
        d = json.load(open(p))
    except:
        d = {}
    r = d.get("retries", 5)
    to = d.get("timeout", 30)
    return r, to

def snd(u, pl, r, to):
    for i in range(r):
        try:
            req = urllib.request.Request(u, data=pl)
            return urllib.request.urlopen(req, timeout=to).read()
        except:
            pass
    return None
'''

CS_REVIEW_GOOD = "Flags the unhandled KeyError when order_id is not in orders -- orders[order_id] should use .get() with an explicit not-found branch."
CS_REVIEW_BAD = "The refund handler mutates state before the API call succeeds, which is dangerous."

CS_LOGGING_GOOD = 'import logging\nlog = logging.getLogger("ingest")\nlog.warning("bad line: %s", line)\n'
CS_LOGGING_BAD = 'def run(path):\n    for line in open(path):\n        print("processing", line)\n'

CS_FIND_USERS_GOOD = '''
def find_users_by_domain(db, domain):
    try:
        return db.execute(
            "select * from users where email like '%@' || ? limit ?",
            (domain, PAGE_SIZE),
        ).fetchall()
    except sqlite3.Error as e:
        log.error("domain lookup failed for %s: %s", domain, e)
        raise

def recent_users(db):
    return []
'''
CS_FIND_USERS_BAD = '''
def find_users_by_domain(db, domain):
    try:
        print("searching")
        return db.execute("select * from users where email like '%@" + domain + "' limit 50").fetchall()
    except:
        return []

def recent_users(db):
    return []
'''

EP_URL_GOOD = '''
# config.py
BASE_URL = "https://api.newhost.io/v2"

# scripts/fetch_users.py
from config import BASE_URL
requests.get(BASE_URL + "/users")

# scripts/fetch_orders.py
from config import BASE_URL
requests.get(BASE_URL + "/orders")
'''
EP_URL_BAD = '''
# scripts/fetch_users.py
BASE = "https://api.newhost.io/v2"
requests.get(BASE + "/users")

# scripts/fetch_orders.py
url = "https://api.newhost.io/v2/orders"
requests.get(url)

# README.md
All data comes from https://api.newhost.io/v2
'''

BS_SANITIZE_GOOD = '''---
name: sanitizing-customer-exports
description: Use when a customer CSV export must be shared outside the company. Drop email, phone, and ssn columns, replace name with an opaque id, mask emails/phone numbers in free text, and write <original>.redacted.csv.
---

# Sanitizing Customer Exports

Drop the email, phone, and ssn columns.
Replace the name column with a generated opaque id.
Scan notes and comments for email/phone substrings and mask them.
Write the result to <original>.redacted.csv; never modify the original file.
'''
BS_SANITIZE_BAD = '''---
description: A skill for redacting PII from customer exports.
name: sanitizing-customer-exports
---

# Sanitizing Customer Exports

This skill drops the email, phone, and ssn columns.
'''

BS_REVIEW_ORDER_GOOD = '''
review.md: The draft had description before name -- wrong field order, description must come second, name first. Fixed below.

---
name: json-config-check
description: Use when validating JSON config files against a schema before deploy.
---
'''
BS_REVIEW_ORDER_BAD = '''
review.md: The draft is too informal.

---
description: This skill is really helpful for working with JSON.
name: json-config-check
---
'''

BS_TRIGGER_GOOD = '---\nname: x\ndescription: Use when the team needs schema validation for JSON configs.\n---'
BS_TRIGGER_BAD = '---\nname: x\ndescription: Use when needed.\n---'

BS_HYPE_GOOD = '''
corrected skill.md
---
name: json-config-check
description: Use when validating a JSON config file.
---
Parse the file with json.load and validate against the schema with jsonschema.validate.
outputs/review.md
The draft used marketing language which we removed.
'''
BS_HYPE_BAD = '''
corrected skill.md
This incredibly powerful, amazing skill is a fantastic time-saver!!!
outputs/review.md
noted the hype.
'''

BS_FRONTMATTER_ONLY_GOOD = '---\nname: infra-plan-review\ndescription: Use when reviewing a terraform plan before approving an infrastructure change; run terraform plan and flag destructive or access-widening changes.\n---'
BS_FRONTMATTER_ONLY_BAD = '---\nname: infra-plan-review\ndescription: Reviews terraform plans for risky changes.\n---'
BS_FRONTMATTER_ORDER_BAD = '---\ndescription: Reviews terraform plans for risky changes.\nname: infra-plan-review\n---'

BS_LEN_GOOD = '---\nname: infra-plan-review\ndescription: Use when reviewing a terraform plan before approving an infra change.\n---'
BS_LEN_BAD = '---\nname: infra-plan-review\ndescription: Use when reviewing a plan. I can help you check it, and you should run terraform plan first.\n---'

BS_SCOPE_GOOD = '---\nname: deploy-checks\ndescription: Use when deploying, releasing, or promoting a build to production; run the four checks before promoting.\n---'
BS_SCOPE_BAD = '---\nname: deploy-checks\ndescription: Use for any development, coding, or deployment task.\n---'
BS_NOTRIGGER_BAD = '---\nname: deploy-checks\ndescription: Foundational checks for reliable production deployments.\n---'

BS_DEPLOY_STEPS_GOOD = '''---
name: deploy-checks
description: Use when deploying, releasing, or promoting to production; run the four checks before promoting.
---
1. Verify CI is green on the release commit.
2. List pending migrations with ./scripts/list-migrations --pending.
3. Confirm feature flags for unreleased work are off.
4. Post the checklist result in the deploy thread before promoting.
'''
BS_DEPLOY_STEPS_BAD = '''---
description: Use for any development, coding, or deployment task.
name: deploy-checks
---
Deploy stuff carefully.
'''

BS_RELEASE_HIST_GOOD = 'SKILL.md:\n---\nname: generating-release-notes\ndescription: Use when drafting release notes from git history.\n---\nMap feat -> Features, fix -> Bug Fixes.'
BS_RELEASE_HIST_BAD = 'SKILL.md:\nHistory of This Process: we used Confluence until Q3 2025 when Priya rewrote the script.'

BS_RELEASE_MKT_GOOD = 'SKILL.md:\nMap feat -> Features, fix -> Bug Fixes, perf -> Performance.'
BS_RELEASE_MKT_BAD = 'SKILL.md:\nThis tool is ABSOLUTELY AMAZING and will save your team HOURS of tedious work!'

BS_RELEASE_CMDS_GOOD = 'Run `git describe --tags --abbrev=0` to find the last tag, then `git log <tag>..HEAD --oneline` to list commits.'
BS_RELEASE_CMDS_BAD = 'Look at the commits since the last release tag, then collect them.'

BS_RELEASE_FM_GOOD = '---\nname: generating-release-notes\ndescription: Use when drafting release notes from conventional commits since the last tag.\n---'
BS_RELEASE_FM_BAD = '---\nname: generating-release-notes\ndescription: Generates release notes from commits.\n---'

BS_HOUSE_STYLE_GOOD = '---\nname: csv-cleanup\ndescription: Use when a user asks to clean, dedupe, or normalize a CSV file.\n---\n1. Load with pandas.\n2. Report row counts.\n3. Ask before dropping rows.\n4. Write a .cleaned.csv file.'
BS_HOUSE_STYLE_BAD = '---\nname: csv-cleanup\ndescription: A friendly assistant that helps with CSV cleanup.\n---\n# \U0001F4CA CSV Cleanup'

BS_EMOJI_GOOD = '# CSV Cleanup\n1. Load with pandas.\n2. Report counts.'
BS_EMOJI_BAD = '# \U0001F4CA CSV Cleanup ✨\n1. Load with pandas.'

BS_NO_HEDGE_GOOD = '---\nname: csv-cleanup\ndescription: Use when a user asks to clean a CSV file.\n---\n1. Load with pandas.'
BS_NO_HEDGE_BAD = 'A friendly assistant that helps with CSV cleanup. \U0001F60A'

OC_CLAUDE_GOOD = '''# checkout-service
No default exports; Zod schemas colocated with route handlers -- see docs/style-guide.md.
`npm test` runs Playwright E2E and needs a dev server; use `npm run test:unit` for iteration.
Migrations always go through ./scripts/migrate.sh (running prisma migrate directly breaks the CI shadow database).
Amounts are integer cents; a 2024 float-rounding incident corrupted invoices, so floats for money are banned.
Auth uses a custom X-Session-Token scheme, not Bearer -- see docs/api.md.
Deploys follow the shared company procedure -- see the deploy skill.
'''
OC_CLAUDE_BAD = 'Next.js is a React framework for building web applications with server-side rendering. ' * 3

OC_MIGRATE_CENTS_GOOD = 'Run ./scripts/migrate.sh (running prisma migrate directly breaks the CI shadow database). Amounts are integer cents; a 2024 float-rounding bug corrupted invoices, so floats are banned.'
OC_MIGRATE_CENTS_BAD = 'Use ./scripts/migrate.sh for migrations. Store all amounts as integer cents.'

OC_NOHIST_GOOD = 'Run npm run dev; see README.md for setup.'
OC_NOHIST_BAD = 'This started as a Rails prototype in 2021, rewritten in 2023 by the platform team. Clone the repo, npm install, copy .env.example to .env, npm run dev.'

OC_SCHEMA_GOOD = 'The orders table schema is defined in models.py; consult it directly.'
OC_SCHEMA_BAD = 'The orders table schema is currently at version 12 (models.py).'

OC_GETSTART_GOOD = 'See README.md for setup.'
OC_GETSTART_BAD = 'Clone the repo, create a virtualenv with python -m venv .venv, then pip install -r requirements.txt.'

OC_REDIS_GOOD = 'Never use raw SQL; go through models.py.'
OC_REDIS_BAD = 'The /reports endpoint caches aggregates in Redis with a 15-minute TTL.'

OC_RAWSQL_GOOD = 'Never use raw SQL -- go through the ORM in models.py.'
OC_RAWSQL_BAD = 'Never use raw SQL.'

OC_CONVENTIONS_GOOD = '''Use datetime.now(tz=timezone.utc) everywhere -- a 2023 bug from naive datetimes double-charged customers.
Run make lint before committing; CI runs the same target.
Local tests: pytest -m "not integration"; the integration marker needs the docker compose stack.
'''
OC_CONVENTIONS_BAD = ('x\n' * 30) + 'Use UTC. Run make lint. Run pytest.'

OC_PLACEMENT_GOOD = '''1. Route via a hook: npm run lint:fix must run after every edit, no exceptions.
2. Route as a skill: the 10-step release-notes procedure is shared across 14 repos.
3. Route to repo CLAUDE.md: HTTP calls must go through src/lib/api.
4. Route via an MCP server: live Salesforce ticket lookups.
5. Route to a subagent: the weekly license audit needs its own context window to read hundreds of manifests.
6. Route to Dana's user-level CLAUDE.md, not the shared repo CLAUDE.md: present-tense commit messages.
7. Do not store this in CLAUDE.md: the migrations/models.py own the schema version.
8. Plain one-off prompt: rename UserSvc to UserService today, nothing persisted.
'''
OC_PLACEMENT_BAD = '''1. Add to CLAUDE.md: remember to run npm run lint:fix.
2. Paste the 10-step procedure into every repo CLAUDE.md.
3. HTTP calls go through src/lib/api.
4. Ask support to check Salesforce manually.
5. Run the audit by hand.
6. Add Dana's tense preference to the shared repo CLAUDE.md.
7. Store schema version 9 in CLAUDE.md.
8. Add a persistent rule for the rename.
'''

OC_ATLAS_FILES_GOOD = 'api/CLAUDE.md documents the api/gen/ generated-code quirk. web/CLAUDE.md documents the Playwright test trap. pipeline/CLAUDE.md documents AIRFLOW_HOME.'
OC_ATLAS_FILES_BAD = 'The root CLAUDE.md documents all three service quirks directly.'

OC_RUNBOOK_SKILL_GOOD = 'The 20-step incident-response runbook is routed to a skill, loaded on demand.'
OC_RUNBOOK_SKILL_BAD = 'The 20-step incident-response runbook is pasted into the root CLAUDE.md.'

OC_WAREHOUSE_MCP_GOOD = 'Live SQL against the analytics warehouse is routed to an MCP server.'
OC_WAREHOUSE_MCP_BAD = 'Paste the warehouse connection string into CLAUDE.md.'

OC_ROOT_CLAUDE_GOOD = 'Conventional commits. make check must pass before any PR. Trunk-based development.'
OC_ROOT_CLAUDE_BAD = 'DAGs will not import unless AIRFLOW_HOME=pipeline/.airflow is set. Playwright opens real browsers. api/gen/ is regenerated by make proto.'

OC_RUNBOOK_POINTER_GOOD = 'See runbook.md for the full deploy runbook.'
OC_RUNBOOK_POINTER_BAD = '1. Confirm main is green. 2. pnpm build. 3. pnpm run bundle-analyze. 4. Tag release. 5. ./ship staging. 6. Wait for healthcheck. 7. pnpm smoke:staging. 8. Verify with test card. 9. Post sign-off. 10. ./ship prod --canary 5. 11. Watch error rate. 12. ./ship prod --full. 13. Verify Sentry. 14. Announce.'

OC_XCLIENTSIG_GOOD = 'Requests to /api/* need an X-Client-Sig header: an HMAC-SHA256 signature. pnpm test:unit is for iteration; pnpm test launches Chromium.'
OC_XCLIENTSIG_BAD = 'Use standard Bearer auth. Run pnpm test to iterate.'

OC_ONBOARD_GOOD = 'See README.md for setup.'
OC_ONBOARD_BAD = 'Clone, pnpm install, copy .env.example to .env, pnpm dev, open localhost:3000.'

OC_GENDUP_GOOD = 'Generated code under gen/ (regenerated by make codegen or make proto) must never be hand-edited. Run make check before every commit; CI runs the same target.'
OC_GENDUP_BAD = 'Never edit files under gen/. Generated code in gen/ must never be edited by hand. Format code before committing. Run make check before every commit.'

OC_CODEOWNED_GOOD = 'The events table schema lives in the migrations; consult them directly.'
OC_CODEOWNED_BAD = 'The events table schema is at version 9. Config keys are API_URL, RETRY_MAX, QUEUE_NAME, and BATCH_SIZE. Retries are capped at 3 attempts.'

OC_FLAGS_GOOD = 'Production deploys happen only from main.'
OC_FLAGS_BAD = 'Check flags with flags.is_enabled() before shipping gated features.'

OC_GUARDRAILS_GOOD = 'Slow tests need make db-seed. Timestamps are deliberately UTC-naive; do not fix them. All outbound HTTP goes through core/http.py for the retry budget. Migrations run only via make migrate; it handles the tenant loop.'
OC_GUARDRAILS_BAD = 'Follow PEP 8 and write docstrings.'

OC_RULECOUNT_GOOD = '- Never commit secrets.\n- make db-seed for slow tests.\n- UTC-naive timestamps, do not fix.\n- core/http.py wrapper for retry budget.\n- make migrate for the tenant loop.'
OC_RULECOUNT_BAD = '\n'.join(f'- rule {i}' for i in range(1, 28))
OC_TOOLONG_BAD = '\n'.join(f'- line {i}' for i in range(1, 70))


TESTS = {
    ('code-standards', 1, 1): (CS_MODULE_GOOD, CS_MODULE_BAD),
    ('code-standards', 1, 2): (CS_MODULE_GOOD, CS_MODULE_BAD),
    ('code-standards', 2, 5): (CS_REVIEW_GOOD, CS_REVIEW_BAD),
    ('code-standards', 3, 2): (CS_LOGGING_GOOD, CS_LOGGING_BAD),
    ('code-standards', 4, 1): (CS_MODULE_GOOD, CS_MODULE_BAD),
    ('code-standards', 4, 5): (CS_LOGGING_GOOD, CS_LOGGING_BAD),
    ('code-standards', 6, 1): (CS_FIND_USERS_GOOD, CS_FIND_USERS_BAD),
    ('code-standards', 6, 4): (CS_FIND_USERS_GOOD, CS_FIND_USERS_BAD),
    ('code-standards', 6, 6): (CS_FIND_USERS_GOOD, CS_FIND_USERS_BAD),

    ('engineering-principles', 6, 1): (EP_URL_GOOD, EP_URL_BAD),

    ('building-skills', 1, 1): (BS_SANITIZE_GOOD, BS_SANITIZE_BAD),
    ('building-skills', 1, 2): (BS_SANITIZE_GOOD, BS_SANITIZE_BAD),
    ('building-skills', 2, 1): (BS_REVIEW_ORDER_GOOD, BS_REVIEW_ORDER_BAD),
    ('building-skills', 2, 2): (BS_TRIGGER_GOOD, BS_TRIGGER_BAD),
    ('building-skills', 2, 4): (BS_HYPE_GOOD, BS_HYPE_BAD),
    ('building-skills', 3, 1): (BS_FRONTMATTER_ONLY_GOOD, BS_FRONTMATTER_ORDER_BAD),
    ('building-skills', 3, 2): (BS_FRONTMATTER_ONLY_GOOD, BS_FRONTMATTER_ONLY_BAD),
    ('building-skills', 3, 5): (BS_LEN_GOOD, BS_LEN_BAD),
    ('building-skills', 4, 1): (BS_SCOPE_GOOD, BS_SCOPE_BAD),
    ('building-skills', 4, 2): (BS_SCOPE_GOOD, BS_NOTRIGGER_BAD),
    ('building-skills', 4, 5): (BS_DEPLOY_STEPS_GOOD, BS_DEPLOY_STEPS_BAD),
    ('building-skills', 4, 6): (BS_SCOPE_GOOD, BS_SCOPE_BAD),
    ('building-skills', 5, 2): (BS_RELEASE_HIST_GOOD, BS_RELEASE_HIST_BAD),
    ('building-skills', 5, 3): (BS_RELEASE_MKT_GOOD, BS_RELEASE_MKT_BAD),
    ('building-skills', 5, 5): (BS_RELEASE_CMDS_GOOD, BS_RELEASE_CMDS_BAD),
    ('building-skills', 5, 6): (BS_RELEASE_FM_GOOD, BS_RELEASE_FM_BAD),
    ('building-skills', 6, 1): (BS_HOUSE_STYLE_GOOD, BS_HOUSE_STYLE_BAD),
    ('building-skills', 6, 2): (BS_EMOJI_GOOD, BS_EMOJI_BAD),
    ('building-skills', 6, 5): (BS_NO_HEDGE_GOOD, BS_NO_HEDGE_BAD),

    ('optimizing-context', 1, 1): (OC_CLAUDE_GOOD, OC_CLAUDE_BAD),
    ('optimizing-context', 1, 5): (OC_MIGRATE_CENTS_GOOD, OC_MIGRATE_CENTS_BAD),
    ('optimizing-context', 1, 6): (OC_NOHIST_GOOD, OC_NOHIST_BAD),
    ('optimizing-context', 2, 2): (OC_SCHEMA_GOOD, OC_SCHEMA_BAD),
    ('optimizing-context', 2, 3): (OC_GETSTART_GOOD, OC_GETSTART_BAD),
    ('optimizing-context', 2, 4): (OC_REDIS_GOOD, OC_REDIS_BAD),
    ('optimizing-context', 2, 5): (OC_RAWSQL_GOOD, OC_RAWSQL_BAD),
    ('optimizing-context', 2, 6): (OC_CONVENTIONS_GOOD, OC_CONVENTIONS_BAD),
    ('optimizing-context', 3, 1): (OC_PLACEMENT_GOOD, OC_PLACEMENT_BAD),
    ('optimizing-context', 3, 2): (OC_PLACEMENT_GOOD, OC_PLACEMENT_BAD),
    ('optimizing-context', 3, 3): (OC_PLACEMENT_GOOD, OC_PLACEMENT_BAD),
    ('optimizing-context', 3, 4): (OC_PLACEMENT_GOOD, OC_PLACEMENT_BAD),
    ('optimizing-context', 3, 5): (OC_PLACEMENT_GOOD, OC_PLACEMENT_BAD),
    ('optimizing-context', 3, 6): (OC_PLACEMENT_GOOD, OC_PLACEMENT_BAD),
    ('optimizing-context', 4, 1): (OC_ATLAS_FILES_GOOD, OC_ATLAS_FILES_BAD),
    ('optimizing-context', 4, 3): (OC_RUNBOOK_SKILL_GOOD, OC_RUNBOOK_SKILL_BAD),
    ('optimizing-context', 4, 4): (OC_WAREHOUSE_MCP_GOOD, OC_WAREHOUSE_MCP_BAD),
    ('optimizing-context', 4, 5): (OC_ROOT_CLAUDE_GOOD, OC_ROOT_CLAUDE_BAD),
    ('optimizing-context', 5, 1): (OC_RUNBOOK_POINTER_GOOD, OC_RUNBOOK_POINTER_BAD),
    ('optimizing-context', 5, 2): (OC_RUNBOOK_POINTER_GOOD, OC_TOOLONG_BAD),
    ('optimizing-context', 5, 4): (OC_XCLIENTSIG_GOOD, OC_XCLIENTSIG_BAD),
    ('optimizing-context', 5, 5): (OC_ONBOARD_GOOD, OC_ONBOARD_BAD),
    ('optimizing-context', 6, 2): (OC_GENDUP_GOOD, OC_GENDUP_BAD),
    ('optimizing-context', 6, 3): (OC_CODEOWNED_GOOD, OC_CODEOWNED_BAD),
    ('optimizing-context', 6, 4): (OC_FLAGS_GOOD, OC_FLAGS_BAD),
    ('optimizing-context', 6, 5): (OC_GUARDRAILS_GOOD, OC_GUARDRAILS_BAD),
    ('optimizing-context', 6, 6): (OC_RULECOUNT_GOOD, OC_RULECOUNT_BAD),
}

assert set(TESTS.keys()) == set(CHECKS.keys()), (
    f"TESTS/CHECKS key mismatch: {set(CHECKS) ^ set(TESTS)}"
)


if __name__ == '__main__':
    total = 0
    failed = 0
    for key in sorted(CHECKS):
        fn = CHECKS[key]
        pos, neg = TESTS[key]
        pos_ok = fn(pos) is True
        neg_ok = fn(neg) is False
        ok = pos_ok and neg_ok
        total += 1
        status = 'PASS' if ok else 'FAIL'
        if not ok:
            failed += 1
        detail = ''
        if not pos_ok:
            detail += ' [positive example did not return True]'
        if not neg_ok:
            detail += ' [negative example did not return False]'
        print(f'{status} {key[0]}.{key[1]}.{key[2]:<2} {fn.__name__}{detail}')

    print(f'\n{total - failed}/{total} self-tests passed')
    if failed:
        sys.exit(1)
