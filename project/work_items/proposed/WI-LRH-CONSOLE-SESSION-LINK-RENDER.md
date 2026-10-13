---
resolution: null
blocked_reason: null
blocked: false
id: WI-LRH-CONSOLE-SESSION-LINK-RENDER
title: "Show execution-record session links on the work-item page and verify a real Console click"
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
  - docs/conversations/session_deep_links.md
  - docs/reference/desktop-server-protocol.md
depends_on:
  - WI-LRH-SESSION-DEEPLINK-HELPER
  - WI-LRH-CONSOLE-DEEPLINK-HANDOFF
blocked_by: []
expected_actions:
  - edit_file
  - create_file
  - run_tests
  - write_docs
forbidden_actions:
  - force_push
  - delete_branch
  - merge_pr
  - add_tauri_capability
  - loosen_validate_url
  - export_transcript_content
  - print_transcript_text
acceptance:
  - "The project work-item page (/project/<project_id>/work-items/<WI-ID>) lists that work item's execution records read-only (execution id, status, PR link, short commit, session pointer), loaded with the existing prompt_workflow_records.load_execution_records, with no new write path"
  - "A session pointer renders as an <a href> only when lrh.conversations.deeplink.link_for returns a link; pending, none, antigravity-app:, unknown and malformed pointers render as escaped plain text with no link; the link is derived at display time and never stored"
  - "Serve's Content-Security-Policy, X-Frame-Options and escaping are unchanged, and a test shows a hostile session_transcript value is escaped, not emitted as markup"
  - "A real click check is recorded as evidence: the branch's Console app is bundled and launched against a fixture project, the owner clicks the rendered link and the vendor app opens, and a non-allowlisted custom-scheme link does nothing"
  - "The docs record that Rust's Url::parse also strips surrounding whitespace and embedded tab, CR and LF (so a padded link validates in Rust while the Python helper rejects the raw text), and Server Details labels the last handoff as a link handoff rather than a browser handoff"
  - "lrh validate reports 0 errors and the Python and desktop test, lint and format checks pass"
required_evidence:
  - manual_review
  - lrh_validate
  - test_output
artifacts_expected:
  - src/lrh/serve.py
  - src/lrh/prompt_workflow_sessions.py
  - tests/cli_tests/serve_test.py
  - apps/desktop/ui/settings.js
  - docs/conversations/session_deep_links.md
  - docs/reference/desktop-server-protocol.md
  - src/lrh/conversations/README.md
  - src/lrh/conversations/deeplink.py
  - project/evidence/
---

# WI-LRH-CONSOLE-SESSION-LINK-RENDER: Show session links on the work-item page and verify a real click

## Summary

Add a read-only "Execution records" section to the project work-item page that renders each
record's session pointer as a deep link, and use it to run the real click check that closes
`WS-LRH-SESSION-DEEP-LINKING`'s exit criterion 4.

## Problem / Context

The Console shell can open allowlisted `claude://` and `codex://` links (PR #833), but no page
renders one, so a real click has never happened. Serve does not show execution records at all:
the work-item detail page (`render_project_work_item_page`, `serve.py:2433`) shows readiness
data only, and nothing mentions `session_transcript`. This item adds the section, links pointers
with `link_for` (PR #822) at display time, and records the click. It follows from the closeout
note of PR #833.

### Duplication search
- In-repo: No existing implementation found (no Serve or UI code references session_transcript or session links). Related: src/lrh/serve.py (work-item page), src/lrh/conversations/deeplink.py
- Sibling repos: None identified
- External libraries: None identified
- Recommendation: Proceed

### Demand search
- Work items: Found: WI-LRH-CONSOLE-DEEPLINK-HANDOFF — "Add an allowlisted session deep-link handoff to the LRH Console shell" (its non-goals explicitly defer rendering to this item)
- Proposals: None found
- Backlog: No matching entries
- Recommendation: No action

## Scope

- A read-only execution-records section on the project work-item page.
- Display-time linking of session pointers, with plain text for everything without a link.
- A recorded real click check, with the two small related corrections below.

## Required Changes

1. In `src/lrh/serve.py`, add an "Execution records" section to `render_project_work_item_page`. Load records with `lrh.prompt_workflow_records.load_execution_records`, keep those whose `work_item` is this item's id, and show execution id, status, PR (an http(s) link), short commit and session pointer. Everything is `html.escape`d; no new route, write path or cache beyond what the page already uses.
2. Resolve each record's pointers through a small public helper in `src/lrh/prompt_workflow_sessions.py` (expose the existing sequence-aware parsing rather than importing its private `_session_transcript_values`), then call `link_for`; emit an `<a href>` only when it returns a link, otherwise escaped plain text.
3. Tests in `tests/cli_tests/serve_test.py`: a record with a Claude pointer and one with a Codex pointer render links; `pending`, `none`, `antigravity-app:`, an unknown scheme and a malformed value render as plain text with no link; a hostile value (quotes, angle brackets, `javascript:`) is escaped; the CSP and `X-Frame-Options` headers are unchanged.
4. Real click check: bundle the branch's Console (`apps/desktop/scripts/run bundle`), launch it against a fixture project containing a work item and an execution record whose pointer is a real, openable `claude-app:` pointer (`launch --workspace <fixture>`), have the owner click the link and confirm the app opens, and confirm a non-allowlisted custom-scheme link does nothing. Record the result in a new note under `project/evidence/`.
5. Documentation: add to `docs/reference/desktop-server-protocol.md`, `docs/conversations/session_deep_links.md`, `src/lrh/conversations/README.md` and the `deeplink.py` docstring that `Url::parse` also strips leading and trailing whitespace and embedded tab, CR and LF.
6. In `apps/desktop/ui/settings.js`, relabel "Last browser handoff" (a session link now reports `vendor_app`) as a link handoff, without changing the `Opened` enum, and check no test pins the old label.

## Non-Goals

- No new Tauri capability, and no change to `validate_url`, `is_external_link` or the routes in `session_links.json`.
- No thread abstraction, and no change to `/lrh-implement` to register links early.
- No Claude CLI or cloud-session links.
- Do not store links in records; derive them at display time.

## Acceptance Criteria

- The work-item page lists the item's execution records read-only, loaded with the existing loader.
- A pointer is a link only when `link_for` returns one; every other value is escaped plain text.
- Serve's CSP, `X-Frame-Options` and escaping are unchanged, with a hostile-value test.
- The real click check is recorded: the owner clicks and the app opens, and a non-allowlisted link does nothing.
- The whitespace/control-character difference is documented and the handoff label is corrected.
- `lrh validate` reports 0 errors, and Python and desktop checks pass.

## Validation

- `lrh validate`
- `scripts/format --check --diff`
- `scripts/lint`
- `scripts/test`
- `apps/desktop/scripts/run fmt --check`
- `apps/desktop/scripts/run lint`
- `apps/desktop/scripts/run test`

## Risk Notes

- Which records belong to a work item is the open design question. This item starts with records whose `work_item` equals the id (the primary and `_CLOSEOUT_NOTE`); review, confirm and self-review records are `AD_HOC` and link to the primary through `rerun_of`, so decide during implementation whether to include them.
- The click check needs a branch build of the app. The owner cannot build PR branches, so the assistant bundles and launches it and asks the owner to click.
- This planning PR takes the base-slug branch, so the implementation run needs a `-impl` suffix; set `rerun_of` on its review and confirm records directly.
