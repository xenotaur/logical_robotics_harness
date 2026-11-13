---
id: EV-CODEX-MANAGED-SANDBOX-NETWORK
title: Codex managed-sandbox GitHub networking incident
type: incident_report
status: draft
owner: anthony
related_work_items:
  - WI-CODEX-MANAGED-SANDBOX-NETWORK-INCIDENT
related_workstreams:
  - WS-LRH-GITHUB-EXECUTION-RESILIENCE
---

# Codex Managed-Sandbox GitHub Networking Incident

## Status

- Incident type: Codex managed-sandbox DNS/egress isolation
- Evidence status: reproducible comparison recorded; external report reference
  pending
- Scope: GitHub-backed LRH commands executed from Codex managed sandboxes
- Owner: `anthony`
- Next diagnostic: repeat the decisive pair after a platform or executor-policy
  change, and determine whether normal execution succeeds without escalation

## Executive summary

The same GitHub connectivity checks were run from the same macOS host, working
directory, repository, GitHub CLI version, and credential context. Normal Codex
sandbox execution failed DNS/HTTPS access, while explicitly approved network
execution succeeded. This isolates the immediate blocker to the normal sandbox
network path or namespace rather than LRH, the repository, GitHub CLI command
selection, or GitHub service availability.

The credential signal is kept separate: an earlier `gh auth status` result was
inconsistent across sessions, but authentication cannot be diagnosed reliably
until the affected execution path can reach GitHub.

## Reproduction and comparison

### Observed timestamps

- `2026-09-26 19:42:10` local macOS Terminal: Python DNS resolution
  succeeded.
- `2026-09-26 19:42:11` local macOS Terminal: `curl` returned HTTP 200.
- The normal-sandbox and approved-execution comparison was performed during the
  same investigation, but its executor-side timestamps were not exposed in the
  report available to this repository; they are recorded as unavailable rather
  than inferred.

The decisive comparison used the same checkout and commands in two execution
modes. Output below is reduced to exit codes and short error categories; no
tokens, authorization headers, full API bodies, or private transcripts are
included.

| Check | Normal sandbox | Approved/elevated execution |
|---|---|---|
| Python `socket.getaddrinfo("api.github.com", 443)` | exit 1; DNS resolution failure | exit 0; address returned |
| `curl -I --max-time 10 https://api.github.com` | exit 6; could not resolve host | exit 0; HTTP 200 |
| `gh api graphql` viewer query | exit 1; connection/DNS failure | exit 0; success |
| REST `gh api` | failed | succeeded |
| `gh pr list` | failed with `lookup api.github.com: no such host` | succeeded |

The approved run used the same repository, working directory, `gh` version,
and credentials as the normal run. A five-iteration paired GraphQL/`gh pr list`
test also failed consistently in an affected normal sandbox, while a known-good
session passed all five iterations.

### Replayable sanitized invocations

These are the complete GitHub invocations used for the comparison. They omit
only credentials, authorization headers, and response bodies:

```sh
gh api -X GET repos/xenotaur/logical_robotics_harness/pulls \
  -f state=open -f per_page=5 \
  --jq '.[] | [.number,.head.ref,.base.ref,.title] | @tsv'
# normal sandbox: exit 1 (DNS/connection failure)
# approved execution: exit 0 (five pull-request records returned)

gh api graphql \
  -f query='query { viewer { login } }' \
  >/dev/null
# normal sandbox: exit 1 (DNS/connection failure)
# approved execution: exit 0 (success)

GH_DEBUG=api gh pr list \
  -R xenotaur/logical_robotics_harness \
  --state open \
  --limit 5 \
  --json number,headRefName,baseRefName,title \
  >/dev/null
# normal sandbox: exit 1 (`lookup api.github.com: no such host`)
# approved execution: exit 0 (HTTP 200; success)
```

## Additional observations

- `dig` in the affected normal sandbox reported `bind: Operation not
  permitted`.
- `dscacheutil` could exit successfully without printing an address record;
  exit status alone was therefore not treated as DNS success.
- A normal macOS Terminal and at least one other Codex session resolved
  `api.github.com`, received HTTP 200, and completed REST, GraphQL, and PR-list
  checks.
- Fresh Codex projects and sessions reproduced the failing normal-sandbox
  behavior, so repository identity and thread identity do not establish a
  shared executor or network namespace.
- Session, project, executor, and host identifiers were not consistently
  exposed; unavailable identifiers are intentionally not inferred.

## Conclusion and alternatives

Strong conclusion: the failing execution path has a normal-sandbox DNS/egress
restriction or provisioning defect. The evidence does not identify whether the
root cause is per-session provisioning, per-project policy, or shared Codex
network infrastructure.

Weaker or separate hypotheses:

- LRH repository or worktree defect: weakened by success from the same checkout
  through approved execution.
- GitHub CLI defect: weakened because REST, GraphQL, `curl`, and Python DNS all
  fail together only in the normal sandbox.
- GitHub outage: contradicted by HTTP 200 and successful API calls through
  approved execution and normal Terminal.
- Credential failure: unresolved and secondary; network access must be restored
  before comparing credential validity.
- macOS host networking: weakened, but not fully excluded, because the normal
  Terminal path worked while the managed sandbox path failed.

## Safe operational workaround

For GitHub-dependent LRH operations, use normal execution for local-only work.
When a GitHub or remote-Git command fails with a sandbox DNS/HTTPS category,
request the explicitly approved network execution path and retry the exact
command once. If approval is unavailable or the retry fails, report a blocker.
Do not refresh, replace, expose, or reauthorize credentials for a DNS or
connection failure.

## External report and follow-up

- External report destination: appropriate OpenAI/Codex support or bug-report
  channel
- Report date: pending submission
- Non-secret report reference: pending submission
- Platform response: pending
- Durable network-policy or executor fix: not established
- Follow-up owner: `anthony`

The report should include this sanitized comparison, the observed timestamps
from the diagnostic session, the available execution-context description, and
the distinction between normal and approved execution. It should not include
tokens, authorization headers, full API response bodies, private transcripts,
or private repository contents.
