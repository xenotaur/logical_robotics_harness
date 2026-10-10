---
id: WS-LRH-SESSION-DEEP-LINKING
kind: planning_node
title: "Deep links to agent sessions"
status: proposed
stage: assessed
origin: ad_hoc
parent_id: null
children: []
summary: "Turn LRH session pointers (claude-app:, codex-app:) into clickable deep links from one shared route definition, and let the LRH Console open them through an allowlisted handoff without loosening its http(s)-only link rules."
related_focus: []
related_roadmap: []
related_design:
  - "project/design/backlog.md"
  - "docs/reference/desktop-server-protocol.md"
work_items:
  - WI-LRH-SESSION-DEEPLINK-HELPER
  - WI-LRH-CONSOLE-DEEPLINK-HANDOFF
exit_criteria:
  - "One shared route definition (src/lrh/conversations/session_links.json) lists each supported vendor's pointer prefix and link shape plus accept and reject test vectors; the Python builder and the Rust allowlist both read it, and both test suites run the same vectors."
  - "A pure helper maps a session pointer to a deep link for the verified vendors (Claude and Codex) and returns None for unknown or malformed pointers, with unit tests."
  - "At least one real consumer calls the helper, so a broken route is noticed."
  - "Clicking an allowlisted claude:// or codex:// link in the LRH Console opens the vendor app, and every other non-http(s) scheme is still refused."
  - "browser.rs validate_url and shell.rs is_external_link are unchanged in behaviour, and the Rust tests cover look-alike hosts and rejected schemes."
  - "The undocumented claude.ai/epitaxy route, the verified-by-hand status of the Codex route, and the unknown Antigravity route are recorded in the docs."
---

# Deep links to agent sessions

## Purpose

LRH records which agent session worked on an item as a `scheme:identifier`
pointer such as `claude-app:<host-uuid-stem>`, but nothing turns that into a
way to open the session. This workstream adds that: a small link-building
helper in Python and a tightly allowlisted handoff in the Console's Tauri
shell. Deep linking is treated as infrastructure, separate from any feature
that displays or records links.

## Scope

- One shared route definition, `src/lrh/conversations/session_links.json`, that both the Python builder and the Rust
  allowlist read, with shared accept and reject test vectors.
- A pure Python helper, `lrh.conversations.deeplink.link_for(pointer)`, that
  returns a deep link or None, plus one real consumer that exercises it.
- A Rust handoff in `apps/desktop/src-tauri` that opens only allowlisted
  session links through the same fixed per-platform opener the browser handoff uses.
- Documenting which routes are verified and which are unknown.

## Prior Art Check

### Duplication search
- In-repo: No existing implementation found. Related: project/design/backlog.md (Codex Copy Deeplink note, thread-id recovery only)
- Sibling repos: None identified
- External libraries: None identified
- Recommendation: Proceed

### Demand search
- Work items: None found
- Proposals: None found
- Backlog: Found: "Reduce Codex export friction across session setup, installation, and guidance" (touches codex://threads/<UUID>; not satisfied by this work)
- Recommendation: No action

## Work Items

- **WI-LRH-SESSION-DEEPLINK-HELPER** — Add the shared route definition, `link_for(pointer)` and one consumer.
- **WI-LRH-CONSOLE-DEEPLINK-HANDOFF** — Add the allowlisted session-link handoff to the Console shell, built from the shared route definition (depends on the helper item for that file).

## Exit Criteria

- One shared route definition (`src/lrh/conversations/session_links.json`) lists each supported vendor's pointer prefix and link shape plus accept and reject test vectors; the Python builder and the Rust allowlist both read it, and both test suites run the same vectors.
- A pure helper maps a session pointer to a deep link for the verified vendors (Claude and Codex) and returns None for unknown or malformed pointers, with unit tests.
- At least one real consumer calls the helper, so a broken route is noticed.
- Clicking an allowlisted `claude://` or `codex://` link in the LRH Console opens the vendor app, and every other non-http(s) scheme is still refused.
- `browser.rs` `validate_url` and `shell.rs` `is_external_link` are unchanged in behaviour, and the Rust tests cover look-alike hosts and rejected schemes.
- The undocumented `claude.ai/epitaxy` route, the verified-by-hand status of the Codex route, and the unknown Antigravity route are recorded in the docs.

## Non-Goals

- Does not add a thread abstraction or any registry of sessions.
- Does not change `/lrh-implement` or other skills to register or record links early.
- Does not render links on work-item, workstream or design pages in the Console.
- Does not make a link route stable: `claude://claude.ai/epitaxy/...` is undocumented and may change.
- Does not support Claude CLI sessions, which have no URL scheme, or cloud sessions, whose route is unverified.

## Open Questions

- Codex route: resolved. `open "codex://threads/01a032cd-cef2-73c0-9714-b61b36ae4513"` was tested by hand and opens the thread.
- Does Antigravity have a conversation route? Its `antigravity://` scheme is registered, but no route was found.
- Route sharing: resolved. One JSON definition in the Python package (`src/lrh/conversations/session_links.json`) is read by Python at run time and by Rust through `include_str!`; it has to live under `src/` because the sdist excludes `apps/`.
- Which focus and roadmap entries should this link to?
