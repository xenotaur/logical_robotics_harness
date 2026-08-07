---
execution_id: 2026_08_07_16_23_09_LRH_CODEX_APP_SERVER_CONVERSATION_EXPORT
prompt_id: PROMPT(AD_HOC:LRH_CODEX_APP_SERVER_CONVERSATION_EXPORT)[2026-08-07T16:22:59+00:00]
work_item: AD_HOC
status: landed
rerun_of:
pr: https://github.com/xenotaur/logical_robotics_harness/pull/510
commit: 4a4e660c7e64a7871daec0b02385be8294bfb723
created_at: 2026-08-07T16:23:09+00:00
agent: codex_app
instruction_source: project/design/proposals/proposed/lrh-codex-app-server-conversation-export/00_proposal.md
session_transcript: codex-app:019fc43f-e2d9-7503-88cb-9d9a8136c111
---

# Summary

Capture the Codex app-server conversation export design as LRH planning
artifacts after PR #503 retired the current-session API feasibility risk.
Create the follow-on proposal, a new workstream, and the first implementation
work item in one reviewable PR.

# Result

- Added `PROP-LRH-CODEX-APP-SERVER-CONVERSATION-EXPORT` as a follow-on proposal
  that extends the adopted Codex conversation exporter design with a documented
  app-server `thread/read` source route.
- Added `WS-LRH-CODEX-APP-SERVER-EXPORT` to coordinate the app-server exporter,
  Codex skill wrapper, later target-aware export wrapper, and dogfood sequence.
- Added `WI-CODEX-CONVERSATION-EXPORT-APP-SERVER` as the first prompt-ready
  implementation item for `lrh conversation export-codex-thread`.
- Updated `project/design/proposals/README.md` with the new proposal-set entry.
- Kept implementation out of scope for this planning PR.

# Validation

- `scripts/version tools` passed.
- `lrh validate` passed with 0 errors and 0 warnings.
- `lrh request ready-work-item --work-item WI-CODEX-CONVERSATION-EXPORT-APP-SERVER`
  reported readiness status `ready`.
- `scripts/format --check --diff` passed.
- `scripts/lint` passed.
- `scripts/test` first failed in the restricted sandbox because `lrh serve`
  tests could not bind local sockets (`PermissionError: [Errno 1] Operation not
  permitted`); rerunning the same command with socket-binding permission passed
  1004 tests.

# Follow-up

- Implement `WI-CODEX-CONVERSATION-EXPORT-APP-SERVER`.
- After the CLI adapter lands, create/implement the `/lrh-codex-export` skill
  wrapper and dogfood it with private real-session exports.
- Only after the Codex-specific export path works, design or implement the
  target-aware `/lrh-export` wrapper.
- Keep the Codex executable trust/signature investigation and
  experimental-code linkage guardrail as separate backlog-driven follow-ups.
