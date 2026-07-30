# Design Backlog

Lightweight list of deferred ideas that are not yet ready for a formal
proposal or work item. Each entry should record what was noted, why it was
deferred, and where it came from so a future reader can act on it without
re-deriving context.

---

## Idempotence-check refinements deferred from PR #438 (follow-up PR)

**Noted:** 2026-07-30, during PR #438's 6th automated review round, after
5 prior rounds had already narrowed the same `find`-by-slug idempotence
check in `lrh-proposal`/`lrh-work-item`/`lrh-workstream` (Step 4 +
`references/execution-record.md`, 6 locations) through several genuine
edge-case fixes (undefined placeholder, substring-match false positive,
missing-directory error, status-blind blocking, missing `--rerun-of`
propagation, ambiguous match selection).

**Idea — two remaining known gaps, deferred by explicit user decision
rather than fixed inline to avoid further scope creep on PR #438:**

1. **Cross-status `rerun_of` precedence (Codex, round 6).** When matches
   span mixed statuses — e.g. an older `landed` record plus a newer
   `failed` rerun of the same slug — the current logic blocks correctly
   (any `landed`/`in_progress` match blocks) but then retains *that*
   blocking match's `execution_id` for `--rerun-of`, not necessarily the
   most recent attempt overall. The new record's `rerun_of` can end up
   pointing at an older run instead of the immediately preceding one.
   Properly fixing this means restructuring the two-bucket
   (blocking-status vs. non-blocking-status) logic into a single
   most-recent-by-timestamp selection that then determines block/no-block
   from that record's status — a real redesign, not a one-line patch,
   replicated across 6 locations.

2. **`find` exit status on a missing `AD_HOC/` directory (Copilot,
   recurring low-confidence, rounds 4, 6, and 7).** `2>/dev/null`
   suppresses the error message but not `find`'s non-zero exit status when
   `project/executions/AD_HOC/` doesn't exist yet; an error-stopping
   runner could treat that as a failure. Copilot also suggested sorting
   the `find` output so "most recent match" selection (used throughout
   this idempotence check) is deterministic rather than relying on
   filesystem iteration order.

