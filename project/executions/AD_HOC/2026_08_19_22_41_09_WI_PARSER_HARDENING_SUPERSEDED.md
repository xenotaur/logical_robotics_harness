---
execution_id: 2026_08_19_22_41_09_WI_PARSER_HARDENING_SUPERSEDED
prompt_id: PROMPT(AD_HOC:WI_PARSER_HARDENING_SUPERSEDED)[2026-08-19T22:39:59+00:00]
work_item: AD_HOC
status: in_progress
rerun_of: 
pr: https://github.com/xenotaur/logical_robotics_harness/pull/569
commit: 
created_at: 2026-08-19T22:41:09+00:00
agent: claude_app
instruction_source: project/work_items/abandoned/WI-PARSER-HARDENING.md
session_transcript: "claude-app:494c3b1f-14c8-46bf-a4e3-0b6e8df119e8"
---

# Summary

Follow-up to PR #531 (`PROP-LRH-FRONTMATTER-PARSER`): while preparing to
file the proposal's implementation work items under
`WS-LRH-FRONTMATTER-PARSER`, a duplication check ahead of filing turned
up `WI-PARSER-HARDENING` — a pre-existing WI (filed 2026-04-14) that the
proposal's own prior-art search had missed.

# Result

`WI-PARSER-HARDENING` ("Replace or harden bootstrap frontmatter
parsing") predates `PROP-LRH-FRONTMATTER-PARSER` by several months and
asks for the same outcome at a higher level. It was missed during the
proposal's original prior-art search because it never uses the later,
more specific vocabulary ("hand-rolled", `_parse_frontmatter_mapping`,
`control/parser.py`) that search's grep terms targeted — a real gap in
search completeness, not a false negative in the search logic itself.
Closed it the same way `WI-VALIDATOR-YAML-PARSER` was closed in #531:
`status: abandoned`, moved to `project/work_items/abandoned/`,
`resolution:` records the supersession and links back to the proposal
and to `WI-VALIDATOR-YAML-PARSER`.

# Validation

- `lrh validate` — 0 errors, 0 warnings

# Follow-up

- None — this closes the gap found; the implementation work items for
  `WS-LRH-FRONTMATTER-PARSER` are filed separately.
