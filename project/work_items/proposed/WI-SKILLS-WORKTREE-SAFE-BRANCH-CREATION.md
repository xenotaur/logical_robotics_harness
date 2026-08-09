---
resolution: null
blocked_reason: null
blocked: false
id: WI-SKILLS-WORKTREE-SAFE-BRANCH-CREATION
title: Make skill branch-creation worktree-safe and default-branch-agnostic
type: deliverable
status: proposed
owner: anthony
contributors:
  - anthony
assigned_agents: []
related_focus: []
related_roadmap: []
related_workstreams: []
related_design: []
depends_on: []
blocked_by: []
expected_actions:
  - edit_file
forbidden_actions:
  - force_push
  - delete_branch
  - modify_lrh_land_step_7
acceptance:
  - No skill instructs a checkout of a hard-coded default branch; grep for "git checkout main" across src/lrh/skills/ and .claude/skills/ returns no matches
  - Branch creation in all 8 affected skills branches from the resolved default branch's remote ref, so it succeeds while another worktree holds the default branch checked out
  - Each of the 8 skills guards a dirty working tree before creating a branch, surfacing the changes rather than carrying them onto the new branch
  - The default branch is resolved at runtime rather than hard-coded, so the skills work in client repositories using master or trunk
  - Canonical guidance lives in one file under src/lrh/skills/_shared/ and is inlined at each consuming site, with the consuming-sites table listing all 8
  - lrh validate reports 0 errors
  - diff -r src/lrh/skills/ .claude/skills/ reports no differences for every affected skill
required_evidence:
  - manual_review
  - lrh_validate
artifacts_expected:
  - src/lrh/skills/_shared/branch-creation.md
  - src/lrh/skills/lrh-create-skill/SKILL.md
  - src/lrh/skills/lrh-doc-organize/SKILL.md
  - src/lrh/skills/lrh-doc-work/SKILL.md
  - src/lrh/skills/lrh-implement/SKILL.md
  - src/lrh/skills/lrh-proposal/SKILL.md
  - src/lrh/skills/lrh-readiness/SKILL.md
  - src/lrh/skills/lrh-work-item/SKILL.md
  - src/lrh/skills/lrh-workstream/SKILL.md
---

# Make skill branch-creation worktree-safe and default-branch-agnostic

## Summary

Eight LRH skills instruct `git checkout main && git pull` before creating a
feature branch. That instruction fails outright when another worktree holds the
default branch checked out, silently carries unrelated uncommitted work onto the
new branch, and hard-codes `main` in a harness designed to be installed into
client repositories that may use `master` or `trunk`. Replace it with the
worktree-safe pattern `/lrh-land` already uses, add a dirty-tree guard, and
factor the guidance into a single canonical file rather than an eighth
independent restatement.

## Problem / Context

The instruction `git checkout main && git pull` appears verbatim in eight
skills:

| Skill | Line |
|---|---|
| `lrh-create-skill/SKILL.md` | 144 |
| `lrh-doc-organize/SKILL.md` | 158 |
| `lrh-doc-work/SKILL.md` | 184 |
| `lrh-implement/SKILL.md` | 162 |
| `lrh-proposal/SKILL.md` | 248 |
| `lrh-readiness/SKILL.md` | 145 |
| `lrh-work-item/SKILL.md` | 265 |
| `lrh-workstream/SKILL.md` | 245 |

It carries four distinct defects, none of them guarded in any of the eight:

1. **Fails when the default branch is checked out in another worktree.** Git
   refuses to check out a branch already checked out elsewhere
   (`fatal: 'main' is already checked out at ...`). This is not hypothetical:
   at the time this work item was written, `main` was checked out in
   `.claude/worktrees/lrh-pypi-installability-status-a4c549`, with more than ten
   worktrees active. Any of the eight skills invoked from another worktree would
   fail at its branch step.
2. **Carries unrelated uncommitted work onto the new branch.** `git checkout`
   brings working-tree modifications along. A skill invoked with unrelated edits
   in progress would silently base its planning-artifact branch on top of them,
   producing a PR polluted with unrelated changes. Zero of the eight check
   `git status --porcelain` first. Two skills (`lrh-work-item`,
   `lrh-readiness`) mention "uncommitted" in prose, but both references concern
   not leaving edits uncommitted *later*; neither is a pre-checkout guard.
3. **Hard-codes `main`.** LRH is a reusable harness installed into independent
   client repositories, which may use `master`, `trunk`, or any other default
   branch name.
4. **Silently stale base if the pull fails.** With `&&`, a failed `git pull`
   after a successful checkout leaves the new branch based on a stale local
   default branch, with no signal.

**The fix already exists in this repository, in two places, and did not
propagate.** `/lrh-land` Step 7 (`src/lrh/skills/lrh-land/SKILL.md:400-405`)
already branches with `git checkout -b tmp-<slug> origin/main`, deliberately
avoiding a local checkout of the default branch — it hit the worktree-lock
problem and solved it. Separately,
`src/lrh/skills/lrh-confirm-fixes/references/round-cap-gate.md` documents
default-branch resolution with a hardened snippet, warning to "never hard-code
`main`; a client repository may use `master`, `trunk`, or anything else," and
noting the `pipefail` trap that makes a naive `||` fallback silently produce an
empty branch name. Neither reached the eight planning skills.

This is the same restatement-drift pattern already tracked in
`project/design/backlog.md` under "Validator drift-check for synced skill
references": guidance restated independently in N places, with fixes landing in
one and never propagating.

*Provenance.* Surfaced while creating `PROP-INVOCATION-AND-GATE-RESET`, when
`/lrh-proposal`'s own Step 6 branch instruction had to be deviated from. The
defect is independent of that proposal's scope and is tracked separately here.

### Prior Art Check

