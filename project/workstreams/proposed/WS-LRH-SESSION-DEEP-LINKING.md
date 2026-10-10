---
id: WS-LRH-SESSION-DEEP-LINKING
kind: planning_node
title: "Deep links to agent sessions"
status: proposed
stage: assessed
origin: ad_hoc
parent_id: null
children: []
summary: "Turn LRH session pointers (claude-app:, codex-app:) into clickable deep links, and let the LRH Console open them through an allowlisted handoff without loosening its http(s)-only link rules."
related_focus: []
related_roadmap: []
related_design:
  - "project/design/backlog.md"
  - "docs/reference/desktop-server-protocol.md"
work_items:
  - WI-LRH-SESSION-DEEPLINK-HELPER
  - WI-LRH-CONSOLE-DEEPLINK-HANDOFF
exit_criteria:
  - "A pure helper maps a session pointer to a deep link for the verified vendors and returns None for unknown or malformed pointers, with unit tests."
  - "At least one real consumer calls the helper, so a broken route is noticed."
  - "Clicking an allowlisted claude:// or codex:// link in the LRH Console opens the vendor app, and every other non-http(s) scheme is still refused."
  - "browser.rs validate_url and shell.rs is_external_link are unchanged in behaviour, and the Rust tests cover look-alike hosts and rejected schemes."
  - "The undocumented claude.ai/epitaxy route and the unverified Codex and Antigravity routes are recorded as best-effort in the docs."
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

- A pure Python helper, `lrh.conversations.deeplink.link_for(pointer)`, that
  returns a deep link or None, plus one real consumer that exercises it.
- A Rust handoff in `apps/desktop/src-tauri` that opens only allowlisted
  session links through `/usr/bin/open`.
- Documenting which routes are verified, documented-but-unverified, and unknown.

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

- **WI-LRH-SESSION-DEEPLINK-HELPER** — Add `link_for(pointer)` and one consumer.
- **WI-LRH-CONSOLE-DEEPLINK-HANDOFF** — Add the allowlisted session-link handoff to the Console shell.

## Exit Criteria

- A pure helper maps a session pointer to a deep link for the verified vendors and returns None for unknown or malformed pointers, with unit tests.
- At least one real consumer calls the helper, so a broken route is noticed.
- Clicking an allowlisted `claude://` or `codex://` link in the LRH Console opens the vendor app, and every other non-http(s) scheme is still refused.
- `browser.rs` `validate_url` and `shell.rs` `is_external_link` are unchanged in behaviour, and the Rust tests cover look-alike hosts and rejected schemes.
- The undocumented `claude.ai/epitaxy` route and the unverified Codex and Antigravity routes are recorded as best-effort in the docs.

## Non-Goals

- Does not add a thread abstraction or any registry of sessions.
- Does not change `/lrh-implement` or other skills to register or record links early.
- Does not render links on work-item, workstream or design pages in the Console.
- Does not make a link route stable: `claude://claude.ai/epitaxy/...` is undocumented and may change.
- Does not support Claude CLI sessions, which have no URL scheme, or cloud sessions, whose route is unverified.

## Open Questions

- Does `codex://threads/<UUID>` open a thread in an installed Codex app? (Documented in the backlog, not yet tested.)
- Does Antigravity have a conversation route? Its `antigravity://` scheme is registered, but no route was found.
- Should the verified route be defined once and shared between the Python builder and the Rust allowlist?
- Which focus and roadmap entries should this link to?
