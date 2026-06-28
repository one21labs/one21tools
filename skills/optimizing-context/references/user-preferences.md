# User Preferences Guide (Claude.ai)

User Preferences are account-wide settings that shape Claude's behavior across all conversations.

## What They Are

Free text describing your preferences, applied to every conversation unless overridden by more specific context.

For current UI location and configuration, see `product-self-knowledge` or https://support.claude.com.

## When to Use User Preferences

| Situation | Use Preferences? | Alternative |
|-----------|------------------|-------------|
| Default tone for all chats | Yes | — |
| Industry terminology you always use | Yes | — |
| Project-specific behavior | No | Project Instructions |
| One-time request | No | State in message |
| Complex workflows | No | Skill |

## Precedence Principle

More specific context overrides more general:
- What you say in the current message overrides everything
- Project Instructions override User Preferences
- User Preferences are the baseline default

For exact precedence rules and interaction with Styles, see `product-self-knowledge`.

## Effective Preferences

### What Works Well

- Communication style: "Be concise" or "Explain thoroughly"
- Expertise acknowledgment: "I'm a software engineer familiar with Python"
- Format preferences: "Use bullet points sparingly" or "Include code examples"
- Domain terminology: "Use medical terminology appropriately"
- Approach preferences: "Prefer practical solutions over theoretical"

### What Doesn't Work Well

- Highly specific instructions (too rigid across varied contexts)
- Contradictory requirements
- Very long preference lists (dilutes signal)
- Instructions that should vary by project

## Example Preferences

### Concise Professional

```
Be direct and concise. Skip unnecessary caveats. I'm a senior engineer—assume technical competence. When showing code, prefer complete working examples over snippets.
```

### Thorough Educator

```
Explain concepts thoroughly with examples. I'm learning, so break down complex ideas. Include analogies where helpful. Prefer clarity over brevity.
```

### Domain Expert

```
I'm a healthcare administrator. Use appropriate medical and regulatory terminology. Focus on practical compliance implications. Reference relevant regulations when applicable.
```

### Minimal Formatting

```
Avoid bullet points and headers unless essential. Write in prose paragraphs. Keep formatting minimal and clean.
```

## Interaction with Styles

**User Preferences**: *What* Claude considers (content, approach)
**Custom Styles**: *How* Claude communicates (tone, format)

They complement each other. Preferences set content expectations; Styles set delivery.

## What Not to Include

| Anti-Pattern | Problem | Alternative |
|--------------|---------|-------------|
| "Always use Python" | Too rigid for varied questions | State per-conversation |
| Very long lists | Dilutes important preferences | Prioritize top 3-5 |
| Project-specific context | Doesn't apply everywhere | Use Project Instructions |
| Contradictions | Confuses Claude | Choose one approach |

## Iteration

Preferences should evolve:

1. Start with core communication preferences
2. Notice patterns in how you correct Claude
3. Add preferences that would prevent repeated corrections
4. Remove preferences that no longer apply
5. Keep it concise—quality over quantity

## Checking What's Applied

You can ask Claude: "What preferences are you currently applying?" Claude will describe the active preferences affecting responses.

## Sources

- Personalization features: https://support.claude.com/en/articles/10185728-understanding-claude-s-personalization-features


## Sources

- [Understanding Claude's Personalization Features](https://support.claude.com/en/articles/10185728-understanding-claude-s-personalization-features) - Official documentation
