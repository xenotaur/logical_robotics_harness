---
resolution: implemented
blocked_reason: null
blocked: false
id: WI-SKILLS-NEXT-STEP-CHAIN
title: Repair the post-PR next-step chain across the LRH skills
type: operation
status: resolved
owner: anthony
contributors:
  - anthony
assigned_agents: []
related_focus: []
related_roadmap: []
related_workstreams: []
related_design:
  - project/design/proposals/adopted/lrh-closeout/00_proposal.md
depends_on: []
blocked_by: []
expected_actions:
  - edit_file
  - create_file
forbidden_actions:
  - force_push
  - delete_branch
  - implement_lrh_proposal
  - implement_lrh_workstream
  - implement_lrh_design_step4
acceptance:
  - Every skill that opens a PR names /lrh-review-response as the next step
  - Every skill that ends a lifecycle stage names /lrh-closeout as the post-merge step
  - lrh-implement names /lrh-confirm-fixes between review response and merge
  - lrh-confirm-fixes names /lrh-closeout in its green-verdict report
  - lrh-work-item-workflow.md closeout section points at /lrh-closeout instead of a manual procedure
  - src/lrh/skills/_shared/lifecycle-chain.md enumerates every consuming site
  - diff -r src/lrh/skills .claude/skills reports differences only for _shared, installer.py, __init__.py, and __pycache__
  - lrh validate reports 0 errors
required_evidence:
  - manual_review
  - lrh_validate
  - test_run
artifacts_expected:
  - src/lrh/skills/_shared/lifecycle-chain.md
  - src/lrh/skills/lrh-work-item/references/lrh-work-item-workflow.md
  - src/lrh/skills/lrh-implement/SKILL.md
  - src/lrh/skills/lrh-confirm-fixes/SKILL.md
  - src/lrh/skills/lrh-proposal/SKILL.md
  - src/lrh/skills/lrh-workstream/SKILL.md
  - src/lrh/skills/lrh-readiness/SKILL.md
  - src/lrh/skills/lrh-doc-work/SKILL.md
  - src/lrh/skills/lrh-doc-organize/SKILL.md
  - src/lrh/skills/lrh-doc-audit/SKILL.md
  - src/lrh/skills/lrh-create-skill/SKILL.md
---

## Summary

Make every LRH skill that hands control back to the user after opening a PR
name the correct next command in the lifecycle chain
(`/lrh-review-response` → `/lrh-confirm-fixes` → merge → `/lrh-closeout`),
and record the canonical chain text once at
`src/lrh/skills/_shared/lifecycle-chain.md` with an index of every site that
inlines it. Guidance text only — no behavioral or workflow-step changes.

## Problem / Context

The LRH skills end with next-step suggestions that are supposed to chain into
each other so a session walks the full lifecycle. The chain is broken: a
Taurcode session followed `/lrh-work-item`'s own guidance, opened a planning
PR, was told nothing about review response, and proposed jumping to the next
build phase — leaving the control plane un-updated. The user corrected it by
hand.

The cause is historical rather than accidental. `/lrh-closeout` describes
itself in `src/lrh/skills/lrh-closeout/SKILL.md` as "the missing complement to
`/lrh-implement` and `/lrh-review-response` in the LRH execution lifecycle"
(`PROP-LRH-CLOSEOUT`, adopted). It was added after the skills that should
point at it, and those upstream skills were never back-updated. The same is
true of `/lrh-confirm-fixes` (`PROP-LRH-CONFIRM-FIXES`).

`src/lrh/skills/lrh-review-response/SKILL.md:245` is the one correct site — it
suggests `/lrh-confirm-fixes <pr-url>` before merge. Its phrasing is the model
for the rest.

### Prior Art Check

#### Duplication search

- In-repo: No existing implementation found. `grep -rl "lrh-closeout\|next step\|next-step" project/work_items/proposed/ project/design/proposals/proposed/` returns only `meta-operational-triage-semantics`, `workstream-execution-framework/03_layer3_workstream_orchestration.md`, and `lrh-open-work` — none of which address inter-skill next-step guidance. `src/lrh/skills/_shared/` contains only `prior-art-check.md`.
- Sibling repos: Taurcode (`/Users/centaur/Workspace/Taurcode/taurcode`) has its own LRH-like control plane and consumes these skills, but does not own them; it is the reporter of the defect, not a duplicate implementation.
- External libraries: None identified — this is repo-specific skill documentation.
- Recommendation: Proceed.

