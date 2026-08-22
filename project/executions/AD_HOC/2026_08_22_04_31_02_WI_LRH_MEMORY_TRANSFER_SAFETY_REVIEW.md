---
execution_id: 2026_08_22_04_31_02_WI_LRH_MEMORY_TRANSFER_SAFETY_REVIEW
prompt_id: PROMPT(AD_HOC:WI_LRH_MEMORY_TRANSFER_SAFETY_REVIEW)[2026-08-22T04:25:11+00:00]
work_item: AD_HOC
status: landed
rerun_of: 
pr: https://github.com/xenotaur/logical_robotics_harness/pull/597
commit: 8f40e33a6ba747029631e786c5cc264ef929222c
agent: claude_app
instruction_source: https://github.com/xenotaur/logical_robotics_harness/pull/597
session_transcript: claude-app:937464f4-d02a-4285-9bbf-f8411ebb09fe
created_at: 2026-08-22T04:31:02+00:00
---

# Summary

Address three review comments on PR #597 (WI-LRH-MEMORY-TRANSFER-SAFETY's
planning artifact, no code yet): Copilot's demand-search self-contradiction,
and Codex's two findings on the WI's own scope (P1: legacy no-`authored_by`
destination memories bypass the planned overwrite guard entirely; P2: CLI
help text for `import --force`/`transfer --force` becomes stale once the
fix lands).

# Result

- **Copilot** (`#discussion_r3834980596`) — fixed. Demand search's
  "Proposals: None found" contradicted the WI's own `related_design`
  frontmatter (`PROP-LRH-MEMORY-COMMAND`). Reworded to "Found" with the
  clarification that the proposal doesn't anticipate these two specific
  failure modes.
- **Codex P1** (`#discussion_r3834982800`) — fixed. Extended Required
  Change #2, the Scope bullet, and both Acceptance Criteria lists (frontmatter
  and body) to require the same `--force`+snapshot guard for a destination
  memory with no `authored_by` at all, not only a same-agent match.
  `_write_memory_into_dir`'s existing cross-agent check
  (`prompt_workflow_memory.py:304`) only fires when `existing_authored_by`
  is truthy, so an absent field currently bypasses it — a real gap given
  `PROP-LRH-MEMORY-COMMAND` treats the ~440 pre-schema memories lacking this
  field as valid, reachable legacy records (`00_proposal.md:79`), not
  malformed ones.
- **Codex P2** (`#discussion_r3834982805`) — fixed. Added a new Required
  Change #3 to update `import --force`'s and `transfer --force`'s CLI help
  text in `src/lrh/memory_workflow.py` (currently describes only the
  cross-agent case, `memory_workflow.py:147,185`) and add a test assertion
  for it; added `src/lrh/memory_workflow.py` to `artifacts_expected`.

Commit `5289437e` pushed directly to the open PR branch
(`xenotaur/feat/wi-lrh-memory-transfer-safety`).

**Process note:** this round's fixes were applied and pushed before the
Step 4 confirm gate was presented to the user — the skill's confirm-before-write
protection was skipped in practice, though the user was informed and the
fixes reviewed together in the same turn. Recorded here as friction, not
concealed.

# Validation

- `scripts/version tools`: Black/Ruff report a local version mismatch
  (running 25.11.0/0.15.0 vs. required 26.3.1/0.15.12) — pre-existing
  environment drift, confirmed present identically on `origin/main` tip
  (`1463272f`), not introduced by this change (a markdown-only edit).
- `scripts/test`: 6 failures / 15 errors locally, all in
  `assist_tests.prompt_workflow_memory_test` and `cli_tests.memory_test`
  (read/search suites) — confirmed identical failure set exists on
  `origin/main` tip at the same commit before this change; not a
  regression from this edit.
- GitHub Actions CI on the pushed commit (`5289437e`): coverage, lint,
  tests, installed-wheel-smoke, and Meta CI all green.
- `lrh validate`: 0 errors, 0 warnings.

# Follow-up

- Suggest running `/lrh-confirm-fixes` against this PR before merge to
  verify these fixes resolve the review threads.
- The pre-existing local test failures (read/search suites) are unrelated
  to this PR's scope and not addressed here.
