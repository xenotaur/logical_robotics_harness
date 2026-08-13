---
id: PROP-LRH-CODEX-APP-SERVER-CONVERSATION-EXPORT
type: design_proposal
title: LRH Codex App-Server Conversation Export
status: adopted
created_on: 2026-08-07
updated_on: 2026-08-07
implementation_status: implemented
implemented_by:
  - WI-CODEX-CONVERSATION-EXPORT-APP-SERVER
  - WI-CODEX-CONVERSATION-EXPORT-SKILL
supersedes: []
superseded_by: null
related_design:
  - project/design/proposals/adopted/lrh-codex-conversation-exporter/00_proposal.md
  - project/workstreams/resolved/WS-LRH-CODEX-CONVERSATION-EXPORTER.md
  - experimental/save_codex_threads/findings.md
  - experimental/save_codex_threads/plan.md
  - docs/reference/cli/conversation.md
  - project/design/backlog.md
---

## Summary

This proposal extends the adopted Codex conversation exporter design with a
production current-session capture path backed by Codex's app-server
`thread/read` API. LRH should add `lrh conversation export-codex-thread` as the
programmatic adapter and expose `/lrh-codex-export` as the Codex skill wrapper,
while preserving the existing private, non-authoritative conversation artifact
contract.

## Background / Motivation

`PROP-LRH-CODEX-CONVERSATION-EXPORTER` deliberately started with a file-based
adapter and left native/API capture as a later adapter extension. That was the
right first slice: it established the manifest, privacy boundary, inspector, and
viewer before LRH relied on a live Codex integration.

The follow-on spike in `experimental/save_codex_threads/` retired the central
technical feasibility risk. It showed that the current Codex task id is
available in-session, that model-visible Codex thread tools can read real turn
data, and that a normal LRH subprocess can use `codex app-server --listen
stdio://` plus JSON-RPC `thread/read` to fetch the same thread data. It also
showed that direct app storage scraping is unnecessary.

The remaining design question is therefore no longer "can LRH export the
current Codex session?" It is "how should LRH productize the documented
app-server route without weakening the private-by-default, non-authoritative,
metadata-inspectable contract that already landed?"

## Prior Art Check

### Duplication search

- In-repo: Related implementation exists in `src/lrh/conversations/` for
  manifest handling, file-based Codex conversion, inspection, and archive
  viewing. No production `export-codex-thread` command or app-server adapter
  exists. The only app-server reader is the experimental spike helper under
  `experimental/save_codex_threads/`.
- Sibling repos: No sibling repository was identified as already implementing
  LRH-specific Codex app-server conversation export.
- External libraries: No external library was identified that provides LRH's
  required combination of Codex thread capture, LRH manifest rendering,
  authority labeling, sensitivity scanning, inspector compatibility, and
  promotion boundaries.
- Recommendation: Proceed by promoting the spike finding into a production LRH
  adapter rather than importing or depending on the experimental helper.

### Demand search

- Work items: No existing proposed work item was found for
  `WI-CODEX-CONVERSATION-EXPORT-APP-SERVER`; the spike closeout recommended that
  id as the next implementation item.
- Proposals: Found the adopted governing proposal
  `PROP-LRH-CODEX-CONVERSATION-EXPORTER`, whose file-based adapter decision is
  extended by this follow-on proposal.
- Backlog: Found related backlog entries for the experimental-code linkage
  guardrail and Codex executable trust/signature investigation.
- Recommendation: Link this proposal to the adopted exporter proposal, create a
  follow-on workstream, and preserve trust/linkage follow-ups as separate
  design backlog items unless they surface a blocking safety issue.

## Design Decisions

### Decision 1: Source route

Options considered:

- Continue with manual file-based imports only.
- Scrape Codex local storage internals.
- Use the documented Codex app-server stdio route.
- Use only model-visible Codex thread tools from a skill.

Chosen: use the documented app-server stdio route for the production LRH CLI
adapter.

Manual file imports remain useful as a fallback and for non-Codex sources, but
they do not satisfy the current-session exporter goal. Local storage scraping is
unnecessary and too brittle. Model-visible tools are useful for skill UX and
bounded probes, but a production LRH command should be runnable, testable, and
documented outside a single model turn. The app-server route gives LRH that
boundary while avoiding undocumented storage internals.

### Decision 2: Initial app-server method

Options considered:

- Stable `thread/read` with `includeTurns: true`.
- Experimental `thread/turns/list` with `itemsView: full`.
- Experimental summary-only pagination.

Chosen: use stable `thread/read` with `includeTurns: true` for the first
production adapter.

The spike demonstrated that this method returns complete turn data for a real
long Codex task. It is not paged, so very large sessions may need a later
experimental paged adapter, but using the stable complete read first keeps the
initial implementation conservative.

### Decision 3: Artifact contract

Options considered:

- Store only rendered Markdown.
- Store only raw app-server JSON.
- Store private raw JSON plus rendered Markdown with
  `ConversationExportManifest` frontmatter.

