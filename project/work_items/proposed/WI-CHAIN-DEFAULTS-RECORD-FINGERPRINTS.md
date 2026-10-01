---
resolution: null
blocked_reason: null
blocked: false
id: WI-CHAIN-DEFAULTS-RECORD-FINGERPRINTS
title: "Record installed-target gate fingerprints with every confirmed_commit re-stamp, including a new /lrh-config-gates re-confirm step"
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
  - project/work_items/resolved/WI-CHAIN-DEFAULTS-STALENESS-RESTAMP.md
  - project/memory/decisions/DEC-CHAIN-INIT-SKIP-CONSENT.md
  - project/memory/decisions/DEC-GATE-POLICY-CASCADE.md
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
  - bundle_restamp_with_consent_grant
  - restamp_without_explicit_confirm
  - record_fingerprints_without_restamp
  - change_consent_hash_binding
  - modify_closeout_with_merge
  - commit_fingerprint_file
acceptance:
  - "`lrh chain-defaults restamp --project-root <root>` records a SHA-256 fingerprint for every fingerprint-kind watch target (written atomically to `$(git rev-parse --git-common-dir)/lrh/chain-defaults-fingerprints.json`) and re-stamps `confirmed_commit`/`confirmed_at` in `project/config/chain-defaults.yaml` as one command; `--dry-run` previews the current stale-files list, the fingerprint plan (new/unchanged/changed/removed), and the new `confirmed_commit` without writing anything"
  - "`restamp` refuses (exit 2, neither the fingerprint store nor the profile touched) when any watch target is unresolved or any installed target file is missing; a missing, unreadable, or malformed store still fails every untracked target closed"
  - "The fingerprint store records the `confirmed_commit` it was written for, and `check_gate_staleness` accepts it only when that value equals the `confirmed_commit` it is checking against (the checkout's own `chain-defaults.yaml`); on a mismatch every fingerprint-kind target fails closed, so a store written without a matching committed profile (failed profile write, declined `main` push, or a branch still carrying the old profile) can never make a fingerprint-only repo read fresh"
  - "After a successful `restamp`, `lrh chain-defaults status` reports `stale: false` for every watch target (git and fingerprint kinds share the same confirmation baseline), and `consent.valid` is `false` per the existing whole-file blob-hash binding (`DEC-GATE-POLICY-CASCADE` Decision 4)"
  - "Every existing `confirmed_commit` re-stamp site in `_shared/chain-defaults.md` and its inlined copy in `lrh-land/references/land-workflow.md` uses `lrh chain-defaults restamp` instead of hand-writing the two fields, so no re-stamp path can update one baseline without the other"
  - "`/lrh-config-gates` offers a re-confirm step, asked as its own question, that shows the stale-files list verbatim plus the `--dry-run` plan, runs `restamp` only on explicit confirm, re-reads status, and then offers the existing skip-consent grant as a further separate question; `_shared/chain-defaults.md` names this step as a sanctioned re-stamp point"
  - "Two worktrees of one clone share the fingerprint store (each accepts it only when its own profile carries the matching stamp); two independent clones do not share it"
  - "`lrh validate` reports 0 errors, `scripts/test` passes, and `lrh skills check` reports the Claude, Codex, and Antigravity rendered targets up to date"
required_evidence:
  - manual_review
  - lrh_validate
  - test_output
artifacts_expected:
  - src/lrh/gate_staleness.py
  - src/lrh/chain_defaults_status.py
  - src/lrh/cli/main.py
  - src/lrh/skills/lrh-config-gates/SKILL.md
  - .claude/skills/lrh-config-gates/SKILL.md
  - .agents/skills/lrh-config-gates/SKILL.md
  - .gemini/plugins/lrh/skills/lrh-config-gates/SKILL.md
  - src/lrh/skills/_shared/chain-defaults.md
  - src/lrh/skills/lrh-land/references/land-workflow.md
  - .claude/skills/lrh-land/references/land-workflow.md
  - .agents/skills/lrh-land/references/land-workflow.md
  - .gemini/plugins/lrh/skills/lrh-land/references/land-workflow.md
  - docs/reference/cli/chain-defaults.md
  - tests/gate_staleness_test.py
  - tests/chain_defaults_status_test.py
  - tests/cli_tests/chain_defaults_test.py
---

# WI-CHAIN-DEFAULTS-RECORD-FINGERPRINTS

## Summary

Make every `confirmed_commit` re-stamp also record content fingerprints for
user-scope (untracked) installed gate-bearing skill files, via one new
command, `lrh chain-defaults restamp`. The command is used at the chain
gate's existing re-stamp points and at a new, separately confirmed
re-confirm step in `/lrh-config-gates`. The goal is that `skip_if_opted_in`
can take effect in client repos, without weakening fail-closed staleness and
without giving git-tracked and fingerprinted targets different confirmation
baselines.