#### Demand search

- Work items: None found. No proposed work item covers skill-chaining guidance.
- Proposals: None found. `PROP-LRH-CLOSEOUT` and `PROP-LRH-CONFIRM-FIXES` are both adopted and implemented; neither includes back-updating upstream skills.
- Backlog: No matching entries. `grep -i "chain\|next step\|closeout" project/design/backlog.md` returns nothing.
- Recommendation: No action.

## Scope

- Next-step guidance text in skill documents under `src/lrh/skills/`, mirrored
  to `.claude/skills/`.
- One new canonical maintainer document at
  `src/lrh/skills/_shared/lifecycle-chain.md`.

## Design Decision — canonical source, inline delivery

The chain text is needed at ten sites (see Required Changes), well past the
four-site threshold at which a single shared document is worth its sync cost.
But the established `_shared/` convention — mirror the master into each
consuming skill's `references/` as a `SYNCED COPY` — is the wrong mechanism
here, for three reasons:

1. `_shared/prior-art-check.md` is a ~120-line **procedure the skill executes
   mid-run**, so it must be runtime-loadable from `references/`. The lifecycle
   chain is ~5 lines of **report text the skill emits at the end**; loading a
   file to learn what to say is a cost paid on every run of ten skills for no
   benefit.
2. Mirroring would produce twenty copies (ten `references/` plus ten
   `.claude/` mirrors) against ten inline sites — a strictly larger drift
   surface than the one it is meant to shrink.
3. Three sites need conditional phrasing that a verbatim shared block cannot
   serve anyway: `/lrh-readiness` only opens a PR when Step 5 created a new
   branch, `/lrh-doc-audit` only when the user chooses the PR path over
   commit-to-main, and `/lrh-create-skill` must additionally mention
   `lrh skills install`.

So: take (b)'s canonical source and (a)'s delivery. `_shared/lifecycle-chain.md`
is the single place the chain is defined and the single place every consuming
site is enumerated; each site inlines the text in its own voice. The actual
root cause of this bug was not that copies drifted — it was that nobody knew
where to look when `/lrh-closeout` was added. A grep-able index of consuming
sites fixes that directly. `_shared/` is skipped by the installer
(`src/lrh/skills/installer.py` excludes `_`-prefixed directories), so the new
file adds no installed-file surface and needs no `.claude/` mirror.

## Required Changes

Canonical chain text, modelled on `lrh-review-response/SKILL.md:245`:

```text
Next steps: run `/lrh-review-response <PR-URL>` to address reviewer comments
(repeat as needed), then `/lrh-confirm-fixes <PR-URL>` to verify the fixes
against the current diff and resolve the review threads before merge. After
merging, run `/lrh-closeout <PR-URL>` to land the execution record and update
the control plane.
```

1. **Create `src/lrh/skills/_shared/lifecycle-chain.md`** — canonical chain
   text, a `CANONICAL SOURCE` header matching the `prior-art-check.md`
   convention, and a table enumerating every consuming site with the variant
   it uses.
2. **`lrh-work-item/references/lrh-work-item-workflow.md`** — the "Suggested
   next steps after skill completes" section (lines 97–112) lists only
   `lrh work-items validate|readiness`, `lrh request ready-work-item`, and
   `lrh request prompt-from-work-item`, but SKILL.md Step 8 opens a PR. Split
   the section into two explicitly-labelled axes: the **PR lifecycle** (the
   chain) and **item refinement** (the existing CLI commands, for an item not
   yet prompt-ready). State that they are orthogonal, not alternatives.
   Reduce "Evidence and closeout" (lines 116–128) from a hand-rolled parallel
   procedure to a pointer at `/lrh-closeout`.
