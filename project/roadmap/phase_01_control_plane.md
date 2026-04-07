---
id: ROADMAP-PHASE-01
title: Control Plane
status: active
parent: ROADMAP-CORE
order: 1
success_criteria:
  - project directory schema is documented
  - Markdown + frontmatter parsing works
  - core Python models exist
  - precedence rules are implemented
  - validation CLI works
---

# Phase 1 — Control Plane

This phase establishes the language of the harness.

## Deliverables

- repository spec
- frontmatter conventions
- internal models for all project objects
- loader/parser/resolver
- validation commands

## Why this comes first

Without a stable control plane, all later runtime or agent behavior becomes brittle and project-specific.

## Risks

- over-designing the schema
- confusing source documents with runtime objects
- unclear authority between focus, roadmap, and work items
