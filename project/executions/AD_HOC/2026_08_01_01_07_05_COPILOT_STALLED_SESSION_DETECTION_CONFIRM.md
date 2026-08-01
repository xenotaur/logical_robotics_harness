---
execution_id: 2026_08_01_01_07_05_COPILOT_STALLED_SESSION_DETECTION_CONFIRM
prompt_id: PROMPT(AD_HOC:COPILOT_STALLED_SESSION_DETECTION_CONFIRM)[2026-08-01T01:06:16+00:00]
work_item: AD_HOC
status: landed
rerun_of: 2026_08_01_00_13_37_COPILOT_STALLED_SESSION_DETECTION
pr: https://github.com/xenotaur/logical_robotics_harness/pull/452
commit: 5211e4027c7cd749f9ef3b98560be14e0e6d7202
created_at: 2026-08-01T01:07:05+00:00
agent: claude_app
instruction_source: https://github.com/xenotaur/logical_robotics_harness/pull/452
session_transcript: claude-app:23a15fdd-6d6c-4d84-a7be-960a54769157
---

# Summary

Pre-merge verification and thread-resolution pass for PR #452, via
`/lrh-land`'s inlined confirm-fixes step. Fresh-eyes check of the 6
unresolved threads against HEAD `e9647f1` (the commit pushed in the prior
`_REVIEW` round), CI check, and thread resolution.

# Result

