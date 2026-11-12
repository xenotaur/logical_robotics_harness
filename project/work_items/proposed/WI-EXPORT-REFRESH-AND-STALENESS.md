---
resolution: null
blocked_reason: null
blocked: false
id: WI-EXPORT-REFRESH-AND-STALENESS
title: "Add a non-destructive --refresh re-export mode and flag missing or stale cloud-session exports in closeout and work-remains"
type: deliverable
status: proposed
owner: anthony
contributors:
  - anthony
assigned_agents: []
related_focus:
  - FOCUS-EXECUTION-FRAMEWORK-PLANNING
related_roadmap:
  - ROADMAP-PHASE-04
related_workstreams: []
related_design:
  - project/design/proposals/proposed/lrh-cloud-session-capture/00_proposal.md
  - project/audits/2026-11-06-cloud-session-export-audit.md
  - project/design/proposals/adopted/lrh-claude-conversation-exporter/00_proposal.md
depends_on: []
blocked_by: []
expected_actions:
  - edit_file
  - run_tests
  - add_cli_command
forbidden_actions:
  - force_push
  - delete_branch
  - merge_pr
  - weaken_human_gate
  - print_transcript_text
  - skills_install_force
acceptance:
  - "export-claude-session records its render options (include_subagents and include_system_attachments) in the export manifest; existing manifest fields are unchanged, and inspect-export tolerates exports that predate the new fields"
  - "export-claude-session --refresh overwrites an existing destination only when that file is an LRH Claude export of the same source id, whose recorded render options equal the current invocation's, and whose recorded source byte count and hash show the recorded source is a byte prefix of the current transcript (the match_source_grew case); every other existing destination, including one with no recorded render options, is refused with a clear error that names any differing flags, and is left untouched"
  - "--refresh with no existing destination behaves like a normal export; when the existing export already matches the current transcript exactly (inspect-export's match case) with the same render options, --refresh is a no-op success that reports the export as current and leaves the file untouched; --refresh and --force are mutually exclusive"
  - "lrh-export-claude documents --refresh as not requiring the --force confirmation gate, because it can't overwrite a different export; --force still always waits for confirmation"
  - "/lrh-closeout Step 8 and /lrh-work-remains item 11 take cloud status only from the cloud_session field of lrh conversation current-claude-session-id --format json, treating a missing field as not a cloud session, and never read CLAUDE_CODE_REMOTE themselves"
  - "/lrh-closeout Step 8 and /lrh-work-remains item 11, when the session is a cloud session, find the existing export from the path lrh-export-claude reported earlier in this session (its delivered path or archive path), never by recomputing the archive path in skill text; they report 'no export found in this session' when there is no such report or the file is gone, and otherwise 'export is N bytes stale' using inspect-export's grown-by count; they offer a refresh plus delivery, and never run the export themselves without the export skill's own gate"
  - "The /lrh-closeout report states when lrh sessions closeout-sync wrote to an archive that won't survive the session"
  - "Unit tests cover the refresh accept and refuse cases; lrh validate, scripts/test, scripts/lint and scripts/format --check --diff pass; rendered skill copies are regenerated without --force"
required_evidence:
  - manual_review
  - lrh_validate
  - test_output
artifacts_expected:
  - src/lrh/conversations/claude_export.py
  - src/lrh/conversations/export_manifest.py
  - tests/conversations_tests/claude_export_test.py
  - tests/conversations_tests/export_manifest_test.py
  - src/lrh/skills/lrh-export-claude/SKILL.md
  - src/lrh/skills/lrh-closeout/SKILL.md
  - src/lrh/skills/lrh-work-remains/references/grounding-sources.md
  - docs/reference/cli/conversation.md
  - plugins/lrh/skills/
---

# WI-EXPORT-REFRESH-AND-STALENESS: Non-destructive re-export and stale-export flags

## Summary

Add `export-claude-session --refresh`. It replaces an earlier export of the
same session only when the transcript has merely grown since, so refreshing
a snapshot no longer needs `--force`. Also teach closeout and work-remains
to flag a missing or stale export in a cloud session before it ends.

## Problem / Context

An export of a live session is a snapshot. Re-exporting to the same default
destination needs `--force`, which can overwrite anything, so the skill
always asks first. A SessionEnd hook can't replace the re-export: its budget
is 1.5 seconds by default and 60 at most, teardown behavior is
undocumented, and its output would land in the discarded container (audit
§1.5). `inspect-export --source` already distinguishes `match_source_grew`
from `mismatch`, so the CLI can tell a safe refresh from a real overwrite.
That comparison covers the source only. An export's content also depends on
`--include-subagents` and `--include-system-attachments`, and the manifest
doesn't record either today (`claude_export.py:119-135`). Without them, a
refresh with default flags could silently replace an export that included
subagent transcripts with one that doesn't. So the manifest has to record
the render options, and `--refresh` has to require them to match.
`PROP-LRH-CLOUD-SESSION-CAPTURE` Decision 6.

