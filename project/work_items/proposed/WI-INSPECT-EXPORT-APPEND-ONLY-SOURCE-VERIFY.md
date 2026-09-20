---
resolution: null
blocked_reason: null
blocked: false
id: WI-INSPECT-EXPORT-APPEND-ONLY-SOURCE-VERIFY
title: Verify append-only export sources by recorded prefix in inspect-export (Claude and Antigravity)
type: deliverable
status: proposed
owner: null
contributors: []
assigned_agents: []
related_focus: []
related_roadmap: []
related_workstreams: []
related_design:
  - project/design/proposals/adopted/lrh-claude-conversation-exporter/00_proposal.md
depends_on: []
blocked_by: []
expected_actions:
  - edit_file
  - write_docs
forbidden_actions:
  - force_push
  - delete_branch
  - change_codex_export_behavior
acceptance:
  - "ConversationExportManifest supports an optional source_byte_count, emitted only when set, and parsed when present or absent"
  - "The Claude and Antigravity exporters each record source_byte_count equal to the number of source bytes they hashed"
  - "inspect-export reports a distinct match_source_grew status when the source is longer than recorded and its recorded prefix hashes to source_sha256; the result is valid with exit code 0"
  - "inspect-export still reports mismatch when an earlier byte changed, when the source is shorter than recorded, or when a whole-file hash differs and no byte count was recorded"
  - "Manifests without source_byte_count (older exports and Codex) verify exactly as before"
  - "docs/reference/cli/conversation.md documents the new status and the append-only assumption"
  - "lrh validate reports 0 errors and introduces no new warnings"
required_evidence:
  - manual_review
  - lrh_validate
  - test_output
artifacts_expected:
  - src/lrh/conversations/export_manifest.py
  - src/lrh/conversations/export_inspector.py
  - src/lrh/conversations/claude_export.py
  - src/lrh/conversations/antigravity_export.py
  - tests/conversations_tests/export_inspector_test.py
  - tests/conversations_tests/claude_export_test.py
  - tests/conversations_tests/antigravity_export_test.py
  - docs/reference/cli/conversation.md
---

# WI-INSPECT-EXPORT-APPEND-ONLY-SOURCE-VERIFY: Verify append-only export sources by recorded prefix in inspect-export (Claude and Antigravity)

## Summary

Make `lrh conversation inspect-export --source` correct for exports whose source is an
append-only log that keeps growing after the export, by recording how many source bytes
were hashed and verifying that recorded prefix instead of the whole file. A source that
has only grown is reported as `match_source_grew`, not `mismatch`.

## Problem / Context

`export-claude-session` reads a live, still-growing transcript once, hashes exactly the
bytes it read (`claude_export.py`: `raw_bytes = path.read_bytes()`, then
`source_sha256 = hashlib.sha256(raw_bytes)`), and records that digest. That is correct at
export time. But `inspect-export` later re-hashes the *whole current file*
(`export_inspector.py`, `_verify_source_hash`: `hashlib.sha256(source.read_bytes())`), and a
session that is still being written has grown by then, so a healthy export reports
`Source hash: mismatch` (which is in the inspector's error set, making the artifact
`Valid: no`).

Observed during the first real run of `/lrh-export-claude` against the session that was
implementing it: the transcript grew by about 36 KB between a snapshot and the verification
step, and a later check showed the live file had grown by 146,624 bytes while the first
16,603,892 bytes still hashed exactly to the recorded digest, i.e. the growth was a pure
append. The skill's own documented default, `--latest`, exports the current session, so
this is the normal case, not an edge case.

Antigravity has the same defect, confirmed by a read-only test on a live conversation
(no conversation content read; sizes and hashes only). Baseline: `transcript.jsonl`
44,262 bytes and `transcript_full.jsonl` 52,222 bytes, each with one chunk file. After
two more messages in the conversation, both logs had grown by roughly 1-2 KB, and the
first 44,262 and 52,222 bytes still hashed exactly to the baseline digests, so growth was
a pure append and the whole-file hash changed. `antigravity_export.py` reads the bytes
once (`path.read_bytes()`), hashes them, and builds the manifest, exactly as the Claude
exporter does, so its exports of a live conversation would report `mismatch` the same way.
Not tested: chunk rollover for a long conversation (only a single chunk existed).

Why the Codex exporter differs: Codex writes a frozen raw JSON capture at export time,
hashes that capture, and points the inspector at it, so its source cannot drift. The
Claude and Antigravity exporters have the live log as the source, but do not retain the
bytes they hashed. The adopted proposal's Decision 1 chose direct file parsing precisely
because it yields a verifiable hash, and it anticipated a live read only as a
partially-written *trailing line*, not growth between export and verification.

The manifest has no field to support a prefix check: `transcript_statistics.byte_count`
measures the rendered artifact, not the source.

Assumption to keep honest: append-only was observed on one session over one interval. It
is not verified across transcript compaction or session resume. The safe failure mode is
preserved: if earlier bytes ever change, the prefix hash differs and the result stays
`mismatch`.

