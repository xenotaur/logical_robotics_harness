---
resolution: null
blocked_reason: null
blocked: false
id: WI-LRH-CONSOLE-DEEPLINK-HANDOFF
title: "Add an allowlisted session deep-link handoff to the LRH Console shell"
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
  - docs/reference/desktop-server-protocol.md
depends_on: []
blocked_by: []
expected_actions:
  - edit_file
  - run_tests
  - write_docs
forbidden_actions:
  - force_push
  - delete_branch
  - merge_pr
  - add_tauri_capability
  - loosen_validate_url
acceptance:
  - "A new validate_session_link accepts only claude://claude.ai/epitaxy/local_<uuid> and codex://threads/<uuid>, by exact scheme, host, path shape and UUID format, with no credentials, query or fragment"
  - "An allowlisted link clicked in the Console is opened with /usr/bin/open using fixed arguments, behind the same one-per-second rate limit"
  - "validate_url and is_external_link behave exactly as before: other non-http(s) schemes, look-alike hosts, extra path segments and javascript: links are still refused"
  - "capabilities/main-window.json still grants no permissions, and the CSP is unchanged"
  - "A failed handoff is recorded in LinkHandoff's last result"
  - "Rust tests cover accepted links and each refusal class, and the desktop test tier passes"
required_evidence:
  - manual_review
  - lrh_validate
  - test_output
artifacts_expected:
  - apps/desktop/src-tauri/src/browser.rs
  - apps/desktop/src-tauri/src/shell.rs
  - apps/desktop/src-tauri/tests/capability_boundaries_test.rs
  - docs/reference/desktop-server-protocol.md
---

# WI-LRH-CONSOLE-DEEPLINK-HANDOFF: Add an allowlisted session deep-link handoff

## Summary

Let the LRH Console open Claude and Codex session links through a separate,
tightly allowlisted handoff in the Tauri shell, without loosening the
http(s)-only browser handoff.

## Problem / Context

Today a `claude://` click in the Console does nothing. `on_navigation`
(`shell.rs:724`) cancels the navigation and calls `links.offer(url)`
(`shell.rs:740`), and `offer` (`shell.rs:495`) proceeds only if `is_external_link`
(`shell.rs:448`) passes. That requires an http(s) URL, and `validate_url`
(`browser.rs:39`) rejects every other scheme. The restriction is deliberate:
page content must not be able to launch arbitrary apps, and the main window has no
app commands (`capabilities/main-window.json`). The handoff therefore needs its own
exact-shape allowlist and the same fixed-argument `/usr/bin/open` launch used at
`browser.rs:116`.

### Duplication search
- In-repo: No existing implementation found. Related: apps/desktop/src-tauri/src/browser.rs (http(s) handoff)
- Sibling repos: None identified
- External libraries: None identified
- Recommendation: Proceed

### Demand search
- Work items: None found
- Proposals: None found
- Backlog: No matching entries
- Recommendation: No action

## Scope

- Add `validate_session_link` and its launch path in `browser.rs`.
- Route allowlisted links in `shell.rs` after `is_external_link` fails.
- Tests for accepted and refused links.

## Required Changes

1. In `browser.rs`, add `validate_session_link(url: &Url) -> Result<(), String>` accepting exactly `claude://claude.ai/epitaxy/local_<uuid>` and `codex://threads/<uuid>` and nothing else (no credentials, query or fragment; strict UUID format; no extra path segments).
2. Add a launch function that runs `/usr/bin/open <url>` with fixed arguments and no shell, following the pattern at `browser.rs:116`.
3. In `shell.rs`, extend `LinkHandoff::offer` so a URL that fails `is_external_link` but passes `validate_session_link` is handed off, using the same rate limiter and the same `last` result.
4. Leave `validate_url`, `is_external_link`, `new_window_response`, the CSP and `capabilities/main-window.json` unchanged.
5. Add Rust unit tests in `browser.rs` and `shell.rs` for accepted links and for look-alike hosts, extra path segments, query strings, credentials, non-UUID ids, `javascript:` and other schemes, and a test in `tests/capability_boundaries_test.rs` that the main window still gets no app commands.
6. Note the allowlisted schemes and the best-effort status of the `epitaxy` route in `docs/reference/desktop-server-protocol.md`.

## Non-Goals

- Do not loosen `validate_url` or `is_external_link`, and do not add a Tauri capability.
- Do not open any other custom scheme.
- Do not render session links on work-item, workstream or design pages.
- Do not build the Python link helper; that is `WI-LRH-SESSION-DEEPLINK-HELPER`.

## Acceptance Criteria

- Allowlisted Claude and Codex links open the vendor app, rate-limited to one per second.
- Every refusal class above is rejected, and the existing http(s) behaviour is unchanged.
- The main window still has an empty permission list and the CSP is unchanged.
- A failed `open` is visible in `LinkHandoff`'s last result.
- `lrh validate` reports 0 errors, and the desktop and Python checks pass.

## Validation

- `lrh validate`
- `apps/desktop/scripts/run fmt --check`
- `apps/desktop/scripts/run lint`
- `apps/desktop/scripts/run test`
- `scripts/test`

## Risk Notes

- The allowlist and the Python builder must agree on the route. Open Question: define it once, or cross-check it with a test.
- A real click needs a branch build of the Console app; the maintainer cannot build PR branches, so bundle and launch it before asking for a manual check.
