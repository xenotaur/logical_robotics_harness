---
resolution: "Implemented and merged in PR #532 (commit f6e0dde60f1b1a8d116a3881f735a621844acc7b)"
blocked_reason: null
blocked: false
id: WI-CODEX-CONVERSATION-EXPORT-SKILL
title: Implement thin Codex conversation export skill wrapper
type: deliverable
status: resolved
owner: anthony
contributors:
  - anthony
assigned_agents: []
related_focus: []
related_roadmap: []
related_workstreams:
  - WS-LRH-CODEX-APP-SERVER-EXPORT
related_design:
  - project/design/proposals/proposed/lrh-codex-app-server-conversation-export/00_proposal.md
  - project/design/proposals/adopted/lrh-codex-conversation-exporter/00_proposal.md
  - docs/reference/cli/conversation.md
  - project/executions/AD_HOC/2026_08_08_21_03_32_CODEX_APP_SERVER_EXPORT_DOGFOOD.md
depends_on:
  - WI-CODEX-CONVERSATION-EXPORT-APP-SERVER
blocked_by: []
expected_actions:
  - create_file
  - write_docs
  - run_tests
forbidden_actions:
  - force_push
  - delete_branch
  - merge_pr
  - scrape_codex_storage_internals
  - commit_raw_transcript_data
acceptance:
  - `src/lrh/skills/lrh-codex-export/SKILL.md` exists as a thin workflow wrapper around `lrh conversation export-codex-thread`
  - the skill defaults the thread id from `CODEX_THREAD_ID` when available and asks for an explicit thread id only when required
  - the skill chooses or instructs the user to choose absolute private output paths outside the current Git worktree, especially for `--raw-out`
  - the skill runs `lrh conversation inspect-export` after export and reports metadata only
  - the skill documents that restricted/sandboxed environments may need approval for Codex app-server access to `~/.codex`
  - the skill warns against line-based previews of exported Markdown and directs users to manifest-aware inspection
  - `lrh validate` reports 0 errors for the new skill/work-item change set
required_evidence:
  - lrh_validate
  - manual_review
artifacts_expected:
  - src/lrh/skills/lrh-codex-export/SKILL.md
---

## Summary

Implement `/lrh-codex-export` as a thin Codex skill wrapper around the landed
`lrh conversation export-codex-thread` CLI command.

## Problem / Context

`WI-CODEX-CONVERSATION-EXPORT-APP-SERVER` delivered and dogfooded the production
Codex app-server export CLI. The remaining usability gap is the agent-facing
workflow: a Codex user should be able to invoke a skill that selects safe private
paths, uses the current task id when available, runs export plus inspection, and
reports only metadata.

The first real dogfood export succeeded, but it found two wrapper-relevant
issues: sandboxed execution can block Codex app-server access to `~/.codex`, and
line-based previews of Markdown can print transcript content after frontmatter.

## Scope

- Create `src/lrh/skills/lrh-codex-export/SKILL.md`.
- Keep the skill as a workflow wrapper; do not duplicate Python export logic.
- Use the CLI command documented in `docs/reference/cli/conversation.md`.
- Require private raw output outside the current Git worktree.
- Run `inspect-export` after export and summarize only metadata.
- Capture dogfood cautions about sandbox approval and manifest-aware inspection.

## Non-Goals

- Do not implement target-aware `/lrh-export` in this work item.
- Do not add a paged app-server adapter.
- Do not commit raw transcript data or generated private exports.
- Do not solve full Codex executable trust diagnostics.

## Validation

- `lrh validate`
- Manual dry-run/read-through of the skill instructions against the dogfood
  findings.
