---
resolution: null
blocked_reason: null
blocked: false
id: WI-LRH-MEMORY-WRITE-SIDE
title: Implement lrh memory write/list/validate/repair
type: deliverable
status: proposed
owner: null
contributors: []
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
  - create_file
  - edit_file
  - add_cli_command
  - run_tests
forbidden_actions:
  - force_push
  - delete_branch
  - implement_lrh_memory_sync
  - implement_lrh_memory_read
  - implement_lrh_memory_search
  - implement_lrh_memory_export
  - implement_lrh_memory_import
  - implement_lrh_memory_transfer
acceptance:
  - lrh memory write creates a validated memory file and a MEMORY.md index entry
  - lrh memory write rejects malformed or missing frontmatter rather than writing it
  - lrh memory list and lrh memory validate distinguish malformed from legacy memories
  - lrh memory repair patches frontmatter/index fields only, never body content, and preserves the original authored_by unless explicitly overridden
  - src/lrh/skills/lrh-closeout/SKILL.md (and its rendered installs) call lrh memory write instead of writing memory files directly
  - lrh validate reports 0 errors after all files are written
required_evidence:
  - manual_review
  - lrh_validate
  - test_output
artifacts_expected:
  - src/lrh/atomic_write.py
  - src/lrh/prompt_workflow_memory.py
  - src/lrh/memory_workflow.py
  - src/lrh/cli/main.py
  - src/lrh/skills/lrh-closeout/SKILL.md
  - project/memory/decisions/DEC-LRH-MEMORY-AUTHORED-BY.md
---

# Implement lrh memory write/list/validate/repair

## Summary

Implement `lrh memory write`, `lrh memory list`, `lrh memory validate`, and
`lrh memory repair` — the write-side command surface that makes malformed
writes to Claude Code's per-project memory corpus structurally impossible,
per `PROP-LRH-MEMORY-COMMAND`.

## Problem / Context

Agents write directly into Claude Code's memory files
(`~/.claude/projects/<slug>/memory/`) today, with no shared tooling and no
validation. `experimental/rescue_claude_sessions/findings.md` documents 19
of 461 memory files across 5 project buckets lacking required frontmatter,
including one Codex wrote live with no `MEMORY.md` entry. This item
delivers the validated write path, its read-side companion (`list`), its
conformance auditor (`validate`), and the retroactive fix-up tool
(`repair`) that close this gap.

### Duplication search
- In-repo: No existing implementation. `project_slug_for_path()` at
  `src/lrh/prompt_workflow_sessions.py:515` and `_atomic_write` at
  `:159-181`/`_atomic_write_bytes` at `:184-211` already exist and should be reused/
  extracted, not reimplemented. `lrh work-items organize`'s "conservatively
  repair" framing (`src/lrh/cli/main.py:293-296`) is the precedent for
  `repair`'s scope.
- Sibling repos: None identified.
- External libraries: None identified.
- Recommendation: Proceed, reusing the cited helpers.

### Demand search
- Backlog: Found — `project/design/backlog.md`'s "lrh memory command to
  make cross-agent memory writes well-formed by construction" entry.
