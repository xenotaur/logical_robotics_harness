---
id: PRINCIPLES-CORE
title: Logical Robotics Harness Principles
status: active
scope: project
priority: highest
applies_to:
  - all
---

# Logical Robotics Harness Principles

The Logical Robotics Harness exists to provide a reusable, evidence-oriented harness for agent-assisted
engineering and research workflows across multiple domains.

It should help projects move from goals and plans to concrete work, evidence, and status while keeping
human intent, review, and project-specific norms visible.

## Core Principles

### 1. The harness is infrastructure, not the project itself
LRH should help orchestrate work in many different projects without hard-coding itself to any one of them.

### 2. Human-readable project control comes first
The project control plane should be understandable and maintainable by humans using ordinary versioned
Markdown files with structured frontmatter.

### 3. Evidence-backed status is required
The harness should not merely report optimistic prose. It should connect work and claims to concrete
evidence such as tests, logs, metrics, screenshots, reports, or review notes.

### 4. Start with a single strong workflow before adding agentic complexity
The first implementation should support a clear end-to-end path before introducing elaborate delegation
or multi-agent behavior.

### 5. Reuse existing infrastructure where practical
LRH should reuse standards and components such as MCP, Python packaging, existing test runners,
and ordinary project repositories rather than reinventing everything.

### 6. Keep projects decoupled from the harness
A client project should remain useful and understandable even if LRH changes substantially.

### 7. Typed work and typed evidence matter
Different kinds of work require different handling. Deliverables, investigations, evaluations, and
operations should not all be collapsed into one vague task type.

### 8. The harness must be inspectable
A run should leave behind a traceable trail of decisions, actions, evidence, and status updates.

## Engineering Norms

- Prefer simple and explicit interfaces.
- Avoid hidden magic in repository discovery or project interpretation.
- Keep file formats stable and documented.
- Prefer additive iteration to large speculative designs.
- Keep project-facing concepts consistent across domains.

## Evaluation Norms

A feature is not complete unless it has:
- a clear control-model effect
- an observable workflow effect
- tests or checks where applicable
- a status/evidence consequence where appropriate
