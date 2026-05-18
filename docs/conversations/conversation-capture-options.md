# Conversation capture options

## Purpose

Use this guide when useful LRH work starts in a human/AI conversation and you need to preserve enough context for later review. Conversation material can help explain why a change was requested, how alternatives were considered, what commands were run, or what follow-up should become durable project work.

Conversation capture is currently a manual, review-first workflow. LRH does not yet provide stable user-facing conversation import, storage, or promotion commands. Planned automation is tracked as design-stage work in the proposed [LRH Conversations, Storage, and External Agent Interop proposal](../../project/design/proposals/proposed/lrh-conversations-storage-interop/README.md).

## Useful conversation inputs

Good candidates for capture include conversations that contain:

- a prompt that drove a meaningful change or PR;
- design alternatives, tradeoffs, and open questions;
- review feedback and the response plan;
- debugging notes, failed attempts, and hypotheses;
- commands, logs, screenshots, metrics, or other evidence references;
- decisions that still need to be promoted into a design proposal or decision record;
- follow-up work that should become a work item, roadmap change, or focus update.

Do not capture conversations just because they exist. Capture only the material that helps future maintainers understand, validate, or continue the work.

## Current implementation status

| Capability | Status | User-facing workflow today |
| --- | --- | --- |
| Manual copy/paste of selected conversation excerpts into reviewable Markdown | Available | Use a private scratch file, PR description, design draft, work-item draft, evidence note, or execution record as appropriate. |
| Prompt execution records | Available | Use the prompt workflow and `lrh prompt check-execution` / `lrh prompt record-execution` or the repository helper script when a prompt drives meaningful work. |
| Sensitivity scanning helper library | Partially available | `lrh.conversations.sensitivity` exists as a local heuristic helper, but there is no stable user-facing conversation import command built around it. |
| Conversation transcript import from vendor exports | Planned / design-stage | The proposed ChatGPT PDF conversion flow is not implemented as a stable CLI in this repository. |
| LRH-managed conversation storage | Planned / design-stage | Keep raw conversation archives private and outside authoritative project state unless a future accepted workflow says otherwise. |
| Automated promotion from transcript to project artifact | Planned / design-stage | Promote manually by writing the target LRH artifact and reviewing it like any other source change. |

## Capture and export options today

### 1. Copy only the useful excerpt

For most LRH work, the safest current option is to copy a small excerpt or summary into the durable artifact that needs it:

- execution record summary and validation notes;
- design proposal motivation or alternatives section;
- work-item context or acceptance criteria;
- evidence note pointing to commands, logs, reports, or screenshots;
- PR description or review response.

Prefer summaries over full transcripts unless the exact wording matters. If you quote a conversation, include enough surrounding context for review without exposing unrelated private content.

### 2. Save a private raw export for provenance

If the full conversation may matter later, save the raw export in a private location controlled by the project maintainers. Treat it as non-authoritative context until selected content is reviewed and promoted.

Recommended private-export practices:

1. Use a clear filename with date, topic, and source tool.
2. Keep the export out of public repositories by default.
3. Note the source tool and export method.
4. Record whether the export has been reviewed for secrets, credentials, personal data, private URLs, or proprietary content.
5. Link to the private location only where your team policy allows it.

### 3. Convert manually to a reviewable Markdown note

When a conversation must be reviewed in text form, create a Markdown note manually. Include minimal metadata at the top, such as:

```markdown
# Conversation note: <topic>

- Source tool: <tool name>
- Captured on: <date>
- Captured by: <person or role>
- Review status: unreviewed | reviewed
- Authority: non-authoritative context
- Sensitivity review: not scanned | reviewed manually | contains sensitive material

## Summary

<short human-authored summary>

## Relevant excerpts or notes

<only the material needed for review>
```

This note is still not authoritative project state. It becomes authoritative only when selected claims are moved into an accepted LRH artifact, such as a design decision, work item, evidence record, status update, or execution record.

## Safe and reviewable capture practices

Before committing or sharing conversation-derived content:

- remove secrets, tokens, credentials, private URLs, personal data, and customer data;
- remove unrelated chat turns and vendor boilerplate;
- preserve the difference between what a human said, what an AI suggested, and what was actually verified;
- cite evidence separately instead of relying on a chat assertion;
- label raw or summarized conversation material as non-authoritative context;
- avoid committing full raw exports unless the repository policy explicitly allows it;
- keep provenance: source, date, prompt ID or work item when relevant, and reviewer notes.

## Authority boundary

Raw conversations are not authoritative LRH project state. They may contain useful context, but they can also contain speculation, stale assumptions, unreviewed AI output, private details, and incorrect claims.

Authoritative LRH state belongs in the project control stack:

```text
Principles -> Project Goal -> Roadmap -> Current Focus -> Work Items -> Evidence -> Status
```

Promote only the reviewed content that belongs in that stack. Keep raw transcripts, exports, and scratch notes separate from durable project-control artifacts unless and until LRH has an accepted storage workflow for them.

## Related docs

- [Promote conversation-derived content to a project artifact](promote-conversation-to-project-artifact.md)
- [Your first prompt-driven change](../tutorials/first-prompt-driven-change.md)
- [Prompt-driven workflow](../explanations/prompt-driven-workflow.md)
- [Evidence-backed status](../explanations/evidence-backed-status.md)
- [Repository state vs runtime state](../explanations/repository-state-vs-runtime-state.md)
- [Documentation structure](../reference/documentation-structure.md)
