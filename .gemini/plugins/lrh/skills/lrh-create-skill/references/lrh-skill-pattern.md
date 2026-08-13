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
when_to_use: >
  Narrows the auto-trigger surface further, or names the human-initiated
  chain(s) this skill is a link in. Omit disable-model-invocation for
  most skills — see below.
argument-hint: [arg1, arg2]      # omit if skill takes no arguments
---
```

Valid frontmatter keys: `name`, `description`, `when_to_use`,
`disable-model-invocation`, `argument-hint`, `context`. No other keys are
recognised.

---

## When to use `disable-model-invocation: true`

**Do not set this by default for a skill that writes files or modifies
control-plane artifacts.** `WI-DELIBERATE-MODEL-INVOCATION` found that
"high-consequence action" is not, by itself, a reason to reach for this
flag — it is a binary *mechanism* (can the Skill tool fire at all) doing
the job of a *policy* question (should this write happen right now), and
it blocks a user's own explicit, in-session request as readily as
unwanted auto-triggering (the platform cannot tell "the model decided on
its own" from "the user named this skill mid-sentence instead of typing
the bare `/name`"). This is why most LRH skills that write files —
`/lrh-implement`, `/lrh-review-response`, `/lrh-closeout`, `/lrh-work-item`,
`/lrh-proposal`, `/lrh-workstream`, and others — do **not** carry this
flag.

**The default pattern:** omit the flag, add a `when_to_use` field that
narrows the auto-trigger surface (and names any human-initiated chain the
skill is a link in), and put an explicit confirm-before-write gate inside
the skill's own steps as the real write-protection — that gate fires
regardless of invocation route, so it doesn't depend on getting this flag
right. This satisfies OWASP LLM08 ("require human approval for high-impact
actions") without blocking composition or a user's own in-prose request.

**Set `disable-model-invocation: true` only for a specific, confirmed gap**
this pattern doesn't cover — name the gap explicitly in the skill's own
guidance when you do, don't just assert "explicit intent only." Two real
examples from this project: a fast path that skips the skill's own confirm
gate entirely (`/lrh-confirm-fixes`'s empty-thread path reaches
REVIEW-LANDED review-signal state handling with no gate in between), and a
live-reply requirement a different mechanism can bypass under one of its
own modes (`/lrh-land`/`/lrh-execute`'s chain-authorization gate can be
skipped under `DEC-CHAIN-INIT-SKIP-CONSENT`'s `skip_if_opted_in`, and
nothing else currently verifies the invocation was a genuine human-typed
command). "The skill performs high-consequence actions" alone is not
sufficient justification — the confirm gate already covers that for every
other skill.

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
