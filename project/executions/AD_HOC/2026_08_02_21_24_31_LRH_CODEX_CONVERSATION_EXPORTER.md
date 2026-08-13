---
execution_id: 2026_08_02_21_24_31_LRH_CODEX_CONVERSATION_EXPORTER
prompt_id: PROMPT(AD_HOC:LRH_CODEX_CONVERSATION_EXPORTER)[2026-08-02T21:21:21+00:00]
work_item: AD_HOC
status: landed
rerun_of: 
pr: https://github.com/xenotaur/logical_robotics_harness/pull/469
commit: ad5931c48d2d62b3da653b9927e38e3a49c160a6
agent: codex_app
instruction_source: ad_hoc conversation — design and file PROP-LRH-CODEX-CONVERSATION-EXPORTER using src/lrh/skills/lrh-proposal as the authoritative skill source
session_transcript: pending
created_at: 2026-08-02T21:24:31+00:00
---

# Summary

Create an LRH design proposal for making Codex app conversations exportable,
inspectable, and later viewable as private, non-authoritative LRH transcript
artifacts. Record Codex-specific skill adaptation issues encountered while
using the repository's authoritative `/lrh-proposal` skill source directly.

# Result

Added `PROP-LRH-CODEX-CONVERSATION-EXPORTER` under
`project/design/proposals/proposed/lrh-codex-conversation-exporter/`. The
proposal defines Markdown-plus-manifest export artifacts, deterministic
`lrh conversation inspect-export` checking, privacy and authority defaults,
deferred `lrh serve` viewer support, and a file-based first Codex adapter.

Added a companion `backlog.md` in the proposal directory for Codex skill
adaptation issues found in this session: missing `.agents/skills` installation
path, Claude-specific execution-record defaults, Claude-specific skill
availability checks, sandbox/network assumptions in idempotence checks, and a
missing Pyright environment preflight finding.

# Validation

Ran `scripts/version tools`; it reported LRH and formatter versions plus
`Pyright not installed`, which is treated as environment/setup context rather
than a proposal-file regression.

Ran `python -m lrh.cli.main validate` after adding the proposal and backlog.
First run found one new error: `backlog.md` needed frontmatter because it lives
under `project/design/proposals/`. Added explicit backlog metadata and reran
validation.

Final validation:

```text
Validation completed: 0 error(s), 1 warning(s)

Warnings:
- [PLANNING_ACTIVE_WORKSTREAM_NO_ACTIONABLE_LEAF] workstreams/active/WS-LRH-ASSISTANTS.md: active workstream 'WS-LRH-ASSISTANTS' has no active or proposed work-item leaf
```

# Follow-up

Create a workstream or work items to implement the proposal after review and
adoption. Resolve the Codex skill adaptation backlog as part of the broader
target-aware skill installation work, especially the Codex session transcript
pointer convention.