## Problem / Context

`WI-GATE-STALENESS-INSTALLED-TARGET-FINGERPRINT` (PR #649) taught
`check_gate_staleness` to compare untracked installed targets (e.g. the
default `~/.claude/skills/...` install) against persisted content
fingerprints, and added `gate_staleness.record_fingerprints()`. Its
resolution deferred the remaining step: "wire record_fingerprints into a real
consent-grant call site once one exists." Nothing outside tests ever calls it
(`git grep -n "record_fingerprints(" -- src` matches only its definition at
`src/lrh/gate_staleness.py:469`).

As a result, in every client repo with a user-scope install:

- every watch target reports "no persisted content fingerprint on record ...
  failing closed";
- `staleness.stale` is permanently `true`;
- `skip_if_opted_in` can never take effect.

This was observed live in the LCATS project: the consent hash was valid,
`chain_init_confirmation` was `skip_if_opted_in`, every installed Claude
target was stale, and no fingerprint file existed.

Design decisions (from the `/lrh-design` session that produced this item,
revised during PR #753 review):

- **Recording is part of the re-stamp, never a separate act.** Git-tracked
  targets are compared against `confirmed_commit`
  (`src/lrh/gate_staleness.py:528`). Fingerprinted targets are compared
  against whenever the fingerprints were recorded. `record_fingerprints`
  was always meant to run "alongside stamping `confirmed_commit`"
  (`src/lrh/gate_staleness.py:475-476`). If recording could happen on its
  own, "stale" would mean "changed since you last confirmed" for one kind of
  target and "changed since someone last recorded" for the other. It would
  also create a way to clear staleness without the canonical stale path
  (`src/lrh/skills/_shared/chain-defaults.md:254-300`), which shows the
  stale-files list and requires a live confirmation before re-stamping. A
  single `restamp` command does both writes. The store also records the
  stamp it was written for and is accepted only against a profile carrying
  that same stamp. Without that binding, a store written but never followed
  by a committed profile would make a fingerprint-only client repo read
  fresh while its old consent stayed valid (found in PR #753 review).
- **`/lrh-config-gates` becomes a second sanctioned re-stamp point.** Today
  only the chain gate re-stamps (`src/lrh/skills/lrh-config-gates/SKILL.md:152-156`,
  `:265-267`). This item adds a config-gates re-confirm step that shows the
  same stale-files payload the chain gate would, and amends
  `_shared/chain-defaults.md` to name it. A user can then clear staleness
  and renew consent in one sitting, as two separately confirmed actions.
- **Consent-hash binding is unchanged.** `DEC-GATE-POLICY-CASCADE.md:56-57`
  and `_shared/chain-defaults.md:59-62` bind skip consent to the whole
  `chain-defaults.yaml` blob hash. A re-stamp therefore invalidates consent,
  and a regrant (config-gates Step 4) is needed afterwards. That costs one
  regrant per gate change, the same as for git-tracked targets today; it is
  not a loop. The original `DEC-CHAIN-INIT-SKIP-CONSENT.md:88-96` bound
  consent only to the condition values, and nothing has argued for the
  re-stamp-invalidates-consent coupling since (`WI-CHAIN-DEFAULTS-STALENESS-RESTAMP`
  never mentions consent). Removing that coupling would need a
  `DEC-GATE-POLICY-CASCADE` Decision 4 amendment, so it is out of scope
  here.
- **Clone-local storage in the git common dir**, not `project/config/`:
  - fingerprints describe one machine's installed files, so committing them
    would spread environment-specific state;
  - LRH cannot control client-repo `.gitignore` files;
  - an untracked file under the worktree would be missing in every new
    worktree.

  `$(git rev-parse --git-common-dir)/lrh/` matches the consent hash's scope:
  per clone, shared across worktrees.
- **Latent bug to fix:** `record_fingerprints` currently skips `unresolved`
  targets and writes `{}` successfully. That contradicts its own docstring
  ("must not silently record an empty/partial fingerprint set").
- **Hashes only, in either location.** Neither the chain gate nor
  config-gates can show *what* changed in a user-scope target: only hashes
  are stored, and the reasons come from `src/lrh/gate_staleness.py:545-567`.
  Content snapshots are deferred.
- **Correction to the seeding suggestion.** It cited
  `src/lrh/skills/_shared/chain-defaults.md:113-128` as documenting
  fingerprint recording at consent time, but that file never mentions
  fingerprints. The "consent-grant time" wording appears only in:
  - the `record_fingerprints` docstring;
  - the `FINGERPRINT_PATH` comment;
  - `docs/reference/cli/chain-defaults.md:96`.

  This item corrects all three.

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
- Add one product-facing command, `lrh chain-defaults restamp`, that re-stamps `confirmed_commit`/`confirmed_at` and records fingerprints as one act.
- Route every existing chain-gate re-stamp through that command.
- Add a separately confirmed re-confirm step to `/lrh-config-gates`, and name it in the shared policy.
- Correct the docs and docstrings that describe fingerprints as recorded "at consent-grant time".

## Required Changes

1. `src/lrh/gate_staleness.py`:
   - Replace the worktree-relative `FINGERPRINT_PATH` with a helper that
     resolves `$(git rev-parse --git-common-dir)/lrh/chain-defaults-fingerprints.json`
     for `project_root`. `load_fingerprints` returns `None` (fail closed) if
     git resolution fails; the write path raises `GateStalenessError`.
   - Do not migrate from the old `project/config/` path. Nothing ever wrote
     it outside tests.
   - Bind the store to the stamp. The store's JSON becomes
     `{"confirmed_commit": "<sha>", "fingerprints": {<name>: <sha256>}}`.
     - `check_gate_staleness` already receives `confirmed_commit`. It
       accepts the store only when the store's `confirmed_commit` equals
       that value.
     - On a mismatch, every fingerprint-kind target fails closed with a
       distinct reason ("fingerprint store was recorded for a different
       `confirmed_commit` -- failing closed").
     - A store without the `confirmed_commit` key (including the old bare
       map) is malformed and fails closed.

     This makes the shared baseline mechanical, not a matter of write order.
     It matters most in a client repo where every target is
     fingerprint-kind (`src/lrh/gate_staleness.py:429`, `:623`). There, a
     store without the binding would make `stale` false whenever it was
     written, even if no profile carrying the matching stamp was ever
     committed.
   - Add a pure `plan_fingerprints(project_root, targets, stored)`. It
     returns, per target: name, absolute path, new hash, and a comparison
     (`new`/`unchanged`/`changed`/`removed`). `--dry-run` and the real write
     both use it, so the preview and the write cannot diverge.
   - `record_fingerprints` must check every target before writing anything:
     - it raises, writing nothing, if **any** target is `unresolved` or any
       fingerprint-kind target file is missing;
     - it keeps the existing temp-file + `os.replace` atomic write;
     - it replaces the whole map.
   - "Nothing to do" happens only when all of these hold: every target
     resolved successfully, there are zero fingerprint-kind targets, and the
     stored map is absent or empty (e.g. the harness repo). If stored entries
     exist but no fingerprint-kind targets remain, write an empty map so the
     previewed `removed` entries actually go away.
   - Update module comments and docstrings to describe recording as part of
     the re-stamp, not "consent-grant time".
2. `src/lrh/chain_defaults_status.py` (or a sibling module): add the
   re-stamp operation. It:
   - validates the fingerprint plan first;
   - computes the new stamp, `confirmed_commit` = `git rev-parse HEAD`;
   - writes the fingerprint store, bound to that same stamp;
   - rewrites only the `confirmed_commit:` and `confirmed_at:` lines of
     `project/config/chain-defaults.yaml` in place, to that same stamp,
     keeping comments and every other field byte-identical.

     Because of the binding, the store-then-profile order is safe. A store
     whose stamp no checkout's profile carries yet is simply not accepted.
   - requires the profile file to exist. The first-encounter "file absent"
     path keeps writing the file first and then calls `restamp`.
3. `src/lrh/cli/main.py`: add `lrh chain-defaults restamp [--project-root]
   [--dry-run] [--format text|json]`.
   - `--dry-run` prints the current stale-files list (the same payload as
     `check-staleness`), the fingerprint plan, and the proposed
     `confirmed_commit`/`confirmed_at`.
   - Exit codes: 0 on success; 2 on refusal or error, with the error text on
     stderr (matching the `check-staleness` and `status` conventions).
   - Update the "requires a subcommand" hint.
4. `src/lrh/skills/_shared/chain-defaults.md` and its inlined copy in
   `src/lrh/skills/lrh-land/references/land-workflow.md` (keep them in
   sync):
   - replace each hand-written `confirmed_commit: $(git rev-parse HEAD)` /
     `confirmed_at: ...` re-stamp instruction (currently
     `_shared/chain-defaults.md:84`, `:287`, and the Decision 4
     profile-update re-stamp at `:111`) with `lrh chain-defaults restamp`;
   - name `/lrh-config-gates`'s re-confirm step as a sanctioned re-stamp
     point with the same re-stamp condition: the stale-files payload was
     shown, and the live reply agrees with the persisted text;
   - point a "no persisted content fingerprint" stale result at either
     remedy (the next chain run's live gate, or `/lrh-config-gates`).

   These edits are inside `GATE-DEFINITION` regions on purpose. They change
   how a gate is cleared, so this repo's own chain-defaults will show as
   stale once. That is the correct outcome.
5. `src/lrh/skills/lrh-config-gates/SKILL.md`:
   - Step 2 table: summarize fingerprint state from the status payload.
   - Add a re-confirm step, wrapped in `GATE-DEFINITION` markers, asked as
     its own question and never combined with Step 3 or Step 4:
     - run `lrh chain-defaults restamp --project-root <project-root> --dry-run`;
     - present the stale-files list verbatim and the fingerprint plan;
     - state plainly that this accepts the *current* gate text of the
       watched files as confirmed, and that for `changed` user-scope entries
       LRH can show only that the content differs, not what changed;
     - wait for explicit confirmation, then run `restamp`;
     - re-read `lrh chain-defaults status --format json` and report
       staleness honestly;
     - say that the re-stamp invalidated skip consent, then offer Step 4's
       consent grant as a separate question.
   - Recommend the step when status shows `stale: true`; otherwise offer it
     as optional.
   - Step 5: widen its trigger. Today it runs only "if Step 3 made changes"
     (`SKILL.md:210-213`), so a re-stamp on its own would never be committed.
     It must also run when the re-confirm step re-stamped. The consent grant
     alone still has nothing to commit.
   - Re-confirm on a PR branch: if `<project-root>` is on a feature branch
     tied to an open PR, do not commit the re-stamp onto that branch. The
     stamp would name a commit that is not on `main`, and it would mix
     policy state into an unrelated PR. The step always runs on Step 5's
     `main` path:
     - create the tmp branch from `origin/main`;
     - run `restamp` there, so `confirmed_commit` = `origin/main`'s HEAD;
     - commit;
     - get the explicit push-to-`main` confirmation Step 5 already requires;
     - push;
     - return to the original branch.

     If the user declines the `main` push, report that the profile is
     unchanged on `main`. The fingerprint store has already been written to
     the common dir, so the re-stamp must be re-run from `main` later.
   - Replace the "does not re-stamp" statements (`SKILL.md:152-156`,
     `:265-267`) to match.
6. Rendered skill targets: regenerate the `.claude`, `.agents` (Codex), and
   `.gemini` (Antigravity) copies of `lrh-config-gates` and `lrh-land` with
   the project's skills installer, and confirm every target is up to date.
7. `docs/reference/cli/chain-defaults.md`:
   - document `restamp`;
   - correct the storage location;
   - correct the "recorded at consent-grant time" wording.
8. Tests (`tests/gate_staleness_test.py`, `tests/chain_defaults_status_test.py`,
   `tests/cli_tests/chain_defaults_test.py`). Cover each case below:
   - successful `restamp` writes the common-dir store atomically and
     updates only the two profile lines;
   - a missing installed target file refuses and leaves the store and the
     profile untouched;
   - an unresolved target refuses (regression for the `{}` bug), including
     when every target is unresolved;
   - a missing store fails closed, and so does a malformed one (the existing
     test repointed to the new path), including an old-format bare map with
     no `confirmed_commit`;
   - stamp binding, in a fixture where every target is fingerprint-kind:
     - a store whose `confirmed_commit` differs from the profile's fails
       every target closed with the distinct reason;
     - after `restamp` writes the store but the profile write fails, status
       is stale and consent is unchanged;
     - after `restamp` succeeds on one worktree, a second worktree whose
       profile still has the old stamp reads stale;
   - after `restamp`, `status` reports `stale: false` and `consent.valid:
     false`;
   - installed content changed after `restamp` → stale;
   - `--dry-run` writes nothing and reports the stale-files list, the
     `new`/`unchanged`/`changed`/`removed` plan, and the proposed stamp;
   - stored entries with no remaining fingerprint targets → the empty map is
     written;
   - two worktrees of one clone share the store; two independent clones do
     not;
   - harness repo with no stored map → nothing-to-do for fingerprints, and
     the stamp is still written.

## Non-Goals

- Do not record fingerprints outside a `restamp`, and do not re-stamp as a
  side effect of a field-value change or a consent grant.
- Do not change consent-hash binding. Removing the
  re-stamp-invalidates-consent coupling needs a `DEC-GATE-POLICY-CASCADE`
  Decision 4 amendment, which belongs in its own proposal.
- Do not change the `closeout_with_merge` read-only policy.
- Do not weaken fail-closed behaviour for missing, unresolved, or mismatched
  targets, and do not change existing stale-file reporting semantics.
- Do not store gate-text snapshots to show what changed in untracked targets.
  Defer that to a follow-up if wanted.
- Do not introduce marker-scoped fingerprinting. That is deferred, as noted
  in the origin WI's resolution.

## Acceptance Criteria

- `lrh chain-defaults restamp` re-stamps `confirmed_commit`/`confirmed_at`
  and atomically records fingerprints to the git common dir as one command.
  `--dry-run` previews the stale list, the fingerprint plan, and the stamp
  without writing.
- `restamp` refuses with exit 2 on any unresolved target or missing installed
  file, and leaves both the store and the profile untouched. A missing or
  malformed store still fails closed.
- The store is bound to the stamp it was written for. A store whose
  `confirmed_commit` doesn't match the checkout's profile fails every
  fingerprint-kind target closed. This holds even in a fingerprint-only
  client repo, and covers a failed profile write, a declined `main` push,
  and a branch still carrying the old profile.
- After `restamp`, `lrh chain-defaults status` reports `stale: false`, and
  `consent.valid: false` per the existing blob-hash binding.
- Every re-stamp site in `_shared/chain-defaults.md` and
  `lrh-land/references/land-workflow.md` uses `restamp`.
- `/lrh-config-gates` offers a separately confirmed re-confirm step:
  - it shows the stale-files list and the dry-run plan;
  - it re-reads status afterwards;
  - it then offers the consent grant as its own question.

  `_shared/chain-defaults.md` names this step as a sanctioned re-stamp
  point.
- Worktrees of one clone share the store, and each accepts it only when its own profile carries the matching stamp. Independent clones do not share it.
- `lrh validate` reports 0 errors, `scripts/test` passes, and every rendered
  skill target is up to date.

## Validation

- `scripts/version tools`
- `lrh validate`
- `scripts/format --check --diff`
- `scripts/lint`
- `scripts/test`
- `lrh chain-defaults restamp --project-root . --dry-run`
- `lrh chain-defaults status --project-root . --format json`
- `lrh skills check --target claude --local`
- `lrh skills check --target codex --local`
- `lrh skills check --target antigravity --local`

## Risk Notes

- **Trust-on-first-use.** A re-stamp accepts whatever is installed now as
  confirmed. Mitigations:
  - the separate confirm;
  - the stale-files list and dry-run preview;
  - explicit wording that hashes cannot show what changed.
- **Partial failure.** `restamp` writes the fingerprint store before the
  profile. If the profile write fails, the store's stamp matches no
  profile, so every fingerprint-kind target fails closed (Required
  Changes 1). Git-tracked targets also stay stale against the old
  `confirmed_commit`. The next run takes the live path even in a
  fingerprint-only client repo. Report the error and do not retry
  silently.
- **Re-stamp from a PR branch.** Two cases:
  - **Chain run.** Per existing practice, a chain run on a PR branch defers
    the re-stamp to closeout, and `restamp` defers with it, since the two
    must stay one act.
  - **`/lrh-config-gates`.** The re-confirm step never re-stamps onto a PR
    branch; it always goes through Step 5's `main` path (see Required
    Changes 5).

  In both cases `confirmed_commit` names a commit on `main`.
- **Declined `main` push after the store was written.** The store's stamp
  then exists only on the discarded tmp branch, so no checkout's profile
  matches it, and every fingerprint-kind target fails closed. This covers
  fingerprint-only repos too. Report the declined push plainly; the user
  re-runs the re-confirm step later.
- **Shared store, branch-local profile.** The store lives in the clone's
  common git dir, but each branch carries its own `chain-defaults.yaml`.
  After a successful re-stamp lands on `main`, any branch whose profile
  still has the old stamp reads stale until it picks up `main`. That is the
  intended fail-closed result: such a branch cannot use the new baseline
  together with its old, still-valid consent.
- **Relative git common dir.** `git rev-parse --git-common-dir` returns a
  relative path in some invocations. Resolve it against `project_root`, and
  watch for the pathlib pitfall where joining onto an absolute right-hand
  path discards the left.
- **Editing `GATE-DEFINITION` regions** of `_shared/chain-defaults.md` and
  `land-workflow.md` makes this repo's own chain-defaults stale once. The
  implementing run's own chain gate must show it and re-confirm normally.
- **Re-cloning loses the store** (including `git clone` of a client repo on a
  new machine). This is intended: it fails closed until the next re-stamp.
