# LRH Design Proposal — Body Section Guide

This document describes the required and optional body sections for an LRH
design proposal, what belongs in each section, and how to write content that
follows LRH proposal conventions.

---

## Required sections

These sections should be present in every design proposal umbrella document.
They follow the reading order established in existing LRH proposals.

### `## Summary`

One to three sentences. State the design decision or direction — not the
implementation approach.

**Good:** "This proposal formalizes the execution session model for LRH,
defining a three-phase design → instruction → execution lifecycle and
optional traceability fields for Claude.app sessions."

**Avoid:** "This proposal is about execution sessions because we need them."

---

### `## Background / Motivation`

Two to four paragraphs explaining:

1. What gap, pain point, or architectural question motivates this proposal.
2. Why it needs to be addressed now (rather than later or never).
3. What prerequisite context a reader needs to evaluate the design.

Cite related design docs, workstreams, or prior proposals by file path.
Do not repeat the Summary — extend it with the "why."

---

### `## Design Decisions`

The core of the proposal. For each design decision:

1. **State the question.** What is being decided?
2. **List the options considered.** What alternatives were on the table?
3. **State the chosen option and rationale.** Why this one over the others?

Use subsections (`### Decision 1: …`) for multi-decision proposals.

**Good:**

```
### Decision: Artifact location for execution records

Options considered:
- `project/runs/` — established but overloaded with Codex-specific semantics
- `project/executions/` — neutral, maps to the "execution phase" vocabulary
- `project/sessions/` — too closely tied to Claude.app sessions

**Chosen: `project/executions/`** — neutral, matches the phase model vocabulary,
extensible to future execution backends.
```

---

### `## Non-Goals`

A bulleted list of things this proposal explicitly does **not** address.
Each entry should be something a reader might otherwise assume is covered.

Write as negative imperatives:

```
- Does not define runtime execution behavior — proposals are documentation only.
- Does not supersede PROP-LRH-PROJECT-LOCAL-SKILLS — that proposal governs
  skill distribution; this one governs session traceability.
```

---

### `## Implementation Plan`

A staged breakdown of how the design decision will be implemented. Reference
the appropriate artifacts:

- **Small scope (one PR):** name the work item ID or describe the single PR.
- **Medium scope (multiple PRs):** list the PRs/work items in proposed
  delivery order.
- **Large scope (multi-stage):** reference the governing workstream (`WS-*`)
  and note that individual work items are defined there.

This section is distinct from `## Design Decisions` — it answers "what gets
built and in what order" rather than "what was decided."

---

## Optional sections

### `## Cross-References`

A list of related documents, proposals, and design files:

```
- Canonical design: `project/design/architecture.md`
- Prior proposal: `project/design/proposals/adopted/lrh-project-local-skills/`
- Related workstream: `project/workstreams/proposed/WS-SKILLS.md`
```

Proposals must reference rather than duplicate canonical documents. When a
proposal would update `design.md` or `architecture.md`, state the diff in
narrative form here.

---

### `## Open Questions`

Any unresolved questions that the proposal leaves open. Use this section
rather than blocking a proposal on incomplete details.

```
- Should sub-proposals share the parent's `PROP-` ID prefix? (Deferred.)
```

---

## Conservative authoring discipline

Prefer explicit gaps over invented content. If a section requires information
that was not provided in the interview:

- Add an `Open Questions` subsection with the specific unknown.
- Do not invent scope, design decisions, or implementation steps.
- A sparse but accurate proposal is better than a complete but fabricated one.

This mirrors the discipline in `lrh request ready-work-item`:
"turn unresolved context into Open Questions, not invented scope."
