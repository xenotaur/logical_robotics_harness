---
name: lrh-workstream
description: >
  Create a new LRH workstream planning node at project/workstreams/proposed/<WS-ID>.md.
  Use when the user wants to capture a meaningful stream of related work — design,
  planning, work items, and closeout — as a formal workstream artifact. Interviews the
  user, researches existing workstreams, proposes complete frontmatter and body for review,
  and writes the file only after explicit confirmation. Validates with lrh validate.
when_to_use: >
  Invoke only when explicitly creating a new LRH workstream planning
  artifact in project/workstreams/proposed/. Do not invoke when the user
  is discussing, reading, or querying workstreams. Suitable for
  orchestration from /lrh-design or /lrh-proposal when those skills need
  to create a companion workstream as part of a design-capture workflow.
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

4. **`references/execution-record.md`** — `lrh prompt label` and
   `lrh prompt check-execution` command syntax, execution record field
   descriptions (`agent`, `instruction_source`, `session_transcript`). Read
   before Step 4 (instruction phase) and Step 10 (execution record).

---

## Execution Steps

Work through these steps in order. Do not skip the confirmation gate (Step 5).

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

### 4. Instruction phase (mint prompt ID + idempotence check)

Derive `<slug>` from the workstream ID (lower-kebab): `WS-DOC-SKILLS` →
`ws-doc-skills`.

**Before minting, check for an existing record by stable slug — the
current checkout and any open PRs.** `lrh prompt label` always mints a
fresh timestamped prompt ID, so `check-execution --prompt-id` alone
cannot detect a rerun — the ID it receives is brand new every time it's
called. Use the slug-based mode instead:

```bash
lrh prompt check-execution --slug <slug> --work-item AD_HOC --project-root .
```