- Proposals: Found — `PROP-LRH-MEMORY-COMMAND` (this item implements its
  Decisions 2, 3, 4's crash-consistency addendum, and 9).
- Recommendation: Offer to close/link the backlog entry once all four
  workstream work items resolve (tracked at the `WS-LRH-MEMORY-COMMAND`
  level, not per-item).

## Scope

- Implement `lrh memory write`, `list`, `validate`, `repair` CLI commands
- Add the `metadata.authored_by`/`metadata.applies_to` frontmatter schema,
  with `validate`'s malformed/legacy distinction
- Extract the shared atomic-write helper from `prompt_workflow_sessions.py`
- Migrate `lrh-closeout`'s direct memory-write instruction

## Required Changes

1. Extract `_atomic_write` (`src/lrh/prompt_workflow_sessions.py:159-181`)
   and `_atomic_write_bytes` (`:184-211`) into a shared module
   (`src/lrh/atomic_write.py`); update `prompt_workflow_sessions.py` to
   import from it instead of defining them locally.
2. Create `src/lrh/prompt_workflow_memory.py` implementing: frontmatter
   validation (`name`/`description`/`metadata.type` required;
   `metadata.authored_by` required for new writes only, not retroactively
   for existing conforming files; `metadata.applies_to` optional, default
   `[authored_by]`), corpus path resolution via `project_slug_for_path()`,
   `write()` (memory-file rename before `MEMORY.md` rename, per Decision
   4's crash-consistency addendum — never the reverse), `list()`,
   `validate()` (reports two categories: malformed — missing the
   pre-existing required fields; legacy — conforming but missing
   `authored_by`), and `repair()` (structural-only field patch via
   `--set`, routes through `write`'s own validated path per record,
   preserves original `authored_by` unless explicitly included in
   `--set`).
3. Create `src/lrh/memory_workflow.py` — thin CLI wiring (`run_memory_cli`),
   argparse subcommands for `write`/`list`/`validate`/`repair` per the
   proposal's API Sketch section.
4. Register `memory` in `src/lrh/cli/main.py`
   (`add_parser("memory", add_help=False)` + dispatch), following the
   `sessions` registration pattern (`main.py:150-154`, `:802-808`).
5. Edit `src/lrh/skills/lrh-closeout/SKILL.md:403-406` to call
   `lrh memory write` instead of the current direct-write instruction;
   verify the rendered `.claude/skills/`/`.agents/skills/` copies are
   regenerated to match.
6. Record the `metadata.authored_by`/`applies_to` schema decision as
   `project/memory/decisions/DEC-LRH-MEMORY-AUTHORED-BY.md`, following the
   precedent of `WI-GATE-POLICY-CASCADE-STAGE3`'s comparable schema/policy
   decisions.

## Non-Goals

- Does not begin implementation before `PROP-LRH-MEMORY-COMMAND` reaches
  `status: adopted` — see the workstream's Purpose section for why
  adoption is an entry gate, not just an exit criterion.
- Does not implement `lrh memory sync` — see `WI-LRH-MEMORY-ARCHIVE-SIDE`.
- Does not implement `lrh memory read`/`search` — see
  `WI-LRH-MEMORY-READ-SIDE`.
- Does not implement `lrh memory export`/`import`/`transfer` — see
  `WI-LRH-MEMORY-PORTABILITY`.
- Does not retroactively run `repair` against the 19 known non-conforming
  files or the ~440 legacy files — this item delivers the tool, not the
  cleanup operation.
- Does not resolve the MCP-tool-delivery Open Question from the governing
  proposal — CLI-only for this item.

## Acceptance Criteria

- `lrh memory write <name> --description ... --type ... --agent ...`
  creates a validated memory file and its `MEMORY.md` index entry.
- `lrh memory write` rejects missing/invalid frontmatter fields rather
  than writing malformed output.
- `lrh memory list` and `lrh memory validate` report accurately against a
  test corpus, with `validate` distinguishing malformed from legacy.
- `lrh memory repair --set metadata.authored_by=<agent>` structurally
  patches an existing memory's frontmatter without touching body content,
  and preserves the original `authored_by` when not explicitly overridden.
- `src/lrh/skills/lrh-closeout/SKILL.md` (and its rendered installs) call
  `lrh memory write` instead of writing memory files directly.
- `lrh validate` reports 0 errors after all files are written.

## Validation

- `scripts/version tools`
- `lrh validate`
- `scripts/format --check --diff`
- `scripts/lint`
- `scripts/test`
- `lrh memory write --help`
- `lrh memory validate --help`

## Risk Notes

- The memory-file-before-`MEMORY.md` write ordering must be implemented
  exactly as specified in Decision 4's addendum, not "atomic in the same
  operation" as an earlier proposal draft mistakenly claimed before
  review caught it — get the ordering wrong and a crash mid-write can
  produce a dangling index entry instead of the safer, already-tooled
  unindexed-file state.
- The `lrh-closeout` migration touches a canonical, frequently-invoked
  skill — verify the rendered `.claude/skills/`/`.agents/skills/` copies
  stay in sync with `src/lrh/skills/`, not just the source file.

## Related Workstream and Designs

- Workstream: `project/workstreams/proposed/WS-LRH-MEMORY-COMMAND.md`
- Design: `project/design/proposals/adopted/lrh-memory-command/00_proposal.md`
  (Decisions 2, 3, 4, 9)
