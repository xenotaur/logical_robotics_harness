---
execution_id: 2026_09_27_18_05_51_WI_SKILLS_REFERENCE_PORTABILITY
prompt_id: PROMPT(WI-SKILLS-REFERENCE-PORTABILITY:WI_SKILLS_REFERENCE_PORTABILITY)[2026-09-27T16:55:48+00:00]
work_item: WI-SKILLS-REFERENCE-PORTABILITY
status: in_progress
rerun_of: 
pr: https://github.com/xenotaur/logical_robotics_harness/pull/749
commit: 8d6e706b
created_at: 2026-09-27T18:05:51+00:00
agent: codex_app
instruction_source: project/work_items/proposed/WI-SKILLS-REFERENCE-PORTABILITY.md
session_transcript: pending
---

# Summary

Implement WI-SKILLS-REFERENCE-PORTABILITY so LRH skills remain operational in
independent client repositories that do not contain LRH's maintainer-owned
`docs/` tree.

# Result

Updated the canonical `lrh-codex-export`, `lrh-codex-session`,
`lrh-config-skills`, and `lrh-doc-audit` guidance to treat LRH documentation
as optional, use installed CLI help or explicit capability checks as
operational authority, and resolve bundled references relative to the skill.
Synchronized Claude, Codex, and Antigravity rendered targets, including the
bundled audit requirements reference. Added a synthetic third-party fixture
with `project/` but no general `docs/` tree and regression coverage that
installs the Codex target and runs metadata-only CLI help from that fixture.

The implementation was independently reviewed in a cold-context diff review.
The first review found that the initial fixture test only checked wording;
that finding was independently verified, the test was strengthened, and a
fresh final review found no further issues.

# Validation

- Toolchain: Black 26.3.1 and Ruff 0.15.12 selected via the pinned Anaconda
  environment; Pyright is unavailable.
- `scripts/format --check --diff`: 264 files unchanged.
- `scripts/lint`: passed, including test-framework guardrails.
- `scripts/test --log`: 1,812 tests passed.
- `lrh validate`: 0 errors, 0 warnings.
- `python -m unittest tests.packaging_tests.skills_reference_portability_test`:
  6 tests passed.
- `git diff --check`: passed.
- The four affected skills report up to date for their maintained targets.
  Aggregate Codex/Antigravity status reports unrelated pre-existing drift.

# Follow-up

Address any review findings with `/lrh-review-response`, then run
`/lrh-confirm-fixes` before merge. After merge, run `/lrh-closeout` to land
this execution record and resolve the work item.
