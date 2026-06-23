# Security Considerations

Read this before publishing or sharing skills.

## Table of Contents

1. [No Hardcoded Secrets](#no-hardcoded-secrets)
2. [Auditing Third-Party Skills](#auditing-third-party-skills)
3. [MCP Tool Security](#mcp-tool-security)
4. [External Data Sources](#external-data-sources)

---

## No Hardcoded Secrets

Never include in skills:
- API keys
- Passwords
- Tokens
- Connection strings
- Private URLs

**Bad**:
```python
API_KEY = "sk-abc123..."
```

**Good**:
```python
# Requires API_KEY environment variable
import os
API_KEY = os.environ.get("API_KEY")
if not API_KEY:
    raise ValueError("Set API_KEY environment variable")
```

---

## Auditing Third-Party Skills

Before using a skill from untrusted source:

1. **Review all files**:
   - SKILL.md
   - All scripts
   - All references
   - Assets and templates

2. **Check for**:
   - Unexpected network calls
   - File access outside skill directory
   - Operations that don't match stated purpose
   - Obfuscated code

3. **Test in isolation** before production use

---

## MCP Tool Security

Use fully qualified tool names:
```
ServerName:tool_name
```

Verify tool permissions before use. Malicious skills can invoke tools in harmful ways.

---

## External Data Sources

Skills fetching external URLs are risky:
- Fetched content may contain malicious instructions
- External dependencies can change over time
- Network errors can cause unpredictable behavior

If external fetch is required:
- Validate fetched content
- Handle network failures gracefully
- Document the dependency clearly
