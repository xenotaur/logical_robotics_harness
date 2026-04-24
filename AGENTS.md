# AGENTS.md

This repository is the home of **Logical Robotics Harness (LRH)**.

LRH is intended to be a reusable harness for structured, evidence-backed, agent-assisted workflows across multiple independent project repositories.

## Mission

Build a harness that can:

- load a project's `project/` control directory
- parse and validate human-readable Markdown + frontmatter control files
- model principles, goals, roadmaps, focus, work items, evidence, and status
- orchestrate bounded work in a project repository
- synthesize evidence-backed status

## Architectural boundary

Keep clear separation between:

1. **the harness code** in `src/lrh/`
2. **package tests** in `tests/`
3. **maintainer-only AI programming helpers** in `scripts/aiprog/`
4. **the harness's own project control plane** in `project/`
5. **future client project repositories**, which will also have their own `project/` directories

Do not hard-code LRH to this repository only. The repository should be self-hosting at the control-plane level, but the code should remain reusable for other projects.

## Current implementation priority

Focus first on the smallest end-to-end slice:

1. core control-model classes
2. Markdown/frontmatter parser
3. project directory loader
4. precedence resolver and validation checks
5. `lrh validate`

Do **not** jump ahead to multi-agent orchestration or deep MCP integration before the control-plane slice works.

## Repository conventions

### Project schema

The project control stack is:

**Principles → Project Goal → Roadmap → Current Focus → Work Items → Evidence → Status**

The `project/` directory is the human-readable source of truth.

### Source vs runtime model

Maintain a strict boundary between:

- source Markdown documents under `project/`
- runtime structured objects inside `src/lrh/`

Do not treat raw dictionaries as the long-term internal API if a typed model is appropriate.

### Work item types

At minimum, preserve these work item categories:

- `deliverable`
- `investigation`
- `evaluation`
- `operation`

### Evidence

Status should be grounded in evidence.
Do not generate optimistic summaries that are detached from tests, logs, metrics, screenshots, reports, or review notes.

## Precedence maintenance note

- Canonical precedence semantics are defined in `project/memory/decisions/precedence_semantics.md`.
- Any precedence change must keep documentation, `src/lrh/control_plane/precedence.py`, and `tests/control_plane/test_precedence.py` synchronized in the same change set.

## Engineering style

- Prefer readable, explicit Python.
- Prefer modular organization by concern.
- Avoid hidden magic in repo discovery.
- Keep formats stable and documented.
- Preserve human readability of `project/` documents.

## Immediate task guidance

When asked to make progress in this repository, prefer work that advances the first validation path:

- define models
- load files
- validate references and precedence
- expose a basic CLI
- add tests

## Out of scope for the first slice

- complex agent societies
- deep vendor-specific integrations
- fancy UI
- premature optimization

## Prompt-driven work

When a task is driven by a generated prompt, follow `PROMPTS.md` for prompt IDs, execution records, rerun handling, and optional work-item traceability. Do not create prompt records for trivial or purely exploratory work unless asked.
