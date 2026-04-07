# LRH Architecture

## Overview

Logical Robotics Harness (LRH) is a reusable workflow harness for structured, evidence-backed, agent-assisted work across multiple repositories.

It is **not** the client project itself. Instead, it operates against a target repository that contains a human-readable `project/` directory describing the project's intent, planning state, active focus, work queue, evidence, and status.

## Core separation

The architecture is intentionally decoupled.

### 1. Harness repository / package

The harness repository contains reusable code such as:

- control-model parsing
- orchestration
- workspace adapters
- evidence handling
- status synthesis
- policy and reporting
- tool integration

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

## Control stack

The project control stack is:

**Principles → Project Goal → Roadmap → Current Focus → Work Items → Evidence → Status**

This can be understood as three planes.

### Intent plane

- Principles
- Project Goal
- Roadmap

This answers: **why are we doing this, and where are we headed?**

### Execution plane

- Current Focus
- Work Items

This answers: **what are we doing now?**

### Truth plane

- Evidence
- Status

This answers: **what is actually true right now?**

## Human-readable source + structured runtime

Each project control object should exist in two forms:

1. Markdown + YAML frontmatter in `project/`
2. structured runtime objects inside `lrh/`

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
- policy and approval controls
