# /lrh-land Workflow Reference

This file is the algorithmic reference for `/lrh-land`. Load it at the
start of the skill (before Step 1) so all rule definitions are available
during execution.

---

## Five Glue-Logic Rules

These rules are applied as explicit algorithmic steps, not re-derived from
prose each run. Source: `PROP-LRH-LAND-EXECUTE` Decision 3.

| Logic | Rule |
|---|---|
| **Primary record selection** | `grep pr: <url>` across `project/executions/`; classify each match as primary/side/ambiguous via the provenance check (§ Primary vs. side-record provenance check below) — **not** a bare filename-suffix exclusion, which misclassifies a primary record whose own topic slug ends in a reserved word |
| **Found-or-backfill** | Found → body is immutable; CHAIN-NOTE goes in a new `_CLOSEOUT_NOTE` record with `rerun_of:`. Not found → backfill record authored directly; CHAIN-NOTE in that record |
| **CHAIN-NOTE placement** | Always in the record being *authored* this run; never appended to an already-merged record body |
| **Main-worktree-lock** | When all worktrees have `main` checked out: `git fetch → checkout -b tmp-<slug> origin/main → apply changes → push origin tmp-<slug>:main → checkout <pr-branch> (or --detach) → delete tmp-<slug>` — the explicit `origin` is required (a bare `tmp-<slug>:main` argument is parsed as a repository, not a refspec) and the checkout-away step is required because Git refuses to delete the branch `HEAD` currently points to |
| **Stale-branch safety** | Before reusing a planning-PR branch: `git diff origin/main <branch> --stat` must confirm zero net lines |

## Main-Worktree-Lock Troubleshooting

Addenda to the Main-worktree-lock rule above, not additional glue-logic
rules from `PROP-LRH-LAND-EXECUTE` Decision 3 — failure modes hit in
production and their resolution.

| Symptom | Resolution |
|---|---|
| **Non-fast-forward on push** | If `git push origin tmp-<slug>:main` is rejected as non-fast-forward, this usually means an unrelated commit landed on `main` concurrently — not a conflict with this run's own changes. Check: `git fetch origin main && git merge-base --is-ancestor <tmp-branch-parent> origin/main`. If it reports an ancestor, this is the clean-rebase case — `git rebase origin/main tmp-<slug>` and retry the push. Do not treat this as a stall or a policy block |
| **Ambiguous permission denial** | If a chained/compound Bash call (multiple git operations joined by `&&` in one tool call) is denied by the permission layer with wording that reads like a policy or gate block, do not conclude the underlying action (e.g. the push itself) is actually restricted. Retry the same action as a single, minimal command first — compound commands can be classified ambiguously independent of whether each individual command is itself safe |

