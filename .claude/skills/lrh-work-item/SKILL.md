---
name: lrh-work-item
description: >
  Create a new LRH work item in project/work_items/proposed/. Use when the
  user wants to capture a deliverable, operation, investigation, or evaluation
  as a formal work item. Interviews the user, researches related workstreams
  and focus, proposes complete frontmatter and body sections, and writes the
  file after explicit confirmation. Validates with lrh validate.
when_to_use: >
  Invoke only when explicitly creating a new LRH work item planning artifact
  in project/work_items/proposed/. Do not invoke when the user is discussing,
  reading, or querying work items. Suitable for orchestration from /lrh-design,
  /lrh-proposal, or /lrh-workstream when those skills need to create companion
  work items as part of a design-capture workflow.
argument-hint: [WI-ID]
---

# lrh-work-item Skill

This skill creates a new LRH work item file at
`project/work_items/proposed/<ID>.md` (where `<ID>` is the full `WI-*`
identifier) following the LRH schema and body conventions. It interviews the user, researches related project context,
proposes a complete work item for review, and writes the file only after
explicit confirmation. All output is shown to the user before any files are
written.

---

## Inputs

The user provides a work item ID as the argument:

```
/lrh-work-item WI-SKILLS-LRH-SETUP
```

The ID must be in SCREAMING-KEBAB-CASE and start with `WI-`. If the ID is
not provided, ask for one before proceeding.

---

## Reference Knowledge

Load these before running any step:

1. **`references/work-item-schema.md`** — Full YAML frontmatter field
   reference: required fields, valid values, type vocabulary, directory-bucket
   rules, and blocking/resolution conventions. Read this to produce valid
   frontmatter.

2. **`references/work-item-body-guide.md`** — Section-by-section authoring
   guide for the work item body: what goes in Summary, Problem/Context, Scope,
   Required Changes, Non-Goals, Acceptance Criteria, Validation, and Risk
   Notes. Read this to produce a body that passes prompt-from-work-item
   readiness checks.

3. **`references/lrh-work-item-workflow.md`** — How this skill fits the
   broader LRH lifecycle: create → validate → ready → prompt → execute.
   Describes the relationship to `lrh request ready-work-item`,
   `lrh request prompt-from-work-item`, and execution records. Read this to
   give the user accurate next-step guidance.

4. **`references/prior-art-check.md`** — Prior art / build-vs-buy check
   procedure (duplication search + demand search). Run this during Step 3
   (research) and record the verdict in the `## Problem / Context` body
   section to confirm the work item does not duplicate existing work.

5. **`references/execution-record.md`** — `lrh prompt label` and
   `lrh prompt check-execution` command syntax, execution record field
   descriptions (`agent`, `instruction_source`, `session_transcript`). Read
   before Step 4 (instruction phase) and Step 10 (execution record).

---

## Execution Steps

Work through these steps in order. Do not skip the confirmation gate (Step 5).

### 1. Check for existing work item

Search all bucket directories for a file whose stem matches the requested ID:

```bash
find project/work_items/ -name "<ID>.md"
```

If found:
- Report the file path and its current `status`.
- Ask whether to overwrite, extend, or abort.
- Do not silently overwrite existing work.

### 2. Interview

Ask all eight questions at once to avoid multiple round-trips. Collect all
answers before proposing anything.

1. **Title and summary:**
   - **Title:** A short one-line title for the `title` frontmatter field
     (e.g., `Implement lrh-work-item Claude Code skill`).
   - **Problem statement:** What problem does this work item solve, or what
     does it deliver? One paragraph suitable for the `## Summary` section.

2. **Type:** Is this a `deliverable` (files, code, docs, config, or skills to
   produce), `operation` (maintenance, tidy, or process task), `investigation`
   (research, surveying, or spike exploration), or `evaluation` (measurement,
   audit, or assessment)?

