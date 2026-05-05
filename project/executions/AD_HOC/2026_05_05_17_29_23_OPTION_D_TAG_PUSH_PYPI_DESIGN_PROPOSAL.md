---
execution_id: 2026_05_05_17_29_23_OPTION_D_TAG_PUSH_PYPI_DESIGN_PROPOSAL
prompt_id: PROMPT(AD_HOC:OPTION_D_TAG_PUSH_PYPI_DESIGN_PROPOSAL)[2026-05-05T12:14:18-04:00]
work_item: AD_HOC
status: landed
rerun_of:
pr:
commit:
created_at: 2026-05-05T17:29:23+00:00
---

# Summary

Added a new design proposal set under
`project/design/proposals/tag-push-pypi-publishing/` describing Option
D tag-push publishing of the safe-default `lrh` distribution to
TestPyPI/PyPI via Trusted Publishing. Updated
`project/design/proposals/README.md` with a minimal index entry for the
new proposal set.

# Result

Created proposal documents that cover motivation, safe-default package
semantics, compatibility with future package split direction, Trusted
Publishing rationale, illustrative workflow shape, TestPyPI rehearsal
posture, smoke-test and release-evidence expectations, open design
choices, tradeoffs, risks/mitigations, and phased follow-up
implementation sequence.

No release workflow, packaging metadata, CLI behavior, or module layout
implementation changes were made.

# Validation

- `scripts/version tools`
- `lrh validate`

Both commands completed successfully in the Codex Cloud environment.

# Follow-up

- If/when this design direction is accepted, convert it into narrow
  implementation PRs: packaging metadata/resource-loading hardening,
  build+smoke scripts, TestPyPI rehearsal lane, and tag-push PyPI
  Trusted Publishing workflow.
- Decide unresolved implementation details listed in the proposal
  (workflow split/filenames, versioning mechanics, Python matrix,
  release artifact attachment, environment protections).
