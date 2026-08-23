---
resolution: "Implemented and merged in PR #579 (commit e094d443d813eabc81e96f95301fdc15ac5787ce)."
blocked_reason: null
blocked: false
id: WI-CODEX-EXPORT-DURABLE-ARCHIVE-DEFAULT
title: Make Codex exports durable-archive-first by default
type: deliverable
status: resolved
owner: anthony
contributors:
  - anthony
assigned_agents: []
related_focus:
  - FOCUS-EXECUTION-FRAMEWORK-PLANNING
related_roadmap:
  - ROADMAP-PHASE-03
related_workstreams:
  - WS-SESSION-ARCHIVE-SYNC
related_design:
  - project/design/proposals/proposed/lrh-session-archive-sync/00_proposal.md
  - project/design/proposals/proposed/lrh-conversations-storage-interop/00_proposal.md
  - project/design/proposals/adopted/lrh-codex-app-server-conversation-export/00_proposal.md
  - project/design/proposals/adopted/lrh-codex-conversation-exporter/00_proposal.md
  - docs/conversations/codex_export.md
depends_on:
  - WI-CODEX-CONVERSATION-EXPORT-SKILL
  - WI-SESSION-ARCHIVE-SYNC-RECONCILER
blocked_by: []
expected_actions:
  - edit_file
  - add_cli_command
  - write_docs
  - run_tests
forbidden_actions:
  - force_push
  - delete_branch
  - merge_pr
  - commit_raw_transcript_data
  - scrape_codex_storage_internals
  - implement_scheduled_or_hook_sync
  - implement_encrypted_off_machine_archive
acceptance:
  - '`/lrh-codex-export` defaults to a durable private archive root outside the Git worktree rather than `${TMPDIR:-/tmp}`'
  - scratch or dogfood exports require an explicit scratch-mode choice and are reported as ephemeral
  - each export attempt writes durable attempt metadata before running the app-server export and records success or failure outcome
  - existing Promptspace/CodexExports-style LRH Codex export directories can be imported or migrated into the durable private archive without printing transcript bodies
  - empty or partial export directories cannot be mistaken for successful exports
  - docs explain the durable archive default, scratch mode, import/migration workflow, and privacy boundaries
  - '`lrh validate` passes with 0 errors'
required_evidence:
  - manual_review
  - lrh_validate
  - test_output
artifacts_expected:
  - src/lrh/skills/lrh-codex-export/SKILL.md
  - .agents/skills/lrh-codex-export/SKILL.md
  - .claude/skills/lrh-codex-export/SKILL.md
  - .gemini/plugins/lrh/skills/lrh-codex-export/SKILL.md
  - .gemini/plugins/lrh/plugin.json
  - src/lrh/cli/main.py
  - src/lrh/conversations/
  - tests/cli_tests/
  - tests/conversations_tests/
  - docs/conversations/codex_export.md
  - docs/reference/cli/conversation.md
  - project/workstreams/active/WS-SESSION-ARCHIVE-SYNC.md
---

## Summary

Make Codex conversation export durable-archive-first by default, so
`/lrh-codex-export` preserves private transcripts in a configured archive root
rather than leaving successful captures in macOS temporary storage.

## Problem / Context

Dogfooding found that the current `/lrh-codex-export` skill uses
`${TMPDIR:-/tmp}` for routine ad hoc captures, which on macOS may resolve under
`/var/folders/`. That made exported sessions hard to discover and vulnerable to
cleanup, defeating the point of a Claude `/export` equivalent after a user
archives or deletes the live Codex task. A manual rescue of `/var/folders/`
exports into a private Promptspace-style archive directory found five valid
exports and six empty directories; the empty directories may be harmless aborted
attempts, but they carry no durable provenance and can look like successful
export artifacts.

`WS-SESSION-ARCHIVE-SYNC` already establishes the governing invariant that no
repo-changing agent session should be lost, and its exit criteria require
resolving the archive-root-location question. The resolved Codex exporter
workstream proved the app-server export path and the thin `/lrh-codex-export`
wrapper, but it explicitly left private archive-root defaults for later
design/implementation.

### Duplication search

- In-repo: Related implementation exists, but no duplicate work item.
  `WI-CODEX-CONVERSATION-EXPORT-SKILL` implemented the thin wrapper,
  `WI-SESSION-ARCHIVE-SYNC-RECONCILER` implemented the Claude/session archive
  reconciler, and `src/lrh/skills/lrh-codex-export/SKILL.md` still defaults
  routine captures to temp storage.
- Sibling repos: No sibling implementation identified for LRH-managed Codex
  durable export defaults; the user mentioned LCATS only as precedent for
  experimental directories, not as a duplicate implementation.
- External libraries: No external library identified that can replace this; the
  work is LRH-specific policy, CLI, skill, manifest, and archive-layout
  integration.
- Recommendation: Proceed by extending the existing Codex export and session
  archive surfaces, not by creating a parallel exporter.

### Demand search

- Work items: No existing proposed work item found for Codex durable archive
  defaults. Related resolved items are `WI-CODEX-CONVERSATION-EXPORT-SKILL` and
  `WI-SESSION-ARCHIVE-SYNC-RECONCILER`.
