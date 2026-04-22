# Repository Specification

## Repository purpose

This repository contains the reusable implementation of Logical Robotics Harness.

The harness should eventually be installable as a package and runnable against independent project repositories.

## Top-level layout

```text
logical_robotics_harness/
  README.md
  AGENTS.md
  pyproject.toml
  docs/
  src/
    lrh/
  tests/
  scripts/
    aiprog/
  project/
```

## The `project/` directory

The `project/` directory is the human-readable control plane for a project.

For LRH itself, this repository includes its own `project/` directory so that the harness can bootstrap against itself.

### Expected layout

```text
project/
  principles/
  goal/
  roadmap/
  focus/
  work_items/
  guardrails/
  evidence/
  status/
  memory/
```

## Object categories

### Principles

Defines norms, constraints, engineering expectations, and evaluation expectations.

### Project Goal

Defines what the project is for and what success looks like.

### Roadmap

Defines medium-term phases, milestones, or epics.

### Current Focus

Defines the active near-term operational charter.

### Work Items

Defines typed units of work such as deliverables, investigations, evaluations, and operations.

Work item metadata may include:

- `expected_actions`: action categories that are likely needed to complete the item
- `forbidden_actions`: action categories prohibited for this item

These are documented schema fields in this phase and are not yet enforced by runtime logic.

### Guardrails

Defines the consequences plane for action review:

- safety
- cost
- optics
- approvals

Guardrails are evaluated during action review before execution decisions are finalized.

### Evidence

Defines proof artifacts or findings tied to work.
Evidence should include notable action outcomes such as:

- blocked actions
- modified actions
- approval records

### Status

Defines synthesized state grounded in current focus, work, and evidence.
Status should include a guardrail summary section describing:

- blocked actions
- pending approvals
- safety/cost/optics warnings

### Memory

Stores lower-authority notes such as decision logs, open questions, and lessons learned.

## File format

Use Markdown with YAML frontmatter.

### Example

```md
---
id: WI-0001
title: Example work item
type: deliverable
status: ready
priority: high
related_focus:
  - FOCUS-BOOTSTRAP
expected_actions:
  - code_change
forbidden_actions:
  - production_write
acceptance:
  - Something measurable happens
required_evidence:
  - test_result
---

# Example work item

Body text here.
```

## Precedence

Canonical precedence semantics are defined in
`docs/decisions/precedence_semantics.md`.

Resolver precedence order is:

1. principles
2. project goal
3. roadmap
4. current focus
5. work items
6. guardrails
7. runtime invocation

Interpretation rules:

- Higher-authority layers are stronger constraints.
- Lower-authority layers may refine/narrow scope, but may not override higher layers.
- Guardrails are subtractive constraints.
- Runtime invocation is narrowing-only and cannot override guardrails.
- Memory is informative but non-authoritative for precedence resolution.

## Initial Python package targets

The initial `src/lrh/` package should likely grow modules such as:

```text
src/lrh/
  cli/
  control/
  orchestration/
  runtime/
  workspace/
  evidence/
  status/
  guardrails/
  reporting/
  adapters/
```

## Initial implementation slice

The first practical slice should include:

- control-model classes
- frontmatter parser
- project loader
- resolver/validator
- basic CLI command for validation

## Initial command target

```bash
lrh validate
```

This should validate the local repository's own `project/` directory.
