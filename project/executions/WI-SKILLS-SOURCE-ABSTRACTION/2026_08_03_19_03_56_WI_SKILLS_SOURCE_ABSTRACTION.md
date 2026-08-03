---
execution_id: 2026_08_03_19_03_56_WI_SKILLS_SOURCE_ABSTRACTION
prompt_id: PROMPT(WI-SKILLS-SOURCE-ABSTRACTION:WI_SKILLS_SOURCE_ABSTRACTION)[2026-08-03T18:47:00+00:00]
work_item: WI-SKILLS-SOURCE-ABSTRACTION
status: landed
rerun_of:
pr: https://github.com/xenotaur/logical_robotics_harness/pull/477
commit: d05b9ccc2593ac29ced343d559b25a2be2f21436
agent: codex_app
instruction_source: project/work_items/proposed/WI-SKILLS-SOURCE-ABSTRACTION.md
session_transcript: codex-app:current-task
created_at: 2026-08-03T19:03:56+00:00
---

# Summary

Implemented the source abstraction slice for `lrh skills install` so LRH can select the canonical skill tree from the packaged distribution, the current repository checkout, or an explicit filesystem path.

# Result

- Added a `SkillSource` abstraction and `SkillSourceKind` selection for `lrh-package`, `current-repo`, and explicit path sources.
- Preserved existing package-backed installer behavior as the default for install, diff, and named-skill installation.
- Added `--source` plumbing to `lrh skills install`, including `--diff` support for non-package sources.
- Rejected symlinked filesystem source content before comparing, diffing, or copying source skill files.
- Added unit and CLI coverage for source resolution, explicit-path installs, current-repo installs, invalid sources, local-modification safety, and symlink rejection.
- Updated the skill update how-to so overwrite and diff language refers to the selected source rather than only the packaged source.
- Opened PR https://github.com/xenotaur/logical_robotics_harness/pull/477.

# Validation

- `conda run -n LRH python -m unittest tests.skills_installer_test tests.cli_tests.skills_test` — 65 tests passed.
- `conda run -n LRH scripts/format --check --diff` — passed; 185 files would be left unchanged.
- `conda run -n LRH scripts/lint` — Ruff and Black checks passed.
- `conda run -n LRH lrh validate` — 0 errors, 0 warnings.
- `conda run -n LRH scripts/test` — 905 tests passed plus smoke checks.
- `git diff --check` — clean.
- Fresh independent Codex self-review found one real symlink-source safety issue and one documentation wording gap; both were fixed before PR creation. Follow-up independent review confirmed diff scope and symlink handling, and requested additional `diff_skill`/existing-install comparison coverage, which was added.

# Follow-up

- Continue the `/lrh-execute` landing phase for PR 477 after automatic PR review and CI have reported.
