---
id: WI-SKILLS-OPENAI-POLICY-NULL-FAILSAFE
title: 'Fail safe on a blank policy in agents/openai.yaml (PR #810 follow-up)'
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
related_workstreams: []
related_design:
  - project/design/proposals/adopted/lrh-skills-target-aware-install/00_proposal.md
depends_on:
  - WI-SKILLS-CHATGPT-EXPORT-HARDENING
blocked_by: []
expected_actions:
  - edit_file
  - run_tests
  - write_docs
  - create_pr
forbidden_actions:
  - force_push
  - delete_branch
  - change_canonical_skill_sources
  - change_codex_renderer_output
acceptance:
  - 'A present-but-null policy key in agents/openai.yaml (for example a bare "policy:" line, "policy: ~", or "policy:" whose only child line is commented out) fails lrh skills export validation with an error that says how to fix it, while an absent policy key or an empty mapping ("policy: {}") still means no policy'
  - 'lrh skills check and lrh skills status report a present-but-null policy, and a present policy.allow_implicit_invocation that is not true or false, as invalid_codex_metadata issues'
  - 'The canonical export result is unchanged from origin/main at implementation time (20 exported and 6 manual-only skipped when this item was written), and no canonical skill gains a new check issue'
  - 'scripts/format --check --diff, scripts/lint, scripts/test, and lrh validate complete successfully'
required_evidence:
  - lrh_validate
  - test_output
  - validation_output
artifacts_expected:
  - src/lrh/skills/exporter.py
  - src/lrh/skills/installer.py
  - tests/skills_exporter_test.py
  - tests/skills_installer_test.py
  - docs/reference/cli/skills.md
---

## Summary

Close the last null-value gap in manual-only detection. PR #810
(`WI-SKILLS-CHATGPT-EXPORT-HARDENING`) made a blank
`policy.allow_implicit_invocation:` fail `lrh skills export` instead of
reading as "no marker". A blank `policy:` one level up still reads as "no
policy", so a manual-only skill whose only marker lives in
`agents/openai.yaml` can silently become auto-selectable in a ChatGPT bundle.
Make a present-but-null `policy` fail export validation, and make
`lrh skills check` and `status` report the same malformed values the
exporter rejects.

## Problem / Context

`_codex_manual_only` in `src/lrh/skills/exporter.py` reads
`loaded.get("policy")`:

- a non-mapping value fails the skill;
- `None` returns "not manual-only".

YAML parses all of these as `None`:

- `policy:`
- `policy: ~`
- `policy:` followed only by a commented-out child line

**Why it matters.** On origin/main (2026-10-11), five canonical skills are
manual-only **only** through `agents/openai.yaml`
(`policy.allow_implicit_invocation: false`, with no `disable-model-invocation`
in `SKILL.md`):

- `lrh-land`
- `lrh-execute`
- `lrh-confirm-fixes`
- `lrh-self-review`
- `lrh-codex-export`

Reproduced against origin/main: replacing `lrh-land`'s or `lrh-codex-export`'s
`openai.yaml` with a bare `policy:` makes the default `lrh skills export`
bundle the skill with no error. It also emits no manual-only notice. These are
exactly the skills the manual-only rule exists to keep out of automatic
ChatGPT selection.

**Codex install has a related reporting gap.**

- For a skill without `disable-model-invocation: true`, `CodexSkillRenderer`
  copies `agents/openai.yaml` verbatim.
- `_compatibility_issues` in `src/lrh/skills/installer.py` flags a non-mapping
  `policy`, but lets `None` through.
- It never checks the type of `allow_implicit_invocation`.

So `lrh skills check --target codex` stays silent about the same malformed
values export now rejects (verified: a blank `policy:` installs verbatim and
`check` reports no Codex-metadata issue for it).

`_render_openai_yaml` already turns a null `policy` into
`{allow_implicit_invocation: false}` for skills with
`disable-model-invocation: true`. That is the fail-safe direction, and it stays
as is.

**Prior art check.**

- **Duplication: none found.** The only related code is the two functions
  above, which this item tightens. No existing work item, proposal, or
  backlog entry covers a null `policy`.
  `WI-EXPORT-SKILL-FAMILY-RENAME` may reduce an old skill's
  `agents/openai.yaml` "to the same stub". This item makes a blank stub fail
  loudly rather than silently change invocation policy.
