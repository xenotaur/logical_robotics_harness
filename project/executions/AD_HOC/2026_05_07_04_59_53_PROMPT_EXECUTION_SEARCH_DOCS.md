---
execution_id: 2026_05_07_04_59_53_PROMPT_EXECUTION_SEARCH_DOCS
prompt_id: PROMPT(AD_HOC:PROMPT_EXECUTION_SEARCH_DOCS)[2026-05-06T12:33:00-04:00]
work_item: AD_HOC
status: landed
rerun_of: 
pr: 
commit: 
created_at: 2026-05-07T04:59:53+00:00
---

# Summary

Harden prompt execution lookup, prompt-file matching, and exploratory
execution-record search documentation for PR 4 of the staged prompt execution
search and match implementation.

# Result

- Clarified that `lrh prompt check-execution --prompt-id ...` is the
  authoritative exact structured lookup for soft idempotence.
- Clarified that `lrh match executions <prompt-file>` extracts prompt IDs from
  prompt files and delegates exact execution-record lookup rather than applying
  heuristic or fuzzy matching.
- Clarified that `lrh search executions <query>` is exploratory text search for
  discovery, auditing, and debugging, and that search hits are not authoritative
  for blocking or rerun decisions.
- Added focused examples for the implemented commands in prompt workflow and
  execution-record documentation.
- Updated command help text for the exact lookup and prompt-file matching
  subcommands to reinforce the evidence hierarchy.
- Addressed PR review feedback by standardizing on "prompt ID" for the
  concept, reserving `prompt_id` for the front-matter field name, using "soft
  idempotence" consistently in touched guidance, and clarifying that the design
  proposal was originally design-only but is now implemented.

# Validation

- `scripts/version tools` (pass)
- `scripts/format --check --diff` (pass)
- `scripts/lint` (pass)
- `scripts/test` (pass)
- `lrh prompt --help` (pass)
- `lrh prompt check-execution --help` (pass)
- `lrh match --help` (pass)
- `lrh match executions --help` (pass)
- `lrh search --help` (pass)
- `lrh search executions --help` (pass)
- `git diff --check` (pass)
- Review protocol triage: both comments were still present, valid, and feasible;
  both were addressed.

# Follow-up

None.
