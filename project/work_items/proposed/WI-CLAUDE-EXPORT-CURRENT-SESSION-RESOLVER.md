---
resolution: null
blocked_reason: null
blocked: false
id: WI-CLAUDE-EXPORT-CURRENT-SESSION-RESOLVER
title: Add a current-session resolver, --current, and a scoped --latest to the Claude exporter
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
  - create_file
  - edit_file
  - add_cli_command
  - write_docs
forbidden_actions:
  - force_push
  - delete_branch
  - implement_export_claude_skill_changes
  - change_codex_export_behavior
acceptance:
  - "lrh conversation current-claude-session-id reports the current session id, its host pointer, and its resolved transcript path without reading transcript content, and exits nonzero with a clear message when the session cannot be resolved"
  - "lrh conversation export-claude-session accepts --current as a member of the mutually exclusive discovery group and never falls back to --latest"
  - "--latest is scoped by default to the invoking working directory's Claude project directory, with --all-projects restoring the previous whole-projects behaviour"
  - "A successful export prints a Source transcript line with the resolved transcript path, and no transcript content"
  - "docs/reference/cli/conversation.md documents the new command, --current, --all-projects, and the Source transcript line"
  - "lrh validate reports 0 errors and introduces no new warnings"
required_evidence:
  - manual_review
  - lrh_validate
  - test_output
artifacts_expected:
  - src/lrh/conversations/claude_session.py
  - src/lrh/conversations/claude_export.py
  - src/lrh/conversations/__init__.py
  - src/lrh/cli/main.py
  - tests/conversations_tests/claude_session_test.py
  - tests/conversations_tests/claude_export_test.py
  - tests/cli_tests/conversation_test.py
  - docs/reference/cli/conversation.md
---

# WI-CLAUDE-EXPORT-CURRENT-SESSION-RESOLVER: Add a current-session resolver, --current, and a scoped --latest to the Claude exporter

## Summary

Give the Claude exporter the same "export this session" entry point the Codex exporter
has: a metadata-only `lrh conversation current-claude-session-id` resolver and an
`export-claude-session --current` flag. Also make `--latest` safe by scoping it to the
current project by default, and have the CLI report which transcript it used.

## Problem / Context

Codex has a shared resolver, `lrh conversation current-codex-thread-id`
(`src/lrh/conversations/codex_session.py`: `resolve_codex_session_identity`,
`run_current_codex_thread_id_cli`, with `--format` and `--field`), and
`/lrh-codex-export` defaults to `CODEX_THREAD_ID`. There is no Claude equivalent: no code
under `src/lrh` reads `CLAUDE_CODE_SESSION_ID` or `CLAUDE_CODE_HOST_SESSION_ID`. The only
consumer is prose in skills, and `/lrh-closeout` Step 3 derives the host-session pointer
by hand from the environment and asks the user to confirm it.

Observed during the first real run of `/lrh-export-claude`:

- **`--latest` picked the wrong session.** With several sessions active, another
  session's transcript was newer by one second, so `--latest` (which sorts every
  `projects/*/*.jsonl` by modification time; `claude_export.py`, `_resolve_transcript_path`)
  would have exported a different conversation.