Chosen: store private raw JSON as the source artifact and render Markdown using
the existing `ConversationExportManifest` contract.

The raw JSON preserves auditability and source hashing. The Markdown remains the
human review surface. The manifest should record `source_tool: codex`,
`source_adapter: codex_app_server_thread_read`, `source_id` as the Codex thread
id, `source_sha256` as the hash of the raw JSON capture, `privacy: private`,
`authority: non_authoritative_context`, warnings, and transcript statistics.

### Decision 4: CLI and skill split

Options considered:

- Implement only a slash skill.
- Implement only a CLI command.
- Implement a CLI/library adapter first, then a thin Codex skill wrapper.

Chosen: implement the CLI/library adapter first and wrap it with
`/lrh-codex-export`.

The CLI is the durable LRH capability: it is testable with fake app-server
subprocesses, documentable in CLI reference docs, and reusable from future
skills. The skill is the ergonomic current-session entry point: it can default
from `CODEX_THREAD_ID`, choose safe paths, run inspection, and summarize the
result without printing transcript text.

### Decision 5: Safe output posture

Options considered:

- Print transcript content to stdout.
- Write raw captures into the repository by default.
- Require explicit private output paths or archive roots and print metadata only.

Chosen: require explicit private output locations and keep terminal output
metadata-only.

The exporter should never print raw transcript text by default. It should write
raw JSON and Markdown to explicit local paths or a configured private archive
root, preserve sensitivity-scanner warnings, and immediately produce artifacts
that `lrh conversation inspect-export` can validate.

### Decision 6: Trust and experimental risks

Options considered:

- Block implementation until Codex executable trust is fully explained.
- Ignore local trust ambiguity.
- Implement the exporter with manifest warnings and keep trust investigation as
  a separate backlog/design item.

Chosen: proceed with warnings and keep trust investigation separate.

The spike proved the app-server route works but did not fully explain the local
macOS trust/signature behavior. That should not block the first adapter unless a
new safety issue appears, but the exporter should record warnings such as
`codex_trust_state_ambiguous` when diagnostics indicate ambiguity.

## Non-Goals

- Does not scrape `.codex` or ChatGPT desktop private storage internals.
- Does not make raw Codex transcripts authoritative LRH project state.
- Does not automatically promote transcript contents into proposals, work
  items, decisions, evidence, execution records, or status.
- Does not require experimental app-server APIs for the first production
  adapter.
- Does not run real Codex app-server probes in the normal unit test suite.
- Does not fully solve Codex executable trust/signature diagnostics; that remains
  a separate backlog item unless it reveals a blocking safety issue.
- Does not make `/lrh-export` target-aware across Claude, Codex, and future
  agents in the first implementation item; that can follow once
  `/lrh-codex-export` works.

## Implementation Plan

Implement this through `WS-LRH-CODEX-APP-SERVER-EXPORT`.

1. `WI-CODEX-CONVERSATION-EXPORT-APP-SERVER` implements the library adapter and
   CLI command `lrh conversation export-codex-thread`, using stable
   `thread/read`, private raw JSON capture, rendered Markdown, sensitivity
   scanning, metadata-only terminal output, docs, and tests with fake app-server
   subprocess boundaries.
2. Add a follow-on work item for `/lrh-codex-export` after the CLI adapter lands,
   so the skill wrapper can dogfood the real command rather than reimplementing
   capture logic.
3. Add a follow-on work item for `/lrh-export` only after the Codex-specific path
   has been dogfooded; the umbrella skill can then dispatch to Claude `/export`
   or LRH Codex export according to target.
4. Use private real-session dogfood exports to validate the path, then resume the
   original conversation dogfood plan using actual exported Codex artifacts as
   input.

## Cross-References

- Adopted exporter proposal:
  `project/design/proposals/adopted/lrh-codex-conversation-exporter/00_proposal.md`
- Completed exporter workstream:
  `project/workstreams/resolved/WS-LRH-CODEX-CONVERSATION-EXPORTER.md`
- App-server spike findings:
  `experimental/save_codex_threads/findings.md`
- Conversation CLI reference:
  `docs/reference/cli/conversation.md`
- Follow-on workstream:
  `project/workstreams/proposed/WS-LRH-CODEX-APP-SERVER-EXPORT.md`
- First implementation work item:
  `project/work_items/resolved/WI-CODEX-CONVERSATION-EXPORT-APP-SERVER.md`

## Open Questions

- Should rendered Markdown include reasoning summaries by default, omit them by
  default, or require an explicit policy option? The initial implementation
  should default to omission or summary-only rendering and record a manifest
  warning either way.
- Should active/in-progress turns be rendered with an explicit partial marker, or
  omitted from Markdown while retained in private raw JSON? The implementation
  should preserve raw data and make the rendered policy explicit.
- What private archive-root convention should `/lrh-codex-export` use when the
  user does not provide paths? The first CLI can require explicit paths; the
  skill wrapper can choose a safe default later.
