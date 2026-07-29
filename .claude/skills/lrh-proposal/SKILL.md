---
name: lrh-proposal
description: >
  Create a new LRH design proposal at project/design/proposals/proposed/<slug>/00_proposal.md.
  Use when the user wants to capture a design decision, architecture choice, or feature direction
  as a formal proposal artifact. Interviews the user, researches existing proposals, proposes
  complete frontmatter and body sections, and writes the file only after explicit confirmation.
  Validates with lrh validate.
when_to_use: >
  Invoke only when explicitly creating a new LRH design proposal planning
  artifact in project/design/proposals/proposed/. Do not invoke when the
  user is discussing, reading, or querying proposals. Suitable for
  orchestration from /lrh-design when it needs to create a companion
  proposal as part of a design-capture workflow.
argument-hint: [slug]
---

# lrh-proposal Skill

This skill creates a new LRH design proposal at
`project/design/proposals/proposed/<slug>/00_proposal.md`
following the LRH proposal schema and body conventions. It interviews the
user, researches related design context, proposes a complete proposal for
review, and writes the file only after explicit confirmation. All output is
shown to the user before any files are written.

---

## Inputs

The user provides a slug as the argument:

```
/lrh-proposal lrh-doc-skills
```

The slug becomes the proposal-set directory name and informs the `id:` field.
If not provided, ask for one before proceeding. Use lowercase-kebab-case.

---

## Reference Knowledge

Load these before running any step:

1. **`references/proposal-schema.md`** — Full YAML frontmatter field reference:
   required fields, valid status values, `implementation_status` vocabulary,
   and optional traceability fields (`implemented_by`, `supersedes`,
   `superseded_by`, `evidence`). Read this to produce valid frontmatter.

2. **`references/proposal-body-guide.md`** — Section-by-section authoring
   guide for the proposal body: what goes in Summary, Background/Motivation,
   Prior Art Check, Design Decisions, Non-Goals, Implementation Plan, and
   cross-references. Read this to produce a body that follows LRH proposal
   conventions.

3. **`references/prior-art-check.md`** — Prior art / build-vs-buy check
   procedure (duplication search + demand search). Run this during Step 3
   (research) and record both verdicts in the `## Prior Art Check` body
   section before drafting Design Decisions.

4. **`references/execution-record.md`** — `lrh prompt label` and
   `lrh prompt check-execution` command syntax, execution record field
   descriptions (`agent`, `instruction_source`, `session_transcript`). Read
   before Step 4 (instruction phase) and Step 10 (execution record).

---

## Execution Steps

Work through these steps in order. Do not skip the confirmation gate (Step 5).

### 1. Check for existing proposal

Search for a file matching the slug under `project/design/proposals/`:

```bash
find project/design/proposals/ -name "00_proposal.md" -path "*<slug>*"
```

Also check for an `id:` conflict in existing proposals:

```bash
grep -r "^id: " project/design/proposals/ | grep -i "<slug>"
```

If found:
- Report the file path and its current `status` and `implementation_status`.
- Ask whether to overwrite, extend, or abort.
- Do not silently overwrite existing work.

### 2. Interview

Ask all questions at once to avoid multiple round-trips. Collect all
answers before proposing anything.

1. **Proposal title and summary:**
   - **Title:** A short one-line title for the `title:` frontmatter field.
   - **Summary:** What design decision, architecture choice, or feature
     direction does this proposal address? One to two sentences suitable
     for the `## Summary` section.

2. **Background / motivation:** What problem or gap motivates this proposal?
   What context does a reader need to evaluate the design? Reference any
   related workstreams, design docs, or prior proposals.

3. **Design decision(s):** What is being decided? List the key options that
   were considered and which option was chosen. This becomes the
   `## Design Decisions` section.

4. **Non-goals:** What is explicitly out of scope? What should a reader not
   assume this proposal addresses?

