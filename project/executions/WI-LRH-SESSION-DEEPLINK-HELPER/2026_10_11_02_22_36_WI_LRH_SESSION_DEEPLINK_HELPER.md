---
execution_id: 2026_10_11_02_22_36_WI_LRH_SESSION_DEEPLINK_HELPER
prompt_id: PROMPT(WI-LRH-SESSION-DEEPLINK-HELPER:WI_LRH_SESSION_DEEPLINK_HELPER)[2026-10-10T18:21:59+00:00]
work_item: WI-LRH-SESSION-DEEPLINK-HELPER
status: in_progress
rerun_of:
pr: https://github.com/xenotaur/logical_robotics_harness/pull/822
commit:
created_at: 2026-10-11T02:22:36+00:00
agent: claude_app
instruction_source: project/work_items/proposed/WI-LRH-SESSION-DEEPLINK-HELPER.md
session_transcript: pending
---

# Summary

Implement WI-LRH-SESSION-DEEPLINK-HELPER: one shared session-link route definition, a pure link_for(pointer) helper that reads it, and an `lrh sessions deeplink` command as the proving consumer.

# Result

Opened PR #822 on xenotaur/feat/wi-lrh-session-deeplink-helper. Added:

- src/lrh/conversations/session_links.json: the single route definition (claude-app and codex-app routes, antigravity listed as unsupported, accept/reject_pointers/reject_links vectors), shipped through pyproject.toml package-data.
- src/lrh/conversations/deeplink.py: link_for(pointer) and is_session_link(url), both pure and both driven by that file.
- `lrh sessions deeplink POINTER` in src/lrh/sessions_workflow.py (link on stdout and exit 0, or error on stderr and exit 1).
- tests/conversations_tests/deeplink_test.py and new cases in tests/cli_tests/sessions_test.py.
- docs/conversations/session_deep_links.md, plus entries in docs/conversations/README.md, docs/reference/cli/sessions.md and src/lrh/conversations/README.md. The last two were beyond the approved plan's file list and were surfaced at the plan-divergence gate and approved.

Claude and Codex routes were verified by hand with `open`; the Claude epitaxy route is undocumented and best-effort. Antigravity has no known route. The helper checks the shape of an id only; the host-vs-child-id invariant stays on the producer side.

# Validation

Dedicated conda env bound to this worktree (scripts/conda-worktree-env LrhSessionDeeplink): ruff 0.15.12, black 26.3.1, Python 3.11.17; pyright is not installed there (scripts/version tools reports it, not a gating check). scripts/format --check --diff clean, scripts/lint clean (after fixing one E501 and a Black reformat in my own new files), scripts/test 2260 tests OK, lrh validate 0 errors and 0 warnings. A built wheel contains lrh/conversations/session_links.json, and link_for and `lrh sessions deeplink` work from a clean venv install. Diff-mode self-review (record 2026_10_10_23_30_05_WI_LRH_SESSION_DEEPLINK_HELPER_SELFREVIEW): no blocking findings.

# Follow-up

WI-LRH-CONSOLE-DEEPLINK-HANDOFF depends on this item and should read session_links.json from Rust with include_str!. session_transcript is pending until closeout.
