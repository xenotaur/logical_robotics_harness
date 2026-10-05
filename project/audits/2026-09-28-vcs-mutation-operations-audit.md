---
title: "VCS Mutation Operations Audit"
date: 2026-10-05
status: completed
type: audit
scope: vcs-mutation-operations
---

# VCS Mutation Operations Audit (2026-10-05)

Prompt ID: `PROMPT(WI-VCS-SAFE-OPERATIONS-BACKEND:WI_VCS_SAFE_OPERATIONS_BACKEND_IMPL)[2026-10-05T17:44:14+00:00]`
Work item: `WI-VCS-SAFE-OPERATIONS-BACKEND`. The filename carries the date the
WI was filed (2026-09-28) because that is the path the WI's
`artifacts_expected` names; the audit itself was written on 2026-10-05
against `origin/main` @ `3082dc3b`. Line numbers below are as of that commit.

Question: which git/`gh` operations that create, push, modify, or merge
branches and pull requests do LRH skills and code perform, which of them have
been denied in practice, and which are stereotyped enough to move behind a
narrower invocation surface?

## 1. Method

Mutating operations were enumerated with line-based greps over the canonical
skill sources (`src/lrh/skills/`; `.claude/skills/` is a byte-identical copy
and `.agents/skills/` a rendered copy, so they add no new operations) and over
Python code that shells out to `git` or `gh`:

```bash
grep -rEn -- '<pattern>' src/lrh/skills
grep -rEn '"(git|gh)"' src/lrh --include=*.py
```

Patterns: `gh pr create|merge|comment|edit|close|ready|review`, mutating
`gh api`/`resolveReviewThread`, `git push` (and force variants),
`git commit|add|checkout -b|branch -D|reset --hard|rebase|merge|clean|restore`,
`git config --local`, `git worktree`, `git tag`, `rm -rf`. Read-only
operations (`gh pr view`, `gh pr checks`, `git fetch`, `git ls-tree`, ...) are
excluded.

Raw hit counts (lines / files, canonical skills only): `gh pr create` 12/10,
`gh pr merge` 9/4, `resolveReviewThread` 10/3, `git push` 11/8,
`git checkout -b` 11/8, `git commit` 9/8, `git add` 13/8,
`git config --local` 7/3, `git branch -D|-d` 3/2, `git push --force*` 1/1,
`git reset --hard` 1/1, `git rebase` 1/1, `git clean` 1/1, `rm -rf` 1/1,
`gh pr comment` 2/1. Many hits are prose that names a command rather than an
instruction to run it; the inventory in section 3 separates the two.

## 2. Denial evidence

This is small, anecdotal evidence: agent memory notes plus this repository's
own session records. It is enough to rank risk, not to estimate rates.

| # | Operation | Date | Outcome | Source |
|---|---|---|---|---|
| E1 | `gh pr merge <url> --merge --match-head-commit <sha>`, run by the agent at `/lrh-land` closeout of PR #742 | 2026-09-27 | Denied by the auto-mode classifier, no reason given. The user ran the identical command in a terminal and it succeeded at once. | memory `gh_pr_merge_classifier_denial_handoff` |
| E2 | The same command shape, run by the agent at closeout of PR #755 | 2026-09-30 | Allowed; PR merged. | closeout note for PR #755 |
| E3 | `git push origin tmp-<slug>:main` (`/lrh-land` closeout push), PR #670 | 2026-09-19 | Denied by the classifier as a "CI bypass"; closeout PRs #675 and #679 were used instead. | memory `closeout-direct-main-push-blocked-use-pr` |
| E4 | The same closeout push, PRs #742 and #755 | 2026-09-27, 2026-09-30 | Allowed (after an ordinary git non-fast-forward rejection, resolved by rebase). A non-fast-forward is not a denial. | memory `feedback-ff-reject-not-same-as-push-denial`; closeout records |
| E5 | `git push --force-with-lease`, `git reset --hard` on a private feature branch | not recorded in the note | Denied by the classifier regardless of context. | memory `feedback-force-push-blocked-use-merge-instead` |
| E6 | `git branch -D` / `-d` | repeatedly, incl. 2026-09-27 and 2026-09-30 | Denied deterministically by the project's own `permissions.deny`. Not a classifier decision. | `docs/how-to/project-setup/claude-code-permissions.md` |
| E7 | Any Bash or Edit call while the classifier returned "no verdict" | 2026-09-28 | Transient outage. After ten consecutive no-verdict responses the turn stopped; work resumed on the next user message. | session record (`claude-app:a4f7b764-fb7e-424a-b0c1-6042007869d3`) |

## 3. Inventory

Risk: **Known** = a denial was observed. **Plausible** = same operation family
as a known denial, none observed. **Low** = local-only or no remote effect.