5. **Implementation scope:** How big is the resulting implementation?
   - One PR worth of work → suggest `/lrh-work-item`
   - Multiple PRs, novel decisions, or uncertain scope → suggest
     `/lrh-workstream` ± `/lrh-work-item`
   - Complex multi-stage → suggest `/lrh-workstream` first, work items later
   This informs the `## Implementation Plan` section and Step 11 follow-on offer.

6. **Related design docs:** Any existing workstream files, design docs, or
   prior proposals that this proposal relates to? Used for `related_design:`.

### 3. Research the project

Before proposing, read:

- `project/design/proposals/README.md` — to understand ID conventions
  (`PROP-*`), lifecycle vocabulary, and proposal-set structure.
- A few similar existing proposals (from `project/design/proposals/`) — to
  follow naming, depth, and cross-reference conventions established in this
  project.
- The related workstream file (if identified) — to understand the broader
  delivery context.

Then propose the complete proposal: frontmatter (all fields) and body
(all required sections with content). Show it to the user before writing.

### 4. Instruction phase (mint prompt ID + idempotence check)

Run (see `references/execution-record.md` for full syntax):

```bash
lrh prompt label --slug <slug>
lrh prompt check-execution --prompt-id "<id>" --project-root .
```

`<PROP-ID>` (the `id:` value decided in Step 2, `PROP-<SLUG-UPPER>`) is not
passed to `--work-item` here — this record documents the proposal's
*creation*, so it stays in the `AD_HOC` bucket (the `lrh prompt label`
default). See `references/execution-record.md`.

If `check-execution` reports a `landed` or `in_progress` record, **stop and
report** — do not continue unless the user explicitly asks for a rerun.

### 5. User confirms

Show the user the complete proposed proposal — frontmatter and full body —
in a readable block.

Wait for explicit confirmation before writing any files.

If the user redirects or declines, adjust the proposal and show it again.
Do not skip this gate — it prevents incorrectly-scoped proposals from
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

Proposals are documentation artifacts; use `feat` as the branch type:

```
xenotaur/feat/lrh-doc-skills
```

### 7. Write files

Re-check that the proposal directory does not already exist on the freshly
pulled main — the Step 1 check may be stale if main advanced since the
session started:

```bash
find project/design/proposals/ -name "00_proposal.md" -path "*<slug>*"
```

If found, stop and report — ask the user to overwrite, extend, or abort
before proceeding.

Create the directory and file:

```
project/design/proposals/proposed/<slug>/00_proposal.md
```

Set `status: proposed`, `implementation_status: not_started`.
The `project/design/proposals/proposed/` directory already exists; do not
recreate it. Create only the `<slug>/` subdirectory and `00_proposal.md`.

### 8. Validate

Run:

```bash
lrh validate
```

Fix any errors before proceeding. Common failures: missing required field
(`id`, `status`, `type`), `status` bucket mismatch (`status: proposed` file
must be under `proposed/`), `type: design_proposal` missing or misspelled.

### 9. Commit and open PR

```bash
git add project/design/proposals/proposed/<slug>/
git commit -m "Add design proposal <PROP-ID>: <title>"
git push -u origin <branch-name>
gh pr create --title "Add design proposal <PROP-ID>: <title>" --body "..."
```

Include in the PR body: the proposal summary, status, `id`, and the prompt
ID minted in Step 4 — it is the traceability link between the PR and the
execution record.

### 10. Create execution record

```bash
lrh prompt record-execution \
  --prompt-id "<id>" \
  --work-item AD_HOC \
  --slug <slug> \
  --status in_progress \
  --project-root .
```

Use `AD_HOC`, not `<PROP-ID>` — see the note in Step 4. This creates the
record under `project/executions/AD_HOC/`, not `project/executions/<PROP-ID>/`.

Immediately edit the generated file to populate the three optional fields
(see `references/execution-record.md`):

```yaml
agent: claude_app
instruction_source: project/design/proposals/proposed/<slug>/00_proposal.md
session_transcript: pending
```

