---
id: WS-LRH-CODEX-APP-SERVER-EXPORT
kind: planning_node
title: Codex App-Server Conversation Export
status: resolved
stage: closed
origin: follow_up
summary: >
  Coordinate implementation and dogfooding of LRH's Codex app-server current
  session exporter, starting with `lrh conversation export-codex-thread` and then
  layering Codex skill wrappers on top.
related_focus: []
related_roadmap: []
related_design:
  - project/design/proposals/proposed/lrh-codex-app-server-conversation-export/00_proposal.md
  - project/design/proposals/adopted/lrh-codex-conversation-exporter/00_proposal.md
  - project/workstreams/resolved/WS-LRH-CODEX-CONVERSATION-EXPORTER.md
  - experimental/save_codex_threads/findings.md
  - experimental/save_codex_threads/plan.md
work_items:
  - WI-CODEX-CONVERSATION-EXPORT-APP-SERVER
  - WI-CODEX-CONVERSATION-EXPORT-SKILL
exit_criteria:
  - `lrh conversation export-codex-thread` can export a real Codex thread through the app-server route into private raw JSON plus manifest-backed Markdown
  - generated Markdown exports pass `lrh conversation inspect-export` and preserve private, non-authoritative metadata
  - unit tests cover fake app-server handshake, thread-read success, app-server errors, malformed responses, timeout or exit behavior, renderer mappings, warnings, and manifest statistics
  - docs explain CLI usage, privacy boundaries, raw artifact handling, residual trust warnings, and dogfood workflow
  - at least one private real-session dogfood export validates the app-server path without committing raw transcript data
---

## Purpose

This workstream coordinates the follow-on work needed to turn the Codex
app-server spike into a durable LRH export capability. The previous Codex
conversation exporter workstream intentionally built the manifest, file adapter,
inspector, and safe viewer first. This workstream adds the missing
current-session capture path now that the spike demonstrated both model-visible
and standalone app-server access to real Codex task data.

## Scope

- Implement a production LRH CLI/library adapter for Codex app-server
  `thread/read` capture.
- Preserve the existing private-by-default, non-authoritative
  `ConversationExportManifest` artifact contract.
- Keep raw app-server JSON captures private and metadata-inspectable.
- Dogfood the exporter with real Codex sessions without committing raw transcript
  files.
- Defer target-aware `/lrh-export` until `/lrh-codex-export` can wrap a working
  CLI command.

## Prior Art Check

### Duplication search

- In-repo: Related exporter infrastructure exists in
  `src/lrh/conversations/`, `docs/reference/cli/conversation.md`, and
  `project/workstreams/resolved/WS-LRH-CODEX-CONVERSATION-EXPORTER.md`. No
  production app-server export workstream exists. The spike helper under
  `experimental/save_codex_threads/` is explicitly provisional and must not
  become a production dependency.
- Sibling repos: No sibling repository was identified as already implementing
  LRH-specific Codex app-server exports.
- External libraries: No external library was identified that provides the LRH
  manifest, privacy, inspection, and promotion-boundary behavior required here.
- Recommendation: Proceed with a focused follow-on workstream that promotes the
  spike finding into reviewed package code.

### Demand search

- Work items: No existing proposed work item was found for
  `WI-CODEX-CONVERSATION-EXPORT-APP-SERVER`; the spike findings recommend that
  id and scope.
- Proposals: Found the adopted Codex conversation exporter proposal and the new
  follow-on app-server proposal.
- Backlog: Found related backlog entries for experimental-code linkage guardrails
  and Codex executable trust/signature investigation.
- Recommendation: Link this workstream to the new proposal and keep backlog
  items as related follow-ups rather than folding them into the first
  implementation item.

## Work Items

- **WI-CODEX-CONVERSATION-EXPORT-APP-SERVER** — implement
  `lrh conversation export-codex-thread` using Codex app-server `thread/read`,
  private raw JSON capture, manifest-backed Markdown rendering, metadata-only
  terminal output, docs, and focused tests with fake app-server boundaries.

Expected follow-on items after the first implementation lands:

- **WI-CODEX-CONVERSATION-EXPORT-SKILL** — implement `/lrh-codex-export` as a
  thin workflow wrapper around the CLI command.
- **Target-aware export wrapper** — design and implement `/lrh-export` only after
  the Codex-specific path has been dogfooded.
- **Dogfood and hardening** — run real private exports against this and other
  sessions, record findings, and fix gaps before using exported artifacts as
  input to the broader conversation-storage dogfood plan.

## Exit Criteria

- `lrh conversation export-codex-thread` can export a real Codex thread through
  the app-server route into private raw JSON plus manifest-backed Markdown.
- Generated Markdown exports pass `lrh conversation inspect-export` and preserve
  private, non-authoritative metadata.
- Unit tests cover fake app-server handshake, thread-read success, app-server
  errors, malformed responses, timeout or exit behavior, renderer mappings,
  warnings, and manifest statistics.
- Docs explain CLI usage, privacy boundaries, raw artifact handling, residual
  trust warnings, and dogfood workflow.
- At least one private real-session dogfood export validates the app-server path
  without committing raw transcript data.

## Non-Goals

- Does not reopen or replace the resolved file-based exporter workstream.
- Does not import from or depend on `experimental/save_codex_threads/`.
- Does not scrape undocumented Codex app storage internals.
- Does not make raw transcripts authoritative LRH project state.
- Does not implement automatic promotion from transcripts to LRH control-plane
  artifacts.
- Does not implement target-aware `/lrh-export` before the Codex-specific path is
  working.

## Relationship to Design

- Governing follow-on proposal:
  `project/design/proposals/proposed/lrh-codex-app-server-conversation-export/00_proposal.md`
- Prior adopted exporter proposal:
  `project/design/proposals/adopted/lrh-codex-conversation-exporter/00_proposal.md`
- Prior resolved workstream:
  `project/workstreams/resolved/WS-LRH-CODEX-CONVERSATION-EXPORTER.md`
- Spike evidence:
  `experimental/save_codex_threads/findings.md`

## Open Questions

- Should the first skill wrapper be named `/lrh-codex-export`,
  `/lrh-export-codex`, or both with one alias?
- Should private archive-root defaults belong in the CLI command, the skill
  wrapper, or both?
- Should the experimental paged adapter become a second work item in this
  workstream after the stable `thread/read` path lands, or wait until large
  sessions demonstrate a concrete need?
