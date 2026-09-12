---
id: PROP-LRH-TARGET-AWARE-EXPORT-ARCHIVE
type: design_proposal
title: Target-Aware LRH Export and Private Conversation Archive
status: proposed
created_on: 2026-08-10
updated_on: 2026-08-11
implementation_status: not_started
implemented_by: []
supersedes: []
superseded_by: null
related_design:
  - project/design/proposals/adopted/lrh-codex-app-server-conversation-export/00_proposal.md
  - project/design/proposals/proposed/lrh-session-archive-sync/00_proposal.md
  - project/design/proposals/proposed/lrh-conversations-storage-interop/00_proposal.md
  - project/design/proposals/proposed/lrh-execution-sessions/00_proposal.md
  - project/design/proposals/proposed/lrh-antigravity-conversation-exporter/00_proposal.md
  - docs/reference/cli/conversation.md
  - project/workstreams/active/WS-SESSION-ARCHIVE-SYNC.md
  - project/design/backlog.md
---

# Target-Aware LRH Export and Private Conversation Archive

## Summary

This proposal defines a target-aware `/lrh-export` workflow and supporting `lrh`
CLI archive tools for sorting private conversation artifacts across Claude,
Codex app, ChatGPT saved PDFs, Codex Cloud prompt files, and future agent
targets. The design chooses a date-first private archive layout optimized for
human file-browser navigation, backed by machine-readable indexes and existing
LRH privacy, inspection, and session-sync conventions.

## Background / Motivation

LRH now has several partial conversation-capture paths. Codex app export is
implemented through `lrh conversation export-codex-thread`; ChatGPT PDF
conversion exists through `lrh conversation convert-pdf`; Claude archive sync
exists through `lrh sessions sync`; and Codex Cloud already treats saved prompt
files as durable instruction artifacts. These paths are useful, but they remain
tool-specific.

The user-facing gap is now the orchestration layer: a human should be able to
ask for `/lrh-export` and have LRH choose the correct safe capture path for the
current target, then place the resulting private artifact in a durable archive.
A second gap is archival hygiene: existing Claude exports, past Codex exports,
ChatGPT PDFs, and Codex Cloud prompt files need a predictable way to be sorted
into a private archive repository without committing transcript bodies to the
LRH project control plane.

The motivating local corpus already has a human-organized workspace shape:
`/Users/centaur/Workspace/Promptspace/Working/` contains incoming prompts,
in-process prompts, completed prompt packages, sample chats, and a large
`Sessions/` directory of Claude and Jules session exports. That points away
from a purely machine-first archive layout. A human should be able to browse the
private archive by year, month, and agent without first consulting an LRH index
or command-line report.

The design must preserve LRH's existing safety boundary. Raw transcripts,
PDFs, app-server captures, and export zips are private, non-authoritative
context. They may inform later reviewed artifacts, but they are not themselves
project decisions, evidence, work items, or status until a separate promotion
step creates sanitized project-control artifacts.

## Prior Art Check

### Duplication search

- In-repo: No complete target-aware `/lrh-export` implementation was found.
  Related implementations exist:
  - `src/lrh/skills/lrh-codex-export/SKILL.md`
  - `docs/reference/cli/conversation.md`
  - `src/lrh/conversations/export_manifest.py`
  - `src/lrh/prompt_workflow_sessions.py`
  - `src/lrh/sessions_workflow.py`
- Sibling repos: No sibling repository was identified as already implementing
  this LRH-specific private archive sorter.
- External libraries: No external library was identified that provides LRH's
  required combination of agent-target dispatch, source-specific export,
  private archive organization, manifest inspection, sensitivity scanning,
  and LRH control-plane promotion boundaries.
- Recommendation: Proceed by composing and extending existing LRH export and
  archive surfaces.

### Demand search

- Work items: Existing resolved Codex work items explicitly deferred
  target-aware `/lrh-export`; active session-archive work still needs the
  archive-root question resolved. Antigravity export work is active separately.
- Proposals: Found related proposals:
  `PROP-LRH-CODEX-APP-SERVER-CONVERSATION-EXPORT`,
  `PROP-LRH-SESSION-ARCHIVE-SYNC`,
  `PROP-LRH-CONVERSATIONS-STORAGE-INTEROP`, and
  `PROP-LRH-EXECUTION-SESSIONS`.
- Backlog: Found entries for generalizing conversation export manifests before
  `/lrh-export` and for avoiding guessed default Claude `/export` zip locations.
- Recommendation: Link this proposal to those artifacts and use it to govern
  the integration layer, not to replace the source-specific exporter designs.

## Design Decisions

### Decision 1: Add target-aware `/lrh-export` as an orchestration skill

Options considered:

- Keep only source-specific skills such as `/lrh-codex-export`.
- Add `/lrh-export` as a thin alias for Codex only.
- Add `/lrh-export` as a target-aware dispatcher over source-specific backends.

Chosen: add `/lrh-export` as a target-aware dispatcher.