This is the mechanism `DEC-PRE-MINT-SLUG-IDEMPOTENCE-DEFAULT` describes
and `WI-SLUG-IDEMPOTENCE-CLI-TOOLING` implements: it matches the complete
trailing filename segment (not a bare substring), searches the local
checkout and every open PR (including forks) via `refs/pull/<N>/head`,
excludes matches a PR only *inherited* via `git merge-base` against its
declared base ref (so a stacked PR never shadows the PR that actually
introduced the record), and selects the truly most recent match by parsed
`created_at:` rather than filename order (execution-record filename
timestamps are not reliably chronological across machines — see
`project/design/backlog.md`'s "Execution-record filename timestamps use
local time, not UTC").

Interpret the exit code:
- **`1` — blocking match:** either a `landed`/`in_progress` match (the
  default per `DEC-PRE-MINT-SLUG-IDEMPOTENCE-DEFAULT`), or a match whose
  status is `planned` or otherwise unrecognized — an unresolved outcome
  blocks too, since it is not license to proceed. This also fires when
  any match's recency can't be established (a missing or malformed
  `created_at`), even if every match's status is otherwise terminal — the
  printed message distinguishes "BLOCKING (unresolved recency)" from an
  ordinary blocking-status match, but both are exit `1`. **Stop and
  report** — do not continue unless the user explicitly asks for a rerun.
  If they do, see Step 6 for how to resume the match's branch
  (`<username>/<type>/<slug>`) whether it's local, remote-only, or gone.
  Either way, keep the printed `execution_id` to pass as `--rerun-of` in
  Step 10.
- **`0` with a match printed** (`failed`/`reverted`/`superseded` only):
  summarize it and continue, but keep its `execution_id` to pass as
  `--rerun-of` in Step 10 (per `PROMPTS.md:136`, a rerun must link back to
  the prior attempt it supersedes).
- **`0` with no match printed:** no prior record — proceed.
- **`3` — the check itself failed** (a `gh`/`git` error surfaced on
  stderr): **stop and report** the error. This is not the same as "no
  prior record" — the command fails loudly rather than guessing, so
  treat it as a blocker, not a green light.
- **`2` — malformed input** (argparse rejected `--slug`/`--work-item`, or
  both/neither of `--slug`/`--prompt-id` were given): a usage error, not a
  slug-check result. **Stop and report** — this indicates the derived
  `<slug>`/work-item value itself is invalid, not a prior-execution
  finding.

Then mint the prompt ID and run the secondary check (see
`references/execution-record.md` for full syntax):

```bash
lrh prompt label --slug <slug>
lrh prompt check-execution --prompt-id "<id>" --project-root .
```

Do not pass `--work-item <WS-ID>` here. This record documents the workstream's
*creation*, not a resolved deliverable, so it stays in the `AD_HOC` bucket
(the `lrh prompt label` default) — see `references/execution-record.md`.

If `check-execution` reports a `landed` or `in_progress` record, **stop and
report** — do not continue unless the user explicitly asks for a rerun.

### 5. User confirms

Show the user the complete proposed workstream — frontmatter and full body —
in a readable block.

Wait for explicit confirmation before writing any files.

If the user redirects or declines, adjust the proposal and show it again.
Do not skip this gate — it prevents incorrectly-scoped workstreams from
being committed to the control plane.

### 6. Create branch from main

If Step 4 found a blocked match and the user asked for a rerun, resume its
branch rather than creating a duplicate. Check local first, then the
remote — the common case is that the branch only exists as
`origin/<branch-name>` (the match came from the cross-PR search, not the
current checkout), not locally yet. This same check covers the
no-prior-match case too — if the branch exists nowhere, the `else` clause
creates it fresh from `main`, same as always.

If the match came from the cross-PR search (tagged `PR#<N>` in Step 4),
check whether it's a fork PR before assuming reuse is possible:
`gh pr view <N> --json isCrossRepository`. A fork PR's branch lives in a
repository you don't have push access to — stop and ask the user how to
proceed (e.g. they push further commits themselves, or this becomes a
fresh attempt) rather than silently trying to continue it. Otherwise (the
normal same-repo case), get the branch name (`gh pr view <N> --json
headRefName`) and reuse it as below:

```bash
if git rev-parse --verify <branch-name> >/dev/null 2>&1; then
  git checkout <branch-name>
  git pull
elif git ls-remote --exit-code --heads origin <branch-name> >/dev/null 2>&1; then
  git fetch origin <branch-name>
  git checkout -b <branch-name> --track "origin/<branch-name>"
else
  git checkout main && git pull
  git checkout -b <branch-name>
fi
```

Branch naming: `<username>/<type>/<slug>`. Get the username:

```bash
gh api user --jq .login
```

Workstreams are planning artifacts; use `feat` as the branch type:

```
xenotaur/feat/ws-doc-skills
```

### 7. Write file

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

### 8. Validate

Run:

```bash
lrh validate
```

Fix any errors before proceeding. Common failures: missing required field
(`id`, `kind`, `title`, `status`, `stage`), `kind` not `planning_node`,
`status` value not in vocabulary, `stage` value not in vocabulary, filename
stem does not match `id`.

### 9. Commit and open PR

```bash
git add project/workstreams/proposed/<WS-ID>.md
git commit -m "Add workstream <WS-ID>: <title>"
git push -u origin <branch-name>
gh pr create --title "Add workstream <WS-ID>: <title>" --body "..."
```

Include in the PR body: the workstream summary, stage, any work items
already listed, and the prompt ID minted in Step 4 — it is the traceability
link between the PR and the execution record.

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

Use `AD_HOC`, not `<WS-ID>` — see the note in Step 4. This creates the
record under `project/executions/AD_HOC/`, not `project/executions/<WS-ID>/`.

Immediately edit the generated file to populate the three optional fields
(see `references/execution-record.md`):

```yaml
agent: <agent-backend>
instruction_source: project/workstreams/proposed/<WS-ID>.md
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
- The minted prompt ID and execution record path.
- Which fields were inferred vs. directly from user answers.
- Suggested next steps: design review → update `related_design`; define
  focus/roadmap references; populate `work_items:` as items are created.
- A reminder that `session_transcript: pending` in the execution record
  should be updated to the durable session pointer for the selected backend
  when one is available.
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
- [ ] `project/workstreams/proposed/<WS-ID>.md` exists
- [ ] Filename stem exactly matches the `id` frontmatter field
- [ ] Required fields present: `id`, `kind: planning_node`, `title`,
      `status`, `stage`
- [ ] `status: proposed` and file is in `proposed/` directory bucket
- [ ] `stage` value is in the allowed vocabulary
- [ ] `lrh validate` reports 0 errors
- [ ] The confirm-before-write gate (Step 5) was honoured
- [ ] PR opened and URL reported to the user
- [ ] Execution record exists under `project/executions/AD_HOC/` (not
      `<WS-ID>/` — see Step 4) with `agent`, `instruction_source`,
      `session_transcript` populated, and `# Summary`/`# Result`/
      `# Validation`/`# Follow-up` filled in with real content, not TODOs
- [ ] Execution record was pushed to the open PR

---

## What This Skill Does Not Do

- Does not create work items — use `/lrh-work-item` for those.
- Does not create design proposals — use `/lrh-proposal` for those.
- Does not advance the workstream lifecycle — stage and status changes are
  human decisions.
- Does not automatically populate `work_items:` from existing proposed items
  — Step 11 offers; the user decides.
- Does not create sub-workstreams or recursive planning hierarchies — the
  skill creates one planning node; children are linked separately.
- Does not update `project/design/`, roadmap, or focus files — those edits
  are separate tasks after the workstream is created.
- Does not land the execution record or mark it `landed` — that happens at
  `/lrh-closeout` after the PR merges.
