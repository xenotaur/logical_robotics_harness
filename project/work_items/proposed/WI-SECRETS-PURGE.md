---
resolution: null
blocked_reason: null
blocked: false
id: WI-SECRETS-PURGE
title: Implement lrh secrets purge
type: deliverable
status: proposed
owner: anthony
contributors:
  - anthony
assigned_agents: []
related_focus: []
related_roadmap: []
related_workstreams:
  - WS-SECRETS-COMMAND
related_design:
  - project/design/proposals/proposed/lrh-secrets-command/00_proposal.md
depends_on:
  - WI-SECRETS-SCAN
  - WI-SECRETS-REVIEW
blocked_by: []
expected_actions:
  - create_file
  - edit_file
  - add_cli_command
  - run_tests
forbidden_actions:
  - force_push
  - delete_branch
  - run_git_push
  - implement_lrh_secrets_scan
  - implement_lrh_secrets_review
acceptance:
  - src/lrh/secrets/purge.py exists and preserves every safety invariant listed in Required Changes
  - lrh secrets purge refuses to run without --refs-file
  - lrh secrets purge never executes git push under any flag combination
  - lrh secrets purge --apply fails loudly (nonzero exit) if post-rewrite verification finds a listed secret still present
  - lrh secrets purge --help documents that --replacements is expected to be review --apply's replacements.reviewed.txt output, not scan's draft replacements.txt
  - lrh secrets purge's printed output on success includes both the push command and purge_history.py's existing manual-step reminders (notify collaborators/branch-owners before pushing; file a host support request to purge cached views if the repo was ever public)
  - lrh validate passes with 0 errors
  - tests/secrets_tests/purge_test.py and the purge portion of tests/cli_tests/secrets_test.py pass
required_evidence:
  - manual_review
  - lrh_validate
  - test_output
artifacts_expected:
  - src/lrh/secrets/purge.py
  - tests/secrets_tests/purge_test.py
  - tests/cli_tests/secrets_test.py
---

## Summary

Implement `lrh secrets purge`, wrapping `git-filter-repo` to rewrite a
disposable mirror clone scoped to explicit refs, verify the rewrite
removed every listed secret, and print — but never execute — the
resulting `git push --force` command.

## Problem / Context

LCATS's experimental `purge_history.py` already implements this correctly
and carries real safety invariants earned from planning an actual
history-rewrite against LCATS's leaked-key incident (see its README's
"Before you run this" section: ~177 affected refs, every existing clone
going stale, open PRs breaking). This item graduates that logic into
`src/lrh/secrets/purge.py` as the first LRH command wrapping a
destructive/history-rewriting external tool, per `PROP-LRH-SECRETS-COMMAND`
Decision 4 — its invariants must be preserved unmodified, not relaxed into
optional flags. It depends on both `WI-SECRETS-SCAN` and `WI-SECRETS-REVIEW`
because it consumes `review`'s finalized `replacements.reviewed.txt`.

A handoff prompt from LCATS PR #315's author, reviewed after this
proposal's initial draft, reinforced two points now reflected below: (1)
`purge` "must refuse to run without an explicit, human-reviewed input
from the scan stage — never scan-then-auto-purge" — this is why
`--replacements` is documented as expecting `review`'s distinctly-named
`replacements.reviewed.txt` (Required Changes item 1; see
`PROP-LRH-SECRETS-COMMAND` Decision 3), not `scan`'s draft output; and (2)
`purge_history.py`'s printed manual-step reminders — notify every
collaborator/branch-owner before pushing (a stale clone's `git pull`
silently reintroduces the purged secret via merge, it does not error),
and file a host-support request to purge cached views/forks if the repo
was ever public — are load-bearing content that must survive graduation
alongside the push command itself, not be dropped as incidental.

### Duplication search
- In-repo: No existing implementation found.
- Sibling repos: LCATS `lcats/experimental/secrets_hygiene/purge_history.py` — source being graduated.
- External libraries: `git-filter-repo` — already the chosen tool, per GitHub's own documented recommendation.
- Recommendation: Proceed.

### Demand search
- Work items: None found.
- Proposals: None found (governed by `PROP-LRH-SECRETS-COMMAND`).
- Backlog: No matching entries.
- Recommendation: No action.

## Scope

- Implement `src/lrh/secrets/purge.py` wrapping `git-filter-repo`
- Wire a `purge` subcommand under the `secrets` group in `src/lrh/cli/main.py`
- Preserve every safety invariant from `purge_history.py` without relaxation
- Add module and CLI test coverage, including a real-`git` mirror-clone/verify path

