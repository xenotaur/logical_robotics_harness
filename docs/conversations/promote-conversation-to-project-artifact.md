# Promote conversation-derived content to a project artifact

## Purpose

Use this guide when a conversation produced something worth keeping in LRH: a design proposal, roadmap update, work item, evidence note, execution record, status update, or project documentation change.

Promotion means rewriting selected conversation material into the target LRH artifact and reviewing it as project state. It does not mean copying a raw transcript into the project and treating it as truth.

## Current implementation status

Promotion is currently manual. LRH does not yet provide a stable `lrh conversation promote` command, transcript store, automated artifact generator, or vendor import pipeline. Future automation is design-stage unless documented in accepted reference docs or CLI reference pages.

Available today:

- normal Markdown editing of `project/` and `docs/` artifacts;
- prompt execution records for meaningful prompt-driven work;
- existing validation commands, such as `lrh validate`, `scripts/lint`, and `scripts/test`, depending on the repository and change type.

Not available as stable user-facing behavior today:

- automatic import of full conversation archives;
- automatic redaction or certification that a transcript is safe;
- automatic promotion of chat output into authoritative project state;
- a new conversation CLI command.

## Promotion workflow

### 1. Identify the durable outcome

Choose the artifact type before editing. Common outcomes are:

| Conversation produced | Promote into |
| --- | --- |
| A prompt that drove a meaningful change | Execution record under `project/executions/` |
| A proposed implementation task | Work item under `project/work_items/` |
| A design direction, tradeoff, or decision candidate | Design proposal or decision artifact under `project/design/` or `project/memory/` |
| Test output, logs, screenshots, metrics, or review notes | Evidence artifact under `project/evidence/` or validation notes in an execution record |
| A change in project priorities | Roadmap, focus, or status artifact under `project/` |
| User-facing guidance | Documentation under `docs/` |

If the conversation only contains transient reasoning and no durable outcome, do not promote it.

### 2. Extract claims, evidence, and follow-up separately

Review the conversation and separate:

- **claims** — assertions that need verification before becoming project state;
- **evidence** — commands, logs, metrics, screenshots, reports, review notes, or links that support a claim;
- **decisions** — human-approved choices that should be captured in the appropriate design or memory artifact;
- **tasks** — future work that belongs in a work item or roadmap;
- **context** — background that may help reviewers but is not authoritative.

Do not let AI-generated wording bypass review. Restate important claims in human-reviewable prose and attach evidence where needed.

### 3. Check privacy and sensitivity before writing durable files

Before adding conversation-derived text to the repository:

1. Remove secrets, credentials, tokens, private URLs, proprietary content, customer data, and personal data.
2. Remove irrelevant chat turns and tool boilerplate.
3. Mark uncertainty explicitly instead of converting speculation into fact.
4. Keep raw exports private unless repository policy explicitly permits them.
5. Prefer linking to reviewed evidence over quoting long conversation passages.

A sensitivity scan, when available, is only a triage aid. It does not certify that content is safe to publish.

### 4. Write the target artifact, not a transcript

Promoted artifacts should read like normal LRH project files. For example:

- a work item should state type, scope, acceptance criteria, and evidence expectations;
- a design proposal should state motivation, options, decisions, risks, and status;
- an execution record should state the prompt ID, result, validation, and follow-up;
- evidence should describe what was observed and how it supports a status claim;
- docs should explain stable user-facing workflows and label planned behavior clearly.

Use the conversation only as input. The artifact should stand on its own for a reviewer who has not read the chat.

### 5. Validate and record what changed

Run checks appropriate to the promoted artifact:

```bash
lrh validate
```

For prompt-driven changes in this repository, follow the repository-specific validation guidance in `AGENTS.md` and `PROMPTS.md`. The typical task-phase sequence starts with:

```bash
scripts/version tools
```

Then run the relevant lint, test, or documentation checks. For meaningful prompt-driven PRs, create or update only the execution record associated with the current prompt.

### 6. Keep authority explicit

Use language such as:

- "The conversation suggested..." for unverified context.
- "The following command passed..." for evidence-backed validation.
- "This proposal recommends..." for design-stage material.
- "This decision records..." only after the decision is accepted by the relevant process.

Avoid phrases that imply a raw conversation is project truth. Project truth comes from reviewed artifacts, evidence, and status updates.

## Example: from chat to work item

A conversation may contain a useful request: "Add docs explaining how to capture ChatGPT conversations for LRH."

Manual promotion would be:

1. Create or update a work item if the task should be tracked beyond the immediate PR.
2. Write docs that describe current manual workflows and planned automation separately.
3. Add an execution record for the prompt that drove the PR.
4. Run the relevant validation.
5. In the PR, summarize the durable docs and validation results, not the entire conversation.

## Related docs

- [Conversation capture options](conversation-capture-options.md)
- [Your first prompt-driven change](../tutorials/first-prompt-driven-change.md)
- [Prompt-driven workflow](../explanations/prompt-driven-workflow.md)
- [Evidence-backed status](../explanations/evidence-backed-status.md)
- [Validate a project control directory](../how-to/validate-a-project.md)
- [CLI reference: `validate`](../reference/cli/validate.md)
- [Documentation structure](../reference/documentation-structure.md)
