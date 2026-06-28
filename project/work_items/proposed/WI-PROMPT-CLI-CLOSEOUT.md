---
resolution: null
blocked_reason: null
blocked: false
id: WI-PROMPT-CLI-CLOSEOUT
title: Implement lrh prompt update-execution CLI command (Phase 2)
type: deliverable
status: proposed
owner: anthony
contributors:
  - anthony
assigned_agents: []
related_focus: []
related_roadmap: []
related_workstreams:
  - WS-SKILLS-CLOSEOUT
related_design:
  - project/design/proposals/adopted/lrh-closeout/00_proposal.md
  - project/design/proposals/adopted/lrh-project-local-skills/00_proposal.md
depends_on:
  - WI-SKILLS-LRH-CLOSEOUT
blocked_by: []
expected_actions:
  - create_file
  - edit_file
  - create_pr
forbidden_actions:
  - force_push
  - delete_branch
  - merge_pr
acceptance: []
required_evidence:
  - lrh_validate
artifacts_expected: []
---

## Summary

Implement `lrh prompt update-execution` — the CLI subcommand specified in
PROP-LRH-CLOSEOUT Decision 3 — and upgrade `/lrh-closeout` Step 5 from
edit-in-place to call this command. This is Phase 2 of `WS-SKILLS-CLOSEOUT`;
Phase 1 (`WI-SKILLS-LRH-CLOSEOUT`) has already landed.

## Problem / Context

Phase 1 (`WI-SKILLS-LRH-CLOSEOUT`) implemented `/lrh-closeout` with edit-in-place
execution record updates. PROP-LRH-CLOSEOUT Decision 3 specifies that record
mutation should instead be performed by a CLI subcommand (`lrh prompt update-execution`)
so the operation is atomic, validatable, and auditable. Phase 2 implements that
command and upgrades Step 5 to call it.

The CLI interface is fully specified in Decision 3:
```bash
lrh prompt update-execution \
  --execution-id <ID> \
  --status landed \
  --pr <URL> \
  --commit <SHA> \
  --session-transcript <ID-or-pending>
```

Validations required: record must exist; `in_progress → landed` is the only
valid forward transition; `--commit` required when `--status landed`.

## Scope

- Add `update-execution` subparser to `run_prompt_cli()` in `src/lrh/prompt_workflow.py`
- Find execution record by scanning `project/executions/**/*.md` for matching `execution_id:` field
- Validate status transition (`in_progress → landed`) and required `--commit`
- Update 4 frontmatter fields in-place: `status`, `pr`, `commit`, `session_transcript`
  (insert `session_transcript:` after `commit:` if absent)
- Add tests to `tests/cli_tests/prompt_test.py` following the subprocess pattern
- Update `src/lrh/skills/lrh-closeout/SKILL.md` Step 5 to call the CLI
- Update `src/lrh/skills/lrh-implement/references/execution-session-reference.md`
  with `update-execution` command syntax
- Mirror all skill changes to `.claude/skills/lrh-closeout/`

## Out of Scope

- Does not implement `lrh closeout` as a top-level command (per PROP-LRH-CLOSEOUT
  Decision 3 — the skill is the interface; CLI is scoped to record mutation only)
- Does not change the skill's external step structure or add/remove steps
- Does not change validation (`lrh validate`) or WI/WS/proposal closeout logic
- Does not implement reverse transitions (e.g., `landed → in_progress`)

## Required Changes

1. **`src/lrh/prompt_workflow.py`** — add `update-execution` subparser and handler
2. **`tests/cli_tests/prompt_test.py`** — add tests for `update-execution`
3. **`src/lrh/skills/lrh-closeout/SKILL.md`** — update Step 5 to call `lrh prompt update-execution`; update "What This Skill Does Not Do" to remove Phase 1 caveat; update description frontmatter
4. **`.claude/skills/lrh-closeout/SKILL.md`** — mirror of item 3
5. **`src/lrh/skills/lrh-implement/references/execution-session-reference.md`** — add `update-execution` command section

## Likely Files

- `src/lrh/prompt_workflow.py` (primary implementation)
- `tests/cli_tests/prompt_test.py` (tests)
- `src/lrh/skills/lrh-closeout/SKILL.md` (skill update)
- `.claude/skills/lrh-closeout/SKILL.md` (mirror)
- `src/lrh/skills/lrh-implement/references/execution-session-reference.md` (reference update)

## Non-Goals

- Does not implement `lrh closeout` as a top-level command (per PROP-LRH-CLOSEOUT
  Decision 3 — the skill is the interface; CLI is scoped to record mutation only)
- Does not change the skill's external step structure or reference files

## Acceptance Criteria

- `lrh prompt update-execution --execution-id <id> --status landed --pr <url> --commit <sha> --session-transcript <value>` runs without error on a valid `in_progress` record and transitions it to `landed`
- Running the command on a record with no `session_transcript:` field inserts the field after `commit:`
- Running the command with `--status landed` and no `--commit` exits with an error
- Running the command with an unknown `--execution-id` exits with a non-zero code
- All new tests pass (`scripts/test` or equivalent)
- `src/lrh/skills/lrh-closeout/SKILL.md` Step 5 uses `lrh prompt update-execution` instead of edit-in-place instructions
- `diff -r src/lrh/skills/lrh-closeout/ .claude/skills/lrh-closeout/` — no diff
- `lrh validate` — 0 errors, 0 warnings

## Validation

- `lrh validate`
- `diff -r src/lrh/skills/lrh-closeout/ .claude/skills/lrh-closeout/`
- `scripts/version tools` / `scripts/test` if Python changes involved
