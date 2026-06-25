---
resolution: null
blocked_reason: null
blocked: false
id: WI-SKILLS-LRH-SETUP
title: Implement lrh setup command to install skills globally
type: deliverable
status: proposed
owner: anthony
contributors:
  - anthony
assigned_agents: []
related_focus: []
related_roadmap: []
related_workstreams:
  - WS-SKILLS
related_design:
  - project/design/proposals/adopted/lrh-project-local-skills/00_proposal.md
depends_on:
  - WI-SKILLS-CREATE-SKILL
blocked_by: []
expected_actions:
  - create_file
  - edit_file
  - create_pr
forbidden_actions:
  - force_push
  - delete_branch
  - implement_upgrade_awareness
  - implement_lrh_skills_subcommand
  - implement_setup_project_flag
  - auto_install_during_bootstrap
acceptance:
  - lrh setup copies all skills from src/lrh/skills/ to ~/.claude/skills/ idempotently
  - lrh setup --dry-run prints what would be installed without writing any files
  - lrh setup --force overwrites user-modified skills without prompting
  - User-modified skills (differ from package version) are skipped with a warning by default
  - lrh setup prints a restart reminder when ~/.claude/skills/ is newly created
  - scripts/test passes with 0 failures
  - lrh validate reports 0 errors
required_evidence:
  - manual_review
  - lrh_validate
  - test_output
artifacts_expected:
  - src/lrh/skills/installer.py
  - src/lrh/cli/main.py (edited — lrh setup subcommand wired in)
  - tests/test_skills_installer.py
---

## Summary

Implement `lrh setup` (Stage 2 of `WS-SKILLS`): a CLI command that copies all
skills from the installed `lrh` package (`src/lrh/skills/`) to
`~/.claude/skills/`, making them globally available in any Claude Code project
on the machine without manual copying.

## Problem / Context

LRH skills (`/lrh-work-item`, `/lrh-implement`, etc.) are currently available
only inside the LRH repository session, where Claude Code auto-discovers
`.claude/skills/`. Users working in other projects must manually copy skill
directories to either that project's `.claude/skills/` or the global
`~/.claude/skills/`. There is no standard, idempotent installation path.

`PROP-LRH-PROJECT-LOCAL-SKILLS` (adopted, in
`project/design/proposals/adopted/lrh-project-local-skills/00_proposal.md`)
designates `lrh setup` as the per-machine installer. The `lrh.skills`
package-data declaration (`pyproject.toml`) is already in place from
`WI-SKILLS-CREATE-SKILL`. This item delivers the CLI command.

## Scope

- Implement the core copy logic in `src/lrh/skills/installer.py` using
  `importlib.resources` to locate skills in the installed package
- Wire `lrh setup` into `src/lrh/cli/main.py` as a new top-level subcommand
- Cover idempotent copy, `--dry-run`, `--force`, skip-with-warning for
  user-modified skills, and restart reminder for newly created `~/.claude/skills/`
- Add tests verifying all four behaviors

## Required Changes

1. Create `src/lrh/skills/installer.py` — core installation logic:
   - Locate skills via `importlib.resources` from the `lrh.skills` package
   - For each skill: compare with `~/.claude/skills/<name>/` (if it exists)
   - If identical or absent: copy/update and report `installed` or `up to date`
   - If modified (differs from package): skip with warning, unless `--force`
   - Accept `dry_run: bool` and `force: bool` parameters

2. Edit `src/lrh/cli/main.py` — add `lrh setup` subcommand:
   - `lrh setup` — install or update LRH skills globally
   - `lrh setup --dry-run` — show what would be installed without writing
   - `lrh setup --force` — overwrite even user-modified skills
   - Prints restart reminder if `~/.claude/skills/` is newly created by the run
   - Import from `lrh.skills.installer`

3. Create `tests/test_skills_installer.py` — unit tests:
   - Install into a tmp directory (monkeypatch `~/.claude/skills/`)
   - Verify idempotency (second run produces "up to date")
   - Verify `--dry-run` writes nothing
   - Verify `--force` overwrites a user-modified skill
   - Verify skip-with-warning on user-modified skill without `--force`

## Non-Goals

- Do not implement Stage 3 upgrade awareness (`lrh skills status`, diff-and-ask
  on conflict, installed-version tracking) — that is `WI-SKILLS-UPGRADE-AWARENESS`.
- Do not add a `lrh skills` top-level subcommand group — deferred to Stage 3.
- Do not implement `lrh setup --project` (add `CLAUDE.md` entry to current
  project) — deferred to `WI-SKILLS-PROJECT-INTEGRATION`.
- Do not auto-invoke `lrh setup` during `lrh request bootstrap_project`.
- Do not modify `pyproject.toml` — `lrh.skills` package data is already declared.

## Acceptance Criteria

- `lrh setup` (no flags) copies all skills from the installed package to
  `~/.claude/skills/`, reporting `installed`, `up to date`, or `warning` for
  each skill.
- Running `lrh setup` twice in sequence produces `up to date` for all skills
  on the second run with no file writes.
- `lrh setup --dry-run` prints the same report without creating or modifying
  any files.
- `lrh setup --force` overwrites a locally-modified `~/.claude/skills/<name>/`
  without warning.
- A user-modified skill (any file differing from the package version) is
  skipped with a warning message by default.
- `lrh setup` prints a restart reminder when `~/.claude/skills/` did not exist
  before the run.
- `scripts/test` passes with 0 failures.
- `lrh validate` reports 0 errors.

## Validation

- `scripts/version tools`
- `scripts/format --check --diff`
- `scripts/lint`
- `scripts/test`
- `lrh validate`
- `lrh setup --dry-run` (manual smoke test in a shell)

## Risk Notes

- `importlib.resources` API for traversing package sub-trees changed between
  Python 3.8 and 3.9. Use `importlib.resources.files()` (3.9+) or the
  `importlib_resources` backport. Confirm the project's minimum Python version
  before choosing the API.
- `~/.claude/skills/` is a user-global directory; tests must not write to the
  real path. Use a tmp directory and monkeypatch.
