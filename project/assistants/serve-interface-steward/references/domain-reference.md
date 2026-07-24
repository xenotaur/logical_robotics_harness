# Reference — Domain: the `lrh serve` interface

Loaded on demand. Orientation for the subject-matter domain this role stewards.

`lrh serve` is LRH's local operational-triage surface. It renders control-plane
state (focus, workstreams, work items, runs, evidence, status) for a human
operator. The steward's remit is the **interface** to that state — clarity,
navigability, and accessibility — not the underlying control-plane semantics,
which belong to other owners.

Managed surface (see `scope.md` for authoritative paths):

- `src/lrh/serve.py`, `src/lrh/serve_triage.py` — the serve entry point and
  triage rendering.
- `src/lrh/ux/**` — shared UX helpers.
- `tests/ux_tests/**` — the interface tests.

Read-only context the steward inspects but does not manage: `core_state.py`
(the deterministic read-only composition serve reads from), and the planning
and run artifacts under `project/`.

Domain priorities, in tie-break order (from `preferences.md`): correctness over
speed, clarity over cleverness, evidence over summary, and accessibility over
visual minimalism. Interface changes that affect what state is considered
authoritative, or that alter a public CLI surface, are **out of scope for
unilateral change** and must be surfaced for decision.
