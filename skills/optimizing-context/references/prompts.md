# Prompts Guide

Prompts are ephemeral, conversational instructions. Use when a skill or persistent mechanism isn't justified.

## When Prompt vs Other Mechanisms

| Situation | Use Prompt? | Alternative |
|-----------|-------------|-------------|
| One-time complex task | Yes | — |
| Will repeat this procedure | No | Skill |
| Need this context in future chats | No | Project or CLAUDE.md |
| User-wide behavior change | No | User Preferences |

## Core Prompt Patterns

### 1. Clear Task Framing

State what you want, then provide context:

**Weak**: "I have this code that's slow and I was wondering if maybe there's a way to make it faster, it's Python and uses pandas..."

**Strong**: "Optimize this Python/pandas code for performance. Current runtime is 45s on 1M rows. Target: under 10s."

### 2. Structured Input with XML Tags

Use XML tags to separate components:

```
<task>Analyze the sales data and identify trends</task>

<data>
[CSV content here]
</data>

<constraints>
- Focus on Q4 2024
- Compare to Q4 2023
- Highlight anomalies
</constraints>
```

### 3. Few-Shot Examples

Show input → output pairs for complex formats:

```
Convert product descriptions to structured data.

Example 1:
Input: "Blue cotton t-shirt, size M, $29.99"
Output: {"color": "blue", "material": "cotton", "type": "t-shirt", "size": "M", "price": 29.99}

Example 2:
Input: "Red wool sweater, XL, on sale for $45"
Output: {"color": "red", "material": "wool", "type": "sweater", "size": "XL", "price": 45}

Now convert:
Input: "Green silk dress, size S, $120"
```

### 4. Chain of Thought

Request reasoning before conclusions:

```
Evaluate whether we should migrate from PostgreSQL to MongoDB.

Think through:
1. Current pain points with PostgreSQL
2. Whether MongoDB addresses them
3. Migration costs and risks
4. Operational differences

Then provide your recommendation with rationale.
```

### 5. Output Specification

Define expected format explicitly:

```
Analyze this error log and respond with:

1. Root cause (one sentence)
2. Immediate fix (code snippet)
3. Long-term prevention (bullet points)
4. Severity: Critical/High/Medium/Low
```

## Token-Efficient Prompt Design

| Technique | Example |
|-----------|---------|
| Remove filler | "Could you please help me by..." → (just state the task) |
| Use abbreviations Claude knows | "TS" for TypeScript, "DB" for database |
| Reference, don't repeat | "Apply the same format to..." not re-stating format |
| Truncate irrelevant context | Include only the relevant code/data |

## Prompt Structure Order

Optimal ordering for complex prompts:

1. **Role/Context** (if needed): Who Claude should be
2. **Task**: What to accomplish
3. **Constraints**: Boundaries and requirements
4. **Format**: How to structure output
5. **Input data**: The content to process
6. **Examples** (if needed): Input/output pairs

## Anti-Patterns

| Anti-Pattern | Problem | Better Approach |
|--------------|---------|-----------------|
| Burying the task | Claude may miss key instruction | Lead with task |
| Over-qualifying | Wastes tokens | Be direct |
| Vague success criteria | Unclear when done | Define specific outputs |
| Mixing multiple tasks | Confused execution | One clear task per prompt |
| Apologetic framing | Unnecessary tokens | Skip politeness fillers |

## Prompt Reuse Decision

If you're about to use the same prompt a third time:

| Reuse Pattern | Consider |
|---------------|----------|
| Same procedure, different inputs | Create a Skill |
| Same context, different questions | Create a Project |
| Same format preference | Add to User Preferences |

## Chaining Prompts

For complex workflows, break into steps:

1. First prompt: Gather/analyze
2. Review output
3. Second prompt: Transform/generate
4. Review output
5. Third prompt: Refine/finalize

Each step gets Claude's fresh attention on the specific sub-task.

## Context Length Awareness

- Claude processes long inputs but performance degrades
- Put critical instructions early (primacy effect)
- Put key data late for recency effect on extraction tasks
- Summarize or truncate when full context isn't needed

## Sources

- Prompt engineering overview: https://docs.claude.com/en/docs/build-with-claude/prompt-engineering/overview
- Context engineering: https://www.anthropic.com/engineering/context-engineering


## Sources

- [Prompt Engineering Overview](https://docs.anthropic.com/en/docs/build-with-claude/prompt-engineering/overview) - Official prompt engineering guide
- [Effective Context Engineering](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents) - Context as curated tokens
