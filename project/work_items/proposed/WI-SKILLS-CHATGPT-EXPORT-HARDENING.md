---
resolution: null
blocked_reason: null
blocked: false
id: WI-SKILLS-CHATGPT-EXPORT-HARDENING
title: 'Harden lrh skills export validation and skill-source discovery (PR #747 follow-ups)'
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
  - project/design/proposals/adopted/lrh-skills-target-aware-install/00_proposal.md
depends_on:
  - WI-SKILLS-CHATGPT-EXPORT
blocked_by: []
expected_actions:
  - edit_file
  - run_tests
  - write_docs
  - create_pr
forbidden_actions:
  - force_push
  - delete_branch
  - implement_openai_api_skill_sync
  - implement_openai_plugin_distribution
acceptance:
  - 'A blank (YAML null) disable-model-invocation or policy.allow_implicit_invocation value fails the skill instead of being treated as absent, while an absent key does not fail'
  - 'An empty or whitespace-only compatibility value fails validation (a non-blank string of at most 500 characters when present)'
  - 'Hidden (dot-prefixed) top-level directories in a skill source are skipped by SkillSource.skill_names(), so lrh skills install, status, check, and export never treat them as skills, while a hidden symlink still raises as all symlinks do'
  - 'Hosted export never silently loses when_to_use: it is folded into the bundled description (single-space separator) when the combined text is at most 1024 characters, and otherwise added as a generated "## When to use" section at the top of the bundled SKILL.md body with a notice; a folded or sectioned when_to_use is not reported as stripped'
  - 'The canonical export still exports the same 20 skills and skips the same 5 manual-only skills'
  - 'Exporter tests assert the specific error for each malformed optional field and that license survives into the bundle'
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
  - docs/how-to/use-lrh-with-agent-assistants.md
---

## Summary

Close out the non-blocking P3 findings deferred from PR #747's review rounds
(`WI-SKILLS-CHATGPT-EXPORT`), recorded in
`project/executions/AD_HOC/2026_09_28_16_05_19_WI_SKILLS_CHATGPT_EXPORT_IMPL_CLOSEOUT_NOTE.md`:

- tighten two fail-safe gaps in `lrh skills export` validation;
- stop hidden directories in a skill source from being treated as skills by
  every `lrh skills` subcommand;
- restore invocation guidance lost when `when_to_use` is dropped for hosted
  targets;
- make two exporter tests assert what they claim.

## Problem / Context

PR #747 landed `lrh skills export --target chatgpt`. Its substitute
self-review rounds reported findings that were all "safe to merge" P3s.
Under the run's agreed P3 policy, one fix round was applied and these were
deferred:

