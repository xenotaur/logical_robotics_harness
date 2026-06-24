# LRH Execution Sessions — Proposal Set

## Status summary

- `00_proposal.md` — umbrella proposal. Status: `proposed` / `not_started`

## What this proposal set covers

This proposal set formalizes the **execution session model** for
Logical Robotics Harness. It addresses the gap between LRH's existing
prompt-driven workflow (designed around Codex Cloud's single-document
submission model) and Claude.app sessions (multi-turn conversations
that produce PRs but have no machine-readable reference in execution
records).

The central proposal defines:

1. A **three-phase execution session model** (design → instruction →
   execution) that applies to any execution backend.
2. How the **Claude.app session transcript** (a JSONL file at
   `~/.claude/projects/<project-slug>/<session-id>.jsonl`) is
   identified and referenced in execution records.
3. How execution sessions relate to the existing **workstream →
   work-item → execution record** hierarchy.
4. Where **Taurcode meta-prompts** (the instruction-phase artifact for
   Claude.app-driven execution) belong in LRH's distribution model.
5. A **staged implementation** that starts with documentation and
   schema additions before requiring new CLI commands.

## Reading order

1. [`00_proposal.md`](00_proposal.md) — the full proposal; start here.

## Canonical documents this proposal touches

- `PROMPTS.md` — prompt workflow; the three-phase model extends this
- `project/executions/README.md` — execution-record schema; optional
  new fields are proposed here
- `project/design/proposals/proposed/lrh-project-local-skills/` —
  the distributable-skills proposal this proposal builds on for
  Taurcode meta-prompt placement
- `project/design/proposals/proposed/workstream-execution-framework/`
  — deferred runtime architecture; provides observability-vs-evidence
  distinction used here
- `project/design/proposals/adopted/workstreams-and-recursive-planning-tree/`
  — adopted hierarchy (Project → Workstream → Work Item)
- `project/design/proposals/proposed/lrh-conversations-storage-interop/`
  — complementary proposal on raw conversation capture and storage
