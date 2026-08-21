---
id: DEC-LRH-MEMORY-AUTHORED-BY
---

# `lrh memory` Frontmatter Adds `metadata.authored_by` and `metadata.applies_to`

Status: accepted
Date: 2026-08-20

## Summary

`lrh memory write` adds two fields to Claude Code's pre-existing memory
frontmatter schema (`name`, `description`, `metadata.type`):
`metadata.authored_by` (required for new writes) and
`metadata.applies_to` (optional, defaults to `[authored_by]`).
`authored_by` is required only going forward, at write time — it is not
retroactively required of the ~440 pre-existing memory files that already
conform to the old schema; `lrh memory validate` reports those as a
distinct `legacy` category, not `malformed`, and `lrh memory repair` is
the tool that closes that gap incrementally.

## Context

- `experimental/rescue_claude_sessions/findings.md` documented 19 of 461
  memory files across 5 project buckets lacking required frontmatter, and
  one concrete contamination case: Codex wrote a memory file into a
  Claude-authored corpus with no `MEMORY.md` entry, so a Claude session
  reading that corpus would have read Codex-specific sandbox guidance as
  if it were its own — with no field distinguishing whose guidance it
  was.
- `PROP-LRH-MEMORY-COMMAND` Decision 3 designed `authored_by`/
  `applies_to` to close exactly that gap: attribution becomes a validated
  field, not an inference from filename convention (which the findings
  document as unreliable — "inference from naming... not proof").

## Decision

1. `metadata.authored_by` is **required** on every `lrh memory write`
   call — the CLI rejects a write with no `--agent`.
2. `metadata.authored_by` is **not** retroactively required of files that
   already conform to the pre-existing schema. `lrh memory validate`
   reports two tiers: **malformed** (missing `name`/`description`/
   `metadata.type` — the original, worse defect, unreachable by recall)
   and **legacy** (conforming, simply predating `authored_by` — reachable
   and correct, just unattributed). Treating `authored_by` as
   universally required would have flagged nearly the entire existing
   corpus as non-conforming, conflating it with the 19 genuinely broken
   files.
3. `metadata.applies_to` defaults to `[authored_by]` when omitted, and is
   never required explicitly — it exists so one agent can deliberately
   write guidance intended for another without ambiguity, not as a
   second mandatory field.
4. `lrh memory repair --set metadata.authored_by=<agent>` is the tool
   that closes the legacy gap, file by file, without requiring a
   whole-corpus migration in one pass. `repair` preserves the original
   `authored_by` unless the caller's `--set` explicitly overrides it — a
   structural fix is not a re-authoring.

## Alternatives considered

1. **Make `authored_by` required corpus-wide, immediately.** Rejected —
   would make `validate` flag ~440 correct files as broken on day one,
   with no incremental path to fix them.
2. **Infer `authored_by` from filename convention instead of a validated
   field.** Rejected — this is the exact mechanism the findings document
   as already having failed silently.
3. **Auto-detect `authored_by` from environment** (analogous to how
   `session_transcript` reads `CLAUDE_CODE_HOST_SESSION_ID`) instead of
   requiring an explicit `--agent` flag. Left open — recorded as an
   unresolved Open Question in `PROP-LRH-MEMORY-COMMAND`, not decided
   here; `--agent` is explicit and required for Stage 1.

## Consequences

- `lrh memory validate`'s two-tier report is now load-bearing for
  `WI-LRH-MEMORY-WRITE-SIDE`'s own acceptance criteria and for any future
  retroactive-cleanup work against the 19 known malformed files.
- `src/lrh/skills/lrh-closeout/SKILL.md`'s Step 7 (session reflection)
  now calls `lrh memory write` instead of writing memory files directly,
  so the canonical LRH workflow that most frequently writes memory no
  longer bypasses this validation.

## Revisit conditions

Revisit when the `authored_by`-auto-detection Open Question
(`PROP-LRH-MEMORY-COMMAND`) is resolved, or when a retroactive cleanup
pass against the 19 known malformed files is scoped — at that point,
confirm whether the malformed/legacy split still needs both categories or
whether malformed has been fully closed out.