3. **Related workstream:** Which `WS-*` workstream does this belong to? If
   none applies, say so and `related_workstreams` will be left empty.

4. **Dependencies:** Does this work item depend on others (`depends_on`) or is
   it currently blocked by any (`blocked_by`)? List WI-* IDs or say none.

5. **Expected artifacts:** What files will this work item create or modify when
   complete? Used for `artifacts_expected` and `acceptance` criteria.

6. **Forbidden actions:** What should this work item explicitly never do?
   Common examples: `force_push`, `delete_branch`, `implement_<next_stage>`.

7. **Acceptance criteria:** How will you know this is done? Two to five
   concrete, verifiable conditions. These become both the `acceptance`
   frontmatter list and the `## Acceptance Criteria` body section.

### 3. Research the project

Before proposing, read:

- The related workstream file (if identified) — to understand the broader
  context and confirm the work item fits the workstream's scope and does not
  duplicate an existing item.
- `project/focus/` — to identify the relevant `FOCUS-*` ID for
  `related_focus`, if applicable.
- `project/roadmap/` — to identify the relevant `ROADMAP-*` ID for
  `related_roadmap`, if applicable.
- A few similar existing work items — to follow naming, scope, and
  `forbidden_actions` conventions established in this project.

Then run the prior art check (see `references/prior-art-check.md`):
- **Duplication search** — does something like this already exist in-repo,
  in sibling repos, or as an external library? Record the verdict. If a
  duplicate is found, stop and surface it to the user before proposing the
  work item.
- **Demand search** — is there an existing work item, proposal, or backlog
  entry requesting this? Record the verdict. If a match is found, offer to
  close/link it at Step 11; do not auto-close.

Record both verdicts in the `## Problem / Context` body section of the
proposed work item before presenting it to the user.

Then propose the complete work item: frontmatter (all fields) and body
(all required sections with content). Show it to the user before writing.

### 4. Instruction phase (mint prompt ID + idempotence check)

Derive `<slug>` from the work item ID (lower-kebab): `WI-SKILLS-LRH-SETUP` →
`wi-skills-lrh-setup`.

**Before minting, search for an existing record on this branch by stable
slug.** `lrh prompt label` always mints a fresh timestamped prompt ID, so
`check-execution` alone cannot detect a rerun — the ID it receives is brand
new every time it's called. Derive `<SLUG_UPPER_UNDERSCORE>` from `<slug>`
by replacing `-` with `_` and uppercasing (e.g. `wi-skills-lrh-setup` →
`WI_SKILLS_LRH_SETUP`), then match the complete trailing filename segment —
not a bare substring, which would also match an unrelated longer slug that
happens to contain this one (e.g. `..._WI_SKILLS_LRH_SETUP_REVIEW.md`):

```bash
find project/executions/AD_HOC/ -name "*_<SLUG_UPPER_UNDERSCORE>.md" 2>/dev/null
```

`AD_HOC/` may not exist yet in a freshly bootstrapped project — no record has
been written there yet — so suppress the not-found error rather than
treating it as a failure.

The glob can return more than one match — a prior rerun mints a new
timestamped file with the same trailing slug. Read the `status:`
frontmatter field of **every** match before deciding — per `PROMPTS.md`'s
status-handling rule, a matched filename is discovery, not by itself a
block:
- Any match is `in_progress` or `landed`: **stop and report** — do not
  continue unless the user explicitly asks for a rerun. If more than one
  match is `in_progress`/`landed`, name all of them and ask the user which
  one this is a rerun of — do not guess. Once the user does confirm a
  rerun, **keep the confirmed match's `execution_id`** (the most recent
  one, if the user doesn't distinguish) to pass as `--rerun-of` in Step 10
  — a rerun links to the prior attempt regardless of which status
  triggered it (`PROMPTS.md:136`).
