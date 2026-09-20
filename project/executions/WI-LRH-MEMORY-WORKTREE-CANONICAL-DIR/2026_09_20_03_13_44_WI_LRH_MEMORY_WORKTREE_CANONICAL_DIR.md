---
execution_id: 2026_09_20_03_13_44_WI_LRH_MEMORY_WORKTREE_CANONICAL_DIR
prompt_id: PROMPT(WI-LRH-MEMORY-WORKTREE-CANONICAL-DIR:WI_LRH_MEMORY_WORKTREE_CANONICAL_DIR)[2026-09-20T02:59:01+00:00]
work_item: WI-LRH-MEMORY-WORKTREE-CANONICAL-DIR
status: landed
rerun_of: 
pr: https://github.com/xenotaur/logical_robotics_harness/pull/681
commit: 7a9711df67e7bc994f5b5754b5a2ffece63d4f60
created_at: 2026-09-20T03:13:44+00:00
agent: claude_app
instruction_source: project/work_items/proposed/WI-LRH-MEMORY-WORKTREE-CANONICAL-DIR.md
session_transcript: claude-app:239809db-0aff-4cae-b00b-76078ee01394
---

# Summary

Implemented WI-LRH-MEMORY-WORKTREE-CANONICAL-DIR via /lrh-execute: linked git worktrees now resolve to the main checkout's memory corpus, plus a `lrh memory recover-orphans` subcommand and an amendment to Decision 8 of the adopted lrh-memory-command proposal.

# Result

- src/lrh/prompt_workflow_memory.py: canonical_project_root(), worktree_mapping_note(), find_orphan_memory_dirs(), recover_orphan_memories(); memory_dir_for_project() uses the mapping.
- src/lrh/memory_workflow.py: `recover-orphans` subcommand; `write` prints a stderr note when mapped.
- Tests (real temp git worktrees, temp --claude-projects-root): regression reproduces the cwd-in-worktree mismatch and fails with the mapping disabled.
- docs/reference/cli/memory.md and README updated; proposal Decision 8 amended with evidence and the dir B underscore-origin check (partially confirmed: earlier files predate e5096c6f, September files postdate it, consistent with a stale bare `lrh`).
- Real ~/.claude/projects untouched; no orphaned or unknown-provenance files moved or deleted.

# Validation

scripts/format --check --diff, scripts/lint, scripts/test (1622 tests, OK), lrh validate (0 errors, 1 pre-existing warning): all pass.

# Follow-up

- Run `lrh memory recover-orphans` (dry-run first) against the real ~/.claude/projects to recover the stranded memories; not done here by design.
- Resolve the work item at closeout.
