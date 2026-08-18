---
id: PROP-LRH-SECRETS-COMMAND
type: design_proposal
title: "lrh secrets — Graduate Secrets-Hygiene Tooling into a Permanent LRH Command"
status: proposed
created_on: 2026-08-18
updated_on: 2026-08-18
implementation_status: not_started
implemented_by: []
supersedes: []
superseded_by: null
related_design:
  - project/workstreams/proposed/WS-SECRETS-COMMAND.md
---

## Summary

This proposal graduates LCATS's experimental secrets-hygiene scripts
(`find_secrets.py`, `purge_history.py`) into a permanent, reusable LRH
command, `lrh secrets scan|review|purge`, following the graduation pattern
already established by `sourcetree_surveyor` → `lrh survey`. It also adds a
new `review` subcommand that formalizes the currently-manual, unaudited
triage of gitleaks findings before they reach history-rewriting.

## Background / Motivation

LCATS added `lcats/experimental/secrets_hygiene/{find_secrets.py,
purge_history.py}` in PR #315 after discovering a live OpenAI API key
committed in its git history. `find_secrets.py` wraps `gitleaks` to
read-only-scan full git history and draft `findings.json` +
`replacements.txt`. `purge_history.py` wraps `git-filter-repo` to rewrite a
disposable mirror clone scoped to explicit refs, verify the rewrite, and
print (never run) the `git push --force` command. Between the two, a human
today hand-edits `replacements.txt` with no structure, no audit trail, and
no CI gate ensuring every finding was actually looked at.

This capability is not LCATS-specific — any git repository can leak a
secret into its history, and any LRH-managed repo should have this tooling
available without depending on LCATS's experimental tree. LRH already has a
graduation precedent for exactly this situation:
`scripts/aiprog/sourcetree_surveyor.py` → `lrh survey` (commits `200e490f`,
`4a0cd0b6`, `94f58395`), where standalone-script logic moved into an
importable, tested package module and was wired into `src/lrh/cli/main.py`.

This proposal was produced via `/lrh-design` in this session; see that
design's full best-practices survey and pros/cons analysis, which this
document summarizes into governing decisions.

**Update (2026-08-18, post-draft):** while this proposal was in review,
LCATS PR #315 pushed `fa308bb18`, which found and removed a second live
secret — a hardcoded Azure OpenAI key in
`lcats/notebooks/05_prog_llm_csharp.ipynb`, live on `main` since January
2025 — during empirical testing of `find_secrets.py`'s provider coverage.
Azure keys have no distinguishing prefix, so `gitleaks`' built-in
`generic-api-key` rule only catches them contextually, and its delimiter
regex didn't tolerate the backslash that JSON escaping adds inside a
`.ipynb` cell's source. The fix was a repo-root `.gitleaks.toml` adding a
custom `azure-openai-key-contextual` rule, which `gitleaks detect`
auto-discovers from the scanned path's root with no extra flag. This
directly affects Decision 6 below.

