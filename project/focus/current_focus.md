---
id: FOCUS-CONTROL-PLANE-SEMANTICS
title: Complete control-plane semantics and resolution
status: active
priority: high
owner: anthony
related_principles:
  - PRINCIPLES-ENGINEERING
  - PRINCIPLES-EVALUATION
---

# Current Focus

The immediate priority is to **complete the control plane by ensuring that LRH can correctly interpret, resolve, and reason about project state—not just parse and validate it.**

The bootstrap milestone established that LRH can load and validate its own `project/` directory.
This focus completes Phase 1 by making the control plane **semantically correct and reliable**.

---

## Why this is active now

LRH can now:

- represent its control plane in `project/`
- validate that structure with `lrh validate`
- produce structured summaries via tools like `snapshot.py`

However, Phase 1 requires more than structural correctness.

The system must also:

- resolve precedence between control-plane elements
- interpret focus and work items correctly
- behave predictably under real project conditions

This focus ensures the control plane is not just valid, but **meaningful and executable as infrastructure**.

---

## Priorities

1. **Define and enforce precedence rules**
   - clarify authority between:
     - focus
     - roadmap
     - work items
   - implement precedence resolution in code
   - ensure behavior is deterministic and documented

2. **Validate semantic interpretation**
   - ensure LRH can correctly identify:
     - current focus
     - active contributors
     - relevant work items
   - confirm tools (e.g., `snapshot.py`) reflect true project state

3. **Strengthen parsing reliability (targeted)**
   - improve or replace bootstrap YAML/frontmatter parsing
   - ensure realistic Markdown inputs are handled correctly
   - avoid silent misinterpretation

4. **Expand evaluation coverage**
   - add tests that demonstrate:
     - correct parsing
     - correct resolution
     - correct interpretation
   - align with evaluation norms

---

## Non-Goals

To keep Phase 1 bounded, do not:

- expand to multi-repository workflows
- introduce agent autonomy or planning systems
- redesign the project schema
- build execution engines beyond validation and interpretation

---

## Exit Criteria

This focus is complete when:

1. **Precedence is defined and implemented**
   - control-plane authority rules are explicit
   - resolution behavior is deterministic and tested

2. **Interpretation is correct**
   - LRH can reliably determine:
     - current focus
     - active contributors
     - relevant work items
   - snapshot and related tools reflect correct state

3. **Parsing is reliable for real inputs**
   - frontmatter parsing handles realistic cases
   - no known fragile edge cases in normal usage

4. **Evaluation norms are satisfied**
   - LRH demonstrably:
     - parses correctly
     - resolves correctly
     - interprets correctly

---

## Notes

This focus completes **Phase 1 — Control Plane**.

The next phase will begin once the control plane is not only valid, but **semantically correct and operationally reliable**.