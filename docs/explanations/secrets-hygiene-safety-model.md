# The secrets-hygiene safety model

`lrh secrets purge` is the first LRH command that wraps a
destructive, history-rewriting external tool
([`git-filter-repo`](https://github.com/newren/git-filter-repo)). Its
surrounding commands, `scan` and `review`, exist to make sure a human
decision always sits between "gitleaks found something" and "history got
rewritten." This document explains why the pipeline is shaped the way it
is — for exact command syntax, see the
[CLI reference](../reference/cli/secrets.md); for a walkthrough, see
[Scan, review, and purge secrets](../how-to/scan-and-purge-secrets.md).

## Why `scan` can never feed `purge` directly

`scan`'s draft `replacements.txt` is gitleaks' raw opinion about what looks
like a secret. Gitleaks' rules match on shape and entropy, not certainty —
a pinned dependency string in a conda `environment.yml` can trip the
`generic-api-key` rule as easily as a real leaked key. If `purge` accepted
that draft directly, a single noisy scan could rewrite a repository's
history over false positives, with no human ever having looked at what was
about to be purged.

`review` closes that gap by requiring an explicit `decision` (`keep` or
`ignore`) *and* a non-empty `reason` for every finding before it will
produce `replacements.reviewed.txt` — a file with a different name from
`scan`'s draft, on purpose, so the two are never visually or
programmatically interchangeable. `purge` then checks this at runtime, not
just by convention: `--replacements` must begin with the exact marker line
`# lrh-secrets-reviewed v1`, or `purge` refuses to run before any clone is
attempted. Pointing `purge` at `scan`'s own draft output is a hard failure,
by design, not an oversight.

This traces back to a real incident: a leaked Azure key sat undetected in
a notebook for a period before discovery, in part because delimiter-based
detection missed JSON-escaped source inside `.ipynb` files. The lesson
that shaped this pipeline wasn't "scan harder" — it was "never let an
automated scan's output drive an automated rewrite." A human has to look.

## Why `purge` is mirror-only and verify-after

`purge` never touches `--project-root`'s own working tree. It clones the
target into a disposable mirror (`--mirror-dir`, or a fresh temp directory
by default), rewrites history there, and only then re-scans the rewritten
mirror to confirm every listed secret is actually gone — using a literal
string match (`git log --all -S<secret>`, deliberately without
`--pickaxe-regex`, so a secret containing regex metacharacters like `ab+c`
can't produce a false "clean" result). If that verification finds anything
remaining, `purge` exits nonzero and prints no push command. Nothing is
ever presented as safe to push until it has actually been confirmed clean.

## Why `purge` never runs `git push`

There is no `--push` flag, and no code path anywhere in `purge` that
invokes `git push` — this is a hard invariant, not a default a flag could
turn off. On a clean rewrite, `purge` prints the exact `git push --force`
command for a human to run manually, together with two reminders that are
just as load-bearing as the command itself:

- **Notify every collaborator and branch-owner before pushing.** A stale
  clone's `git pull` silently reintroduces the purged secret via merge — it
  does not error, and there is no automated way to detect that it happened.
- **File a support request with the git host to purge cached views and
  forks if the repository was ever public.** Rewriting history and pushing
  the rewrite does not reach anything the host itself cached, or any fork
  that already has the old history.

Both reminders — and the invariant that this command never pushes on its
own — carry over unmodified from the experimental tooling this command was
graduated from, which earned them from planning an actual history-rewrite
against a real leaked-key incident. They are not generic caution; they are
specific, hard-won operational knowledge about what actually goes wrong
after a history rewrite if a human doesn't do these two things.

## What this pipeline deliberately does not do

- It does not decide *when* to run a purge against a real incident — that
  operational decision belongs to whoever owns the repository, not to this
  tooling.
- It does not expand gitleaks' rule coverage (for example, closing the
  Azure-key detection gap) — that is scan-quality tuning, tracked
  separately from the pipeline's own safety invariants.
- It does not attempt to automate collaborator notification or host
  support requests — both remain manual, on purpose, because both require
  human judgment about who is affected and what a given host's process
  actually requires.