**Second update (2026-08-18, handoff prompt from LCATS PR #315):** a
handoff prompt from that PR's author supplies additional first-hand
incident context this design must account for. In short: (a) provider
detection coverage is uneven and must be disclosed to the user, not
assumed uniform — OpenAI/Anthropic/Gemini keys have structural prefixes
`gitleaks` catches reliably, Azure keys do not and depend entirely on
contextual variable naming; (b) a specific, previously-uncaptured
technical gap: inside a Jupyter notebook, source lines are JSON string
literals, so `KEY = "value"` is stored on disk as `KEY = \"value\"` —
`gitleaks`' generic delimiter regex doesn't tolerate that escaping and
silently under-matches on exactly the file type most likely to leak a key
via saved cell output; (c) `purge_history.py`'s printed manual-step
reminders (notify every collaborator/branch-owner before pushing; file a
GitHub Support request to purge cached views if the repo was ever public)
are load-bearing content, not incidental, and must survive graduation;
and (d) the human-review gate between `scan` and `purge` needs to be
enforceable by filename convention, not merely documented — see Decision
3's revision below, which fixes a real gap this update surfaced: `review`
was designed to overwrite `scan`'s draft `replacements.txt` in place,
leaving no filename signal distinguishing reviewed from unreviewed
output. Points (a)–(d) are folded into the decisions and work items
below; three further ideas from the handoff (repo-local `.gitleaks.toml`
scaffolding, a periodic key-lifecycle audit mode, and nudging toward
habit-level fixes such as LCATS's `nbstripout` hook) are real but are new
capabilities, not refinements of `scan`/`review`/`purge` — recorded under
Open Questions rather than added as scope here.

## Prior Art Check

### Duplication search
- In-repo (LRH): No existing implementation found. `lrh.conversations.sensitivity`
  (`project/executions/AD_HOC/2026_05_18_04_51_12_LRH_CONVERSATION_SENSITIVITY_SCANNER.md`)
  is a related but distinct capability — heuristic PII/secret scanning of
  conversation transcripts before export, not git-history scanning or
  history rewriting. No functional overlap.
- Sibling repos: LCATS, at `lcats/experimental/secrets_hygiene/` — this is
  the source being graduated, not a duplicate.
- External libraries: `gitleaks` (scan) and `git-filter-repo` (rewrite) are
  the tools already chosen and wrapped by the experimental scripts;
  `git-filter-repo` is GitHub's own documented recommendation over
  deprecated BFG/`git filter-branch`. No reason to look further.
- Recommendation: **Proceed.**

### Demand search
- Work items: None found (`project/work_items/`).
- Proposals: None found (`project/design/proposals/`).
- Backlog: No matching entries (`project/design/backlog.md`).
- Recommendation: **No action** — net-new territory.

## Design Decisions

### Decision 1: Command shape

Options considered:
- Flat top-level commands (`lrh secrets-scan`, `lrh secrets-review`, `lrh secrets-purge`)
- Nested group (`lrh secrets scan|review|purge`), matching `lrh work-items organize|validate|audit|readiness`

**Chosen: nested group.** `work-items` is the closest existing precedent for
several related subcommands sharing a target-repo argument and mutation
gating; `secrets` fits that shape exactly. Implementation lives in
`src/lrh/secrets/{scan,review,purge}.py` as plain functions (no
`run_x_cli` wrapper — that convention is reserved for standalone
single-parser commands), dispatched from `src/lrh/cli/main.py` via
`if args.command == "secrets": if args.secrets_command == "scan": ...`.

### Decision 2: How `lrh secrets` addresses a target repo

Options considered:
- A bare positional `repo_path`, matching `find_secrets.py`'s existing signature
- LRH's established `--project-root` convention (seen in `work_items/organize.py`, `snapshot_cli.py`), default cwd

**Chosen: `--project-root`, default cwd**, for `scan` and `review` (both
read/report against a checked-out repo). `purge` additionally accepts
`--source <url-or-path>`, defaulting to `git -C <project-root> remote
get-url origin` when omitted, since `purge_history.py`'s mirror-clone step
needs an explicit clone source that may differ from the local checkout
path (e.g. a URL). This keeps the CLI consistent with the rest of `lrh`
while preserving the original script's flexibility to target an arbitrary
remote.

### Decision 3: Closing the manual `replacements.txt` triage gap

Options considered:
- Leave triage as free-text hand-editing of `replacements.txt` (status quo)
- Add `review` as an interactive y/N prompt loop over findings
- Add `review` as a decisions-file-gated step

**Chosen: decisions-file-gated `review`.** LRH has no interactive-prompt
convention anywhere in its CLI (gating is flag-based:
`--dry-run`/`--check`/`--apply`). `lrh secrets review` reads
`findings.json` + the draft `replacements.txt` and requires a `--decisions
<file>` (one entry per unique secret: `keep`/`ignore` + reason) before
writing a final, reviewed replacements file. `--check` fails if any
finding is undecided — usable as a CI gate blocking an unreviewed scan
from ever reaching `purge`. This keeps the no-prompts convention intact
while making triage auditable, which the free-text status quo is not.

**Revised per the handoff-prompt update above:** the original draft of
this decision had `review --apply` overwrite `scan`'s draft
`replacements.txt` in place — same filename for both the unreviewed and
reviewed state. The handoff's emphasis that `purge` "must refuse to run
without an explicit, human-reviewed input from the scan stage — never
scan-then-auto-purge" exposed this as a real gap: nothing would stop
`purge --replacements` from being pointed at the unreviewed draft before
`review` ever ran, since the tool has no way to distinguish the two states
by inspecting the file. Fix: `review --apply` writes to a distinctly-named
`<out-dir>/replacements.reviewed.txt`, leaving `scan`'s draft
`<out-dir>/replacements.txt` untouched. `purge`'s `--replacements`
argument is documented as expecting the `.reviewed.txt` output — the
naming difference is the enforcement mechanism, consistent with this
codebase's convention of flag/file-based gating rather than runtime
provenance tracking.

### Decision 4: Preserving `purge_history.py`'s safety invariants

This is the first LRH command wrapping a history-rewriting/destructive-adjacent
external tool. The experimental script's existing invariants are carried
over **unmodified, not relaxed into optional flags**:
- Operates only on a fresh `--mirror` clone in a scratch dir; never touches `--project-root`'s working tree.
- `--refs-file` is mandatory; omitting it is a hard failure, not a flag toggle.
- Always re-verifies the mirror is clean of every listed secret after rewrite; a failed verification is a hard `exit(1)`.
- **No `--push` flag exists, ever** — the push command is always printed, never executed. This is an omission by design: there is no code path from this tool to `git push`.
- `--apply` performs the mirror-clone + rewrite + verify; without it (`--dry-run`), the command validates inputs (refs file well-formed, replacements file exists, binaries present) without cloning or rewriting anything.
- **Per the handoff-prompt update above:** `purge_history.py`'s existing printed manual-step reminders — notify every collaborator/branch-owner before pushing (a stale clone's `git pull` silently reintroduces the purged secret via merge, it does not error), and file a request with the git host's support team to purge cached views/forks if the repo was ever public — are preserved verbatim in spirit in the graduated command's output alongside the push command, not dropped as "just documentation." These reminders are exactly as load-bearing as the push command itself.

### Decision 5: Disposition of the LCATS standalone scripts

Options considered:
- Delete immediately in the same PR (exact `sourcetree_surveyor` precedent)
- Keep temporarily with a deprecation note

**Chosen: delete via a fast-follow companion PR in LCATS**, not in the same
PR — the scripts live in a different repository than this graduation, so a
same-commit deletion is impossible. Once `lrh secrets` lands and is
validated in LRH, open a companion LCATS PR deleting
`lcats/experimental/secrets_hygiene/{find_secrets.py,purge_history.py}` and
updating `lcats/docs/how-to/secrets-hygiene.md` to point at `lrh secrets`.
Leaving the scripts in place indefinitely with only a deprecation note
would recreate the two-tools-doing-one-job problem this proposal exists to
fix, so that option is rejected.

### Decision 6: Preserving target-repo `gitleaks` config (e.g. LCATS's `.gitleaks.toml`)

Newly relevant per the 2026-08-18 update above: LCATS now ships a
repo-root `.gitleaks.toml` with a custom `azure-openai-key-contextual`
rule, added specifically because the default ruleset missed a real, live
key. `gitleaks detect --source <path>` auto-discovers `.gitleaks.toml` at
the scanned path's root with no extra flag — since `scan.py`'s design
already passes `--project-root` straight through as `--source` (Decision
2), this works automatically with no code change required, *as long as
`scan.py` never passes an explicit `--config`/`--no-config`-style override
that would suppress that auto-discovery*. This must be an explicit,
tested requirement of `WI-SECRETS-SCAN`, not an implicit assumption —
before this update, this proposal's Non-Goals characterized Azure-key
coverage purely as a hypothetical future gap; it is now a real gap that a
real target repo has already fixed at the config layer, and graduating a
scan wrapper that accidentally overrides that fix would be a regression
against LCATS's own incident response.

Options considered:
- `scan.py` passes no config-related flags at all, relying entirely on `gitleaks`' own auto-discovery (chosen)
- `scan.py` adds an explicit `--config <path>` passthrough flag now, for repos whose `.gitleaks.toml` doesn't live at `--project-root`

**Chosen: rely on auto-discovery for now; defer an explicit `--config` flag.**
Every case seen so far (LCATS) keeps `.gitleaks.toml` at the repo root,
which matches `--project-root` by construction, so auto-discovery is
sufficient today. An explicit `--config` override is easy to add later as
a non-breaking flag if a repo with a non-standard layout needs it — no
reason to speculatively build it now.

### Decision 7: Disclosing provider-coverage limitations to the user

Per the handoff prompt: "provider coverage is uneven and worth surfacing
to the user, not assuming uniform." `find_secrets.py`'s own README already
documents this empirically (OpenAI/Anthropic/Gemini keys caught reliably
via structural prefixes; Azure keys caught only contextually; and, newly,
the notebook JSON-escaping delimiter gap that let a live Azure key sit
undetected). The gap is that this knowledge lived only in the LCATS
README — nothing required the graduated `scan` command itself to surface
it to a user running it against an unfamiliar repo.

Options considered:
- Leave coverage caveats as external documentation only (status quo — the risk this decision addresses)
- Require `scan`'s own `--help`/docstring and printed run summary to state known coverage gaps

**Chosen: require disclosure in the tool itself**, not only in
prose documentation elsewhere. `WI-SECRETS-SCAN` must document, in its
module docstring and `--help` output, that (a) Azure-family keys have no
structural prefix and are only caught via contextual rules — either
`gitleaks`' default `generic-api-key` rule or a target repo's own
`.gitleaks.toml` extension (Decision 6) — and are invisible to
pattern-based scanning entirely if assigned to a non-suggestive variable
name, and (b) `.ipynb` files store source as JSON-escaped strings, which
can defeat delimiter-based rules that don't account for the escaping,
regardless of provider. This is disclosure, not new detection logic —
`scan.py` still wraps `gitleaks` unmodified per Decision 6.

## Non-Goals

- Does not implement `lrh secrets push` or any flag that executes `git push --force` — the push step remains permanently manual by design, not merely by default.
- Does not vendor or pip-install `gitleaks`/`git-filter-repo` — both remain required external binaries on `PATH`, with fail-fast install hints on absence.
- Does not delete the LCATS experimental scripts in this PR — that is a separate, fast-follow LCATS-side PR (see Decision 5).
- Does not expand `gitleaks`' *default* rule coverage, and does not add rule-authoring tooling — rule-set tuning (e.g. LCATS's project-specific `azure-openai-key-contextual` rule in its repo-root `.gitleaks.toml`, added in PR #315 `fa308bb18`) is each target repo's own responsibility, not `lrh secrets`'. `scan.py` must preserve `gitleaks`' automatic discovery of a target repo's own `.gitleaks.toml` unmodified (see Decision 6) — that is in scope as a preservation requirement, not as new coverage this proposal builds.
- Does not decide whether/when to actually run an all-branches purge against LCATS's real leaked-key history — that operational decision is separate from shipping the tool.
- Does not implement repo-local `.gitleaks.toml` scaffolding/management, a periodic key-lifecycle/audit reminder mode, or remediation-pattern nudging (e.g. suggesting a habit-level backstop like LCATS's `nbstripout` hook when a leak is found) — all three are real ideas from the handoff prompt but are new capabilities beyond scan/review/purge; see Open Questions.

## Implementation Plan

Delivered under `WS-SECRETS-COMMAND`, as three work items in dependency order:

1. `WI-SECRETS-SCAN` — `lrh secrets scan` (no dependencies)
2. `WI-SECRETS-REVIEW` — `lrh secrets review` (depends on `WI-SECRETS-SCAN`'s output format)
3. `WI-SECRETS-PURGE` — `lrh secrets purge` (depends on both — consumes `review`'s finalized `replacements.txt`)

Each work item carries a hard test-coverage requirement (`tests/secrets_tests/`
module tests + `tests/cli_tests/secrets_test.py` CLI-dispatch tests,
mirroring `tests/assist_tests/sourcetree_surveyor_test.py` and
`tests/cli_tests/survey_test.py`), since this graduates code with no
existing coverage today and `purge` specifically rewrites git history.

## Cross-References

- Workstream: `project/workstreams/proposed/WS-SECRETS-COMMAND.md`
- Graduation precedent: `src/lrh/assist/sourcetree_surveyor.py`, `tests/cli_tests/survey_test.py`
- Grouped-command precedent: `src/lrh/work_items/organize.py`, `src/lrh/cli/main.py` (`work-items` dispatch)
- Related capability (transcript scanning, not history scanning): `src/lrh/conversations/sensitivity.py`
- Source scripts being graduated: LCATS `lcats/experimental/secrets_hygiene/{find_secrets.py,purge_history.py,README.md}`
- Azure-key incident and config-preservation requirement (Decision 6): LCATS PR #315 commit `fa308bb18` ("fix: remove live Azure OpenAI key found during coverage testing; add custom gitleaks rule"), LCATS repo-root `.gitleaks.toml`

## Open Questions

- Should `purge`'s `--source` default (derived from `git remote get-url origin`) replace `purge_history.py`'s original required-positional `source`, or should the graduated command keep the positional for a closer 1:1 port? Recommended: the `--project-root`-derived default, for CLI consistency — but this is a UX-consistency-vs-minimal-diff tradeoff worth a second opinion during `WI-SECRETS-PURGE` implementation.
- Exact `decisions` file format (YAML shape, key names) for `review` is left to `WI-SECRETS-REVIEW`'s implementation rather than fixed here.
- Should `lrh secrets` eventually scaffold/manage a repo-local `.gitleaks.toml` (e.g. `lrh secrets rules init`) rather than only relying on a target repo to maintain one by hand? The handoff prompt notes `gitleaks`' `[extend] useDefault = true` mechanism is a clean base to build on. Deferred — no work item in this workstream covers it; would need its own design/prior-art pass (including the handoff's precision/recall lesson: any shipped rule must be empirically validated against a real repo before landing, not assumed additive) if picked up later.
- Should `lrh secrets` grow a periodic audit/key-lifecycle-reminder mode, given the handoff's finding that OpenAI keys have no native expiration and nothing else prompts periodic review across provider dashboards? Deferred — out of scope for the scan/review/purge pipeline; would be a distinct capability if pursued.
- Should `scan` or `review` output nudge toward habit-level remediation (e.g. "this pattern also exists in N other files" or "consider a pre-commit stripping hook"), per the handoff's observation that the same leaky print pattern existed dormant in six other LCATS notebooks beyond the one that actually leaked? Deferred — real UX idea, not required for this workstream's exit criteria.