1. **Blank manual-only markers.** `disable-model-invocation:` or
   `allow_implicit_invocation:` with no value loads as YAML null and is
   treated as absent. A manual-only intent written that way exports as
   automatically selectable. Quoted strings already fail (PR #747), so null
   is the remaining fail-safe gap, and it contradicts the reference doc's
   "must be booleans" wording.
2. **Empty `compatibility`.** `compatibility: ''` is accepted. The Agent
   Skills spec is believed to require 1–500 characters when the field is
   present; confirm this during implementation.
3. **Hidden directories in a skill source.** `SkillSource.skill_names()`
   (`src/lrh/skills/installer.py`) skips only `_`-prefixed top-level
   entries, so dot-directories (`.git/`, `.vscode/`, `.idea/`,
   `.pytest_cache/`) are treated as skills. Verified on `main` (`ae123356`)
   with a source containing `demo-skill/` and `.git/`:
   - `skill_names()` returns `['.git', 'demo-skill']`;
   - `install_skills` installs `.git` into the target skills directory;
   - `inspect_skills` (status/check) reports `.git: up_to_date`;
   - `export_skills` fails `.git` with "missing SKILL.md", and because
     export writes all-or-nothing, nothing is written.

   This does not happen with `lrh-package` or `current-repo` sources. It
   does happen with `--source <path>` when that path is its own git clone or
   holds editor/tool directories; with a real `.git/`, install would copy
   the entire object store into the user's skills directory.
4. **Dropped `when_to_use`.** The ChatGPT renderer drops `when_to_use`, as
   the Codex renderer does. ChatGPT selects uploaded skills automatically
   and has no known explicit-only control, so guards such as
   `lrh-export-claude`'s "Do not invoke proactively" are lost exactly where
   automatic selection happens. Folding it into `description` alone is not
   enough: `description` is capped at 1024 characters, and three canonical
   skills exceed that once `when_to_use` is added (description + 1-character
   separator + `when_to_use`):
   - `lrh-export-claude`: 1480 (its "Do not invoke proactively" guard lives
     only in `when_to_use`);
   - `lrh-work-remains`: 1155;
   - `lrh-config-gates`: 1143.

   The design therefore needs a lossless path for over-limit skills.
5. **Weak test assertions.**
   - `test_malformed_optional_portable_fields_fail` checks only a generic
     `"frontmatter"` fragment.
   - `test_valid_optional_portable_fields_are_kept` never asserts that
     `license` survives.

The stale 1852 test count in PR #747's primary record is historical and out
of scope.

### Duplication search

- In-repo: `src/lrh/skills/exporter.py` and `installer.py` hold the code in
  question. No existing work item or open PR addresses these findings.
  Other items mentioning `when_to_use` (`WI-LRH-EXPORT-DISPATCHER`,
  `WI-ANTIGRAVITY-EXPORT-CONFIRM-GATE-ASSESSMENT`) concern individual
  skills' own invocation text, not export rendering.
- Sibling repos / external libraries: none; this hardens LRH's own
  exporter and skill-source discovery.
- Recommendation: proceed.

### Demand search

- Work items / proposals: none requesting these changes.
- The deferred findings are recorded in PR #747's closeout note and its
  `_ROUND2_SELFREVIEW` / `_CONFIRM_SELFREVIEW` execution records.
- Backlog: no matching entry.
- Recommendation: this work item is the tracking artifact for them.

## Scope

- `exporter.py` validation for null manual-only markers and empty
  `compatibility`.
- `SkillSource.skill_names()` hidden-entry filtering. This is shared by
  `install`, `status`, `check`, and `export`, so the fix covers all of them.
- The ChatGPT renderer's handling of `when_to_use`.
- Test tightening and regression tests for each change.
- Reference-doc updates.

## Required Changes

1. In `src/lrh/skills/exporter.py`, when `disable-model-invocation` (SKILL.md
   frontmatter) or `policy.allow_implicit_invocation` (`agents/openai.yaml`)
   is present, its value must be a boolean. A present-but-null value fails
   the skill with an error that says how to fix it. An absent key still
   means "no marker".
2. Reject `compatibility` when it is present but empty or whitespace-only.
   First confirm the Agent Skills spec's bounds and cite them in a code
   comment.
3. In `src/lrh/skills/installer.py`, make `SkillSource.skill_names()` skip
   top-level entries whose names start with `.`, just as it skips `_`.
   Keep the existing symlink refusal ahead of that filter, so a hidden
   symlink still raises.
4. In the ChatGPT renderer, never silently lose `when_to_use`:
   - **Fold:** when `description` + one space + `when_to_use` is at most
     1024 characters, the bundled `description` becomes exactly that string.
   - **Section:** otherwise keep `description` unchanged and add the
     `when_to_use` text as a generated `## When to use` section at the top of
     the bundled `SKILL.md` body, immediately after the frontmatter. Report a
     notice that the guidance was moved into the body because of the
     description limit.
   - A folded or sectioned `when_to_use` must no longer be listed by the
     existing `stripped_metadata` notice as "not included in the bundle".
   - Both paths must be deterministic.
   - Today the section path applies to `lrh-export-claude`,
     `lrh-work-remains`, and `lrh-config-gates`; every other canonical skill
     with `when_to_use` folds.
   - Leave canonical sources unchanged, and leave the Codex and Antigravity
     renderers unchanged.
5. Tests:
   - `tests/skills_exporter_test.py`:
     - null markers fail;
     - empty `compatibility` fails;
     - hidden directories are ignored by export;
     - `when_to_use` is folded with a single-space separator when the
       combined text fits;
     - an over-limit skill gets the generated `## When to use` section at the
       top of the bundled body, an unchanged `description`, and the notice;
     - a folded or sectioned `when_to_use` is not reported as stripped;
     - each malformed-field case asserts its specific error;
     - `license` survives into the bundle.
   - `tests/skills_installer_test.py`:
     - hidden directories are neither installed nor reported by status;
     - a hidden symlink still raises.
6. Documentation:
   - `docs/reference/cli/skills.md`:
     - describe the null-marker rule and the `compatibility` bounds;
     - describe hidden-entry skipping (all subcommands);
     - describe `when_to_use` folding and the generated-section fallback
       for export.
   - `docs/how-to/use-lrh-with-agent-assistants.md`: update the ChatGPT
     Online section's "What changes in the bundle" bullets, which currently
     say `when_to_use` is dropped and reported, to describe the folding
     behavior and the generated-section fallback.

## Non-Goals

- Do not change the Codex or Antigravity renderers' metadata handling.
- Do not rewrite canonical skill text or canonical `SKILL.md` files. The only
  change allowed to a bundled body is the generated `## When to use` section
  from Required Change 4; existing body text is never modified.
- Do not add OpenAI API publishing or plugin distribution.
- Do not change the export's all-or-nothing write semantics.
- Do not re-dogfood in ChatGPT unless a folded description or the generated
  section is rejected by ChatGPT.

## Acceptance Criteria

- A blank `disable-model-invocation:` or `allow_implicit_invocation:` fails
  the skill, while an absent key does not.
- `compatibility: ''` or a whitespace-only value fails validation, and
  non-blank values up to 500 characters pass.
- A dot-prefixed directory beside real skills is skipped by
  `lrh skills install`, `status`, `check`, and `export`, and a hidden
  symlink still raises.
- `when_to_use` is folded into the bundled description (single-space
  separator) when the combined text is at most 1024 characters. Otherwise it
  becomes a generated `## When to use` section at the top of the bundled
  body, with an unchanged description and a notice. It is never silently
  dropped or reported as stripped.
- Exporter tests assert specific errors for each malformed optional field,
  and assert that `license` survives.
- The canonical export still exports the same 20 skills and skips the same
  5 manual-only skills.
- `scripts/format --check --diff`, `scripts/lint`, `scripts/test`, and
  `lrh validate` complete successfully.

## Validation

- `scripts/version tools`
- `scripts/format --check --diff`
- `scripts/lint`
- `scripts/test`
- `lrh validate`
- `lrh skills export --target chatgpt --source current-repo --out <temporary-directory>`
- `lrh skills install --dry-run --local --source <temporary-source-containing-a-.git-directory>`

## Risk Notes

- Filtering dot-prefixed entries in `skill_names()` changes install
  behavior. A deliberately dot-named skill would disappear, but none exists
  and the Agent Skills name pattern forbids leading dots.
- Folding `when_to_use` lengthens descriptions that drive ChatGPT's
  automatic selection. Keep the fold deterministic and bounded.
- For over-limit skills, guidance in the body section is read when ChatGPT
  loads the skill, not when it selects one. A guard such as
  `lrh-export-claude`'s "Do not invoke proactively" therefore takes effect
  as an in-skill instruction to stop rather than as a selection filter.
  Shortening those skills' canonical `when_to_use` so they fold is a possible
  follow-up, out of scope here.
- Making null markers fail could fail a third-party skill that writes a
  blank key. That's intended, as it's the fail-safe direction, but the error
  message should say how to fix it.