- **Demand: found.** Deferred follow-up 1 in
  `project/executions/AD_HOC/2026_10_11_01_25_43_WI_SKILLS_CHATGPT_EXPORT_HARDENING_IMPL_CLOSEOUT_NOTE.md`
  (PR #810 closeout) requests exactly this. Link that record from the
  implementation PR.

## Scope

- `exporter.py`: a present-but-null `policy` key fails export validation.
- `installer.py` `_compatibility_issues`:
  - report a present-but-null `policy` as `invalid_codex_metadata`;
  - report a present `allow_implicit_invocation` that is not a boolean the
    same way.
- Regression tests for each case, including that absent keys and
  `policy: {}` still pass.
- A reference-doc update.

## Required Changes

1. In `src/lrh/skills/exporter.py`, `_codex_manual_only`:
   - when the loaded mapping contains a `policy` key whose value is not a
     mapping (including `None`), append an error such as "policy in
     agents/openai.yaml must be a mapping; remove the key to declare no
     policy" and fail the skill;
   - an absent `policy` key, or `policy: {}`, still means "no policy";
   - keep the existing order: both markers are validated before they are
     combined.
2. In `src/lrh/skills/installer.py`, `_compatibility_issues`:
   - report a present-but-null `policy` as an `invalid_codex_metadata` issue;
   - report a present `policy.allow_implicit_invocation` that is not `true`
     or `false` the same way, matching the exporter's rule;
   - do not change `CodexSkillRenderer` output or install's write behavior.
3. Tests:
   - `tests/skills_exporter_test.py`:
     - each null form (`policy:`, `policy: ~`, commented-out child) fails;
     - a skill that also has `disable-model-invocation: true` still fails;
     - absent `policy` and `policy: {}` export normally.
   - `tests/skills_installer_test.py`:
     - `inspect_skills` reports `invalid_codex_metadata` for a null `policy`
       and for a non-boolean `allow_implicit_invocation`;
     - valid canonical-style metadata reports no issue.
4. `docs/reference/cli/skills.md`: in the export validation list and the
   `check` description, state that a present `policy` must be a mapping, and
   that a blank one fails rather than meaning "no policy".

## Non-Goals

- Do not change any canonical `agents/openai.yaml` or `SKILL.md`.
- Do not change `CodexSkillRenderer` rendering, or make `lrh skills install`
  refuse to write. Install keeps its current behavior; `check` and `status`
  report the issue.
- Do not add `disable-model-invocation` to the five openai.yaml-only skills.
  That is a separate design choice about redundant markers.
- Do not address the `## When to use` placement edge cases (tracked in
  `project/design/backlog.md`).

## Acceptance Criteria

- A present-but-null `policy` (`policy:`, `policy: ~`, or a commented-out
  child) fails `lrh skills export` validation with a fix hint. An absent
  `policy` key or `policy: {}` does not fail.
- `lrh skills check` and `status` report a present-but-null `policy`, and a
  non-boolean `policy.allow_implicit_invocation`, as `invalid_codex_metadata`.
- The canonical export result is unchanged from origin/main at implementation
  time (20 exported and 6 manual-only skipped when written), and no canonical
  skill gains a check issue.
- `scripts/format --check --diff`, `scripts/lint`, `scripts/test`, and
  `lrh validate` complete successfully.

## Validation

- `scripts/version tools`
- `scripts/format --check --diff`
- `scripts/lint`
- `scripts/test`
- `lrh validate`
- `lrh skills export --target chatgpt --source current-repo --out <temporary-directory>`
- `lrh skills check --target codex --source current-repo --local`

## Risk Notes

- **Codex's own reading of a null `policy` is not verified here.** Codex
  probably treats it as "no policy" (implicit invocation allowed). That is
  exactly why a null value should be surfaced rather than trusted.
- **Third-party skill sources** with a deliberately empty `policy:` will now
  fail export and get a `check` issue. The fix hint (remove the key) makes
  this a one-line change for them.
- **Canonical counts drift.** The 20/6 export figures were measured on
  2026-10-11 and will change as skills are added. Compare against
  origin/main at implementation time, not these literal numbers.
