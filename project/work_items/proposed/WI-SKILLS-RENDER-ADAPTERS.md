---
resolution: null
blocked_reason: null
blocked: false
id: WI-SKILLS-RENDER-ADAPTERS
title: Add Claude and Codex skill render adapters
type: deliverable
status: proposed
owner: anthony
contributors:
  - anthony
assigned_agents: []
related_focus: []
related_roadmap: []
related_workstreams:
  - WS-SKILLS-TARGET-AWARE-INSTALL
related_design:
  - project/design/proposals/proposed/lrh-skills-target-aware-install/00_proposal.md
  - project/design/proposals/proposed/lrh-skills-target-aware-install/backlog.md
depends_on:
  - WI-SKILLS-SOURCE-ABSTRACTION
blocked_by: []
expected_actions:
  - edit_file
  - run_tests
forbidden_actions:
  - force_push
  - delete_branch
acceptance:
  - Claude and Codex install paths render through explicit target adapters
  - Codex installs emit or preserve `agents/openai.yaml` when needed
  - Claude `disable-model-invocation: true` is translated to Codex manual-only invocation policy
  - Unsupported Claude-only metadata is stripped, translated, or reported deliberately
  - lrh validate reports 0 errors
required_evidence:
  - lrh_validate
  - test_output
artifacts_expected:
  - src/lrh/skills/installer.py
  - tests/skills_installer_test.py
---

# Add Claude and Codex skill render adapters

## Summary

Split skill output generation into target-specific render adapters so Claude
and Codex installs can preserve platform-specific semantics without divergent
hand-maintained skill trees.

## Problem / Context

Direct copying is enough for the first Codex install slice, but it cannot
preserve all intended behavior. Manual-only invocation policy and unsupported
Claude UI metadata require explicit Codex handling.

## Scope

- Add Claude and Codex renderer abstractions.
- Translate manual-only invocation policy into Codex `agents/openai.yaml`.
- Report or remove unsupported metadata intentionally.
- Use the proposal-local backlog as test input for Codex compatibility cases.

## Required Changes

- Add explicit target render adapter structure for skill installation, including
  Claude and Codex renderers or equivalent target-specific rendering functions.

- Preserve current Claude install output behavior by default while routing Claude
  installs through the new renderer path.

- Add Codex rendering support that writes `SKILL.md` content appropriate for the
  `.agents/skills/` target and supports Codex metadata through a sibling
  `agents/openai.yaml` file.

- Define Codex metadata source precedence: canonical source trees may include
  authored `agents/openai.yaml`; renderers may generate Codex metadata from
  translatable `SKILL.md` frontmatter; when both are present, the authored
  canonical `agents/openai.yaml` values are preserved and generated values fill
  only missing/defaultable policy fields. Installed target-local
  `agents/openai.yaml` edits are local modifications, not authoritative source.

- Translate Claude `disable-model-invocation: true` metadata into Codex manual
  invocation policy, using `policy.allow_implicit_invocation: false` in
  `agents/openai.yaml`.

- Strip `argument-hint` from rendered Codex `SKILL.md` output. For other
  Claude-only metadata with no Codex equivalent, strip, translate, or
  deliberately report the field.

- Preserve canonical skill sources as authoritative and keep `.claude/skills/`
  and `.agents/skills/` as generated install targets.

- Preserve existing install safety behavior across rendered outputs, including
  dry-run, local-modification detection, `--force`, `--diff`, symlink refusal,
  and no script execution during install.

- Add focused tests proving Claude output remains compatible, Codex output gets
  the expected policy metadata, unsupported metadata is handled deliberately, and
  install planning still respects configured source/target/scope values.

- Update documentation where needed to describe rendered target output and the
  interim boundary between render adapters and later body-prose neutralization.

## Non-Goals

- Does not perform all body-prose neutralization.
- Does not implement ChatGPT export.

## Validation

- `scripts/version tools`
- `scripts/format --check --diff`
- `scripts/lint`
- `scripts/test`
- `lrh validate`
