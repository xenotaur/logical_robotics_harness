# Design Backlog

Lightweight list of deferred ideas that are not yet ready for a formal
proposal or work item. Each entry should record what was noted, why it was
deferred, and where it came from so a future reader can act on it without
re-deriving context.

---

## Generalize conversation export manifests beyond Codex before `/lrh-export`

**Noted:** 2026-08-07, while reviewing Antigravity's draft conversation
exporter plan in PR #514 after landing the Codex app-server export design in
PR #510. The Antigravity plan correctly wants exported artifacts to identify
`source_tool: antigravity`, but LRH's current
`ConversationExportManifest` implementation is still Codex-specific: the module
describes private Codex exports, sets `KIND =
"lrh_codex_conversation_export"` and `SOURCE_TOOL_CODEX = "codex"`, and
validates `source_tool` as exactly Codex. That is fine for
`WI-CODEX-CONVERSATION-EXPORT-APP-SERVER`, whose immediate acceptance criteria
remain Codex-specific, but it becomes a design blocker for non-Codex exporters
and the later target-aware `/lrh-export` wrapper.

**Idea:** Add a follow-on design/work item after the Codex app-server exporter
lands and dogfoods: generalize the conversation export manifest and inspector
contract for multiple source tools. Decide whether the manifest `kind` stays
backward-compatible, becomes a more general `lrh_conversation_export`, or uses
schema-versioned compatibility rules. The resulting contract should support
`source_tool` values such as `codex`, `antigravity`, and future agent targets
without weakening the existing private-by-default,
`authority: non_authoritative_context`, sensitivity-scan, source-hash,
metadata-only inspection, and archive-viewer safety boundaries.

**Status:** Tracked, not yet designed. Do not block the Codex-specific
`export-codex-thread` implementation on this, but do not implement umbrella
`/lrh-export` or non-Codex export adapters on top of a Codex-only manifest
contract.

**Related:** PR #510; PR #514; `src/lrh/conversations/export_manifest.py`;
`docs/reference/cli/conversation.md`;
`project/design/proposals/proposed/lrh-codex-app-server-conversation-export/00_proposal.md`;
`project/work_items/resolved/WI-CODEX-CONVERSATION-EXPORT-APP-SERVER.md`.

---

## `lrh request review_response` cannot surface a specific outdated-but-unresolved thread

