# `lrh chain-defaults`

`lrh chain-defaults` reports on `project/config/chain-defaults.yaml`, the
profile that `/lrh-land` and `/lrh-execute`'s chain-authorization gate
reads to decide whether a run's completion/stop-work conditions can be
pre-filled or skipped (`chain_init_confirmation: skip_if_opted_in`).

## Subcommands

```bash
lrh chain-defaults status [options]
lrh chain-defaults check-staleness --confirmed-commit <sha> [options]
lrh chain-defaults restamp [--dry-run] [options]
```

| Subcommand | Behavior |
|---|---|
| `status` | Single-read status view: the 4 human-decidable fields, `closeout_with_merge` shown read-only, skip-consent hash validity, and staleness — all in one structured read. |
| `check-staleness` | Gate-definition staleness check for stored chain-defaults consent, against an explicit `--confirmed-commit` (and `--confirmed-at`). |
| `restamp` | Re-stamps `confirmed_commit`/`confirmed_at` and records user-scope installed-target fingerprints bound to that same stamp, as one act. |

`status` and `check-staleness` are read-only. `restamp` is the only command
that writes: it rewrites the two stamp lines of `chain-defaults.yaml` and
the fingerprint store. It never touches git config.

## `status`

```bash
lrh chain-defaults status [--head HEAD] [--project-root PROJECT_ROOT] [--format {text,json}]
```

| Option | Behavior |
|---|---|
| `--head` | Commit-ish to check staleness against (default: `HEAD`). |
| `--project-root` | Target repository root (default: current directory). |
| `--format` | `text` (default) or `json`. |

Reports:

- **Human-decidable fields** — `chain_init_confirmation`,
  `confirm_fixes_batch`, `completion_condition`, `stop_work_condition`.
- **`closeout_with_merge`** — the shipped, unconditional `/lrh-land`
  merge+closeout behavior; shown read-only, not a configurable toggle.
- **Consent** — the local git-config skip-consent hash (`stored_hash`),
  the file's current blob hash (`current_hash`), and whether they match
  (`valid`). Consent is scoped per git clone: shared across every
  worktree of the same clone, never shared across independent clones.
- **Staleness** — whether any watched gate-bearing skill file has
  changed since `confirmed_commit` in a way that counts as stale, and
  the specific stale files if so. See `check-staleness` below for how
  "counts as stale" differs between git-diffable and user-scope
  installed targets.

### Example

```bash
$ lrh chain-defaults status
Human-decidable fields:
  chain_init_confirmation: 'skip_if_opted_in'
  confirm_fixes_batch: 'auto_unless_unusual'
  completion_condition: 'PR merged, its execution records landed, and any linked work item resolved.'
  stop_work_condition: "Any failing CI check, a reviewer finding that isn't Clear-satisfied on re-verification, or an ambiguous/refused merge-authorization reply."
Read-only fields (not a user-facing toggle):
  closeout_with_merge: True
Consent (skip_if_opted_in, per-clone scope):
  stored_hash: f578b957b5ffeca7ab62bc549e033d4e31b09381
  current_hash: 5eb55e14e6b32751019801dacea0054a66701acf
  valid: False
Staleness:
  stale: False
```

## `check-staleness`

```bash
lrh chain-defaults check-staleness --confirmed-commit <sha> [--confirmed-at <timestamp>] [--head HEAD] [--project-root PROJECT_ROOT] [--format {text,json}]
```

| Option | Behavior |
|---|---|
| `--confirmed-commit` | Required. The commit stored consent was last confirmed against. |
| `--confirmed-at` | The profile's `confirmed_at`. Needed for user-scope installed targets: their fingerprint store is accepted only when its stamp matches. Omitted, those targets fail closed. |
| `--head` | Commit-ish to check against (default: `HEAD`). |
| `--project-root` | Target repository root (default: current directory). |
| `--format` | `text` (default) or `json`. |

Resolves each gate-bearing skill to where it actually lives, then checks
one of two ways depending on that resolution:

