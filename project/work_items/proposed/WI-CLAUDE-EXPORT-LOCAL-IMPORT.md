---
resolution: null
blocked_reason: null
blocked: false
id: WI-CLAUDE-EXPORT-LOCAL-IMPORT
title: "Add lrh conversation import-claude-export to file a downloaded Claude export into the local private archive"
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
  - add_cli_command
  - edit_file
  - run_tests
  - write_docs
forbidden_actions:
  - force_push
  - delete_branch
  - merge_pr
  - print_transcript_text
  - commit_transcript_export
  - skills_install_force
  - delete_source_without_flag
acceptance:
  - "lrh conversation import-claude-export <file> reads exported_at and source_id from the file's frontmatter and files it at the same path export-claude-session would have written for that export, using one path helper factored out of claude_export.py and shared by both commands; a test asserts both produce the same path for the same inputs"
  - "The archive root resolves through resolve_claude_archive_root, so --archive-root and LRH_SESSION_ARCHIVE_ROOT apply and a root inside the current Git worktree is rejected"
  - "Missing destination folders are created 0700 and the file is written 0600 from its first byte, never via copy2 then chmod, under a permissive umask; existing folders' modes are left unchanged; tests cover this"
  - "The command refuses a file that isn't an LRH Claude export (missing or invalid manifest) and refuses to overwrite a different existing export; an identical existing file is a no-op success, and a grown same-source export is accepted under the same rule as export-claude-session --refresh"
  - "The source file is left in place by default, and deleted only with an explicit --move after the destination is written and checked; --dry-run reports the destination without writing"
  - "Output is metadata-only (destination, source id, manifest check result) and never prints transcript text"
  - "lrh-export-claude/SKILL.md stops citing claude_export.py line numbers for the path rule and names the helper instead; docs/reference/cli/conversation.md documents the command; lrh validate, scripts/test, scripts/lint and scripts/format --check --diff pass; rendered copies are regenerated without --force"
required_evidence:
  - manual_review
  - lrh_validate
  - test_output
artifacts_expected:
  - src/lrh/conversations/claude_export.py
  - src/lrh/cli/main.py
  - tests/conversations_tests/claude_export_test.py
  - src/lrh/skills/lrh-export-claude/SKILL.md
  - docs/reference/cli/conversation.md
  - plugins/lrh/skills/lrh-export-claude/SKILL.md
---

# WI-CLAUDE-EXPORT-LOCAL-IMPORT: Local import command for downloaded Claude exports

## Summary

Add `lrh conversation import-claude-export <file>`. It files an export that
was downloaded from a cloud session into the local private archive, at the
same path the exporter would have used, with private permissions and a
manifest check. This replaces the manual `mkdir`/`mv`/`chmod` sequence.

## Problem / Context

In two cloud sessions, getting an export home ended with the user filing it
by hand:

```
mkdir -p ~/.local/share/lrh/session-archive/claude/exports/2026/11
mv ~/Downloads/<id>.md …/2026/11/
chmod 600 …/<id>.md
```

That sequence has several problems:

- The folders come out 0755.
- The file stays readable by others until the `chmod`.
- `LRH_SESSION_ARCHIVE_ROOT` is ignored.
- Nothing checks the file.
- The user has to reproduce the exporter's path rule — the export's UTC year
  and month plus the sanitized source ID — which lives inline at
  `src/lrh/conversations/claude_export.py:505-515`. The skill already
  refuses to copy that rule because of drift, and its own citation for it
  (`lrh-export-claude/SKILL.md:296`, which says `488-498`) has already gone
  stale.

The export's frontmatter carries `exported_at` and `source_id`
(`claude_export.py:122,132`), so the destination can be recomputed from the
file alone. `PROP-LRH-CLOUD-SESSION-CAPTURE` Decision 7. The audit's §1.4
has the evidence.

### Duplication search
- In-repo: Related: `lrh conversation import-codex-exports` (`src/lrh/conversations/codex_archive.py:224`), the precedent to follow. Don't copy its `copy2`-then-`chmod` approach (`codex_archive.py:479-480`).
- Sibling repos: None identified
- External libraries: None identified
- Recommendation: Proceed

### Demand search
- Work items: None found. Adjacent: WI-EXPORT-REFRESH-AND-STALENESS shares the grown-same-source rule; WI-EXPORT-CLAUDE-CLOUD-BRANCH reports this command.
- Proposals: Found: PROP-LRH-CLOUD-SESSION-CAPTURE (Decision 7)
- Backlog: No matching entries
- Recommendation: No action

## Scope

- A path helper shared by the exporter and the import command.
- The `import-claude-export` CLI command, with its tests and docs.
- Replace the skill's stale line citation with the helper's name.

## Required Changes

1. In `src/lrh/conversations/claude_export.py`, factor the default-path
   computation (lines 505-515) into a helper that takes the archive root,
   the export time, and the source ID. Use it from
   `run_convert_claude_session_cli`, with no change in behavior.
2. Add the `import-claude-export` subcommand, registered next to
   `import-codex-exports`, with `--archive-root`, `--dry-run` and `--move`.
   It:
   - parses the manifest;
   - computes the destination with the helper;
   - creates folders 0700;
   - writes the file 0600 through the existing private-write pattern;
   - checks the written copy;
   - deletes the source only with `--move`.
3. Overwrite rules:
   - Identical existing file: no-op success.
   - Grown same-source export: accept, using the same rule as `--refresh`.
     If `WI-EXPORT-REFRESH-AND-STALENESS` hasn't landed yet, implement the
     comparison once here and have that item reuse it.
   - Anything else: refuse.
4. Add tests in `tests/conversations_tests/claude_export_test.py`.
5. Document the command in `docs/reference/cli/conversation.md`. Update
   `lrh-export-claude/SKILL.md` to name the helper instead of line numbers.
   Regenerate rendered copies.

## Non-Goals

- Do not scan `~/Downloads` or any default folder. The user names the file.
  A later `lrh sessions sync --exports-dir` pickup is an open question in
  the proposal.
- Do not install a watcher or a launchd job.
- Do not import Codex or Antigravity exports.
- Do not re-verify against the original transcript, which stayed in the
  cloud container. The check is manifest-only.

## Acceptance Criteria

- The imported file lands at exactly the path the exporter would have used,
  enforced by a shared helper and a test.
- Permissions are 0700 for folders and 0600 for the file from the first
  byte, under a permissive umask.
- Non-exports and conflicting exports are refused. Identical and grown
  same-source files are handled.
- The source is kept unless `--move`. `--dry-run` writes nothing.
- No transcript text is printed.
- `lrh validate`, `scripts/test`, `scripts/lint` and
  `scripts/format --check --diff` pass.

## Validation

- `scripts/version tools`
- `lrh validate`
- `scripts/format --check --diff`
- `scripts/lint`
- `scripts/test`
- `lrh conversation import-claude-export --help`
- `lrh skills check --target claude --local`

## Risk Notes

- Exports written before `exported_at` existed, or with a malformed value,
  must be refused with a clear error rather than filed under a guessed
  month.
- The helper refactor must not change existing export paths. Add a
  regression test before refactoring.
