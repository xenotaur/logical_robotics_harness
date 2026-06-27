# LRH Workstream — Body Section Guide

This document describes the recommended body sections for an LRH workstream,
what belongs in each section, and how to write content that follows LRH
workstream conventions.

---

## Recommended sections

These sections appear in most well-formed workstream bodies. They follow the
reading order established in existing LRH workstreams.

### `## Purpose`

Two to four sentences. State what stream of work this workstream coordinates
and why it exists now.

**Good:** "This workstream groups the design, implementation, and validation
of the three LRH documentation skills (`/lrh-doc-audit`, `/lrh-doc-organize`,
`/lrh-doc-work`). It captures decisions made during the Option C-1 Diataxis
design review and tracks each deliverable through to closeout."

**Avoid:** "This workstream exists because we need to do documentation skills
work." Do not repeat the `summary` field — extend it with the "why" and the
specific grouping rationale.

---

### `## Scope`

One to four bullets stating what is in scope for this workstream. Distinct
from exit criteria — Scope describes the bounded purpose; Exit Criteria states
what must be true to close.

**Good:**

```
- Implement /lrh-doc-audit, /lrh-doc-organize, and /lrh-doc-work skills
- Land associated work items through the standard LRH execution lifecycle
- Update CLAUDE.md ## Skills index for each skill
```

---

### `## Work Items`

A prose paragraph or bulleted list of the work items belonging to this
workstream, with a brief description of each. Mirrors and expands the
`work_items:` frontmatter list.

This section is useful for readers who want context beyond a bare ID list.
When work items are not yet known, note that they will be added as the
design matures.

```
- **WI-DOC-SKILLS-AUDIT** — Implement the /lrh-doc-audit skill.
- **WI-DOC-SKILLS-ORGANIZE** — Implement the /lrh-doc-organize skill.
- **WI-DOC-SKILLS-WORK** — Implement the /lrh-doc-work skill.
```

---

### `## Exit Criteria`

A bulleted list of verifiable conditions that must be true before this
workstream can be closed. Each criterion should have a clear pass/fail answer.
Mirrors and expands the `exit_criteria:` frontmatter list.

**Good (specific, verifiable):**

```
- All three documentation skills pass lrh validate with 0 errors
- CLAUDE.md ## Skills index updated for each skill
- Each skill has a corresponding resolved work item in project/work_items/resolved/
```

**Avoid (vague):**

```
- The work is done
- Documentation is good
```

---

### `## Non-Goals`

A bulleted list of things this workstream explicitly does **not** address.
Each entry should be something a reader might otherwise assume is in scope.

```
- Does not implement lrh serve dashboard integration — deferred.
- Does not affect the Diataxis audit of existing docs — a separate effort.
```

---

## Optional sections

### `## Background / Rationale`

Two to four sentences explaining the broader context and decisions that
led to this workstream. Reference related design proposals or prior
workstreams by file path.

---

### `## Relationship to Design`

A short list of related design proposals, canonical design docs, or prior
workstreams that govern this workstream's scope:

```
- Design proposal: project/design/proposals/proposed/lrh-doc-skills/00_proposal.md
- Canonical design: project/design/architecture.md
- Prior workstream: project/workstreams/resolved/WS-SKILLS.md
```

---

### `## Open Questions`

Any unresolved questions that the workstream leaves open. Use this section
rather than blocking workstream creation on incomplete details.

```
- Which work items should land first — audit or organize? (Deferred to planning.)
```

---

## Conservative authoring discipline

Prefer explicit gaps over invented content. If a section requires information
that was not provided in the interview:

- Add an `Open Questions` subsection with the specific unknown.
- Do not invent scope, work items, or exit criteria.
- A sparse but accurate workstream is better than a complete but fabricated one.

This mirrors the discipline in `lrh request ready-work-item`:
"turn unresolved context into Open Questions, not invented scope."
