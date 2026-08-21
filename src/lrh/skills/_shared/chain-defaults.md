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
confirmed_commit: null
confirmed_at: null
```

The two steelmanned default values (`completion_condition`,
`stop_work_condition`) are `PROP-LRH-CHAIN-DEFAULTS`'s "Steelmanned Defaults"
section, verbatim — do not paraphrase them when proposing.
`chain_init_confirmation` ships `always_confirm` by default;
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

## Decision 5 — gate-definition staleness fallback

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
  # skip_if_opted_in skip), check whether any gate-definition surface has
  # changed since the profile was last confirmed:
  git diff --quiet "$CONFIRMED_COMMIT" HEAD -- \
    src/lrh/skills/_shared/chain-defaults.md \
    src/lrh/skills/lrh-land/SKILL.md \
    src/lrh/skills/lrh-land/references/land-workflow.md \
    src/lrh/skills/lrh-execute/SKILL.md \
    src/lrh/skills/lrh-implement/SKILL.md \
    src/lrh/skills/lrh-review-response/SKILL.md \
    src/lrh/skills/lrh-confirm-fixes/SKILL.md \
    src/lrh/skills/lrh-confirm-fixes/references/confirm-fixes-workflow.md \
    src/lrh/skills/lrh-confirm-fixes/references/round-cap-gate.md \
    src/lrh/skills/lrh-self-review/SKILL.md \
    src/lrh/skills/lrh-closeout/SKILL.md \
    src/lrh/skills/lrh-closeout/references/closeout-workflow.md
fi
```

Exit status `1` means a gate-definition surface changed since the stored
confirmation. Per `DEC-GATE-POLICY-CASCADE`, inspect the diff for changes to
gate-definition statements: when a gate is reached, what payload is presented,
what reply or stored consent satisfies it, what special condition forces a live
gate, what downstream step may rely on it, or what action is forbidden without
it. If any such statement changed, treat this run as if
`chain_init_confirmation` were `always_confirm` regardless of the stored value,
and note this in the gate's presentation ("defaults pre-filled, but
re-confirming since gate policy changed since you last confirmed"). If the diff
is only non-semantic churn, document that inspection and continue. Exit status
greater than `1` means the diff command itself failed; surface the error and do
not classify it as a semantic gate-definition change. Do not silently rewrite
the stored value based on this fallback alone — it only affects this run's
liveness, not the persisted setting.

## Consuming sites

| Skill | Location |
|---|---|
| `/lrh-land` | `SKILL.md` Step 2, detail inlined in `references/land-workflow.md` |
| `/lrh-execute` | `SKILL.md` Step 2 — cross-references `/lrh-land`'s inlined copy in `references/land-workflow.md` rather than carrying its own third copy, since `/lrh-execute`'s Reference Knowledge already lists that file as loaded (it inlines all of `/lrh-land` at its own Step 4) |
