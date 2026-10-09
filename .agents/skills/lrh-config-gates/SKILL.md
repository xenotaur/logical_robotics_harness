---
name: lrh-config-gates
description: 'Inspect and change the chain-defaults gate policy in project/config/chain-defaults.yaml.
  Presents the 4 human-decidable fields (chain_init_confirmation, confirm_fixes_batch,
  completion_condition, stop_work_condition), closeout_with_merge shown read-only,
  the local git-config skip-consent hash''s validity, and the gate-definition staleness
  status -- all in one read, via `lrh chain-defaults status` -- before asking anything.
  Field-value changes, the re-confirm of stale gates (which re-stamps confirmed_commit
  and records user-scope installed-target fingerprints via `lrh chain-defaults restamp`),
  and the separate skip-consent grant each require their own explicit confirm; a consent
  grant is never bundled into or implied by another confirm. Use instead of manually
  running `git config --get`, `git hash-object`, `lrh chain-defaults check-staleness`,
  and reading the raw YAML across several turns.

  '
---

# lrh-config-gates Skill

A thin, CLI-backed skill: `lrh chain-defaults status` computes the full
read (see `src/lrh/chain_defaults_status.py`); this skill presents it,
elicits confirmed changes to the 4 human-decidable fields, offers a
separately confirmed re-confirm of stale gates (`lrh chain-defaults
restamp`), and separately handles the skip-consent grant -- never two of
these in the same confirm.

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
- **Installed-target fingerprints** (from the same `files` list): say how
  many watched files are user-scope installed targets (paths qualified like
  `claude:lrh-land/SKILL.md`) and, if any are stale because the fingerprint
  store is missing ("no persisted content fingerprint") or bound to a
  different stamp ("different confirmation stamp"), say so plainly -- that
  is the client-repo case Step 3b clears.

This presentation itself is not a question -- it is shown in full before
Step 3 asks anything, matching the same "propose, then confirm" shape every
other gate in this codebase follows.
<!-- /GATE-DEFINITION -->

### Step 3 — Offer field-value changes (its own confirm)

Ask the user whether they want to change any of the 4 human-decidable
fields. If not, skip to Step 3b.

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

Once confirmed, edit `<project-root>/project/config/chain-defaults.yaml`
with only the confirmed field changes (leave `confirmed_commit`/
`confirmed_at` and `closeout_with_merge` untouched here -- this step never
re-stamps confirmation state or touches the read-only field). **Always
edit the file under `<project-root>`, never a bare relative path** --
`<project-root>` may differ from the current directory, and editing the
wrong clone's file both misses the intended change and can leave a stale
edit behind in whatever directory happens to be current. Then:

```bash
lrh validate --project-dir <project-root>/project
```

(`lrh validate` takes `--project-dir`, not `--project-root` -- point it at
`<project-root>/project`, not the bare repo root.)

Fix any error before proceeding to Step 5's commit.

**Note on `confirmed_commit`/`confirmed_at`:** Step 3 never re-stamps
them. A field-value change made here will show as stale (or, if
`chain_init_confirmation` was just set to `skip_if_opted_in` for the first
time, as no-prior-confirmation) until a human re-confirms -- either live at
the next `/lrh-land`/`/lrh-execute` chain gate, or in Step 3b below once
the change has landed on `main`.

### Step 3b — Offer to re-confirm stale gates (its own, separate confirm)

Recommend this step when Step 2 showed `stale: true`; otherwise offer it as
optional, or skip it if the user has no interest. Ask it as its own
question -- never combined with Step 3's or Step 4's ask.

If Step 3 made field changes in this run that are not yet on `main`, do not
offer this step now: the stamp must cover the values on `main`. Say so, and
tell the user to re-confirm after those changes land.

The re-stamp always lands on `main` through Step 5's `main` path, never on a
feature branch: a stamp committed onto a PR branch would name a commit that
is not on `main` and mix policy state into an unrelated PR. So, scoped to
`<project-root>`, create the tmp branch from `origin/main` first (Step 5's
`main`-path commands, up to the edit), and run everything below there.

```bash
lrh chain-defaults restamp --project-root <project-root> --dry-run
```

Keep the `plan_digest` it prints. The real run below passes it back with
`--expect-digest` and refuses if the plan changed in between (e.g. an
installed file changed), so it can only record what was shown here. The
`confirmed_at` time shown is indicative: the real run stamps the moment it
runs, and the digest deliberately excludes it.

<!-- GATE-DEFINITION -->
**Confirm gate.** Before re-stamping, show:

- The `Stale files being re-confirmed` list from the dry run, verbatim
  (path and reason per file) -- the same payload the chain-authorization
  gate would show (`chain-defaults.md`'s re-stamp condition).
- The fingerprint plan: each user-scope installed target with its
  comparison (`new` / `unchanged` / `changed` / `removed`) and path.
- The new stamp (`confirmed_commit` and `confirmed_at`) and the
  `plan_digest`.
- Plainly: this accepts the **current** gate text of every watched file as
  confirmed. For a `changed` user-scope entry, LRH stores only hashes, so it
  can say the installed content differs but not what changed -- inspect the
  file yourself if that matters.
- Plainly: re-stamping changes `chain-defaults.yaml`, so any skip consent
  becomes invalid until re-granted (Step 4).

Wait for explicit confirmation before running the re-stamp. A confirm here
covers only the re-stamp -- never the consent grant.
<!-- /GATE-DEFINITION -->

Run, on the tmp branch:

```bash
lrh chain-defaults restamp --project-root <project-root> --expect-digest <plan_digest>
```

If it exits 2, report the error verbatim and stop this step -- nothing was
written. That covers an unresolved, missing, or unreadable installed
target, a failed staleness check, an identical stamp, and a plan that no
longer matches the approved digest; in the last case, offer to start this
step again from the dry run. Otherwise commit
the profile change and continue through Step 5's `main` path (including its
explicit push confirmation). If the user declines the push, say plainly
that `main`'s profile is unchanged; the fingerprint store was already
written to the clone's git common dir, but it is bound to a stamp no
committed profile carries, so it is ignored (user-scope targets keep
failing closed) until a re-stamp lands. Return to the original branch and
leave the tmp branch for the user to delete; skip the rest of this step.

