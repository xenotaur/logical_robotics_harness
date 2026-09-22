---
id: WI-LRH-MEMORY-WRITE-OVERWRITE-PRESERVE-METADATA
title: Fix key-loss and filename-derivation bugs in lrh memory write/import/transfer/repair
type: deliverable
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
forbidden_actions:
  - force_push
  - delete_branch
  - write_to_real_claude_projects_in_tests
  - run_repair_or_write_against_the_real_memory_corpus_without_a_backup
acceptance:
  - Overwriting an existing memory via write, import, or transfer preserves that memory's unknown frontmatter keys, the same way repair now does
  - Importing or transferring a bundled record into a corpus where it does not yet exist (a new file, not an overwrite) also preserves the source's unknown metadata keys, since the bundle already carries them (_export_records_from_dir exports the full metadata dict) but _import_records_into_dir currently discards everything except type/authored_by/applies_to regardless of whether the destination is new or existing
  - repair (and any other command that resolves a target file from a caller-supplied name) writes to the SAME file it read, even when the memory's own name field omits a type prefix its filename carries; it never silently creates a second, differently-named file
  - A regression test exists for EACH of write, import (new-file case), import (overwrite case), transfer, and repair's filename-derivation bug, separately -- not one shared test covering only a subset of these five entry points -- and each fails without its corresponding fix
  - lrh memory validate reports a name/filename mismatch as a first-class finding (a new or existing bucket) -- this is a required change, not an optional consideration, since the acceptance criteria already require it
  - docs/reference/cli/memory.md documents all of the above
  - lrh validate reports 0 errors
required_evidence:
  - manual_review
  - lrh_validate
  - test_output
artifacts_expected:
  - src/lrh/prompt_workflow_memory.py
  - tests/assist_tests/prompt_workflow_memory_test.py
  - docs/reference/cli/memory.md
---

## Summary

`lrh memory repair` was fixed (WI-LRH-MEMORY-REPAIR-PRESERVE-METADATA) to
preserve frontmatter keys outside its own schema on an overwrite. Three
related defects remain: `write`, `import`, and `transfer` share the same
key-loss on their own overwrite paths; `import`/`transfer` also drop
source-carried unknown metadata even when writing a brand-new file, since
the bundle already carries the full metadata dict but the import path only
extracts three canonical keys from it; and `repair` itself can silently
write to the wrong file when a memory's `name:` field doesn't match its
on-disk filename -- discovered live during that work item's real-corpus
backfill.

## Problem / Context

**Key-loss on overwrite.** `write`, `import`, and `transfer` all funnel
through `_render_memory_file` on an overwrite, the same function `repair`
used before its fix. Overwriting an existing memory through any of these
three commands silently drops any frontmatter key outside
`name`/`description`/`metadata.{type,authored_by,applies_to}`.

**Filename-derivation bug in `repair`.** `repair_memory` resolves its
write-back path from the frontmatter `name:` field
(`merged_name = frontmatter.get("name", slug)`), not from the caller-supplied
name used to locate the file. When a memory's `name:` field omits the type
prefix its on-disk filename carries (e.g. filename
`feedback_closeout_direct_main_push_blocked_use_pr.md` with
`name: closeout-direct-main-push-blocked-use-pr`), running `repair` on the
correct argument reads the right file but writes a **new, differently-named**
file, leaving the original untouched and unfixed, and adding a duplicate,
worse-titled `MEMORY.md` entry for the same memory.

Reproduced live during the WI-LRH-MEMORY-REPAIR-PRESERVE-METADATA backfill:
`feedback_closeout_direct_main_push_blocked_use_pr.md`,
`feedback_compound_command_with_denied_git_branch_delete.md`,
`feedback_lrh_land_from_pr_branch_defer_chain_defaults_restamp.md`, and
`project_land_worktree_lock_reverted_to_tmp_branch.md` all had this
mismatch; each `repair` run created a stray duplicate file and index entry.
Manually remediated in that session (stray files deleted, duplicate index
entries removed, originals hand-backfilled with `authored_by`); the real
corpus is currently clean (`lrh memory validate`: 0 malformed/unindexed/
legacy, 43 conforming) but the bug in the code itself is unfixed and will
recur on the next affected file.

