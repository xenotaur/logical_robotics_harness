---
resolution: null
blocked_reason: null
blocked: false
id: WI-CLI-REFERENCE-ANTIGRAVITY-EXPORT-DOC-GAP
title: Document lrh conversation export-antigravity-session in the CLI reference
type: deliverable
status: proposed
owner: null
contributors: []
assigned_agents: []
related_focus: []
related_roadmap: []
related_workstreams: []
related_design:
  - project/design/proposals/adopted/lrh-antigravity-conversation-exporter/00_proposal.md
depends_on: []
blocked_by: []
expected_actions:
  - edit_file
forbidden_actions:
  - force_push
  - delete_branch
acceptance:
  - "docs/reference/cli/conversation.md contains a ##-level lrh conversation export-antigravity-session section"
  - "The new section documents command syntax, all flags (--transcript-path, --conversation-id, --latest, --app-data-dir, --out, --archive-root, --force, --source-id, --no-scan-sensitive), and exit behavior, matching the depth of the existing Codex sections"
  - "lrh validate reports 0 errors"
required_evidence:
  - manual_review
  - lrh_validate
artifacts_expected:
  - docs/reference/cli/conversation.md
---

# WI-CLI-REFERENCE-ANTIGRAVITY-EXPORT-DOC-GAP: Document lrh conversation export-antigravity-session in the CLI reference

## Summary

Add the missing `##`-level `lrh conversation export-antigravity-session` section to `docs/reference/cli/conversation.md`, closing a pre-existing documentation-parity gap.

## Problem / Context

`docs/reference/cli/conversation.md` documents every Codex conversation subcommand (`current-codex-thread-id`, `convert-codex-file`, `export-codex-thread`, `archive-codex-thread`, `import-codex-exports`, `inspect-export`, `convert-pdf`) but has no entry at all for `export-antigravity-session` — a subcommand that has been implemented, registered in `src/lrh/cli/main.py:157-161`, and adopted (`PROP-LRH-ANTIGRAVITY-CONVERSATION-EXPORTER`, `status: adopted`) since PR #625. This gap was noticed while designing the parallel Claude Code exporter (`PROP-LRH-CLAUDE-CONVERSATION-EXPORTER`) and is unrelated to that proposal's own scope — fixing it here rather than folding it into the Claude proposal keeps that proposal's design decisions from being diluted by an orthogonal docs fix.

### Duplication search
- In-repo: No existing `export-antigravity-session` section anywhere under `docs/`.
- Sibling repos: None identified.
- External libraries: Not applicable.
- Recommendation: Proceed.

### Demand search
- Work items: None found requesting this directly.
- Proposals: Noted as an Open Question in `PROP-LRH-CLAUDE-CONVERSATION-EXPORTER`'s "Whether `docs/reference/cli/conversation.md` should also gain the missing `export-antigravity-session` entry" — this work item resolves that open question independently.
- Backlog: No matching entries.
- Recommendation: No action beyond this item.

## Scope

- Add one new `##` section to `docs/reference/cli/conversation.md` documenting `lrh conversation export-antigravity-session`.
- Mirror the structure and depth of the existing `##`-level `lrh conversation convert-codex-file` section: command syntax, behavior description, `### Options`, `### Exit behavior`.

## Required Changes

1. Add a `##`-level `lrh conversation export-antigravity-session` section to `docs/reference/cli/conversation.md`, placed in the same reading order as the CLI subparser registration order in `src/lrh/cli/main.py:115-161`.
2. Document all flags implemented in `src/lrh/conversations/antigravity_export.py`'s `run_convert_antigravity_session_cli`: `--transcript-path`, `--conversation-id`, `--latest` (mutually exclusive discovery group), `--app-data-dir` (default `~/.gemini/antigravity`), `--out`, `--archive-root`, `--force`, `--source-id`, `--no-scan-sensitive`.
3. Document the durable-archive-default behavior (when `--out` is omitted, the CLI resolves a durable session archive path) and metadata-only terminal output, matching the actual behavior in `antigravity_export.py:358-405`.

## Non-Goals

- Does not modify `src/lrh/conversations/antigravity_export.py` or any runtime behavior — documentation only.
- Does not address the Claude Code exporter's own doc entry — that is covered by `WI-CLAUDE-CONVERSATION-EXPORT-CLI`.

## Acceptance Criteria

- `docs/reference/cli/conversation.md` contains a `##`-level `lrh conversation export-antigravity-session` section.
- The section documents all flags and matches the depth of the existing Codex sections.
- `lrh validate` reports 0 errors.

## Validation

- `lrh validate`
- `grep -n "export-antigravity-session" docs/reference/cli/conversation.md`
