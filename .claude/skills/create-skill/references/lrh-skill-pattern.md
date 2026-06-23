# LRH Skill Structure Pattern

This document records the validated LRH pattern for project-local Claude Code
skills, derived from the `new-scenario` reference implementation and the
`PROP-LRH-PROJECT-LOCAL-SKILLS` design proposal.

---

## Required frontmatter

Every LRH skill SKILL.md must begin with a YAML frontmatter block:

```yaml
---
name: kebab-case-name
description: >
  One-paragraph description used for auto-invocation matching.
  Must be ≤ 1024 characters. Should be specific enough that
  Claude knows exactly when to trigger the skill.
disable-model-invocation: true   # or omit/false for auto-triggered skills
argument-hint: [arg1, arg2]      # omit if skill takes no arguments
---
```

Valid frontmatter keys: `name`, `description`, `disable-model-invocation`,
`argument-hint`, `context`. No other keys are recognised.

---

## When to use `disable-model-invocation: true`

Set `disable-model-invocation: true` when:

- The skill performs high-consequence actions (writing files, modifying
  project control plane artifacts).
- Invocation is intentional — the user must explicitly type `/<name>`.
- The description keywords are likely to appear in unrelated queries.

Omit `disable-model-invocation` (or set to `false`) when:

- The skill is domain-specific and auto-triggering is desirable.
- Accidental triggering would be harmless (e.g., a read-only reporting skill).

---

## Recommended body structure

Follow this section order. Do not invent new section names.

```markdown
# <name> Skill

One-paragraph purpose description.

---

## Inputs

What the user provides: arguments, optional flags, context.

---

## Reference Knowledge

Numbered list of references/ files to load before execution.
One entry per file; include what information it contains.

---

## Execution Steps

### 1. <Step title>
<concrete instructions>

### 2. <Step title>
...

---

## Quality Checklist

- [ ] item 1
- [ ] item 2

---

## What This Skill Does Not Do

Explicit scope limits. One bullet per non-goal.
```

---

## Size constraint

Keep `SKILL.md` under approximately 500 lines. If instructions grow beyond
this, move reference material to `references/` and load it on demand.

The `references/` directory exists for:

- Large domain data (tables, schemas, templates)
- Content that is only needed in specific steps
- Worked examples and annotated reference implementations

Do not put step-by-step instructions in `references/`; those belong in
`SKILL.md`. References are loaded on demand; `SKILL.md` is always loaded.

---

## The confirm-before-write gate

LRH skills that write files must always include a mandatory user-confirmation
step before writing. This gate:

- Prevents scope creep (the proposal may reveal mismatched intent).
- Aligns with LRH's "preserve human control" principle.
- Addresses OWASP LLM risk guidance on excessive agency.

The gate must:

1. Show the user the proposed structure in readable form.
2. Wait for explicit confirmation.
3. Adjust and re-show if the user redirects.

Do not write files before this gate passes.

---

## LRH-specific additions

When a skill produces LRH control-plane artifacts (work items, workstreams,
proposals), it should:

1. Read the relevant schema file from `project/design/schemas/` before
   generating any YAML frontmatter.
2. Confirm the artifact structure with the user before writing.
3. Run `lrh validate` after writing and report the result.

These additions enforce LRH's "evidence-backed, auditable" discipline at the
skill level, not just at the CLI level.
