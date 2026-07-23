---
name: lrh-doc-organize
description: >
  Implement one scoped phase of Diataxis-informed documentation reorganization
  as a reviewable PR. Reads the "Proposed first PR scope" section from a
  docs-audit artifact produced by /lrh-doc-audit (or runs a small discovery
  pass if no audit is provided), confirms the scope with the user, creates a
  branch, implements file moves/stubs/README updates, validates, and opens a
  PR. One phase per invocation — use /lrh-doc-audit first for best results.
disable-model-invocation: true
argument-hint: "[audit-path] [--phase N]"
---

# lrh-doc-organize Skill

This skill implements one scoped phase of documentation reorganization as a
reviewable PR. It reads the scope from a docs-audit artifact produced by
`/lrh-doc-audit`, or runs a small discovery pass when no audit is available.
It does not audit docs (that is `/lrh-doc-audit`) and does not update docs to
reflect new work (that is `/lrh-doc-work`).

---

## Inputs

Provide an optional path to a docs-audit artifact and an optional phase number:

```
/lrh-doc-organize
/lrh-doc-organize project/audits/docs/docs-audit-2026-06-27.md
/lrh-doc-organize project/audits/docs/docs-audit-2026-06-27.md --phase 2
```

Without an argument the skill checks for the most recent audit artifact at
`project/audits/docs/`. If none exists, it runs a small discovery pass to
derive a scope. `--phase N` selects a specific phase from the audit's
"Recommended phased PRs" section; without it, phase 1 ("Proposed first PR
scope") is used.

---

## Reference Knowledge

Load these before running any step:

1. **`references/organize-constraints.md`** — Scope source rules, path-preservation
   requirements, README update rules, Diataxis boundary rules, planned-vs-implemented
   distinction. Read at Steps 4–5 and apply throughout Step 8.

2. **`references/organize-workflow.md`** — Lifecycle placement (relationship to
   `/lrh-doc-audit` and `/lrh-doc-work`), one-phase-per-PR rule, execution
   record convention. Read before Step 6 and Step 11.

3. **`references/diataxis-criteria.md`** — Four-quadrant definitions and
   classification heuristics. Read at Step 5 when evaluating scope.

<!-- Template counterpart: src/lrh/assist/templates/request/organize_docs.md -->

---

## Execution Steps

Work through these steps in order. Do not skip Step 6 (confirm gate).

### Step 1 — Parse input

Determine the audit path and phase:

- If `[audit-path]` was provided: use it. Verify the file exists; if not,
  stop and report.
- If omitted: check `project/audits/docs/` for any `docs-audit-*.md` file.
  Use the most recent (by filename date). If none exists, proceed to
  discovery mode in Step 4.
- If `--phase N` was provided: record N as the target phase. Otherwise use
  phase 1.

### Step 2 — Load references

Read `references/organize-constraints.md`, `references/organize-workflow.md`,
and `references/diataxis-criteria.md` in full before proceeding. The
constraint rules (Step 8) and scope evaluation (Step 5) derive from these
files.

### Step 3 — Mint prompt ID + idempotence check

Before reading any files or making any changes, mint a prompt ID:

```bash
lrh prompt label --slug doc-organize-phase-<N>-<YYYY-MM-DD>
lrh prompt check-execution --prompt-id "<id>" --project-root .
```

Use the phase number from Step 1 (default 1) and today's date for the slug.
Store the prompt ID for use in Step 11 (execution record).

If `check-execution` reports a `landed` or `in_progress` record, **stop and
report** — do not continue unless the user explicitly asks for a rerun.

### Step 4 — Read audit or run discovery pass

**Audit mode (audit artifact found):**

Read the full audit artifact. Locate the target phase:
- Phase 1: the "Proposed first PR scope" section
- Phase N (N > 1): the Nth entry in "Recommended phased PRs"

Extract the concrete file actions listed for that phase. These become the
candidate scope for Step 5.

**Discovery mode (no audit artifact):**

Run a small discovery pass to derive a minimal scope:
1. Walk `docs/` (or the evident docs root) and note obvious Diataxis
   mis-placements (e.g., a how-to in a `reference/` folder).
2. Check top-level README.md for outdated structure references.
3. Identify no more than 5–8 concrete, low-risk improvements suitable for
   a single PR.
4. Do not make broad inferences — scope conservatively.

Flag to the user at Step 6 that the scope was derived from discovery, not
from a `/lrh-doc-audit` artifact, and recommend running the audit first.

### Step 5 — Scope one phase

Review the candidate scope from Step 4 against the constraints in
`references/organize-constraints.md`:

- Are moved paths preserved or stubbed so existing links survive?
- Are all changes within the docs layer (not `project/`)?
- Does each move respect Diataxis quadrant boundaries?
- Are any items listed as planned (not yet implemented)?
- Is the total scope achievable in a single reviewable PR?

Trim or flag any items that violate constraints. The result is the confirmed
candidate scope for Step 6.

### Step 6 — Confirm gate (human gate)

Before creating a branch or touching any files, show the user:

- Source of scope (audit artifact path + phase, or discovery mode)
- Confirmed list of file actions (moves, stubs, README edits) with source
  and destination for each
- Any items trimmed from the candidate scope and why
- Any discovery-mode warning (recommend running `/lrh-doc-audit` first)

**Wait for explicit confirmation.** If the user adjusts scope, update the
list and re-show. Do not proceed past this gate without approval.

### Step 7 — Create branch

```bash
git checkout main && git pull
git checkout -b <username>/chore/doc-organize-phase-<N>-<YYYY-MM-DD>
```

Get `<username>` from `gh api user --jq .login`. Use `chore` branch type
(documentation reorganization is not a deliverable feature). Include the
phase number and date to make concurrent organize runs distinguishable.

### Step 8 — Implement

Execute each confirmed file action from Step 6. For every file moved or
renamed, apply the rules from `references/organize-constraints.md`:

**Path preservation:** if any existing markdown file links to the moved path,
either update the links or create a redirect stub at the old path pointing
to the new location. Do not silently break links.

**README updates:** for every directory that gains or loses a file, update
that directory's `README.md` (or create one if absent and the directory now
has enough content to warrant it).