- All matches are `failed`, `reverted`, or `superseded`: not a blocking
  prior run — summarize the most recent one and continue, but **keep its
  `execution_id`** to pass as `--rerun-of` in Step 10 (per `PROMPTS.md:136`,
  a rerun must link back to the prior attempt it supersedes).
- Matches disagree (e.g. one `failed`, one unknown) or any status is
  unrecognized: **stop and report** the ambiguity.

Then mint the prompt ID and run the secondary check (see
`references/execution-record.md` for full syntax):

```bash
lrh prompt label --slug <slug>
lrh prompt check-execution --prompt-id "<id>" --project-root .
```

Do not pass `--work-item <ID>` here. This record documents the *creation* of
the work item, not its implementation, so it stays in the `AD_HOC` bucket
(the `lrh prompt label` default). Bucketing it under the new WI's own ID
would make `/lrh-closeout`'s decision matrix treat the freshly created,
not-yet-implemented item as resolved the moment this planning PR merges —
see `references/execution-record.md`.

If `check-execution` reports a `landed` or `in_progress` record, **stop and
report** — do not continue unless the user explicitly asks for a rerun.

### 5. User confirms

Show the user the complete proposed work item — frontmatter and full body —
in a readable block.

Wait for explicit confirmation before writing any files.

If the user redirects or declines, adjust the proposal and show it again.
Do not skip this gate — it prevents incorrectly-scoped work items from
being committed to the control plane.

### 6. Create branch from main

```bash
git checkout main && git pull
git checkout -b <branch-name>
```

Branch naming: `<username>/<type>/<slug>`. Get the username:

```bash
gh api user --jq .login
```

Derive `<slug>` from the work item ID (lower-kebab):
`WI-SKILLS-LRH-SETUP` → `wi-skills-lrh-setup`

Map the work item `type` (known from Step 2) to `<type>`:

| Work item type | Branch type |
|---|---|
| `deliverable` | `feat` |
| `operation` | `chore` |
| `investigation` | `spike` |
| `evaluation` | `audit` |

Example: `xenotaur/feat/wi-skills-lrh-setup`

### 7. Write file

Re-check that the work item does not already exist on the freshly pulled
main — the Step 1 check may be stale if main advanced since the session
started:

```bash
find project/work_items/ -name "<ID>.md"
```

If found, stop and report — ask the user to overwrite, extend, or abort
before proceeding.

Create `project/work_items/proposed/<ID>.md` with the confirmed content.
The `project/work_items/proposed/` directory already exists; do not recreate
it. Set `status: proposed`, `blocked: false`, `blocked_reason: null`,
`resolution: null`.

Important formatting rule for the `## Validation` section: use bullet-listed
commands (lines starting with `- `), not a fenced code block. The readiness
parser only extracts bullets; a code block produces an empty list and the
item will fail `lrh work-items readiness` with "missing Validation commands"
even though the section exists.

### 8. Validate

Run:

```bash
lrh validate
```

Fix any errors before proceeding. Common failures: required frontmatter field
missing, `status` value does not match directory bucket, filename stem does
not match `id` field.

### 9. Commit and open PR

Stage and commit the work item file:

```bash
git add project/work_items/proposed/<ID>.md
git commit -m "Add work item <ID>: <title>"
git push -u origin <branch-name>
gh pr create --title "Add work item <ID>: <title>" --body "..."
```

Include in the PR body: the work item summary, type, related workstream,
acceptance criteria, and the prompt ID minted in Step 4 — it is the
traceability link between the PR and the execution record.

### 10. Create execution record

```bash
lrh prompt record-execution \
  --prompt-id "<id>" \
  --work-item AD_HOC \
  --slug <slug> \
  --status in_progress \
  --project-root .
```

If Step 4 found a prior matching record — whether summarized
(`failed`/`reverted`/`superseded`) or explicitly overridden by the user
(`in_progress`/`landed`) — add `--rerun-of <its-execution_id>` to the
command above so the new record links back to it, per `PROMPTS.md:136`.

