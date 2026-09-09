---
id: PROP-LRH-CLAUDE-CONVERSATION-EXPORTER
type: design_proposal
title: LRH Claude Code Conversation Exporter Design Proposal
status: proposed
created_on: 2026-09-09
updated_on: 2026-09-09
implementation_status: not_started
implemented_by: []
supersedes: []
superseded_by: null
related_design:
  - project/design/proposals/adopted/lrh-antigravity-conversation-exporter/00_proposal.md
  - project/design/proposals/adopted/lrh-codex-conversation-exporter/00_proposal.md
  - project/design/proposals/proposed/lrh-conversations-storage-interop/00_proposal.md
---

# LRH Claude Code Conversation Exporter Design Proposal

## Summary

This proposal defines the design and implementation model for exporting Claude Code
session transcripts into private-by-default, non-authoritative Markdown transcript
artifacts, backed by the existing generalized `ConversationExportManifest` and
heuristic sensitivity scanning. The exporter is delivered across three modular
tranches: (1) a core Python API in `src/lrh/conversations/claude_export.py`,
(2) a CLI subcommand `lrh conversation export-claude-session` in `src/lrh/cli/main.py`,
and (3) a Claude Code skill package in `src/lrh/skills/lrh-export-claude/`.

## Background / Motivation

Claude Code's built-in `/export` slash command is unavailable in the Claude Desktop
app's Code-tab session surface — confirmed live via the butterbar message
`"/export" is not available for this session` — making it a non-starter for
continuing to rely on it as the archival path for AI-assisted development sessions.

LRH has already solved the equivalent problem twice: `/lrh-antigravity-export`
(`PROP-LRH-ANTIGRAVITY-CONVERSATION-EXPORTER`) exports Google Antigravity session
transcripts by reading their local JSONL file directly, and `/lrh-codex-export`
(`PROP-LRH-CODEX-CONVERSATION-EXPORTER`) exports Codex tasks through the Codex
app-server RPC boundary. This proposal builds the third parallel exporter, closing
the gap left by `/export`'s unavailability, following the design established by
both prior exporters and the broader `PROP-LRH-CONVERSATIONS-STORAGE-INTEROP`
framework.

Claude Code's own documentation (`code.claude.com/docs/en/sessions.md`, "Where
transcripts are stored") states: "By default, Claude Code stores transcripts as
JSONL at `~/.claude/projects/<project>/<session-id>.jsonl`... The entry format is
internal to Claude Code and changes between versions, so scripts that parse these
files directly can break on any release. To build on session data, use `/export`
or the script interfaces instead." Since `/export` is unavailable in this surface
and the documented script interfaces (headless `-p --resume`, hooks) do not cover
retroactive full-transcript capture of an already-finished session, this proposal
knowingly accepts the same class of format-stability risk LRH already accepts for
Antigravity's equally undocumented `transcript.jsonl` format — mitigated by the
same defensive-parsing discipline already proven in `antigravity_export.py`.

## Prior Art Check

### Duplication search
- In-repo: No `lrh-export-claude` skill directory anywhere (`.claude/skills/`,
  `.agents/skills/`, `.gemini/plugins/lrh/skills/`, `src/lrh/skills/` all checked).
  No `export-claude-session` CLI subcommand in `src/lrh/cli/main.py:115-158`. No
  `src/lrh/conversations/claude_export.py`. No `docs/reference/cli/conversation.md`
  section for a Claude exporter.
- Sibling repos: None identified.
- External libraries: None identified providing a stable, version-independent
  Claude Code transcript export API.
- Recommendation: Proceed — implement `src/lrh/conversations/claude_export.py`.

### Demand search
- Work items: No open work item requests this directly.
- Proposals: No open proposal requests this directly. Closest matches are the
  adopted, implemented siblings `PROP-LRH-ANTIGRAVITY-CONVERSATION-EXPORTER` and
  `PROP-LRH-CODEX-CONVERSATION-EXPORTER`, and the related, still-`proposed`
  `PROP-LRH-CONVERSATIONS-STORAGE-INTEROP`.
