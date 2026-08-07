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
file still ends in the literal `_REVIEW.md`. A round-numbered suffix like
`_REVIEW_ROUND2.md`
breaks the primary-record-selection exclusion above (`grep -v "_REVIEW\.md$"`
only matches the literal suffix) — a later `/lrh-land` re-run could pick up
that file as the primary record instead of excluding it. If the round number
needs to be recorded, put it in the record body or the CHAIN-NOTE's `cycles`
field, not the filename.

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

A **primary record** is one whose filename does NOT end with `_REVIEW.md`,
`_CONFIRM.md`, `_CLOSEOUT_NOTE.md`, or `_SELFREVIEW.md`, and whose `pr:`
field matches the PR URL.

**Known limitation, not fixed by this exclusion list:** these are bare
filename-suffix matches, not a check for the actual slug-suffix
convention that produces them. A primary record whose own topic slug
happens to end in "review," "confirm," or "selfreview" self-excludes from
this search — verified live during this project's own `PROP-LRH-SELF-REVIEW`
and `WI-SKILLS-LRH-SELF-REVIEW` landings
(`feedback_lrh_land_step1_primary_record_substring_exclusion` in agent
memory). Cross-check with a plain `find` before trusting an empty result
when the target topic's own name plausibly ends in one of these words.

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


## Chain-defaults propose-and-confirm flow

<!-- INLINED from src/lrh/skills/_shared/chain-defaults.md — update both if this changes. -->

## Profile file

`project/config/chain-defaults.yaml`, repo-level and git-tracked (Decision 1
of `PROP-LRH-CHAIN-DEFAULTS`):

```yaml
completion_condition: "PR merged, its execution records landed, and any linked work item resolved."
stop_work_condition: "Any failing CI check, a reviewer finding that isn't Clear-satisfied on re-verification, or an ambiguous/refused merge-authorization reply."
self_review_preference: substitute_self_review
chain_init_confirmation: always_confirm
confirmed_commit: null
confirmed_at: null
```

The three steelmanned default values (`completion_condition`,
`stop_work_condition`, `self_review_preference`) are `PROP-LRH-CHAIN-DEFAULTS`'s
"Steelmanned Defaults" section, verbatim — do not paraphrase them when
proposing. `chain_init_confirmation` ships `always_confirm` by default;
reaching `skip_if_opted_in` requires the two-step consent below.
`confirmed_commit`/`confirmed_at` record when a human last live-confirmed
these exact values (Decision 5 staleness fallback below).

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

## `skip_if_opted_in` — the five requirements (`DEC-CHAIN-INIT-SKIP-CONSENT`)

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

## Decision 5 — staleness fallback

**Only applies once `confirmed_commit` is non-null** — the
propose-and-confirm flow above already routes a null/absent
`confirmed_commit` to the first-encounter path, which skips this section
entirely. Do not run this section's `git diff` against the literal string
`"null"` as if it were a commit SHA — that fails hard
(`fatal: bad revision 'null'`), so guard for it explicitly even if this
section is read or executed in isolation from the flow above:

```bash
CONFIRMED_COMMIT="$(grep '^confirmed_commit:' project/config/chain-defaults.yaml | sed 's/^confirmed_commit: *//; s/^"//; s/"$//')"
if [ "$CONFIRMED_COMMIT" = "null" ] || [ -z "$CONFIRMED_COMMIT" ]; then
  echo "No prior confirmation on record — staleness check does not apply; use the first-encounter path above." >&2
else
  # Before trusting any stored value (always_confirm pre-fill or
  # skip_if_opted_in skip), check whether the gate's own skill logic has
  # changed materially since the profile was last confirmed:
  git diff --quiet "$CONFIRMED_COMMIT" HEAD -- \
    src/lrh/skills/lrh-land/SKILL.md \
    src/lrh/skills/lrh-land/references/land-workflow.md \
    src/lrh/skills/lrh-execute/SKILL.md \
    src/lrh/skills/_shared/chain-defaults.md
fi
```

A non-zero exit (files changed) means the stored confirmation predates a
skill-logic change it was never evaluated against — treat this run as if
`chain_init_confirmation` were `always_confirm` regardless of the stored
value, and note this in the gate's presentation ("defaults pre-filled, but
re-confirming since the skill logic changed since you last confirmed").
Do not silently rewrite the stored value based on this fallback alone — it
only affects this run's liveness, not the persisted setting.

