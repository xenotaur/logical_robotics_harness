---
execution_id: 2026_08_04_20_08_35_WI_SKILLS_RENDER_ADAPTERS
prompt_id: PROMPT(WI-SKILLS-RENDER-ADAPTERS:WI_SKILLS_RENDER_ADAPTERS)[2026-08-04T19:51:24+00:00]
work_item: WI-SKILLS-RENDER-ADAPTERS
status: landed
rerun_of:
pr: https://github.com/xenotaur/logical_robotics_harness/pull/485
commit: 3d7a38cf120998a1fbf870813700ab181095ffae
agent: codex_app
instruction_source: project/work_items/proposed/WI-SKILLS-RENDER-ADAPTERS.md
session_transcript: codex-app:current-task
created_at: 2026-08-04T20:08:35+00:00
---

# Summary

Implemented `WI-SKILLS-RENDER-ADAPTERS`, adding target-specific skill render
adapters for Claude and Codex installs while preserving the existing
target-aware install/source/scope machinery.

# Result

- Added explicit Claude and Codex renderers in `src/lrh/skills/installer.py`.
- Preserved Claude install output as canonical skill bytes.
- Rendered Codex `SKILL.md` output by stripping Claude-only frontmatter fields
  including `argument-hint` and `disable-model-invocation`.
- Translated `disable-model-invocation: true` into Codex
  `agents/openai.yaml` policy with `policy.allow_implicit_invocation: false`.
- Preserved authored canonical `agents/openai.yaml` values and only filled
  missing/defaultable generated policy fields.
- Routed install comparison, overwrite, and CLI `--diff` behavior through
  rendered target output.
- Updated skill-install documentation to describe Codex render-adapter
  behavior while leaving body-prose neutralization as follow-on work.

# Validation

- `scripts/version tools` — Black 26.3.1, Ruff 0.15.12, Python 3.11.8;
  pyright not installed per known tooling gap.
- `scripts/format --check --diff` — 187 files unchanged.
- `scripts/lint` — Ruff passed; Black check passed.
- `conda run -n LRH python -m unittest tests.skills_installer_test` — 64
  tests OK.
- `scripts/test` — 937 tests OK when rerun outside the sandbox because serve
  tests bind loopback sockets.
- `conda run -n LRH lrh validate` — 0 errors, 0 warnings.
- `conda run -n LRH lrh skills install --dry-run --local --target codex
  --source current-repo` — resolved expected install plan.

# Follow-up

Follow-on `WI-SKILLS-BODY-PROSE-NEUTRALIZATION` remains responsible for
rewriting Claude-specific body prose in installed skill instructions.
