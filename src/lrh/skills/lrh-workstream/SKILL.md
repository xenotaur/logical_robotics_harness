---
name: lrh-workstream
description: >
  Create a new LRH workstream planning node at project/workstreams/proposed/<WS-ID>.md.
  Use when the user wants to capture a meaningful stream of related work — design,
  planning, work items, and closeout — as a formal workstream artifact. Interviews the
  user, researches existing workstreams, proposes complete frontmatter and body for review,
  and writes the file only after explicit confirmation. Validates with lrh validate.
disable-model-invocation: true
argument-hint: [WS-ID]
---

# lrh-workstream Skill

This skill creates a new LRH workstream at
`project/workstreams/proposed/<WS-ID>.md`
following the LRH workstream schema and body conventions. It interviews the
user, researches related project context, proposes a complete workstream for
review, and writes the file only after explicit confirmation. All output is
shown to the user before any files are written.

---

## Inputs

The user provides a workstream ID as the argument:

```
/lrh-workstream WS-DOC-SKILLS
```

The ID must be in SCREAMING-KEBAB-CASE and start with `WS-`. If not
provided, ask for one before proceeding.

---

## Reference Knowledge

Load these before running any step:

1. **`references/workstream-schema.md`** — Full YAML frontmatter field
   reference: required fields, `stage` and `status` vocabularies, list
   fields, and conventional optional fields. Read this to produce valid
   frontmatter.

2. **`references/workstream-body-guide.md`** — Section-by-section authoring
   guide for the workstream body: what goes in Purpose, Scope, Prior Art
   Check, Work Items, Exit Criteria, and Non-Goals. Read this to produce a
   body that passes review.

3. **`references/prior-art-check.md`** — Prior art / build-vs-buy check
   procedure (duplication search + demand search). Run this during Step 3
   (research) and record both verdicts in the `## Prior Art Check` body
   section before defining Work Items.

---

## Execution Steps

Work through these steps in order. Do not skip the confirmation gate (Step 4).

### 1. Check for existing workstream

Search all bucket directories for a file whose stem matches the requested ID.
The `project/workstreams/` tree may not exist in freshly bootstrapped repos —
suppress errors and treat an absent directory as "not found":

```bash
find project/workstreams/ -name "<WS-ID>.md" 2>/dev/null
```

If found:
- Report the file path and its current `status` and `stage`.
- Ask whether to overwrite, extend, or abort.
- Do not silently overwrite existing work.

### 2. Interview

Ask all questions at once to avoid multiple round-trips. Collect all
answers before proposing anything.

1. **Title and summary:**
   - **Title:** A short one-line title for the `title:` frontmatter field.
   - **Summary:** What stream of work does this workstream coordinate? One
     to two sentences suitable for the `summary:` frontmatter field and the
     `## Purpose` body section.

2. **Motivation / rationale:** Why does this workstream exist now? What gap
   or opportunity does it address? What context does a reader need to
   understand the grouping?

3. **Initial scope and work items:** What work items (if any) are already
   known or proposed for this workstream? List `WI-*` IDs or describe the
   planned work in terms of deliverables. These go in `work_items:` and the
   body.

4. **Exit criteria:** What conditions must be true before this workstream can
   be closed? Two to five concrete, verifiable conditions. These become the
   `exit_criteria:` list and the `## Exit Criteria` body section.

5. **Related design docs:** Any existing proposals, design docs, or focus
   files that this workstream is grounded in? Used for `related_design:`,
   `related_focus:`, and `related_roadmap:`.

6. **Stage:** Where in the lifecycle does this workstream start?
   - `conceived` — idea not yet assessed
   - `assessed` — pros/cons reviewed, direction chosen
   - `designed` — design reviewed, approach locked
   - `planned` — roadmap, focus, and work items defined
   Offer `conceived` as the default if unsure.

### 3. Research the project

Before proposing, read:

- `project/workstreams/README.md` — to understand lifecycle conventions,
  status/stage vocabulary, and the expected relationship to work items.
- A few similar existing workstreams (from `project/workstreams/`) — to
  follow naming, scope, and exit-criteria conventions.
- The related design proposals and focus files (if identified) — to ground
  the workstream in the project's current direction.

Then propose the complete workstream: frontmatter (all fields) and body
(all required sections with content). Show it to the user before writing.

### 4. User confirms

Show the user the complete proposed workstream — frontmatter and full body —
in a readable block.

Wait for explicit confirmation before writing any files.

If the user redirects or declines, adjust the proposal and show it again.
Do not skip this gate — it prevents incorrectly-scoped workstreams from
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

Workstreams are planning artifacts; use `feat` as the branch type:

```
xenotaur/feat/ws-doc-skills
```

### 6. Write file

Re-check that the workstream does not already exist on the freshly pulled
main — the Step 1 check may be stale:

```bash
find project/workstreams/ -name "<WS-ID>.md" 2>/dev/null
```

If found, stop and report — ask the user to overwrite, extend, or abort
before proceeding.

Create the bucket directory if it does not exist, then write the file:

```bash
mkdir -p project/workstreams/proposed/
```

Create `project/workstreams/proposed/<WS-ID>.md` with the confirmed content.
Set `status: proposed`, `stage: <chosen>` (default `conceived`).

### 7. Validate

Run:

```bash
lrh validate
```

Fix any errors before proceeding. Common failures: missing required field
(`id`, `kind`, `title`, `status`, `stage`), `kind` not `planning_node`,
`status` value not in vocabulary, `stage` value not in vocabulary, filename
stem does not match `id`.

### 8. Commit and open PR

```bash
git add project/workstreams/proposed/<WS-ID>.md
git commit -m "Add workstream <WS-ID>: <title>"
git push -u origin <branch-name>
gh pr create --title "Add workstream <WS-ID>: <title>" --body "..."
```

Include in the PR body: the workstream summary, stage, and any work items
already listed.

### 9. Offer follow-on and report

**Follow-on actions (offer, not automatic):**

- **Link existing work items:** if any `WI-*` IDs were identified in Step 2,
  offer to read their current `related_workstreams:` field and add `<WS-ID>`
  to each. Wait for approval before editing; commit each change and push to
  the open PR.
- **Create new work items:** if the workstream scope implies immediate work
  items not yet created, offer to invoke `/lrh-work-item` to create them.

**Report to the user:**

- The file created and its path.
- The `lrh validate` outcome.
- The PR URL.
- Which fields were inferred vs. directly from user answers.
- Suggested next steps: design review → update `related_design`; define
  focus/roadmap references; populate `work_items:` as items are created.

---

## Quality Checklist

Before reporting completion, verify:

- [ ] Branch created from a fresh `git pull` of main
- [ ] `project/workstreams/proposed/<WS-ID>.md` exists
- [ ] Filename stem exactly matches the `id` frontmatter field
- [ ] Required fields present: `id`, `kind: planning_node`, `title`,
      `status`, `stage`
- [ ] `status: proposed` and file is in `proposed/` directory bucket
- [ ] `stage` value is in the allowed vocabulary
- [ ] `lrh validate` reports 0 errors
- [ ] The confirm-before-write gate (Step 4) was honoured
- [ ] PR opened and URL reported to the user

---

## What This Skill Does Not Do

- Does not create work items — use `/lrh-work-item` for those.
- Does not create design proposals — use `/lrh-proposal` for those.
- Does not advance the workstream lifecycle — stage and status changes are
  human decisions.
- Does not automatically populate `work_items:` from existing proposed items
  — Step 9 offers; the user decides.
- Does not create sub-workstreams or recursive planning hierarchies — the
  skill creates one planning node; children are linked separately.
- Does not update `project/design/`, roadmap, or focus files — those edits
  are separate tasks after the workstream is created.