**Multi-round review-response naming.** A single `/lrh-land` run can invoke
`/lrh-review-response` more than once (Step 4's loop). Each round reuses the
*same* slug — do not append a round-number suffix (e.g. `-round2`) to
disambiguate. `lrh prompt record-execution`'s timestamp prefix gives each
round a distinct filename in the normal case (it's second-resolution and
errors rather than overwrites on an exact collision), and every round's
`execution_id` still ends in the literal `_REVIEW` suffix. A round-numbered
suffix like `_REVIEW_ROUND2` breaks the primary-vs-side-record provenance
check below — it strips exactly the literal `_REVIEW`/`_CONFIRM`/
`_CLOSEOUT_NOTE`/`_SELFREVIEW` suffixes, so `_REVIEW_ROUND2` would not be
recognized as a side-record suffix at all, and a later `/lrh-land` re-run
could pick up that file as the primary record instead of excluding it. If
the round number needs to be recorded, put it in the record body or the
CHAIN-NOTE's `cycles` field, not the filename.

---

## CHAIN-NOTE Format

```text
cycles=<N>; stops=<N>; gates=[<gate-list>]; friction=<phrase or none>; note="<free text>"
```

Field definitions:

| Field | Description |
|---|---|
| `cycles` | Number of review-response → confirm-fixes iterations in this run |
| `stops` | Number of times the chain halted before reaching completion, **including no-progress review-cap stops** (see below) |
| `gates` | Human gates encountered, e.g. `[merge]` or `[merge, confirm]` |
| `friction` | Brief phrase describing the primary friction source, or `none` |
| `note` | Free text; record design findings, backfill path, noteworthy deviations, or **no-progress review-cap stops** (see below) |
| `self_review_rounds` | Optional. Number of `/lrh-self-review` PR-mode passes used as substitute review signals in this run. Omit the field entirely when zero — do not write `self_review_rounds=0` to every CHAIN-NOTE. |
| `bot_rounds` | Optional. Present only when a hosted review-bot round occurred outside this skill's manual workflow, such as an automatic first-push review or a human-reported external reviewer run. Do not infer or trigger bot rounds from `/lrh-confirm-fixes` Step 8. |

**No-progress cap vs. `cycles`.** `/lrh-confirm-fixes` Step 8's provisional
review cap (`src/lrh/skills/lrh-confirm-fixes/references/round-cap-gate.md`)
counts consecutive substitute self-review rounds that produce no actionable
progress — a finer-grained, separate metric from `cycles`, which counts whole
review-response ↔ confirm-fixes iterations. Do not conflate the two, and do
not derive one from the other.

Each time the no-progress review cap stops the chain and the human chooses
a different path: count it toward `stops`, and record the disposition in
`note`, e.g. `note="review-cap: stopped after 3 no-progress substitute reviews; human chose redesign"`.

Example:

```text
cycles=2; stops=0; gates=[merge]; friction=stale-review; note="Codex reviewed first commit only; second review pass required after rebase."
```

Example with a no-progress review-cap stop:

```text
cycles=1; stops=1; gates=[merge]; friction=stale-review; note="review-cap: stopped after 3 no-progress substitute reviews; human chose redesign"
```

Example with a self-review substitution:

```text
cycles=1; stops=0; gates=[merge]; friction=none; self_review_rounds=1; note="review-cap: substitute self-review clean"
```

---

## Found-or-Backfill Matrix

| Condition | Record action | CHAIN-NOTE location |
|---|---|---|
| Primary record found | Body is **immutable** — do not edit | New `_CLOSEOUT_NOTE` record; frontmatter must include `rerun_of: <primary-record-id>` |
| No primary record | Author a new backfill `AD_HOC` record in `project/executions/AD_HOC/` | Directly in the `# Result` section of the backfill record being authored |

A **primary record** is one whose `pr:` field matches the PR URL and whose
`execution_id` was not minted by a side-record-producing skill (Primary vs.
side-record provenance check below).

### Primary vs. side-record provenance check

A bare filename-suffix match (`grep -v "_REVIEW\.md$"` etc.) misclassifies
a primary record whose own topic slug happens to end in "review,"
"confirm," or "selfreview" — it self-excludes from the search, even though
no side-record-producing skill ever ran on it. This was hit live during
this project's own `PROP-LRH-SELF-REVIEW` and `WI-SKILLS-LRH-SELF-REVIEW`
landings (`feedback_lrh_land_step1_primary_record_substring_exclusion` in
agent memory) — both artifacts are themselves about "self-review," so
their own primary records' `execution_id`s end in `_SELF_REVIEW`, tripping
the exclusion glob meant for genuine `_REVIEW.md` side records.

The fix checks provenance instead of a bare suffix. `execution_id` is
`<timestamp>_<SLUG>`, and each record — primary or side — gets its own
fresh timestamp at creation time (`lrh prompt record-execution` stamps
`now()`), so a side record's full `execution_id` never equals its
primary's plus a suffix; only the `<SLUG>` portion carries the appending
relationship. Strip the leading timestamp first (`^[0-9]{4}(_[0-9]{2}){5}_`)
to get each record's `<SLUG>`, then compare slugs, not full IDs.

**Three-state classification, not a binary side/not-side test.** An
earlier draft of this fix classified any candidate as primary whenever
stripping its reserved suffix found no matching base slug anywhere —
but "no base found" is genuinely ambiguous on its own: it is produced
both by a primary record whose slug coincidentally ends in a reserved
word (the case this fix targets) *and* by an orphaned side record for a
PR that never got a `/lrh-implement` primary at all (`rerun_of` left
empty by design when "the PR was created outside `/lrh-implement`" — see
the `rerun_of` population rules in `/lrh-confirm-fixes` and
`/lrh-review-response`). These two situations are lexically
indistinguishable from `execution_id` alone; treating "no base" as
automatically primary silently picks the wrong answer in the orphan
case, attaching closeout state to a record that was never a primary
implementation record (caught in review on this WI's own PR, `chatgpt-codex-connector`
on PR #508). The corrected algorithm resolves this with **sibling
elimination**: classify every PR-matching candidate first, and only
treat a "no base" reserved-suffix candidate as primary when at least one
*other* candidate for the same PR is unambiguously a genuine side record
(has a base match) — proving a primary must exist for this PR to be the
"other" record review/confirm/self-review ran against. If no sibling can
prove that, the candidate is **ambiguous**, not primary — stop and ask
rather than guess.

**The base-slug proof must be scoped to this search's own candidates, not
the whole repository.** An earlier draft looked up the stripped base slug
against every `execution_id` under `project/executions/`, repo-wide —
caught in review (Codex, P1, PR #508) as its own false-positive risk in
the opposite direction: two entirely unrelated work items whose primaries
happen to be named `FOO` and `FOO_REVIEW` would make the repo-wide lookup
"prove" `FOO_REVIEW` is a side record of `FOO`, even though no
side-record-producing skill ever ran on it and the two share no actual
relationship. Since a genuine side record's base is always among this
search's own gathered `$candidates` (that is what makes it a sibling —
see "sibling elimination" above), scoping the lookup to `$candidates`
itself gives the same correct answer for every real case (below) while
closing the cross-project false-positive — important since this harness
is installed into independent client repositories with their own,
potentially much smaller, naming schemes (`AGENTS.md`).

```bash
# $candidates: newline-separated list of files to classify (e.g. from
# `grep -rl "pr: <pr-url>" project/executions/`, or from the UPPER_SLUG
# `find` used by /lrh-confirm-fixes and /lrh-review-response)
slug_of() {
  grep '^execution_id:' "$1" | head -1 \
    | sed -E 's/^execution_id: *[0-9]{4}(_[0-9]{2}){5}_//'
}
candidate_slugs=""
while IFS= read -r f; do
  [ -z "$f" ] && continue
  candidate_slugs="${candidate_slugs:+$candidate_slugs$'\n'}$(slug_of "$f")"
done <<< "$candidates"

side=""; reserved_no_base=""; unsuffixed=""
while IFS= read -r f; do
  [ -z "$f" ] && continue
  slug=$(slug_of "$f")
  matched=false
  for suf in _REVIEW _CONFIRM _CLOSEOUT_NOTE _SELFREVIEW; do
    case "$slug" in
      *"$suf")
        matched=true
        base="${slug%$suf}"
        if grep -qxF "$base" <<< "$candidate_slugs"; then
          side="${side:+$side$'\n'}$f"
        else
          reserved_no_base="${reserved_no_base:+$reserved_no_base$'\n'}$f"
        fi
        ;;
    esac
  done
  if [ "$matched" = false ]; then
    unsuffixed="${unsuffixed:+$unsuffixed$'\n'}$f"
  fi
done <<< "$candidates"

if [ -n "$unsuffixed" ]; then
  primary="$unsuffixed"; ambiguous=""
elif [ -n "$reserved_no_base" ]; then
  if [ -n "$side" ]; then
    primary="$reserved_no_base"; ambiguous=""
  else
    primary=""; ambiguous="$reserved_no_base"
  fi
else
  primary=""; ambiguous=""
fi
```

`$primary` is the result to use when non-empty (found path). `$ambiguous`
being non-empty means: stop and ask the human whether a primary
implementation record ever existed for this PR, rather than silently
choosing found or backfill — do not fall through to the backfill path
automatically, since that path also assumes "no primary exists" as a
confirmed fact, not a guess.

Verified against this repo's own real collision case (PR #464,
`WI-SKILLS-LRH-SELF-REVIEW`): candidates are
`.../WI_SKILLS_LRH_SELF_REVIEW.md` (slug `WI_SKILLS_LRH_SELF_REVIEW`,
ends in `_REVIEW`, base `WI_SKILLS_LRH_SELF` has no match within
`$candidate_slugs` → `reserved_no_base`) and
`.../WI_SKILLS_LRH_SELF_REVIEW_CONFIRM.md` (slug ends in `_CONFIRM`, base
`WI_SKILLS_LRH_SELF_REVIEW` matches the other candidate's slug → `side`).
Since `side` is non-empty, the `reserved_no_base` candidate is correctly
promoted to primary by elimination. The doubled-collision case
`ADOPT_PROP_LRH_SELF_REVIEW_REVIEW` resolves the same way against its own
sibling `ADOPT_PROP_LRH_SELF_REVIEW_CONFIRM`. A real orphan case (PR #347,
`.../WI_TEST_LAYOUT_SUBDIRECTORY_CONVENTION_REVIEW.md`, the sole
`project/executions/` record for that PR, cited directly by Copilot's own
finding on PR #508) correctly falls into `$ambiguous` instead of being
silently misclassified as primary — this is the regression Codex's and
Copilot's findings on PR #508 identified in an earlier draft of this
algorithm. Codex's follow-up finding on the same PR — restricting the
base-slug proof to `$candidate_slugs` rather than every `execution_id` in
the repository — is also verified directly: isolating
`.../WI_SKILLS_LRH_SELF_REVIEW.md` with no sibling candidates (simulating
an unrelated primary elsewhere in the repo that happens to match its base
slug) now correctly falls into `$ambiguous` rather than being
misclassified as a side record of that unrelated primary.

This still does not resolve every conceivable case — a PR with **only**
one orphaned side record and genuinely nothing else can never be
disambiguated from `execution_id` content alone, no matter how the
provenance check is written; that is a fundamental limit of inferring
provenance from naming rather than an explicit record-kind marker (a
schema change, out of this fix's scope — see
`project/design/backlog.md`). The fix here converts that unresolvable
case from a silent wrong answer into an explicit stop-and-ask, which is
the actionable improvement in scope.

### A separate, narrower algorithm for the two slug-based `rerun_of` searches

`/lrh-land` Step 1 gathers `$candidates` by an exact `pr:` field match —
every candidate is already known to belong to the PR being searched, and
the target primary is *unknown in advance* (any of several candidates
could be it), so classifying every candidate and picking the survivor,
as the algorithm above does, is the right shape.

`/lrh-confirm-fixes`'s and `/lrh-review-response`'s `rerun_of` searches
are a different problem: the target's slug is *known in advance*
(`UPPER_SLUG`, derived directly from the branch name) — the question is
only "does a genuine primary record with exactly this slug exist, and is
it safe to treat as primary." Reusing the classify-every-candidate
algorithm above for this case was tried twice and broke twice:

- **Round 3** gathered candidates with a bare substring glob
  (`*${UPPER_SLUG}*.md`), which can pull in an unrelated, longer-named
  work item's own record — e.g. branch slug `WI_FOO` matching an
  unrelated `WI_FOOBAR_REVIEW.md` (caught by Copilot).
- **The fix attempted for that** — narrowing the glob to a trailing-exact
  match (`*_${UPPER_SLUG}.md`) — creates its own regression when
  `UPPER_SLUG` itself ends in a reserved suffix: a genuine sibling's slug
  is always `UPPER_SLUG` *plus* a suffix, so it can never also end in
  exactly `_${UPPER_SLUG}.md`. `$candidates` collapses to one file with no
  sibling to prove it isn't an orphan, and the classify-every-candidate
  algorithm's `unsuffixed` branch — first-priority, no further checks —
  can also seize the primary slot for an unrelated but still-matching
  substring candidate before any exact-match filter even runs. Both
  failure modes were caught live on this PR's own review (round 3 fixing
  the substring glob without solving the sibling problem; a
  `/lrh-self-review` PR-mode pass, round 4, catching the resulting
  regression by hand-tracing `WI_SKILLS_LRH_SELF_REVIEW.md` against its
  real `_CONFIRM` sibling and finding the corrected-looking fix actually
  couldn't find it anymore).

The algorithm that actually works: gather candidates broadly (substring
glob, so a genuine sibling is never excluded from the evidence pool), but
only ever classify **the one candidate whose slug exactly equals
`UPPER_SLUG`** — everything else in the pool is evidence only, never a
competing primary candidate:

```bash
UPPER_SLUG=<derived-from-branch-slug>
candidates=$(find project/executions/ -name "*${UPPER_SLUG}*.md")

target=""
while IFS= read -r f; do
  [ -z "$f" ] && continue
  [ "$(slug_of "$f")" = "$UPPER_SLUG" ] && target="${target:+$target$'\n'}$f"
done <<< "$candidates"

primary=""; ambiguous=""
if [ -n "$target" ]; then
  matched=false; is_side=false
  for suf in _REVIEW _CONFIRM _CLOSEOUT_NOTE _SELFREVIEW; do
    case "$UPPER_SLUG" in
      *"$suf")
        matched=true
        base="${UPPER_SLUG%$suf}"
        while IFS= read -r f; do
          [ -z "$f" ] && continue
          [ "$(slug_of "$f")" = "$base" ] && is_side=true
        done <<< "$candidates"
        ;;
    esac
  done
  if [ "$matched" = false ]; then
    primary="$target"
  elif [ "$is_side" = false ]; then
    has_sibling_side=false
    while IFS= read -r f; do
      [ -z "$f" ] && continue
      slug=$(slug_of "$f")
      [ "$slug" = "$UPPER_SLUG" ] && continue
      for suf in _REVIEW _CONFIRM _CLOSEOUT_NOTE _SELFREVIEW; do
        case "$slug" in
          *"$suf")
            [ "${slug%$suf}" = "$UPPER_SLUG" ] && has_sibling_side=true
            ;;
        esac
      done
    done <<< "$candidates"
    if [ "$has_sibling_side" = true ]; then
      primary="$target"
    else
      ambiguous="$target"
    fi
  fi
  # else: $UPPER_SLUG's own base exists in the pool, meaning the target
  # is itself a genuine side record of something else — not primary, and
  # not meaningfully "ambiguous" either; primary/ambiguous both stay empty.
fi
```

This resolves both prior failures simultaneously: the substring glob
means a genuine sibling is always available as evidence when `UPPER_SLUG`
itself ends in a reserved suffix (fixes the round-4 regression), and only
the exact-slug `target` is ever eligible to become `primary` — an
unrelated longer-slug candidate pulled in by the substring glob can only
ever serve as sibling evidence, never seize the primary slot (fixes
Copilot's round-3 concern) — without needing a post-hoc filter that can
be defeated by an unrelated candidate's own `unsuffixed` classification
racing ahead of it, which is exactly how the first attempt at this fix
broke.

Verified directly against this repo's own data: for `UPPER_SLUG =
WI_SKILLS_LRH_SELF_REVIEW` (own slug ends in `_REVIEW`), the substring
glob returns six candidates including the genuine sibling
`WI_SKILLS_LRH_SELF_REVIEW_CONFIRM.md` — `has_sibling_side` finds it,
`target` is correctly promoted to `primary`. For the doubled-collision
case `ADOPT_PROP_LRH_SELF_REVIEW` (sibling
`ADOPT_PROP_LRH_SELF_REVIEW_CONFIRM`), same result. For the PR #347 real
orphan (`WI_TEST_LAYOUT_SUBDIRECTORY_CONVENTION_REVIEW`, no sibling in
the pool), `target` correctly falls to `ambiguous`. For a `UPPER_SLUG`
with no exact-match candidate at all (simulating Copilot's unrelated
longer-slug concern), `target` is empty and `primary` stays empty
regardless of what else the substring glob happened to pull in.

A `_CLOSEOUT_NOTE` record must be placed in the same execution directory
bucket as the primary record (e.g., `project/executions/WI-FOO/` if the
primary is there, not `AD_HOC/`).

---

## Run Journal Skeleton

The run journal is a prototype scratchpad file (not committed to the repo).
Append one entry per `/lrh-land` invocation. Minimum shape from
`PROP-LRH-LAND-EXECUTE` Decision 8:

```yaml
run_id: <datetime-slug>
node: <WS-ID or WI-ID associated with this PR, or AD_HOC>
completion_condition: <user-provided at Step 2>
stop_work_condition: <user-provided at Step 2>
actions:
  - type: land_pr
    wi: <WI-ID or AD_HOC>
    prompt_id: <PROMPT(...)>
    pr: <pr-url>
    result: merged | stopped
    chain_note: <one-line CHAIN-NOTE text>
findings:
  - <gap or observation surfaced during this run>
```

Store the journal at: `<scratchpad>/lrh-land-run-journal.yaml`

The `<scratchpad>` path is the session scratchpad directory reported at the
start of the Claude Code session.

---

## Interim Invocation Pattern

Steps 4–7 in Phase 1 inline the sub-skill workflows: read the target
`SKILL.md` and execute its steps directly within the current session. This
avoids requiring `WI-DELIBERATE-MODEL-INVOCATION` to land before `/lrh-land`
can ship.

Sub-skills to inline per step:

| Step | Sub-skill to inline |
|---|---|
| Step 4 (review-response) | `/lrh-review-response/SKILL.md` |
| Step 5 (confirm-fixes) | `/lrh-confirm-fixes/SKILL.md` |
| Step 7 (closeout) | `/lrh-closeout/SKILL.md` |

**`WI-DELIBERATE-MODEL-INVOCATION` resolved this as permanent, not interim.**
Per that work item's Design Decision, chain-runner invocation mechanics stay
inlined by design (self-contained, independently testable chain runners) —
removing flags from the lifecycle skills does not trigger an upgrade to
direct `Skill` tool calls. `PROP-LRH-LAND-EXECUTE` Decision 7's original
upgrade plan is superseded by that resolution. The inlining rule is a settled
chain-runner design preference, not a workaround for any one sub-skill's
frontmatter.

**Step 5's CI-wait mechanism is inherited via this inlining, not separately
specified here.** `/lrh-land` has no CI-check logic of its own — Step 5
inlines the whole of `/lrh-confirm-fixes/SKILL.md`, so whatever CI-wait
mechanism that skill's own Step 8 uses (the bounded background-poll loop
in `lrh-confirm-fixes/references/confirm-fixes-workflow.md` § Bounded
background-poll wait) applies here automatically once that step runs.
`/lrh-land` Step 4's own "wait and re-check" note (§ Step 4 above) and the
"Re-run REVIEW-LANDED... sufficient time to run" passage near Step 5/6 are
a **different** predicate — waiting on the automatic first-push bot
response, not CI — and remain deliberately unspecified; that gap is
out of scope for the CI-wait work this note describes, deferred to Stage
4 per `PROP-INVOCATION-AND-GATE-RESET`'s own Non-Goals.


## Chain-defaults propose-and-confirm flow

<!-- INLINED from src/lrh/skills/_shared/chain-defaults.md — update both if this changes. -->

## Profile file

`project/config/chain-defaults.yaml`, repo-level and git-tracked (Decision 1
of `PROP-LRH-CHAIN-DEFAULTS`):

```yaml
completion_condition: "PR merged, its execution records landed, and any linked work item resolved."
stop_work_condition: "Any failing CI check, a reviewer finding that isn't Clear-satisfied on re-verification, or an ambiguous/refused merge-authorization reply."
chain_init_confirmation: always_confirm
closeout_with_merge: true
confirm_fixes_batch: always_confirm
confirmed_commit: null
confirmed_at: null
```

The two steelmanned default values (`completion_condition`,
`stop_work_condition`) are `PROP-LRH-CHAIN-DEFAULTS`'s "Steelmanned Defaults"
section, verbatim — do not paraphrase them when proposing.
`chain_init_confirmation` ships `always_confirm` by default;
reaching `skip_if_opted_in` requires the two-step consent below.
`closeout_with_merge` records that the merge-plus-closeout single ask
(`/lrh-land` Step 6) is the shipped, unconditional behavior — per
`DEC-SINGLE-ASK-RUN-GATES` rule 5 and `WI-LRH-CHAIN-DEFAULTS-INCREMENT-3`,
this is not a user-facing toggle; it is stored so the field exists on the
same schema Increment 1 established (for staleness-tracking symmetry with
`chain_init_confirmation`) and so a future decision to make it optional has
a field to attach to, not because `/lrh-land` branches on its value today.
`confirm_fixes_batch` ships `always_confirm` by default, same as
`chain_init_confirmation` — reaching `auto_unless_unusual` is a repo-level
opt-in edit to this file (a visible, revertible commit; it does not require
the separate git-config consent below, since that two-step mechanism is
specific to the chain-initiation gate per `PROP-LRH-CHAIN-DEFAULTS`
Decision 6, not generalized to every per-gate autopilot flag). See
`/lrh-confirm-fixes`'s own Step 2 and Step 4 for the gate-owned
`auto_unless_unusual` predicate (`WI-LRH-CHAIN-DEFAULTS-INCREMENT-2`,
`src/lrh/confirm_fixes_batch.py`), which this file does not restate.
`confirmed_commit`/`confirmed_at` record when a human last live-confirmed
these exact values (Decision 5 staleness fallback below); editing this file
to change `confirm_fixes_batch` (or any other field) invalidates any
previously-granted `skip_if_opted_in` git-config consent, since that
consent is bound to this file's exact blob hash — re-grant it after
confirming the new values if `skip_if_opted_in` is in use.

<!-- GATE-DEFINITION -->
## Propose-and-confirm flow

At the chain-authorization gate, before eliciting conditions from scratch:

```bash
cat project/config/chain-defaults.yaml 2>/dev/null
```

**File absent, or present with `confirmed_commit: null` (never live-confirmed
yet — the shipped file starts this way):** propose the steelmanned defaults
above (from the file if present, otherwise the hardcoded steelmanned text)
as the initial values. Present them to the user exactly as
`/lrh-land`/`/lrh-execute` Step 2 already do (planned chain + completion
condition + stop-work condition), pre-filled with this text instead of
inventing new wording. Wait for explicit confirmation, same as today — never
skip the live reply here, regardless of `chain_init_confirmation`'s stored
value, since `skip_if_opted_in` requires the two-step consent in the next
section, and that consent cannot yet exist for values nobody has ever
live-confirmed. On confirmation, write the file with
`confirmed_commit: $(git rev-parse HEAD)` and
`confirmed_at: $(date -u +%Y-%m-%dT%H:%M:%SZ)`. Do not run the staleness
check (below) in this case — there is nothing to compare `confirmed_commit`
against yet.

**File present with a non-null `confirmed_commit`:** run the staleness check
(below) first. If not stale,
pre-fill the gate's proposed conditions from the stored `completion_condition`
and `stop_work_condition` values rather than re-deriving them. Then branch on
`chain_init_confirmation`:

- **`always_confirm` (default):** still present the pre-filled conditions and
  require one live confirming reply per run, exactly as today — the only
  change from pre-Increment-1 behavior is that the proposed text is now
  pulled from the stored profile instead of freshly invented each time.
- **`skip_if_opted_in`:** check user-local skip consent (below). If valid
  (hash matches, no special condition fires), proceed without a live reply
  for the conditions — but still *display* what's being used, so the run is
  never silent about what it's operating under. If consent is invalid,
  missing, or a special condition fires, fall back to the `always_confirm`
  path for this run only (do not overwrite the stored `chain_init_confirmation`
  value).

If the user's live reply diverges from the stored values (wording changed,
not just re-confirmed), apply the **Decision 4 profile-update offer**: at
the end of the run, ask "Update the stored default to match?" — never
silently persist a one-off override. Only rewrite the file on explicit yes,
and re-stamp `confirmed_commit`/`confirmed_at`.

## `skip_if_opted_in` — the five requirements (`DEC-CHAIN-INIT-SKIP-CONSENT`) plus the Stage 3.5 compensating control (`DEC-GATE-POLICY-CASCADE`)

1. **Initiation act preserved** — no special handling needed: the human's own
   `/lrh-land <pr>` / `/lrh-execute <target>` invocation is what starts this
   flow at all: skip mode never fires without that.
2. **Two separate affirmative actions** — storing the profile (above) is
   action (a). Action (b) is a distinct grant, never implied by (a):
   ```bash
   git config --local lrh.chainDefaults.skipConsentHash "$(git hash-object project/config/chain-defaults.yaml)"
   ```
   Only run this on an explicit, separate user instruction to opt into
   skip mode — never as a side effect of confirming or storing defaults.
3. **User-local storage only** — the command above is deliberately
   `git config --local`, which writes to `.git/config` (never committed,
   never shared via the git-tracked profile file). Never write skip
   consent into `project/config/chain-defaults.yaml` or any other
   git-tracked location.
4. **Value-hash binding** — validity check before trusting skip mode:
   ```bash
   STORED_HASH="$(git config --local --get lrh.chainDefaults.skipConsentHash 2>/dev/null || true)"
   CURRENT_HASH="$(git hash-object project/config/chain-defaults.yaml)"
   [ -n "$STORED_HASH" ] && [ "$STORED_HASH" = "$CURRENT_HASH" ]
   ```
   A mismatch (or unset `STORED_HASH`) means the consent does not cover the
   profile's current values — fall back to `always_confirm` for this run.
   The profile-update offer (Decision 4) naturally invalidates a stale
   consent this way, since updating the file changes its blob hash.
5. **Special-conditions check, unconditional even in skip mode:**
   - an unmet `depends_on` (the caller's own dependency-resolution step,
     e.g. `/lrh-execute` Step 1, already surfaces this — re-check it applies
     here too);
   - a prior failed or stopped run on the same PR/WI (check the scratch run
     journal's last entry, or an execution record with a `stopped`/`failed`
     status, for this target);
   - uncommitted stray changes: `git status --porcelain` non-empty;
   - a target mismatch: the resolved PR/WI does not match what a reasonable
     reading of the stored profile's context would expect (e.g. confirming
     you're still in the same repository the profile was confirmed in).

   Any hit forces the full `always_confirm` path for this run, regardless of
   stored `chain_init_confirmation` or valid consent.
6. **`human_initiated_invocation_evidence` (`DEC-GATE-POLICY-CASCADE` Decision
   4) — additional to requirements 1–5 above, not a replacement for any of
   them; all must hold together for skip mode to apply.** Before
   `skip_if_opted_in` may be used for a run, verify and record all of:
   - the run began from a live user message that explicitly invoked this
     chain skill and named the target PR, WI, or WS being run;
   - the resolved run target (from Step 1's resolution) matches that named
     target exactly;
   - no model-initiated `Skill()` call or sibling skill handoff is being
     treated as the human-initiation act for this run;
   - local skip consent exists and is bound to the exact current
     `project/config/chain-defaults.yaml` blob hash (requirement 4 above);
   - no special condition from requirement 5 above fired.

   Missing UI transcript access to confirm the live user message, an
   ambiguous target, a model-initiated handoff, a missing or mismatched
   consent hash, or any special-condition hit means this evidence is
   unavailable for this run. **This does not block the run — it falls back
   to the `always_confirm` path for this run only**, exactly as an
   invalid/missing consent already does under requirement 4. This
   requirement activates the mechanism `skip_if_opted_in` describes above;
   before it was wired in here, a user who had validly completed the
   two-step consent (requirements 1–5) would still have had no live check
   that this specific run was genuinely human-initiated rather than a
   model-initiated invocation riding stored consent.

## Decision 5 — gate-definition staleness fallback (semantic, `WI-LRH-CHAIN-DEFAULTS-INCREMENT-3`)

**Redesigned from file-granular to semantic**, per
`PROP-INVOCATION-AND-GATE-RESET` Decision 9. The original version invalidated
stored consent on *any* diff to a whole watched file — a typo fix and a gate
redesign were indistinguishable (over-watch) — and never watched
`/lrh-land`'s own inlined `/lrh-confirm-fixes`, `/lrh-review-response`, or
`/lrh-closeout` at all (under-watch), so a real change to any of their gates,
including this same increment's own `closeout_with_merge` behavior, would not
have invalidated consent even though it materially changed what the human
consented to.

The replacement watches gate-*definition* prose specifically: each
gate-bearing skill file marks the paragraphs that actually define a gate
(when it's reached, what's presented, what satisfies it, what special
condition forces it live, what relies on it, what's forbidden without it —
`PROP-LRH-GATE-POLICY` Decision 6's six categories) with
`<!-- GATE-DEFINITION -->` / `<!-- /GATE-DEFINITION -->` markers. A diff that
touches lines outside every marked region (a typo, a comment, reordered
unrelated prose) does not invalidate consent; a diff that touches even one
line inside a marked region does. See `src/lrh/gate_staleness.py` for the
implementation and `tests/gate_staleness_test.py` for the acceptance-criteria
case (a typo-only edit must not invalidate; a gate-definition edit must).

**Only applies once `confirmed_commit` is non-null** — the
propose-and-confirm flow above already routes a null/absent
`confirmed_commit` to the first-encounter path, which skips this section
entirely:

```bash
CONFIRMED_COMMIT="$(grep '^confirmed_commit:' project/config/chain-defaults.yaml | sed 's/^confirmed_commit: *//; s/^"//; s/"$//')"
if [ "$CONFIRMED_COMMIT" = "null" ] || [ -z "$CONFIRMED_COMMIT" ]; then
  echo "No prior confirmation on record — staleness check does not apply; use the first-encounter path above." >&2
else
  lrh chain-defaults check-staleness --confirmed-commit "$CONFIRMED_COMMIT" --project-root .
fi
```

The watched files (`lrh.gate_staleness.DEFAULT_WATCHED_FILES`) are the four
originally watched files, the three previously under-watched skills
`/lrh-land` inlines (`/lrh-confirm-fixes`, `/lrh-review-response`,
`/lrh-closeout`), and three reference files carrying real gate-defining
prose of their own that predate this increment's watch list but were never
covered by it either — `/lrh-implement`'s Step 4 plan-confirm gate (inlined
by `/lrh-execute`, not duplicated in `land-workflow.md`), the substitute
self-review round-cap gate, and the WS exit-criteria confirmation gate:

```
src/lrh/skills/_shared/chain-defaults.md
src/lrh/skills/lrh-land/SKILL.md
src/lrh/skills/lrh-land/references/land-workflow.md
src/lrh/skills/lrh-execute/SKILL.md
src/lrh/skills/lrh-implement/SKILL.md
src/lrh/skills/lrh-confirm-fixes/SKILL.md
src/lrh/skills/lrh-confirm-fixes/references/round-cap-gate.md
src/lrh/skills/lrh-review-response/SKILL.md
src/lrh/skills/lrh-closeout/SKILL.md
src/lrh/skills/lrh-closeout/references/closeout-workflow.md
```

`src/lrh/skills/lrh-confirm-fixes/references/confirm-fixes-workflow.md` and
`src/lrh/skills/lrh-self-review/SKILL.md` were checked and contain no gate
*definitions* of their own (`confirm-fixes-workflow.md`'s "Idempotency and
re-run edge cases" section restates the empty-thread gate in prose — "that
gate is the human checkpoint that replaced the old ungated fast path" — but
the normative definition lives solely in `lrh-confirm-fixes/SKILL.md`'s
marked region, so this file's own edits cannot change what the gate does;
`lrh-self-review` has no live in-session gate at all — its report-vs-apply
choice is a flag decided at invocation, not something a stored consent could
skip) — they are deliberately not watched, not an oversight. If a future
edit to `confirm-fixes-workflow.md` ever states something about the gate
that contradicts the marked definition, that is a doc-consistency bug to
fix directly, not evidence this file needs its own markers.

Exit status `1` means a gate-definition region changed (`stale: true` in the
output — one or more `stale files` entries name which file and why). A
watched file added or removed since confirmation counts as stale too (its
`reason` says so explicitly) — it is a data outcome (exit `1`), not a check
failure. Treat this run as if `chain_init_confirmation` were `always_confirm`
regardless of the stored value, and note this in the gate's presentation
("defaults pre-filled, but re-confirming since gate policy changed since you
last confirmed"). Exit status `0` (`stale: false`) means every diff since
confirmation, if any, fell outside all marked regions — continue trusting the
stored value. Exit status `2` means the check itself could not run at all —
an invalid or unresolvable `confirmed_commit`/`--head`, a git error, or a
malformed markers structure (see the command's own error text) — and is
distinct from a stale result; surface it and do not silently classify it
either way. Do not silently rewrite the stored value based on this fallback
alone — it only affects this run's liveness, not the persisted setting.

**Adding a new gate-bearing file or a new gate to an existing file requires
adding `<!-- GATE-DEFINITION -->` markers around its defining prose** (and,
if it's a new file, adding it to `DEFAULT_WATCHED_FILES`) — an unmarked gate
is invisible to this check by construction, the same failure shape as the
old under-watch defect, just scoped to one file instead of the whole
mechanism.
<!-- /GATE-DEFINITION -->