**Duplication search**

- In-repo: No existing work item, proposal, or workstream addresses skill
  branch-creation mechanics. Five artifacts matched a keyword search
  (`WI-REVIEW-RESPONSE-INCLUDE-THREAD`, `WI-WORKFLOW-DOCS-READINESS-AUDIT-PROMPTING`,
  `WI-SKILLS-LRH-DOC-ORGANIZE`, `PROP-LRH-PROJECT-LOCAL-SKILLS` sub-proposal 01,
  `PROP-LRH-EXECUTION-SESSIONS`); inspection confirms each merely *uses* the
  branch pattern rather than fixing it.
- Sibling repos: None identified. Taurcode maintains its own prompts and is not
  a source for LRH skill text.
- External libraries: Not applicable.
- Recommendation: Proceed.

**Demand search**

- Work items: None found requesting this.
- Proposals: None found requesting this.
- Backlog: No matching entry. The one worktree mention concerns Codex
  `.agents/skills` installation paths, unrelated to branch creation.
- Recommendation: No action; nothing to close or link.

*Workstream note.* No active or proposed workstream fits. `WS-SKILLS` (Claude
Code Skills Infrastructure) is the natural conceptual home but is `resolved`;
attaching would reopen a closed workstream. `WS-SKILLS-TARGET-AWARE-INSTALL`
covers Codex install targets, not branch mechanics. `related_workstreams` is
therefore left empty deliberately, not by oversight.

## Scope

The branch-creation step in the eight skills listed above, plus a new canonical
reference under `src/lrh/skills/_shared/` and its `.claude/skills/` mirrors.

Out of scope: any other step in those skills, and `/lrh-land`'s Step 7, which is
already correct and serves as the reference implementation.

## Required Changes

1. Create `src/lrh/skills/_shared/branch-creation.md` as canonical text,
   following the existing `_shared/prior-art-check.md` and
   `_shared/chain-defaults.md` conventions: a `CANONICAL SOURCE` header comment,
   the procedure, and a consuming-sites table listing all eight skills.
2. Specify the procedure as: fetch; resolve the default branch at runtime
   (reusing `round-cap-gate.md`'s hardened snippet, including its explicit
   emptiness check rather than a `||` fallback, since without `pipefail` a
   `git symbolic-ref | sed` pipeline reports the exit status of `sed`); check
   `git status --porcelain` and stop to surface a dirty tree rather than
   carrying it; then `git checkout -b <branch> origin/<default>` without ever
   checking out the default branch locally.
3. State the intent in guidance terms, not only as a command: prefer a feature
   branch based on an up-to-date default branch, unless the user named a branch
   or a named condition applies. Enumerate the conditions explicitly — dirty
   working tree, default branch held by another worktree, user-specified
   branch — rather than using an open-ended phrase such as "special
   conditions," which produces inconsistent agent behavior run to run.
4. Replace the `git checkout main && git pull` block in each of the eight
   skills with the inlined canonical procedure.
5. Mirror every `src/lrh/skills/` change into `.claude/skills/` exactly.

## Non-Goals

- Does not modify `/lrh-land` Step 7, which already implements the correct
  pattern and is the reference for this change.
- Does not build an automated drift-check for the inlined copies. That remains
  the deferred backlog entry "Validator drift-check for synced skill
  references"; this work item adds one more synced reference to its eventual
  scope rather than solving it.
- Does not change branch naming conventions (`<username>/<type>/<slug>`).
- Does not change the rerun/resume branch logic that precedes the branch
  creation step in `lrh-work-item`, `lrh-workstream`, and `lrh-proposal`; only
  the final `else` clause that creates a fresh branch is in scope.
- Does not add a git hook or any enforcement mechanism outside skill text.

## Acceptance Criteria

- Grep for `git checkout main` across `src/lrh/skills/` and `.claude/skills/`
  returns no matches.
- Branch creation in all eight skills branches from the resolved default
  branch's remote ref, succeeding while another worktree holds the default
  branch checked out.
- Each of the eight guards a dirty working tree before creating a branch,
  surfacing the changes rather than carrying them.
- The default branch is resolved at runtime, so the skills work in client
  repositories using `master` or `trunk`.
- Canonical guidance lives in one `src/lrh/skills/_shared/` file, inlined at
  each consuming site, with a consuming-sites table listing all eight.
- `lrh validate` reports 0 errors.
- `diff -r` between `src/lrh/skills/` and `.claude/skills/` reports no
  differences for every affected skill.

## Validation

- `lrh validate`
- `grep -rn "git checkout main" src/lrh/skills/ .claude/skills/` returns no matches
- `for d in lrh-create-skill lrh-doc-organize lrh-doc-work lrh-implement lrh-proposal lrh-readiness lrh-work-item lrh-workstream; do diff -r "src/lrh/skills/$d" ".claude/skills/$d"; done`
- Manual: invoke one affected skill from a worktree while another worktree holds the default branch checked out, and confirm the branch step succeeds
- Manual: invoke one affected skill with a deliberately dirty working tree, and confirm it surfaces the changes instead of carrying them onto the new branch

## Risk Notes

The dirty-tree guard is the change most likely to add friction: it introduces a
stop where the skills previously proceeded silently. That is the intended
behavior — carrying unrelated edits onto a planning-artifact branch is the more
expensive failure — but the guard should surface the changed files and offer
concrete options (stash, commit selectively, or continue on the current branch)
rather than simply aborting. An abort-only guard would trade a silent-corruption
failure for a dead-end one.

Because `src/lrh/skills/_shared/` is skipped by the installer, the canonical
file is maintainer-facing only; each consuming skill still carries its own
inlined copy. This work item therefore reduces future drift but does not
eliminate it, and adds one more synced reference to the deferred drift-check
backlog entry's eventual scope.
