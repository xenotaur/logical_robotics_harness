---
id: PROP-LRH-IMPLEMENT-SKILL
type: design_proposal
title: "lrh-implement — Implementation Session Skill"
status: adopted
parent: PROP-LRH-PROJECT-LOCAL-SKILLS
created_on: 2026-06-24
updated_on: 2026-06-24
implementation_status: not_started
implemented_by: []
supersedes: []
superseded_by: null
related_design:
  - project/design/proposals/proposed/lrh-execution-sessions/00_proposal.md
  - PROMPTS.md
  - project/executions/README.md
---

# `lrh-implement` — Implementation Session Skill

## Summary

This sub-proposal defines the design for `/lrh-implement`, a Claude Code
skill that encodes the **instruction and execution phases** of the
three-phase execution session model (`PROP-LRH-EXECUTION-SESSIONS`) as a
structured, reproducible Claude.app workflow.

The skill picks up where `/lrh-work-item` leaves off: given a ready work
item (or an ad-hoc task description), it mints a prompt ID, checks
idempotence, confirms the plan with the user, creates a branch, implements
the work, runs canonical validation, opens a PR, and creates a populated
execution record — including the new optional `agent`, `instruction_source`,
and `session_transcript` fields.

This proposal is documentation-only. No skill file is delivered in the
proposal PR; implementation is tracked under a separate work item.

## Background and motivation

After `/lrh-work-item` creates a planning artifact, the next step in the
LRH lifecycle is implementation. Currently this is done via an informal
Claude.app session: the user pastes the work item into a chat, asks Claude
to implement it, and manually follows the prompt workflow from `PROMPTS.md`.
There is no structured skill to enforce the three-phase model, remind the
user to mint a prompt ID, run the canonical validation sequence, or populate
the new execution-record fields consistently.

`/lrh-implement` addresses this gap by encoding the implementation workflow
as a reusable, auditable Claude Code skill.

## Lifecycle placement

```text
/lrh-work-item WI-<ID>           ← create planning artifact
    ↓
lrh work-items readiness          ← check prompt-readiness
lrh request ready-work-item       ← refine if thin
    ↓
/lrh-implement WI-<ID>            ← THIS SKILL
    ↓
project/executions/<ID>/          ← execution record (created by this skill)
    ↓
Merge PR + closeout (human)
```

The existing `lrh request prompt-from-work-item` step is intentionally
skipped: that command generates a prompt file for submission to Codex Cloud,
which is redundant when Claude is reading the work item directly. The work
item's `Required Changes` and `Acceptance Criteria` sections serve as the
implementation specification.

## Inputs

- **Primary:** a `WI-*` work item ID (e.g., `/lrh-implement WI-SKILLS-LRH-SETUP`)
- **Fallback:** a free-form ad-hoc task description for tasks without a
  formal work item (e.g., `/lrh-implement "update executions README with new optional fields"`)

When a `WI-*` ID is provided, the skill reads the work item file and uses
its content as the authoritative implementation specification. When a
free-form description is provided, the skill uses the `AD_HOC` prompt bucket
for the execution record.

## Skill frontmatter

```yaml
---
name: lrh-implement
description: >
  Implement an LRH work item or ad-hoc task using the three-phase execution
  session model. Given a work item ID or task description, this skill mints
  a prompt ID, checks idempotence, confirms the implementation plan, creates
  a branch, implements the changes, runs canonical validation, opens a PR,
  and creates a populated execution record. Use when the user wants to execute
  a defined work item (WI-*) or an ad-hoc task in a structured, traceable way.
disable-model-invocation: true
argument-hint: "[WI-ID or task description]"
---
```

`disable-model-invocation: true` is required: this skill creates branches,
writes files, runs commands, and opens PRs. It must only run on explicit
user intent.

## Reference files (3)

**`references/execution-session-reference.md`** — The practical facts from
`PROP-LRH-EXECUTION-SESSIONS` needed at execution time: `lrh prompt label`
and `lrh prompt check-execution` command syntax, branch naming convention,
execution record field descriptions (including `agent`, `instruction_source`,
`session_transcript`). Read to populate the execution record correctly.

**`references/lrh-implement-workflow.md`** — Lifecycle placement, the
relationship to `lrh work-items readiness`, `ready-work-item`, and
post-implementation closeout (move work item to `resolved/`, run
`lrh work-items audit`). Read to give the user accurate next-step guidance.

**`references/canonical-validation.md`** — The `scripts/` validation
command sequence (`scripts/version tools`, `scripts/format --check --diff`,
`scripts/lint`, `scripts/test`), what to do on each failure mode, and what
evidence to record in the execution record Validation section. Read to run
and report validation correctly.

Three reference files keeps the scope tight. More would suggest the skill is
too broad (per the `lrh-skill-pattern.md` constraint: more than five
reference files is a smell).

## Execution steps (10)

### Step 1 — Parse input and check readiness

