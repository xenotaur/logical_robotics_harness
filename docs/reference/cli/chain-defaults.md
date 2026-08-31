# `lrh chain-defaults`

`lrh chain-defaults` reports on `project/config/chain-defaults.yaml`, the
profile that `/lrh-land` and `/lrh-execute`'s chain-authorization gate
reads to decide whether a run's completion/stop-work conditions can be
pre-filled or skipped (`chain_init_confirmation: skip_if_opted_in`).

## Subcommands

```bash
lrh chain-defaults status [options]
lrh chain-defaults check-staleness --confirmed-commit <sha> [options]
```

| Subcommand | Behavior |
|---|---|
| `status` | Single-read status view: the 4 human-decidable fields, `closeout_with_merge` shown read-only, skip-consent hash validity, and staleness — all in one structured read. |
| `check-staleness` | Semantic (marker-scoped) gate-definition staleness check for stored chain-defaults consent, against an explicit `--confirmed-commit`. |

Both subcommands are read-only — neither writes `chain-defaults.yaml` or
git config.

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
- **Staleness** — whether any `GATE-DEFINITION`-marked region in a
  watched gate-bearing skill file has changed since `confirmed_commit`,
  and the specific stale files if so.

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
lrh chain-defaults check-staleness --confirmed-commit <sha> [--head HEAD] [--project-root PROJECT_ROOT] [--format {text,json}]
```

| Option | Behavior |
|---|---|
| `--confirmed-commit` | Required. The commit stored consent was last confirmed against. |
| `--head` | Commit-ish to check against (default: `HEAD`). |
| `--project-root` | Target repository root (default: current directory). |
| `--format` | `text` (default) or `json`. |

Diffs each gate-bearing skill file between `--confirmed-commit` and
`--head`, scoped to lines inside `<!-- GATE-DEFINITION -->` /
`<!-- /GATE-DEFINITION -->` markers — a change outside any marked region
(a typo fix, a comment, reordered prose) does not count as stale. Exits
`0` if fresh, `1` if stale, `2` if the check itself failed (e.g. an
unresolvable `--confirmed-commit`).

## Related

- `/lrh-config-gates` — the LRH skill that presents this state and gates
  confirmed field-value changes and consent grants.
- [`skills`](skills.md) — install and inspect rendered agent skills,
  including the gate-bearing files this command's staleness check
  watches.