## Required Changes

1. Create `src/lrh/secrets/purge.py`: fail fast with an install hint if `git-filter-repo` is not on `PATH`. Accept `--project-root` (default cwd), `--source <url-or-path>` (default: `git -C <project-root> remote get-url origin`), `--refs-file` (**mandatory** — hard failure if missing or empty, mirroring `purge_history.py`'s refusal to run unscoped), `--replacements <path>` (expected to be `review --apply`'s `replacements.reviewed.txt` output, not `scan`'s draft `replacements.txt` — document this explicitly in `--help`, per `PROP-LRH-SECRETS-COMMAND` Decision 3), `--mirror-dir` (default: temp dir), and `--dry-run`/`--apply` (mutually exclusive, per this repo's convention). `--dry-run`: validate all inputs (refs file well-formed, replacements file exists, binaries present) without cloning or rewriting. `--apply`: mirror-clone the source, run `git-filter-repo --replace-text <replacements> --force --refs <ref> ...` scoped to every line in `--refs-file`, then re-verify via `git log --all -S <secret> --pickaxe-regex` that no listed secret remains; a nonclean verification is a hard `exit(1)` with no further action. On success, print — but do not execute — the `git push --force <source> <ref>` command for each ref, **together with the same manual-step reminders `purge_history.py` already prints** (notify every collaborator/branch-owner before pushing; file a host-support request to purge cached views/forks if the repo was ever public) — carry this text over, do not drop it as incidental to just the push command.
2. **Do not add a `--push` flag or any code path that invokes `git push`.** This is a hard requirement, not a default — verify no such path exists as part of code review.
3. In `src/lrh/cli/main.py`: add a `purge` sub-parser under `secrets_subparsers` (from `WI-SECRETS-SCAN`) with the above arguments, and a dispatch branch.
4. Create `tests/secrets_tests/purge_test.py`: mock the `git-filter-repo` subprocess call for the default suite; cover missing-`--refs-file` refusal, empty-refs-file refusal, `--dry-run` performing no clone, and failed-verification hard-exit. Add a `unittest.skipUnless(shutil.which("git-filter-repo"), ...)`-gated integration test exercising a real mirror-clone + verify against a throwaway fixture git repo (real `git` is always available; `git-filter-repo` may not be, mirroring the environment-conditional-skip idiom in `tests/cli_tests/serve_test.py`).
5. Extend `tests/cli_tests/secrets_test.py` with `lrh secrets purge --help` and dispatch coverage.

## Non-Goals

- Does not implement `lrh secrets scan` or `lrh secrets review` — separate work items.
- Does not add any flag or code path that executes `git push` — permanently manual.
- Does not decide whether/when LCATS actually runs an all-branches purge against its real incident — that operational decision is separate from shipping this tool.

## Acceptance Criteria

- `lrh secrets purge --help` documents `--project-root`, `--source`, `--refs-file`, `--replacements`, `--mirror-dir`, `--dry-run`, `--apply`.
- Running without `--refs-file` (or with an empty one) is a hard failure with no mirror clone attempted.
- `--dry-run` never clones or rewrites anything.
- A failed post-rewrite verification exits nonzero and does not print a push command.
- No flag combination results in `git push` being executed.
- `lrh validate` reports 0 errors.
- `tests/secrets_tests/purge_test.py` and the `purge` portion of `tests/cli_tests/secrets_test.py` pass.

## Validation

- `scripts/version tools`
- `lrh validate`
- `scripts/format --check --diff`
- `scripts/lint`
- `scripts/test`
- `lrh secrets purge --help`

## Risk Notes

- History-rewrite logic is the highest-risk part of this graduation; any regression in the mirror-only/verify-after invariants would reintroduce real risk to a repo's history. Code review for this item should specifically check for any accidental code path to `git push` or to `--project-root`'s working tree.

## Dependencies / Order

Depends on both `WI-SECRETS-SCAN` and `WI-SECRETS-REVIEW`: `purge` consumes the finalized `replacements.reviewed.txt` that `review --apply` produces from `scan`'s findings. Implement last.

## Related Workstream and Designs

- Workstream: `project/workstreams/proposed/WS-SECRETS-COMMAND.md`
- Design: `project/design/proposals/proposed/lrh-secrets-command/00_proposal.md`
