---
execution_id: 2026_09_26_02_57_59_WI_LRH_CONSOLE_DESKTOP_L0_TOOLCHAIN_GUARDRAILS
prompt_id: PROMPT(AD_HOC:WI_LRH_CONSOLE_DESKTOP_L0_TOOLCHAIN_GUARDRAILS)[2026-09-26T02:57:28+00:00]
work_item: AD_HOC
status: in_progress
rerun_of: 
pr: https://github.com/xenotaur/logical_robotics_harness/pull/732
commit: 
agent: "claude_app"
instruction_source: "project/work_items/proposed/WI-LRH-CONSOLE-DESKTOP-L0.md"
session_transcript: "claude-app:3a9df9bd-cfda-4996-b6c4-5cff467b530a"
created_at: 2026-09-26T02:57:59+00:00
---

# Summary

Ad-hoc planning update, requested by the user after a toolchain-options review:
fold the desktop toolchain isolation guardrails into `WI-LRH-CONSOLE-DESKTOP-L0`
before implementation.

# Result

The work item was updated with:

- a "Toolchain placement" section comparing four options, backed by repository
  evidence at `9919582b`;
- a Node-free Cargo CLI requirement in required change 1;
- new required change 9, covering a pinned Rust toolchain under
  `apps/desktop/`, `MANIFEST.in` `prune apps` plus an sdist-exclusion check,
  path-filtered non-required `desktop.yml`, `apps/README.md` and an AGENTS.md
  boundary line, and a thin `scripts/desktop` wrapper;
- matching `artifacts_expected`, acceptance, validation, and risk entries.

No code changed.

# Validation

- `lrh validate`: 0 errors, 0 warnings.
- `lrh work-items readiness WI-LRH-CONSOLE-DESKTOP-L0`: `prompt_ready: yes`,
  no warnings.

# Follow-up

Land after review. Implementation remains `/lrh-execute WI-LRH-CONSOLE-DESKTOP-L0`.
