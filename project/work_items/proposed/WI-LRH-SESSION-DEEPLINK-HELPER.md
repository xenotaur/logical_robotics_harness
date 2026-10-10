---
resolution: null
blocked_reason: null
blocked: false
id: WI-LRH-SESSION-DEEPLINK-HELPER
title: "Add a shared session-link route definition, link_for(pointer) and an lrh sessions deeplink command"
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
  - "src/lrh/conversations/session_links.json is the single route definition: per vendor it gives the pointer prefix, link scheme, host, path template, id shape, and an optional id prefix, plus accept and reject test vectors, and it ships in the wheel"
  - "lrh.conversations.deeplink.link_for(pointer) reads that definition and returns claude://claude.ai/epitaxy/local_<stem> for claude-app:<stem> and codex://threads/<id> for codex-app:<id>"
  - "link_for returns None for antigravity-app:, pending, none, unknown schemes, empty or malformed pointers, and claude-app child ids that are not host ids, and never guesses a link"
  - "link_for re-adds the local_ prefix that prompt_workflow_sessions.py strips, and accepts a pointer that already carries it without doubling it"
  - "lrh sessions deeplink <pointer> prints the link and exits 0, or exits 1 with a message when there is none"
  - "Docs state which routes are verified (Claude, Codex) and which are unknown (Antigravity), and that the Claude epitaxy route is undocumented"
  - "lrh validate reports 0 errors and scripts/test, scripts/lint and scripts/format --check --diff pass"
required_evidence:
  - manual_review
  - lrh_validate
  - test_output
artifacts_expected:
  - src/lrh/conversations/session_links.json
  - src/lrh/conversations/deeplink.py
  - pyproject.toml
  - tests/conversations_tests/deeplink_test.py
  - src/lrh/sessions_workflow.py
  - docs/conversations/
---

# WI-LRH-SESSION-DEEPLINK-HELPER: Add the shared route definition, link_for(pointer) and a proving consumer

## Summary

Add one shared route definition for session deep links, a pure helper,
`lrh.conversations.deeplink.link_for(pointer)`, that reads it and turns an LRH
session pointer into a clickable deep link or `None`, and a small
`lrh sessions deeplink` command that uses it. `WI-LRH-CONSOLE-DEEPLINK-HANDOFF`
builds its Rust allowlist from the same definition.

## Problem / Context

LRH stores `claude-app:` and `codex-app:` pointers (`claude_session.py:16`,
`codex_session.py:13`), but nothing says how to open them. The Claude route
`claude://claude.ai/epitaxy/local_<uuid>` was verified by hand with `open`; it is
undocumented, so it may change. The Codex route `codex://threads/<id>` is
documented in `project/design/backlog.md:1577` and was also verified by hand with
`open "codex://threads/01a032cd-cef2-73c0-9714-b61b36ae4513"`. No Antigravity
conversation route was found. The Python builder and the Rust allowlist must not
drift, so both read one definition. It lives under `src/lrh/` because the sdist
excludes `apps/` (`MANIFEST.in`, `src/lrh/dev/release_smoke.py`) and the wheel must
carry it. The helper must be pure and conservative so every
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

- The shared route definition file, with accept and reject test vectors.
- A pure `link_for(pointer)` helper that reads it, with unit tests.
- One consumer, the `lrh sessions deeplink` command, so a broken route is noticed.
- Documentation of verified and unknown routes.

## Required Changes

1. Create `src/lrh/conversations/session_links.json`: for each vendor, the pointer prefix, link scheme, host, path template, id shape (UUID), and optional id prefix (`local_` for Claude), plus lists of valid and invalid example links and pointers. Add it to `[tool.setuptools.package-data]` in `pyproject.toml` so the wheel ships it, and keep it free of anything the Rust side cannot parse with `serde_json`.
2. Create `src/lrh/conversations/deeplink.py` with `link_for(pointer: str) -> str | None`, loading that file and checking its pointer prefixes against the constants in `claude_session.py` and `codex_session.py`.
3. Map `claude-app:<stem>` to `claude://claude.ai/epitaxy/local_<stem>` (stem validated as a UUID; `local_` re-added, never doubled), and `codex-app:<id>` to `codex://threads/<id>` (id validated as a UUID).
4. Return `None` for `antigravity-app:`, `pending`, `none`, unknown schemes, and empty or malformed values. Never raise on bad input.
5. Create `tests/conversations_tests/deeplink_test.py` covering the shared test vectors, the `local_` round trip, malformed values, unknown schemes, `pending`/`none`, child ids not yet promoted to a host id, and Antigravity.
6. Add `lrh sessions deeplink <pointer>` in `src/lrh/sessions_workflow.py`: print the link, exit 0, or print a message to stderr and exit 1.
7. Document the route statuses (Claude and Codex verified by hand, Antigravity unknown) under `docs/conversations/`, note that the `epitaxy` route is undocumented and best-effort, and say that the Console allowlist reads the same file.

## Non-Goals

- Do not add a thread abstraction or session registry.
- Do not change `/lrh-implement` or other skills to record links early.
- Do not write any Rust; the Console allowlist is `WI-LRH-CONSOLE-DEEPLINK-HANDOFF`, which reads the file this item creates.
- Do not store links in execution records; derive them at display time.
- Do not support Claude CLI or cloud sessions.

## Acceptance Criteria

- `link_for` returns the right link for `claude-app:` and `codex-app:` pointers.
- `link_for` returns `None` for Antigravity, `pending`, `none`, unknown and malformed pointers, and never guesses.
- The `local_` prefix is re-added exactly once.
- `lrh sessions deeplink <pointer>` prints the link, or exits 1 with a message.
- The shared definition exists, ships in the wheel, and carries accept and reject vectors that the tests run.
- The docs record which routes are verified and which are unknown.
- `lrh validate` reports 0 errors, and tests, lint and format checks pass.

## Validation

- `lrh validate`
- `scripts/format --check --diff`
- `scripts/lint`
- `scripts/test`
- `lrh sessions deeplink claude-app:a6e3e7d1-6dca-4a75-999f-73b646ceb1fa`

## Risk Notes

- The Claude `epitaxy` route is undocumented. It lives only in the shared definition, so a route change is a one-file edit, and the docs say it is best-effort.
- The definition file's format is now an interface between Python and Rust. Keep it small and flat, and add fields only when both sides use them.
