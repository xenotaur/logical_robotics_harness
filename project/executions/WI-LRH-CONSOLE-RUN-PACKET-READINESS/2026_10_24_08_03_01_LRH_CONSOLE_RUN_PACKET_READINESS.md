---
execution_id: 2026_10_24_08_03_01_LRH_CONSOLE_RUN_PACKET_READINESS
prompt_id: PROMPT(WI-LRH-CONSOLE-RUN-PACKET-READINESS:LRH_CONSOLE_RUN_PACKET_READINESS)[2026-10-23T05:31:50+00:00]
work_item: WI-LRH-CONSOLE-RUN-PACKET-READINESS
status: landed
rerun_of:
pr: https://github.com/xenotaur/logical_robotics_harness/pull/855
commit: 8976c8b70d220909003e5d0128add696cc131d09
created_at: 2026-10-24T08:03:01+00:00
agent: claude_app
instruction_source: https://github.com/xenotaur/logical_robotics_harness/pull/855
session_transcript: claude-app:3a9df9bd-cfda-4996-b6c4-5cff467b530a
---

# Summary

This record covers the implementation of `WI-LRH-CONSOLE-RUN-PACKET-READINESS` under `/lrh-execute`, with the run plan approved by the owner. The owner chose 1A: a blocked item whose run packet passes keeps Copy enabled, and the blocked flag is shown on its own row. The owner asked for the Copy-button mismatch to be filed at closeout.

# Result

- **`run_packet.py`:**
  - New public `validate_work_item(path)`, plus a private `_validate_frontmatter`. Together they return exactly the diagnostics generation checks.
  - `render_run_packet_from_work_item` now calls that helper, with its behavior unchanged.
- **`serve.py`, work-item page:**
  - A "Run packet (validated)" row (`_run_packet_validation_text`) shows Passes, Fails with its errors, or Not declared.
  - A "Blocked flag" row reads `item.blocked` and its reason. It replaces the never-firing `status == "blocked"` check.
  - Copy generated prompt is enabled exactly when the run packet passes, and the explanatory paragraph is rewritten to match.
- **Tests:** `run_packet_test` (the helper matches generation) and `serve_test` (Copy equals generation for WI-A, WI-B and a blocked WI-HELD; the Fails text tested directly).
- **Docs:** `docs/reference/cli/serve.md` and the visual-language proposal's readiness vocabulary table.
- **Finding:**
  - Any item that declares run-packet fields which then fail validation fails `lrh validate`, and `load_core_project_state` then returns an empty project, so every page 404s.
  - Fails therefore cannot appear on a loadable project. The cold review confirmed this across ten cases.
- **Owner check:**
  - The owner's LRH Console points its LRH project at another checkout, so the check ran on a serve of this branch.
  - The three pages looked right: Passes with Copy enabled on a temporarily declared item, which was reverted and never committed; "Blocked flag: Yes: …" on WI-LRH-ASSISTANTS-STAGE-2; and Not declared on an ordinary item.
  - The owner noted that these items cannot be reached from LRH Console unless they are on a map, and asked for that to be filed.

# Validation

- `scripts/format --check --diff`: exit 0.
- `scripts/lint`: exit 0.
- `scripts/test`: 2371 OK.
- `lrh validate`: 0 errors, 0 warnings.

# Follow-up

- Land through `/lrh-land`.
- Three follow-ups to file at closeout, at the owner's request:
  - wiring and gating of the Copy generated prompt button;
  - one failing run-packet declaration blanks the whole project in LRH Console;
  - work-item pages are reachable only from map cards.
