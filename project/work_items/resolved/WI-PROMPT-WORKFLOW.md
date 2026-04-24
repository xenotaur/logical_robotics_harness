---
resolution: Completed
blocked_reason: null
blocked: false
id: WI-PROMPT-WORKFLOW
title: Integrate prompt-workflow guidance into project documentation
type: operation
status: resolved
priority: medium
owner: anthony
contributors:
  - anthony
assigned_agents: []
related_roadmap:
  - ROADMAP-PHASE-03
depends_on: []
blocked_by: []
expected_actions:
  - edit_file
  - run_tests
  - create_report
forbidden_actions:
  - force_push
  - delete_branch
acceptance:
  - prompt-workflow guidance is referenced in design, context, and roadmap docs where it naturally fits
  - work-item guidance references `PROMPTS.md` and execution-record conventions
  - execution records are used for meaningful prompt-driven work with soft idempotence checks
required_evidence:
  - code_diff
  - manual_review
artifacts_expected:
  - docs_diff
---

# Summary

Integrate lightweight prompt-workflow guidance into LRH documentation so prompt-driven work is traceable without adding heavy process.

## Completion Notes

- Prompt-workflow references are integrated in project design, human context, roadmap, and work-item guidance.
- Execution-record conventions remain anchored on `PROMPTS.md` and `project/executions/README.md`.
