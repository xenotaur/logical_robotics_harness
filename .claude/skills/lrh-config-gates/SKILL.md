---
name: lrh-config-gates
description: >
  Inspect and change the chain-defaults gate policy in
  project/config/chain-defaults.yaml. Presents the 4 human-decidable fields
  (chain_init_confirmation, confirm_fixes_batch, completion_condition,
  stop_work_condition), closeout_with_merge shown read-only, the local
  git-config skip-consent hash's validity, and the gate-definition staleness
  status -- all in one read, via `lrh chain-defaults status` -- before asking
  anything. Field-value changes and the separate skip-consent grant each
  require their own explicit confirm; a consent grant is never bundled into
  or implied by a field-value confirm. Use instead of manually running
  `git config --get`, `git hash-object`, `lrh chain-defaults check-staleness`,
  and reading the raw YAML across several turns.
when_to_use: >
  Invoke when the user wants to inspect or change chain-authorization gate
  behavior for /lrh-land or /lrh-execute -- e.g. "what's our current gate
  config", "flip confirm_fixes_batch", "grant consent for skip_if_opted_in".
  Do not use to change any other project config, and do not use it to make
  a gate decision on the user's behalf -- every change is presented and
  confirmed, never inferred.
argument-hint: "[--project-root <path>]"
disable-model-invocation: false
---

# lrh-config-gates Skill

A thin, CLI-backed skill: `lrh chain-defaults status` computes the full
read (see `src/lrh/chain_defaults_status.py`); this skill presents it,
elicits confirmed changes to the 4 human-decidable fields, and separately
handles the skip-consent grant -- never in the same confirm.

This is architecture Option C from the session that filed
`WI-SKILLS-LRH-CONFIG-GATES`: compute in a tested Python module behind a CLI
subcommand, gate on a human confirm in skill prose -- the same pattern
`confirm_fixes_batch.py` / `lrh confirm-fixes check-batch-routine` and
`gate_staleness.py` / `lrh chain-defaults check-staleness` already
established. No ad hoc bash computes gate-relevant state in this skill's
own prose.

---

## Inputs

```
/lrh-config-gates
/lrh-config-gates --project-root <path>
```

`--project-root` defaults to the current directory. There is no other
argument -- this skill always starts from a full status read, never a
pre-selected field.

---

## Execution Steps

### Step 1 — Read status

```bash
lrh chain-defaults status --project-root <project-root> --format json
```

Parse the structured output. Do not read `project/config/chain-defaults.yaml`
directly, run `git config --get`, or run `git hash-object` by hand --
`compute_status` already computed all of this in one read
(`src/lrh/chain_defaults_status.py`), and duplicating it in skill-prose bash
is exactly the ad hoc-bash risk this WI was filed to avoid (this session's
own worktree-`.git/` capture bug is the concrete precedent).

If `profile_exists` is `false`, present that plainly: no
`chain-defaults.yaml` exists yet at this project root, so there is nothing
to inspect or change here. Stop -- do not offer to create the file; that is
`/lrh-land`'s or `/lrh-execute`'s own first-encounter propose-and-confirm
flow (`chain-defaults.md`), not this skill's job.

### Step 2 — Present the full status table

<!-- GATE-DEFINITION -->
Before asking anything, show one table covering the entire status read:

- **Human-decidable fields** (`fields`): `chain_init_confirmation`,
  `confirm_fixes_batch`, `completion_condition`, `stop_work_condition`,
  with their current values.
- **Read-only** (`read_only_fields.closeout_with_merge`): labeled
  explicitly as not a user-facing toggle -- per `chain-defaults.md:40-46`,
  it is the shipped, unconditional `/lrh-land` merge+closeout behavior.
  Never present this as something the user can change here.
- **Consent** (`consent`): `stored_hash`, `current_hash`, `valid`. If
  `valid` is `false`, state plainly whether that's because no hash is
  stored yet, or because a stored hash no longer matches the file's
  current content (e.g. a prior edit re-stamped it) -- these are different
  situations even though both read as "not valid."
- **Staleness** (`staleness` / `staleness_error`): if `staleness` is
  present, show `stale` and, when `true`, the `files` list verbatim (path
  and reason per file) -- the same "show the actual stale-files payload,
  not a generic note" requirement `chain-defaults.md` states for the
  chain-authorization gate itself. If `staleness` is `null`, show
  `staleness_error` as-is (e.g. "no prior confirmation on record").

This presentation itself is not a question -- it is shown in full before
Step 3 asks anything, matching the same "propose, then confirm" shape every
other gate in this codebase follows.
<!-- /GATE-DEFINITION -->

### Step 3 — Offer field-value changes (its own confirm)

Ask the user whether they want to change any of the 4 human-decidable
fields. If not, skip to Step 5.

If yes, collect the desired new value(s) for one or more of the 4 fields.
Valid values:

- `chain_init_confirmation`: `always_confirm` | `skip_if_opted_in`
- `confirm_fixes_batch`: `always_confirm` | `auto_unless_unusual`
- `completion_condition`, `stop_work_condition`: free-text

<!-- GATE-DEFINITION -->
**Confirm gate.** Show the proposed diff (old value → new value, per
field) and wait for explicit confirmation before writing anything. This is
the same confirm-then-commit-then-push pattern every other config change
this session used -- never write `chain-defaults.yaml` on an inferred or
assumed "yes."

