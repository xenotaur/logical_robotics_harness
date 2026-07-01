# Design Backlog

Lightweight list of deferred ideas that are not yet ready for a formal
proposal or work item. Each entry should record what was noted, why it was
deferred, and where it came from so a future reader can act on it without
re-deriving context.

---

## Validator drift-check for synced skill references

**Noted:** 2026-06-30, during `WS-PRIOR-ART-CHECK` design session.

**Idea:** Extend `lrh validate` (or a small standalone script) to diff each
consuming skill's copy of a shared reference doc against the `_shared/`
master and fail on drift — replacing the comment-only sync convention
currently used for `prior-art-check.md` copies.

**Status:** Deferred — not in scope for `WS-PRIOR-ART-CHECK`. The current
approach is a header comment in each copy naming the master file. Revisit
if copies are observed drifting in practice.

**Related:** `project/workstreams/proposed/WS-PRIOR-ART-CHECK.md` Non-Goals.
