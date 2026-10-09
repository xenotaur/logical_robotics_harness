---
execution_id: 2026_10_09_15_47_18_LRH_CONSOLE_STATUSBOARD
prompt_id: PROMPT(WI-LRH-CONSOLE-STATUSBOARD:LRH_CONSOLE_STATUSBOARD)[2026-10-09T05:15:05+00:00]
work_item: WI-LRH-CONSOLE-STATUSBOARD
status: in_progress
rerun_of:
pr: https://github.com/xenotaur/logical_robotics_harness/pull/805
commit:
agent: "claude_app"
instruction_source: "/lrh-execute WS-LRH-CONSOLE-LOCAL-DOGFOOD"
session_transcript: claude-app:3a9df9bd-cfda-4996-b6c4-5cff467b530a
created_at: 2026-10-09T15:47:18+00:00
---

# Summary

`/lrh-execute WS-LRH-CONSOLE-LOCAL-DOGFOOD` resolved to `WI-LRH-CONSOLE-STATUSBOARD`, the first
unfinished item in the workstream's order. Its dependency (FRAME) was resolved, readiness was
`prompt_ready: yes` with no warnings, and there was no prior record. At the chain gate the owner
approved the run plan and conditions, and settled the band set.

# Result

- **Band decision (owner):** the six states LRH already computes, in the display order Blocked,
  Needs attention, Active work, Awaiting review, Stable, Unknown, with sentence-case labels. There
  is no new triage logic, and `triage_lane` keeps its name. This is recorded in
  `PROP-LRH-CONSOLE-VISUAL-LANGUAGE` (Vocabulary) and cross-referenced in
  `PROP-META-OPERATIONAL-TRIAGE-SEMANTICS`, where Ready for Work and Archived stay later work.
- **Statusboard (`/meta`):**
  - Each band is a `<details>` element with a glyph, label, count, description, tinted header,
    and accent rail. Bands with projects start open; empty bands stay visible and closed, and an
    empty Unknown band says why.
  - Cards show focus, next action, a validation chip, and a freshness chip ("Read live" or "Not
    read: <reason>"). The registry facts are under Details.
  - The bands come before the explanatory text, which the owner approved as part of the plan
    (content first).
- **`/api/meta`:** returns the new order and labels, and gains `read_at`. Tests now look bands up
  by status rather than position.
- **Desktop:** at the owner's choice after the pre-push review, LRH Console opens on `/meta`.
  View > Statusboard (Cmd+0) and View > Workspace (Cmd+Shift+0) replace Dashboard and Meta, and
  Open in browser falls back to the statusboard.
- **Pre-push cold review:** found no escaping problems. Its fixes are applied in `5a86684c` and
  `6bfb3839`:
  - the band order is stated as a display order, not triage precedence;
  - cards get a border, padding, and a surface, and long text wraps;
  - band counts are read aloud as "N projects", and the disclosure glyph is silent;
  - new tests cover escaping, the Not read chip, and HTML band order;
  - the README now describes the statusboard;
  - the desktop app opens on the home view (the owner chose this).

# Validation

- `scripts/format --check --diff [--desktop]`, `scripts/lint [--desktop]`, and
  `scripts/test [--desktop]` pass, as does `tests/smoke/desktop_protocol_smoke.py`.
- `lrh validate`: 0 errors, 0 warnings.
- A browser check against the owner's registry of 8 projects, in light and dark and at phone
  width, found no horizontal scroll.

# Follow-up

- Owner check in this branch's LRH Console build, which also checks the WebKit layout of the
  `<summary>` element.
- Remote-only projects land in Unknown because LRH cannot read them. That comes from the existing
  triage logic, not from this change.
