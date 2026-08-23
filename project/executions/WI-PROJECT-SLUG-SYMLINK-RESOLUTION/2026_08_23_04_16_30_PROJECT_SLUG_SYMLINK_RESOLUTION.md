---
execution_id: 2026_08_23_04_16_30_PROJECT_SLUG_SYMLINK_RESOLUTION
prompt_id: PROMPT(WI-PROJECT-SLUG-SYMLINK-RESOLUTION:PROJECT_SLUG_SYMLINK_RESOLUTION)[2026-08-22T20:31:45+00:00]
work_item: WI-PROJECT-SLUG-SYMLINK-RESOLUTION
status: landed
rerun_of: 
pr: https://github.com/xenotaur/logical_robotics_harness/pull/615
commit: e9d45739619f6784ea941fe3f4b6173263031aa5
created_at: 2026-08-23T04:16:30+00:00
agent: claude_code
instruction_source: project/work_items/proposed/WI-PROJECT-SLUG-SYMLINK-RESOLUTION.md
session_transcript: claude-app:local_02330303-d423-49f8-9864-aeac6023c0b9
---

# Summary

Implemented `WI-PROJECT-SLUG-SYMLINK-RESOLUTION`: fixed `project_slug_for_path()`
(`src/lrh/prompt_workflow_sessions.py`) to stop resolving symlinks and to
also replace underscores in its character-substitution regex, matching
Claude Code's real bucket-naming behavior.

# Result

Replaced `pathlib.Path(path).expanduser().resolve()` with
`os.path.abspath(os.path.expanduser(str(path)))` (no symlink following,
still collapses `..`/`.` and anchors relative paths). Widened
`_PROJECT_SLUG_UNSAFE` from `[/.]` to `[/._]`.

Before finalizing the underscore fix, independently re-verified the
existing docstring's own claim that underscores were "preserved as-is"
(cited a `replication_vector` bucket as evidence) — found that none of
the four `replication_vector`-related buckets on this machine contain an
actual `*.jsonl` session transcript except one, and that one (a worktree
bucket) is fully hyphenated, not underscore-preserving. The original
claim's cited evidence was a memory-only bucket, not proof of a real
Claude Code session — i.e. potentially a symptom of this exact bug
class, not counter-evidence to it. This gives independent corroboration
across two separate repositories (`logical_robotics_harness`,
`replication_vector`) that real Claude Code buckets are fully hyphenated.

Reviewed all 5 existing call sites
(`prompt_workflow_sessions.py`; `prompt_workflow_memory.py` x4): none
relied on either old behavior. Updated a stale docstring reference in
`prompt_workflow_memory.py`'s `_resolve_memory_dir` that described the
old two-character substitution. Updated `project_slug_for_path()`'s own
docstring to describe the corrected contract and cite the
transcript-bearing-bucket verification methodology.

Updated the existing `ProjectSlugForPathTest` (which asserted the now-
incorrect underscore-preservation behavior) and added a new symlink
regression test.

# Validation

- `lrh validate` — 0 errors (1 pre-existing, unrelated warning:
  `PLANNING_ACTIVE_WORKSTREAM_NO_ACTIONABLE_LEAF` on `WS-SESSION-ARCHIVE-SYNC`).
- `scripts/format --check --diff` — clean (after one `scripts/format` pass).
- `scripts/lint` — clean.
- `scripts/test` — 1331 tests, all pass.
- Manually re-verified the fix against real observed bucket state: the
  old symlinked LRH path, the new real LRH path, and this session's own
  worktree cwd all now slug to their real, existing `~/.claude/projects/`
  bucket names exactly.

# Follow-up

- None outstanding from this implementation.