- Backlog: `WI-SESSION-ARCHIVE-ROOT-DEFAULT` and `WI-SESSION-ARCHIVE-DATE-BROWSABILITY`
  (both `proposed`) touch the shared archive-root/browsability layer this exporter
  writes into, but neither requests a Claude-specific exporter.
- Recommendation: Proceed; link to `PROP-LRH-CONVERSATIONS-STORAGE-INTEROP`.

## Design Decisions

### Decision 1: Input route — direct local JSONL parse vs. RPC/live-process capture

Options considered:
- **Direct JSONL file parse** (Antigravity's model) — read the session's local
  transcript file directly from `~/.claude/projects/<project>/<session-id>.jsonl`.
- **App-server/RPC capture** (Codex's model) — talk to a live, documented API
  boundary that returns structured thread data.
- **LLM-mediated re-summarization** — `claude -p --resume <session-id>
  --output-format json "..."` to ask the model to reproduce its own history.

**Chosen: direct JSONL file parse.** Claude Code exposes no documented RPC/app-server
equivalent to Codex's `thread/read` for retroactively reading a *finished* session's
full history — `claude -p --resume` sends a *new* prompt and returns a fresh,
LLM-generated answer, not a verbatim structured dump of prior turns. That
disqualifies it as the primary mechanism: it cannot produce a literal, hash-verifiable
capture, which both sibling skills treat as load-bearing
(`src/lrh/skills/lrh-codex-export/SKILL.md:201-205`
runs `inspect-export --source $RAW_PATH` specifically to verify `Source hash: match`
against raw ground truth). Direct file parse is the only route that preserves
verbatim tool-call payloads and produces a real hash to verify against, and it
requires no live process or network call the way `codex_archive.py`'s RPC-failure
mitigation (`attempt.json` crash-safety bookkeeping) exists to handle — though a
local file read is not itself guaranteed atomic while the session is still being
written: the implementation must defensively handle a partially-written trailing
line/record rather than assume the read always observes a complete final record.

This was verified empirically, live, in the design session that produced this
proposal, rather than deferred as a follow-up spike (contrast with the Antigravity
proposal, which required a dedicated "dogfood verification gate" before locking
renderer mapping functions): this exact conversation's own live-growing transcript
was located on disk mid-session at a path of the shape
`~/.claude/projects/<encoded-working-directory>/<session-id>.jsonl`,
confirming Claude Desktop *does* write to the documented CLI storage path, not a
separate undocumented location, despite the docs' own caveat that "the desktop app...
[maintains its] own session history." Subagent transcripts were also confirmed live
as sibling files at `<session-id>/subagents/agent-<id>.jsonl` plus a matching
`.meta.json` (fields: `agentType`, `description`, `toolUseId`, `spawnDepth`) — found
by locating the actual transcript of a research subagent dispatched earlier in the
same conversation.

### Decision 2: Manifest generalization prerequisite

Unlike the Antigravity proposal, which required a Step 0 prerequisite to generalize
`ConversationExportManifest` from Codex-only to multi-vendor (see
`lrh-antigravity-conversation-exporter/00_proposal.md`, Design Decision 1), that
generalization is already in place: `SUPPORTED_KINDS`/`SUPPORTED_SOURCE_TOOLS`
already support multiple vendors and even a generic fallback kind
(`export_manifest.py:13-18`), and `export_inspector.py` was confirmed to contain no
vendor-specific branching on `kind` or `source_tool`. **Chosen: no Step 0 needed.**
This is purely additive: append `KIND_CLAUDE = "lrh_claude_conversation_export"` and
`SOURCE_TOOL_CLAUDE_CODE = "claude_code"` to the existing constant tuples.
`claude_code`, not `claude`, was chosen specifically to avoid ambiguity against
Claude.ai, Claude Desktop (as a product), and the underlying model family in
manifests that will be read years from now.

### Decision 3: Session discovery interface

Options considered:
- Mirror Antigravity's `--transcript-path` / `--conversation-id` / `--latest`
  mutually-exclusive flag set.
- A positional session-id argument only.

**Chosen: `--transcript-path` / `--session-id` / `--latest`**, mutually exclusive,
matching `antigravity_export.py:298-311`'s shape for interface consistency across
LRH's exporters. App data dir defaults to `${CLAUDE_CONFIG_DIR:-~/.claude}`,
override-able via `--app-data-dir` (mirroring `antigravity_export.py:312-319`'s
`--app-data-dir` default). `--session-id` resolves by globbing
`<app-data-dir>/projects/*/<id>.jsonl`; Claude Code's own docs note a session ID can
resolve to more than one project directory only when "exactly one other project
holds a transcript with messages for it" (implying a real, if narrow, collision
surface) — so more than one match is treated as an error requiring `--transcript-path`
disambiguation, not a silent first-match pick.

### Decision 4: Record classification and rendering

The Claude Code JSONL schema uses a `type` discriminator per line (`user`,
`assistant`, `attachment`, `queue-operation`, `ai-title`, confirmed against real
records observed in this design session). **Chosen rendering rules:**
- Render `user`/`assistant` records, including nested content blocks (text,
  `tool_use`, `tool_result`, `thinking`).
- Skip `queue-operation` records (enqueue/dequeue bookkeeping, not conversation
  content).
- Use an `ai-title` record's value as the Markdown H1 when present.
- Skip `attachment` records by default (`deferred_tools_delta`,
  `agent_listing_delta`, `mcp_instructions_delta`, `skill_listing` — internal
  system-context deltas, not part of the visible conversation, consistent with
  what Claude Code's own `/export` docs describe rendering: "messages and tool
  outputs," not tool-listing deltas), with `--include-system-attachments` as an
  escape hatch for completeness.

### Decision 5: Subagent transcript handling

A session can spawn many subagents (this design session spawned one; sessions
observed on disk during verification had a dozen or more). **Chosen:** reference
subagent transcripts by id and description (sourced from the sibling `.meta.json`)
in the primary export rather than inlining full sub-transcripts by default, to keep
the top-level export scannable as a primary read. `--include-subagents` appends
full subagent transcripts as an appendix section.

### Decision 6: Statistics, privacy, and safety plumbing — unchanged reuse

`transcript_statistics.turn_count` counts `type=="user"` records carrying a
`message` field; `message_count` counts `type in ("user","assistant")` records
carrying `message` — same pattern as `antigravity_export.py:214-225`. All other
plumbing is reused without modification: `sensitivity.py` heuristic scan,
`DEFAULT_PRIVACY = "private"`, `DEFAULT_AUTHORITY = "non_authoritative_context"`,
the `umask 077` / `chmod 0600` private-file pattern, and `export_inspector.py`
source-hash verification.

### Decision 7: Archive layout

**Chosen:** `<archive_root>/claude/exports/<YYYY>/<MM>/<session-id>.md`, matching
the `antigravity/exports/YYYY/MM/` convention already established.

### Decision 8: Delivery staging

Options considered mirrored the Antigravity precedent's 3-tranche staging
(confirmed via `git log --diff-filter=A`: PRs #526, #625, #627 for Antigravity's
API/CLI/Skill, plus a #633 follow-up). **Chosen: the same 3-tranche staging**, each
tranche its own future work item:
1. Core Python API — `src/lrh/conversations/claude_export.py`
2. CLI subcommand — `lrh conversation export-claude-session` in `src/lrh/cli/main.py`
3. Skill package — `src/lrh/skills/lrh-export-claude/SKILL.md`

No dogfood-verification-gate prerequisite work item is needed, unlike Antigravity's
original build, because that verification was already performed empirically within
this design/proposal session (see Decision 1).

### Decision 9: Skill naming — `lrh-export-claude`, not `lrh-claude-export`

Options considered:
- **`lrh-claude-export`** — matches the two already-shipped siblings,
  `lrh-antigravity-export` and `lrh-codex-export`.
- **`lrh-export-claude`** — shares a prefix with the long-deferred umbrella
  dispatcher `/lrh-export`.

**Chosen: `lrh-export-claude`.** `/lrh-export` has been the documented name for
a future target-aware dispatcher since 2026-08-07 — never a per-vendor command —
per `project/design/backlog.md`'s "Generalize conversation export manifests
beyond Codex before `/lrh-export`" entry ("Status: Tracked, not yet designed")
and `PROP-LRH-CODEX-APP-SERVER-CONVERSATION-EXPORT`'s Implementation Plan item 3
("the umbrella skill can then dispatch to Claude `/export` or LRH Codex export
according to target"). The CLI layer already uses this prefix shape for the
subcommands that actually export a live session — `export-antigravity-session`,
`export-codex-thread`, and this proposal's own `export-claude-session`
(Decision 8) — so `lrh-export-claude` also brings the skill layer into line with
the CLI layer's existing convention.

This skill has not shipped, so adopting the prefix form costs nothing today.
The two already-shipped siblings, `lrh-antigravity-export` and `lrh-codex-export`,
are deliberately **not** renamed as part of this proposal: both names are quoted
verbatim inside multiple `status: resolved`/`adopted` documents (the adopted
Codex app-server proposal itself, `WS-LRH-CODEX-APP-SERVER-EXPORT`, and five
resolved work items), and per this project's own lifecycle convention — adopted
documents are not retroactively rewritten — renaming them is deferred to the
`/lrh-export` umbrella's own future design work, where the full-family naming
decision belongs.

## Non-Goals

- Does not modify Claude Code's internal storage format or session lifecycle.
- Does not make exported transcripts authoritative project state.
- Does not commit raw session JSONL files to public repository state.
- Does not automatically promote transcript text into work items, design
  decisions, or evidence without human review.
- Does not attempt to replicate the Claude Desktop app's
  `session-export-<timestamp>.zip` diagnostic bundle mechanism — investigated and
  identified in the design conversation preceding this proposal as an unrelated
  Cowork-diagnostics feature (bundling the same per-session directory plus
  `cowork_vm_*`/`coworkd`/`vzgvisor` application logs), not a target this exporter
  reproduces.
- Does not implement the `SessionEnd` hook-based automatic-capture mechanism
  discussed as a complementary follow-on in the preceding design conversation —
  that remains prospective-only future work, out of scope here.

## Implementation Plan

Medium scope, three tranches, each its own work item, in delivery order:
1. `WI-CLAUDE-CONVERSATION-EXPORT-API` — core Python API
   (`src/lrh/conversations/claude_export.py`, manifest constant additions).
2. `WI-CLAUDE-CONVERSATION-EXPORT-CLI` — CLI subcommand
   (`lrh conversation export-claude-session` in `src/lrh/cli/main.py`), plus the
   corresponding `docs/reference/cli/conversation.md` entry.
3. `WI-CLAUDE-CONVERSATION-EXPORT-SKILL` — skill package
   (`src/lrh/skills/lrh-export-claude/SKILL.md`), following `lrh-codex-export/SKILL.md`'s
   confirm-before-write-gate and metadata-only-report pattern.

## Cross-References

- `project/design/proposals/adopted/lrh-antigravity-conversation-exporter/00_proposal.md`
- `project/design/proposals/adopted/lrh-codex-conversation-exporter/00_proposal.md`
- `project/design/proposals/proposed/lrh-conversations-storage-interop/00_proposal.md`
- `src/lrh/conversations/antigravity_export.py`
- `src/lrh/conversations/export_manifest.py`
- `src/lrh/conversations/export_inspector.py`

## Open Questions

- Whether Claude Code on the web and the VS Code extension write transcripts to
  the same `~/.claude/projects/` path as the CLI and Desktop app was not verified
  in this design session — only the Desktop app path was confirmed empirically.
  If they differ, `--app-data-dir`/`--transcript-path` should still cover them, but
  this is unconfirmed.
- Whether `docs/reference/cli/conversation.md` should also gain the missing
  `export-antigravity-session` entry (an existing documentation gap noted during
  design, unrelated to this proposal's scope) is left open rather than folded in
  here.