If a `WI-*` ID was given: locate the file across all bucket directories
(`find project/work_items/ -name "<ID>.md"`), confirm it exists, then run:

```bash
lrh work-items readiness --status proposed --format md
```

If the item is flagged as not prompt-ready, **warn prominently** but allow
the user to decide whether to continue — do not hard-block. An expert user
may override. If the item is not found, stop and report.

If free-form input was given: acknowledge it as an ad-hoc task, summarize
the stated goal back to the user, and confirm before proceeding.

### Step 2 — Read and understand the task

For a work item: read the full file. Identify and summarize:
- Acceptance criteria
- Required Changes
- Validation commands (from the `## Validation` section bullets)
- Forbidden actions
- Related workstream

For ad-hoc: the user's description is the spec; restate it in one paragraph
and wait for confirmation that the understanding is correct.

### Step 3 — Instruction phase (mint prompt ID + idempotence check)

Run:

```bash
lrh prompt label --slug <slug> [--work-item <WI-ID>]
lrh prompt check-execution --prompt-id "<id>" --project-root .
```

If `check-execution` reports a `landed` or `in_progress` record, **stop
and report** — do not continue unless the user explicitly asks for a rerun.
This is the soft-idempotence gate from `PROMPTS.md`.

For a work item, derive the slug from the work item ID (lower-kebab):
`WI-SKILLS-LRH-SETUP` → `wi-skills-lrh-setup`. For ad-hoc, ask the user
for a short slug if one cannot be cleanly derived from the description.

### Step 4 — Confirm plan (human gate)

Before touching any files or creating any branches, show the user:

- Task summary (one paragraph)
- Minted prompt ID
- Branch name to be created (see Step 5 for naming convention)
- High-level list of expected file changes
- Validation commands that will be run
- Any readiness warnings from Step 1

**Wait for explicit confirmation.** If the user redirects, adjust and
re-show. Do not proceed past this gate without approval. This is the
LRH confirm-before-write gate adapted for implementation work.

### Step 5 — Create branch from main

```bash
git checkout main && git pull
git checkout -b <branch-name>
```

Branch naming convention: `<username-prefix>/<type>/<slug>`. Derive the
type from the work item's `type` field:

| Work item type | Branch type prefix |
|---|---|
| `deliverable` | `feat` |
| `operation` | `chore` |
| `investigation` | `spike` |
| `evaluation` | `audit` |
| ad-hoc / unknown | `fix` or `chore` |

The username prefix comes from `git config user.name` or a project
convention (e.g., `xenotaur` for this repository). Example:
`xenotaur/feat/wi-skills-lrh-setup`.

**Do not use the `agents/<backend>/<id>` namespace** — that is reserved for
future autonomous execution backends, not human-driven Claude.app sessions
(per `PROP-WORKSTREAM-EXECUTION-FRAMEWORK`).

### Step 6 — Implement

Do the actual work. Read the relevant source files, make the changes
described in the work item's `Required Changes` section. Respect
`forbidden_actions`. Follow `STYLE.md` and `AGENTS.md`. Load only the
files needed for this specific task — do not front-load the entire
codebase.

This step is intentionally open-ended: the skill sets up the frame; Claude
performs the implementation. The work item's acceptance criteria are the
specification.

### Step 7 — Validate

Run the canonical validation sequence:

```bash
scripts/version tools
scripts/format --check --diff
scripts/lint
scripts/test
```

If format or lint fails, repair and re-run before continuing. If tests
fail, fix the underlying issue before continuing. **Do not create a PR
with failing validation.** Record the tool versions and test result for
inclusion in the execution record.

### Step 8 — Commit and PR

Stage and commit the changes. Include the prompt ID in the commit message.
Push and open a PR:

```bash
gh pr create --title "..." --body "..."
```

Include the prompt ID in the PR body. The prompt ID is the traceability
link between the PR and the execution record.

### Step 9 — Create execution record

```bash
lrh prompt record-execution \
  --prompt-id "<id>" \
  --work-item <WI-ID or AD_HOC> \
  --slug <slug> \
  --status in_progress \
  --project-root .
```

Immediately edit the generated file to populate the three optional fields
from `PROP-LRH-EXECUTION-SESSIONS`:

```yaml
agent: claude_app
instruction_source: <work-item path, e.g. project/work_items/proposed/WI-SKILLS-LRH-SETUP.md>
session_transcript: pending
```

Commit the execution record on the same branch before pushing, so the PR
contains the record stub and reviewers can see what execution this PR
corresponds to.

### Step 10 — Report and offer closeout

Report to the user:
- What was changed and where
- PR URL
- Execution record path and prompt ID
- Validation evidence (tool versions, test count, result)

Offer (do not automatically do):
- Adding the work item ID to the parent workstream's `work_items:` list
  if it is not already present