**Diataxis boundaries:** if a file is moved into a quadrant folder, verify
its content matches that quadrant. If it does not, note the mismatch in the
PR description rather than forcing a mis-classified file into a folder.

**Planned vs. implemented:** do not create docs for features that do not yet
exist. If the audit scope listed a stub for a planned feature, create the stub
only if it is clearly marked as "planned" or "coming soon."

Keep the change surface minimal — no drive-by formatting, unrelated content
edits, or refactors beyond the confirmed scope.

### Step 9 — Validate

Run the canonical sequence:

```bash
scripts/version tools
scripts/format --check --diff
scripts/lint
scripts/test
lrh validate
```

Format and lint failures are unlikely for pure doc moves (no Python changes),
but run them. If any stale links were broken by the moves, fix them now.
Do not open a PR with broken links introduced by this change.

### Step 10 — Commit and open PR

Stage and commit all changes. Push and open a PR:

```bash
gh pr create --title "docs: reorganize phase <N> — <brief description>" \
             --body "..."
```

Include in the PR body:
- Source audit artifact (or "discovery mode")
- Phase number and brief description of scope
- List of files moved/created/updated
- Any deferred items and why they were not included

### Step 11 — Create execution record

```bash
lrh prompt record-execution \
  --prompt-id "<id>" \
  --work-item AD_HOC \
  --slug doc-organize-phase-<N>-<YYYY-MM-DD> \
  --status in_progress \
  --project-root .
```

Use the prompt ID minted in Step 3. Populate optional fields:

```yaml
agent: claude_app
instruction_source: <audit-path or "discovery mode — no audit available">
session_transcript: pending
```

Run `lrh validate`, commit the record as an additional commit to the open PR,
and push.

Then report the PR URL, the execution record path, and the next steps: run
`/lrh-review-response <PR-URL>` to address reviewer comments (repeat as
needed), then `/lrh-confirm-fixes <PR-URL>` to verify the fixes against the
current diff and resolve the review threads before merge. After merging, run
`/lrh-closeout <PR-URL>` to land the execution record and update the control
plane. If more phases remain, `/lrh-doc-organize` runs again for the next one
only after this phase's PR is merged and closed out.

---

## Quality Checklist

Before reporting completion, verify:

- [ ] Prompt ID minted at Step 3 before any file reads or changes
- [ ] Idempotence check passed (no prior landed/in_progress record)
- [ ] References read at Step 2 before any implementation work
- [ ] Audit artifact located or discovery mode declared at Step 4
- [ ] Scope reviewed against all constraints in `organize-constraints.md`
- [ ] User confirmed the exact file action list at Step 6
- [ ] Branch created from a fresh `git pull` of main
- [ ] Every moved path preserved or stubbed (no silent link breakage)
- [ ] Every touched directory's README updated
- [ ] No files moved across the `project/`–`docs/` boundary
- [ ] `lrh validate` passes with 0 errors after execution record added
- [ ] Execution record committed as additional commit to the open PR

---

## What This Skill Does Not Do

- Does not audit documentation — use `/lrh-doc-audit` first
- Does not update docs to reflect completed work — that is `/lrh-doc-work`
- Does not implement more than one phase per invocation
- Does not reorganize the LRH `project/` control plane — docs only
- Does not rewrite doc content, fix prose, or make formatting changes beyond
  the confirmed scope
