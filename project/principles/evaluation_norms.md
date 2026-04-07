---
id: PRINCIPLES-EVALUATION
title: Evaluation Norms
status: active
scope: project
priority: high
applies_to:
  - validation
  - status
  - evidence
---

# Evaluation Norms

## What LRH must prove

The harness must show that it can:

1. parse a project control plane correctly
2. resolve precedence correctly
3. identify current focus correctly
4. interpret work items correctly
5. record evidence correctly
6. synthesize status correctly

## Preferred Evidence

- unit tests for parsing and model behavior
- integration tests for project loading
- example-generated status snapshots
- example evidence records
- reproducible CLI outputs

## Anti-Patterns

- status generated without evidence links
- undocumented precedence conflicts
- project-specific assumptions embedded in core logic
- claiming multi-project support without at least two distinct example projects
