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

# lrh-implement Skill

This skill encodes the **instruction and execution phases** of the three-phase
execution session model for LRH work items and ad-hoc tasks. It picks up where
`/lrh-work-item` leaves off: given a work item ID or task description, it mints
a prompt ID, checks idempotence, confirms the plan, creates a branch, implements
the work, validates, opens a PR, and creates a populated execution record.

---

## Inputs

Provide a work item ID or ad-hoc task description as the argument:

```
/lrh-implement WI-SKILLS-LRH-SETUP
/lrh-implement "update executions README with new optional fields"
```

A `WI-*` ID is the primary input. Free-form text triggers ad-hoc mode, which
uses the `AD_HOC` prompt bucket.

---

## Reference Knowledge

Load these before running any step:

1. **`references/execution-session-reference.md`** — `lrh prompt label` and
   `lrh prompt check-execution` command syntax, branch naming convention,
   execution record field descriptions (`agent`, `instruction_source`,
   `session_transcript`). Read to populate the execution record correctly.

2. **`references/lrh-implement-workflow.md`** — Lifecycle placement,
   relationship to `lrh work-items readiness`, `ready-work-item`, and
   post-implementation closeout. Read to give the user accurate next-step
   guidance.

3. **`references/canonical-validation.md`** — The `scripts/` validation
   command sequence, failure handling, and evidence to record. Read to run
   and report validation correctly.

4. **`references/prior-art-check.md`** — Prior art / build-vs-buy check
   procedure (duplication search + demand search). Used in Step 1.5 to
   validate or perform a prior-art check before implementation begins.

---

## Execution Steps

Work through these steps in order. Do not skip Step 4 (confirm plan).

### Step 1 — Parse input and check readiness

Determine whether the input is a `WI-*` ID or a free-form description.

**Work item input:** locate the file:

```bash
find project/work_items/ -name "<WI-ID>.md"
```

If not found, stop and report. If found, run:

```bash
lrh work-items readiness <WI-ID> --format md
```

If flagged not prompt-ready, **warn prominently** but allow the user to decide
whether to continue — do not hard-block.

**Ad-hoc input:** summarize the stated goal back to the user and confirm the
understanding before proceeding.

### Step 1.5 — Validate or perform prior-art check

**For work item input:** check whether the work item's `## Problem / Context`
section already contains a prior-art check (duplication search + demand search
verdicts). If it does, note "prior-art check present in WI" and proceed.

**If the work item predates this check or is missing verdicts:**
Run a quick check using `references/prior-art-check.md`:
- **Duplication search** — does something like this already exist in-repo,
  in sibling repos, or as an external library?
- **Demand search** — is there an existing work item, proposal, or backlog
  entry requesting this?

**This step is warn-don't-block:** if a prior-art check is absent or a
potential duplicate is found, surface a warning to the user and wait for
acknowledgement before continuing. Do not hard-stop implementation unless
the user directs you to. Record the outcome in the execution record's Result
section (for demand matches) or flag as a warning (for duplication findings).

**For ad-hoc input:** always run a quick prior-art check as above.

### Step 2 — Read and understand the task

**Work item:** read the full file. Identify and summarize:

- Acceptance criteria
- Required Changes (specific files and actions)
- Validation commands (from the `## Validation` bullets)
- Forbidden actions
- Related workstream

**Ad-hoc:** the user's description is the spec. Restate it in one paragraph
and wait for confirmation.

### Step 3 — Instruction phase (mint prompt ID + idempotence check)

Run (see `references/execution-session-reference.md` for full syntax):

```bash
lrh prompt label --slug <slug> [--work-item <WI-ID>]
lrh prompt check-execution --prompt-id "<id>" --project-root .
```

If `check-execution` reports a `landed` or `in_progress` record, **stop and
report** — do not continue unless the user explicitly asks for a rerun.

Derive the slug from the work item ID (lower-kebab):
`WI-SKILLS-LRH-SETUP` → `wi-skills-lrh-setup`. For ad-hoc, ask the user for
a short slug if one cannot be cleanly derived from the description.

### Step 4 — Confirm plan (human gate)

Before touching any files or creating any branches, show the user:

