---
name: lrh-antigravity-export
description: >
  Deprecated: use /lrh-export-antigravity. Do not select this skill; it is a
  stub kept only so the old name still resolves, and it hands off to
  /lrh-export-antigravity with the same arguments.
disable-model-invocation: true
argument-hint: "[--out OUTPUT.md] [--transcript-path PATH | --conversation-id ID | --latest]"
---

# lrh-antigravity-export (deprecated)

This skill was renamed to `/lrh-export-antigravity` under
`PROP-LRH-EXPORT-SESSION-ID-SKILL-FAMILIES` (the `lrh-export-<vendor>`
naming scheme). This stub exists only so the old name keeps working.

## What to do

Run `/lrh-export-antigravity` with exactly the arguments this invocation
received (for example `--latest` or `--conversation-id <id>`), and follow
that skill's steps and safety rules. Do not reimplement its behavior here,
and do not export anything unless the user explicitly asked for it.

If `/lrh-export-antigravity` is not installed, tell the user that
`lrh-antigravity-export` is deprecated and that they should install the
current LRH skills (`lrh skills install`) to get `/lrh-export-antigravity`.
