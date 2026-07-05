---
name: lrh-readiness
description: >
  Close the ready-work-item apply loop for a thin LRH work item. Runs
  lrh work-items readiness <WI-ID>; if already ready, reports and stops. If
  not ready, runs lrh request ready-work-item <WI-ID>, drafts a Proposed
  Work-Item Patch from the rendered request, shows it for confirmation,
  applies it only after approval, re-validates readiness, and commits.
  Provide a WI-* ID as the argument.
disable-model-invocation: true
argument-hint: "[WI-ID]"
---

# lrh-readiness Skill

`lrh request ready-work-item` renders a non-mutating refinement request for a
thin work item, but it does not draft or apply a patch — that step is left to
a human or coding assistant reading the rendered request. No skill closes
that loop today: `/lrh-implement` Step 1 only warns on a not-ready item and
proceeds anyway; nothing turns the rendered request into an applied,
re-validated fix. This skill closes it, following the same confirm-gate →
write → validate pattern every other LRH skill uses for its own artifact
type.

---

## Inputs

Provide a work item ID as the argument:

```
/lrh-readiness WI-AGENT-BRANCH-CONTAINMENT
```

If not provided, ask for one before proceeding.

---

## Reference Knowledge

No references are needed. This skill wraps two existing CLI commands
(`lrh work-items readiness`, `lrh request ready-work-item`) plus a confirm
gate; the drafting protocol is embedded in the execution steps below.

---

## Execution Steps

Work through these steps in order. Do not skip Step 4 (confirm gate).

### Step 1 — Check readiness

Locate the work item:

```bash
find project/work_items/ -name "<WI-ID>.md"
```

If not found, stop and report.

```bash
lrh work-items readiness <WI-ID> --format md
```

If `prompt_ready: yes`: report this to the user and stop. Take no further
action — do not re-run `ready-work-item` on an already-ready item.

If `prompt_ready: no`: note the `blocking:` list and proceed to Step 2.

### Step 2 — Render the refinement request

```bash
lrh request ready-work-item <WI-ID>
```

This renders a non-mutating Markdown request. It is not itself a patch —
do not show or apply this raw output as if it were the fix.

### Step 3 — Draft the patch

Follow the rendered request's own "Expected Response Shape"
(`src/lrh/assist/templates/request/ready_work_item.md:56-64`). Draft all
five sections:

1. `## Grounded Facts` — facts copied or summarized from the target item and
   its resolved context (`related_roadmap`, `related_focus`, `related_design`,
   `related_workstreams`, `depends_on`).
2. `## Proposed Work-Item Patch` — the actual Markdown patch or replacement
   body sections, addressing the `blocking:` list from Step 1.
3. `## Grounding Notes` — which proposed bullets came from which artifacts.
4. `## Open Questions` — unresolved references, missing validation
   specifics, or decisions requiring human review.
5. `## Non-Goals Confirmed` — implementation work intentionally left
   untouched (refining the work item is not implementing it).

Ground every proposed line in the work item itself or its referenced
artifacts. Do not invent scope — unresolved context becomes an Open
Question, not a guess.

### Step 4 — Confirm gate (human gate)

Show the user the full drafted response from Step 3 — all five sections.

**Wait for explicit confirmation before touching any files.** If the user
redirects (requests changes, disputes a grounding claim, wants an Open
Question resolved first), revise and show again. Do not proceed past this
gate without approval.

### Step 5 — Apply the patch

Read the current work item file. Apply only the sections confirmed at
Step 4 — typically inserting or replacing the missing body sections named
in Step 1's `blocking:` list. Do not touch sections the user did not
confirm, and do not silently absorb scope beyond what was shown.

### Step 6 — Re-validate

```bash
lrh work-items readiness <WI-ID> --format md
lrh validate
```

If `prompt_ready` is now `yes`: proceed to Step 7.

If still `no`: report the remaining `blocking:` items to the user. Do not
force the item through or invent content to satisfy the remaining gaps.

### Step 7 — Commit

Check whether the work item already has an open PR:

```bash
gh pr list --state open --search "<WI-ID>"
```

If an open PR is found: check out its branch and commit there as an
additional commit — do not open a competing PR.

If none is found: create a new branch from a fresh `main` and open a PR,
following the same branch-naming convention as `/lrh-work-item`
(`<username>/<type>/<slug>-readiness`, type derived from the work item's
`type` field):

```bash
git checkout main && git pull
git checkout -b <branch-name>
git add project/work_items/<bucket>/<WI-ID>.md
git commit -m "Refine <WI-ID> toward prompt-readiness"
git push -u origin <branch-name>
gh pr create --title "Refine <WI-ID> toward prompt-readiness" --body "..."
```

### Step 8 — Report

Report to the user:

- Whether the item was already ready, or a one-line summary of what was
  added
- The re-validated `prompt_ready` status
- PR URL (existing or newly opened)
- Any remaining Open Questions or blocking items

---

## Quality Checklist

Before reporting completion, verify:

- [ ] `lrh work-items readiness` checked before any other action
- [ ] If already ready, no further action was taken
- [ ] If not ready, the rendered request was used to draft a patch — the
      raw rendered request was never shown or applied as the fix
- [ ] User confirmed at Step 4 before any files were touched
- [ ] Only the confirmed sections were applied
- [ ] `lrh work-items readiness` and `lrh validate` re-run after applying
- [ ] Existing open PR reused if one exists; no competing PR opened

---

## What This Skill Does Not Do

- Does not batch-process multiple work items in one invocation.
- Does not touch the execution-readiness schema
  (`src/lrh/control/execution_readiness.py`) — an unrelated concept covering
  opt-in autonomous-execution metadata, not prompt-readiness.
- Does not change `/lrh-implement`'s Step 1 behavior — it still warns and
  does not hard-block; this skill is an optional prerequisite step, not a
  replacement.
- Does not apply any patch content without an explicit confirmation gate.
- Does not invent scope for Open Questions — unresolved context stays
  unresolved until a human resolves it.
- Does not implement the work item's underlying task — refining readiness
  is not implementation; use `/lrh-implement` once the item is ready.