**Noted:** 2026-08-01, during PR #453's confirm-fixes round (fixing
`/lrh-land` Step 4's loop-exit condition). Codex flagged (P2, thread
`PRRT_kwDOR7l1D86VlgLc`) that the PR's own fix — "loop back to Step 4 for
that thread" when `/lrh-confirm-fixes` surfaces a not-Clear-satisfied
outdated thread — doesn't actually work mechanically: Step 4 drives
through `lrh request review_response`, whose unresolved filter excludes
outdated threads (`src/lrh/integrations/github/formatters.py:31-40`,
`_matches_state`'s default branch requires `not is_resolved and not
is_outdated`). Re-invoking that command returns the same incomplete list
and cannot progress — the operator has to manually carry the thread's
content from Step 5's classification into the review-response triage
protocol by hand instead of relying on Step 4's automated fetch.

**Idea:** Give `lrh request review_response` a way to include one or more
specific outdated-but-unresolved threads explicitly — e.g. a
`--include-thread <thread-id>` flag, or a mode that accepts the
authoritative thread list — `lrh github threads --state all`, filtered
client-side to `isResolved == false` per `/lrh-confirm-fixes/SKILL.md`
Step 2 (the command itself does not filter) — as input instead of
re-deriving its own narrower list — so `/lrh-land` Step 4 can handle this
case mechanically instead of requiring a documented manual workaround.

**Status:** Closed 2026-08-07. Designed via `/lrh-design` on 2026-08-01
and filed as `PROP-OUTDATED-THREAD-RECOVERY`
(`project/design/proposals/proposed/outdated-thread-recovery/00_proposal.md`),
with two work items: `WI-REVIEW-RESPONSE-INCLUDE-THREAD` (the mechanical
`lrh request review_response` fix, PR #497) and
`WI-LRH-LAND-OUTDATED-THREAD-RECOVERY` (the governed `/lrh-land` Step 4/5
recovery flow, PR #511). Both are now `resolved/`, satisfying this
entry's own close condition. The governed recovery path — precondition
check against the run's stop-work condition, hard bucket-scoping to
Unaddressed/Partial/Problematic resolution, `--include-thread`
propagation into `/lrh-review-response`'s Step 2, and a same-run
continuation carve-out in that skill's Step 3 idempotence check — is
live in `/lrh-land` Step 5 and `/lrh-review-response` Step 3.

An earlier revision of this PR tried to solve the recovery path in prose
instead — a `/lrh-land` Step 5 exception letting the operator fix the
diff by hand and loop back without a hard stop. Seven Codex/Copilot
review rounds against that exception (2026-08-01) each found a genuine,
distinct problem with it, none of them noise:

- It could silently override the human's own Step-2-approved stop-work
  condition for the run (e.g. "any reviewer finding") — a P1 finding,
  since the exception declared itself "not a hard stop" without checking
  what the human had already asked to halt on.
- It lumped Ambiguous and Problematic-comment buckets in with the
  actionable ones, when `/lrh-confirm-fixes` Step 3's own taxonomy
  treats those two as non-actionable and reviewer-comment-may-be-wrong,
  respectively — auto-driving a code change to satisfy either risked an
  unnecessary or harmful edit.
- It didn't allow `/lrh-review-response`'s own feasibility check to
  reject the fix as inappropriate for the change.
- It told the operator to run `/lrh-review-response`'s "full protocol"
  for safeguards (confirm gate, validation, execution record), but that
  protocol's own Step 2 exits immediately on `Nothing to resolve:` for
  exactly this thread class — so following it literally would stop
  before ever reaching the safeguards the exception said to preserve.
- It required carrying `rerun_of` and treating a same-run invocation as
  implicitly pre-authorized against `/lrh-review-response` Step 3's own
  idempotence gate, which the exception's first draft didn't address.

Each fix was individually correct and narrowly scoped, but the pattern —
a mechanism needing a sixth and seventh patch, each surfacing a new edge
case — is itself the signal: this needs a proper design pass (explicit
governance-check ordering, taxonomy scoping, protocol integration) rather
than incremental prose patches under review pressure. The exception was
reverted rather than patched an eighth time; a future implementation of
this idea should design the full recovery path (not just the
`lrh request review_response` fetch gap above) before it reaches
`/lrh-land`'s `SKILL.md` again — ideally via `/lrh-design` given the
number of interacting constraints (stop-work-condition governance,
confirm-fixes' taxonomy, review-response's own gates) a purely prose fix
kept failing to get right in one pass.

**Related:**
`src/lrh/skills/lrh-land/SKILL.md` (Step 4/Step 5);
`src/lrh/skills/lrh-review-response/SKILL.md`;
`src/lrh/skills/lrh-confirm-fixes/SKILL.md` (Step 3 taxonomy, Step 5's
"offer `/lrh-review-response`" note);
`src/lrh/integrations/github/formatters.py` (`_matches_state`);
`src/lrh/assist/request_service.py` (`review_response` template branch);
PR #453 review threads `PRRT_kwDOR7l1D86Vl6Hq` (P1, stop-work condition),
`PRRT_kwDOR7l1D86Vl6Hs` (feasibility rejection), and the suppressed
Copilot comment on `src/lrh/skills/lrh-land/SKILL.md:188` (Step 2
short-circuit).

---

## Idempotence cross-PR discovery doesn't fail closed on fetch errors

**Noted:** 2026-07-30, during PR #441 review (round 6), while hardening
the idempotence-check's cross-PR discovery logic in `lrh-proposal`,
`lrh-work-item`, and `lrh-workstream`.

**Idea:** The cross-PR search's `gh pr list` and `git fetch` calls all
suppress stderr (`2>/dev/null`) and never check exit status. This is
deliberate for the common case — a nonzero exit with no output legitimately
means "no prior record" — but it can't currently distinguish that from a
genuine failure: an auth problem, a network blip, or a missing/unreachable
ref. If `gh pr list` fails outright, the loop silently processes zero PRs
(as if none were open) rather than reporting the failure. If a `git fetch`
into `refs/remotes/pr/<N>` fails (e.g. transient network issue) after a
previous successful fetch already populated that ref, the subsequent
`ls-tree` silently scans the **stale** cached ref instead of the current
PR state — the same kind of staleness the round-2 fix already addressed
for force-pushes, but from a different cause (fetch failure vs. rejected
non-fast-forward). Either failure mode can make the skill wrongly report
"no prior record" (creating a duplicate) or act on outdated information.

**Status:** Deferred — properly fixing this means adding explicit exit-status
checks and distinct error handling to `gh pr list` and each `git fetch` in
the pipeline, then deciding what "abort and report" looks like inside a
pipeline that's currently written as a single composed shell block (not
just one command) — a real design question, not a one-line patch, and this
PR (round 6) already fixed a correctness bug (PR-inheritance false-tagging),
a staleness bug (force-push), and a chronology bug (local-time filenames)
in the same pipeline. Revisit alongside, or as part of, item 4 already
covering incomplete failure semantics in this same discovery logic (see
"Idempotence-check refinements deferred from PR #438" below).

**Related:** harness PR #441 (round 6, Codex);
`src/lrh/skills/lrh-proposal/SKILL.md`,
`src/lrh/skills/lrh-work-item/SKILL.md`,
`src/lrh/skills/lrh-workstream/SKILL.md` (Step 4, cross-PR discovery) and
their `references/execution-record.md` mirrors.

---

## Execution-record filename timestamps use local time, not UTC

**Noted:** 2026-07-30, during PR #441 review (round 5), while fixing the
idempotence-check's cross-PR/rerun-detection logic in `lrh-proposal`,
`lrh-work-item`, and `lrh-workstream`.

**Idea:** `src/lrh/prompt_workflow.py:299` generates the timestamp prefix
used in execution-record filenames (and in minted `PROMPT(...)[<timestamp>]`
IDs) via `datetime.datetime.now(datetime.timezone.utc).astimezone()` —
this converts to the **local system timezone** before formatting with
`strftime`. Two machines (or one machine across a DST change) in
different UTC offsets can therefore produce filenames whose lexicographic
order does not match true chronological order: a record created at local
`09:00-04:00` (`13:00 UTC`) sorts *before* one created at local
`12:00+00:00` (`12:00 UTC`), even though the first is chronologically
later. Every place in this codebase that relies on "sort filenames, take
the last line, that's the most recent record" (PR #438's and PR #441's
idempotence checks in `lrh-proposal`/`lrh-work-item`/`lrh-workstream`/
`lrh-review-response`, at minimum) inherits this gap.

PR #441 worked around this locally by reading each surviving match's
`created_at:` frontmatter field and comparing actual timestamps instead
of trusting filename order, rather than fixing the root cause. The root
fix is in `src/lrh/prompt_workflow.py`: generate the timestamp prefix from
UTC (`datetime.datetime.now(datetime.timezone.utc)`, no `.astimezone()`)
instead of local time, so filenames — and therefore simple lexicographic
sort — are chronologically correct again everywhere they're relied on.

**Status:** Deferred — this is real Python source code in the CLI
(`lrh prompt label` / `record-execution`), not skill documentation, with
its own test suite and behavior-change implications (existing execution
records already carry local-time-based filenames and IDs; a UTC change
would only affect newly-created ones, but worth confirming no code
assumes the two are always in the same timezone). Out of scope for a
skills-only follow-up PR. Revisit as its own work item.

**Related:** `src/lrh/prompt_workflow.py:299` (and `:64`, the
`timestamp_for_file` sibling); harness PR #441 (round 5, Codex);
`src/lrh/skills/lrh-proposal/SKILL.md`,
`src/lrh/skills/lrh-work-item/SKILL.md`,
`src/lrh/skills/lrh-workstream/SKILL.md`,
`src/lrh/skills/lrh-review-response/SKILL.md` (all rely on filename order
for "most recent match" selection; PR #441 patched the `created_at`
comparison locally in the first three but the root cause remains).

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

5. **`lrh-review-response` and `lrh-confirm-fixes` predate the invariant
   and don't meet it (Codex, PR #440 review).** Both use the same idea
   (filename-slug search before minting, to catch a rerun `check-execution`
   alone can't) with the same earlier, less complete glob: a broader
   substring match (`find ... -name "*<UPPER_SLUG>*.md"`) instead of the
   trailing-segment anchor `DEC-PRE-MINT-SLUG-IDEMPOTENCE-DEFAULT` makes
   authoritative. `src/lrh/skills/lrh-review-response/SKILL.md:122-131` additionally has
   no per-match `status:` inspection before blocking — it stops on *any*
   match unconditionally, including `failed`/`reverted`/`superseded` ones
   that shouldn't block; `lrh-confirm-fixes/SKILL.md:180-181`'s
   status-handling deviation itself is fine and deliberate (Decision 12 —
   see the decision record), only its glob needs anchoring. Bring both up
   to the invariant: anchor the glob in each; add the status-handling
   branch to `lrh-review-response` (matching
   `lrh-proposal`/`lrh-work-item`/`lrh-workstream`, not `lrh-confirm-fixes`'s
   deliberately different warning-only behavior); and (once item 1 is
   resolved) the same `rerun_of` precedence logic where applicable.

**Status:** Resolved — 2026-07-30, all five items fixed in the follow-up
PR this entry called for. Items 1–4 resolved together in `lrh-proposal`,
`lrh-work-item`, and `lrh-workstream`: replaced the two-bucket
blocking-vs-non-blocking logic with a single most-recent-by-timestamp
match selection (resolves item 1's precedence question and removes the
need to ask the user to disambiguate multiple matches); added `| sort` to
every glob plus an explicit note that a nonzero exit with no output means
no prior record (item 2); added a branch-existence check + reuse at
branch-creation time for explicit reruns (item 3); added a second search
over open PRs' remote branches alongside the current-checkout `find`
(item 4). Item 5: anchored the glob in both `lrh-review-response` and
`lrh-confirm-fixes`; added the missing per-match status-handling branch to
`lrh-review-response` (it previously blocked on any match
unconditionally); left `lrh-confirm-fixes`'s status-handling untouched
(Decision 12 — correct and deliberate, only its glob needed anchoring).
Neither skill needed items 3/4's branch-reuse or cross-PR search — both
operate on an already-checked-out PR branch rather than creating a new
one.

**Noticed but not fixed:** `lrh-review-response/SKILL.md` Step 7 has a
separate unanchored substring `find` used for `rerun_of` *attribution*
(finding the primary record to link back to) — a different search than
the Step 3 idempotence check this entry covers, lower risk
(misattribution, not a false block), and not part of this entry's
original five items. Flagged in the resolving PR's execution record
rather than fixed inline.

**Related:** harness PR #438 (rounds 4, 6, and 7); harness PR #440 (item 5);
`src/lrh/skills/lrh-proposal/SKILL.md`,
`src/lrh/skills/lrh-work-item/SKILL.md`,
`src/lrh/skills/lrh-workstream/SKILL.md` (Step 4, idempotence check) and
their `references/execution-record.md` mirrors;
`src/lrh/skills/lrh-review-response/SKILL.md` Step 3 and
`src/lrh/skills/lrh-confirm-fixes/SKILL.md` Step 3 (item 5's targets);
"Filename-slug idempotence search drives blocking, contrary to
`PROMPTS.md`" entry below.

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

**Status:** Resolved — 2026-07-30, promoted to
`DEC-PRE-MINT-SLUG-IDEMPOTENCE-DEFAULT`
(`project/memory/decisions/DEC-PRE-MINT-SLUG-IDEMPOTENCE-DEFAULT.md`).
Revisited three options: (1) codify the exception in `PROMPTS.md` — the
exact-ID lookup mechanism genuinely cannot answer "has this slug run
before" since no ID exists yet to look up, so filename-slug search isn't
the same kind of thing as the fuzzy/heuristic discovery the original rule
was warning about; (2) make slug discovery non-blocking everywhere,
literally complying with the old wording, at the cost of turning every
rerun path interactive; (3) build a real CLI mechanism (e.g.
`check-execution --slug`) so slug-based duplicate detection becomes
genuinely authoritative tooling, not a hand-rolled `find` in prose —
touches the CLI, its tests, `PROMPTS.md`, and all 4 skills.

Went with **option 1**, but not as a single pass: an initial attempt to
write one universal status-handling matrix into `PROMPTS.md` was refined
across several PR #440 review rounds (undefined placeholder, substring
false positive, missing-directory error, status-blind blocking, missing
`rerun_of` propagation, ambiguous-match handling, a missed third copy of
the rule in `project/executions/README.md`) until review surfaced two
*structural* gaps rather than typos: `lrh-confirm-fixes` already
documents a deliberate deviation from this exact pattern (Decision 12 —
prior `_CONFIRM` records are warning-only, never blocking, since live
review-thread state changes between rounds), which the universal matrix
contradicted; and the `planned` status exists but fits none of the
matrix's buckets. Rather than keep expanding the matrix, `PROMPTS.md` now
states only an **invariant** (filename-slug-by-bucket search, matched to
the complete trailing segment, is authoritative for this narrow question)
and a **default** (explicitly labeled as such, not a mandate) — a skill
that deviates, or hits a status the default doesn't cover, documents its
own reason locally, the way `lrh-confirm-fixes` already does. Full
rationale, alternatives, and consequences are in the promoted decision
record, not restated here or in `PROMPTS.md` itself. No skill code
changed — `lrh-proposal`/`lrh-work-item`/`lrh-workstream` follow the
default, `lrh-confirm-fixes` deviates deliberately and needs no change,
`lrh-review-response` predates the default and is tracked as item 5 in
the "Idempotence-check refinements deferred from PR #438" entry above.

**Not done — revisit if this resurfaces:** option 3 (real CLI tooling for
slug-based duplicate detection) remains the more complete long-term fix.
See the decision record's "Revisit conditions" for the specific triggers.

**Related:** `PROMPTS.md` "Soft idempotence before execution" section
(now includes the "Pre-mint duplicate detection by slug" subsection);
`project/memory/decisions/DEC-PRE-MINT-SLUG-IDEMPOTENCE-DEFAULT.md`;
`src/lrh/skills/lrh-review-response/SKILL.md` Step 3;
`src/lrh/skills/lrh-confirm-fixes/SKILL.md` Step 3 (Decision 12);
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

**Status:** Trigger fired, user wants to build it — not yet scoped. This
entry's own revisit trigger fired without anyone circling back: written
2026-07-05 when only one promoted decision file existed
(`project/memory/decisions/precedence_semantics.md`); two more were
promoted since without this entry being updated —
`project/memory/decisions/DEC-DELIBERATE-CHAIN-INITIATION.md` (2026-07-24)
and `project/memory/decisions/DEC-PRE-MINT-SLUG-IDEMPOTENCE-DEFAULT.md`
(2026-07-30, this entry's own author noticing the staleness while
cross-linking). That's three real, hand-written instances of the
promotion pattern now — the "single instance proves nothing" objection no
longer holds. 2026-07-30: confirmed with the user that `/lrh-decision` is
wanted; not yet scoped or built. Next step when picked up: derive the
interview questions and body-section shape from the three existing
promoted files' actual structure (they don't all use identical section
names — compare `Context`/`Options considered`/`Decision`/`Rationale`/
`Alternatives considered`/`Consequences`/`Revisit conditions` across all
three before finalizing a template), following the same pattern
`/lrh-work-item` and `/lrh-proposal` already establish for interview-driven
planning-artifact skills.

**Related:** `project/work_items/resolved/WI-DECISION-RECORD-CONVENTIONS.md`
Non-Goals; `project/design/design.md` §14 "Decision-record tiers";
`project/memory/decisions/precedence_semantics.md`,
`project/memory/decisions/DEC-DELIBERATE-CHAIN-INITIATION.md`,
`project/memory/decisions/DEC-PRE-MINT-SLUG-IDEMPOTENCE-DEFAULT.md`.

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

---

## `WorkItem.blocked`/`blocked_reason` not populated by every builder

**Noted:** 2026-08-01, Copilot review (suppressed comment) on PR #455,
which added typed `blocked: bool` / `blocked_reason: str | None` fields to
`control_models.WorkItem` and wired them through `control/loader.py`'s
`_load_work_items()` so `core_state.py`'s `WorkItemState` and `serve.py`'s
blocked-count logic stop dropping the frontmatter fields.

**Idea:** Two other `WorkItem` builders were not updated to set these
fields, so instances they construct keep the `blocked: bool = False` /
`blocked_reason: str | None = None` defaults regardless of the source
frontmatter: `src/lrh/control/validator.py`'s
`_work_item_model_from_artifact()` and `src/lrh/assist/snapshot_cli.py`'s
`_load_snapshot_work_items()`. This is a real typed-model consistency gap
— a future reader could reasonably assume every `WorkItem` instance
reflects its frontmatter's `blocked` state.

**Status:** Deferred — traced both current consumers and neither is
actually broken by the gap. `validator.py`'s typed `WorkItem` here only
feeds `build_planning_tree_from_artifacts()` for parent/child/cycle
diagnostics; that function recomputes `blocked`/`blocked_reason` on its
own `PlanningArtifact` output directly from `artifact.frontmatter`
(`src/lrh/control/planning_tree.py:256-257`), not from `WorkItem.blocked`.
`snapshot_cli.py`'s readiness-hint feature (`_active_leaf_readiness_hint`,
line 329) reads `PlanningArtifact.blocked`, the same frontmatter-derived
value — also unaffected. Revisit if a future consumer starts reading
`.blocked`/`.blocked_reason` directly off either builder's `WorkItem`
output rather than through `PlanningArtifact`.

**Related:** harness PR #455 (Copilot review, suppressed comment);
`src/lrh/control/models.py` (`WorkItem.blocked`/`blocked_reason`);
`src/lrh/control/loader.py` (`_load_work_items`);
`src/lrh/control/validator.py` (`_work_item_model_from_artifact`);
`src/lrh/assist/snapshot_cli.py` (`_load_snapshot_work_items`);
`src/lrh/control/planning_tree.py` (`build_planning_tree_from_artifacts`).

---

## Promote stalled-reviewer-session detection from skill prose to a tested LRH primitive

**Noted:** 2026-07-31, while adding stalled-reviewer-session detection
(check-run + issue-timeline heuristic, for distinguishing "reviewer never
invoked" from "reviewer's own session started and stalled," e.g. GitHub
Copilot code review running out of included credits) to
`lrh-confirm-fixes/SKILL.md` Step 8.3 and
`references/round-cap-gate.md`.

**Idea:** The detection landed as skill-embedded bash/`gh api` prose,
callable only from inside an already-running `/lrh-confirm-fixes`
invocation that is actively waiting on a reviewer — it cannot fire
proactively (e.g. overnight, with no session open). `round-cap-gate.md`'s
own "Risk Notes — deferred hardening" section already documents that this
skill-prose approach is expensive to get right and hard to verify: the
round-cap mechanism it lives alongside took 8 review rounds to reach its
current state, each round finding a genuinely different category of
correctness bug, and remains untested in practice.
`WI-BOUNDED-STABILIZATION-LOOP-DESIGN.md`'s Risk Notes independently
recommend promoting this class of logic to "a shared, unit-tested LRH
primitive (real code, not skill prose)" that both an assisted mode (a
human-driven skill invocation) and a future bounded-auto mode (e.g. a
scheduled poller) could call, rather than duplicating hand-rolled
`gh api`/`jq` logic at each call site. A real primitive (e.g. `lrh
pr-health check`) would also get `scripts/test` unit coverage, unlike the
current prose, which is verified only by manual reasoning.

**Status:** Obsolete — `WI-RETRIGGER-REMOVAL-STAGE1` removes the hosted
reviewer retrigger path and the skill-prose stalled-reviewer-session
diagnostic this entry targeted. The replacement path uses a synchronous
fresh self-review subagent plus a provisional no-progress cap, so the old
GitHub check-run/timeline heuristic no longer has an active call site. A
dispatched subagent can also stall, but that would need a separate
subagent-lifecycle heuristic rather than promotion of the retired hosted
reviewer detector.

**Cross-reference (2026-08-01):** This entry's own landing PR (#452) is
cited as supporting evidence for the self-review-first tier problem —
now promoted to its own dedicated entry, "Self-review-first tier for
reducing GitHub bot-review credit consumption" below, since it outgrew a
cross-reference paragraph here. Not itself a reason to revisit this
entry's own status above — orthogonal concern (this entry is about
promoting *this* heuristic to tested code; the cross-referenced entry is
about the review-credit model generally).

**Related:** `src/lrh/skills/lrh-confirm-fixes/SKILL.md` Step 8.3;
`src/lrh/skills/lrh-confirm-fixes/references/round-cap-gate.md`
"Detecting a stalled reviewer session" and "Risk Notes — deferred
hardening"; `project/work_items/proposed/WI-BOUNDED-STABILIZATION-LOOP-DESIGN.md`;
harness PR #452 (execution records) and PR #453 (the proposal's original
motivating example).

---

## Stalled-reviewer-session detection is Copilot-specific but reads as reviewer-generic

**Noted:** 2026-08-01, during PR #452 review round 7 (Copilot,
`copilot-pull-request-reviewer`), landing the stalled-reviewer-session
detection heuristic in `lrh-confirm-fixes/SKILL.md` Step 8.3 and
`references/round-cap-gate.md`.

**Idea — two remaining items, deferred by explicit decision rather than
fixed inline to stop an 8-round retrigger loop (rounds 1–7 each found a
real, distinct, low-risk issue: a cross-product timeline-correlation bug,
three wording/grammar fixes, a stale cross-reference direction, an
unpaginated `gh api` call, a `gh --jq`-runs-per-page-not-merged
correctness bug, and a misleading null-object edge case — see this PR's
`_CONFIRM` execution record for the full round-by-round account):**

1. **Reviewer-generic framing, Copilot-specific signals.** `SKILL.md`
   Step 8.3 says "first check whether that reviewer's own session
   actually started and stalled" for *any* retriggered reviewer that
   hasn't responded, but the only heuristic this cross-references
   (`round-cap-gate.md`'s "Detecting a stalled reviewer session") is
   built entirely from Copilot-specific signals: the
   `copilot-pull-request-reviewer` check-run name and `copilot_work_*`
   timeline events. Codex (comment-driven, no equivalent check-run or
   timeline signal) would just get an empty result and correctly fall
   through to the "No stall detected" question — not a correctness bug,
   since the fallback is safe, but the prose doesn't make that scope
   explicit, and a future reviewer added to `REVIEWS.md` might wrongly
   assume this heuristic applies to them too.
2. **`backlog.md`'s own entry above quotes stale wording.** The
   "Promote stalled-reviewer-session detection..." entry's **Noted**
   section quotes "reviewer never invoked" — the phrasing this same PR's
   round 3 replaced with "no evidence the reviewer was invoked this
   round" specifically to avoid implying the heuristic can determine
   configuration state. Purely a documentation-consistency echo, not a
   behavioral issue.

**Status:** Obsolete — `WI-RETRIGGER-REMOVAL-STAGE1` removes the hosted
reviewer retrigger path and the stalled-reviewer-session diagnostic this
entry wanted to clarify. The remaining Step 8 path no longer tries to
distinguish Copilot-specific hosted-reviewer stalls from absent reviewer
responses; it waits for any automatic response already in flight, then uses
a fresh self-review substitute subject to the provisional no-progress cap.
A dispatched subagent can also stall, but that is a new subagent-lifecycle
problem rather than a reason to preserve this Copilot-specific wording fix.

**Related:** `src/lrh/skills/lrh-confirm-fixes/SKILL.md` Step 8.3;
`src/lrh/skills/lrh-confirm-fixes/references/round-cap-gate.md`
"Detecting a stalled reviewer session"; harness PR #452 (rounds 1–7);
"Promote stalled-reviewer-session detection..." entry above.

---

## `/lrh-implement` Step 9 never populates the execution record's `pr:` field

**Noted:** 2026-08-02, during PR #459's automatic on-open review (Codex,
P1), while implementing `/lrh-execute` (`WI-SKILLS-LRH-EXECUTE`) by
inlining `/lrh-implement`'s own procedure to bootstrap it.

**Idea:** `src/lrh/skills/lrh-implement/SKILL.md` Step 9 creates the
execution record via `lrh prompt record-execution` and its own
"immediately edit" instruction populates `agent`, `instruction_source`,
and `session_transcript` — but never `pr:`, even though Step 8 (which
runs first) already opened the PR, so the URL is available. `lrh prompt
record-execution` already supports `--pr <url>` (confirmed: `lrh prompt
record-execution --help` lists it) — this is a missing instruction, not a
missing CLI capability.

The consequence is structural, not cosmetic: `/lrh-land`'s Step 1
primary-record selection searches `project/executions/` for a record
whose `pr:` field matches the target PR URL. A record created by
`/lrh-implement` Step 9 with `pr:` blank is invisible to that search —
`/lrh-land` falls back to an `AD_HOC` backfill record, and closeout's
own found-or-backfill matrix does not resolve a WI for the `AD_HOC`
bucket. Any chain that inlines `/lrh-implement` then `/lrh-land` in
sequence (exactly what `/lrh-execute` does) can therefore merge the PR
while leaving the target work item silently stuck `proposed` and its
real execution record silently stuck `in_progress` — the opposite of
what an "implement and land it end-to-end" skill advertises.

**Status:** Worked around locally, not fixed at the root. `/lrh-execute`'s
own Step 3 (`src/lrh/skills/lrh-execute/SKILL.md`) now explicitly
instructs populating `pr:` via `--pr` before proceeding to Step 4 — a
defensive fix scoped to `/lrh-execute`'s own correctness, since
`WI-SKILLS-LRH-EXECUTE`'s Non-Goals don't cover modifying
`/lrh-implement` itself. The root gap remains open for every *other*
`/lrh-implement` caller (a human running `/lrh-implement` directly, then
`/lrh-land` manually) — same failure mode, just with more time for a
human to notice between the two steps rather than none. Fix: add `--pr
<pr-url-from-step-8>` to Step 9's own `record-execution` call in
`/lrh-implement/SKILL.md` (and its `.claude/` mirror) directly.

**Related:** `src/lrh/skills/lrh-implement/SKILL.md` Step 8–9;
`src/lrh/skills/lrh-land/SKILL.md` Step 1 (primary-record selection) and
`references/land-workflow.md` (found-or-backfill matrix); `src/lrh/skills/lrh-execute/SKILL.md`
Step 3 (the defensive workaround); harness PR #459.

---

## `/lrh-closeout` never refreshes a skill-touching PR's global install — deferred pending more real-world usage

**Noted:** 2026-08-01, closing out `WI-CLOSEOUT-SKILLS-INSTALL-SYNC`.
`~/.claude/skills/<name>` silently drifts from the canonical
`src/lrh/skills/<name>` source after a PR edits an existing skill,
because nothing in the LRH workflow ever re-runs an install after merge
(root-caused live during a `/lrh-land` run on PR #452, where
`lrh-confirm-fixes`'s installed copy was missing an entire mechanism a
prior PR had added).

**Idea:** PR #454 filed the WI; PR #456 attempted a full implementation —
a new `/lrh-closeout` step detecting a skill-touching merge and
force-refreshing exactly the touched skill names, bypassing the ordinary
`USER_MODIFIED` safety check for those names only. That design required
proving a live, mutable local git checkout matches a specific verified
commit before trusting a live filesystem read
(`PYTHONPATH`/`importlib.resources`), and went through 14 review rounds,
each finding a further real gap in that proof (repo/branch/identity
scoping, base-SHA sourcing, shallow-clone object availability, ancestry
vs. exact tree-hash, working-tree dirtiness, `.gitignore`d files,
per-skill vs. package-root scoping, verifying the installer code's own
state). A fresh-context go/no-go self-review concluded the mechanism was
architecturally unsound — disproportionate complexity for the problem,
symptomatic of the wrong foundational choice (live filesystem read
instead of a git-object-database read pinned to a verified SHA), and
still had an open TOCTOU gap between the confirm gate and execution. The
`/lrh-closeout` wiring was reverted; only the underlying primitive,
`install_named_skills()` in `src/lrh/skills/installer.py`, shipped (not
wired into any CLI command or caller).

**Status:** Deferred, not merely to a narrower follow-up PR. Explicit
user judgment: this problem currently has one real user/repo, and a
more robust design (e.g. a small tested CLI command reading from git's
object database at a SHA pinned once at a confirm gate, rather than
agent-followed prose re-establishing checkout trust from scratch every
invocation — sketched in the self-review, recorded in PR #456's
description and in `WI-CLOSEOUT-SKILLS-INSTALL-SYNC`'s "Outcome"
section) would be overfitting to that single use case before there's
enough real-world usage across more users/repos to inform the right
trade-offs (how often skills actually change, how tolerant users are of
a manual `lrh skills install`, whether the CLI-command shape holds up).
Revisit once there's a broader user base to design against, not on a
fixed timeline.

**Related:** `WI-CLOSEOUT-SKILLS-INSTALL-SYNC` (resolved as
partial/pivoted, in `project/work_items/resolved/`); PR #454 (WI
creation); PR #456 (attempted implementation + revert); memory
`project_live_checkout_verification_smell.md` and
`feedback_review_pattern_over_round_count.md`.

---

## Self-review-first tier for reducing GitHub bot-review credit consumption

**Noted:** 2026-08-01 (raised in another session, motivated by PR #453's
9 retrigger batches); promoted from a cross-reference paragraph to its
own entry 2026-08-02 while auditing outstanding review-credit work, as
the first consolidation of what was known ahead of a formal proposal.

**Idea:** Every external bot-review retrigger (GitHub Copilot, Codex)
draws on a metered, billable AI-credit resource — not merely session
time. The `round-cap-gate.md` mechanism (`WI-REVIEW-ROUND-ESCALATION-GATE`,
PR #445/#452) bounds *how many* retriggers happen and requires live
human reauthorization past a ceiling, but does not reduce *how often a
retrigger is actually necessary* in the first place. A self-review-first
tier would insert an independent, cold-context subagent review pass
before some or all bot retriggers, on the theory that (a) it costs
session compute/agent-turns but not the metered bot-credit resource, and
(b) it can catch a category of bug bot review keeps missing.

**Evidence for the idea**, all real, in-repo, cited data points (not
speculative):

- **PR #452** (this session, `round-cap-gate.md` implementation): the
  round-cap-gate.md state ledger
  (`project/executions/round_state/xenotaur-logical_robotics_harness-pr452.json`
  on the `lrh-round-state` branch) shows `completed_count: 10, ceiling:
  10` — 10 completed bot-retrigger batches, ceiling escalated 3→10 via
  human reauthorization. After exhausting the authorized ceiling, the
  session substituted 3 independent cold-subagent review passes for
  further bot retriggers instead of asking for a further escalation. Only
  the *first* pass found a bug bot review had genuinely missed across its
  prior rounds — a harness-level discovery that shell variables don't
  survive across separate tool calls, which "no bot-review round had
  caught in 8 prior rounds" per the landed CHAIN-NOTE
  (`project/executions/AD_HOC/2026_08_01_01_07_05_COPILOT_STALLED_SESSION_DETECTION_CONFIRM.md`).
  The second and third passes instead found regressions introduced by
  that first pass's own fix (two opposite-direction mirror-image bugs in
  the same retrigger-timestamp-filtering mechanism) — not bugs bots had
  independently missed, but exactly the class of self-inflicted-regression
  issue a *pre-push* self-review pass (not just a post-ceiling substitute)
  could plausibly catch for free, before it ever reaches a bot and costs
  a retrigger.
- **PR #447** (`WI-REVIEW-LANDED-CANONICAL-CHECK` creation, 2026-07-31 to
  08-01): the earliest live trial of the substitution pattern. Round 4 of
  a 4-cycle review-response/confirm-fixes loop swapped a fresh
  independent subagent for external bot retrigger (human-directed) and
  caught 2 more real issues, including one that 3 prior rounds of Codex
  review had missed. This substitution *replaced* the PR's eventual bot
  round entirely — verified: every recorded bot review on this PR
  predates the round-4 fix commit by nearly a day, and none reviewed it
  or anything after it before merge. (The same pattern holds for PR #452
  and #459 too, on independent verification — see Open Question 4.) See
  `project/executions/AD_HOC/2026_08_02_00_00_29_WI_REVIEW_LANDED_CANONICAL_CHECK_CLOSEOUT_NOTE.md`
  for the full CHAIN-NOTE.
- **PR #453**: 9 retrigger batches in one landing session — the original
  motivating example for this idea in the other session that raised it.
  Cited as evidence of the *problem* (excessive bot-retrigger volume),
  not as a mechanism trial — no subagent-substitution pass is recorded in
  this PR's execution records.
- **PR #459** (`WI-SKILLS-LRH-EXECUTE`, this session, 2026-08-02): given
  an explicit instruction to prefer independent subagent review over bot
  retrigger throughout, 3 sequential cold-subagent review rounds
  surfaced 6 distinct real issues in total (path portability, a missing
  `pr:` field propagation, an unreachable journal path, an unfiltered
  status grep, an unresolved placeholder, a missing `depends_on` lookup
  mechanism) rather than narrowing into refinement noise on the same
  issue — the pattern this project already treats as the signal that
  continued review is finding real bugs, not diminishing returns (see
  `feedback_review_pattern_over_round_count` in agent memory).
- **PR #469** (`PROP-LRH-CODEX-CONVERSATION-EXPORTER`, this session,
  2026-08-02): the user explicitly clarified during `/lrh-land` that the
  current standard is no manual paid GitHub reviewer retriggers beyond the
  automatic review on initial PR push; post-fix confirmation should use
  "self-review with a fresh independent sub-agent" instead. This exposed a
  workflow mismatch in `/lrh-land` and `/lrh-confirm-fixes`, whose current
  Step 8 prose still assumes external reviewer retrigger side effects,
  round-cap state, and possible Copilot credit exhaustion after `_CONFIRM`
  commits.

**Open design questions**, as originally posed when this was only a
backlog entry — see **Status** below for which of these `PROP-LRH-SELF-REVIEW`
went on to decide, and which (question 4 specifically) it left open:

1. **Trigger point.** Does self-review run only as a post-ceiling
   substitute for a bot retrigger (the ad hoc pattern used in PR #452),
   or proactively before every push (which is what would actually catch
   the "self-inflicted regression from my own prior-round fix" class of
   bug, per PR #452's second data point above)? These have different
   costs and different mechanisms.
2. **Interaction with `round-cap-gate.md`.** Does a self-review pass
   count against the existing retrigger ceiling, run outside it
   entirely, or replace a fixed fraction of ceiling slots? The gate's
   state machine (`src/lrh/skills/lrh-confirm-fixes/references/round-cap-gate.md`)
   was not designed with a second review-source type in mind.
3. **What resource is actually being conserved.** GitHub Copilot/Codex
   AI-credits are a real, metered, billable resource; subagent review
   passes cost session compute/agent-turns instead — not free, just a
   different resource. Any proposal should be explicit that this is a
   resource *substitution*, not a cost elimination, and should say
   whether the substitution is actually cheaper in the cases that matter.
4. **Who decides "clean enough to skip a bot round."** All three
   mechanism-trial cases (PR #447, #452, #459 — PR #453 is problem
   evidence only, not a mechanism trial, see above) show the same
   pattern on independent verification: once the session substituted
   self-review for a bot round, no bot reviewed any of the PR's
   subsequent commits, including the one that actually merged. PR #452's
   own CHAIN-NOTE frames this as a deliberate choice ("...plus 3
   independent cold-subagent review passes after the ceiling was reached
   instead of further bot rounds"); PR #447 and #459 show the identical
   outcome with no equivalent explicit up-front decision on record — it
   emerged operationally, because nobody retriggered a bot after the
   substitution. So in practice, self-review substitution has already
   ended up skipping the PR's final bot round in all 3 real trials to
   date — just not always as a named, deliberate policy decided in
   advance. Whether that's safe as a *designed* behavior (rather than an
   emergent side effect of nobody asking for one more bot round), and
   what evidence would justify formalizing it, is undesigned.
5. **Scope of "self-review."** All three mechanism-trial data points
   above (PR #447, #452, #459) used the same mechanism — a fresh `Agent`
   tool call with `subagent_type: general-purpose`, given the PR URL and
   told not to trust prior summaries. Whether that ad hoc pattern should
   become the designed mechanism, or whether a tighter-scoped review
   agent/prompt would do better, is unexplored.

**Status:** Resolved — 2026-08-02, filed as `PROP-LRH-SELF-REVIEW`
(`project/design/proposals/adopted/lrh-self-review/00_proposal.md`,
adopted) and implemented the same day as `/lrh-self-review`
(`WI-SKILLS-LRH-SELF-REVIEW`, resolved, PR #467). The proposal's
Decisions 1-6 resolve open questions 1 and 2 above (two trigger points —
pre-push diff-mode and post-ceiling PR-mode substitute; `round-cap-gate.md`
interaction — substituted rounds count identically); open question 3
(resource substitution, not elimination) is Decision 3's explicit
framing. **Open question 4 remains genuinely open, not resolved** —
Decision 4's title is specifically "Never skip a PR's **first** real bot
round" and its own text defers "a broader design-space pass on
later-round skip policy" as explicit future work, tracked in the
proposal's own Open Questions ("trust-scored skip policies for later
rounds"). Backlog question 4 asks about the *final*-round case
specifically (is it safe that self-review substitution has, in practice,
ended up skipping the last bot round before merge in all 3 trial PRs) —
a narrower, harder question Decision 4 explicitly did not decide. Open
question 5 (a
tighter-scoped review agent vs. the ad hoc pattern) was not decided
either way — the ad hoc `Agent`-tool pattern from the evidence PRs became
the shipped mechanism by default, not by an explicit comparison. One gap
remains: Decision 7's named governance
workstream, `WS-SKILLS-SELF-REVIEW`, was never created — the
implementing WI deferred it as a follow-on rather than building it
(see the WI's own Non-Goals); `PROP-LRH-SELF-REVIEW`'s
`implementation_status` is therefore `partial`, not `implemented`.

**Related:** `src/lrh/skills/lrh-confirm-fixes/references/round-cap-gate.md`;
`project/work_items/resolved/WI-REVIEW-ROUND-ESCALATION-GATE.md`; harness
PR #445, #447, #452, #453, #459; agent memory
`feedback_round_cap_self_review_alternative.md`,
`feedback_self_review_agent_first_trial.md`,
`feedback_review_pattern_over_round_count.md`; the "Promote
stalled-reviewer-session detection..." entry above (orthogonal —
tested-primitive promotion vs. review-credit-model design).

---

## Codex skill adaptation gaps encountered while creating PROP-LRH-CODEX-CONVERSATION-EXPORTER

**Noted:** 2026-08-02, while creating
`project/design/proposals/proposed/lrh-codex-conversation-exporter/`
from a Codex app session using the authoritative
`src/lrh/skills/lrh-proposal/SKILL.md` source.

The run confirmed several places where current LRH skills or skill-adjacent
workflow prose still assume Claude.app capabilities, installation paths, or
session identifiers that do not map cleanly to Codex:

1. **Missing `.agents/skills` installation path.** Codex did not have an
   `~/.agents/skills/` or project `.agents/skills/` directory available in this
   worktree. The session used the authoritative repo copy at
   `src/lrh/skills/lrh-proposal/SKILL.md` directly. Codex can follow the skill
   manually, but slash-command discovery and installation are not yet
   first-class.
2. **Claude-specific execution-record defaults.** `lrh-proposal`'s
   execution-record reference still shows `agent: claude_app` and final
   reporting text assumes `session_transcript` will later become
   `claude-app:<host-uuid-stem>`. Codex sessions need a Codex-specific
   convention, likely `agent: codex_app` or another open-ended value, and a
   `codex-app:<id>` / `pending` / `none` transcript resolution path.
3. **Claude-specific skill availability checks.** `lrh-proposal` Step 11 checks
   whether `/lrh-workstream` is listed in `CLAUDE.md ## Skills`. Codex needs an
   equivalent target-aware skill availability check that can inspect
   Codex-discoverable skills or fall back to authoritative repo skill sources.
4. **Network assumptions in idempotence checks.** The proposal skill's cross-PR
   idempotence check assumes GitHub network access is available. In Codex's
   restricted sandbox, `gh pr list` failed until the session requested
   escalation. Codex-friendly skills should explicitly describe
   sandbox/network escalation behavior and graceful local-only fallback
   semantics.
5. **Environment preflight surfaced missing Pyright.** `scripts/version tools`
   reported `Pyright not installed`. This is likely environment setup/cache
   state rather than a proposal design issue, but Codex-facing workflows should
   preserve the repo guidance that tool-version mismatches are setup issues to
   reconcile before validation-focused debugging.
6. **Claude-specific closeout memory reflection.** `/lrh-closeout` still
   frames optional durable session memory as a Claude-app memory write. Codex
   sessions need an equivalent closeout path that can point at Codex transcript
   exports or explicitly record `session_transcript: pending` until the Codex
   exporter proposal defines the durable archive identifier.

**Status:** Tracked, not yet implemented. Related design is
`PROP-LRH-CODEX-CONVERSATION-EXPORTER` and the target-aware skill installation
workstream in PR #468. The proposal-local
`project/design/proposals/proposed/lrh-codex-conversation-exporter/backlog.md`
exists only as a pointer back to this canonical backlog entry so future
proposal/work-item demand searches do not miss these follow-ups.

---

## Experimental-code linkage guardrail

**Noted:** 2026-08-07, while closing the Codex app-server thread export spike in
`experimental/save_codex_threads/`.

The repository now has an `experimental/` area for temporary exploration code.
That is useful for fast technical-risk retirement, but it creates a governance
gap: provisional spike helpers can accidentally become production dependencies
if `src/lrh/`, package exports, or normal tests import from `experimental/`.

Design a lightweight lint or validation check that preserves the intended
boundary:

- production package code under `src/lrh/` must not import from
  `experimental`;
- normal unit tests should not depend on `experimental` helpers;
- documentation may link to experimental findings;
- manual smoke scripts may invoke experimental probes only when explicitly
  marked as such;
- promoted code must move through an ordinary reviewed work item rather than
  being imported in place.

The check should be cheap enough to run with ordinary validation and should
avoid freezing `experimental/` into a public API surface. A simple first pass
could scan import statements and package metadata; a later proposal can decide
whether this belongs in `scripts/lint`, `lrh validate`, or both.

**Status:** Not started.

**Related:** `experimental/README.md`;
`experimental/save_codex_threads/findings.md`; Codex app-server thread export
spike.

---

## Codex executable trust and signature investigation

**Noted:** 2026-08-07, during the Codex app-server thread export spike after
macOS reported "Malware Blocked and Moved to Trash" for a stale Homebrew Codex
binary.

The spike retired the API feasibility risk, but it did not fully explain the
local trust state. After reinstall, the Homebrew Codex app-server route ran
successfully, but strict codesign verification still reported an invalid
signature for the candidate executable. That leaves an operational question for
LRH's eventual Codex exporter: how should the tool diagnose and report local
Codex executable trust ambiguity without either over-alarming users or silently
normalizing a compromised install?

Design or run an investigation that captures:

- reproducible diagnostics for Homebrew and ChatGPT-bundled Codex binaries;
- which `codesign`, Gatekeeper, XProtect, Homebrew cask, and ChatGPT app
  signals are authoritative for this installation path;
- whether the observed strict-verification failure is expected packaging
  behavior, a local quarantine/signature issue, or an upstream bug to report;
- the warning shape a production LRH exporter should emit when API calls work
  but executable trust checks are ambiguous;
- whether LRH should document a safe reinstall/verification path before
  invoking standalone `codex app-server`.

This should stay separate from the first exporter implementation unless it
surfaces a disqualifying safety issue. The exporter can record a manifest
warning such as `codex_trust_state_ambiguous` while the trust investigation
continues.

**Status:** Not started.

**Related:** `experimental/save_codex_threads/findings.md`; Codex app-server
thread export spike.

---

## Execution records have no positive primary-vs-side marker

**Noted:** 2026-08-07, during `WI-LAND-PRIMARY-RECORD-SUFFIX-COLLISION`'s
own review (PR #508). Codex flagged (P1,
`r3737192840`) that the fix's primary-vs-side-record provenance check —
strip a candidate's reserved suffix (`_REVIEW`, `_CONFIRM`,
`_CLOSEOUT_NOTE`, `_SELFREVIEW`) and check whether the resulting base slug
matches another record's slug — cannot, on its own, distinguish a primary
record whose slug coincidentally ends in one of those words from a
genuinely orphaned side record (created via `/lrh-review-response` or
`/lrh-confirm-fixes` for a PR that never got a `/lrh-implement` primary at
all, per those skills' own "leave `rerun_of:` empty" rule for that case).
Both produce identical `execution_id` content: a reserved-suffix ending
with no matching base anywhere. The landed fix mitigates this with sibling
elimination (a genuine side-record sibling for the same PR proves a
primary exists) and falls back to an explicit "ambiguous, stop and ask"
state rather than guessing when no sibling can prove it — but a PR with
exactly one orphaned side record and nothing else remains fundamentally
undecidable from naming alone.

**Idea:** Add a positive `record_kind:` (or similarly named) frontmatter
field, stamped by `lrh prompt record-execution` itself based on which
skill invokes it (or passed explicitly via a new CLI flag from each
side-record-producing skill's own call site), distinguishing `primary`
from `side` unambiguously regardless of slug wording. This removes the
need for any slug-based inference — the provenance check becomes a direct
field read — and fully resolves the single-orphan case the current fix
cannot. Touches `lrh prompt record-execution`'s CLI surface and the
execution-record schema (`lrh validate`), not just skill/reference
documentation, so it's a larger-scoped change than the current fix.

**Status:** Not started. Current landed behavior (sibling-elimination +
explicit ambiguous state) is a safe, appropriately-scoped mitigation, not
a full resolution.

**Related:** `WI-LAND-PRIMARY-RECORD-SUFFIX-COLLISION`,
`src/lrh/skills/lrh-land/references/land-workflow.md` § Primary vs.
side-record provenance check.

---

## `lrh sessions sync` has no default `/export` zip location

**Noted:** 2026-08-07, implementing `WI-SESSION-ARCHIVE-SYNC-RECONCILER`
(Stage 2 of `PROP-LRH-SESSION-ARCHIVE-SYNC`). `lrh sessions sync`'s
`--exports-dir` flag has no default value and export harvest is skipped
entirely when it is omitted — there is no established OS-level or LRH
convention for where a user's downloaded `session-export-*.zip` files
live (unlike `--claude-projects-root`, which defaults to
`~/.claude/projects`, the app's own fixed location). A wrong guess (e.g.
defaulting to `~/Downloads`) risks silently harvesting unrelated files or
missing the real location on a differently configured machine.

**Idea:** Once the archive-root-location open question (tracked in
`PROP-LRH-SESSION-ARCHIVE-SYNC`'s own Open Questions) is resolved, revisit
whether export-zip discovery should also gain a configurable default —
e.g. an `LRH_SESSION_EXPORTS_DIR` env var mirroring
`LRH_SESSION_ARCHIVE_ROOT`, or a value stored via `lrh meta config` once
that surface supports non-boolean values. Deferred rather than guessed at
in Stage 2, matching the proposal's Non-Goal that this item "does not
resolve the archive-root-location open question itself."

---

## Card-architecture reuse assessment (prosoc) — not yet warranted

**Noted:** 2026-08-03 (user-directed design session), assessing whether
`prosoc`'s normative-card-architecture tooling (`prosoc/packet/`,
`prosoc/literate/`, `prosoc/utils/cards/`, `prosoc/auditor/` — schema +
template + literate compiler + lifecycle gate + packet assembly) could be
extracted as a reusable library so LRH's own `project/principles/` and
`project/guardrails/` governance could adopt it, given growing
agent-harness surface (Claude Code, Codex, Antigravity) and deepening
autonomy/review-cycle structure around `/lrh-execute`.

**Findings, grounded in a full audit of both repos:**
- prosoc's engine is mostly already domain-agnostic: `prosoc/literate/`,
  `prosoc/packet/gate.py`, `prosoc/packet/manifest.py`,
  `prosoc/packet/resolve.py`, and all of `prosoc/auditor/` have zero
  family-specific branching. The one genuinely domain-coupled piece is
  `prosoc/packet/assemble.py`'s principle-union composition
  (`_principle_union`, lines 64-107; `_tensions`, lines 110-126), plus the required
  `guidance.principles`/`guidance.tensions` fields baked into
  `prosoc/packet/schema.json:108-136`. `prosoc/manifests/schema.json:50-59`
  also closed-enums prosoc's five family names directly.
- LRH's own current guidance content is small: `project/principles/*.md` +
  `project/guardrails/*.md` = 7 files, 53 bullet-level units, 188 lines
  (`wc -l project/principles/*.md project/guardrails/*.md`)
  total. Every file's `status` field reads `active` — no other lifecycle
  value has ever been exercised. Nothing in `src/lrh/` parses the internal
  structure: `src/lrh/assist/snapshot_cli.py:571-587`'s `summarize_file()`
  only pulls a fixed set of frontmatter keys (`id`/`title`/`status`/
  `priority`/`owner`) plus an opaque prose-excerpt "summary" for the
  `snapshot` CLI. `src/lrh/guardrails/safety.py:9-12`'s
  `SafetyGuardrail.evaluate()` is a literal no-op (`del proposal; return
  []`) — a same-named but disconnected skeleton package that never reads
  these markdown files.
- The actual growing complexity — autonomy scoping for `/lrh-execute`,
  review-cycle gating — is already served by a different, working,
  self-amending pattern: `project/memory/decisions/DEC-DELIBERATE-CHAIN-INITIATION.md`
  plus its two narrowing amendments (`DEC-CHAIN-INIT-SKIP-CONSENT.md`,
  `DEC-AGENT-EXECUTED-MERGE-GATE.md`), and
  `project/assistants/serve-interface-steward/*.md`'s independently
  invented `kind:`-tagged policy files. Neither borrows anything from
  prosoc.
- Harness differentiation is real and shipped for two of three targets:
  `src/lrh/skills/installer.py:21-23`'s `SkillTarget` enum currently
  covers `CLAUDE`/`CODEX` only, with `ClaudeSkillRenderer`/
  `CodexSkillRenderer` (`installer.py:172`, `:181`) implementing the
  per-target rendering. Antigravity support is tracked separately as
  proposed, not-yet-shipped work
  (`project/work_items/proposed/WI-SKILLS-ANTIGRAVITY-TARGET.md`,
  `status: proposed`) — correcting an earlier overstatement in this note
  that had it as already shipped for all three targets (caught in PR #517
  review). Either way, this differentiation lives at the skill-packaging
  layer — no evidence yet that `project/guardrails/` *content* itself
  needs to fork per harness.
- Checked against best-practice sources: Nygard's original ADR argument
  for small lightweight files over premature structure
  ("[l]arge documents are never kept up to date... [n]obody ever reads
  large documents, either" — cognitect.com, 2011); Fowler/Roberts' Rule of
  Three (one worked example — prosoc — is short of the threshold usually
  cited for safely abstracting a shared interface); Beck/Fowler's YAGNI
  cost-of-delay framing (martinfowler.com/bliki/Yagni.html); and Sandi
  Metz's "wrong abstraction" warning sign — *"if you find yourself passing
  parameters and adding conditional paths through shared code, the
  abstraction is incorrect"* (sandimetz.com, 2016) — which is already
  visible inside prosoc's own single-consumer `assemble.py` today
  (`if card.family == "constitutions": ...`).

**Status:** Not adopting or extracting now. Revisit at a future backlog
burndown when any of:
1. something in LRH needs to *programmatically gate* on guardrail/principle
   content, not just display it;
2. a guardrail or principle actually needs a non-`active` lifecycle state;
3. harness differentiation needs to reach into guidance *content*, not just
   skill packaging;
4. prosoc cleans up its own `packet/loader.py`/`utils/cards/validate_status.py`
   `FAMILIES`-dict duplication and/or makes `assemble.py`'s
   guidance-composition step pluggable — either would lower the cost of a
   future LRH adoption enough to reopen this.

If any of those fire, the recommended next step is prototyping directly in
LRH — define LRH's own family registry and a from-scratch LRH `assemble`
step (its composition need looks simpler than prosoc's, since it wouldn't
need per-scenario/context principle-emphasis unioning) — rather than
committing to a shared package up front.

**Related:** Mirrored entry in the sibling `prosocial` repo's own
`project/design/backlog.md` §
"LRH card-architecture reuse assessment — not yet warranted";
`prosoc/packet/assemble.py`, `prosoc/packet/loader.py`,
`prosoc/manifests/schema.json`; `project/principles/`,
`project/guardrails/`, `project/memory/decisions/DEC-DELIBERATE-CHAIN-INITIATION.md`,
`project/assistants/serve-interface-steward/`, `src/lrh/skills/installer.py`.

---

## `rerun_of`'s branch-slug search misses the primary record in two skills

**Noted:** 2026-08-10, during PR #536's review-response and confirm-fixes
rounds (`WI-FRONT-OF-RUN-GATE-COLLAPSE`). Both `/lrh-review-response` Step 7
and `/lrh-confirm-fixes` Step 7 resolve `rerun_of` by converting the *current
branch's* slug to upper-underscore and searching `project/executions/` for a
matching filename (excluding `_REVIEW.md`/`_CONFIRM.md`/`_SELFREVIEW.md`).
This search comes up empty whenever the branch slug and the primary record's
own slug diverge, and it fails silently — no error, just an empty result,
which is easy to miss and leave `rerun_of` unset without noticing.

Two distinct divergence shapes are now confirmed, in two different skills:
a branch carrying a disambiguating suffix the record's slug doesn't share
(e.g. `-impl`, PR #374 — see `feedback_split_wi_creation_impl_branch_naming`
in agent memory), and a WI-*creation* branch (`.../front-of-run-gate-collapse-wi`)
whose slug never matches a record that's named after the work item ID rather
than the branch (`..._WI_FRONT_OF_RUN_GATE_COLLAPSE.md`). Both times, a
`grep -rl "^pr: <pr-url>" project/executions/` search (excluding the same
three suffixes) found the record immediately.

A third shape surfaced 2026-08-17 on PR #561 (`/lrh-review-response` against
`experimental/rescue_claude_sessions`), and it is not a divergence at all:
the PR was opened by hand rather than through `/lrh-implement`, so **no**
primary record exists. The branch-slug search returned empty — correctly this
time — but produced exactly the same signal as the two miss cases above. That
generalises the defect: an empty result is not merely easy to overlook, it is
*uninterpretable*, because "the search missed the record" and "there is no
record" are indistinguishable without a second query. The run reached the
right `rerun_of` value on reasoning the search itself could not support, and
only confirmed it afterwards by running the `pr:`-field fallback (which also
returned nothing for #561, while returning three records for #556 — proving
the query sound and the absence real).

**Idea:** Change both skills' `rerun_of` resolution to search by the `pr:`
field first (or as a fallback when the branch-slug search comes up empty),
rather than relying solely on branch-slug matching. The `pr:` field is
already populated on the primary record by the time either skill runs, so
this doesn't require a new lookup mechanism — just reordering which one runs
first. Given the third shape, make the second query **mandatory** rather than
advisory: a skill should never record an empty `rerun_of` on the strength of
the branch-slug search alone, since that search cannot distinguish absence
from failure. Confirming a genuine absence is as much a use of the fallback
as finding a missed record.

**Status:** Not yet a work item. Surfaced twice on the same PR (its `_REVIEW`
and `_CONFIRM` records both hit it) and a third time on PR #561, so it's a
live nuisance, not a theoretical one — but it's a small, mechanical fix
confined to two `SKILL.md` files, better batched with other skill-text
maintenance than run solo.

**Related:** `src/lrh/skills/lrh-review-response/SKILL.md` Step 7;
`src/lrh/skills/lrh-confirm-fixes/SKILL.md` Step 7;
`project/executions/AD_HOC/2026_08_10_04_10_59_FRONT_OF_RUN_GATE_COLLAPSE_WI_REVIEW.md`;
`project/executions/AD_HOC/2026_08_10_07_01_20_FRONT_OF_RUN_GATE_COLLAPSE_WI_CONFIRM.md`;
PR #536; PR #374.

---

## Workstream `## Exit Criteria` body-restatement guidance is stale relative to adopted practice

**Noted:** 2026-08-10, during PR #536's review response. Fixing a Codex P2
finding (a duplicated Stage 3 exit criterion drifting between
`WS-INVOCATION-AND-GATE-RESET`'s frontmatter `exit_criteria:` list and its
human-readable `## Exit Criteria` body section — the second copy had already
drifted once before, on the `skip_if_opted_in` clause) meant choosing between
syncing the two copies or removing the duplication. The duplication was
removed, replaced with a pointer at the frontmatter field.

That departs from the skill's own documented convention:
`src/lrh/skills/lrh-workstream/references/workstream-body-guide.md:96` says
the body section "mirrors and expands" the frontmatter list, and
`src/lrh/skills/lrh-workstream/SKILL.md:107-109` instructs authors to produce
both. But checking practice against convention found five sibling
workstreams — spanning every lifecycle bucket
(`WS-EXECUTION-FRAMEWORK`, `WS-CI-CAPABILITY-SCAFFOLDING` in `proposed/`;
`WS-LRH-ASSISTANTS` in `active/`; `WS-PRIOR-ART-CHECK`, `WS-SKILLS` in
`resolved/`) — already carry a populated `exit_criteria:` with no body
restatement at all. The documented convention and the adopted practice
disagree, and nothing currently reconciles them.

**Idea:** Decide one convention for the `## Exit Criteria` body section —
either restore the "mirrors and expands" instruction and backfill the five
outlier workstreams, or update `workstream-body-guide.md` and
`lrh-workstream/SKILL.md` to say the body section may be a pointer, and treat
that as the default going forward. Two copies of a mutable list are two
things to get right and one thing that will eventually be wrong, which is
exactly the restatement-drift failure `PROP-INVOCATION-AND-GATE-RESET`
documents — leaving the skill's own guidance ambiguous on this point
guarantees the next workstream author picks arbitrarily.

**Status:** Not yet a work item. Recorded as a Risk Notes follow-up in
`WI-FRONT-OF-RUN-GATE-COLLAPSE` but not filed as its own item; small in scope
(two reference files plus a decision about backfilling five workstreams),
better batched with other `lrh-workstream` skill maintenance.

**Related:** `src/lrh/skills/lrh-workstream/references/workstream-body-guide.md:96`;
`src/lrh/skills/lrh-workstream/SKILL.md:107-109`;
`project/work_items/resolved/WI-FRONT-OF-RUN-GATE-COLLAPSE.md` (Risk Notes);
`project/workstreams/active/WS-INVOCATION-AND-GATE-RESET.md`; PR #536.

---

## Review-comment fetch misses the GitHub issue-comments surface entirely

**Noted:** 2026-08-10/11, during PR #541's confirm-fixes round
(`WI-RETRIGGER-REMOVAL-STAGE1`). `chatgpt-codex-connector` posted a
substantive comment on the PR's automatic first-push review — narrating
findings and an attempted (unmerged, unreachable) fix — via
`POST /issues/{n}/comments`, not as a formal PR review or an inline review
thread. Neither `lrh request review_response`'s comment fetch (used by
`/lrh-review-response` Step 2 and `/lrh-confirm-fixes` Step 2) nor
`lrh github threads` reads that endpoint, so the comment was invisible to
both skills' standard triage. It surfaced only because this session
independently queried
`gh api repos/<owner>/<repo>/issues/<n>/comments` out of caution after a
prior, unrelated finding about non-thread reviewer content
(`feedback_codex_clean_pass_issue_comment` in agent memory) — not because
any tooling step called for it.

One of the comment's two claims was real: a propagation gap
(`self_review_preference` inlined a third time, in
`lrh-land/references/land-workflow.md`, missed by the work item's own
Required Changes and `artifacts_expected`) that a full review round had
already passed without catching, simply because the finding never reached
either skill's read path. Round 1 of this PR's review-response therefore
completed, and Round 1 of confirm-fixes nearly reported clean, without
either skill ever having read the comment that contained the one thing
still wrong.

**Idea:** Add `gh api repos/{owner}/{repo}/issues/{pr_number}/comments` as
a third read in `lrh request review_response`'s comment-gathering step
(alongside the existing reviews and review-thread reads), or as an
explicit Step 2.4 in `/lrh-confirm-fixes`, so issue-comment-posted findings
enter the same triage taxonomy as thread comments rather than requiring a
human or an unusually cautious agent to think to check a third endpoint.
Needs its own dedup logic against `lrh github threads`' output, since a
bot sometimes posts the same content on both surfaces.

**Status:** Not yet a work item. Confirmed exactly once so far (this PR),
but the mechanism generalizes to any Codex/Copilot posting pattern that
uses the issue-comment API rather than a formal review, and the existing
`feedback_codex_clean_pass_issue_comment` memory shows this is not a
first occurrence of content landing there — only the first occurrence
of a *missed defect*, not just a missed clean-pass signal.

**Related:** `src/lrh/skills/lrh-review-response/SKILL.md` Step 2;
`src/lrh/skills/lrh-confirm-fixes/SKILL.md` Step 2;
`project/executions/AD_HOC/2026_08_11_00_55_07_RETRIGGER_REMOVAL_STAGE1_WI_CONFIRM.md`
(Round 2); PR #541.

---

## `lrh memory` command to make cross-agent memory writes well-formed by construction

**Noted:** 2026-08-17, while preparing the memory migration in
`experimental/rescue_claude_sessions/`. Auditing all 461 memory files under
`~/.claude/projects/*/memory/` found 19 across 5 project buckets that lack
Claude's memory frontmatter (`name`, `description`, `metadata.type`). Codex was
caught writing one live: it created a memory file in Claude's LCATS corpus with
no frontmatter and no `MEMORY.md` entry, making it unreachable by recall. In
another bucket it wrote `MEMORY.md` to the bucket root instead of
`memory/MEMORY.md`, orphaning all three files there. Nothing was overwritten
and no data was lost — the existing 129-line LCATS index was verified
byte-identical against a snapshot — but the writes are silently ineffective.

The pattern predates the 2026-08-17 repository relocation: non-conforming
writes start 2026-08-03, and conforming and non-conforming files appear on the
same days (Aug 3: 5 vs 4; Aug 13: 25 vs 5), which rules out a format migration
and indicates two writers with two conventions.

**Idea:** Provide an `lrh memory` command (or equivalent) that agents call
instead of writing memory files directly, so a malformed memory is not
representable: validate frontmatter on write; update `MEMORY.md` in the same
operation so an unindexed memory cannot exist; resolve the corpus path
internally so "wrong location" cannot happen; record `authored_by` (and
possibly `applies_to`) so memories can be filtered by agent; and offer a read
path so agents recall without knowing the layout. The `authored_by` field also
addresses semantic contamination — the Codex file that landed in LCATS is
Codex-specific sandbox guidance sitting where a Claude session would read it as
its own.

**Second gap — memory has no archival path at all (found 2026-08-18).**
`lrh sessions sync` mirrors `<project-slug>/*.jsonl` only. It archives **zero**
memory files: after a full sync of 187 transcripts, `find <archive-root> -name
'*.md'` returned 0 and no `memory/` directory existed anywhere under it. So the
durable-archive guarantee that covers transcripts does not extend to memory,
and during this rescue the only backup of 296 memory files was a tarball in
`/private/tmp`, which macOS reclaims. That was caught only at the point of
retiring the source corpora, which would otherwise have left them single-copy;
they were moved to `~/.local/share/claude-session-rescue/` instead.

This is arguably the larger half of the problem: the write-side idea above
stops malformed memories being created, but nothing today makes memory
*survivable*. Candidate fix: have `lrh sessions sync` mirror `memory/`
alongside `*.jsonl` under the same archive root, with the same never-replace-
with-a-smaller-source invariant. That would also give `authored_by` filtering
a durable corpus to operate over, and would close the gap without a new
mechanism — memory is already path-keyed the same way transcripts are.

**Status:** Tracked, not designed. Deliberately not blocking the memory
migration it was discovered during: migration is a byte-exact copy and is
format-agnostic, so it neither improves nor worsens these files. The archival
gap is independent of the write-side idea and could land first.

**Related:** `experimental/rescue_claude_sessions/findings.md` (full evidence,
per-bucket counts, and the interleaving analysis);
`experimental/rescue_claude_sessions/README.md`; PR #561.

## Codex export durable-archive gap has a stopgap; the real fix is still open

**Idea (already scoped):** `WI-CODEX-EXPORT-DURABLE-ARCHIVE-DEFAULT`
(`project/work_items/proposed/`) is the real fix — makes `/lrh-codex-export`
durable-archive-first by default instead of `${TMPDIR:-/tmp}`, adds per-attempt
metadata, and covers full migration UX. It `depends_on:
WI-CODEX-CONVERSATION-EXPORT-SKILL, WI-SESSION-ARCHIVE-SYNC-RECONCILER` and
bundles a skill rewrite, tests, and docs — not something to wait on for the
immediate problem of exports already stranded in OS temp storage.

**Stopgap shipped instead:** `experimental/rescue_codex_exports/` — two
scripts (`find_exports.py` read-only scan/classify, `move_exports.py`
copy-verify-delete migration) that find `lrh-codex-export-*` directories
under an arbitrary root and consolidate them into `~/.lrh/private/codex/`,
the durable location `SKILL.md` Step 2 already documents but the routine
capture path doesn't use. Covers Required Change #5 of the work item above
("import/migrate existing... export directories... into the durable
archive") narrowly, not the rest of its scope. `<dest>/MIGRATION_LOG.md`
records every directory's origin so nothing moved by this tool loses
provenance.

**Status:** Stopgap tooling landed; the work item above remains `proposed`
and unblocked by this — whoever picks it up should know this tool already
covers its import/migrate requirement and can either reuse or supersede it.

**Related:** `experimental/rescue_codex_exports/README.md`;
`project/work_items/proposed/WI-CODEX-EXPORT-DURABLE-ARCHIVE-DEFAULT.md`.

---

## `/lrh-assess` skill — not yet warranted

**Noted:** 2026-08-21, during WS-SKILLS retrospective after all workstream
items resolved.

**Background:** `WS-SKILLS` (`project/workstreams/resolved/WS-SKILLS.md`)
described Stage 3 workflow skills as `/lrh-work-item`, `/lrh-workstream`, and
`/lrh-assess`. The first two were implemented and their work items resolved.
`/lrh-assess` was never promoted to a work item; the workstream closed without
it. No work item, backlog entry, or decision record for `/lrh-assess` existed
anywhere in the control plane as of the date above.

**Original intent:** The WS-SKILLS summary describes LRH's Apple Notes workflow
steps as "assess → design → create workstream → create work item." The `assess`
step was the session-opening triage: survey project state, synthesise
priorities, recommend what to work on next.

**Analysis:**

`/lrh-work-remains` (`.claude/skills/lrh-work-remains/SKILL.md`) reads the
same signals (open PRs, work items, workstreams, `lrh snapshot current_focus`)
but is oriented retrospectively — "what's unfinished?" — and is report-only by
design; it "does not offer to act on any finding." The genuinely missing piece
would be prospective synthesis: given current state, recommend the
highest-value next action with rationale.

That prospective question is, however, already largely answered by the
structured planning artifacts: the active workstream's `stage` +
`exit_criteria` fields, `lrh work-items readiness --status proposed`, and
`lrh snapshot current_focus` together deterministically identify the next ready
item in most sessions. The session-opening question "what's next on this
workstream?" is answered correctly in two tool calls — a skill for it would add
maintenance cost (two-file mirror: `src/lrh/skills/` + `.claude/skills/`)
without a proportionate reduction in friction.

Extending `/lrh-work-remains` with a `--plan` mode was considered and
rejected: the skill's strict report-only identity is its most important safety
property; mixing retrospective accounting with prospective action
recommendations would erode that.

**Decision:** Do not implement `/lrh-assess` as a separate skill. Re-evaluate
if a pattern emerges where session-start triage is consistently painful despite
using `/lrh-work-remains` + workstream/work-item reads. If that pattern
emerges, prefer a `--plan` flag on `/lrh-work-remains` over a new skill only
if the prospective output is genuinely separable from report-only; otherwise
implement as a new skill at that time.