**Thread verification (against `gh pr diff` on `e9647f1`, not the
execution record's claims):**

| Thread | Author | Bucket | Rationale |
|---|---|---|---|
| `PRRT_kwDOR7l1D86VkPB2` | chatgpt-codex-connector | Clear-satisfied | `round-cap-gate.md`'s corroboration section now correlates `copilot_work_started` to this step's own reviewer-request call by timestamp, not any event on the PR |
| `PRRT_kwDOR7l1D86VkPR7` | copilot-pull-request-reviewer | Clear-satisfied | "not simple lag" softened in `SKILL.md`'s Stall-detected question text |
| `PRRT_kwDOR7l1D86VkPSe` | copilot-pull-request-reviewer | Clear-satisfied | duplicate of the above |
| `PRRT_kwDOR7l1D86VkPSk` | copilot-pull-request-reviewer | Clear-satisfied | "Both signals together ... is stalled" fixed to "indicate a stalled session" in `round-cap-gate.md` |
| `PRRT_kwDOR7l1D86VkPSt` | copilot-pull-request-reviewer | Clear-satisfied | literal "`_finished_failure`" shorthand wasn't present verbatim (verified by grep before the review-response round), but the diff addresses the underlying spirit — `SKILL.md`'s Step 8.3 now names `copilot_work_finished`/`copilot_work_finished_failure` explicitly, matching `round-cap-gate.md`'s phrasing |
| `PRRT_kwDOR7l1D86VkPS2` | copilot-pull-request-reviewer | Clear-satisfied | duplicate of the `PRRT_...PSk` fix |

All 6 confirmed present in the current diff (no guess-resolution). Batch
confirmed with the user before resolving. All 6 resolved via
`resolveReviewThread`; no exceptions surfaced.

**Thread-resolution verdict (Step 6): Green** — every thread resolved, no
exceptions remain open.

**CI (Step 2, provisional read):** `gh pr checks --required` errored "no
required checks reported"; distinguishing check
(`gh api repos/xenotaur/logical_robotics_harness/rules/branches/main`)
returned 0 `required_status_checks` rules — confirmed no required-check
protection on this repo (matches this doc's own PR #399 precedent), safe
to fall back to the unfiltered aggregate: 5/5 checks (`Check workflow
files`, `coverage`, `installed-wheel-smoke`, `lint`, `tests`) `SUCCESS`.

**Step 8 — retrigger on `97ce0cc` (the `_CONFIRM` commit above):** CI went
green (5/5). Codex reviewed `97ce0cc931` and reported no findings (clean
pass). Copilot reviewed and reported "generated no new comments" but
surfaced 2 **suppressed** (non-blocking, non-thread) findings in the
review body — per `SKILL.md` Step 8's non-thread-finding rule, these count
as genuine findings, not silence, and were triaged:

1. **Check-run selection bug (real, valid):** the check-run `--jq`
   expression selected *every* matching check-run, not the most recent —
   a retriggered/rerun check-run could get compared against the wrong
   `started_at`. Fixed: `sort_by(.started_at) | last`.
2. **Self-contradiction (real, valid):** the section's opening framing
   ("reviewer never invoked / not configured for this repo") and the
   check-run bullet's parenthetical implied the heuristic can determine
   "not configured," contradicting this same section's own later caveat
   against inferring unconfigured status from silence. Reworded both to
   "no evidence the reviewer was invoked this round."

Both fixed in `round-cap-gate.md` (+ `src/lrh/...` mirror), replied to on
the PR (issuecomment-5148867522) since there's no thread to resolve, and
pushed as a further commit — REVIEW-LANDED requires a fresh
retrigger-and-wait pass against that new `HEAD` per Step 8's own rule for
non-thread findings.

This is retrigger round 2 for this PR (round 1: the initial `_REVIEW`
push). Both rounds are within the round-cap gate's default ceiling of 3 —
not yet tracked via the full `lrh-round-state` branch mechanism at this
point in the run (see the later correction below — round 8's Codex review
found actual inline threads this record's own monitoring missed, and
that same pass discovered a live concurrent session already using
`lrh-round-state` for real on two other open PRs, at which point this PR
was backfilled onto it too).

# Validation

```
lrh validate            — 0 errors, 1 pre-existing unrelated warning
scripts/format --check --diff, scripts/lint, scripts/test — all clean/808 tests OK
gh pr checks (unfiltered, required-check-protection confirmed absent) —
                           5/5 SUCCESS at e9647f1, then again after the
                           round-2 push
resolveReviewThread × 6 — all returned isResolved: true
```

**Round 2 retrigger result, on `70d8f98` (post-remediation commit):** CI
green (5/5). Codex: "Didn't find any major issues" (clean, reviewed
`70d8f98da3`). Copilot: "generated no new comments" (clean, no suppressed
findings this round, reviewed `70d8f98da325b0a5b85595530524d41849bf40f9`).
REVIEW-LANDED satisfied on this commit.

**Self-caught process error:** after computing a Green verdict against
`70d8f98`, this same record was then pushed as a further commit
(`79de62f`) to document that verdict — moving `HEAD` past the commit the
verdict actually covered, exactly the race Step 8 warns against ("a human
who replies 'I'll merge it' right after the push races the same delayed
finding an agent would"). Caught before presenting any merge command;
treated `79de62f` as requiring its own full CI + REVIEW-LANDED re-check
(round 3) rather than trusting the stale verdict.

**Round 3 retrigger result, on `79de62f`:** CI green (5/5). Codex: "Didn't
find any major issues" (clean, reviewed `79de62f79b`). Copilot:
"generated no new comments" but surfaced 2 more suppressed non-thread
findings: (1) a "Round-state branch mechanics ... above" cross-reference
that's actually later in the file (line 233 vs. 62) — fixed to "below";
(2) this record's own "not-configured vs. stalled" phrasing drifted from
the now-corrected "no evidence the reviewer was invoked this round"
wording — updated to match. Both fixed, replied to on the PR
(issuecomment-5149696806).

**Round-cap gate fired:** this PR had completed 3 retrigger batches
(round 1 initial push, round 2 remediation, round 3 record-only push),
at the default ceiling of 3 — pushing the round-3 fixes would start a
4th batch. Presented the three-way gate to the human (`completed_count=3,
ceiling=3`, one-line findings summary above); **authorized new
ceiling → 10.** At this point in the run, not yet tracked via the full
`lrh-round-state` branch mechanism — mistakenly reasoned as unnecessary
for a single-PR case; the round count was instead tracked only in this
markdown record. **This reasoning was wrong** — an automated reviewer
(Codex, round 8, thread `PRRT_kwDOR7l1D86VlgVj`, P1) correctly flagged
that a fresh session resuming this chain would re-initialize at
`completed_count=0, ceiling=3` from this file alone, since
`round-cap-gate.md` itself forbids reconstructing round state from a
post-hoc record. Backfilled onto `lrh-round-state` for real once found
(see the round 8 entry below) — discovering, in the process, that the
branch already had live entries for two other open PRs from a concurrent
session, confirming the mechanism genuinely works under real concurrent
use, not just in the worked-through design in `round-cap-gate.md`.

**Round 4 retrigger result, on `cc76f67`** (the round-3 fixes + this
record update, pushed together in one commit this time): CI green (5/5).
Codex: clean pass, reviewed `cc76f6745b`. Copilot: "generated no new
comments" but surfaced 2 more suppressed non-thread findings, both about
missing `--paginate` on the `gh api` calls in "Detecting a stalled
reviewer session" — the check-runs call could miss the reviewer's own
check-run on a CI-heavy commit, and the timeline call could miss the
corroborating `copilot_work_*` event on a PR with a long history. Fixed in
both mirrors, replied to on the PR.

Round 4 completed_count is now 4 (still under the authorized ceiling of
10) — no further gate needed for round 5.

**Round 5 retrigger result, on `3e0caea`** (the `--paginate` fix): CI
green (5/5). Codex: clean pass, reviewed `3e0caeaf6c`. Copilot: 1 more
suppressed finding — **and this one caught a real over-claim in this same
record's own round-4 entry above.** That entry said the paginated queries
were "verified live against this PR" to return "the correctly merged,
multi-page result" — but the live test only exercised this PR's own
commits, which have 5-6 check-runs, well under one page; it could not
actually distinguish "jq runs once on the merged cross-page result" from
"jq runs once per page," and the claim of having verified the latter was
false. Copilot's finding: `gh help api` states directly ("Each page is a
separate JSON array or object") that `--jq` runs **per page**, not on a
merged result. The check-run query's `map(...) | sort_by(...) | last`
inside `--jq` therefore only finds the "most recent" match *within a
single page* — a page with zero matches would independently emit a
spurious `{"status":null,...}`, and a true most-recent match on an
earlier page could be discarded. Confirmed directly (`gh help api`
excerpt, plus a constructed zero-match-page test reproducing the spurious
null object). Fixed properly this time: stream `.check_runs[] |
select(...)` per page (safe under per-page evaluation — zero matches on a
page emits nothing, not a null), then a second `jq -s` pass outside
`gh api` collects the full cross-page stream before sorting and selecting
the true most recent. Verified both the match and zero-match cases
against this fix. The timeline query was checked too and needs no
equivalent fix — it never attempts a `sort`/`last` selection inside
`--jq`; it streams every match across all pages as-is, leaving
timestamp correlation to the reader, so per-page evaluation doesn't
truncate anything there.

Round 5 completed_count is now 5 (still under ceiling 10).

**Round 6 retrigger result, on `7ef28f6`:** CI green (5/5). Codex: clean
pass, reviewed `7ef28f687e`. Copilot: 1 more suppressed finding — the
zero-match case still emitted a misleading `{"status":null,...}` object
(empty slurped array → `last` → `null` → projected fields), undermining
the "no check-run" vs. "in_progress" distinction. Fixed:
`select(. != null)` after `last`, before projecting — verified both the
match and zero-match cases produce truly empty output on no match.

Round 6 completed_count is now 6 (still under ceiling 10). Given six
consecutive rounds have each found one real, legitimate, low-risk issue
in this same detection heuristic — a pattern this repo's own
`round-cap-gate.md` "Risk Notes" section already documents happening on
its *own* mechanism (8 rounds on PR #445) — round 7 is treated as the
last one chased before deferring any further micro-refinement to the
design backlog per this project's standing "defer narrow edge cases"
convention, rather than continuing indefinitely.

**Round 7 retrigger result, on `33e66ca`:** CI green (5/5). Codex: clean
pass, reviewed `33e66ca3d3`. Copilot: "generated no new comments" but
surfaced 3 more suppressed findings — (1) `backlog.md`'s own
"Promote stalled-reviewer-session detection..." entry quotes stale
"reviewer never invoked" wording, drifted from round 3's correction; (2)
and (3) `SKILL.md` Step 8.3's "first check whether that reviewer's own
session actually started and stalled" reads as reviewer-generic, but the
heuristic it cross-references is built entirely from Copilot-specific
signals (check-run name, `copilot_work_*` events) — not a correctness
bug (a non-Copilot reviewer would just get an empty result and correctly
fall through to "No stall detected"), but the scope isn't made explicit.

**Classified per Step 3's taxonomy and Step 8's non-thread-finding rule
(genuine findings, not silence — routed through triage, not silently
dropped):** all three **Unaddressed — deferred**, per the round-7
stopping-point decision recorded above (written *before* round 7's
response was read, not retrofitted to justify skipping real findings).
Rationale: neither is core to this PR's stated purpose (detecting a
Copilot-credit-exhaustion-shaped stall), neither is a correctness bug,
and this project's own `round-cap-gate.md` models the identical
practice — its implementation (PR #445) stopped chasing after 8 rounds
for the same reason. Captured in `project/design/backlog.md` ("Stalled-
reviewer-session detection is Copilot-specific but reads as
reviewer-generic") for follow-up. Replied to on the PR explaining the
deferral.

REVIEW-LANDED is satisfied on `33e66ca` — both reviewers gave their
round-7 response with no formal thread and no blocking finding; the 3
deferred items are explicitly triaged Unaddressed-and-deferred, not
silently waved through.

**This backlog entry plus this paragraph are themselves new content on
top of `33e66ca`** — pushed together as one commit, this record's true
final round (round 8): retrigger, wait for a clean pass on that exact new
`HEAD`, and present the merge command only then, with no further edits
after that push. See the final verdict below.

**Round 8 retrigger result, on `0c58868`: a real process error, caught by
Codex, not by this record's own monitoring.** CI green (5/5), Codex clean
pass (review body), Copilot clean pass (review body, re-surfacing only
the 2 already-deferred items from round 7 — expected, since Copilot
re-scans the cumulative diff each round and these were deliberately left
unfixed). But a post-round check of `lrh github threads` — run only
because the human asked for round 9+ before merging, not as a standing
practice this record had been following — found **7 unresolved inline
review threads from Codex**, accumulated silently across rounds 4–8. This
record's own round-by-round monitoring (rounds 4–8) only polled `.reviews[]`
and `.comments[]` for each round's *response*, never re-polled
`lrh github threads` for new *inline* threads distinct from those
response bodies — a real gap against `SKILL.md` Step 8.2's own
instruction to poll for "a new inline thread whose body cites the current
SHA," not just reviews and comments. All 7 read and triaged:

1. **P1 (`PRRT_...VlgVj`) — persist the authorized round count.** Real
   and correctly caught: `completed_count`/`ceiling` had only ever been
   tracked in this markdown record, contradicting `round-cap-gate.md`'s
   own explicit rule that a fresh session must not reconstruct round
   state from a post-hoc record. **Fixed for real**, not just
   documented: backfilled `project/executions/round_state/xenotaur-logical_robotics_harness-pr452.json`
   (`ceiling: 10, completed_count: 8, pending_attempt: null`) onto the
   live `lrh-round-state` branch via the documented worktree procedure
   — discovering in the process that the branch already carries live
   state for two other open PRs (`#453`, `#454`) from a concurrent
   session, confirming the mechanism works under genuine concurrent use.
2. **P2 (`PRRT_...Vkede`) — product-mismatch dispute, reopened.**
   Investigated rigorously, not dismissed: re-fetched `xenotaur/LCATS#202`'s
   full timeline directly (not from memory) and confirmed, with exact
   timestamps, that both Copilot products emit `copilot_work_*` events —
   comment-triggered coding-agent instances at `19:57:47`, `20:09:15`,
   `20:41:21`, `23:14:24`, `23:50:48`; and **two** review-request-triggered
   code-review instances, `19:06:30` (25s after its `review_requested`)
   and `22:29:57` (34s after its `review_requested` — the actual stalled
   incident this whole feature is about). Also found and fixed a real
   bug Codex's finding pointed at: the section previously *required*
   both the check-run and a correlated timeline event (an AND) before
   calling anything "stalled" — backwards for a fail-safe design, since
   the timeline correlation is the fragile signal. Redesigned: check-run
   alone is now the sufficient, primary signal; the timeline event is
   optional corroboration only, never a gate on the verdict.
3. **P2 (`PRRT_...Vkoef`) and P2 (`PRRT_...VlcVw`) — pagination,
   re-flagged with more specificity.** Cited this repo's own established
   `--paginate --slurp` pattern (`src/lrh/integrations/github/pull_reviews.py:164-173`)
   as precedent I should have followed instead of the ad hoc two-jq-pass
   workaround from round 5. Switched both queries to that pattern.
4. **P2 (`PRRT_...Vld0U`) — same pagination bug, independently
   confirmed.** Directly cites this repo's own `--paginate --slurp`
   convention as the fix — same as items 3, folded into the same change.
5. **P2 (`PRRT_...VlhdI`) — strip `local_` prefix from `session_transcript`.**
   Real: `project/executions/README.md:65` states the canonical form is
   `claude-app:<host-uuid-stem>`, "`local_` prefix stripped." All 3
   execution records this PR created had the un-stripped form. Fixed in
   all 3.
6. **P2 (`PRRT_...Vljbj`) — capture the reviewer-request timestamp
   explicitly.** Real: the prose said "correlate to the nearest event
   after the retrigger call" but never showed capturing that boundary.
   Fixed: the timeline query now captures `RETRIGGER_AT` via `date -u`
   immediately before issuing the reviewer-request, and filters/sorts
   against it directly in the `jq` pipeline. (Now optional corroboration
   per item 2's redesign, not load-bearing, but still specified
   precisely per this finding.)

Also fixed while re-verifying item 2: this record's own `instruction_source`
and Result text had mislabeled the LCATS#202 incident as a "coding-agent
session" — it was actually the **code-review** product (the one Step 8
retriggers); the coding-agent evidence in that same PR is real but from
different, earlier timeline entries. Corrected.

Round 8 completed_count is now 8 — round-state now real, on
`lrh-round-state`, not just this record's own prose.

**Round 9 retrigger result, on `f758176`:** CI green (5/5), Codex and
Copilot both clean (review bodies). This round's monitoring explicitly
re-checked `lrh github threads` (not just reviews/comments) — the exact
gap that caused rounds 4-8 to miss the 7 threads above — and found **1**
new formal thread (`PRRT_kwDOR7l1D86Vl3Au`, Codex, P2): a real,
precisely-caught bug in the round-8 fix itself. The redesigned check-run
query selected the globally most-recent matching check-run, but never
required it to have started at or after *this round's* retrigger — on a
same-`HEAD` retry (no new push), a stale `in_progress` run from an
already-answered earlier round would still be the "most recent" one,
misreporting an old, already-known stall as evidence for the current
round. Fixed: capture `RETRIGGER_AT` once, before either query (not just
before the timeline query, as the round-8 version did), and filter the
check-run query itself to `started_at >= $since`. Verified live (match
and zero-match cases). Thread resolved.

Round-state updated to `completed_count: 9` on `lrh-round-state` (batch
promoted on confirmed submission, per "Any-side-effect-counts
promotion" — before waiting for the response above).

**Round 10 retrigger result, on `951359c` — at the authorized ceiling of
10.** CI green (5/5). Codex: fully clean, no findings at all. Copilot:
"generated no new comments," 2 suppressed — one a repeat of the
already-deferred reviewer-generic-framing item (expected, re-scans the
cumulative diff each round), one new and real: the check-run `--jq`
output omitted `name`, but `SKILL.md`'s "Stall detected" prompt template
has a `<name>` placeholder with nothing to fill it. Zero unresolved
formal threads. Round-state updated to `completed_count: 10` on
`lrh-round-state`.

Per the round-cap gate firing again at this ceiling, presented the
options to the human; **chose neither authorize-a-new-ceiling nor
merge-as-is** — fixed the `name` omission (one-line addition:
`{name, status, conclusion, started_at, completed_at}`, verified live)
and requested an independent subagent review pass instead of an 11th
bot-retrigger batch, avoiding further Copilot/Codex spend after 10
rounds.

**Independent subagent review, dispatched cold** (PR URL + orientation
only, no session memory, instructed to verify every claim itself rather
than trust the summary): found the **most severe issue of the entire
PR** — more serious than anything Codex or Copilot caught in 10 rounds.

The "capture `RETRIGGER_AT`, re-issue `gh pr edit --add-reviewer
@copilot`" design from round 8 (still in place through round 10) is
self-contradictory with `SKILL.md` Step 8.1's own pre-existing,
not-written-by-this-PR text: "the reviewer-request may likewise no-op
(already requested)... without touching a file either way." By the time
Step 8.3's stall-check runs, Copilot is *always* already a requested
reviewer (Step 8.1 just requested it) — so re-issuing the same command
inside "Detecting a stalled reviewer session" would either no-op
silently (the documented common case) or, even if it somehow did launch
something, would still set `$since` to a timestamp *after* the real
check-run Step 8.1's original retrigger started. Either way: the
heuristic reports "no evidence invoked this round" for a reviewer that
was invoked this round and is genuinely, actively stalled — the exact
failure mode the whole design claims to prevent, in precisely the
primary scenario the feature exists for (Step 8.1 retriggers, waits,
gets nothing, Step 8.3 checks for a stall).

Verified the root cause against `SKILL.md` Step 8.1's own text (not
newly written — confirmed pre-existing, from PR #445) before accepting
the finding. **Fixed properly, not patched around:** removed the
redundant re-retrigger entirely from `round-cap-gate.md` — that section
is now explicitly documented as a **read-only diagnostic**, never an
action. `SKILL.md` Step 8.1 now captures `BATCH_RETRIGGERED_AT` at the
point of its own (only) retrigger call, and `round-cap-gate.md`'s two
queries (check-run and timeline) both reuse that single value — passed
through, never re-minted. Added a note that Step 8.2's wait can span a
session interruption (this session hit exactly that scenario earlier),
so the captured value should be noted somewhere durable, not trusted to
survive purely as shell state. Updated the "Never invoked" bucket's
definition to state explicitly that its correctness depends on
`$BATCH_RETRIGGERED_AT` being Step 8.1's real timestamp, not a
freshly-issued one.

The subagent separately verified, live against this PR's own commits and
timeline (not just re-reading the prose), that everything else already
landed is correct: `--paginate --slurp` pagination mechanics for both
endpoint shapes, `$since` filtering behavior, zero-match empty output,
the fixed per-page-`--jq` bug class from round 5, `SKILL.md`↔
`round-cap-gate.md` consistency, and mirror byte-identity. No other
findings. Fixed and pushed as `9f66b83`.

**Second independent subagent review, dispatched cold** (told explicitly
not to trust the first pass's fix, verify it itself): found an even more
severe, previously-undetected bug in that exact fix, by testing an
assumption no one — not 10 bot-review rounds, not the first subagent —
had actually tested empirically: whether a shell variable set in one
Bash tool call survives to a *separate* Bash tool call in this harness.

It ran the test directly (`export X=1` in one call, `echo $X` in the
next → empty) and showed the consequence: `BATCH_RETRIGGERED_AT`,
captured in `SKILL.md` Step 8.1, could never actually reach Step 8.3's
queries in real execution — Step 8.2's wait is inherently one or more
separate tool calls, sometimes spanning a session interruption (this
session hit exactly that scenario earlier tonight). With `$since` empty,
`jq`'s `>=` comparison is true for every timestamp (verified:
`jq -n --arg since "" '"2024-01-01T00:00:00Z" >= $since'` → `true`),
silently defeating the entire round-9 fix and reintroducing the
stale-check-run misattribution it was built to prevent — with no error
to signal it. **This was confirmed myself, independently, before
accepting it**: reproduced the exact empty-variable-across-calls
behavior directly in this session's own shell, then reproduced the `jq`
empty-string comparison separately. Both true.

**Root cause and proper fix, not a patch:** a plain shell variable was
never the right mechanism to carry a value from Step 8.1 to Step 8.3 —
this mechanism already has a durable, git-committed, cross-invocation
store built for exactly this (`lrh-round-state`), and the fix uses it
instead. Added `retriggered_at` to the `pending_attempt` object in
`round-cap-gate.md`'s "State schema," written at batch start (Step 8.1,
via "Check-then-attempt ordering") as part of the same write that already
persists `pending_attempt`. "Detecting a stalled reviewer session" now
reads it back with `git show origin/lrh-round-state:.../<key>.json | jq
-r '.pending_attempt.retriggered_at'` at the top of Step 8.3 — verified
live against this PR's actual round-state file. `SKILL.md` Step 8.1's
prose updated to match: persist into the state file, not a bash
variable.

The same review separately found a real, if lower-severity, design
weakness: the timeline corroboration signal relied on timestamp
proximity alone to distinguish Copilot code-review events from
coding-agent events, when every such event actually carries
`.performed_via_github_app.slug` — verified live against both
`xenotaur/LCATS#202` (mixed: `copilot-pull-request-reviewer` and
`copilot-swe-agent` interleaved) and this PR (`copilot-pull-request-reviewer`
throughout) that the slug is 100% reliable, no exceptions. Filtering the
timeline query on slug (not just `$since`) closes a real gap: nothing
previously stopped an unrelated coding-agent event from landing inside
the same narrow time window as this batch's retrigger.

Also closed a minor gap the same review flagged: the 15-minute stall
threshold was asserted in prose only, with no actual age computation
shown. Added a concrete `AGE=$(( $(date +%s) - ... ))` snippet (GNU/BSD
`date` portability handled the same way "Round-state branch mechanics"
already does), verified live on this machine's own `date`.

Fixed and pushed as `662d6fb`.

**Third independent subagent review, dispatched cold** (told two prior
passes each found and fixed a real bug, instructed to find what they
missed rather than re-litigate). Found one more real, opposite-direction
mirror of the bug the second pass had just fixed, plus two minor
polish items.

**Real, confirmed:** `jq -r '.pending_attempt.retriggered_at'` on a
`null` `pending_attempt` (or one missing the field, e.g. written by an
older, pre-this-PR revision of the skill) prints the literal string
`"null"`, not empty — verified directly. Every real ISO-8601 timestamp
starts with a digit, and `'2' < 'n'` lexicographically, so
`.started_at >= "null"` is **false for every real check-run** —
verified directly (`jq -n --arg since "null" '"2026-08-01T10:00:00Z" >=
$since'` → `false`). This is the mirror image of the second pass's bug
from the *other* direction: an empty `$since` made the comparison true
for everything (over-matching, found a stale check-run); a literal
`"null"` `$since` makes it false for everything (under-matching, finds
nothing at all) — both reach the same fail-unsafe outcome, a genuinely
stalled reviewer reported as "no evidence invoked," just via opposite
mechanisms. Fixed: explicit guard right after reading `$SINCE` —
`if [ -z "$SINCE" ] || [ "$SINCE" = "null" ]; then` surface as a
data-integrity anomaly and `exit 1`, consistent with this document's
existing pattern for other anomalies (the PR-identity mismatch check in
"State schema"), rather than silently running a broken filter.

**Minor (2):** the AGE-computation snippet's own commentary claimed to
avoid "`||` masking which one actually ran" while the code directly
below it used exactly that `||` pattern — a real inconsistency, though
not a live bug: tested directly that BSD/macOS `date -d` fails hard
(non-zero exit), unlike the `stat -f`/`-c` ambiguity elsewhere in this
doc where GNU's `-f` silently produces wrong output instead of failing.
Fixed the prose to say why `||` is actually safe here, rather than
adding unneeded explicit detection to code that wasn't broken.

**Minor (3):** `$STARTED_AT` was referenced with no preceding
assignment. Fixed: the check-run query now captures its result into
`$CHECK_RUN`, and a guard (empty → never invoked; non-`in_progress` →
not stalled; else compute age from `$CHECK_RUN`'s own `.started_at`)
runs before the age computation — closes a real crash I hit myself while
testing the fix live: running the age snippet against a `completed`
check-run with no guard produced empty `$STARTED_AT` and a `date`
parse error.

All fixes verified live (match, zero-match, and terminal-status cases
for the check-run guard; both `$SINCE` anomaly cases for the new guard).
Mirrors identical, `lrh validate` clean, `scripts/format`/`lint`/`test`
all clean (808 tests).

**Final verdict: Green**, on `013bdf37a1bbea4892a5bd30461d293446ef949d`
— CI 5/5, 0 unresolved threads, mirrors identical, `lrh validate` clean.
Merge authorized in-session ("stop here and merge once you confirm") per
`DEC-AGENT-EXECUTED-MERGE-GATE`; executed
`gh pr merge --squash --match-head-commit 013bdf3...`. Squash-merged as
`5211e4027c7cd749f9ef3b98560be14e0e6d7202` at 2026-08-01T17:03:22Z.

CHAIN-NOTE: cycles=1; stops=7; gates=[merge]; friction="12 pushed
retrigger-batch rounds across confirm-fixes' Step 8 loop (ceiling
authorized 3→10 at one round-cap gate), plus 3 independent cold-subagent
review passes after the ceiling was reached instead of further bot
rounds — each of the 3 passes found and fixed a real, distinct bug the
prior state had missed, including two opposite-direction mirror-image
bugs in the same retrigger-timestamp-filtering mechanism (empty-string
`$since` matching every timestamp, then literal-string `\"null\"`
`$since` matching none) and a harness-level discovery (shell variables do
not survive across separate Bash tool calls) that no bot-review round
had caught in 8 prior rounds. Also self-caught a HEAD-race process error
mid-run (computed a Green verdict, then pushed a further commit
documenting it, invalidating the verdict against its own new HEAD) and
corrected course before presenting any merge command. Discovered a live
concurrent session already using this same PR's shared `lrh-round-state`
mechanism for two other open PRs (#453, #454) partway through, confirming
it works under genuine concurrent use rather than only in the
worked-through design."; note="Session hit a real interruption partway
through (computer sleep / MCP reconnect) and resumed cleanly with no work
lost, since all in-flight edits were already on disk, not just in
context. `project/design/backlog.md` gained two entries from this PR:
one on the round-cap-gate mechanism's own future architecture (promote
skill-prose to a tested LRH primitive), one on a remaining
Copilot-specific-vs-reviewer-generic framing gap deliberately deferred
at round 7's stopping point (fixed find/reply-only follow-up, not a
correctness bug)."

# Follow-up

- Done: merged as `5211e4027c7cd749f9ef3b98560be14e0e6d7202`, all 3
  execution records for this PR landed with the real commit SHA.
- `project/design/backlog.md`'s two entries from this PR ("Promote
  stalled-reviewer-session detection..." and "Stalled-reviewer-session
  detection is Copilot-specific but reads as reviewer-generic") remain
  open for future pickup — not resolved by this closeout.
