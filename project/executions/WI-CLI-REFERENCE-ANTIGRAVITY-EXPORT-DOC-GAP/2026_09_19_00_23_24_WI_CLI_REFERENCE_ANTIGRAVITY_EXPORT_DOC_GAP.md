---
execution_id: 2026_09_19_00_23_24_WI_CLI_REFERENCE_ANTIGRAVITY_EXPORT_DOC_GAP
prompt_id: PROMPT(WI-CLI-REFERENCE-ANTIGRAVITY-EXPORT-DOC-GAP:WI_CLI_REFERENCE_ANTIGRAVITY_EXPORT_DOC_GAP)[2026-09-19T00:21:40+00:00]
work_item: WI-CLI-REFERENCE-ANTIGRAVITY-EXPORT-DOC-GAP
status: in_progress
rerun_of: 
pr: https://github.com/xenotaur/logical_robotics_harness/pull/671
commit: 
created_at: 2026-09-19T00:23:24+00:00
agent: claude_app
instruction_source: project/work_items/proposed/WI-CLI-REFERENCE-ANTIGRAVITY-EXPORT-DOC-GAP.md
session_transcript: claude-app:3278dd49-9852-4955-b978-00367552dc27
---

# Summary

Add the missing `##`-level `lrh conversation export-antigravity-session`
section to `docs/reference/cli/conversation.md`, closing a pre-existing
documentation-parity gap: the subcommand has been implemented and
registered (`src/lrh/cli/main.py:157-161`) and adopted
(`PROP-LRH-ANTIGRAVITY-CONVERSATION-EXPORTER`) since PR #625, but was
never documented alongside the Codex subcommands.

# Result

Implemented via `/lrh-execute`'s inlined `/lrh-implement`:

- `docs/reference/cli/conversation.md`: added a new `##`-level
  `lrh conversation export-antigravity-session` section, placed
  immediately before `## lrh conversation export-claude-session`
  (matching their adjacent order in `src/lrh/cli/main.py`'s subparser
  registration). Documents command syntax, the
  `--transcript-path`/`--conversation-id`/`--latest` discovery group,
  `--app-data-dir` (default `~/.gemini/antigravity`), `--out`,
  `--archive-root`, `--force`, `--source-id`, `--no-scan-sensitive`, and
  exit behavior — matching the depth of the existing
  `## lrh conversation convert-codex-file` section.

**Pre-push diff-mode self-review** (`/lrh-implement` Step 7.5) found and
fixed one real issue: the `--source-id` bullet was drafted by adapting
the sibling `export-claude-session` section's wording ("defaults to the
transcript filename stem") without checking antigravity's own
`_derive_source_id()` implementation, which actually returns the
conversation-ID path segment following `brain/` when derivable, else a
12-character SHA-256 prefix — never `path.stem`. Independently
re-verified by reading both `_derive_source_id` implementations
directly (Claude's genuinely uses `path.stem`; Antigravity's does not).
Fixed to describe the real fallback behavior. Full execution record:
`project/executions/AD_HOC/2026_09_19_00_21_55_WI_CLI_REFERENCE_ANTIGRAVITY_EXPORT_DOC_GAP_SELFREVIEW.md`.

Publication: pushed directly, PR opened at
https://github.com/xenotaur/logical_robotics_harness/pull/671.

# Validation

- `lrh validate` — 0 errors, 1 pre-existing unrelated warning
  (`WI-GATE-STALENESS-INSTALLED-TARGET-FINGERPRINT.md`, not touched by
  this branch).
- `grep -n "export-antigravity-session" docs/reference/cli/conversation.md`
  — new section present.

# Follow-up

- Continue `/lrh-execute`'s chain: Step 4 (`/lrh-land`) for PR #671.
