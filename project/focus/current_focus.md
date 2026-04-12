---
id: FOCUS-HARDEN-CONTROL-PLANE
title: Harden the control plane and operational workflow
status: active
priority: high
owner: anthony
related_principles:
  - PRINCIPLES-ENGINEERING
  - PRINCIPLES-EVALUATION
---

# Current Focus

The immediate priority is to **harden the LRH control plane so it is reliable, enforceable, and usable as a daily workflow tool**.

The bootstrap milestone has shown that LRH can represent and validate its own `project/` directory.
Now the goal is to make that capability robust enough to support real development workflows and future multi-repository use.

---

## Why this is active now

LRH has successfully demonstrated:

- a working project control model (`project/`)
- a validator that can load and check that model
- a coherent representation of principles, goal, roadmap, focus, and work items

However, the system is still in a **bootstrap-quality state**:

- parsing is minimal and fragile (custom YAML parser)
- validation is not yet enforced in all workflows
- contributor and workflow semantics are only lightly exercised
- developer ergonomics are not yet fully established

Before expanding scope (e.g., to external repositories or agent autonomy), LRH must become **stable and trustworthy as infrastructure**.

---

## Priorities

1. **Strengthen parsing and validation reliability**
   - Replace or harden the bootstrap YAML/frontmatter parser
   - Ensure validator correctness on realistic inputs
   - Expand test coverage for edge cases

2. **Integrate validation into the development workflow**
   - Ensure `lrh validate` is part of CI (tests workflow)
   - Ensure local workflows (`scripts/validate`) are consistent and reliable
   - Establish clear failure modes and error messaging

3. **Stabilize contributor and ownership semantics**
   - Ensure contributor records are well-formed and minimally complete
   - Ensure consistent use of contributor IDs across all artifacts
   - Validate focus, roadmap, and work item references rigorously

4. **Improve control-plane observability**
   - Ensure tools like `snapshot.py` produce clear, correct summaries
   - Validate that LRH can correctly interpret:
     - current focus
     - active contributors
     - work item state

---

## Non-Goals (for this focus)

To keep the slice narrow and testable, do **not**:

- introduce multi-repository orchestration
- redesign the project schema
- add complex agent autonomy or planning logic
- expand into execution engines beyond current tooling

---

## Exit Criteria

This focus is complete when:

1. **Validation is robust and enforced**
   - `lrh validate` passes on the LRH repository
   - validation is integrated into CI and consistently enforced

2. **Parsing is production-appropriate**
   - the bootstrap parser is replaced or hardened
   - realistic frontmatter is correctly handled

3. **Control-plane semantics are stable**
   - contributor, owner, and reference relationships are consistent and validated
   - no ambiguity in contributor resolution

4. **LRH can reliably introspect its own state**
   - tools like `snapshot.py` produce accurate, interpretable summaries
   - LRH can identify:
     - current focus
     - active contributors
     - relevant work items

5. **The system remains narrow and testable**
   - changes are covered by tests where appropriate
   - the control-plane slice remains understandable and reviewable

---

## Notes

This focus completes **Phase 1 (Control Plane Hardening)** of the roadmap.

Once complete, LRH will be ready to:

- operate reliably on its own repository
- extend to external project directories
- support more advanced agent-assisted workflows