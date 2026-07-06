# LRH Architecture

## Overview

Logical Robotics Harness (LRH) is a reusable workflow harness for structured, evidence-backed, agent-assisted work across multiple repositories.

It is **not** the client project itself. Instead, it operates against a target repository that contains a human-readable `project/` directory describing the project's intent, planning state, active focus, work queue, action decisions, guardrails, evidence, and status.

## Core separation

The architecture is intentionally decoupled.

### 1. Harness repository / package

The harness repository contains reusable package code in `src/lrh/` such as:

- control-model parsing
- orchestration
- workspace adapters
- evidence handling
- status synthesis
- guardrail reporting
- tool integration

Maintainer-only AI programming helpers live in `scripts/aiprog/` and are outside the supported package API boundary.

### 2. Client project repository

A client project repository contains:

- its own source code and assets
- project-specific scripts and tooling
- its own `project/` control plane

### 3. Runtime tool environment

A runtime environment may provide:

- local commands
- MCP servers
- build/test tools
- sandboxing and approval controls

## Package and distribution boundary

The canonical user-facing distribution and CLI target is `lrh`. The
default distribution should be safe-default and non-agentic so normal CLI
users can install LRH with `pipx install lrh` once PyPI publishing is
available. Safe-default user assistance may include local commands such as
`lrh validate`, `lrh snapshot`, `lrh request`, and a local `lrh serve`
viewer/prompt workbench that projects control-plane state without autonomous
dispatch or branch mutation. Future agentic capability should remain explicit
through `lrh[agentic]` and/or a separate `lrh-agentic` distribution when that
package exists.

This package split direction is a packaging and governance boundary, not
a runtime security sandbox claim. The accepted release architecture is
tag-push publishing of the safe-default `lrh` package via PyPI Trusted
Publishing, with TestPyPI rehearsal and installed-package smoke evidence
introduced through follow-on implementation PRs.

## Four-plane model

The project control model is:

- **Intent Plane**: Principles → Project Goal → Roadmap
- **Execution Plane**: Current Focus → Work Items → Actions
- **Truth Plane**: Evidence → Status
- **Consequences Plane**: Guardrails (Safety, Cost, Optics, Approvals)

### Intent plane

- Principles
- Project Goal
- Roadmap

This answers: **why are we doing this, and where are we headed?**

### Execution plane

- Current Focus
- Work Items
- Actions

This answers: **what are we doing now and what execution units are being proposed?**

### Truth plane

- Evidence
- Status

This answers: **what is actually true right now?**

### Consequences plane

- Guardrails
  - Safety
  - Cost
  - Optics
  - Approvals

This answers: **what constraints, risks, and authorization boundaries apply to proposed actions?**

Canonical precedence semantics are documented in `project/memory/decisions/precedence_semantics.md`.
See `design.md` §14 ("Decision-record tiers") for why this decision is a
promoted single-topic file rather than an entry in `project/memory/decision_log.md`.


## Execution lifecycle

Execution should move through an explicit lifecycle:

**Work Item → Action Proposal → Guardrail Review → Action Decision → Execution → Evidence → Status**

This separates execution intent from consequence review and keeps decision records inspectable.

## Human-readable source + structured runtime

Each project control object should exist in two forms:

1. Markdown + YAML frontmatter in `project/`
2. structured runtime objects inside `src/lrh/`

The Markdown files are the human-readable source of truth for collaboration.
The runtime model is the typed internal representation used by LRH.

## Initial implementation layers

The initial LRH implementation should emphasize these layers:

### Control model

Define structured internal models for:

- principles
- project goal
- roadmap
- current focus
- work items
- actions
- guardrails
- evidence
- status

### Document/context layer

Load Markdown files, parse frontmatter, normalize objects, and validate references.

### Workflow layer

Start small. The first useful workflow is validation rather than full orchestration.

### Evidence and status

Evidence should be first-class. Status should be synthesized from evidence and work state rather than being only hand-written prose.

## First milestone

The first meaningful milestone is self-hosting at the control-plane level.

That means LRH should be able to load and validate its own repository's `project/` directory.

The first useful command is therefore:

```bash
lrh validate
```

## Future direction

After the control plane and validation workflow exist, LRH can expand to:

- workspace adapters for external repositories
- run management
- evidence recording
- status synthesis
- MCP/tool integration
- agent runtime integration
- guardrail evaluation and approval workflows
