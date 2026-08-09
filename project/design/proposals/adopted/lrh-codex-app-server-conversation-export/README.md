# LRH Codex App-Server Conversation Export

This proposal set captures the follow-on design for turning the Codex
app-server spike findings into a production LRH current-session exporter.

## Status summary

- `00_proposal.md` — umbrella proposal. Status: `proposed` / `not_started`
  (planning/control-plane only; no CLI, app-server adapter, or skill wrapper
  implementation in this proposal PR)

## What this proposal set covers

This proposal set extends the adopted Codex conversation exporter design with a
production source route backed by Codex app-server `thread/read`. It keeps the
existing private, non-authoritative export artifact contract and scopes the
first implementation slice to `lrh conversation export-codex-thread`, with
`/lrh-codex-export` and target-aware `/lrh-export` wrappers deferred until the
CLI adapter has been implemented and dogfooded.

## Reading order

1. `00_proposal.md` — governing follow-on proposal for
   `lrh conversation export-codex-thread` and the `/lrh-codex-export` skill
   wrapper.

## Canonical-document touchpoints

If adopted and implemented later, this proposal would likely inform future
updates to:

- `docs/reference/cli/conversation.md` — CLI reference for
  `lrh conversation export-codex-thread`, private raw JSON capture behavior,
  and inspector compatibility.
- `src/lrh/conversations/` — production app-server adapter, rendering, manifest,
  and sensitivity-scanning integration.
- `src/lrh/cli/main.py` — command registration for
  `lrh conversation export-codex-thread`.
- `src/lrh/skills/` and installed agent skill targets — later
  `/lrh-codex-export` and target-aware `/lrh-export` wrappers.
- `project/workstreams/proposed/WS-LRH-CODEX-APP-SERVER-EXPORT.md` and
  `project/work_items/resolved/WI-CODEX-CONVERSATION-EXPORT-APP-SERVER.md` —
  the planning artifacts that sequence implementation.
- `experimental/save_codex_threads/findings.md` — spike evidence that grounds
  the app-server feasibility decision; this remains evidence only, not a
  production dependency.

No canonical document (`project/design/design.md`,
`project/design/architecture.md`, or `project/design/repository_spec.md`) is
edited by this proposal. Adoption may later fold stable decisions into one of
those documents.
