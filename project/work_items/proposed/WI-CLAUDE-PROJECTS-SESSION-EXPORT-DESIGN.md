---
resolution: null
blocked_reason: null
blocked: false
id: WI-CLAUDE-PROJECTS-SESSION-EXPORT-DESIGN
title: "Design how LRH captures Claude Projects conversations: coordinator, linked-folder threads, and cloud threads"
type: investigation
status: proposed
owner: anthony
contributors:
  - anthony
assigned_agents: []
related_focus:
  - FOCUS-EXECUTION-FRAMEWORK-PLANNING
related_roadmap:
  - ROADMAP-PHASE-03
related_workstreams: []
related_design:
  - project/design/proposals/adopted/lrh-claude-conversation-exporter/00_proposal.md
  - project/design/proposals/adopted/lrh-session-archive-sync/00_proposal.md
  - project/design/proposals/proposed/lrh-conversations-storage-interop/00_proposal.md
  - project/design/proposals/proposed/lrh-execution-sessions/00_proposal.md
  - project/workstreams/proposed/WS-LRH-SESSION-DEEP-LINKING.md
depends_on: []
blocked_by: []
expected_actions:
  - create_file
  - create_report
forbidden_actions:
  - force_push
  - delete_branch
  - merge_pr
  - implement_export_changes
  - print_transcript_text
  - commit_raw_transcript_data
acceptance:
  - "A proposal records, with evidence, where each kind of Claude Projects conversation is stored and whether LRH can retrieve it: the coordinator conversation, a cloud thread, and a linked-folder thread"
  - "The proposal chooses how LRH treats the coordinator conversation (capture it, have the coordinator keep a worklog, or record it as not retrievable) and gives the reason"
  - "The proposal states whether the cloud-session design in PROP-LRH-CLOUD-SESSION-CAPTURE holds inside a Project cloud thread, marking each point as tested or unverified"
  - "The proposal says how a Project and its threads map onto session_transcript pointers and the project/sessions index"
  - "The proposal says what should happen to the two older session proposals (supersede, amend, or leave) and lists the follow-on work items it recommends, without creating them"
  - "No transcript text is printed or committed, and lrh validate reports 0 errors"
required_evidence:
  - manual_review
  - lrh_validate
artifacts_expected:
  - project/design/proposals/proposed/lrh-claude-projects-session-capture/00_proposal.md
---

# WI-CLAUDE-PROJECTS-SESSION-EXPORT-DESIGN: Design session capture for Claude Projects

## Summary

Run a design session and write a proposal for how LRH keeps a record of work
done through Claude Projects. A Project has a coordinator conversation and
threads; a thread runs either in Anthropic's cloud or on the user's own
machine through Remote Control. LRH's exporter was built for single local
sessions and has no notion of a Project.

## Problem / Context

`WS-SESSION-ARCHIVE-SYNC` set the rule that no agent session that changed a
repository is ever lost. Claude Projects puts that rule at risk in three
different ways, one per conversation kind:

| Kind | Where it runs | State on 2026-11-23 |
|---|---|---|
| Linked-folder thread | The user's machine, started through Remote Control | Verified: it writes an ordinary transcript under the Claude projects directory, and `export-claude-session --transcript-path` exported it with a matching source hash |
| Cloud thread | Anthropic cloud VM | Not retrievable locally. `PROP-LRH-CLOUD-SESSION-CAPTURE` (open PR #863) designs in-session export plus download for ordinary cloud sessions; nothing has tested it inside a Project thread |
| Coordinator conversation | Anthropic cloud | No local file and no documented export |

What the code does today:

- Every discovery route in the exporter ends at a local file
  (`src/lrh/conversations/claude_export.py`, `_resolve_transcript_path`).
- `/lrh-closeout` already accepts `none` as a terminal `session_transcript`
  value for back ends with no retrievable transcript, and names a
  `codex-cloud:` pointer. No equivalent exists for Claude cloud or Projects.

What Anthropic documents (code.claude.com/docs, read 2026-11-23):

- Project threads are usually cloud sessions; a thread can instead run on
  the user's computer through Remote Control and pauses while that computer
  is asleep.
- Each cloud session gets a fresh VM. User-level skills are not loaded.
- Project threads do not run hooks from a repository's settings file.
- No transcript export, download, or API for cloud sessions is documented.

Open questions for the design session:

- Can the coordinator conversation be captured at all? If not, is a
  coordinator-kept worklog committed or archived by LRH an acceptable
  substitute, and what must it record?
- Does `/lrh-export-claude` resolve the current session when typed inside a
  linked-folder thread, or only by explicit path from outside it?
- Do the plugin sync, allow rules, and file delivery that
  `PROP-LRH-CLOUD-SESSION-CAPTURE` relies on behave the same in a Project
  cloud thread?
- Should a Project be a first-class grouping in the `project/sessions`
  index, and what pointer scheme identifies a thread?
- Could session-end capture remove the manual export step for local and
  linked-folder threads?

### Duplication search

- In-repo: no work item, proposal, workstream, or skill mentions Claude
  Projects, a coordinator, a worklog, or teleport. `WS-LRH-SESSION-DEEP-LINKING`
  explicitly excludes cloud sessions.
- Open PRs: PR #863 (`PROP-LRH-CLOUD-SESSION-CAPTURE` and seven work items)
  covers transcript capture from ordinary Claude Code cloud sessions,
  including a probe of `claude --teleport` and an open question on a
  `claude-cloud:` pointer. This item is scoped to exclude that ground.
- Sibling repos: none identified.
- External libraries: none identified.
- Verdict: no duplicate once PR #863's scope is excluded.

### Demand search

- The adopted Claude exporter proposal leaves open whether Claude Code on
  the web writes transcripts. No work item or backlog entry requests
  Projects support.
- Verdict: no existing request to close or link.

## Scope

- The three conversation kinds above, for Claude Projects only.
- Identity and pointer design for Projects and threads.
- How this fits with `lrh-conversations-storage-interop` and
  `lrh-execution-sessions`.

## Required Changes

- Create `project/design/proposals/proposed/lrh-claude-projects-session-capture/00_proposal.md`
  with the findings, the decisions, and a list of recommended follow-on
  work items.
- Run whatever live checks are needed to answer the open questions, and
  mark any that could not be run as unverified.

## Non-Goals

- Does not change the exporter, the skills, or the CLI.
- Does not redo the cloud-container design in `PROP-LRH-CLOUD-SESSION-CAPTURE`.
- Does not cover Codex Cloud or Antigravity.
- Does not create the follow-on work items it recommends.
- Does not decide whether to run Projects on a dedicated machine.

## Acceptance Criteria

- The proposal records, with evidence, where each of the three conversation
  kinds is stored and whether LRH can retrieve it.
- It chooses a treatment for the coordinator conversation and gives the
  reason.
- It states whether the `PROP-LRH-CLOUD-SESSION-CAPTURE` design holds in a
  Project cloud thread, with each point marked tested or unverified.
- It says how a Project and its threads map onto `session_transcript`
  pointers and the `project/sessions` index.
- It says what should happen to the two older session proposals and lists
  recommended follow-on work items without creating them.
- No transcript text is printed or committed, and `lrh validate` reports
  0 errors.

## Validation

- lrh validate

## Risk Notes

- Claude Projects is in public beta, so storage and behaviour may change
  under the design.
- If PR #863 changes materially before it merges, the boundary between the
  two proposals needs rechecking.
