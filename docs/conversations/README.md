# Conversations

Conversation documentation covers user-facing workflows for capturing, reviewing, and promoting conversations into durable LRH artifacts. Import and storage automation is design-stage unless a stable reference page says otherwise.

## What belongs here

- Human-facing workflows for conversation capture, review, and manual promotion.
- Guidance for turning conversation notes into project-control artifacts, evidence, or follow-up work.
- Interoperability notes for conversation archives when they affect LRH users, clearly labeled as current workflow or planned design.
- Boundaries between ephemeral conversation context and durable LRH records.

## What does not belong here

- General tutorials, task recipes, or reference pages that are not conversation-specific.
- Raw conversation dumps without curation, context, or promotion guidance.
- Authoritative project state duplicated from [`../../project/`](../../project/).
- Deep vendor-specific integration details before LRH has stable user-facing behavior for them.

## How to decide whether to add content here

Add content here when the reader's problem starts with conversation material: capture it, preserve provenance, review it safely, or promote it into durable LRH artifacts. If the resulting artifact is a stable schema, document the schema in [reference](../reference/README.md) and link from here.

## Implemented capture support

LRH includes local, private-by-default conversation capture paths for Codex app
tasks, explicit local Codex files, and ChatGPT PDF exports with extractable
text. Codex app exports default to LRH's durable private session archive, while
explicit file/PDF conversions write caller-chosen local paths. These paths
create non-authoritative Markdown artifacts for later private review; they do
not perform redaction certification, public export, model calls, or automatic
promotion into project-control state.

For Codex app tasks, use [`/lrh-codex-export`](codex_export.md) as the
agent-facing workflow wrapper around `lrh conversation archive-codex-thread`.
For exact command options and exit behavior, see the
[`lrh conversation` CLI reference](../reference/cli/conversation.md).

## Currently relevant docs

- [Import ChatGPT PDF conversations](chatgpt_pdf_import.md) — convert ChatGPT PDFs into private-by-default Markdown transcripts with sensitivity metadata and review guidance.
- [Export Codex conversations](codex_export.md) — capture a current or specified Codex task through `/lrh-codex-export` without printing transcript text or committing raw exports.
- [Conversation capture options](conversation-capture-options.md) — current manual capture/export choices, safety guidance, and implementation-status boundaries.
- [Promote conversation-derived content to a project artifact](promote-conversation-to-project-artifact.md) — manual workflow for turning reviewed conversation material into durable LRH artifacts.

Current design exploration for future storage, import, and automation remains under [`../../project/design/`](../../project/design/). User-facing docs here should label planned behavior clearly and avoid presenting design-stage workflows as implemented.
