---
name: lrh-doc-work
description: >
  Update a repository's documentation to reflect recently completed work.
  Accepts a merged PR URL, a resolved work item ID (WI-*), or a closed
  workstream ID (WS-*) — auto-detects from the current branch if no argument
  is provided. Identifies which docs are affected, classifies needed updates
  by Diataxis quadrant, confirms with the user, and implements the updates
  in a reviewable PR. Use after work lands to keep docs current.
disable-model-invocation: true
argument-hint: "[pr-url | WI-ID | WS-ID]"
---

# lrh-doc-work Skill

This skill updates a repository's documentation to reflect work that has
recently landed: a merged PR, a resolved work item, or a closed workstream.
It does not audit documentation structure (that is `/lrh-doc-audit`) and does
not reorganize docs (that is `/lrh-doc-organize`).

---

## Inputs

Provide a reference to the recently completed work, or omit to auto-detect:

```
/lrh-doc-work
/lrh-doc-work https://github.com/owner/repo/pull/123
/lrh-doc-work WI-SKILLS-LRH-DOC-AUDIT
/lrh-doc-work WS-SKILLS-DOC
```

**Argument disambiguation:**
- Starts with `https://` → merged PR URL
- Starts with `WI-` → resolved work item ID
- Starts with `WS-` → closed workstream ID
- Omitted → auto-detect: inspect the current branch name and recent git
  history to identify the most recently merged work

---

## Reference Knowledge

Load these before running any step:

1. **`references/doc-work-scope.md`** — How to identify affected docs from a
   PR diff, work item acceptance criteria, or workstream completion summary.
   Scope rules (update only, no audit or reorganization). PR vs. direct-commit
   guidance. Read at Steps 4–6.

2. **`references/diataxis-criteria.md`** — Four-quadrant definitions and
   classification heuristics. Read at Step 6 (classify needed updates by
   Diataxis quadrant).

---

## Execution Steps

Work through these steps in order. Do not skip Step 7 (confirm gate).

### Step 1 — Parse work reference

Determine the type and identity of the completed work:

- **PR URL** (`https://...`): fetch the PR metadata.
  ```bash
  gh pr view <pr-url> --json title,body,mergedAt,state,files
  ```
  Verify `state` is `MERGED`. If not, stop and report.

- **WI-ID** (`WI-*`): locate the work item file.
  ```bash
  find project/work_items/resolved/ -name "<WI-ID>.md"
  ```
  If not found in `resolved/`, check `proposed/` to confirm whether the file
  exists and report its location, then **stop** — the skill operates only on
  resolved work items.

- **WS-ID** (`WS-*`): locate the workstream file.
  ```bash
  find project/workstreams/resolved/ -name "<WS-ID>.md"
  ```
  If not found in `resolved/`, stop and report — the skill operates only on
  closed workstreams.

- **Auto-detect**: inspect the current branch and recent git log to find the
  most recent merged PR or resolved work item. Report what was detected and
  confirm before proceeding.

### Step 2 — Load references

Read `references/doc-work-scope.md` and `references/diataxis-criteria.md` in
full before proceeding. The affected-doc identification logic (Steps 4–5) and
Diataxis classification (Step 6) derive from these files.

### Step 3 — Mint prompt ID + idempotence check

Before reading the work reference or making any changes to the repository,
mint a prompt ID:

```bash
lrh prompt label --slug doc-work-<work-reference-slug>
lrh prompt check-execution --prompt-id "<id>" --project-root .
```

Derive `<work-reference-slug>` from the input:
- PR URL: `pr-<number>` (e.g., `pr-336`)
- WI-ID: lower-kebab of the ID (e.g., `wi-skills-lrh-doc-audit`)
- WS-ID: lower-kebab of the ID (e.g., `ws-skills-doc`)
- Auto-detected: use the detected reference's slug

If `check-execution` reports a `landed` or `in_progress` record, **stop and
report** — do not continue unless the user explicitly asks for a rerun.

Store the prompt ID for use in Step 12 (execution record).

### Step 4 — Identify scope of completed work

Read the work reference to understand what changed:

- **PR**: read the PR body (what was built), the file diff (what changed),
  and the PR title. Fetch the diff explicitly — `gh pr view` only returns
  metadata and file names, not the patch:
  ```bash
  gh pr diff <pr-url>
  ```
  Focus on user-visible changes: new CLI commands, new config options,
  changed APIs, new concepts, changed workflows.
- **WI**: read the full work item file. Focus on the Summary, Acceptance
  Criteria, and Required Changes sections. Identify what was delivered.
- **WS**: read the workstream file and all resolved work items under it.
  Summarize what the workstream as a whole delivered.

Apply the scope identification heuristics from `references/doc-work-scope.md`.

### Step 5 — Map changes to affected docs

For each change identified in Step 4, determine which documentation is
affected. Consult `references/doc-work-scope.md` for mapping heuristics.

