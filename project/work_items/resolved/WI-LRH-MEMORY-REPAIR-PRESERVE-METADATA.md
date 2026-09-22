---
id: WI-LRH-MEMORY-REPAIR-PRESERVE-METADATA
title: Make lrh memory repair preserve unknown frontmatter keys
type: deliverable
status: resolved
blocked: false
blocked_reason: null
resolution: "Implemented and merged in PR #702 (commit 50aeda70)."
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
forbidden_actions:
  - force_push
  - delete_branch
  - write_to_real_claude_projects_in_tests
  - run_repair_against_the_real_memory_corpus
acceptance:
  - repair with --set metadata.authored_by on a memory carrying Claude Code auto-memory metadata (node_type, originSessionId, modified) keeps every extra metadata key and any extra top-level frontmatter key, with values byte-for-byte unchanged (including an unquoted ISO timestamp)
  - repair output for a memory with only the canonical schema keys is byte-identical to today's output, and all existing repair tests pass unchanged
  - Body content is unchanged apart from the existing leading/trailing blank-line normalization, which is documented
  - Extra keys cannot shadow or duplicate the canonical fields (name, description, metadata.type, metadata.authored_by, metadata.applies_to)
  - A unittest.TestCase test reproduces the current key loss against a temp --claude-projects-root, and fails without the fix
  - docs/reference/cli/memory.md and Decision 9 of the adopted proposal state that repair preserves unknown frontmatter keys
  - lrh validate reports 0 errors
required_evidence:
  - manual_review
  - lrh_validate
  - test_output
artifacts_expected:
  - src/lrh/prompt_workflow_memory.py
  - tests/assist_tests/prompt_workflow_memory_test.py
  - docs/reference/cli/memory.md
  - project/design/proposals/adopted/lrh-memory-command/00_proposal.md
---

## Summary

`lrh memory repair` is documented as a conservative, structural-only fix-up
that never touches body content, but it rebuilds the frontmatter from
scratch and silently drops every key outside its canonical schema. Make it
preserve unknown frontmatter keys, so a legacy-memory backfill (setting
`metadata.authored_by` on files written before that field existed) loses
nothing.

## Problem / Context

14 memories in the canonical corpus were written by Claude Code's built-in
auto-memory, not by `lrh memory write`. They lack `metadata.authored_by`
(so `validate` reports them as `legacy`, `--agent` filters skip them, and
`write`'s cross-agent overwrite guard does not protect them) and carry
Claude Code's own metadata: `node_type`, `originSessionId`, and `modified`.
Backfilling `authored_by` with `lrh memory repair` would drop that
provenance, and the repository has no evidence whether Claude Code reads
those keys.

Code path: `repair_memory` (`src/lrh/prompt_workflow_memory.py`) reads the
frontmatter, then calls `write_memory(..., force=True)`, which calls
`_render_memory_file`. That function emits only `name`, `description`, and
`metadata.{type, authored_by, applies_to}`, so any other key is lost.

Format hazard, measured: a YAML parse-and-dump round trip rewrites an
unquoted timestamp. `modified: 2026-08-19T04:27:39.225Z` parses to a
datetime and is dumped as `modified: 2026-08-19 04:27:39.225000+00:00`. A
correct fix therefore has to preserve extra keys textually, not merely
semantically.

Prior-art check:

- Duplication verdict: nothing in-repo, in sibling repos, or externally does
  this. `repair_memory` is the only frontmatter-rewriting path and has no
  key-preservation.
- Demand verdict: no existing work item, proposal, or backlog entry asks for
  it. Decision 9 of the adopted proposal calls `repair` "structural-only" but
  does not say it drops unknown keys.

## Scope

- `lrh memory repair` only.
- Whether `write` (overwriting an existing memory), `import`, and `transfer`
  have the same key-loss is out of scope; record the finding in the work
  item's execution record so it can be tracked separately if real.

## Required Changes

1. Carry unknown top-level and `metadata` keys through the repair path,
   preserved as text rather than re-serialized (for example, capture the raw
   frontmatter lines of the non-canonical keys and re-emit them verbatim).
2. Emit preserved keys after the canonical keys. Canonical fields always win
   over same-named extras, and `--set` still overrides, so extras can never
   shadow or duplicate `name`, `description`, `metadata.type`,
   `metadata.authored_by`, or `metadata.applies_to`.
3. Add tests using `unittest.TestCase` and `tempfile.TemporaryDirectory`
   (`AGENTS.md`, `STYLE.md` Rule 5): a reproduction of the current key loss
   that fails without the fix, a check that an unquoted ISO timestamp
   survives byte-for-byte, and a check that canonical-only memories produce
   byte-identical output to today's.
4. Update `docs/reference/cli/memory.md` and Decision 9 of the adopted
   proposal to state that repair preserves unknown frontmatter keys.

## Non-Goals

- No backfill of the real memory corpus. That is a separate operation, done
  after this ships, with a backup first (`lrh memory sync` plus a tar of the
  corpus), because `repair` runs with `force=True` and takes no snapshot.
- No change to `--set` supported keys, and no change to body content.
- No change to `write`, `import`, or `transfer` behavior.
- No tests that touch the user's real `~/.claude/projects`; use
  `--claude-projects-root` against a temp dir.

## Acceptance Criteria

- `repair --set metadata.authored_by=<agent>` on a memory carrying
  `node_type`, `originSessionId`, and `modified` keeps every extra key,
  including any extra top-level key, with values byte-for-byte unchanged.
- A memory with only the canonical schema keys repairs to output identical to
  today's, and all existing repair tests pass unchanged.
- Body content is unchanged apart from the existing leading/trailing
  blank-line normalization, which is documented.
- Extra keys cannot shadow or duplicate the canonical fields.
- A test reproduces the current key loss and fails without the fix.
- The CLI reference and Decision 9 say repair preserves unknown frontmatter
  keys.
- `lrh validate` reports 0 errors.

## Validation

- scripts/format --check --diff
- scripts/lint
- scripts/test
- lrh validate

## Risk Notes

- A YAML round trip reformats timestamps; preserve extra keys as text.
- Preserved keys must not smuggle in duplicate or conflicting canonical
  fields.
- `repair` overwrites with `force=True` and no snapshot; any run against the
  real corpus needs a backup first.
- Run `lrh` with `PYTHONPATH=src` when working from a non-primary worktree.
