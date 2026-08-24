# Chain-Defaults Propose-and-Confirm Flow — Canonical Text

<!-- CANONICAL SOURCE: src/lrh/skills/_shared/chain-defaults.md
     This text is INLINED at each consuming site listed below, not mirrored
     into references/. If you change this flow, update every site in the
     table. See project/design/backlog.md's "Validator drift-check for
     synced skill references" entry — this file's inlined copies are the
     same class of synced-reference drift risk that entry already tracks,
     though it does not name this file specifically (it predates it). -->

This file defines Increment 1 of `PROP-LRH-CHAIN-DEFAULTS`: the
propose-and-confirm flow every chain-authorization gate (`/lrh-land` Step 2,
`/lrh-execute` Step 2) runs before eliciting completion/stop conditions from
scratch. It is maintainer-facing: `src/lrh/skills/_shared/` is skipped by the
installer, so nothing here is loaded at runtime directly — each consuming
site carries its own inlined copy.

---

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
either way.

**Re-stamp on a live-answered reconfirmation whose result matches what
ends up on disk, not only on the no-divergence case.** `confirmed_commit`/
`confirmed_at` record when a human last live-confirmed *the values that
are actually stored* (see the field description above) — so the re-stamp
condition is "the live reply and the persisted text now agree," not
merely "a live reply happened":

- **Reply matches the stored text (no divergence):** write
  `confirmed_commit: $(git rev-parse HEAD)` and
  `confirmed_at: $(date -u +%Y-%m-%dT%H:%M:%SZ)`. This is not a no-op:
  the human explicitly re-affirmed the current gate text, and that
  affirmation is exactly what `confirmed_commit` exists to record —
  previously nothing re-stamped here, which is the bug this section fixes.
- **Reply diverges and the human says yes to the Decision 4 profile-update
  offer:** the stored `completion_condition`/`stop_work_condition` are
  rewritten to the new wording, and — per the pre-existing Decision 4 text
  above — `confirmed_commit`/`confirmed_at` re-stamp together with that
  rewrite. The two actions are one unit: both happen, or neither does.
- **Reply diverges and the human says no (or the offer is never reached
  this run):** do **not** re-stamp. The text still on disk is not what the
  human just said — re-stamping here would misrepresent an unchanged,
  un-ratified value as freshly confirmed, exactly the failure mode Risk
  Notes warns against, just reached via a declined profile-update instead
  of a silent skip.

Do not silently rewrite the stored value based on the fallback's `exit 1`
signal *alone* — the "do not silently rewrite" caution applies to both the
no-live-reply case (not reachable via the path described above, since this
fallback always forces a live ask before this point, but the caution stays
precise for any future path that could reach staleness without one) and
the diverge-and-decline case just above; it does not apply once a live
reply has been given and left the persisted text matching that reply.

**Adding a new gate-bearing file or a new gate to an existing file requires
adding `<!-- GATE-DEFINITION -->` markers around its defining prose** (and,
if it's a new file, adding it to `DEFAULT_WATCHED_FILES`) — an unmarked gate
is invisible to this check by construction, the same failure shape as the
old under-watch defect, just scoped to one file instead of the whole
mechanism.
<!-- /GATE-DEFINITION -->

## Consuming sites

| Skill | Location |
|---|---|
| `/lrh-land` | `SKILL.md` Step 2, detail inlined in `references/land-workflow.md` |
| `/lrh-execute` | `SKILL.md` Step 2 — cross-references `/lrh-land`'s inlined copy in `references/land-workflow.md` rather than carrying its own third copy, since `/lrh-execute`'s Reference Knowledge already lists that file as loaded (it inlines all of `/lrh-land` at its own Step 4) |
