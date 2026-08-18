---
execution_id: 2026_08_18_00_18_38_RESCUE_CLAUDE_SESSIONS_REVIEW
prompt_id: PROMPT(AD_HOC:RESCUE_CLAUDE_SESSIONS_REVIEW)[2026-08-17T23:47:02+00:00]
work_item: AD_HOC
status: in_progress
rerun_of: 
pr: https://github.com/xenotaur/logical_robotics_harness/pull/561
commit: 
created_at: 2026-08-18T00:18:38+00:00
agent: claude-code
instruction_source: https://github.com/xenotaur/logical_robotics_harness/pull/561
session_transcript: pending
---

# Summary

Address five open review comments on PR #561 (`experimental/rescue_claude_sessions`):
one Codex P1, one Codex P2, and three from Copilot. All five passed the
presence / validity / feasibility triage; none conflicted with a design
decision. Two were genuine silent-failure bugs in tooling whose entire purpose
is to prevent silent failure.

`rerun_of` is intentionally empty: Step 3's slug search found no prior
`_REVIEW` record for this branch, and no primary record with slug
`RESCUE_CLAUDE_SESSIONS` exists — PR #561 was opened by hand rather than
through `/lrh-implement`, so there is no primary implementation record to
link.

Corroborated by the `pr:`-field fallback rather than by the branch-slug
search alone, per the `feedback_rerun_of_branch_slug_mismatch` memory: that
search returns nothing on a slug mismatch *and* on a genuine absence, so an
empty result cannot by itself distinguish the two.
`grep -rl "^pr: <url>" project/executions/`, excluding
`_REVIEW`/`_CONFIRM`/`_SELFREVIEW`, also returns nothing for PR #561, while
the same query against PR #556 returns its three records — so the query is
sound and the absence is real.

# Result

**Codex P1 — divergent memory-file collisions (fixed).** Under `--allow-merge`,
`migrate_memory.py` left the destination's version of a colliding file
untouched, verified only the copied set, and returned success. A divergent
`MEMORY.md` would therefore leave the migrated corpus unindexed while the run
reported success — the exact failure mode the tool exists to prevent.
`plan_copy` now returns `(to_copy, identical, divergent)`, classifying
collisions by SHA-256, and divergence is refused with the offending paths
named and `MEMORY.md` called out as the index that drives recall. No override
flag was added: reconciling two versions of a memory is a judgement about
content, not a mechanical merge, mirroring the divergence refusal already in
`archive_split_transcripts.py`.

**Codex P2 + Copilot `choose_keeper` — one defect in two places (fixed).**
`pair_buckets` required a trailing hyphen, so an alias naming a repository
directly (`~/old/repo=~/new/repo`) matched nothing and exited 0 reporting zero
corpora considered. `choose_keeper` used an unbounded `startswith`, which could
match an unrelated sibling and, on a size tie, keep the non-canonical copy
while archiving the canonical one. Both now call one shared
`bucketlib.matches_root`, which accepts an exact root match and requires the
`-` boundary for descendants, so the two callers cannot drift apart again.

**Copilot — macOS-only `/private/tmp` in two tools (fixed, adapted).** Taken as
Copilot's own fallback clause rather than the literal `${TMPDIR:-/tmp}`
suggestion: `experimental/README.md` asks for raw captures under
`/private/tmp`, and on macOS `$TMPDIR` is a per-user `/var/folders/...` path,
so switching outright would diverge from a stated repo convention. Both
`snapshot_state.sh` and `archive_split_transcripts.py` now prefer
`/private/tmp` when it exists and fall back to `${TMPDIR:-/tmp}` otherwise.

Docs updated to match: `README.md` now states the divergence refusal covers
both tools with no override, and records the non-macOS fallback.

Nothing skipped.

# Validation

    scripts/version tools          — Python 3.11.8, Ruff 0.15.0, Black 25.11.0,
                                     lrh 0.2.5.dev1727+g8b897fe4c
    scripts/format --check --diff  — FAILED (exit 1) — environment, see below
    scripts/lint                   — FAILED (exit 1) — environment, see below
    scripts/test                   — Ran 1088 tests, OK (exit 0)
    lrh validate                   — 0 errors, 0 warnings

**`scripts/format` and `scripts/lint` fail on a pinned-version gate, not on
this branch's code.** `pyproject.toml:75` pins Black `26.3.1` (installed
`25.11.0`) and `pyproject.toml:80` pins Ruff `==0.15.12` (installed `0.15.0`).
Both tools refuse before examining any file. Evidence that this is
pre-existing and unrelated to this PR:

- Both pins are byte-identical on `main` (`git show main:pyproject.toml`).
- Black fails the same way on `src/lrh/__init__.py`, which this PR never
  touches; the PR's diff is confined to `experimental/rescue_claude_sessions/`.
- The failure text is a version assertion, not a formatting or lint finding.

Treated as a missing environment dependency per the review-response protocol's
canonical-validation section, not a code regression. Remediation is
`pip install 'black==26.3.1' 'ruff==0.15.12'`, deliberately not run here
because it mutates the user's shared environment.

To avoid shipping code that would fail once the pins are met, both tools were
run against the changed files with the pin bypassed (isolated config, same
line-length 88 / py311 / `E,F,I` rule set). That surfaced 16 real findings,
all fixed: Black reformatted 4 files, and 8 Ruff findings (7 × E501, 1 × I001)
were resolved. Both now report clean. This is supplementary evidence, not a
substitute for the canonical run — Black 25.11.0 may differ from 26.3.1 in
edge cases.

Behaviour re-verified after formatting, with regression coverage for the two
silent-failure bugs:

- `matches_root` unit assertions: exact root pairs, descendants pair, a
  prefix-sharing sibling (`<prefix>Extra`) is rejected.
- End-to-end, single-repo alias: `audit_buckets.py` and `migrate_memory.py`
  now find the LCATS bucket (previously "0 corpora considered").
- Controlled fixture with a divergent `MEMORY.md`: `--allow-merge --apply`
  refuses, exits 1, leaves the destination untouched, and does not partially
  migrate. Control case with an identical index proceeds and reports "same".
- Live dry runs unchanged: 5 splits detected, all 5 correctly refused pending
  `lrh sessions sync`.

# Follow-up

- `session_transcript: pending` — update to the durable session pointer once
  available.
- Run `/lrh-confirm-fixes` on PR #561 before merge.
- The Black/Ruff version drift blocks the canonical gate for *every* PR in this
  repository, not just this one. Worth resolving independently of #561.
- Unrelated to this PR and still outstanding: the rescue itself has not been
  performed. 136 LRH and 159 LCATS memory files remain orphaned under the old
  bucket spelling.
