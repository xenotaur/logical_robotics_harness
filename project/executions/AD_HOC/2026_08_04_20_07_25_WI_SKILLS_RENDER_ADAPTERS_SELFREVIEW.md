---
execution_id: 2026_08_04_20_07_25_WI_SKILLS_RENDER_ADAPTERS_SELFREVIEW
prompt_id: PROMPT(AD_HOC:WI_SKILLS_RENDER_ADAPTERS_SELFREVIEW)[2026-08-04T20:07:19+00:00]
work_item: AD_HOC
status: in_progress
rerun_of: 
pr: 
commit: 
agent: codex_app
instruction_source: project/work_items/proposed/WI-SKILLS-RENDER-ADAPTERS.md
session_transcript: codex-app:current-task
created_at: 2026-08-04T20:07:25+00:00
---

# Summary

Diff-mode self-review for `WI-SKILLS-RENDER-ADAPTERS` before opening the
implementation PR.

# Result

A fresh independent Codex subagent reviewed the uncommitted branch diff against
the work item requirements. It reported one P2 finding: authored
`agents/openai.yaml` files with non-mapping `policy` values would have that
policy silently replaced by generated defaults during Codex rendering.

The invoking session independently re-verified the finding in
`src/lrh/skills/installer.py`, accepted it as valid, and fixed it by raising
`SkillSourceError` for non-mapping authored `policy` values. A regression test
was added in `tests/skills_installer_test.py`.

# Validation

- `conda run -n LRH python -m unittest tests.skills_installer_test` — 64 tests OK.
- `scripts/version tools` — Black 26.3.1, Ruff 0.15.12, Python 3.11.8.
- `scripts/format --check --diff` — 187 files unchanged.
- `scripts/lint` — Ruff passed; Black check passed.
- `scripts/test` — 937 tests OK when rerun outside the sandbox because serve
  tests bind loopback sockets.
- `conda run -n LRH lrh validate` — 0 errors, 0 warnings.

# Follow-up

None from this self-review pass.
