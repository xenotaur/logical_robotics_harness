# Canonical Precedence Semantics

Status: accepted  
Date: 2026-04-22

## Context

LRH documentation had drifted on precedence semantics.

- `src/lrh/control_plane/precedence.py` already implemented deterministic behavior where
  runtime directives narrow scope and guardrails constrain results.
- `project/design/design.md` and `project/context/humans.md` described a mostly compatible
  conceptual ordering, but included wording that could be read as contradictory
  (for example, saying "low → high" while listing principles first).
- `docs/repository_spec.md` described a conflicting precedence ordering and included
  memory as a precedence layer.

This ambiguity makes implementation, review, and future changes error-prone.

## Options considered

1. **Adopt `docs/repository_spec.md` ordering** (runtime first and memory in the chain).
2. **Keep implementation semantics and codify them as canonical**.
3. **Redesign the model now** to include new precedence layers and richer override behavior.

## Decision

LRH canonical precedence semantics are the current implementation model in
`src/lrh/control_plane/precedence.py`.

Resolution is applied from broad intent to narrow execution context:

1. principles
2. goal
3. roadmap
4. focus
5. work items
6. guardrails
7. runtime invocation

### Operational meaning

- **Higher authority = stronger constraint.**
  Earlier layers constrain later layers.
- **Lower layers refine, not override, higher layers.**
  Focus narrows roadmap intent; work items operationalize focus.
- **Guardrails are subtractive constraints.**
  Guardrails can block candidates (for example blocked work items or contributors)
  but do not define positive scope on their own.
- **Runtime invocation is narrowing-only.**
  Runtime inputs may select a subset of already-allowed focus/work/contributors;
  they must not reintroduce entities removed by guardrails or violate higher layers.
- **Memory is non-authoritative for precedence resolution.**
  Memory informs future planning and interpretation but is not a precedence layer in
  resolver computation.

## Invariants

Any precedence implementation or change must preserve these invariants:

1. Lower-authority layers cannot widen scope beyond higher-authority constraints.
2. Guardrail exclusions remain excluded after runtime narrowing.
3. Runtime selection can only intersect already-allowed sets.
4. Focus mismatch at runtime is reported as a consistency issue rather than silently
   overriding loaded focus state.
5. Resolver output is deterministic for identical inputs.

## Consequences

- All precedence references in docs should link to or summarize this record.
- Implementation and tests should remain synchronized with this decision.
- Any future precedence redesign must update this record, implementation, and tests
  in the same change set.