### Duplication search
- In-repo: no existing prefix or growth-aware verification. `WI-CODEX-CONVERSATION-INSPECT-EXPORT` (resolved) is the inspector's origin and does not overlap.
- Sibling repos: none identified.
- External libraries: not applicable.
- Recommendation: Proceed.

### Demand search
- Work items: none open. `project/work_items/proposed/` has no item about source growth or hash verification.
- Proposals: `PROP-LRH-CLAUDE-CONVERSATION-EXPORTER` Decision 1 covers only partial trailing lines.
- Backlog: no entry on live-session or grown-source verification.
- Recommendation: No action; this item is the tracking artifact.

## Scope

- Add an optional, additive `source_byte_count` to the export manifest (schema version stays 1; emitted only when set, as `source_id` already is).
- Record it in the Claude and Antigravity exporters.
- Teach the inspector prefix verification and the new `match_source_grew` status.
- Document it and test it.

## Required Changes

1. In `src/lrh/conversations/export_manifest.py`, add an optional non-negative-int `source_byte_count` to `ConversationExportManifest`: the number of source bytes hashed to produce `source_sha256`. Emit it in `to_mapping()` only when it is not `None`, and accept it in `from_mapping()` when present or absent. Keep `schema_version: 1`; confirm existing readers tolerate the field being absent and present.
2. In `src/lrh/conversations/claude_export.py`, pass `source_byte_count=len(raw_bytes)` when building the manifest, from the same `raw_bytes` that `source_sha256` is computed from, so the pair is always consistent.
3. In `src/lrh/conversations/antigravity_export.py`, do the same: pass `source_byte_count=len(raw_bytes)` from the same `raw_bytes` that `source_sha256` is computed from (around lines 57-61 and the manifest at line 122). The CLI path that hashes `transcript_file.read_bytes()` separately (around line 416) must not compute the count from a second read; use the exporter's own bytes so the pair stays consistent.
4. In `src/lrh/conversations/export_inspector.py`, extend `_verify_source_hash`: when the manifest records `source_byte_count` N and the source is longer than N, hash the first N bytes; equal means the new status `match_source_grew`, unequal means `mismatch`. If the source length equals N, compare the whole file as today. If it is shorter than N, report `mismatch`. If the manifest has no `source_byte_count`, behave exactly as today.
5. Extend `SourceHashVerification` and its `to_mapping()` (JSON output) with the expected and actual source byte counts. In text output, `Source hash:` shows `match_source_grew` followed by a line stating how many bytes the source has grown since export. Do **not** add `match_source_grew` to the error set, so the inspection stays `Valid: yes` with exit code 0.
6. Update `docs/reference/cli/conversation.md` (`## lrh conversation inspect-export`) to describe the new status, the recorded byte count, and the append-only assumption, including that `mismatch` is still reported if earlier bytes changed.
7. Add `unittest.TestCase` tests in `tests/conversations_tests/export_inspector_test.py`, `claude_export_test.py` and `antigravity_export_test.py`: unchanged source is `match`; appended source is `match_source_grew` and valid; an altered earlier byte with a longer source is `mismatch`; a shorter source is `mismatch`; a manifest without the field verifies as before; manifest round trip with and without the field; each of the Claude and Antigravity exporters records a byte count equal to the source length.
8. Check what the Antigravity exporter does when a conversation has several chunk files, and record the finding in the execution record. Fixing chunk rollover is out of scope here.

## Non-Goals

- Does not change the Codex exporter or its raw-capture model.
- Does not change how the Antigravity exporter discovers or reads its source, only that it records `source_byte_count`.
- Does not archive a raw copy of the source. That would multiply storage and the sensitive-data footprint for no additional guarantee over prefix verification.
- Does not change what `source_sha256` means for existing exports.
- Does not amend the adopted proposal; the gap is recorded here.

## Acceptance Criteria

- `ConversationExportManifest` supports an optional `source_byte_count`, emitted only when set, and parsed when present or absent.
- The Claude and Antigravity exporters record `source_byte_count` equal to the number of source bytes they hashed.
- `inspect-export` reports `match_source_grew` (valid, exit 0) when the source is longer than recorded and its recorded prefix hashes to `source_sha256`.
- `inspect-export` still reports `mismatch` when an earlier byte changed, when the source is shorter than recorded, or when no byte count was recorded and the whole-file hash differs.
- Manifests without `source_byte_count` (older exports, Codex) verify exactly as before.
- The CLI reference documents the new status and the append-only assumption.
- `lrh validate` reports 0 errors and introduces no new warnings.

## Validation

- `PYTHONPATH=src scripts/test tests/conversations_tests/export_inspector_test.py`
- `PYTHONPATH=src scripts/test tests/conversations_tests/claude_export_test.py`
- `PYTHONPATH=src scripts/test tests/conversations_tests/antigravity_export_test.py`
- `PYTHONPATH=src scripts/test`
- `scripts/lint`
- `scripts/format --check --diff`
- `lrh validate`
