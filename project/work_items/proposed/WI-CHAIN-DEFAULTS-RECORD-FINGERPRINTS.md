---
resolution: null
blocked_reason: null
blocked: false
id: WI-CHAIN-DEFAULTS-RECORD-FINGERPRINTS
title: "Record installed-target gate fingerprints via a separate /lrh-config-gates action"
type: deliverable
status: proposed
owner: anthony
contributors:
  - anthony
assigned_agents: []
related_focus:
  - FOCUS-EXECUTION-FRAMEWORK-PLANNING
related_roadmap:
  - ROADMAP-PHASE-03
related_workstreams:
  - WS-INVOCATION-AND-GATE-RESET
related_design:
  - project/work_items/resolved/WI-GATE-STALENESS-INSTALLED-TARGET-FINGERPRINT.md
  - project/memory/decisions/DEC-CHAIN-INIT-SKIP-CONSENT.md
  - project/design/proposals/adopted/lrh-gate-policy/00_proposal.md
  - src/lrh/skills/_shared/chain-defaults.md
depends_on: []
blocked_by: []
expected_actions:
  - edit_file
  - add_cli_command
  - run_tests
  - write_docs
  - create_pr
forbidden_actions:
  - force_push
  - delete_branch
  - merge_pr
  - weaken_fail_closed_staleness
  - bundle_fingerprint_recording_with_consent_grant
  - record_fingerprints_without_explicit_confirm
  - modify_closeout_with_merge
  - commit_fingerprint_file
acceptance:
  - "`lrh chain-defaults record-fingerprints --project-root <root>` records a SHA-256 fingerprint for every fingerprint-kind watch target, written atomically to `$(git rev-parse --git-common-dir)/lrh/chain-defaults-fingerprints.json`, and `--dry-run` previews new/unchanged/changed/removed entries without writing"
  - "Recording refuses (exit 2, stored file untouched) when any watch target is unresolved or any installed target file is missing; a missing, unreadable, or malformed store still fails every untracked target closed"
  - "After a successful record, `lrh chain-defaults status` reports those targets as matching the persisted fingerprint, and `consent.valid` and `confirmed_commit` are unchanged by the record action"
  - "`/lrh-config-gates` offers fingerprint recording as its own separately confirmed step (distinct from field-value changes and the skip-consent grant), previews via `--dry-run`, and re-reads status afterward"
  - "Two worktrees of one clone share the fingerprint store; two independent clones do not"
  - "`lrh validate` reports 0 errors and `scripts/test` passes"
required_evidence:
  - manual_review
  - lrh_validate
  - test_output
artifacts_expected:
  - src/lrh/gate_staleness.py
  - src/lrh/cli/main.py
  - src/lrh/skills/lrh-config-gates/SKILL.md
  - .claude/skills/lrh-config-gates/SKILL.md
  - src/lrh/skills/_shared/chain-defaults.md
  - docs/reference/cli/chain-defaults.md
  - tests/gate_staleness_test.py
---

# WI-CHAIN-DEFAULTS-RECORD-FINGERPRINTS

## Summary

Add an explicit, separately confirmed action — `lrh chain-defaults
record-fingerprints`, offered by `/lrh-config-gates` — that records content
fingerprints for user-scope (untracked) installed gate-bearing skill files,
so `skip_if_opted_in` can take effect in client repos without weakening
fail-closed staleness or bundling fingerprint recording into the consent
grant.

## Problem / Context