After the push, return to the original branch. If that branch is `main`,
fast-forward it so its profile carries the new stamp:

```bash
git -C <project-root> merge --ff-only origin/main
```

(after a `git -C <project-root> fetch origin main --quiet`). If the
fast-forward fails, report it and do not offer Step 4. Then re-read status. Report
the staleness result honestly. Offer Step 4's consent grant only if
`<project-root>`'s checked-out `chain-defaults.yaml` now carries the new
stamp (e.g. a `main` checkout fast-forwarded to `origin/main`). If it
doesn't -- notably on a PR branch -- do not offer the grant: Step 4 hashes
the checked-out file, so a grant there would be bound to the old profile
and could never match. Tell the user to run `/lrh-config-gates` from a
checkout with the new profile (e.g. `main`, or the PR branch after it
merges `main`) to grant consent.

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
  git -C <project-root> config --local lrh.chainDefaults.skipConsentHash "$(git -C <project-root> hash-object project/config/chain-defaults.yaml)"
  ```
  **Always run this with `git -C <project-root>`, never a bare `git`
  invocation from the current directory.** `<project-root>` may differ
  from the current directory (it is an explicit skill input, per Step 1);
  a bare `git config --local` and `git hash-object` operate on whatever
  clone the current directory happens to be in, which can silently grant
  consent in the wrong clone while leaving the requested `<project-root>`
  clone's consent untouched -- a real P1 finding on this skill's own
  filing PR (`AGENTS.md:24-27`'s "operate on the resolved target, not an
  assumed cwd" principle).
- This binds consent to the **current on-disk file's content** at the
  moment the command runs. If Step 3 just edited the file in this same
  session, that edit is already reflected -- but if the file changes again
  after this grant (including a later `confirmed_commit` re-stamp, e.g. from
  Step 3b or a chain gate), this grant is invalidated and must be re-run; this skill does not
  automatically detect and silently re-grant that later.

Wait for explicit confirmation before running the command.
<!-- /GATE-DEFINITION -->

Run the confirmed command, then re-read status
(`lrh chain-defaults status --project-root <project-root> --format json`)
and confirm `consent.valid` is now `true` before reporting success. If it
is not (e.g. the file changed between the confirm and the command), report
the mismatch plainly rather than claiming success -- this is the same
class of self-caught error this session hit and corrected live while
granting consent for `WI-SKILLS-LRH-CONFIG-GATES` itself.

### Step 5 — Commit and push (if Step 3 or Step 3b made changes)

Skip this step if neither Step 3 nor Step 3b changed anything (a consent
grant alone, from Step 4, is a local-only git-config write with nothing to
commit). A Step 3b re-stamp always takes the `main` path below, even when
the current branch is tied to an open PR.

Determine the current branch, scoped to `<project-root>` like every other
git operation in this skill:

```bash
git -C <project-root> branch --show-current
```

**If on a feature branch already tied to an open PR (Step 3 field changes
only):** commit and push as an additional commit to that branch, same as any other config change
mid-PR -- `git -C <project-root> add ...`, `git -C <project-root> commit
...`, `git -C <project-root> push`.

**If on `main` (or no open PR context):** pushing directly to `main`
always requires its own explicit confirmation, even for a small change --
this is a standing project constraint, not specific to this skill. Use the
main-worktree-lock tmp-branch workaround this codebase's other skills use
when the primary worktree has `main` checked out elsewhere, every command
scoped to `<project-root>`:

```bash
git -C <project-root> fetch origin main --quiet
git -C <project-root> checkout -b tmp-config-gates-<slug> origin/main
# edit + commit here, still under <project-root>
git -C <project-root> push origin tmp-config-gates-<slug>:main
git -C <project-root> checkout <original-branch>
```

State the exact commit(s) about to be pushed and wait for explicit
confirmation before the push, whichever path applies.

### Step 6 — Report

Report to the user:

- The full status table as it now stands (re-read after any change).
- Which fields changed, if any (Step 3).
- Whether gates were re-confirmed (Step 3b): the new stamp, the
  fingerprint plan that was recorded, and the resulting staleness.
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
- Does not re-stamp `confirmed_commit`/`confirmed_at`, or record
  installed-target fingerprints, outside Step 3b's own confirm -- and only
  ever via `lrh chain-defaults restamp`, which does both as one act. The
  only other sanctioned re-stamp point is a live chain-authorization reply
  at `/lrh-land`/`/lrh-execute` Step 2 (`chain-defaults.md`).
- Does not commit a re-stamp onto a feature or PR branch.
- Does not bundle the skip-consent grant into the field-value confirm, or
  infer consent-granting intent from an ambiguous reply.
- Does not claim git-config consent transfers across independent clones.
- Does not decide policy on the user's behalf -- every change (field value
  or consent grant) is proposed and confirmed, never inferred or applied
  by default.