- **The resolved path is never reported.** The exporter's success output prints the
  destination, source id and hash, privacy, sensitivity, and warning count, but not the
  transcript path it read. Callers must re-derive it, and `/lrh-export-claude` Step 1
  re-implements the glob rules in prose. A duplicated rule already drifted once (a
  review finding on PR #669).

Facts checked in the Claude.app session used for that first run: `CLAUDE_CODE_SESSION_ID` equals the
transcript's filename stem (a `projects/*/<id>.jsonl` glob matched exactly one file);
`CLAUDE_CODE_HOST_SESSION_ID` has the form `local_<uuid>`, from which the durable
`claude-app:<uuid>` pointer is derived (per `/lrh-closeout` Step 3; the host id can rotate
on resume). `project_slug_for_path` (`src/lrh/prompt_workflow_sessions.py`) returned exactly
the real Claude project directory name for this worktree, so it can scope `--latest`.

**Unverified, must be checked during implementation:** whether these environment
variables are set outside the Claude desktop app (plain CLI, IDE integrations). The
resolver must not silently fall back to `--latest` when they are missing; it should fail
with a clear message.

### Duplication search
- In-repo: the Codex resolver is the precedent to mirror (`WI-CODEX-SESSION-ID-RESOLVER`, resolved). No Claude equivalent exists; a search of `src/lrh/**/*.py` finds no reader of `CLAUDE_CODE_SESSION_ID`.
- Sibling repos: none identified.
- External libraries: not applicable.
- Recommendation: Proceed.

### Demand search
- Work items: none open on a Claude session resolver or a scoped `--latest`.
- Proposals: `PROP-LRH-CLAUDE-CONVERSATION-EXPORTER` defines `--latest` as newest across all projects and has no current-session concept.
- Backlog: no matching entry.
- Recommendation: No action; this item is the tracking artifact.

## Scope

- New `lrh conversation current-claude-session-id` command (metadata only).
- New `--current` discovery flag on `export-claude-session`.
- `--latest` scoped to the invoking working directory's project by default, plus `--all-projects`.
- A `Source transcript:` line in the exporter's success output.
- Docs and tests.

## Required Changes

1. Add `src/lrh/conversations/claude_session.py`, modelled on `codex_session.py`: `lrh conversation current-claude-session-id` with `--format text|json` and `--field`. It reports the session id from `CLAUDE_CODE_SESSION_ID`, the host pointer derived from `CLAUDE_CODE_HOST_SESSION_ID` (`local_` stripped, `claude-app:<uuid>`), and the transcript path found by globbing `<app-data-dir>/projects/*/<id>.jsonl` (honouring `CLAUDE_CONFIG_DIR` and `--app-data-dir` as the exporter does). It never reads or prints transcript content. It exits nonzero with a clear message when the id is unset, or when zero or several transcripts match.
2. Register the command in `src/lrh/cli/main.py` and export it from `src/lrh/conversations/__init__.py`.
3. Add `--current` to `export-claude-session` as a fourth member of the required mutually exclusive discovery group, resolved through the shared resolver. It must error, not fall back to `--latest`, when the session cannot be resolved.
4. Scope `--latest` by default to `<app-data-dir>/projects/<project_slug_for_path(cwd)>/`, and add `--all-projects` to restore the current behaviour. Keep the documented silent tie-break.
5. Print `Source transcript: <path>` in the success output (path only, no content), so callers stop re-deriving resolution.
6. Update `docs/reference/cli/conversation.md`: a `current-claude-session-id` section, `--current`, `--all-projects`, the `Source transcript:` line, and the resolver's failure behaviour.
7. Add `unittest.TestCase` tests (standard-library fixtures only, e.g. `unittest.mock.patch.dict(os.environ, ...)` and `tempfile.TemporaryDirectory`; no pytest fixtures): id resolves to the transcript; unset id fails clearly; ambiguous or missing match fails; `--current` exports the right file; `--current` never falls back to `--latest`; scoped `--latest` picks the working directory's newest file even when another project's file is newer; `--all-projects` restores the old pick; the `Source transcript:` line is present; `--current` is mutually exclusive with the other discovery flags; a CLI-level test through `lrh.cli.main`.

## Non-Goals

- Does not change `inspect-export` or the manifest (`WI-INSPECT-EXPORT-APPEND-ONLY-SOURCE-VERIFY`).
- Does not change the `/lrh-export-claude` skill (`WI-EXPORT-CLAUDE-SKILL-CURRENT-SESSION-DEFAULT`).
- Does not change Codex or Antigravity behaviour.
- Does not migrate `/lrh-closeout` Step 3 to use the new resolver. That is a natural follow-up: it would replace hand-derived host-id handling with the shared resolver.

## Acceptance Criteria

- `current-claude-session-id` reports the id, host pointer, and transcript path, metadata only, and fails clearly when unresolvable.
- `--current` works, is mutually exclusive with the other discovery flags, and never falls back to `--latest`.
- `--latest` is scoped to the current project by default; `--all-projects` restores the old behaviour.
- A successful export prints the `Source transcript:` line and no content.
- The CLI reference documents all of it.
- The environment-variable availability outside the desktop app is verified and the result documented.
- `lrh validate` reports 0 errors and introduces no new warnings.

## Validation

- `PYTHONPATH=src scripts/test tests/conversations_tests/claude_session_test.py`
- `PYTHONPATH=src scripts/test tests/conversations_tests/claude_export_test.py`
- `PYTHONPATH=src scripts/test tests/cli_tests/conversation_test.py`
- `PYTHONPATH=src scripts/test`
- `scripts/lint`
- `scripts/format --check --diff`
- `lrh validate`