Use `AD_HOC`, not `<ID>` — see the note in Step 4. This creates the record
under `project/executions/AD_HOC/`, not `project/executions/<ID>/`.

Immediately edit the generated file to populate the three optional fields
(see `references/execution-record.md`):

```yaml
agent: claude_app
instruction_source: project/work_items/proposed/<ID>.md
session_transcript: pending
```

Then replace the generated `TODO` placeholders in `# Summary`, `# Result`,
`# Validation`, and `# Follow-up` with real content grounded in what this
run actually did (per `AGENTS.md`'s evidence policy) — e.g. Summary states
the work item created, Result names the file and PR, Validation reports the
Step 8 `lrh validate` outcome, Follow-up notes any offers from Step 11 that
are still open. `/lrh-closeout` later only touches frontmatter, so an
unedited TODO body would ship as `landed` with no narrative evidence.

Commit the execution record and push it as an additional commit to the
already-open PR.

### 11. Offer workstream update and report

**Workstream update (offer, not automatic):**

If a workstream was identified in Step 2, read its current `work_items:`
list from the YAML frontmatter and show the user what adding the new ID
would look like. Wait for explicit approval before editing the workstream
file.

If the user approves, edit the workstream, then validate and push the change
to the open PR as an additional commit — do not leave it uncommitted:

```bash
lrh validate
git add project/workstreams/<WS-ID>.md
git commit -m "Update workstream <WS-ID>: add <ID>"
git push
```

**Report to the user:**

- The file created and its path.
- The `lrh validate` outcome.
- The PR URL.
- The minted prompt ID and execution record path.
- Which fields were inferred vs. directly from user answers — be explicit
  so the user can correct mismatches.
- A reminder that `session_transcript: pending` in the execution record
  should be updated to `claude-app:<host-uuid-stem>` after the session ends.
- Suggested next steps per `references/lrh-work-item-workflow.md`.

---

## Quality Checklist

Before reporting completion, verify:

- [ ] Prompt ID minted (Step 4) before the confirm gate (Step 5)
- [ ] Idempotence check passed (no prior landed/in_progress record)
- [ ] Branch created from a fresh `git pull` of main
- [ ] `project/work_items/proposed/<ID>.md` exists
- [ ] Filename stem exactly matches the `id` frontmatter field
- [ ] Required fields present: `id`, `title`, `type`, `status`, `blocked`,
      `blocked_reason`, `resolution`
- [ ] `status: proposed` and file is in `proposed/` directory bucket
- [ ] `blocked: false`, `blocked_reason: null`, `resolution: null`
- [ ] Body contains all required sections: Summary, Problem/Context, Scope,
      Required Changes, Non-Goals, Acceptance Criteria, Validation
- [ ] `lrh validate` reports 0 errors
- [ ] The confirm-before-write gate (Step 5) was honoured
- [ ] PR opened and URL reported to the user
- [ ] Execution record exists under `project/executions/AD_HOC/` (not
      `<ID>/` — see Step 4) with `agent`, `instruction_source`,
      `session_transcript` populated, and `# Summary`/`# Result`/
      `# Validation`/`# Follow-up` filled in with real content, not TODOs
- [ ] Execution record was pushed to the open PR

---

## What This Skill Does Not Do

- Does not refine existing thin work items — use
  `lrh request ready-work-item <ID>` for that.
- Does not promote work items to `active` or `resolved` — status changes
  are human decisions.
- Does not implement the work item — it creates the planning artifact only.
- Does not automatically update workstreams — Step 11 offers; the user
  decides.
- Does not land the execution record it creates for this PR, or mark it
  `landed` — that happens at `/lrh-closeout` after the PR merges. Separately,
  it does not create the *implementation's* execution record — that is
  produced by `/lrh-implement` when the work item is later executed.
- Does not run `lrh request prompt-from-work-item` — that is a separate
  step after the item has been refined to readiness.