| Class | Operation and location | Risk | Disposition |
|---|---|---|---|
| Merge | `gh pr merge <url> --match-head-commit <sha>` presented by `/lrh-confirm-fixes` Step 8 (`SKILL.md:633`, also `:30,691,747,757`; `references/confirm-fixes-workflow.md:31`), `/lrh-land` Step 6 Half A (`SKILL.md:419`, queue note `:508`), and `references/review-response-workflow.md:30` | Known, intermittent (E1 denied, E2 allowed) | **Wired in this work item**: now `lrh vcs merge` |
| Merge | `git push origin HEAD:main` closeout push (`/lrh-land` `SKILL.md:532,571`; `references/land-workflow.md:30`) | Known, historical (E3 denied, E4 allowed) | Candidate `push_default_branch` action. Not wired: content varies per run, and it is already gated by Step 6 |
| Create | `gh pr create --title ... --body ...` in 8 skills: `lrh-implement:324`, `lrh-work-item:371`, `lrh-workstream:338`, `lrh-proposal:341`, `lrh-readiness:212`, `lrh-create-skill:248`, `lrh-doc-work:261`, `lrh-doc-organize:236` | Plausible; no denial recorded | Candidate `open_pull_request` action. Design vocabulary only |
| Push | `git push -u origin <branch>` in `lrh-workstream:337`, `lrh-work-item:370`, `lrh-readiness:206`, `lrh-proposal:340`, `lrh-create-skill:247`; bare `git push` `lrh-work-item:433`; prose "push" in `lrh-implement`, `lrh-doc-work`, `lrh-doc-organize` | Plausible; no denial recorded | Candidate `push_branch` action. Design vocabulary only |
| Modify | `gh api graphql` `resolveReviewThread` (`lrh-confirm-fixes:387`; `references/confirm-fixes-workflow.md:145`) | Plausible. The permissions how-to deliberately leaves mutating `gh api` unmatched, so it prompts | Candidate `resolve_review_thread` action |
| Modify | `gh pr comment` (`lrh-confirm-fixes:612`, prose remediation path) | Low; no denial recorded | Out of scope |
| Local | `git checkout -b` (8 skills), `git commit`, `git add`, `git worktree list` | Low | Out of scope. `create_branch` stays in the design vocabulary |
| Local | `git config --local lrh.chainDefaults.skipConsentHash ...` (`references/land-workflow.md:555`, `_shared/chain-defaults.md:121`) | Low; writes `.git/config` only | Out of scope |
| Destructive | `git branch -D|-d`, `git reset --hard`, `git clean`, `git restore`, `rm -rf`, `--force-with-lease` (`references/land-workflow.md:19,31`; `/lrh-land` `SKILL.md:559`) | Known-denied (E5, E6) | Out of scope per the WI's Non-Goals. Skills mention them only as examples of denied commands and never instruct them |
| Python | `src/lrh/dev/versioning.py:377` (`git tag`) and `:404` (`git push origin refs/tags/<tag>`), reached through `scripts/version` | Plausible; no denial recorded | Out of scope; release automation |
| Python | `src/lrh/secrets/purge.py` clones a local mirror and only prints the force-push command; no code path pushes | Low | Out of scope |
| Python | `src/lrh/vcs/github_backend.py` (new): `gh pr merge` behind `lrh vcs merge` | n/a | This work item |

## 4. Findings

1. **The merge denial is intermittent, not deterministic.** The same command
   shape was denied (E1) and later allowed (E2). A narrower invocation surface
   cannot be shown to help from one success. What it can promise is a stable,
   validated, single-purpose surface, not a bypass.
2. **Two operations combine "irreversible and shared" with "stereotyped and
   already gated by a skill": the merge and the closeout push to the default
   branch.** Both have an observed classifier denial, and only the merge has a
   fixed command shape, so only the merge is wired.
3. **`gh pr create` and `git push -u origin` are the highest-volume mutating
   operations** (8 and at least 5 skills) with no recorded denial. Abstracting
   them now would be speculative; they are documented as planned actions and
   left as prose.
4. **Destructive commands are never instructed by a skill.** They appear only
   as examples of what the project's deny list blocks.
5. **The merge command is named in nine places**: two present it as a command
   to run (`lrh-confirm-fixes:633`, `lrh-land:419`) and seven refer to it
   (five more lines across the two skills' prose and checklists, two lifecycle
   diagrams). A single `lrh vcs merge` surface gives them one name to keep in
   step.
6. **Five distinct failure modes need different handling**, and only some are
   visible to code: (a) a host-level denial before the command launches
   (E1, E3, E5); (b) a classifier outage with no verdict (E7); (c) a
   deterministic `permissions.deny` match (E6); (d) the `gh`/`git` process
   itself failing; (e) a git-level non-fast-forward rejection (E4). A backend
   can observe (d) and, if it issues the command, (e). Cases (a) to (c) stop
   the command before any LRH code runs, so reporting them stays with the
   calling skill or session. This is the scope boundary the backend design
   states.

## 5. Dispositions

- **Implemented here:** the SHA-locked merge as `lrh vcs merge`
  (`src/lrh/vcs/`, `src/lrh/cli/vcs.py`), wired into `/lrh-land` Step 6 and
  `/lrh-confirm-fixes` Step 8. See `docs/reference/vcs-backend.md`.
- **Planned, not implemented:** `create_branch`, `push_branch`,
  `open_pull_request`, and `resolve_review_thread`, listed in the design doc
  as the action vocabulary a future backend or work item would fill in.
- **Deliberately not abstracted:** the closeout push to the default branch,
  release tag pushes, and all local-only or destructive operations.

## 6. Limitations

- Counts come from line-based greps and include prose mentions; they are an
  upper bound on instructions, not a count of them.
- The denial evidence is a handful of events from one project and mostly one
  agent environment. The classifier's logic is opaque, so none of this
  predicts future denials.
- Evidence E7 and the E1/E2 contrast come from session records that live in
  the private session archive, not in this repository.
