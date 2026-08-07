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
| **Primary record selection** | `grep pr: <url>` across `project/executions/`; exclude `*_REVIEW.md`, `*_CONFIRM.md`, `*_CLOSEOUT_NOTE.md`, `*_SELFREVIEW.md` from results |
| **Found-or-backfill** | Found → body is immutable; CHAIN-NOTE goes in a new `_CLOSEOUT_NOTE` record with `rerun_of:`. Not found → backfill record authored directly; CHAIN-NOTE in that record |
| **CHAIN-NOTE placement** | Always in the record being *authored* this run; never appended to an already-merged record body |
| **Main-worktree-lock** | When all worktrees have `main` checked out: `git fetch → checkout -b tmp-<slug> origin/main → apply changes → push tmp-<slug>:main → delete tmp-<slug>` |
| **Stale-branch safety** | Before reusing a planning-PR branch: `git diff origin/main <branch> --stat` must confirm zero net lines |

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
| `stops` | Number of times the chain halted before reaching completion, **including round-cap gate crossings** (see below) |
| `gates` | Human gates encountered, e.g. `[merge]` or `[merge, confirm]` |
| `friction` | Brief phrase describing the primary friction source, or `none` |
| `note` | Free text; record design findings, backfill path, noteworthy deviations, or **round-cap ceilings authorized this run** (see below) |
| `self_review_rounds` | Optional. Number of `/lrh-self-review` PR-mode passes substituted for a bot round in this run (see `round-cap-gate.md`'s "The three-way gate", fourth answer). Omit the field entirely when zero — do not write `self_review_rounds=0` to every CHAIN-NOTE. |
| `bot_rounds` | Optional, present only when `self_review_rounds` is also present. `completed_count - self_review_rounds` — **never** read directly from `round-cap-gate.md`'s `completed_count`, which is source-agnostic and counts both bot and self-review rounds identically; reading it straight would double-count self-review rounds as bot rounds. |

**Round-cap counter vs. `cycles`.** `/lrh-confirm-fixes` Step 8's round-cap
gate (`src/lrh/skills/lrh-confirm-fixes/references/round-cap-gate.md`)
counts bot-retrigger batches — a finer-grained, separate metric from
`cycles`, which counts whole review-response ↔ confirm-fixes iterations.
A single `cycles` count can span many round-cap batches (this is exactly
what happened on PR #442: `cycles=1` while the round-cap-relevant count
would have been 14). Do not conflate the two, and do not derive one from
the other.

Each time the round-cap gate blocks and the human is asked to authorize a
new ceiling, deny, or pause: count it toward `stops`, and record the
ceiling the human authorized (or "denied"/"paused") in `note`, e.g.
`note="round-cap: authorized ceiling 3->10"`.

Example:

```text
cycles=2; stops=0; gates=[merge]; friction=stale-review; note="Codex reviewed first commit only; second review pass required after rebase."
```

Example with a round-cap crossing:

```text
cycles=1; stops=1; gates=[merge]; friction=none; note="round-cap: authorized ceiling 3->10 after 3 real findings"
```

Example with a self-review substitution:

```text
cycles=1; stops=0; gates=[merge]; friction=none; self_review_rounds=1; bot_rounds=0; note="round-cap: substituted self-review for the only round this PR needed"
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

```bash
# $candidates: newline-separated list of files to classify (e.g. from
# `grep -rl "pr: <pr-url>" project/executions/`, or from the UPPER_SLUG
# `find` used by /lrh-confirm-fixes and /lrh-review-response)
slug_of() {
  grep '^execution_id:' "$1" | head -1 \
    | sed -E 's/^execution_id: *[0-9]{4}(_[0-9]{2}){5}_//'
}
all_slugs=$(grep -rh '^execution_id:' project/executions/ \
  | sed -E 's/^execution_id: *[0-9]{4}(_[0-9]{2}){5}_//')

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
        if grep -qxF "$base" <<< "$all_slugs"; then
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
ends in `_REVIEW`, base `WI_SKILLS_LRH_SELF` has no match →
`reserved_no_base`) and `.../WI_SKILLS_LRH_SELF_REVIEW_CONFIRM.md` (slug
ends in `_CONFIRM`, base `WI_SKILLS_LRH_SELF_REVIEW` matches the other
candidate's slug → `side`). Since `side` is non-empty, the
`reserved_no_base` candidate is correctly promoted to primary by
elimination. The doubled-collision case `ADOPT_PROP_LRH_SELF_REVIEW_REVIEW`
resolves the same way against its own sibling `ADOPT_PROP_LRH_SELF_REVIEW_CONFIRM`.
A simulated lone orphan (the same `WI_SKILLS_LRH_SELF_REVIEW.md` file
with no sibling candidates at all) correctly falls into `$ambiguous`
instead of being silently misclassified as primary — this is the exact
regression Codex's finding on PR #508 identified in an earlier draft of
this algorithm.

This still does not resolve every conceivable case — a PR with **only**
one orphaned side record and genuinely nothing else can never be
disambiguated from `execution_id` content alone, no matter how the
provenance check is written; that is a fundamental limit of inferring
provenance from naming rather than an explicit record-kind marker (a
schema change, out of this fix's scope — see
`project/design/backlog.md`). The fix here converts that unresolvable
case from a silent wrong answer into an explicit stop-and-ask, which is
the actionable improvement in scope.

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

After `WI-DELIBERATE-MODEL-INVOCATION` lands (which removes
`disable-model-invocation: true` from the lifecycle skills), upgrade Steps
4–7 to direct `Skill` tool calls. The upgrade is a one-step `SKILL.md` edit
per step and does not require a new PR or a WI of its own. Source:
`PROP-LRH-LAND-EXECUTE` Decision 7.
