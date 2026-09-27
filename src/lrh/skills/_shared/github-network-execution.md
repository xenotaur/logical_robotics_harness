# Bounded GitHub Network Execution

Use normal execution for local-only work: reading and editing files, local Git
inspection, parsing, formatting, linting, tests, and `lrh validate`.

Commands that contact GitHub or a remote Git server include `gh`, `git fetch`,
`git pull`, `git push`, `git ls-remote`, PR/review/check queries, and
GitHub-backed LRH commands. In a restricted sandbox, a DNS or HTTPS failure
for one of these commands can be an executor network-policy failure even when
the same command works in an approved execution path.

When a remote command fails:

1. Confirm the absolute project root and current repository before retrying:
   `git rev-parse --show-toplevel` and `pwd`. Do not reinterpret an invalid
   project root as a credential or executable problem.
2. Preserve the original command and its short, redacted error category.
3. Request approved network execution for one bounded retry of that exact
   command. Do not loop, broaden the command, or make every command elevated.
4. If the approved retry succeeds, continue and record that approved path was
   required. If approval is unavailable or the retry fails, report a blocker
   with the command category, exit status, and next safe diagnostic.

Do not refresh, replace, expose, or reauthorize credentials to address DNS,
connection, or sandbox-policy failures. Diagnose authentication separately
only after the execution path can reach GitHub. Do not silently replace a
required remote check with `--no-remote` or a local-only approximation.

Canonical source: `src/lrh/skills/_shared/github-network-execution.md`.
