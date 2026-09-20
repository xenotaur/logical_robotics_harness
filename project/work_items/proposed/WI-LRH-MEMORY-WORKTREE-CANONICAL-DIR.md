---
id: WI-LRH-MEMORY-WORKTREE-CANONICAL-DIR
title: Resolve lrh memory write to the canonical memory dir for worktree sessions, and recover orphaned memories
type: investigation
status: proposed
blocked: false
blocked_reason: null
resolution: null
owner: anthony
contributors:
  - anthony
assigned_agents: []
related_focus: []
related_roadmap: []
related_workstreams:
  - WS-LRH-MEMORY-COMMAND
related_design:
  - project/design/proposals/adopted/lrh-memory-command/00_proposal.md
depends_on: []
blocked_by: []
expected_actions:
  - edit_file
  - run_tests
  - investigate
forbidden_actions:
  - force_push
  - delete_branch
  - delete_or_move_user_memory_files_without_confirmation
  - write_to_real_claude_projects_in_tests
acceptance:
  - Design question settled and documented with evidence from real Claude Code behavior (worktree maps to main repo via git common dir, or otherwise)
  - If the outcome maps worktrees to the main-repo corpus, the adopted lrh-memory-command proposal's Decision 8 (separate worktree corpora with curated transfer) is explicitly amended or superseded
  - lrh memory write from a worktree cwd resolves to the canonical dir, or fails/warns loudly when the target differs from it
  - A test reproduces the cwd-in-worktree slug mismatch, using --claude-projects-root against a temp dir
  - A recovery command detects orphaned worktree-suffixed memory dirs and merges them into the canonical dir non-destructively (cp -n semantics, index updated, originals left in place)
  - Underscore-slug orphan (dir B) origin confirmed or refuted; files of unknown provenance are reported, not moved
  - lrh validate reports 0 errors
required_evidence:
  - manual_review
  - lrh_validate
  - test_output
artifacts_expected:
  - src/lrh/prompt_workflow_memory.py
  - src/lrh/memory_workflow.py
  - tests/assist_tests/prompt_workflow_memory_test.py
  - docs/reference/cli/memory.md
  - project/design/proposals/adopted/lrh-memory-command/00_proposal.md
---

## Summary

`lrh memory write` derives its target `~/.claude/projects/<slug>/memory/`
from the cwd. Inside a git worktree the slug gains a
`--claude-worktrees-<name>` suffix, but the session's canonical memory
directory has no suffix, so memories land in a directory future sessions
never read. The command still prints a normal "wrote:/indexed:" result, so
nothing warns the user. This work item settles which directory is canonical
for a worktree session, fixes the write path, and adds non-destructive
recovery of already-orphaned memories.

## Problem / Context

Reproduced at least twice:

- PR #668 session: wrote to
  `...--claude-worktrees-lrh-work-item-ordering-dep-78ba8c/memory/`
  (documented in the canonical memory
  `feedback_lrh_memory_write_cwd_project_slug.md`).
- Session in worktree `lrh-memory-command-design-46789b`: orphaned 8 memories
  across two non-canonical directories.
  - Dir A: hyphen slug + worktree suffix.
  - Dir B: underscore `logical_robotics_harness` + worktree suffix.

Relevant code:

- `src/lrh/prompt_workflow_sessions.py:1083` `project_slug_for_path()`
- `src/lrh/prompt_workflow_memory.py:48` `memory_dir_for_project()`
- `src/lrh/prompt_workflow_memory.py:1155` `_resolve_memory_dir()`
- `src/lrh/memory_workflow.py` (the `lrh memory write` command)

`lrh memory write` already has a `--claude-projects-root` flag, which is the
documented workaround. Prior related fix: WI-PROJECT-SLUG-SYMLINK-RESOLUTION
(PR #615) changed slug spelling (no symlink resolution; underscores replaced).
It did not address mapping a worktree to its main repo.

Prior-art check:

- Duplication verdict: nothing in-repo, in sibling repos, or externally does
  this. PR #615 covers slug spelling only.
- Demand verdict: no existing work item, proposal, or backlog entry tracks
  this (searched project/work_items, project/design/backlog.md, proposals).

Unverified (investigate, do not assert):

- Why dir B uses underscores. Hypothesis: an older `lrh` build predating the
  PR #615 underscore fix (commit e5096c6f) wrote it. Confirm or refute.
- The orphan dirs contain files of unknown provenance that must not be moved
  or deleted without confirmation: feedback_bash_heredoc_in_quoted_cmd_substitution,
  feedback_codex_review_not_triggered_by_push,
  feedback_force_push_blocked_use_merge_instead (dir B);
  feedback_stop_work_condition_survives_batch_approval,
  feedback_memory_testing_needs_explicit_claude_projects_root,
  project_memory_md_stale_vs_transfer_safety_fix (dir A).

## Scope

1. Settle first: for a session running in a worktree, which directory is
   canonical, the main repo's project dir (no suffix) or the worktree's?
   Claude Code appears to store the transcript under the worktree-suffixed
   dir but auto-memory under the main repo's, so the likely answer is
   "map worktree to main repo (git common dir)". Verify against real
   behavior before deciding.
2. Fix `lrh memory write` (and sibling memory commands sharing the
   resolver) accordingly.
3. If the decision changes corpus identity for worktrees, amend or supersede
   Decision 8 of the adopted `lrh-memory-command` proposal, which currently
   chooses separate worktree corpora with curated `transfer`; the control
   plane must not prescribe contradictory behavior.
4. Provide detection and non-destructive merge of orphaned worktree-suffixed
   memory dirs into the canonical one.

## Required Changes

1. Document the canonical-dir decision with evidence.
2. Make resolution map a worktree cwd to the canonical dir, or at minimum
   fail/warn loudly when the target differs from the canonical one.
3. Add a recovery command (with `--dry-run`) that detects orphan dirs and
   merges with `cp -n` semantics, updates the index, and leaves originals
   in place; report files of unknown provenance rather than acting on them.
4. Add tests, including one reproducing the cwd-in-worktree mismatch. Tests
   must subclass `unittest.TestCase` and use `tempfile.TemporaryDirectory`
   (`AGENTS.md`, `STYLE.md` Rule 5).
5. Update memory command docs (`docs/reference/cli/memory.md`).
6. Amend or supersede Decision 8 of the adopted proposal if the outcome
   maps worktrees to the main-repo corpus.

## Non-Goals

- No moving or deleting files of unknown provenance.
- No tests touching the user's real `~/.claude/projects`; use
  `--claude-projects-root` against a temp dir.
- No changes to session-transcript slugging.
- No code changes in the session that creates this work item.

## Acceptance Criteria

- The canonical-dir design question is settled and documented with evidence.
- `lrh memory write` from a worktree cwd resolves to the canonical dir, or
  fails/warns loudly when the target differs.
- If worktrees map to the main-repo corpus, Decision 8 of the adopted
  proposal is amended or superseded.
- A test reproduces the cwd-in-worktree slug mismatch against a temp
  projects root.
- A recovery command merges orphaned worktree-suffixed memory dirs
  non-destructively (`cp -n`, index updated, originals kept).
- Dir B's underscore origin is confirmed or refuted; unknown-provenance
  files are reported only.
- `lrh validate` reports 0 errors.

## Validation

- scripts/format --check --diff
- scripts/lint
- scripts/test
- lrh validate

## Risk Notes

- Guessing the wrong canonical dir could orphan memories in the other
  direction; verify against real Claude Code behavior first.
- Recovery must never overwrite existing canonical files.
- Bare `lrh` may resolve to a different checkout; run with `PYTHONPATH=src`.
