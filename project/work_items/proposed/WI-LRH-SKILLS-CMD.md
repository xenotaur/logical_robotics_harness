---
resolution: null
blocked_reason: null
blocked: false
id: WI-LRH-SKILLS-CMD
title: Rename lrh setup to lrh skills install and add --local flag
type: deliverable
status: proposed
owner: anthony
contributors:
  - anthony
assigned_agents: []
related_focus: []
related_roadmap: []
related_workstreams: []
related_design:
  - project/design/proposals/adopted/lrh-project-local-skills/00_proposal.md
depends_on: []
blocked_by: []
expected_actions:
  - edit_file
  - create_pr
forbidden_actions:
  - force_push
  - delete_branch
  - add_deprecation_alias
  - implement_lrh_skills_list
  - implement_package_flag
  - modify_archival_records
acceptance:
  - lrh skills install copies all skills to ~/.claude/skills/ idempotently
  - lrh skills install --local copies to ./.claude/skills/ instead
  - lrh skills install --dry-run prints report without writing files
  - lrh skills install --force overwrites user-modified skills without prompting
  - lrh setup does not exist as a command or alias
  - scripts/test passes with 0 failures
  - lrh validate reports 0 errors
required_evidence:
  - manual_review
  - lrh_validate
  - test_output
artifacts_expected:
  - src/lrh/cli/main.py (edited — lrh skills install subcommand replaces lrh setup)
  - tests/cli_tests/skills_test.py (renamed from setup_test.py via git mv; updated test strings)
  - CONTRIBUTING.md (lrh setup references updated)
  - src/lrh/skills/lrh-create-skill/SKILL.md (updated)
  - src/lrh/skills/lrh-implement/references/lrh-implement-workflow.md (updated)
  - src/lrh/skills/lrh-review-response/SKILL.md (updated)
  - src/lrh/skills/lrh-work-item/references/work-item-body-guide.md (updated)
---

## Summary

Rename the `lrh setup` CLI subcommand to `lrh skills install` and add a
`--local` flag that installs skills to `./.claude/skills/` instead of
`~/.claude/skills/`.

## Problem / Context

`lrh setup` is semantically misleading: it sounds like a project-bootstrap
command (analogous to `make setup` or `lrh project init`), but it manages
skill installation — a distinct concern that belongs under a `skills`
subcommand family for discoverability and extensibility. The non-goals in
`WI-SKILLS-LRH-SETUP` explicitly deferred a `lrh skills` top-level subcommand
group to Stage 3; this is that work.

Additionally, `installer.py` already accepts a `skills_dir` parameter that
the CLI does not expose. Adding `--local` is a one-flag CLI change that
enables project-scoped skill installation without any library modification.

There are no external users of `lrh setup` (pre-1.0, single developer), so
no deprecation alias is needed.

## Scope

- Rename `lrh setup` → `lrh skills install` in `src/lrh/cli/main.py`
- Add `--local` flag: write to `./.claude/skills/` instead of `~/.claude/skills/`
- Rename `tests/cli_tests/setup_test.py` → `tests/cli_tests/skills_test.py`
  via `git mv` and update test strings; add a test for `--local`
- Update all Category A references to `lrh setup` in `CONTRIBUTING.md` and
  the four `src/lrh/skills/` files identified above

## Required Changes

1. Edit `src/lrh/cli/main.py`:
   - Replace the `setup` top-level subparser with a `skills` subparser
     containing an `install` sub-subparser (mirroring `lrh project {init,doctor}`)
   - Carry `--dry-run` and `--force` to `lrh skills install`
   - Add `--local`: when set, pass `Path.cwd() / ".claude" / "skills"` as
     `skills_dir`; otherwise pass `None` (uses existing `~/.claude/skills/` default)
   - Remove `setup` entirely — no alias

2. `git mv tests/cli_tests/setup_test.py tests/cli_tests/skills_test.py`:
   - Update all test strings `"lrh setup"` → `"lrh skills install"`
   - Add a test for `--local` (installs to a temp CWD-relative subdirectory)

3. Edit `CONTRIBUTING.md`:
   - Replace `lrh setup` → `lrh skills install`
   - Remove the stale `(WI-SKILLS-LRH-SETUP)` parenthetical

4. Edit the four `src/lrh/skills/` files that reference `lrh setup`:
   - `lrh-create-skill/SKILL.md` — fix stale "not yet implemented" note
   - `lrh-implement/references/lrh-implement-workflow.md` — fix stale "future" note
   - `lrh-review-response/SKILL.md` — update non-goal reference
   - `lrh-work-item/references/work-item-body-guide.md` — update example

## Non-Goals

- Do not add a deprecation alias for `lrh setup` — clean rename, no external users.
- Do not implement `lrh skills list` — natural follow-on, not required here.
- Do not add `--package <name>` — installing from other packages is future work.
- Do not touch archival records (`project/design/proposals/adopted/`,
  `project/work_items/resolved/`, `project/workstreams/resolved/`,
  `project/executions/`) — they correctly document history under the name `lrh setup`.

## Acceptance Criteria

- `lrh skills install` copies all skills to `~/.claude/skills/` idempotently.
- `lrh skills install --local` copies to `./.claude/skills/` instead.
- `lrh skills install --dry-run` prints the expected report without writing files.
- `lrh skills install --force` overwrites user-modified skills without prompting.
- `lrh setup` returns an unrecognized-command error — no alias exists.
- `scripts/test` passes with 0 failures.
- `lrh validate` reports 0 errors.

## Validation

- `scripts/version tools`
- `scripts/format --check --diff`
- `scripts/lint`
- `scripts/test`
- `lrh validate`
- `lrh skills install --dry-run` (manual smoke test)
- `lrh setup` (should fail — confirms alias removed)

## Risk Notes

- The renamed test file breaks `git log` continuity unless `git mv` is used;
  do not delete-and-recreate.
- Skills installed to `~/.claude/skills/` will still reference `lrh setup`
  until the user re-runs `lrh skills install` after upgrading. Expected and
  acceptable — installed skills are a snapshot.
