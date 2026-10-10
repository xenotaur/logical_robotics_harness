---
resolution: null
blocked_reason: null
blocked: false
id: WI-LRH-SESSION-DEEPLINK-HELPER
title: "Add link_for(pointer) deep-link helper and an lrh sessions deeplink command"
type: deliverable
status: proposed
owner: anthony
contributors:
  - anthony
assigned_agents: []
related_focus: []
related_roadmap: []
related_workstreams:
  - WS-LRH-SESSION-DEEP-LINKING
related_design:
  - project/design/backlog.md
depends_on: []
blocked_by: []
expected_actions:
  - create_file
  - edit_file
  - run_tests
  - write_docs
  - add_cli_command
forbidden_actions:
  - force_push
  - delete_branch
  - merge_pr
  - export_transcript_content
  - print_transcript_text
acceptance:
  - "lrh.conversations.deeplink.link_for(pointer) returns claude://claude.ai/epitaxy/local_<stem> for claude-app:<stem> and codex://threads/<id> for codex-app:<id>"
  - "link_for returns None for antigravity-app:, pending, none, unknown schemes, empty or malformed pointers, and claude-app child ids that are not host ids, and never guesses a link"
  - "link_for re-adds the local_ prefix that prompt_workflow_sessions.py strips, and accepts a pointer that already carries it without doubling it"
  - "lrh sessions deeplink <pointer> prints the link and exits 0, or exits 1 with a message when there is none"
  - "Docs state which routes are verified, documented-but-unverified, and unknown"
  - "lrh validate reports 0 errors and scripts/test, scripts/lint and scripts/format --check --diff pass"
required_evidence:
  - manual_review
  - lrh_validate
  - test_output
artifacts_expected:
  - src/lrh/conversations/deeplink.py
  - tests/conversations_tests/deeplink_test.py
  - src/lrh/sessions_workflow.py
  - docs/conversations/
---

# WI-LRH-SESSION-DEEPLINK-HELPER: Add link_for(pointer) and a proving consumer

## Summary

Add a pure helper, `lrh.conversations.deeplink.link_for(pointer)`, that turns an
LRH session pointer into a clickable deep link or `None`, plus a small
`lrh sessions deeplink` command that uses it.

## Problem / Context

LRH stores `claude-app:` and `codex-app:` pointers (`claude_session.py:16`,
`codex_session.py:13`), but nothing says how to open them. The Claude route
`claude://claude.ai/epitaxy/local_<uuid>` was verified by hand with `open`; it is
undocumented, so it may change. The Codex route `codex://threads/<id>` is
documented in `project/design/backlog.md:1577` but untested. No Antigravity
conversation route was found. The helper must be pure and conservative so every
later consumer (the Console, skills, docs) shares one definition.
`prompt_workflow_sessions.py:241` strips `local_` when reading a pointer, so the
builder has to add it back.

### Duplication search
- In-repo: No existing implementation found. Related: project/design/backlog.md (Codex Copy Deeplink note)
- Sibling repos: None identified
- External libraries: None identified
- Recommendation: Proceed

### Demand search
- Work items: None found
- Proposals: None found
- Backlog: Found: "Reduce Codex export friction across session setup, installation, and guidance" (different goal; not satisfied)
- Recommendation: No action

## Scope

- A pure `link_for(pointer)` helper with unit tests.
- One consumer, the `lrh sessions deeplink` command, so a broken route is noticed.
- Documentation of verified, unverified and unknown routes.

## Required Changes

1. Create `src/lrh/conversations/deeplink.py` with `link_for(pointer: str) -> str | None`, reusing the prefix constants from `claude_session.py` and `codex_session.py`.
2. Map `claude-app:<stem>` to `claude://claude.ai/epitaxy/local_<stem>` (stem validated as a UUID; `local_` re-added, never doubled), and `codex-app:<id>` to `codex://threads/<id>` (id validated as a UUID).
3. Return `None` for `antigravity-app:`, `pending`, `none`, unknown schemes, and empty or malformed values. Never raise on bad input.
4. Create `tests/conversations_tests/deeplink_test.py` covering the `local_` round trip, malformed values, unknown schemes, `pending`/`none`, child ids not yet promoted to a host id, and Antigravity.
5. Add `lrh sessions deeplink <pointer>` in `src/lrh/sessions_workflow.py`: print the link, exit 0, or print a message to stderr and exit 1.
6. Document the three route statuses (verified, documented-but-unverified, unknown) under `docs/conversations/`, and note that the `epitaxy` route is undocumented and best-effort.

## Non-Goals

- Do not add a thread abstraction or session registry.
- Do not change `/lrh-implement` or other skills to record links early.
- Do not render links in the Console; that is `WI-LRH-CONSOLE-DEEPLINK-HANDOFF` and later work.
- Do not store links in execution records; derive them at display time.
- Do not support Claude CLI or cloud sessions.

## Acceptance Criteria

- `link_for` returns the right link for `claude-app:` and `codex-app:` pointers.
- `link_for` returns `None` for Antigravity, `pending`, `none`, unknown and malformed pointers, and never guesses.
- The `local_` prefix is re-added exactly once.
- `lrh sessions deeplink <pointer>` prints the link, or exits 1 with a message.
- The docs record which routes are verified, unverified and unknown.
- `lrh validate` reports 0 errors, and tests, lint and format checks pass.

## Validation

- `lrh validate`
- `scripts/format --check --diff`
- `scripts/lint`
- `scripts/test`
- `lrh sessions deeplink claude-app:a6e3e7d1-6dca-4a75-999f-73b646ceb1fa`

## Risk Notes

- The Claude `epitaxy` route is undocumented. Keep it in one constant and say so in the docs.