The skill should detect or ask for the current target, then delegate to the
narrowest correct path. In Codex app, it should call the existing Codex
app-server exporter. In Claude, it should use Claude's `/export` workflow and
then route the result through LRH archive sorting. For ChatGPT PDFs, it should
use the PDF converter. For Codex Cloud, it should archive saved prompt files as
instruction artifacts, not as transcripts. Future Antigravity support should be
gated on the Antigravity CLI/skill workstream landing.

### Decision 2: Add a private archive sorter CLI

Options considered:

- Extend `lrh sessions sync` to sort every artifact type.
- Add a separate `lrh conversation archive sort` command.
- Keep sorting manual.

Chosen: add `lrh conversation archive sort`.

`lrh sessions sync` should continue to own Claude session reconciliation.
A broader archive sorter should classify mixed inputs, delegate Claude session
cases to existing session code where appropriate, and copy recognized artifacts
into a common private archive layout. Manual sorting is too error-prone once
artifacts include export zips, raw Codex JSON, Markdown exports, PDFs, and
Codex Cloud prompt files.

Initial command shape:

```bash
lrh conversation archive sort --archive-root ARCHIVE_ROOT --inbox PATH --dry-run
lrh conversation archive sort --archive-root ARCHIVE_ROOT --inbox PATH --copy
lrh conversation archive list --archive-root ARCHIVE_ROOT
lrh conversation archive inspect ARTIFACT_ID --metadata-only
```

The default operation should be dry-run or copy, never destructive move.

### Decision 3: Use one configurable Promptspace-style private archive root

Options considered:

- One archive root for all agent artifacts.
- Separate roots per source tool.
- Hard-code a default project-local archive path.
- Preserve the current unused `~/.local/share/lrh/session-archive` default as
  the canonical layout.

Chosen: one configurable private root in a sibling private workspace, with
date-first source-specific subdirectories.

The archive root should be supplied by `--archive-root`, environment, or later
LRH config. It must not be guessed from the current project checkout. A
Promptspace-style sibling directory such as
`/Users/centaur/Workspace/Promptspace/Private Sessions Archive/` is a good
deployment shape: outside LRH and client repositories, readable in Finder, and
aligned with the existing private prompt/session workspace.

The current `LRH_SESSION_ARCHIVE_ROOT` default of
`~/.local/share/lrh/session-archive` has not been populated in this environment,
so this proposal does not preserve its top-level `raw/`, `exports/`, and
`sessions/` layout as the canonical private archive. Existing code should be
updated to the new layout before the archive becomes populated rather than
locking in an unused machine-first structure.

The archive root may be a private repository, but LRH should not auto-commit or
auto-push it. It is a sensitive data store.

### Decision 4: Use a date-first B-plus archive layout

Options considered:

- Preserve the existing top-level session archive directories.
- Use a source-first `conversations/<source>/<id>/` layout.
- Use a pure date-first archive with no machine indexes.
- Use a date-first archive backed by root-level machine indexes.

Chosen: use a date-first archive backed by root-level machine indexes.

Recommended layout:

```text
<archive-root>/
  README.md
  archive/
    2026/
      08/
        claude-app/
          20260807T195735Z_<safe-title-or-session-id>/
            session-export.zip
            metadata.json
            artifact.json
        codex-app/
          20260810T184526Z_<thread-id-stem>/
            export.md
            raw.json
            inspect.json
            artifact.json
        codex-cloud-prompt/
          20260513T000000Z_<prompt-id-or-sha>/
            prompt.md
            artifact.json
        chatgpt-pdf/
          20260518T023120Z_<source-sha-stem>/
            source.pdf
            export.md
            inspect.json
            artifact.json
        jules/
          20260801T120000Z_<session-id-or-sha>/
            session.zip
            artifact.json
  indexes/
    artifacts.jsonl
    sessions.jsonl
    prompts.jsonl
    by-agent/
    by-project/
```

The `archive/YYYY/MM/<agent>/...` tree is the human-facing canonical file
layout. The `indexes/` tree is the machine-facing search and reconciliation
surface. The implementation should update `lrh sessions sync` to write Claude
mirrors and harvested export metadata into this layout rather than preserving
the older unpopulated `raw/` / `exports/` root layout.

Date partitioning should use a deterministic precedence rule: explicit
artifact/export timestamp first, prompt-id timestamp second, embedded source
metadata third, and source file mtime last. Every artifact record should store
the chosen `archive_date`, `date_source`, and original source mtime so later
audits can explain why a file landed where it did.

### Decision 5: Use metadata-only inspection and index output

Options considered:

- Print transcript snippets during sorting and inspection.
- Record only paths with no sidecar metadata.
- Record sidecar metadata plus a global index.

Chosen: record sidecar metadata plus a global index, and keep CLI output
metadata-only.

Each archived artifact should have enough metadata to be understood later:
source tool, source adapter, source kind, source id when known, hashes, sizes,
created/exported/archived timestamps, archive date and date source, privacy,
authority, sensitivity status, warnings, related prompt ids, related PRs, and
normalized paths. A global JSONL index makes listing and duplicate detection
cheap; sidecars make individual artifact directories self-describing.

The sorter and inspector should not print transcript body text by default.

### Decision 6: Treat Codex Cloud prompt files as instruction artifacts

Options considered:

- Treat Codex Cloud prompt files as conversation transcripts.
- Ignore Codex Cloud because it lacks a transcript export.
- Archive prompt files as instruction artifacts with honest limitations.

Chosen: archive Codex Cloud prompt files as instruction artifacts.

Codex Cloud saved prompts are valuable archaeology, but they are not session
transcripts. The archive record should use a source kind such as
`codex_cloud_prompt`, record the prompt id when present, and avoid claiming
conversation capture.

### Decision 7: Keep raw archive and committed LRH control plane separate

Options considered:

- Commit raw archives into the LRH repo.
- Commit sanitized indexes only.
- Keep all archive metadata outside LRH.

Chosen: keep raw artifacts private and outside project control; commit only
sanitized, intentional project artifacts when separately promoted.

The private archive may have its own private repository lifecycle, but LRH's
project control plane should only receive reviewed summaries, execution-record
pointers, or sanitized indexes. This preserves the existing authority boundary:
conversation exports are non-authoritative context.

## Non-Goals

- Does not commit raw transcripts, PDFs, raw JSON captures, export zips, or
  transcript excerpts to LRH project repositories.
- Does not make private conversation archives authoritative project state.
- Does not replace `lrh sessions sync`; it composes with it.
- Does not preserve the unused `~/.local/share/lrh/session-archive`
  machine-first layout as the canonical private archive layout.
- Does not scrape undocumented app storage internals.
- Does not solve encrypted off-machine backup in the first implementation.
- Does not claim Codex Cloud prompt files are transcripts.
- Does not implement Antigravity export before the existing Antigravity
  exporter workstream delivers its CLI and skill path.
- Does not automatically commit or push the private archive repository.

## Implementation Plan

1. **Archive contract and configuration.**
   Define the private archive root precedence, directory layout, artifact index
   schema, sidecar metadata schema, date-source precedence, safety rules, and
   docs. Decide whether the umbrella setting is `LRH_PRIVATE_ARCHIVE_ROOT`,
   `LRH_CONVERSATION_ARCHIVE_ROOT`, or a revised
   `LRH_SESSION_ARCHIVE_ROOT`, but treat the Promptspace-style date-first root
   as the intended deployment model.

2. **Archive sorter CLI.**
   Implement `lrh conversation archive sort` with `--dry-run`, `--copy`,
   explicit `--archive-root`, explicit input paths/inbox roots, classification
   for Claude export zips, Claude JSONL transcripts, Codex LRH exports, ChatGPT
   PDFs, and Codex Cloud prompt files. Reuse existing converters and session
   archive code.

3. **Archive list/inspect commands.**
   Add metadata-only commands that list archived artifacts, verify hashes, and
   report diagnostics without printing transcript bodies.

4. **Target-aware `/lrh-export` skill.**
   Add a skill that detects or asks for target, dispatches to the correct
   backend-specific export/capture path, invokes archive sorting when durable
   storage is requested, and reports only metadata.

5. **Dogfood and hardening.**
   Test with real private artifacts: this Codex task, an existing Claude export
   zip, a past Codex export, a ChatGPT saved PDF, and a Codex Cloud saved prompt
   file. Include a dry-run over
   `/Users/centaur/Workspace/Promptspace/Working/Sessions` and the Promptspace
   prompt directories. Capture findings in docs or execution records without
   committing raw private content.

6. **Follow-on integration.**
   After the sorter and skill are dogfooded, consider closeout integration,
   scheduled archive checks, and `lrh serve` views over the broader archive.

## Cross-References

- Codex app-server export proposal:
  `project/design/proposals/adopted/lrh-codex-app-server-conversation-export/00_proposal.md`
- Session archive proposal:
  `project/design/proposals/proposed/lrh-session-archive-sync/00_proposal.md`
- Conversation storage interop proposal:
  `project/design/proposals/proposed/lrh-conversations-storage-interop/00_proposal.md`
- Execution sessions proposal:
  `project/design/proposals/proposed/lrh-execution-sessions/00_proposal.md`
- Antigravity exporter proposal:
  `project/design/proposals/proposed/lrh-antigravity-conversation-exporter/00_proposal.md`
- Conversation CLI docs:
  `docs/reference/cli/conversation.md`
- Session archive workstream:
  `project/workstreams/active/WS-SESSION-ARCHIVE-SYNC.md`

## Open Questions

- Should the first dogfood archive root be
  `/Users/centaur/Workspace/Promptspace/Private Sessions Archive/`, or should
  the implementation use that only as a documented example while requiring an
  explicit `--archive-root`?
- Should the umbrella archive setting be named `LRH_PRIVATE_ARCHIVE_ROOT`,
  `LRH_CONVERSATION_ARCHIVE_ROOT`, or should LRH extend
  `LRH_SESSION_ARCHIVE_ROOT`?
- Should explicit archive sorting copy original Claude `/export` zips by
  default, or harvest metadata by default and copy full zips only with an
  `--include-original` option?
- What metadata should be committed, if any, to project-control indexes after
  private sorting succeeds?
- Should archive-root configuration eventually live in `lrh meta config` once
  non-boolean values are supported?