- A reminder that `session_transcript: pending` should be updated to
  `claude-app:<session-id>` after the session ends, using the JSONL
  file path at `~/.claude/projects/<project-slug>/`
- Next steps: merge PR, move work item to `resolved/` with a non-null
  `resolution` value once the PR lands

## Key design decisions and rationale

### Skip `lrh request prompt-from-work-item`

`prompt-from-work-item` generates a prompt file for submission to Codex
Cloud. In a Claude.app session, Claude reads the work item directly — the
file is the spec, not a rendered prompt. Calling `prompt-from-work-item`
would add a step with no benefit.

### Warn on readiness, do not hard-block

A hard block on `lrh work-items readiness` failures would prevent expert
users from implementing a work item they know is sufficiently specified.
The check is a quality gate, not a hard prerequisite. The skill warns
prominently and records the warning in the execution record, giving
reviewers visibility without removing user agency.

### No `context: fork`

The skill needs human interaction at the confirmation gate (Step 4) and
possibly during implementation (Step 6). A forked subagent would be
isolated from the main session, preventing this interaction. Running
inline means the context window fills with implementation work, but that
is the expected and appropriate behaviour for a complex implementation
session.

### `xenotaur/<type>/<slug>` branch namespace

The `agents/<backend>/<id>` namespace proposed in
`PROP-WORKSTREAM-EXECUTION-FRAMEWORK` is intended for future autonomous
execution backends where the agent (not the human contributor) owns the
branch. Claude.app sessions are human-driven: the human invokes the skill,
approves the plan, and merges the PR. The human-contribution namespace is
more accurate.

## Staged implementation plan

### Stage 1 — Core skill (`WI-SKILLS-LRH-IMPLEMENT`)

- `src/lrh/skills/lrh-implement/SKILL.md`
- `src/lrh/skills/lrh-implement/references/execution-session-reference.md`
- `src/lrh/skills/lrh-implement/references/lrh-implement-workflow.md`
- `src/lrh/skills/lrh-implement/references/canonical-validation.md`
- `.claude/skills/lrh-implement/` — self-hosting copy, byte-for-byte
  identical to `src/lrh/skills/lrh-implement/`
- `CLAUDE.md` update — add `/lrh-implement` entry to the Skills section
- `pyproject.toml` — `lrh.skills` package data already declared; no change

Stage 1 delivers the skill for immediate use in the LRH repository without
requiring `lrh setup`.

### Stage 2 — `lrh setup` integration (`WI-SKILLS-LRH-SETUP`)

Once `lrh setup` ships, `lrh-implement` is automatically included in the
skills copied to `~/.claude/skills/` and becomes available in all projects.
No skill-level changes needed; Stage 2 is a dependency, not a modification.

## Non-goals

- Does not design or create work items — use `/lrh-work-item`.
- Does not refine thin work items — use `lrh request ready-work-item`.
- Does not call `lrh request prompt-from-work-item` — reads work items
  directly.
- Does not merge PRs or close/resolve work items — human decisions.
- Does not implement multiple work items in one invocation.
- Does not run in a forked subagent context.
- Does not automatically update `session_transcript` from `pending` to the
  real session ID — the JSONL file lookup requires local filesystem access
  outside the skill's scope.

## Risks and mitigations

### Risk 1 — Step 6 complexity

The "implement" step cannot be fully prescribed by the skill. Implementation
quality depends on the model, the work item's specificity, and the
surrounding codebase state.

Mitigation: the work item's acceptance criteria and validation step (Step 7)
are the correctness signal. If validation passes and acceptance criteria are
met, the implementation is correct by the project's own definition.

### Risk 2 — Context window exhaustion

A complex implementation (many file reads + many writes + validation output)
can fill the context window. The skill may degrade in quality late in a long
session.

Mitigation: Step 6 instructs Claude to load only files needed for the
specific task. For particularly large work items, `context: fork` could be
added in a future version; this is deferred until the need arises.

### Risk 3 — Stale branch

If `git pull` in Step 5 is skipped or main has moved, the branch may be
based on stale state.

Mitigation: Step 5 explicitly requires `git checkout main && git pull`
before branching. The skill should not skip this even if it appears the
branch is fresh.

## Acceptance criteria

This sub-proposal can be considered implemented when:

- `src/lrh/skills/lrh-implement/SKILL.md` exists and passes validation
- All three `references/` files exist under both `src/` and `.claude/`
  locations, byte-for-byte identical
- The skill successfully guides a Claude.app session through a complete
  implementation of a real LRH work item, producing a PR and a populated
  execution record with `agent: claude_app`
- `CLAUDE.md` lists `/lrh-implement` in the Skills section
- `lrh validate` reports 0 errors

## Work items

- `WI-SKILLS-LRH-IMPLEMENT` — implement Stage 1 (skill files and self-hosting
  copy); depends on `WI-SKILLS-LRH-SETUP` for global availability but can
  ship independently for LRH-local use