### Duplication search
- In-repo: Related: `inspect-export`'s source-grew logic (`src/lrh/conversations/export_inspector.py`). Reuse it; don't duplicate it.
- Sibling repos: None identified
- External libraries: None identified
- Recommendation: Proceed

### Demand search
- Work items: Adjacent: WI-CLOSEOUT-EXPORT-SCOPE — "Decouple /lrh-closeout Step 8 /export offer wording from Pending offers completion". It edits the same Step 8 offer; coordinate wording.
- Proposals: Found: PROP-LRH-CLOUD-SESSION-CAPTURE (Decision 6)
- Backlog: No matching entries
- Recommendation: No action

## Scope

- The `--refresh` mode in the Claude exporter.
- Cloud-aware stale-export flags in `/lrh-closeout` and `/lrh-work-remains`.

## Required Changes

1. Record `include_subagents` and `include_system_attachments` in the
   export manifest (`export_manifest.ConversationExportManifest` and its
   frontmatter), set from the invocation. Keep `inspect-export` working on
   exports that lack them.
2. Add `--refresh` to `export-claude-session` in
   `src/lrh/conversations/claude_export.py`. Before writing, read the
   existing destination's frontmatter and check, in order:
   - the source ID matches;
   - the recorded render options are present and equal the current
     invocation's;
   - the recorded source bytes are a prefix of the current source, using
     the inspector's own comparison.

   If the source has grown (`match_source_grew`), overwrite. If it is
   unchanged (`match`), leave the file untouched and report that the export
   is already current. Otherwise refuse, naming any flag that differs so
   the user can re-run with matching flags. Make `--refresh` and `--force`
   mutually exclusive.
3. Add tests for the accept-grown, unchanged-no-op,
   refuse-different-source, refuse-mismatch,
   refuse-different-render-options, refuse-no-recorded-render-options,
   refuse-non-LRH-file, and no-existing-file cases.
4. Update `lrh-export-claude`:
   - Step 3: `--refresh` is not on the dangerous-flag list.
   - Step 3's "destination already exists" note: suggest `--refresh` first,
     with the same render flags as the earlier export.
5. Update `/lrh-closeout` Step 8 and `/lrh-work-remains` item 11 with the
   cloud-session stale-export check. Cloud status comes only from the
   `cloud_session` field of `current-claude-session-id --format json`
   (Decision 4). Until `WI-EXPORT-CLAUDE-CLOUD-BRANCH` adds that field, a
   missing field means "not a cloud session", so the check stays dormant
   rather than reading `CLAUDE_CODE_REMOTE` in skill text.

   The check finds the export from the path `lrh-export-claude` reported in
   its Step 6 earlier in this session. With a delivery tool that is
   `<delivery-dir>/<source-id>.md`; without one it is the archive path the
   CLI printed. The skill text must not recompute the archive path, which
   lives only in `claude_export.py:505-515` (the export skill already
   refuses to copy it). With no such report, or if the file is gone,
   report "no export found in this session". That is safe to offer on,
   because `--refresh` refuses a mismatched file and an unchanged one is a
   no-op.
6. Document `--refresh` and the new manifest fields in
   `docs/reference/cli/conversation.md`, and regenerate rendered copies.

## Non-Goals

- Do not add a SessionEnd or Stop hook.
- Do not add `--refresh` to the Codex or Antigravity exporters.
- Do not make closeout or work-remains run an export themselves. They only
  flag and offer.

## Acceptance Criteria

- The manifest records the render options.
- `--refresh` overwrites only the grown-same-source case with matching
  render options, treats an unchanged export as a no-op, and refuses the
  rest, as shown by tests.
- The stale-export check takes the export's path from the export skill's
  own report, never from recomputing it.
- `--force` keeps its confirmation gate; `--refresh` doesn't need one.
- Closeout and work-remains flag missing or stale exports in cloud sessions.
- `lrh validate`, `scripts/test`, `scripts/lint` and
  `scripts/format --check --diff` pass.

## Validation

- `scripts/version tools`
- `lrh validate`
- `scripts/format --check --diff`
- `scripts/lint`
- `scripts/test`
- `lrh skills check --target claude --local`

## Risk Notes

- The prefix check needs the source byte count recorded at export time, and
  the options check needs the recorded render options. Exports without
  either must be refused rather than guessed, so exports made before this
  item ships can't be refreshed; re-exporting them still goes through
  `--force` and its gate.
- Closeout and work-remains must not read transcript content. The grown-by
  count from `inspect-export` is metadata only.
- The export skill's earlier report can drop out of context after
  compaction, so the check then says "no export found in this session"
  even though one exists. That errs toward offering a refresh, which is
  safe. If it proves noisy, a later read-only CLI lookup built on
  `WI-CLAUDE-EXPORT-LOCAL-IMPORT`'s shared path helper could replace it.
