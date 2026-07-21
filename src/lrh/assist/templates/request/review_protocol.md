# Review Protocol (Packaged)

This is the packaged review protocol used by `review_response` so guidance
remains available when LRH is installed outside a source checkout.

**Sync note:** The content of this file is mirrored inline in
`review_response.md`. When either changes, keep both in sync.
For repository-local overrides and supplements, see root `REVIEWS.md`
when present.

## 0) Precondition — verify before doing anything else

This protocol is invoked in the context of an existing pull request. Before
making any changes, establish identity: does this checkout actually
correspond to the target PR? Use the strongest evidence available — PR or
platform metadata first (e.g. `gh pr view <pr-url> --json
headRefName,headRefOid,state`, or your environment's own PR-tracking
integration), falling back to local git state (`git remote -v`, `git branch
-vv`, commit history vs. the PR's known content) only when no such metadata
is reachable. A checkout with no configured git remote, or a
generic/synthetic branch name, is not by itself evidence of a mismatch —
some environments materialize a PR's content without exposing git remotes
directly.

- If the evidence shows this checkout is for a **different PR or
  repository**, stop immediately, report the mismatch, and make no changes.
- If identity **cannot be established by any available method**, stop and
  report exactly what you checked and why it was inconclusive.
- Otherwise, proceed.

## 1) Triage each reported comment/issue

For each review comment or reported issue:

1. **Presence check**: Is the issue still present on the current branch?
2. **Validity check**: Is the concern valid and worth addressing?
3. **Feasibility check**: Is remediation feasible in this change?

If not present, valid, or feasible, explain briefly and stop processing
that comment.

## 2) Canonical validation

Identify the repository's canonical validation commands. When available,
use them in this order:

```bash
scripts/version tools        # if present: verify tool versions first
scripts/format --check --diff
scripts/lint
scripts/test
```

If these scripts are absent, identify equivalent commands from `README.md`,
CI configuration, or `Makefile`. Report which commands were unavailable and
what equivalent was used instead.

If any command fails with a missing-install or missing-import error (for
example `ModuleNotFoundError`), report it as a missing environment
dependency — not a code regression — and stop.

## 3) Repair sequencing

After confirming tool versions match (or confirming scripts are absent and
an equivalent was identified):

- If formatting fails: apply formatter fix, run `git diff`, then lint,
  then tests.
- If lint fails: apply lint fix, run `git diff`, then lint, then tests.

Do not substitute direct tool invocations (e.g. `black .`, `ruff check .`)
for canonical repository scripts. Use direct invocations only as follow-up
diagnostics after canonical commands.

## 4) Evidence requirements before claiming drift/non-repro

Do not claim pre-existing drift or non-reproducibility without command
evidence from the current branch state:

```bash
git rev-parse HEAD
git status --short
<tool/version command if available>
<canonical lint command>
<canonical format-check command>
<canonical test command>
```

Report any canonical command that was unavailable and what equivalent was
used.

## 5) Repository-policy reminders

- Respect `AGENTS.md` and `STYLE.md` if they exist at the repository root.
- Keep `README.md` guidance current in directories with affected code.

## 6) Output

After addressing all comments, get the fixes onto the target PR, then
report exactly one of the following publication outcomes:

- **Pushed directly** — you ran `git push` (or equivalent) yourself to the
  branch backing the PR.
- **Submitted via platform** — your environment provides its own mechanism
  for publishing local commits to an existing PR (a "create/update PR"
  action, a managed sandbox integration, etc.) that does not depend on a
  working `git push` from inside the checkout. Commit the fixes locally,
  leave the working tree clean, and use that mechanism.
- **Local only** — neither of the above was possible. This is only a valid
  outcome if you attempted direct git publication — including adding a
  remote for the target repository if none was configured — and confirmed
  no platform-managed publication mechanism exists in this environment.
  Quote the exact command and error that blocked direct publication, and
  state plainly that the fixes have not reached the PR.

Do not report success unless the fixes have actually reached the target PR
by one of the first two paths.

Then provide a summary:
- What was fixed and the fix applied.
- What was skipped and why (presence / validity / feasibility).