Then replace the generated `TODO` placeholders in `# Summary`, `# Result`,
`# Validation`, and `# Follow-up` with real content grounded in what this
run actually did (per `AGENTS.md`'s evidence policy) — `/lrh-closeout` later
only touches frontmatter, so an unedited TODO body would ship as `landed`
with no narrative evidence.

Commit the execution record and push it as an additional commit to the
already-open PR.

### 11. Offer follow-on and report

**Follow-on artifacts (offer, not automatic):**

Based on the implementation scope assessed in Step 2, offer the user the
appropriate next step:

- **Small scope (one PR):** offer to invoke `/lrh-work-item` to create a
  companion work item.
- **Medium scope (multiple PRs):** check whether `/lrh-workstream` is listed
  in `CLAUDE.md ## Skills`. If it is, offer to invoke it followed by
  `/lrh-work-item` for each immediate task. If it is not yet available,
  direct the user to create a workstream manually at
  `project/workstreams/proposed/<WS-ID>.md` following the workstream schema,
  then offer `/lrh-work-item` for each immediate task.
- **Large scope (multi-stage):** check whether `/lrh-workstream` is listed
  in `CLAUDE.md ## Skills`. If it is, offer to invoke it first; defer
  individual work items until workstream scope is defined. If it is not yet
  available, direct the user to the manual workstream path and defer work
  items.

Do not automatically invoke any skill — offer and wait for the user to confirm.

**Report to the user:**

- The file created and its path.
- The `lrh validate` outcome.
- The PR URL.
- The minted prompt ID and execution record path.
- Which fields were inferred vs. directly from user answers.
- Suggested next steps per the scope assessment above.
- A reminder that `session_transcript: pending` in the execution record
  should be updated to `claude-app:<session-id>` after the session ends.
- Next steps for the PR itself: run `/lrh-review-response <pr-url>` to
  address reviewer comments (repeat as needed), then
  `/lrh-confirm-fixes <pr-url>` to verify the fixes against the current diff
  and resolve the review threads before merge. After merging, run
  `/lrh-closeout <pr-url>` to land this skill's execution record — and any
  additional `_REVIEW`/`_CONFIRM` records the review rounds created — and to
  update the record's status to `landed`.

---

## Quality Checklist

Before reporting completion, verify:

- [ ] Prompt ID minted (Step 4) before the confirm gate (Step 5)
- [ ] Idempotence check passed (no prior landed/in_progress record)
- [ ] Branch created from a fresh `git pull` of main
- [ ] `project/design/proposals/proposed/<slug>/00_proposal.md` exists
- [ ] `id`, `type: design_proposal`, `title`, `status`, `implementation_status`
      all present in frontmatter
- [ ] `status: proposed` and file is in `proposed/` directory bucket
- [ ] `implementation_status: not_started`
- [ ] Body contains all required sections: Summary, Background/Motivation,
      Design Decisions, Non-Goals, Implementation Plan
- [ ] `lrh validate` reports 0 errors
- [ ] The confirm-before-write gate (Step 5) was honoured
- [ ] PR opened and URL reported to the user
- [ ] Execution record exists under `project/executions/AD_HOC/` (not
      `<PROP-ID>/` — see Step 4) with `agent`, `instruction_source`,
      `session_transcript` populated, and `# Summary`/`# Result`/
      `# Validation`/`# Follow-up` filled in with real content, not TODOs
- [ ] Execution record was pushed to the open PR

---

## What This Skill Does Not Do

- Does not create work items or workstreams — use `/lrh-work-item` or
  `/lrh-workstream` for those.
- Does not adopt or supersede proposals — status changes are human decisions.
- Does not implement the design — the skill creates the planning artifact only.
- Does not create sub-proposals or appendices (`01_*.md`) — the umbrella
  `00_proposal.md` only; sub-proposals are added manually or in follow-on work.
- Does not update `project/design/design.md` or `architecture.md` — those
  edits follow adoption and are separate tasks.
- Does not land the execution record it creates for this PR, or mark it
  `landed` — that happens at `/lrh-closeout` after the PR merges.