Prior-art check:

- Duplication verdict: nothing in-repo does this. WI-LRH-MEMORY-REPAIR-
  PRESERVE-METADATA fixed `repair` only; its own Scope section explicitly
  excluded `write`/`import`/`transfer`.
- Demand verdict: no existing work item or backlog entry names either issue.

## Scope

- The overwrite path of `write`, `import`, and `transfer`.
- `import`/`transfer`'s new-file path specifically for source-derived
  unknown metadata (a record already carried in the bundle via
  `_export_records_from_dir`'s full-metadata export, currently discarded on
  import regardless of whether the destination is new or existing) --
  `write`'s own new-file case is unaffected and out of scope, since it has
  no prior source to preserve from.
- `repair`'s filename/write-back-path resolution.
- `lrh memory validate` surfacing a name/filename mismatch as its own
  finding.

## Required Changes

1. Thread `preserved_top_level_lines`/`preserved_metadata_lines` (already
   built for `repair`) into the overwrite path of `write`, `import`, and
   `transfer`.
2. Widen `_import_records_into_dir`'s extraction of a bundled record's
   `metadata` (currently only `type`/`authored_by`/`applies_to`) to also
   carry through any other keys the bundle's full `metadata` dict holds,
   for both the new-file and overwrite cases, and define how source and
   destination extras reconcile on overwrite (source wins, destination
   wins, or merge -- pick one and document it).
3. Make `repair` (and any shared helper) always resolve its write-back path
   from the file it actually opened, never from a frontmatter field that
   might not match it. The existing refusal of `--set name=<...>` (no
   renaming) must stay intact.
4. Make `lrh memory validate` report a name/filename mismatch as a
   first-class finding (a new or existing bucket) -- required, not
   optional, so it is visible before it causes a silent duplicate.
5. Tests reproducing every bug above, using `unittest.TestCase` and
   `tempfile.TemporaryDirectory` (`AGENTS.md`, `STYLE.md` Rule 5): one each
   for `write` overwrite, `import` new-file, `import` overwrite,
   `transfer`, and `repair`'s filename-derivation bug.
6. Update `docs/reference/cli/memory.md`.

## Non-Goals

- No change to `write`'s own new-file semantics (it has no source to
  preserve extras from).
- No automated fix-up of any other real-corpus inconsistency beyond what is
  already remediated.
- No change to `transfer`'s literal path/slug resolution for `--from`/`--to`.
- No tests touching the user's real `~/.claude/projects`; use
  `--claude-projects-root` against a temp dir.

## Acceptance Criteria

- Overwriting an existing memory via `write`, `import`, or `transfer`
  preserves its unknown frontmatter keys.
- Importing or transferring a bundled record into a corpus where it does
  not yet exist also preserves the source's unknown metadata keys.
- `repair` writes to the same file it read, even when `name:` omits a type
  prefix its filename carries; it never creates a second, differently-named
  file.
- A separate regression test exists for each of the five entry points
  above (write overwrite, import new-file, import overwrite, transfer,
  repair filename-derivation), and each fails without its fix.
- `lrh memory validate` reports a name/filename mismatch as a required,
  first-class finding.
- The CLI reference documents all of the above.
- `lrh validate` reports 0 errors.

## Validation

- scripts/format --check --diff
- scripts/lint
- scripts/test
- lrh validate

## Risk Notes

- Any manual testing against the real corpus needs a backup first
  (`lrh memory sync` plus a tar of the corpus), per this incident.
- The filename-derivation fix must keep the "no renaming via `--set name=`"
  refusal intact -- it must always write back to the same path it read, not
  adopt whatever the frontmatter `name:` claims.
- Run `lrh` with `PYTHONPATH=src` when working from a non-primary worktree.