Do not fold a skip-consent grant/regrant into this confirm, even if the
user's reply also mentions consent -- Step 4 is a categorically separate,
explicit action per `chain-defaults.md:117-123`'s two-separate-affirmative-
actions requirement. If the user's reply is ambiguous about whether it
covers both, ask which one(s) they mean rather than inferring the more
permissive reading -- inferring action-authorization from an ambiguous
reply is a documented anti-pattern in this project's own session history.
<!-- /GATE-DEFINITION -->

Once confirmed, edit `project/config/chain-defaults.yaml` with only the
confirmed field changes (leave `confirmed_commit`/`confirmed_at` and
`closeout_with_merge` untouched here -- this step never re-stamps
confirmation state or touches the read-only field). Then:

```bash
lrh validate
```

Fix any error before proceeding to Step 5's commit.

**Note on `confirmed_commit`/`confirmed_at`:** this skill does not
re-stamp them. That is the chain-authorization gate's own job
(`chain-defaults.md`'s propose-and-confirm flow, exercised at
`/lrh-land`/`/lrh-execute` Step 2), triggered by a live chain-authorization
reply -- not by a config-editing session. A field-value change made here
will show as stale (or, if `chain_init_confirmation` was just set to
`skip_if_opted_in` for the first time, as no-prior-confirmation) the next
time a chain gate runs, which is correct: the human edited the policy here,
but hasn't yet live-confirmed a chain run under it.

### Step 4 — Offer the skip-consent grant (its own, separate confirm)

Ask, as its own distinct question -- never combined with Step 3's ask --
whether the user wants to grant or regrant local skip-consent for
`chain_init_confirmation: skip_if_opted_in`. Skip this step entirely if the
user has no interest in it this run.

If yes:

<!-- GATE-DEFINITION -->
**Confirm gate.** Before running anything, state plainly:

- This grants consent scoped to **this git clone only** -- shared across
  every worktree of the *same* clone (the common `.git/config`, even when
  `extensions.worktreeConfig` is set -- verified empirically this session),
  but **not** shared with any other, independent clone. Never claim consent
  granted here transferred to a different checkout.
- The command to be run:
  ```bash
  git config --local lrh.chainDefaults.skipConsentHash "$(git hash-object project/config/chain-defaults.yaml)"
  ```
- This binds consent to the **current on-disk file's content** at the
  moment the command runs. If Step 3 just edited the file in this same
  session, that edit is already reflected -- but if the file changes again
  after this grant (including a later `confirmed_commit` re-stamp), this
  grant is invalidated and must be re-run; this skill does not
  automatically detect and silently re-grant that later.

Wait for explicit confirmation before running the command.
<!-- /GATE-DEFINITION -->

Run the confirmed command, then re-read status
(`lrh chain-defaults status --format json`) and confirm `consent.valid` is
now `true` before reporting success. If it is not (e.g. the file changed
between the confirm and the command), report the mismatch plainly rather
than claiming success -- this is the same class of self-caught error this
session hit and corrected live while granting consent for
`WI-SKILLS-LRH-CONFIG-GATES` itself.

### Step 5 — Commit and push (if Step 3 made changes)

Skip this step if Step 3 made no changes (a consent grant alone, from Step
4, is a local-only git-config write with nothing to commit).

Determine the current branch:

```bash
git branch --show-current
```

**If on a feature branch already tied to an open PR:** commit and push as
an additional commit to that branch, same as any other config change
mid-PR.

**If on `main` (or no open PR context):** pushing directly to `main`
always requires its own explicit confirmation, even for a small change --
this is a standing project constraint, not specific to this skill. Use the
main-worktree-lock tmp-branch workaround this codebase's other skills use
when the primary worktree has `main` checked out elsewhere:

```bash
git fetch origin main --quiet
git checkout -b tmp-config-gates-<slug> origin/main
# edit + commit here
git push origin tmp-config-gates-<slug>:main
git checkout <original-branch>
```

State the exact commit(s) about to be pushed and wait for explicit
confirmation before the push, whichever path applies.

### Step 6 — Report

Report to the user:

- The full status table as it now stands (re-read after any change).
- Which fields changed, if any (Step 3).
- Whether consent was granted/regranted, and its resulting validity (Step
  4).
- The commit(s) pushed, if any (Step 5).

---

## What This Skill Does Not Do

- Does not create `project/config/chain-defaults.yaml` if it doesn't exist
  -- that is the chain-authorization gate's first-encounter
  propose-and-confirm flow (`chain-defaults.md`), reached from
  `/lrh-land`/`/lrh-execute`, not this skill.
- Does not expose `closeout_with_merge` as a configurable field -- it is
  documented read-only (`chain-defaults.md:40-46`).
- Does not re-stamp `confirmed_commit`/`confirmed_at` -- that only happens
  through a live chain-authorization reply at `/lrh-land`/`/lrh-execute`
  Step 2, per the re-stamp condition in `chain-defaults.md`.
- Does not bundle the skip-consent grant into the field-value confirm, or
  infer consent-granting intent from an ambiguous reply.
- Does not claim git-config consent transfers across independent clones.
- Does not decide policy on the user's behalf -- every change (field value
  or consent grant) is proposed and confirmed, never inferred or applied
  by default.
