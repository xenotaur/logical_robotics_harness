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
  - "export-claude-session --refresh overwrites an existing destination only when that file is an LRH Claude export of the same source id whose recorded source byte count and hash show the recorded source is a byte prefix of the current transcript (the match_source_grew case); every other existing destination is refused with a clear error and left untouched"
  - "--refresh with no existing destination behaves like a normal export; --refresh and --force are mutually exclusive"
  - "lrh-export-claude documents --refresh as not requiring the --force confirmation gate, because it can't overwrite a different export; --force still always waits for confirmation"
  - "/lrh-closeout Step 8 and /lrh-work-remains item 11, when the session is a cloud session, report 'no export' or 'export is N bytes stale' using inspect-export's grown-by count, and offer a refresh plus delivery; they never run the export themselves without the export skill's own gate"
  - "The /lrh-closeout report states when lrh sessions closeout-sync wrote to an archive that won't survive the session"
  - "Unit tests cover the refresh accept and refuse cases; lrh validate, scripts/test, scripts/lint and scripts/format --check --diff pass; rendered skill copies are regenerated without --force"
required_evidence:
  - manual_review
  - lrh_validate
  - test_output
artifacts_expected:
  - src/lrh/conversations/claude_export.py
  - tests/conversations_tests/claude_export_test.py
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

1. Add `--refresh` to `export-claude-session` in
   `src/lrh/conversations/claude_export.py`. Before writing, read the
   existing destination's frontmatter, check that the source ID matches, and
   verify that the recorded source bytes are a prefix of the current source
   using the inspector's own comparison. Otherwise refuse. Make
   `--refresh` and `--force` mutually exclusive.
2. Add tests for the accept, refuse-different-source, refuse-mismatch,
   refuse-non-LRH-file, and no-existing-file cases.
3. Update `lrh-export-claude`:
   - Step 3: `--refresh` is not on the dangerous-flag list.
   - Step 3's "destination already exists" note: suggest `--refresh` first.
4. Update `/lrh-closeout` Step 8 and `/lrh-work-remains` item 11 with the
   cloud-session stale-export check. Cloud status comes from
   `current-claude-session-id`'s `cloud_session` field once
   `WI-EXPORT-CLAUDE-CLOUD-BRANCH` ships, and from `CLAUDE_CODE_REMOTE`
   until then.
5. Document `--refresh` in `docs/reference/cli/conversation.md`, and
   regenerate rendered copies.

## Non-Goals

- Do not add a SessionEnd or Stop hook.
- Do not add `--refresh` to the Codex or Antigravity exporters.
- Do not make closeout or work-remains run an export themselves. They only
  flag and offer.

## Acceptance Criteria

- `--refresh` accepts only the grown-same-source case, as shown by tests.
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

- The prefix check needs the source byte count recorded at export time.
  Exports without it must be refused rather than guessed.
- Closeout and work-remains must not read transcript content. The grown-by
  count from `inspect-export` is metadata only.
