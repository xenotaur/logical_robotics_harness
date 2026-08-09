---
resolution: null
blocked_reason: null
blocked: false
id: WI-SKILLS-WORKTREE-SAFE-BRANCH-CREATION
title: Make skill branch-creation worktree-safe, and fix non-compliant commit-message templates
type: deliverable
status: proposed
owner: anthony
contributors:
  - anthony
assigned_agents: []
related_focus: []
related_roadmap: []
related_workstreams:
  - WS-CROSS-REPO-CODE-HEALTH
related_design:
  - project/design/proposals/proposed/invocation-and-gate-reset/00_proposal.md
depends_on: []
blocked_by: []
expected_actions:
  - edit_file
forbidden_actions:
  - force_push
  - delete_branch
  - restructure_lrh_land_step_7
acceptance:
  - No skill hard-codes the default branch; neither "git checkout main" nor "origin/main" appears anywhere under src/lrh/skills/ or .claude/skills/
  - Branch creation in all 8 affected skills branches from the resolved default branch's remote ref, so it succeeds while another worktree holds the default branch checked out
  - Each of the 8 skills guards a dirty working tree before creating a branch, surfacing the changes rather than carrying them onto the new branch
  - The default branch is resolved at runtime rather than hard-coded, so the skills work in client repositories using master or trunk
  - Canonical guidance lives in one file under src/lrh/skills/_shared/ and is inlined at each consuming site, with the consuming-sites table listing all 8
  - Every commit-message template in src/lrh/skills/ and .claude/skills/ satisfies STYLE.md's Conventional Commits requirement, with a type drawn from its Required types table
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
  - src/lrh/skills/lrh-land/SKILL.md
  - src/lrh/skills/lrh-land/references/land-workflow.md
---

# Make skill branch-creation worktree-safe, and fix non-compliant commit-message templates

## Summary

Two defects in the git-workflow steps LRH skills instruct agents to run, both
found by using the skills rather than by audit.

**Primary.** Eight skills instruct `git checkout main && git pull` before
creating a feature branch. That instruction fails outright when another worktree
holds the default branch checked out, silently carries unrelated uncommitted
work onto the new branch, and hard-codes `main` in a harness designed to be
installed into client repositories that may use `master` or `trunk`. Replace it
with the worktree-safe pattern `/lrh-land` already uses, add a dirty-tree guard,
and factor the guidance into a single canonical file rather than an eighth
independent restatement.

**Secondary, folded in.** Five commit-message templates across four of those
same eight skills do not satisfy `STYLE.md`'s Conventional Commits requirement,
and agents following them have already written non-compliant commits to `main`.
Fixed in the same pass because the affected files are a subset of the primary
scope.

## Problem / Context

### Defect 1 — branch creation

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

### Defect 2 — non-compliant commit-message templates