- Task summary (one paragraph)
- Minted prompt ID
- Branch name to be created (see Step 5)
- High-level list of expected file changes
- Validation commands that will be run
- Any readiness warnings from Step 1

**Wait for explicit confirmation.** If the user redirects, adjust and re-show.
Do not proceed past this gate without approval.

### Step 5 — Create branch from main

```bash
git checkout main && git pull
git checkout -b <branch-name>
```

Branch naming: `<username>/<type>/<slug>`. Get the username:

```bash
gh api user --jq .login
```

Derive the type from the work item's `type` field:

| Work item type | Branch type prefix |
|---|---|
| `deliverable` | `feat` |
| `operation` | `chore` |
| `investigation` | `spike` |
| `evaluation` | `audit` |
| ad-hoc / unknown | `chore` |

Example: `xenotaur/feat/wi-skills-lrh-setup`.

Do not use the `agents/<backend>/<id>` namespace — reserved for future
autonomous backends, not human-driven Claude.app sessions.

### Step 6 — Implement

Do the actual work. Read the relevant source files; make the changes described
in the work item's `Required Changes` section. Respect `forbidden_actions`.
Follow `STYLE.md` and `AGENTS.md`. Load only files needed for this specific
task.

This step is intentionally open-ended: the skill sets up the frame; Claude
performs the implementation. The work item's acceptance criteria are the
specification.

### Step 7 — Validate

Run the canonical validation sequence (see `references/canonical-validation.md`):

```bash
scripts/version tools
scripts/format --check --diff
scripts/lint
scripts/test
lrh validate
```

Then run any **item-specific validation commands** extracted from the work
item's `## Validation` section in Step 2 (for example `diff -r src/ .claude/`
for skills items, or `python -c "import lrh.skills"` for package checks).

If format or lint fails, repair and re-run before continuing. If tests fail,
fix the underlying issue. **Do not create a PR with failing validation.**
Record tool versions and test results for the execution record.

### Step 8 — Commit and PR

Stage and commit the implementation changes. Include the prompt ID in the
commit message. Push and open a PR:

```bash
gh pr create --title "..." --body "..."
```

Include the prompt ID in the PR body — it is the traceability link between
the PR and the execution record.

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
(see `references/execution-session-reference.md` for field descriptions):

```yaml
agent: claude_app
instruction_source: <work-item path or ad-hoc description>
session_transcript: pending
```

Commit the execution record and push it as an additional commit to the
already-open PR.

### Step 10 — Report and offer closeout

Report to the user:

- What was changed and where
- PR URL
- Execution record path and prompt ID
- Validation evidence (tool versions, test count, result)

Offer (do not automatically do):

- Adding the work item ID to the parent workstream's `work_items:` list if not
  already present
- A reminder that `session_transcript: pending` should be updated to
  `claude-app:<session-id>` after the session ends
- Next steps: wait for reviewer comments and run
  `/lrh-review-response <pr-url>` to address them (repeat as needed), then
  `/lrh-confirm-fixes <pr-url>` to verify the fixes against the current diff
  and resolve the review threads before merge. After merging, run
  `/lrh-closeout <pr-url>` to land the execution record and move the work
  item to `resolved/` with a non-null `resolution` value

---

## Quality Checklist

Before reporting completion, verify:

- [ ] Prompt ID minted before any implementation work began
- [ ] Idempotence check passed (no prior landed/in_progress record)
- [ ] User confirmed the plan at Step 4 before any files were touched
- [ ] Branch created from a fresh `git pull` of `main`
- [ ] All validation commands passed before PR was opened
- [ ] Execution record exists with `agent`, `instruction_source`,
      `session_transcript` fields populated
- [ ] Execution record committed as additional commit to open PR
- [ ] `lrh validate` reports 0 errors

---

## What This Skill Does Not Do

- Does not create or refine work items — use `/lrh-work-item` and
  `lrh request ready-work-item`.
- Does not call `lrh request prompt-from-work-item` — reads work items
  directly.
- Does not merge PRs or resolve work items — human decisions.
- Does not implement multiple work items in one invocation.
- Does not automatically update `session_transcript` from `pending` to the
  real session ID — the JSONL lookup requires local filesystem access outside
  the skill's scope.
