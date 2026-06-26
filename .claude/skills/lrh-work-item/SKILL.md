---
name: lrh-work-item
description: >
  Create a new LRH work item in project/work_items/proposed/. Use when the
  user wants to capture a deliverable, operation, investigation, or evaluation
  as a formal work item. Interviews the user, researches related workstreams
  and focus, proposes complete frontmatter and body sections, and writes the
  file after explicit confirmation. Validates with lrh validate.
disable-model-invocation: true
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

---

## Execution Steps

Work through these steps in order. Do not skip the confirmation gate (Step 4).

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

Then propose the complete work item: frontmatter (all fields) and body
(all required sections with content). Show it to the user before writing.

### 4. User confirms

Show the user the complete proposed work item — frontmatter and full body —
in a readable block.

Wait for explicit confirmation before writing any files.

If the user redirects or declines, adjust the proposal and show it again.
Do not skip this gate — it prevents incorrectly-scoped work items from
being committed to the control plane.

### 5. Create branch from main

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

### 6. Write file

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

### 7. Validate

Run:

```bash
lrh validate
```

Fix any errors before proceeding. Common failures: required frontmatter field
missing, `status` value does not match directory bucket, filename stem does
not match `id` field.

### 8. Commit and open PR

Stage and commit the work item file:

```bash
git add project/work_items/proposed/<ID>.md
git commit -m "Add work item <ID>: <title>"
git push -u origin <branch-name>
gh pr create --title "Add work item <ID>: <title>" --body "..."
```

Include in the PR body: the work item summary, type, related workstream, and
acceptance criteria.

### 9. Offer workstream update and report

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
- Which fields were inferred vs. directly from user answers — be explicit
  so the user can correct mismatches.
- Suggested next steps per `references/lrh-work-item-workflow.md`.

---

## Quality Checklist

Before reporting completion, verify:

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
- [ ] The confirm-before-write gate (Step 4) was honoured
- [ ] PR opened and URL reported to the user

---

## What This Skill Does Not Do

- Does not refine existing thin work items — use
  `lrh request ready-work-item <ID>` for that.
- Does not promote work items to `active` or `resolved` — status changes
  are human decisions.
- Does not implement the work item — it creates the planning artifact only.
- Does not automatically update workstreams — Step 9 offers; the user
  decides.
- Does not create execution records — those are produced during
  implementation.
- Does not run `lrh request prompt-from-work-item` — that is a separate
  step after the item has been refined to readiness.
