# Serve Interface Steward

This directory defines an LRH assistant role.

Read first:

1. `assistant.md`
2. `scope.md`
3. `policy.md`
4. `preferences.md`
5. `communication-policy.md`
6. `context-policy.md`
7. `review-policy.md`
8. `SKILL.md`

Live planning and run state do **not** live in this directory. This package is
stable role configuration only.

To orient once inspection tooling exists (Stage 5 of `WS-LRH-ASSISTANTS`):

```
lrh assistant context ASST-SERVE-INTERFACE-STEWARD --view current
```

Until then, read the files above directly, and inspect the root workstream that
declares this assistant in its `managed_by` field to see what it is currently
managing.

This assistant is backend-neutral: the same package may be instantiated through
Claude, Codex, Jules, another runtime, or a human following the same files. The
contributor or execution record — not this directory — identifies the actual
actor that performed any work.
