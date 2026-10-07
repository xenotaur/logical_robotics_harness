---
execution_id: 2026_10_07_06_21_12_VISUAL_LANGUAGE_REV2
prompt_id: PROMPT(AD_HOC:VISUAL_LANGUAGE_REV2)[2026-10-07T06:21:11+00:00]
work_item: AD_HOC
status: landed
rerun_of: 
pr: https://github.com/xenotaur/logical_robotics_harness/pull/781
commit: 2952acba5bc59b124eb655ba6cb1b927600b96ab
agent: "claude_app"
instruction_source: "user request in session: revise the LRH Console visual-language proposal with the Q0-Q12 design-language decisions (\"Please proceed.\")"
session_transcript: "claude-app:3a9df9bd-cfda-4996-b6c4-5cff467b530a"
created_at: 2026-10-07T06:21:12+00:00
---

# Summary

This record covers Revision 2 of `PROP-LRH-CONSOLE-VISUAL-LANGUAGE`. The owner reviewed four
design sources and decided twelve design-language questions in chat between 2026-10-06 and
2026-10-07. The sources were the ChatGPT Workstream Analyzer, the Alternative D swimlane
mockups, the dependency-map mockups, and the current app and Serve. The owner then approved an
interactive frame mock. This change records those decisions in the proposal.

# Result

- **`00_proposal.md`:**
  - Added the "Revision 2 decisions" section: provenance, a decision summary, vocabulary,
    the status model, effort, themes, look and feel, layout, static-first Serve, the app frame,
    tokens, type and icons, and color vision.
  - Added inline "Revision 2" pointers where earlier sections use changed terms.
  - Rewrote Open questions and Mockup assets, extended the implementation guidance, and updated
    the frontmatter.
- **`assets/lrh-console-frame-mock.html` (new):** the interactive mock the owner reviewed, with
  sample data, Light, Dark, and System themes, and the LRH v8 icon embedded. It is also
  published privately as an artifact.
- **`README.md` and `assets/README.md`:** updated for the revision and the new asset.
- **`project/design/backlog.md`:** added "Effort estimates for work items", following the owner's
  Q4 decision.

**Fidelity handling.** Agent recommendations the owner has not explicitly reviewed are tagged
*(recommended)*. The Q8 question of how the JavaScript mode is switched on stays open: the owner
named a "`--desktop` mode", and the agent recommended a separate `--interactive` flag, which the
owner has not confirmed. The conflict with `PROP-META-OPERATIONAL-TRIAGE-SEMANTICS` ("triage
lane", a different lane set, precedence, and Title Case labels) is recorded as an open
reconciliation. The internal `triage_lane` field is unchanged.

**Pre-push cold review.** A subagent compared the change with the owner's answers, verbatim.
It confirmed every repository citation and standards claim, and found 7 should-fix items, all
applied:

- recommendation tags added;
- the Q7 pluggability scope and the Q8 "v1 is static" wording corrected;
- inline vocabulary pointers added;
- the triage-semantics band note added;
- the token-prefix note added;
- the blank line at end of file removed.

# Validation

- `lrh validate`: 0 errors and 1 warning. The warning is the existing
  `PLANNING_ACTIVE_WORKSTREAM_NO_ACTIONABLE_LEAF`.
- `scripts/lint`, `scripts/check-workflows`, and `scripts/test` passed. `git diff --check` is
  clean.
- The mock asset parses as HTML. Its interactive behavior was checked on the published artifact
  version: 20 links drawn, tracing highlights, the drawer opens, and there were no console
  errors.

# Follow-up

- A planning PR to create the L1 work items under `WS-LRH-CONSOLE-LOCAL-DOGFOOD`, after the
  owner approves the list.
- Open questions to settle, possibly as part of those work items: the Q8 mode flag and the band
  reconciliation.