For each affected doc, note:
- **Path** — existing file to update, or new file to create
- **Action** — update, create, or mark stale
- **Reason** — what changed that makes this doc update necessary

Also check for docs that have become stale: reference docs describing APIs
that changed, how-to guides for workflows that were modified, or explanation
docs for concepts that have evolved.

### Step 6 — Classify by Diataxis quadrant

For each doc action identified in Step 5, classify it using
`references/diataxis-criteria.md`:

- **Tutorial** — does the new work warrant a new learning exercise?
- **How-to** — does it introduce or change a task the user needs to accomplish?
- **Reference** — does it change a CLI flag, config option, API, or schema?
- **Explanation** — does it introduce a new concept or change a design rationale?

Note the quadrant for each action. This drives both the content of the update
and where the doc should live.

### Step 7 — Confirm gate (human gate)

Before creating a branch or touching any files, show the user:

- Work reference and summary of what was completed
- List of doc actions (path, action type, Diataxis quadrant, reason)
- Any stale docs identified
- Scope of new docs to create (stub vs. full)

**Wait for explicit confirmation.** If the user trims or redirects scope,
adjust and re-show. Do not proceed past this gate without approval.

### Step 8 — Create branch

```bash
git checkout main && git pull
git checkout -b <username>/chore/doc-work-<work-reference-slug>
```

Get `<username>` from `gh api user --jq .login`. Use the same
`<work-reference-slug>` from Step 3.

### Step 9 — Implement updates

Execute each confirmed doc action from Step 7:

- **Update existing doc**: apply the minimal change needed to reflect the
  completed work. Do not rewrite sections unrelated to the change.
- **Create new doc**: create the file at the appropriate location for its
  Diataxis quadrant. Use a stub if the full content would require knowledge
  beyond what the work reference provides; mark stubs clearly.
  ```markdown
  > **Stub:** This document is a placeholder. Full content will be added after
  > the feature is exercised in production. See <work-reference> for context.
  ```
- **Mark stale**: if a doc describes behavior that has changed and a full
  update is out of scope for this run, add a notice at the top rather than
  leaving it silently wrong:
  ```markdown
  > **Note:** This doc is under review. Some content may not reflect recent
  > changes. See <work-reference> for context.
  ```

Keep the change surface minimal — update only what the completed work
requires. Do not reorganize, reformat, or expand scope beyond the confirmed
list.

### Step 10 — Validate

Run the canonical sequence:

```bash
scripts/version tools
scripts/format --check --diff
scripts/lint
scripts/test
lrh validate
```

If any links introduced by the new or updated docs are stale, fix them.
Do not open a PR with validation failures.

### Step 11 — Commit and open PR

Stage and commit all changes. Push and open a PR:

```bash
gh pr create --title "docs: update for <work-reference>" --body "..."
```

Include in the PR body:
- Work reference (PR URL, WI-ID, or WS-ID)
- List of docs updated/created with brief description of each change
- Any deferred items (stale docs not yet updated, stubs created) and why

### Step 12 — Create execution record

```bash
lrh prompt record-execution \
  --prompt-id "<id>" \
  --work-item AD_HOC \
  --slug doc-work-<work-reference-slug> \
  --status in_progress \
  --project-root .
```

Use the prompt ID minted in Step 3. Populate optional fields:

```yaml
agent: claude_app
instruction_source: <pr-url or WI-ID or WS-ID>
session_transcript: pending
```

Run `lrh validate`, commit the record as an additional commit to the open PR,
and push.

Then report the PR URL, the execution record path, and the next steps: run
`/lrh-review-response <pr-url>` to address reviewer comments (repeat as
needed), then `/lrh-confirm-fixes <pr-url>` to verify the fixes against the
current diff and resolve the review threads before merge. After merging, run
`/lrh-closeout <pr-url>` to land the execution record and update the control
plane.

---

## Quality Checklist

Before reporting completion, verify:

- [ ] Work reference parsed and type confirmed (PR merged / WI resolved / WS closed)
- [ ] Prompt ID minted at Step 3 before any file reads or changes
- [ ] Idempotence check passed (no prior landed/in_progress record)
- [ ] References read at Step 2 before identification work
- [ ] Every doc action has a Diataxis quadrant classification
- [ ] User confirmed the exact list of doc actions at Step 7
- [ ] Branch created from a fresh `git pull` of main
- [ ] No scope creep beyond confirmed list (no reorganization or reformatting)
- [ ] No stale links introduced by new or updated docs
- [ ] `lrh validate` passes with 0 errors after execution record added
- [ ] Execution record committed as additional commit to open PR

---

## What This Skill Does Not Do

- Does not audit documentation structure — use `/lrh-doc-audit` for that
- Does not reorganize docs — use `/lrh-doc-organize` for that
- Does not update docs for work that has not yet landed (unmerged PRs,
  proposed work items, open workstreams)
- Does not rewrite docs wholesale — minimal, targeted updates only
- Does not automatically determine scope without consulting the work reference