- **In this harness repo itself** (or a client repo with its own
  `src/lrh/skills/` tree), or **a project-local installed target
  committed to a client repo's git history** — diffs the file between
  `--confirmed-commit` and `--head`, scoped to lines inside
  `<!-- GATE-DEFINITION -->` / `<!-- /GATE-DEFINITION -->` markers. A
  change outside any marked region (a typo fix, a comment, reordered
  prose) does not count as stale.
- **A user-scope installed target with no git history to diff against**
  (e.g. the default `~/.claude/skills/...` install) — compares the
  file's current content against a persisted whole-file fingerprint
  recorded by `restamp`. Marker scoping does not apply here: **any**
  content change to the file, including a typo or reordered prose, makes
  it stale. The fingerprint store is accepted only when its stamp equals
  `(--confirmed-commit resolved to a full SHA, --confirmed-at)`; a
  missing, malformed, or differently stamped store fails every such target
  closed.

If an installed target can't be resolved at all, it is always reported
stale (fail-closed). Exits `0` if fresh, `1` if stale, `2` if the check
itself failed (e.g. an unresolvable `--confirmed-commit`).

## `restamp`

```bash
lrh chain-defaults restamp [--dry-run] [--expect-digest DIGEST] [--project-root PROJECT_ROOT] [--format {text,json}]
```

| Option | Behavior |
|---|---|
| `--dry-run` | Preview the stale-files list being re-confirmed, the fingerprint plan, the new stamp, and a `plan_digest`, without writing anything. |
| `--expect-digest` | The `plan_digest` from the approved dry run. Refuses (exit `2`, nothing written) if the plan has changed since. The digest covers the stale files, every fingerprint entry, and the commits, but not the timestamp. |
| `--project-root` | Target repository root (default: current directory). |
| `--format` | `text` (default) or `json`. |

Run only after a human has re-confirmed the stale-files payload: at a
`/lrh-land`/`/lrh-execute` chain-authorization gate, or in
`/lrh-config-gates`'s re-confirm step. It:

1. Refuses (exit `2`, nothing written) if `chain-defaults.yaml` is absent;
   if the staleness check against the current `confirmed_commit` fails
   (there would be no stale-files payload to confirm; only a null or absent
   `confirmed_commit`, the first-encounter case, proceeds without one); if
   any watch target can't be resolved, or any user-scope installed target
   file is missing or unreadable; if the new stamp would equal the current
   one; or if `--expect-digest` no longer matches the plan.
2. Computes one stamp: `HEAD`'s full SHA and the current UTC time as
   ISO-8601 with a trailing `Z`.
3. Writes the fingerprint store, bound to that stamp, to
   `$(git rev-parse --git-common-dir)/lrh/chain-defaults-fingerprints.json`.
   The store is clone-local, shared across the clone's worktrees, and
   never committed. It replaces the whole map: targets no longer
   configured are dropped, and when no user-scope targets remain, an empty
   map is written. With no user-scope targets and nothing stored (e.g. this
   harness repo), nothing is written.
4. Rewrites only the `confirmed_commit:` and `confirmed_at:` lines of
   `chain-defaults.yaml`, to that same stamp.

The fingerprint plan labels each user-scope target `new`, `unchanged`,
`changed`, or `removed`. Only hashes are stored, so `changed` means the
content differs, not what changed.

Because skip consent is bound to the profile's blob hash, a re-stamp always
invalidates it; re-grant via `/lrh-config-gates`. If the re-stamped profile
is never committed (a failed write or a declined push), the store's stamp
matches no profile, so user-scope targets keep failing closed.

Exits `0` on success (including a dry run) and `2` on refusal or error,
with the error on stderr.

## Related

- `/lrh-config-gates` — the LRH skill that presents this state and gates
  confirmed field-value changes, the re-confirm of stale gates (`restamp`),
  and consent grants, each as its own confirm.
- [`skills`](skills.md) — install and inspect rendered agent skills,
  including the gate-bearing files this command's staleness check
  watches.
