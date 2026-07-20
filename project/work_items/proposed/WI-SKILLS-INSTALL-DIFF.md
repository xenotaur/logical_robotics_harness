---
resolution: null
blocked_reason: null
blocked: false
id: WI-SKILLS-INSTALL-DIFF
title: Add --diff flag to lrh skills install
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
  - add_cli_command
  - create_pr
forbidden_actions:
  - force_push
  - delete_branch
  - implement_skills_diff_subcommand
  - add_external_diff_dependency
acceptance:
  - lrh skills install --diff prints a unified diff for each user-modified skill's differing files
  - added/removed files (present in the package but not on disk, or vice versa) are reported distinctly from content diffs
  - files that fail UTF-8 decoding are reported as "binary files differ" instead of raising
  - --diff has no effect on skills with status installed, up_to_date, or forced
  - new unit tests in tests/skills_installer_test.py cover a modified text file, an added file, a removed file, and a binary file
  - scripts/test passes with 0 failures
  - lrh validate reports 0 errors
required_evidence:
  - manual_review
  - lrh_validate
  - test_output
artifacts_expected:
  - src/lrh/skills/installer.py (edited — per-file diff computation)
  - src/lrh/cli/main.py (edited — --diff flag on skills install)
  - tests/skills_installer_test.py (edited — diff coverage)
---

## Summary

Add a `--diff` flag to `lrh skills install` that prints a unified diff of
what changed, per file, for every skill flagged as user-modified.

## Problem / Context

`lrh skills install` currently reports "has local modifications — skipped"
for a modified skill but gives no way to see what changed short of manually
diffing the installed copy against the package source. `_skill_differs_from_package`
already computes a full-tree byte comparison (`src/lrh/skills/installer.py:66-70`)
but discards which files or bytes differ, returning only a bool. Users have
to reconstruct the diff by hand before deciding whether `--force` is safe.

A prior design discussion (this session) compared four approaches: a
`difflib`-based `--diff` flag (pure stdlib), shelling out to `diff`/`git diff
--no-index`, a separate `lrh skills diff <name>` subcommand, and always-on
diff printing. The `difflib` flag was chosen because it avoids introducing an
external-binary dependency — this project already has a documented PATH
fragility issue with external binaries (bare `lrh` isn't on PATH in the dev
environment) — and it fits the existing in-process `unittest` test style in
`tests/skills_installer_test.py` without needing subprocess mocking.

### Duplication search
- In-repo: No existing diff-rendering implementation found. Related file:
  `src/lrh/skills/installer.py` (the function being extended).
- Sibling repos: None identified.
- External libraries: Python stdlib `difflib` — no external library needed;
  this is the chosen approach.
- Recommendation: Proceed.

### Demand search
- Work items: None found.
- Proposals: None found.
- Backlog: No matching entries.
- Recommendation: No action.

## Scope

- Extend `installer.py` to compute per-file diffs (added/removed/changed)
  between the package skill tree and the installed skill tree
- Add a `--diff` flag to `lrh skills install` that prints those diffs for
  each `USER_MODIFIED` skill
- Add unit test coverage for the new diff logic

## Required Changes

1. Extend `src/lrh/skills/installer.py`:
   - Add a function that, given a skill name and skills dir, returns the set
     of differing relative file paths (added / removed / changed) using the
     `pkg_files`/`fs_files` dicts already built by `_collect_pkg_files` /
     `_collect_fs_files`.
   - For changed text files, produce a `difflib.unified_diff` between the
     package bytes and filesystem bytes (decoded as UTF-8).
   - For files that fail UTF-8 decoding, report "binary files differ"
     instead of raising.
   - For files present on only one side, report them as added/removed
     rather than attempting a content diff.
2. Add `--diff` to `skills_install_parser` in `src/lrh/cli/main.py`
   (alongside `--dry-run`, `--force`, `--local` at `main.py:142-156`), and
   wire it through to print the diff output for each `USER_MODIFIED` result
   after `format_report`'s existing warning line.
3. Add tests to `tests/skills_installer_test.py` covering: a modified text
   file, an added file, a removed file, and a binary-content file, following
   the existing `unittest` + tmpdir style already in that file.

## Non-Goals

- Do not implement a separate `lrh skills diff <name>` subcommand — the
  `--diff` flag on `install` is the chosen shape.
- Do not shell out to `diff` or `git diff --no-index` — avoids an external
  binary/PATH dependency.
- Do not change `--force` overwrite behavior.
- Do not make diff output print automatically without the flag — keep the
  default report terse.

## Acceptance Criteria

- `lrh skills install --diff` prints a unified diff for each user-modified
  skill's differing files.
- Added/removed files are reported distinctly from content diffs.
- Files that fail UTF-8 decoding are reported as "binary files differ"
  instead of raising an exception.
- `--diff` has no visible effect on skills with status `installed`,
  `up_to_date`, or `forced`.
- New unit tests cover a modified text file, an added file, a removed file,
  and a binary file.
- `scripts/test` passes with 0 failures.
- `lrh validate` reports 0 errors.

## Validation

- `scripts/version tools`
- `scripts/format --check --diff`
- `scripts/lint`
- `scripts/test`
- `lrh validate`
- `lrh skills install --diff --local` (manual smoke test against a locally modified skill)

## Risk Notes

- Decoding assumptions: skill content is expected to be text (Markdown,
  Python); a skill that legitimately ships binary assets must fall back to
  "binary files differ" rather than crashing the install command.
- Large diffs on heavily modified skills could produce noisy terminal
  output — no truncation is planned in this item; a future item could add
  a `--diff-stat`-style summary if this becomes a problem.
