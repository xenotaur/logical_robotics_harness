# LRH Work Item — Body Section Guide

This document describes the required and optional body sections for an LRH
work item, what belongs in each section, and how to write content that passes
`lrh request prompt-from-work-item` readiness checks.

---

## Required sections

These sections must be present for an item to be considered prompt-ready.
The section heading names are exact — the readiness parser lowercases headings
and keys on specific strings: `summary`, `scope`, `required changes`,
`acceptance criteria`, and `validation`. Using different heading names (e.g.
`## Validation Commands` instead of `## Validation`) will cause readiness
checks to fail even though the content looks correct.

### `## Summary`

One to two sentences. State the deliverable or outcome — not the approach.

**Good:** "Implement the `lrh-work-item` Claude Code skill that guides users
through creating new LRH work items."

**Avoid:** "This work item is about creating a skill because we need one."

Keep it dense: a reader scanning the `project/work_items/` directory should
understand the item's purpose from this alone.

---

### `## Problem / Context`

Two to four sentences explaining:

1. What gap, pain point, or requirement motivates this item.
2. Why it needs to be solved now (rather than later or never).
3. What prerequisite context the implementor needs.

Cite related design docs, workstreams, or prior work items by path or ID.
Do not repeat the Summary — extend it.

---

### `## Scope`

One to four bullets stating what is in scope for this work item. This section
is distinct from `## Required Changes` — Scope describes the bounded purpose,
while Required Changes lists the specific files and actions.

**Good:**

```
- Implement `src/lrh/skills/lrh-work-item/` and mirror to `.claude/skills/`
- Create work item and execution records in `project/`
- Add a `## Skills` index entry to `CLAUDE.md`
```

**Avoid combining with Required Changes.** A work item with no `## Scope`
section will fail `lrh work-items readiness` with "missing Scope section",
even if `## Required Changes` is present and detailed.

---

### `## Required Changes`

A numbered or bulleted list of the concrete changes this item demands. Each
bullet should name a specific file, command, or artifact.

**Good:**

```
1. Create `src/lrh/skills/lrh-work-item/SKILL.md` following the LRH pattern.
2. Create three `references/` files: work-item-schema.md, ...
3. Mirror both to `.claude/skills/lrh-work-item/`.
4. Add WI-SKILLS-LRH-WORK-ITEM to WS-SKILLS `work_items:` list.
```

**Avoid vague scope:** "Implement the skill." This gives an implementor no
constraint on what to build or where.

An item with a `Required Changes` section that names concrete files is
substantially more prompt-ready than one without.

---

### `## Non-Goals`

A bulleted list of things this work item explicitly does **not** do. Each
entry should be something a reader might otherwise assume is in scope.

Non-goals serve two purposes: they bound the implementation and they document
deferred work for future items. Write them as negative imperatives:

```
- Do not implement `lrh setup` — that is WI-SKILLS-LRH-SETUP.
- Do not add skill evaluation logic — defer to anthropic-skills:skill-creator.
- Do not modify existing skills.
```

---

### `## Acceptance Criteria`

A bulleted list of verifiable conditions that must be true for the work item
to be considered complete. Each criterion should have a clear pass/fail answer.

This section mirrors the `acceptance:` YAML frontmatter list but may contain
more prose. The YAML list is used by machine checks; this section is for
human review.

**Good (specific, verifiable):**

```
- `lrh validate` reports 0 errors after all files are written.
- `diff -r src/lrh/skills/lrh-work-item/ .claude/skills/lrh-work-item/`
  reports no differences.
- The skill produces a valid work item when run in the LRH repo session.
```

**Avoid (vague):**

```
- The skill works correctly.
- Code quality is good.
```

---

### `## Validation`

List the exact commands an implementor should run to verify the item is
complete. The heading must be exactly `## Validation` — the readiness parser
keys on the lowercase string `"validation"`, so `## Validation Commands`
will not be recognised.

These are the commands that produce evidence for `required_evidence`.

**Format:** use bullet-listed commands, not a code block. The readiness
parser calls `_extract_bullets` on this section and only recognises lines
that start with `- `. A fenced code block will produce an empty validation
list and fail the readiness check.

Standard LRH validation sequence:

- `scripts/version tools`
- `lrh validate`

For items that touch Python package behavior or tests, add:

- `scripts/format --check --diff`
- `scripts/lint`
- `scripts/test`

Add item-specific commands as additional bullets:

- `diff -r src/lrh/skills/lrh-work-item/ .claude/skills/lrh-work-item/`
- `` `python -c "import lrh.skills"` ``

---

## Optional sections

These sections appear in many work items and add useful context when present.

### `## Risk Notes`

Two to four bullets on what could go wrong, and how. Focus on risks specific
to this work item — not generic risks that apply to all code changes.

---

### `## Dependencies / Order`

Narrative prose (one paragraph) explaining when this item should be worked
relative to its `depends_on` list. Useful when the dependency order is not
obvious from IDs alone.

---

### `## Related Workstream and Designs`

A short list of file paths to the workstream YAML and any design proposals
that govern this work item's scope. Example:

```
- Workstream: `project/workstreams/proposed/WS-SKILLS.md`
- Design: `project/design/proposals/adopted/lrh-project-local-skills/00_proposal.md`
```

---

## Conservative authoring discipline

Prefer explicit gaps over invented content. If a section requires information
that was not provided in the interview:

- Add an `Open Questions` subsection with the specific unknown.
- Do not invent scope, requirements, or validation steps.
- A sparse but accurate work item is better than a complete but fabricated one.

This mirrors the discipline in `lrh request ready-work-item`:
"turn unresolved context into Open Questions, not invented scope."
