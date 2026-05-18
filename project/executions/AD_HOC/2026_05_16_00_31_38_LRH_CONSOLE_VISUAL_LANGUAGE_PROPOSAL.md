---
execution_id: 2026_05_16_00_31_38_LRH_CONSOLE_VISUAL_LANGUAGE_PROPOSAL
prompt_id: PROMPT(AD_HOC:LRH_CONSOLE_VISUAL_LANGUAGE_PROPOSAL)[2026-05-15T23:58:00-04:00]
work_item: AD_HOC
status: in_progress
rerun_of:
pr:
commit:
created_at: 2026-05-16T00:31:38+00:00
---

# Summary

Recorded the proposed LRH Console visual-language direction for later `lrh serve` dashboard work.
The proposal names Alternative D, the Enhanced Swimlane Console, as the preferred future light/dark
visual direction while keeping the current safe-default MVP scope unchanged.

# Result

- Added `project/design/proposals/proposed/lrh-console-visual-language/00_proposal.md` with the
  proposed visual language, information architecture, conceptual model, UI component patterns,
  semantic status vocabulary, theme/token guidance, accessibility requirements, safe-default
  constraints, implementation guidance, open questions, and mockup-asset references.
- Added `project/design/proposals/proposed/lrh-console-visual-language/README.md` as the proposal-set
  entry point.
- Added `project/design/proposals/proposed/lrh-console-visual-language/assets/README.md` as the
  placeholder for manually supplied light and dark Alternative D mockups.
- Updated `project/design/proposals/README.md` to list the proposed design.
- Updated `project/work_items/proposed/WI-LRH-SERVE-SAFE-DEFAULT-MVP.md` to reference the proposal as
  future directional UX guidance, explicitly not an acceptance criterion or scope expansion for the
  current safe-default MVP.

# Validation

- `scripts/version tools` passed and reported the task-phase tool versions; Pylint and Conda remain
  unavailable in this environment as reported by the script.
- `lrh validate` passed with 0 errors and 3 existing planning warnings for unrelated orphaned active
  work items.
- `git diff` was inspected to keep the PR scoped to the new design proposal, proposal index link,
  serve work-item reference, and this execution record.

# Follow-up

- Manually add the selected illustrative mockup image files when available:
  `alternative_d_enhanced_swimlane_console_light.png` and
  `alternative_d_enhanced_swimlane_console_dark.png`.
- Later `lrh serve` UI work can use this proposal as directional visual-language guidance after the
  safe-default MVP behavior stabilizes.
