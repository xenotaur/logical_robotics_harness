---
resolution: null
blocked_reason: null
blocked: false
id: WI-EXEC-SESSIONS-DISCOVERY
title: Implement lrh sessions discover and lrh sessions link commands
type: deliverable
status: proposed
owner: anthony
contributors:
  - anthony
assigned_agents: []
related_focus:
  - FOCUS-EXECUTION-FRAMEWORK-PLANNING
related_roadmap:
  - ROADMAP-PHASE-03
related_workstreams:
  - WS-EXECUTION-FRAMEWORK
related_design:
  - project/design/proposals/proposed/lrh-execution-sessions/00_proposal.md
depends_on:
  - WI-EXEC-SESSIONS-DOCS
  - WI-EXEC-SESSIONS-SCHEMA
blocked_by: []
expected_actions:
  - edit_file
  - write_docs
  - run_tests
forbidden_actions:
  - force_push
  - delete_branch
  - modify_lrh_closeout_skill
  - write_session_transcript_without_confirmation
acceptance:
  - lrh sessions discover [--project-root .] scans ~/.claude/projects/<project-slug>/ and lists local session JSONL files with their child SDK id, approximate size, and mtime, plus any execution record whose session_transcript already references that id
  - discover output explicitly labels ids as the child SDK id and does not suggest writing them directly into session_transcript, since the child id differs from the canonical host id on resumed sessions (the bug fixed in PR #409/#431)
  - lrh sessions link --session <id> --execution <execution-id> writes session_transcript on the named record only when given a value already conforming to the <backend>:<id> grammar (validated per WI-EXEC-SESSIONS-SCHEMA's rules) or a pending/none sentinel — it does not silently promote a bare discovered child id
  - both commands are local-filesystem-only (no session-management MCP tool dependency), complementing rather than duplicating /lrh-closeout Step 3's live host-id resolution
  - lrh validate passes with 0 errors; new tests cover discover (empty dir, sessions found, malformed filenames) and link (grammar-valid and grammar-invalid inputs)
required_evidence:
  - test_output
  - lrh_validate
artifacts_expected:
  - src/lrh/sessions_workflow.py
  - src/lrh/cli/main.py
  - tests/sessions_workflow_test.py
  - PROMPTS.md
---

# WI-EXEC-SESSIONS-DISCOVERY: Implement lrh sessions discover and lrh sessions link commands

## Summary

Stage 3 of `PROP-LRH-EXECUTION-SESSIONS`. Adds two new CLI commands —
`lrh sessions discover` and `lrh sessions link` — that inventory local
Claude Code session transcripts and attach a validated `session_transcript`
reference to an execution record, without requiring the user to hand-craft
the pointer.

## Problem / Context

`PROP-LRH-EXECUTION-SESSIONS` §"Design" defines Stage 3 as:

- `lrh sessions discover [--project-root .]` — scan
  `~/.claude/projects/<project-slug>/` for JSONL files and list sessions
  with timestamps, approximate sizes, and any linked execution records.
- `lrh sessions link --session <id> --execution <execution-id>` — add
  `session_transcript` to an existing execution record.

That text predates a finding from this session's later work (PR #409,
2026-07-23): Claude.app sessions have **two** distinct identifiers — a
**host session id** (`local_<uuid>`, the durable app-level key surfaced by
View > Copy URL) and a **child SDK session id** (the UUID that names the
local JSONL file). They coincide only sometimes; on resumed or continued
sessions they diverge. The canonical `session_transcript` grammar
(2026-07-23 decision-log entry, `<backend>:<id>` scalar or sequence, plus
`pending`/`none` sentinels) stores the **host** id, not the child id.

A literal implementation of the original Stage 3 text — scan JSONL
filenames and write them straight into `session_transcript` — would write
child ids into a field whose grammar expects host ids, reintroducing the
exact confusion PR #409 and PR #431 (`WI-CLOSEOUT-SESSION-SOURCING`) fixed
for `/lrh-closeout`. This work item's scope is written to avoid that: local
discovery surfaces child ids for human review, but `link` only accepts
values already in the canonical grammar.

There is also no reliable local-only method to map a child id to its host
id — this session's investigation into the closeout skill found no on-disk
correlation guarantee between the two (a session's host id can be listed by
the app with no matching local JSONL file at all). `link` is therefore
necessarily a manual/confirm-driven tool for local records, not an
automated resolver — that limitation is accepted here rather than solved.

**Prior-art check (2026-07-29):**

- *Duplication search* — grepped `src/lrh/` for any existing `sessions`
  command or module; none exists. No CLI subcommand named `sessions` is
  registered in `src/lrh/cli/main.py`.
- *Demand search* — `WI-CLOSEOUT-SESSION-SOURCING` (PR #431, resolved)
  explicitly lists `implement_session_discovery` and
  `implement_lrh_sessions_command` in its own `forbidden_actions`,
  deferring exactly this scope here. The proposal-status update in PR #433
  named `WI-EXEC-SESSIONS-DISCOVERY` as the placeholder id for this work.
  No duplicate or existing backlog entry found beyond these explicit
  deferrals.

## Scope

- New module `src/lrh/sessions_workflow.py` (mirrors the existing
  `src/lrh/prompt_workflow.py` pattern) implementing `discover` and `link`.
- Wire a `"sessions"` case into `src/lrh/cli/main.py`'s command dispatch,
  alongside the existing `"prompt"` case.
- `discover` is read-only and advisory. `link` writes `session_transcript`
  on a named execution record, gated by grammar validation.
- No changes to `/lrh-closeout` — its Step 3 (host-id-first resolution) is
  already backend-aware per PR #431 and is out of scope here.
- No network or session-management MCP tool calls — this is a local
  filesystem utility, complementary to closeout's live `list_sessions`
  path, not a replacement for it.

## Required Changes

### `src/lrh/sessions_workflow.py` (new)

- `discover(project_root)`: derive the project-path slug (`/` and `_` to
  `-`), list `~/.claude/projects/<slug>/*.jsonl`, and for each file report
  the child id (filename stem), approximate size, and mtime. Cross-reference
  `project/executions/**/*.md` for any record whose `session_transcript`
  already contains that child id as a substring, and flag it. Output must
  visibly label the reported id as the child SDK id, not a ready-to-use
  `session_transcript` value.
- `link(session_id, execution_id, project_root)`: locate the named
  execution record; validate `session_id` against the `<backend>:<id>`
  grammar or the `pending`/`none` sentinels (reuse the validation logic
  from `WI-EXEC-SESSIONS-SCHEMA`'s `lrh validate` checks rather than
  duplicating it); reject and explain if the value is a bare child id or
  otherwise malformed; on success, write `session_transcript` via the same
  update path `lrh prompt update-execution` uses.

### `src/lrh/cli/main.py`

- Add a `"sessions"` subcommand with `discover` and `link` subcommands,
  following the existing `"prompt"` dispatch pattern.

### Tests

- `discover`: empty project directory, one or more sessions found,
  malformed/non-UUID filenames ignored gracefully.
- `link`: grammar-valid id accepted and written; bare child id rejected
  with an explanatory message; `pending`/`none` accepted; unknown
  `execution_id` reported as an error, not a silent no-op.

### `PROMPTS.md`

- Add `lrh sessions discover`/`lrh sessions link` to the "Installed CLI
  commands" section, cross-referencing the "Claude.app execution sessions"
  section added in PR #432.

## Non-Goals

- No changes to `/lrh-closeout` Step 3 — already backend-aware (PR #431).
- No network or session-management MCP tool integration.
- No automatic child-id-to-host-id resolution — no reliable local method
  exists; `link` requires the caller to supply an already-valid pointer.
- No `lrh validate` changes — reuse `WI-EXEC-SESSIONS-SCHEMA`'s existing
  grammar-check logic rather than adding new validator rules.

## Acceptance Criteria

- `lrh sessions discover [--project-root .]` scans
  `~/.claude/projects/<project-slug>/` and lists local session JSONL files
  with their child SDK id, approximate size, and mtime, plus any execution
  record whose `session_transcript` already references that id.
- `discover` output explicitly labels ids as the child SDK id and does not
  suggest writing them directly into `session_transcript`.
- `lrh sessions link --session <id> --execution <execution-id>` writes
  `session_transcript` on the named record only when given a value already
  conforming to the `<backend>:<id>` grammar or a `pending`/`none`
  sentinel — it rejects a bare discovered child id.
- Both commands are local-filesystem-only, with no session-management MCP
  tool dependency.
- `lrh validate` passes with 0 errors; new tests cover the discover and
  link cases listed under Required Changes → Tests.

## Validation

- `scripts/test`
- `lrh validate`
- Manual: run `lrh sessions discover` against a real
  `~/.claude/projects/<slug>/` directory and confirm output lists sessions
  without claiming any are ready-to-use `session_transcript` values; run
  `lrh sessions link --session bareid --execution <id>` and confirm it is
  rejected with an explanation rather than written silently.

## Risk Notes

Medium risk on the Python side: `discover`'s cross-reference step must
correctly parse execution-record frontmatter without accidentally matching
substrings across unrelated records (a partial UUID collision is
astronomically unlikely but the matching logic should still anchor on the
full id, not a loose substring search). The core limitation — no reliable
local child-to-host id mapping — is a deliberate scope boundary, not a bug
to work around silently; `link`'s grammar-only validation keeps that
limitation visible to the user rather than papered over.