`WI-GATE-STALENESS-INSTALLED-TARGET-FINGERPRINT` (PR #649) taught
`check_gate_staleness` to compare untracked installed targets (e.g. the
default `~/.claude/skills/...` install) against persisted content
fingerprints, and added `gate_staleness.record_fingerprints()` — but its
resolution explicitly deferred "wire record_fingerprints into a real
consent-grant call site once one exists." Nothing outside tests ever calls
it, so in every client repo with a user-scope install, every watch target
reports "no persisted content fingerprint on record ... failing closed",
`staleness.stale` is permanently `true`, and `skip_if_opted_in` can never
take effect. This was observed live in the LCATS project: consent hash
valid, `chain_init_confirmation: skip_if_opted_in`, all installed Claude
targets stale, no fingerprint file present.

Design decisions (from the `/lrh-design` session that produced this item):

- **Separate action, not folded into the consent grant or the chain gate's
  `confirmed_commit` re-stamp.** A re-stamp rewrites
  `project/config/chain-defaults.yaml`, which invalidates the consent hash
  and would force a regrant loop; the consent grant is a distinct decision
  per `DEC-CHAIN-INIT-SKIP-CONSENT`. Recording a baseline is its own
  trust-on-first-use act, so it gets its own confirm.
- **Clone-local storage in the git common dir**, not
  `project/config/`. Fingerprints describe one machine's installed files;
  committing them would propagate environment-specific state, LRH cannot
  control client-repo `.gitignore`, and a worktree-relative untracked file
  would be missing in every new worktree. `$(git rev-parse
  --git-common-dir)/lrh/` matches the consent hash's per-clone,
  worktree-shared scope.
- **Latent bug to fix:** `record_fingerprints` currently skips `unresolved`
  targets and writes `{}` successfully, contradicting its own docstring
  ("must not silently record an empty/partial fingerprint set").
- The suggestion that seeded this item cited
  `src/lrh/skills/_shared/chain-defaults.md:113-128` as documenting
  fingerprint recording at consent time; that file never mentions
  fingerprints. The "consent-grant time" wording lives only in the
  `record_fingerprints` docstring, `FINGERPRINT_PATH`'s comment, and
  `docs/reference/cli/chain-defaults.md:96`, all of which this item corrects.

### Duplication search
- In-repo: Related: `src/lrh/gate_staleness.py` (`record_fingerprints`, `load_fingerprints`, `FINGERPRINT_PATH`) — plumbing exists but has no production caller, no CLI subcommand, and no skill step; this item extends it rather than duplicating it. Other "fingerprint" hits (`src/lrh/pii/allowlist.py`, WS-PII-SCAN) are unrelated.
- Sibling repos: None identified (LCATS is the observing client, not an implementation)
- External libraries: None identified (SHA-256 over file bytes via `hashlib`)
- Recommendation: Proceed

### Demand search
- Work items: Found: WI-GATE-STALENESS-INSTALLED-TARGET-FINGERPRINT — "Fix gate-staleness detection to work once LRH is installed outside this repo" (resolved; its resolution names this exact follow-up)
- Proposals: None found
- Backlog: No matching entries
- Recommendation: No action (origin item is already resolved; link it via `related_design`)

## Scope

- Make fingerprint persistence clone-local, strict, and previewable in `src/lrh/gate_staleness.py`.
- Expose it as a product-facing CLI subcommand, `lrh chain-defaults record-fingerprints`.
- Offer it from `/lrh-config-gates` as its own separately confirmed step.
- Correct the docs and docstrings that describe fingerprints as recorded "at consent-grant time".

## Required Changes

1. `src/lrh/gate_staleness.py`:
   - Replace the worktree-relative `FINGERPRINT_PATH` with a helper resolving
     `$(git rev-parse --git-common-dir)/lrh/chain-defaults-fingerprints.json`
     for `project_root`. `load_fingerprints` returns `None` (fail closed) if
     git resolution fails; the write path raises `GateStalenessError`.
   - No migration from the old `project/config/` path (nothing ever wrote it
     outside tests).
   - `record_fingerprints` raises (writing nothing) if any target is
     `unresolved` or any fingerprint-kind target file is missing; keeps the
     existing temp-file + `os.replace` atomic write; replaces the whole map
     (drops entries for targets no longer configured).
   - Add a pure `plan_fingerprints(project_root, targets, stored)` returning
     per-target name, absolute path, new hash, and comparison
     (`new`/`unchanged`/`changed`/`removed`), used by both `--dry-run` and
     the real write so preview and write cannot diverge.
   - When no fingerprint-kind targets exist (harness repo, or all targets
     git-tracked), report "nothing to fingerprint" and write nothing.
   - Update module comments/docstrings to describe the separate
     record action instead of "consent-grant time".
2. `src/lrh/cli/main.py`: add `lrh chain-defaults record-fingerprints
   [--project-root] [--dry-run] [--format text|json]`. Exit 0 on recorded
   or nothing-to-do; exit 2 on refusal/error, error text on stderr (matching
   `check-staleness`/`status` conventions). Update the "requires a
   subcommand" hint.
3. `src/lrh/skills/lrh-config-gates/SKILL.md` (and byte-identical
   `.claude/skills/lrh-config-gates/SKILL.md`):
   - Step 2 table: summarize fingerprint state from the status payload.
   - New Step 4b, wrapped in `GATE-DEFINITION` markers, asked as its own
     question (never combined with Step 3 or Step 4): run
     `lrh chain-defaults record-fingerprints --project-root <project-root>
     --dry-run`, present the table plus the plain-language statement that
     this accepts the *current* installed files as trusted gate text and that
     LRH cannot show what changed for `changed` entries (hashes only); wait
     for explicit confirm; run without `--dry-run`; re-read
     `lrh chain-defaults status --format json` and report the staleness
     result honestly.
   - Recommend Step 4b when status shows any "no persisted content
     fingerprint" or "differs from persisted fingerprint" reason; otherwise
     offer it as optional.
   - Step 5: note that fingerprint recording, like the consent grant, has
     nothing to commit. Update "What This Skill Does Not Do".
4. `src/lrh/skills/_shared/chain-defaults.md`: one sentence, **outside**
   any `GATE-DEFINITION` region, pointing a "no persisted content
   fingerprint" stale result at `/lrh-config-gates` as the remedy.
5. `docs/reference/cli/chain-defaults.md`: document `record-fingerprints`;
   correct the storage location and the "recorded at consent-grant time"
   wording.
6. Tests (`tests/gate_staleness_test.py` and the CLI/status test modules):
   - successful record writes the common-dir store atomically;
   - missing installed target file refuses and leaves any existing store
     untouched;
   - unresolved target refuses (regression for the `{}` bug);
   - missing and malformed store both fail closed (existing test repointed
     to the new path);
   - after recording, `status` shows those targets fresh, and
     `consent.valid`/`confirmed_commit` are unchanged;
   - installed content changed after recording → stale;
   - `--dry-run` writes nothing and reports new/unchanged/changed/removed;
   - two worktrees of one clone share the store; two independent clones do
     not;
   - harness-repo (no fingerprint-kind targets) → nothing to do, exit 0.

## Non-Goals

- Do not record fingerprints automatically, or as a side effect of a
  field-value change, a consent grant, or a `confirmed_commit` re-stamp.
- Do not change consent-hash semantics, `confirmed_commit` re-stamp rules,
  or the `closeout_with_merge` read-only policy.
- Do not weaken fail-closed behavior for missing/unresolved/mismatched
  targets, and do not change existing stale-file reporting semantics.
- Do not store gate-text snapshots to enable "show what changed" diffs for
  untracked targets — defer to a follow-up if wanted.
- Do not introduce marker-scoped fingerprinting — defer (noted in the
  origin WI's resolution).
- Do not edit any `GATE-DEFINITION` region of a watched skill file.

## Acceptance Criteria

- `lrh chain-defaults record-fingerprints` records atomically to the git
  common dir; `--dry-run` previews without writing.
- Recording refuses with exit 2 and an untouched store on any unresolved
  target or missing installed file; missing/malformed stores still fail
  closed.
- After recording, `lrh chain-defaults status` reports the targets as
  matching the persisted fingerprint; `consent.valid` and
  `confirmed_commit` are unchanged.
- `/lrh-config-gates` offers recording as its own confirmed step with a
  dry-run preview and a post-record status re-check.
- Worktrees of one clone share the store; independent clones do not.
- `lrh validate` reports 0 errors; `scripts/test` passes.

## Validation

- `scripts/version tools`
- `lrh validate`
- `scripts/format --check --diff`
- `scripts/lint`
- `scripts/test`
- `lrh chain-defaults record-fingerprints --project-root . --dry-run`
- `lrh chain-defaults status --project-root . --format json`
- `lrh skills check --target claude --local`

## Risk Notes

- Trust-on-first-use: recording accepts whatever is installed now. Mitigated
  by the separate confirm, the dry-run preview, and explicit wording that
  hashes cannot show what changed.
- `git rev-parse --git-common-dir` returns a relative path in some
  invocations; resolve it against `project_root`, and watch for the
  pathlib absolute-right-operand pitfall when joining.
- `_shared/chain-defaults.md` is a watched gate file in this repo; an edit
  inside a `GATE-DEFINITION` region would make this repo's own chain-defaults
  stale. Keep the added sentence outside markers.
- Re-cloning (or `git clone` of a client repo on a new machine) loses the
  store; this is intended and fails closed until the human re-records.