3. **Explicit-rerun branch-name collision (Codex, round 7).** When a user
   explicitly reruns a matched `in_progress` record that's still on its
   original feature branch, Step 6's `git checkout -b
   <username>/<type>/<slug>` uses the same deterministic branch name as
   the original attempt and fails with `fatal: a branch named ... already
   exists`, blocking the rerun before it reaches Step 10. Needs a decision
   on whether reruns reuse the existing branch or create a suffixed one
   that still carries the prior record forward for `rerun_of`.

4. **`find` only searches the current working tree (Codex, round 8).** If
   a prior `in_progress` record exists only on its own open PR branch and
   a new invocation starts from `main` or a fresh checkout, the `find`
   search reports no match — it never looks at other local or remote
   branches. The workflow then mints an unlinked duplicate record, which
   can later collide with the same deterministic branch name (item 3) or
   push conflict. Needs a decision on whether to query relevant PR/remote
   branches, or require checking out the active branch first, before
   concluding no prior run exists.

**Status:** Deferred — PR #438's original purpose (fixing 8 bugs in
`lrh-closeout`/`lrh-proposal`/`lrh-work-item`/`lrh-workstream`/`lrh-land`
that blocked Taurcode's downstream skill resync) was already done and
validated after 5 review rounds. Continuing to harden this idempotence
check's edge-case precedence is lower value while the check's more
fundamental design question — whether filename-slug search should drive
blocking at all — remains open (see "Filename-slug idempotence search
drives blocking, contrary to `PROMPTS.md`" below); a full fix here could
be partly obsoleted by resolving that question differently. Merged as-is;
address all four items in a follow-up PR.

**Related:** harness PR #438 (rounds 4, 6, and 7);
`src/lrh/skills/lrh-proposal/SKILL.md`,
`src/lrh/skills/lrh-work-item/SKILL.md`,
`src/lrh/skills/lrh-workstream/SKILL.md` (Step 4, idempotence check) and
their `references/execution-record.md` mirrors; "Filename-slug idempotence
search drives blocking, contrary to `PROMPTS.md`" entry below.

---

## Filename-slug idempotence search drives blocking, contrary to `PROMPTS.md`

**Noted:** 2026-07-29, during PR #438 review (fixing bugs in `lrh-closeout`,
`lrh-proposal`, `lrh-work-item`, `lrh-workstream` surfaced by Taurcode's
downstream resync of these skills).

**Idea:** `PROMPTS.md`'s "Soft idempotence before execution" section is
explicit: "Exploratory search results can provide useful context for
discovery, auditing, and debugging, but they should not by themselves drive
blocking or rerun decisions" — only an exact structured `prompt_id` lookup
(`lrh prompt check-execution`) is authoritative for blocking. But
`lrh-proposal`, `lrh-work-item`, and `lrh-workstream` (added in PR #438,
addressing a Codex finding that `lrh prompt label` always mints a fresh
timestamped ID so `check-execution` alone can't catch a rerun) search
`project/executions/AD_HOC/` by filename-slug match *before* minting, and
that filename match itself drives a stop-and-report block on
`in_progress`/`landed` records. This is not a new pattern invented for PR
#438 — it was copied from the pre-existing, already-merged
`lrh-review-response/SKILL.md:122-131`, which does the identical
"find by filename slug → stop and report" thing and was cited as the
precedent to follow. So either that existing skill already violates the
`PROMPTS.md` rule and it's gone unnoticed, or there's an implicit accepted
exception for this specific pre-mint case that the general rule doesn't
anticipate.

Resolving this properly means deciding, then applying consistently across
all four skills (`lrh-review-response` included): should filename-slug
discovery ever be blocking, or should it always be presented as
context/confirmation-request only (per the literal `PROMPTS.md` rule)? That
is a design decision bigger than a single-PR bug fix, and touching
`lrh-review-response` was out of scope for PR #438.

**Status:** Resolved (lightweight) — 2026-07-30. Revisited three options:
(1) codify the exception in `PROMPTS.md` — the exact-ID lookup mechanism
genuinely cannot answer "has this slug run before" since no ID exists yet
to look up, so filename-slug search isn't the same kind of thing as the
fuzzy/heuristic discovery the original rule was warning about; (2) make
slug discovery non-blocking everywhere, literally complying with the old
wording, at the cost of turning every rerun path interactive; (3) build a
real CLI mechanism (e.g. `check-execution --slug`) so slug-based duplicate
detection becomes genuinely authoritative tooling, not a hand-rolled `find`
in prose — touches the CLI, its tests, `PROMPTS.md`, and all 4 skills.

Went with **option 1**: `PROMPTS.md`'s "Soft idempotence before execution"
section now has a "Pre-mint duplicate detection by slug" subsection
explicitly naming filename-slug-by-bucket search (matched to the complete
trailing filename segment, not a substring) as authoritative for this
specific pre-mint case, distinct from the still-non-authoritative general
exploratory/fuzzy search. No code changes — `lrh-review-response`,
`lrh-proposal`, `lrh-work-item`, and `lrh-workstream`'s existing behavior
is now correctly documented rather than an undocumented exception. Chosen
over options 2 and 3 as proportionate to the actual (narrow) risk without
touching working code across 4 skills again.

**Not done — revisit if this resurfaces:** option 3 (real CLI tooling for
slug-based duplicate detection) remains the more complete long-term fix.
Revisit if the current `find`-based approach causes a real incident (a
legitimate rerun blocked by a stale/irrelevant filename match), or if a
5th skill needs the same pattern and hand-copying the `find` command again
starts to feel like the wrong layer for this logic.

**Related:** `PROMPTS.md` "Soft idempotence before execution" section
(now includes the "Pre-mint duplicate detection by slug" subsection);
`src/lrh/skills/lrh-review-response/SKILL.md` Step 3;
`src/lrh/skills/lrh-proposal/SKILL.md`,
`src/lrh/skills/lrh-work-item/SKILL.md`,
`src/lrh/skills/lrh-workstream/SKILL.md` (Step 4, idempotence check);
harness PR #438; harness PR #440 (this resolution).

---

## Validator drift-check for synced skill references

**Noted:** 2026-06-30, during `WS-PRIOR-ART-CHECK` design session.

**Idea:** Extend `lrh validate` (or a small standalone script) to diff each
consuming skill's copy of a shared reference doc against the `_shared/`
master and fail on drift — replacing the comment-only sync convention
currently used for `prior-art-check.md` copies.

**Status:** Deferred — not in scope for `WS-PRIOR-ART-CHECK`. The current
approach is a header comment in each copy naming the master file. Revisit
if copies are observed drifting in practice.

Re-examined 2026-07-22 during a design review of the "Agent-specific
publication guidance" entry below, which initially cited section-header
wording differences between `review_response.md` and `review_protocol.md`
(`## 1) Triage` vs `## 1) Triage each reported comment/issue`, and
similarly for sections 4 and 5) as evidence this trigger had fired. A PR
#406 reviewer correctly flagged that this was a false premise: `git show
2300612:.../review_response.md` and `.../review_protocol.md` show those
exact header differences already present when the two files were first
introduced, well before PR #405 — and PR #405's diff (`9b3010b`) never
touched the headings. That is a preexisting, apparently intentional
stylistic difference, not post-sync drift; the trigger has not fired.

What PR #405 *did* demonstrate is duplicate-edit toil: the same two
generic-correctness fixes (`headRefOid` identity check; head-repo-derived
remote) had to be applied by hand, identically, to both files — without
producing drift. That is a real cost of the manual-sync convention, but it
is a different problem than this entry addresses (this entry is about
detecting divergence once introduced, not about eliminating the need to
edit two files). It does not by itself satisfy "copies observed drifting
in practice." Continue to defer until an actual post-sync divergence is
observed, or revisit this entry's scope to also address duplicate-edit
toil (e.g. via a de-duplication mechanism) rather than drift detection
alone.

For the `review_response.md`/`review_protocol.md` pair specifically, the
duplicate-edit-toil path (de-duplication / single-sourcing) is now captured
as Option 4 in
`project/design/proposals/proposed/agent-targeted-review-response-templates/00_proposal.md`;
that proposal is the resolution path for this pair. This entry remains open
only for the `prior-art-check.md` fan-out, where a `_shared/` master plus 5
skill copies genuinely exists and drift detection would still apply if drift
is observed there.

**Related:** `project/workstreams/proposed/WS-PRIOR-ART-CHECK.md` Non-Goals;
`src/lrh/assist/templates/request/review_response.md`;
`src/lrh/assist/templates/request/review_protocol.md` (candidate second
copy pair, see entry below — not yet an observed-drift instance);
`project/design/proposals/proposed/agent-targeted-review-response-templates/00_proposal.md`.

---

## `/lrh-decision` skill for authoring `project/memory/decisions/*.md` files

**Noted:** 2026-07-05, during design and implementation of
`WI-DECISION-RECORD-CONVENTIONS`.

**Idea:** A skill (parallel to `/lrh-work-item` and `/lrh-proposal`) that
interviews the user and writes a new `project/memory/decisions/<slug>.md`
file — following the `Context` / `Options considered` / `Decision` /
`Invariants` / `Consequences` shape and the `DEC-*` id convention — for a
decision that resolves an ambiguity or contradiction in existing docs or
implementation. Distinct from `/lrh-proposal`, which proposes new design
direction under a proposed/adopted lifecycle; `/lrh-decision` would record a
decision that's already effectively made, promoted out of
`project/memory/decision_log.md` because other documents need to cite it
independently and repeatedly.

**Status:** Deferred — only one promoted decision file exists in this repo
(`project/memory/decisions/precedence_semantics.md`). The interview
questions and body-section shape can't be specified with confidence from a
single instance; a synthetic second file would prove nothing. Revisit once a
second `project/memory/decisions/*.md` file is created by hand and the
promotion pattern (see `design.md` §14 "Decision-record tiers") has a real
second data point.

**Related:** `project/work_items/resolved/WI-DECISION-RECORD-CONVENTIONS.md`
Non-Goals; `project/design/design.md` §14 "Decision-record tiers"; `project/memory/decisions/precedence_semantics.md`.

---

## Agent-specific publication guidance for `review_response`/`review_protocol`

**Noted:** 2026-07-21, while dogfooding the `review-response` prompt against
Codex Cloud on an external repo (`xenotaur/LCATS#140`).

**Idea:** `review_response.md`/`review_protocol.md` were made agent-neutral
about *how* fixes reach a PR — a three-way outcome (pushed directly /
submitted via platform / local only) instead of assuming `git push` always
works — because different agent sandboxes publish PR fixes through
different mechanisms (direct git push, a platform "Update PR" action with
no working git push inside the container, etc.) and the prompt can't know
in advance which one a given execution environment provides. That generic
framing is deliberately vague about the concrete idiom for any one agent
(e.g. it can't say "click Update PR" because it doesn't know the agent is
Codex).

A sharper version would let `lrh request review-response` accept a target
agent (the `--target-agent`/`REQUEST_TARGET_AGENT` plumbing already exists
for `audit_docs`/`organize_docs`, see `request_cli.py` and
`request_service.py`, but isn't wired into `review_response`) and inject a
short, Python-selected "publication guidance" string naming the concrete
mechanism for known agents, while leaving the rest of the prompt
(triage/validation/evidence, which is agent-independent) single-sourced —
not a full per-agent template file, which would duplicate the ~90% of the
prompt that has nothing to do with publication and re-create the
maintenance burden the `review_response.md`/`review_protocol.md` manual
sync note already causes with just two copies.

**Status:** Deferred — reviewed again 2026-07-22 after PR #405's own review
round grew the precondition/output sections twice more (tightening
`headRefOid` identity verification; deriving the "Local only" remote from
the PR's head repository, not the base repository). Both changes were
generic-correctness fixes applied identically to both `review_response.md`
and `review_protocol.md` — not an instance of a specific agent's
publication idiom needing to be spelled out. This entry's trigger — "a
specific agent's publication idiom repeatedly needs spelling out beyond
what the generic three-way vocabulary can convey" — has still not fired;
generic-correctness churn on the shared prose does not count toward it and
should not be mistaken for it in a future review. That churn is a
different problem (duplicate-edit toil from the manual-sync convention,
distinct from drift detection); see the "Validator drift-check for synced
skill references" entry above for the current state of that thread (its
own trigger also has not fired — an initial claim of observed drift
between these two files did not hold up to scrutiny). Continue to defer
this entry until an agent's own idiom is what's driving a change.

The full design space for this thread — general-only vs additive per-agent
guidance vs subtractive targeted template vs de-duplication — is now
captured in
`project/design/proposals/proposed/agent-targeted-review-response-templates/00_proposal.md`
(recommended direction: defer building; when triggered, prefer additive
guidance validated by dogfooding). That proposal is the resolution path for
this entry; this backlog line remains as the lightweight open-thread
pointer and its revisit trigger.

**Related:**
`project/design/proposals/proposed/agent-targeted-review-response-templates/00_proposal.md`;
`src/lrh/assist/templates/request/review_response.md`;
`src/lrh/assist/templates/request/review_protocol.md`;
`src/lrh/assist/request_cli.py` (`--target-agent`);
`src/lrh/assist/request_service.py` (`REQUEST_TARGET_AGENT`);
"Validator drift-check for synced skill references" entry above.