3. **`lrh-implement/SKILL.md`** (Step 10, lines 261–264) — insert
   `/lrh-confirm-fixes` between review response and merge; replace the manual
   "merge it and move the work item to `resolved/` with a non-null
   `resolution` value" with `/lrh-closeout`.
4. **`lrh-confirm-fixes/SKILL.md`** — add `/lrh-closeout <pr-url>` to the
   Step 8 report list as an explicit post-merge next step, green verdict only.
   Reword the line-354 "Does not trigger `/lrh-closeout`" disclaimer so it
   scopes to automatic invocation rather than reading as "closeout is out of
   scope for the user".
5. **`lrh-proposal/SKILL.md`** (Step 9 report) — add the chain alongside the
   existing scope-based follow-on offers.
6. **`lrh-workstream/SKILL.md`** (Step 9 report) — add the chain alongside the
   existing design-review next steps.
7. **`lrh-readiness/SKILL.md`** (Step 9 report) — add the chain, conditioned
   on whether Step 8 opened a new PR or pushed to an existing one.
8. **`lrh-doc-work/SKILL.md`** (end of Step 12) — add the chain after the
   execution-record push.
9. **`lrh-doc-organize/SKILL.md`** (end of Step 11) — add the chain after the
   execution-record push.
10. **`lrh-doc-audit/SKILL.md`** (Step 10) — add the chain to the "Open a PR"
    branch only; the commit-to-main branch has no PR to review.
11. **`lrh-create-skill/SKILL.md`** (Step 10 report) — add the chain, plus a
    note that `lrh skills install` is required after merge for the new skill
    to reach `~/.claude/skills/`.
12. Mirror changes 2–11 into the corresponding `.claude/skills/` paths.

## Non-Goals

- Do not change what any skill does. Guidance text only — no behavioral or
  workflow-step changes.
- Do not make any skill automatically invoke another. The chain is a
  suggestion to the user; `disable-model-invocation: true` is deliberate.
- Do not restructure Execution Steps, quality checklists, or frontmatter.
  Where a skill has no Report step (`/lrh-doc-work`, `/lrh-doc-organize`),
  append to the existing final step rather than adding a new one.
- Do not add the automated `_shared/` drift check — tracked in
  `project/design/backlog.md`.
- Do not change `/lrh-design` (opens no PR, commits nothing),
  `/lrh-closeout` (terminal), or `/lrh-review-response` (already correct).

## Acceptance Criteria

- `src/lrh/skills/_shared/lifecycle-chain.md` exists, carries a
  `CANONICAL SOURCE` header, and enumerates all ten consuming sites
- Every skill that opens a PR names `/lrh-review-response` as the next step:
  `lrh-work-item` (via its workflow reference), `lrh-implement`,
  `lrh-proposal`, `lrh-workstream`, `lrh-readiness`, `lrh-doc-work`,
  `lrh-doc-organize`, `lrh-doc-audit` (PR branch only), `lrh-create-skill`
- Every one of those sites continues the chain through `/lrh-confirm-fixes`,
  merge, and `/lrh-closeout`
- `lrh-implement/SKILL.md` Step 10 names `/lrh-confirm-fixes` between review
  response and merge, and `/lrh-closeout` in place of the manual
  move-to-`resolved/` instruction
- `lrh-confirm-fixes/SKILL.md` Step 8 report names `/lrh-closeout` for the
  green verdict, and its "What This Skill Does Not Do" entry scopes the
  disclaimer to automatic invocation
- `lrh-work-item-workflow.md` presents PR lifecycle and item refinement as
  two labelled, orthogonal paths, and its closeout section is a pointer to
  `/lrh-closeout` rather than a parallel manual procedure
- No skill's Execution Steps, quality checklist, or frontmatter changed
- `diff -r src/lrh/skills .claude/skills` reports differences only for
  `_shared`, `installer.py`, `__init__.py`, and `__pycache__`
- `scripts/format --check --diff`, `scripts/lint`, and `scripts/test` pass
- `lrh validate` reports 0 errors

## Validation

- `scripts/version tools`
- `scripts/format --check --diff`
- `scripts/lint`
- `scripts/test`
- `lrh validate`
- `lrh work-items validate`
- `diff -r src/lrh/skills .claude/skills`
