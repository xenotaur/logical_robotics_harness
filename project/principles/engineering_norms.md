---
id: PRINCIPLES-ENGINEERING
title: Engineering Norms
status: active
scope: project
priority: high
applies_to:
  - implementation
---

# Engineering Norms

## Code Organization

- Keep the `lrh/` package modular by concern.
- Do not tightly couple CLI logic to the internal data model.
- Keep adapters isolated from the core control model.

## Style

- Favor readable Python over clever abstractions.
- Prefer explicit typed models over ad hoc dictionaries for internal state.
- Preserve a clean boundary between source Markdown and parsed runtime objects.

## Repository Discipline

- Keep sample projects and example fixtures small and comprehensible.
- Maintain at least one end-to-end example repository layout in tests or fixtures.
- Document precedence and resolution rules in code and docs, not just conversation.
