---
name: lrh-codex-session
description: 'Deprecated: use /lrh-session-id-codex. Do not select this skill; it
  is a stub kept only so the old name still resolves, and it hands off to /lrh-session-id-codex
  with the same arguments.

  '
---

# lrh-codex-session (deprecated)

This skill was renamed to `/lrh-session-id-codex` under
`PROP-LRH-EXPORT-SESSION-ID-SKILL-FAMILIES` (the `lrh-session-id-<vendor>`
naming scheme). This stub exists only so the old name keeps working.

## What to do

Run `/lrh-session-id-codex` with exactly the arguments this invocation
received (for example, an optional Codex thread id), and follow that skill's
steps and safety rules. Do not reimplement its behavior here.

If `/lrh-session-id-codex` is not installed, tell the user that
`lrh-codex-session` is deprecated and that they should install the current
LRH skills (`lrh skills install`) to get `/lrh-session-id-codex`.