- Proposals: Found governing demand in `PROP-LRH-SESSION-ARCHIVE-SYNC` and
  `PROP-LRH-CODEX-APP-SERVER-CONVERSATION-EXPORT`; the latter leaves the
  private archive-root convention open.
- Backlog: Found related backlog demand for archive-root-location-dependent
  helper scripting, but not the full durable-default Codex export behavior.
- Recommendation: Link this item to `WS-SESSION-ARCHIVE-SYNC` and the Codex
  app-server export proposal; do not close the narrower backlog note
  automatically.

## Scope

- Change `/lrh-codex-export` from temp-first to durable-private-archive-first.
- Add or extend LRH CLI support for resolving the Codex export archive root and
  importing existing LRH Codex export directories into it.
- Preserve scratch/dogfood mode as an explicit, clearly labeled ephemeral path.
- Record per-attempt metadata so empty or failed export directories are
  diagnosable.
- Keep raw transcript artifacts private, outside the Git worktree, and out of
  committed project-control records.
- Update docs and tests so users can understand the new durable path and safely
  migrate rescued exports.

## Required Changes

1. Define the durable Codex export archive-root convention, reusing the
   `PROP-LRH-SESSION-ARCHIVE-SYNC` private local archive policy where possible
   and resolving whether the default is under an LRH user-local root, a
   configured Promptspace-style root, or an explicit config value.
2. Update `src/lrh/skills/lrh-codex-export/SKILL.md` so the normal path writes
   to the durable private archive root instead of `${TMPDIR:-/tmp}`.
3. Keep scratch/dogfood output available only through an explicit scratch-mode
   instruction or CLI flag, and make the final report clearly say the files are
   ephemeral.
4. Add durable attempt metadata, such as `attempt.json`, written before export
   begins and updated after completion or failure with timestamp, source tool,
   adapter, thread id if known, output paths, command outcome, validation
   status, and error summary when applicable.
5. Add or extend a CLI command to import/migrate existing LRH Codex export
   directories such as
   `$HOME/<private-archive>/CodexExports/lrh-codex-export-*` into the durable
   archive. The command must inspect manifests and hashes without printing
   transcript bodies.
6. Treat empty, partial, or invalid export directories as explicit
   failed/partial attempts, not successful exports; preserve whatever metadata
   exists and report missing `export.md` / `raw.json` clearly.
7. Update `docs/conversations/codex_export.md`,
   `docs/reference/cli/conversation.md`, and any relevant archive/sessions docs
   with the durable default, scratch mode, migration workflow, and privacy
   warnings.
8. Add focused tests for archive-root resolution, scratch-mode behavior,
   attempt metadata creation/update, migration of valid exports, handling of
   empty/partial directories, and transcript-body non-disclosure.
9. Keep skill mirrors synchronized for every touched skill target present in the
   repository.

## Non-Goals

- Do not commit raw transcript exports, raw JSON, or private archive paths to the
  LRH repository.
- Do not scrape undocumented Codex app storage internals.
- Do not implement weekly scheduled sync, closeout-triggered sync, or
  SessionEnd hooks; those remain `WS-SESSION-ARCHIVE-SYNC` Stage 4 scope.
- Do not implement encrypted off-machine backup.
- Do not make raw transcripts authoritative LRH project-control state.
- Do not solve the broader target-aware `/lrh-export` command for every agent
  unless it falls out as a thin alias over the Codex-specific durable behavior.
- Do not print transcript bodies during migration, validation, or status
  reporting.

## Acceptance Criteria

- `/lrh-codex-export` defaults to a durable private archive root outside the Git
  worktree rather than `${TMPDIR:-/tmp}`.
- Scratch or dogfood exports require an explicit scratch-mode choice and are
  reported as ephemeral.
- Each export attempt writes durable attempt metadata before running the
  app-server export and records success or failure outcome.
- Existing Promptspace/CodexExports-style LRH Codex export directories can be
  imported or migrated into the durable private archive without printing
  transcript bodies.
- Empty or partial export directories cannot be mistaken for successful exports.
- Docs explain the durable archive default, scratch mode, import/migration
  workflow, and privacy boundaries.
- `lrh validate` passes with 0 errors.

## Validation

- `scripts/version tools`
- `scripts/format --check --diff`
- `scripts/lint`
- `scripts/test`
- `lrh validate`
- `lrh skills check --target claude --local`
- `lrh skills check --target codex --local`
- `lrh skills check --target antigravity --local`
- `lrh conversation inspect-export <migrated-export.md> --source <migrated-raw.json> --format json`
- `lrh conversation <migration-command> --help`

## Risk Notes

- Choosing a durable default too quickly could bake in the wrong archive-root
  shape; the implementation should prefer explicit config and document the
  resolution of the archive-root-location question.
- Importing rescued exports must avoid printing transcript text; tests should
  cover metadata-only output paths.
- Empty directories may represent aborted attempts rather than lost data;
  migration should classify them conservatively as empty/partial attempts
  instead of inventing provenance.
- A durable local archive still depends on the user's local backup regime;
  encrypted off-machine backup remains deferred but should not be designed out.