`STYLE.md` requires [Conventional Commits 1.0.0](https://www.conventionalcommits.org/en/v1.0.0/),
formatted `<type>: <description>` or `<type>(<scope>): <description>`, with
`type` drawn from its Required types table (`feat`, `fix`, `chore`, `docs`,
`test`, `refactor`). Five commit-message templates across four skills omit the
type prefix entirely:

| Skill | Line | Current template |
|---|---|---|
| `lrh-create-skill/SKILL.md` | 221 | `Add /<name> skill` |
| `lrh-proposal/SKILL.md` | 304 | `Add design proposal <PROP-ID>: <title>` |
| `lrh-work-item/SKILL.md` | 332 | `Add work item <ID>: <title>` |
| `lrh-work-item/SKILL.md` | 395 | `Update workstream <WS-ID>: add <ID>` |
| `lrh-workstream/SKILL.md` | 300 | `Add workstream <WS-ID>: <title>` |

Two templates are already compliant and serve as the in-repo pattern to follow:
`lrh-closeout/SKILL.md:411` (`chore(closeout): ...`) and
`lrh-readiness/SKILL.md:180` (`chore(work-items): ...`).

**This is not theoretical — agents are already following the bad templates.**
Commits `eebba0d3` ("Add design proposal PROP-LRH-FRONTMATTER-PARSER") and
`ca50b0d3` ("Add design proposal PROP-REVIEW-WAIT-POSTURE") are both
non-compliant and both trace directly to `lrh-proposal`'s Step 9 template. Both
currently sit on open PR branches (#531 and #522) rather than on `main`, and
because this repository merges with merge commits rather than squashing, each
message is preserved verbatim on `main` when its PR lands. A skill that
instructs an agent to violate the repository's own documented standard will keep
producing violations for as long as it says so.

All four affected skills are already inside Defect 1's eight-skill set, so this
is folded into the same work item rather than tracked separately.

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

The branch-creation step in the eight skills listed above, the five
non-compliant commit-message templates in four of those same eight, a new
canonical reference under `src/lrh/skills/_shared/`, and the `.claude/skills/`
mirrors of all of the above.

Also in scope: `/lrh-land`'s three `origin/main` occurrences
(`lrh-land/SKILL.md:403`, `land-workflow.md:19`, `:20`). **These were initially
placed out of scope on the grounds that Step 7 "already implements the correct
pattern"; that is only half true.** Step 7 is correct about the *worktree-lock*
half of Defect 1 — it branches from a remote ref rather than checking out the
default branch — but it hard-codes `main`, which is the other half. Leaving it
untouched would ship `_shared/branch-creation.md` saying "never hard-code
`main`" alongside the very implementation it cites as exemplary doing exactly
that, still broken in a `master`/`trunk` client repo.

Out of scope: any other step in those skills, and
`lrh-closeout`/`lrh-readiness`'s commit templates, which are already compliant
and serve as the reference for Defect 2.

## Required Changes

1. Create `src/lrh/skills/_shared/branch-creation.md` as canonical text,
   following the existing `_shared/prior-art-check.md` and
   `_shared/chain-defaults.md` conventions: a `CANONICAL SOURCE` header comment,
   the procedure, and a consuming-sites table listing all eight skills.
2. Specify the procedure as: fetch; resolve the default branch at runtime
   (reusing `round-cap-gate.md`'s hardened snippet — **note that
   `PROP-INVOCATION-AND-GATE-RESET` Stage 1 reduces that file from 749 to ~59
   lines and removes this block; if Stage 1 has already landed, recover the
   snippet from git history rather than assuming the file still contains it** —
   including its explicit emptiness check rather than a `||` fallback, since without `pipefail` a
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
5. Rewrite the five non-compliant commit-message templates to satisfy
   `STYLE.md`, choosing the type from its Required types table and following
   the scope style the two already-compliant templates use. Suggested, subject
   to implementation judgement:

   | Site | Suggested |
   |---|---|
   | `lrh-create-skill:221` | `feat(skills): add /<name> skill` |
   | `lrh-proposal:304` | `chore(design): add <PROP-ID>` |
   | `lrh-work-item:332` | `chore(work-item): add <ID>` |
   | `lrh-work-item:395` | `chore(workstream): add <ID> to <WS-ID>` |
   | `lrh-workstream:300` | `chore(workstream): add <WS-ID>` |

   `chore` is correct for the four planning-artifact sites per `STYLE.md`'s own
   mapping ("planning artifacts"); `lrh-create-skill` is the one arguable case,
   since a new skill is a new capability rather than maintenance.
6. Where a skill's PR-body or commit step is adjacent to the message template,
   check that the surrounding prose does not restate the old non-compliant form
   in narrative text as well as in the command block.
7. Mirror every `src/lrh/skills/` change into `.claude/skills/` exactly.

## Non-Goals

- Does not change `/lrh-land` Step 7's *structure* — branching from a remote ref
  rather than checking out the default branch is the pattern this work item
  propagates. Only its hard-coded `main` is corrected, per Scope above.
- Does not build an automated drift-check for the inlined copies. That remains
  the deferred backlog entry "Validator drift-check for synced skill
  references"; this work item adds one more synced reference to its eventual
  scope rather than solving it.
- Does not change branch naming conventions (`<username>/<type>/<slug>`).
- Does not change the rerun/resume branch logic that precedes the branch
  creation step in `lrh-work-item`, `lrh-workstream`, and `lrh-proposal`; only
  the final `else` clause that creates a fresh branch is in scope.
- Does not add a git hook, commit-lint, or any enforcement mechanism outside
  skill text. Fixing the templates stops the source of new violations; making
  compliance mechanically enforced is separate work.
- Does not rewrite the non-compliant commit messages already sitting on open PR
  branches (#531, #522). Rewriting merged or in-review history is out of
  proportion to the problem, and `forbidden_actions` prohibits force-push.
- Does not audit commit-message compliance outside `src/lrh/skills/` and
  `.claude/skills/` — Taurcode prompts and other repositories are not in scope.

## Acceptance Criteria

- Neither `git checkout main` nor `origin/main` appears anywhere under
  `src/lrh/skills/` or `.claude/skills/` — the narrower first pattern misses
  `checkout -b <branch> origin/main`, which is the shape `/lrh-land` uses.
- Branch creation in all eight skills branches from the resolved default
  branch's remote ref, succeeding while another worktree holds the default
  branch checked out.
- Each of the eight guards a dirty working tree before creating a branch,
  surfacing the changes rather than carrying them.
- The default branch is resolved at runtime, so the skills work in client
  repositories using `master` or `trunk`.
- Canonical guidance lives in one `src/lrh/skills/_shared/` file, inlined at
  each consuming site, with a consuming-sites table listing all eight.
- Every `git commit` template in `src/lrh/skills/` and `.claude/skills/` begins
  with a valid `STYLE.md` type, optionally scoped.
- `lrh validate` reports 0 errors.
- `diff -r` between `src/lrh/skills/` and `.claude/skills/` reports no
  differences for every affected skill.

## Validation

- `lrh validate`
- `grep -rnE "git checkout main|origin/main" src/lrh/skills/ .claude/skills/` returns no matches (the narrower "git checkout main" form misses `checkout -b <branch> origin/main`, which is the shape /lrh-land uses)
- `grep -rhn 'git commit -m' src/lrh/skills/ .claude/skills/ | grep -vE 'git commit -m "(feat|fix|chore|docs|test|refactor)(\([a-z-]+\))?: '` returns no matches
- `for d in lrh-create-skill lrh-doc-organize lrh-doc-work lrh-implement lrh-land lrh-proposal lrh-readiness lrh-work-item lrh-workstream; do diff -r "src/lrh/skills/$d" ".claude/skills/$d"; done`
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

Defect 2 is low-risk textually but carries one judgement call worth surfacing at
review rather than deciding silently: whether `lrh-create-skill`'s template
should be `feat` or `chore`. `STYLE.md` maps "planning artifacts" to `chore`,
which clearly covers the four proposal/work-item/workstream sites, but a new
skill is closer to "a new feature or capability." Getting this wrong is
cosmetic, not functional; it is called out so the reviewer decides deliberately.

The two defects are bundled because their file sets overlap, not because they
are related in substance. If Defect 1's design needs iteration in review, Defect
2 should be split out and landed on its own rather than held behind it — it is a
five-line text fix blocking nothing.
