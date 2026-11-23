# Profile Instructions Guide (Claude.ai)

Profile instructions are the account-wide free text Claude.ai applies to all of your
conversations. The setting is labelled "Instructions for Claude"; for where it sits in Settings,
see the Personalization documentation (Sources below).

## When to Use Them

| Situation | Use profile instructions? | Alternative |
|-----------|---------------------------|-------------|
| Default tone for all chats | Yes | — |
| Industry terminology you always use | Yes | — |
| Project-specific behavior | No | Project instructions (they apply only inside that project) |
| One-time request | No | State in message |
| Complex workflows | No | Skill |

The documentation gives no precedence order between profile instructions, project instructions
and the current message. Don't design around one: keep the two from contradicting each other.

## What Works Well

- Communication style: "Be concise" or "Explain thoroughly"
- Expertise acknowledgment: "I'm a software engineer familiar with Python"
- Format preferences: "Use bullet points sparingly" or "Include code examples"
- Domain terminology: "Use medical terminology appropriately"
- Approach preferences: "Prefer practical solutions over theoretical"

## Examples

### Concise Professional

```
Be direct and concise. Skip unnecessary caveats. I'm a senior engineer—assume technical competence. When showing code, prefer complete working examples over snippets.
```

### Domain Expert

```
I'm a healthcare administrator. Use appropriate medical and regulatory terminology. Focus on practical compliance implications. Reference relevant regulations when applicable.
```

## What Not to Include

| Anti-Pattern | Problem | Alternative |
|--------------|---------|-------------|
| "Always use Python" | Too rigid for varied questions | State per-conversation |
| Very long lists | Dilutes the important ones | Prioritize top 3-5 |
| Project-specific context | Doesn't apply everywhere | Use project instructions |
| Contradictions | Confuses Claude | Choose one approach |

## Iteration

1. Start with core communication preferences
2. Notice patterns in how you correct Claude
3. Add an instruction that would prevent a repeated correction
4. Remove what no longer applies
5. Keep it concise—quality over quantity

## Sources

- [Understanding Claude's Personalization Features](https://support.claude.com/en/articles/10185728-understanding-claude-s-personalization-features) - names the setting and its scope; read 23-Nov-2026
