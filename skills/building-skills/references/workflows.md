# Workflow Patterns

Read this when skills involve multi-step processes.

## Table of Contents

1. [Sequential Workflows](#sequential-workflows)
2. [Conditional Workflows](#conditional-workflows)
3. [Checkpoint Pattern](#checkpoint-pattern)
4. [Feedback Loops](#feedback-loops)

---

## Sequential Workflows

For complex tasks, show steps upfront:

```markdown
## PDF form filling workflow

1. Analyze form (run analyze_form.py)
2. Create field mapping (edit fields.json)
3. Validate mapping (run validate_fields.py)
4. Fill form (run fill_form.py)
5. Verify output (run verify_output.py)

Do not skip steps. Each validates the previous.
```

---

## Conditional Workflows

Guide through decision points:

```markdown
## Document modification

1. Determine type:
   - **Creating new?** → Follow "Creation" below
   - **Editing existing?** → Follow "Editing" below

2. Creation workflow:
   a. Choose template from templates/
   b. Fill sections per TEMPLATE_GUIDE.md
   c. Run validate.py before saving

3. Editing workflow:
   a. Load existing document
   b. Track changes if collaboration needed
   c. Run diff.py to verify changes
```

---

## Checkpoint Pattern

For risky operations, require explicit checkpoints:

```markdown
## Database migration

1. Generate migration script
2. **CHECKPOINT**: Review script, confirm before proceeding
3. Run on staging
4. **CHECKPOINT**: Verify staging results
5. Run on production
```

Claude pauses at CHECKPOINTs for human confirmation.

---

## Feedback Loops

For quality-critical operations:

```markdown
## Document editing process

1. Make edits to document.xml
2. **Validate immediately**: python scripts/validate.py
3. If validation fails:
   - Review error message
   - Fix issues
   - Run validation again
4. **Only proceed when validation passes**
5. Rebuild: python scripts/pack.py
6. Test the output
```

The validation loop catches errors early.

---

## Verifiable Intermediate Outputs

For complex operations, create a plan file validated before execution.

```markdown
## Batch update workflow

1. Generate changes.json with planned modifications
2. Validate: python scripts/validate_plan.py changes.json
3. If validation fails, fix changes.json and re-validate
4. Execute: python scripts/apply_changes.py changes.json
5. Verify: python scripts/verify_output.py
```

Machine-verifiable plans catch errors before changes are applied.
