---
resolution: null
blocked_reason: null
blocked: false
id: WI-CONVERSATION-EXPORT-SOURCE-PREFIX-VERIFICATION
title: Verify a live transcript export by hashing the recorded source prefix
type: deliverable
status: proposed
owner: anthony
contributors:
  - anthony
assigned_agents: []
related_focus: []
related_roadmap: []
related_workstreams: []
related_design: []
depends_on:
  - WI-EXPORT-SKILLS-LIVE-SESSION-WORDING
blocked_by: []
expected_actions:
  - edit_file
  - create_file
forbidden_actions:
  - force_push
  - delete_branch
  - merge_pr
  - weaken_human_gate
  - print_transcript_text
acceptance:
  - The Claude and Antigravity exporters record in the export manifest how many source bytes they read and hashed (a new source_bytes_read field, or an equivalent name settled at implementation)
  - inspect-export with --source hashes only the recorded number of bytes and reports match when the source is exactly that length and the hash equals the recorded one
  - When the source has grown but its first source_bytes_read bytes still hash to the recorded value, inspect-export reports a new match_prefix status, states how many bytes the source has grown, and exits 0 by default
  - A new --strict-source flag makes inspect-export require an exact full match; a grown source then fails with the existing mismatch semantics
  - When the source is shorter than the recorded length, or the prefix hash differs, inspect-export reports mismatch and exits nonzero
  - Manifests written before this change (no source_bytes_read) are still accepted and verified exactly as before
  - The Codex exporter and its raw-capture verification are unchanged
  - Unit tests use unittest.TestCase, are hermetic, and cover exact match, grown-source prefix match, strict mode failure, shortened source, prefix hash mismatch, legacy manifest, and JSON output for the new status
  - docs/reference/cli/conversation.md documents the new manifest field, the match_prefix status, the default exit behavior and --strict-source
  - lrh-export-claude and lrh-antigravity-export wording is updated to describe match_prefix, replacing the workaround-only text from the live-session wording work item where it is now redundant
  - .claude/skills is byte-identical to src/lrh/skills; .agents/skills and .gemini/plugins/lrh/skills are regenerated via lrh skills install
  - No transcript text is printed or committed; tests use synthetic fixtures only
  - scripts/test, scripts/lint, scripts/format --check --diff and lrh validate are all clean
required_evidence:
  - manual_review
  - lrh_validate
  - test_output
artifacts_expected:
  - src/lrh/conversations/claude_export.py
  - src/lrh/conversations/antigravity_export.py
  - src/lrh/conversations/export_manifest.py
  - src/lrh/conversations/export_inspector.py
  - tests/ (export and inspector tests)
  - docs/reference/cli/conversation.md
  - src/lrh/skills/lrh-export-claude/SKILL.md
  - src/lrh/skills/lrh-antigravity-export/SKILL.md
  - .claude/skills/ (mirrors)
  - .agents/skills/ and .gemini/plugins/lrh/skills/ (regenerated)
---

## Summary

Make export verification robust for live transcripts by recording how many
source bytes each export hashed, so the inspector can verify that prefix even
after the source has grown, instead of relying on a documented workaround.

## Problem / Context

Both exporters read the transcript once and hash those bytes
(`src/lrh/conversations/claude_export.py:58-62`,
`src/lrh/conversations/antigravity_export.py:57-61`). The manifest records
`source_sha256` (`src/lrh/conversations/export_manifest.py:96`), and
`inspect-export --source` recomputes the hash of the whole file later
(`src/lrh/conversations/export_inspector.py:365`). For a live session the file
keeps growing, so a later inspection reports `Source hash: mismatch` even
though the export was valid as of the moment it ran. The wording work item
(`WI-EXPORT-SKILLS-LIVE-SESSION-WORDING`) documents a single-call workaround;
this work item removes the cause.

Design assumption: live transcripts are append-only JSONL. If a transcript were
rewritten rather than appended, its prefix would no longer match and the
inspector would correctly report `mismatch`.

Decision recorded from the design discussion: `match_prefix` is a successful
verification by default (exit 0, with the growth stated); exact-only behavior
is available with `--strict-source`.

Prior art check:

- **Duplication:** none. `export_inspector.py` already reports `not_supplied`,
  `source_missing`, `source_not_file`, `source_unreadable`, `not_available`,
  `match` and `mismatch`; none covers a grown source.
- **Demand:** none existing; it arises from the live-session hash mismatch.

## Scope

- Manifest field, two exporters, inspector status and flag, tests, reference
  docs and the small skill wording follow-up.

## Required Changes

- Add the field and record it in both exporters, keeping the existing
  `source_sha256` semantics unchanged for exact matches.
- Extend the inspector as specified, with a backward-compatible legacy path.
- Add tests and update `docs/reference/cli/conversation.md`.
- Update the two skills' wording, then sync and regenerate mirrors.

## Non-Goals

- No change to the Codex exporter or its raw-capture verification.
- No change to the privacy, sensitivity or destination behavior.
- No printing of transcript text.

## Acceptance Criteria

- The behavior matrix above, with backward compatibility.
- Tests, docs, skill wording and mirrors done; validation commands clean.

## Validation

- scripts/test
- scripts/lint
- scripts/format --check --diff
- lrh validate

## Risk Notes

- The manifest schema gains a field; the reader must tolerate its absence.
- Accepting `match_prefix` by default relaxes verification for grown sources; the
  status and the growth must be stated in the output so it is never silent, and
  `--strict-source` remains available.
- An append-only assumption underlies the prefix check; document it.
