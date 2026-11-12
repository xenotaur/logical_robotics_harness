---
name: lrh-codex-export
description: >
  Deprecated: use /lrh-export-codex. Do not select this skill; it is a stub
  kept only so the old name still resolves, and it hands off to
  /lrh-export-codex with the same arguments.
disable-model-invocation: true
argument-hint: "[THREAD_ID]"
---

# lrh-codex-export (deprecated)

This skill was renamed to `/lrh-export-codex` under
`PROP-LRH-EXPORT-SESSION-ID-SKILL-FAMILIES` (the `lrh-export-<vendor>`
naming scheme). This stub exists only so the old name keeps working.

## What to do

Run `/lrh-export-codex` with exactly the arguments this invocation received
(for example, an optional Codex thread id), and follow that skill's steps,
confirmation behavior, and safety rules. Do not reimplement its behavior
here, and do not export anything unless the user explicitly asked for it.

If `/lrh-export-codex` is not installed, tell the user that
`lrh-codex-export` is deprecated and that they should install the current
LRH skills (`lrh skills install`) to get `/lrh-export-codex`.
