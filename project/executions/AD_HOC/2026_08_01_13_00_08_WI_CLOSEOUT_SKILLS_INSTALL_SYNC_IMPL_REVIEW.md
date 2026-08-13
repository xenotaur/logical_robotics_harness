---
execution_id: 2026_08_01_13_00_08_WI_CLOSEOUT_SKILLS_INSTALL_SYNC_IMPL_REVIEW
prompt_id: PROMPT(AD_HOC:WI_CLOSEOUT_SKILLS_INSTALL_SYNC_IMPL_REVIEW)[2026-08-01T12:59:59-04:00]
work_item: AD_HOC
status: landed
rerun_of: 2026_08_01_12_42_29_WI_CLOSEOUT_SKILLS_INSTALL_SYNC_IMPL
pr: https://github.com/xenotaur/logical_robotics_harness/pull/456
commit: 63820e567304a13cd13d2324bf463da460944727
created_at: 2026-08-01T13:00:08-04:00
agent: claude_app
instruction_source: https://github.com/xenotaur/logical_robotics_harness/pull/456
session_transcript: claude-app:20d16dd9-a465-4d31-b39f-280db14488ef
---

# Summary

Addressed review feedback on PR #456 from Codex (bound to commit
`f64778f`) and Copilot (bound to commit `f44f826`, the initial push).

# Result

- Codex, P1 "Verify the checkout matches merged main before refreshing"
  — **confirmed valid** (checked: `/lrh-closeout` has no step anywhere
  that verifies its invoking checkout matches `origin/main` before this
  PR's changes; the skill-refresh step's `PYTHONPATH="$(pwd)/src")`
  pins *which* checkout is loaded but does nothing to establish that
  `$(pwd)` is current). Added an explicit `git fetch origin main` +
  `git rev-parse HEAD`/`git rev-parse origin/main` comparison before
  Step 2 computes "current" `_skill_names()` membership, with an
  explicit skip-this-item-not-the-whole-closeout fallback if they don't
  match and can't be reconciled in-session; cross-referenced from Step 5.
- Copilot: `install_named_skills()` called `target.mkdir(...)` inside the
  per-name loop — redundant repeated syscalls. **Confirmed valid, minor.**
  Moved to a single conditional call before the loop (only when at least
  one name is actually valid), verified behavior unchanged via a manual
  smoke test (an all-absent call still creates no directory).
- Copilot (x2 duplicate threads): the SKILL.md frontmatter description's
  phrase "refreshing any global skill install the PR touched" read as
  awkward/ambiguous. **Confirmed valid, minor.** Reworded to "refreshing
  the global skill install for any skill the PR modified."
- All fixes applied to `src/lrh/skills/installer.py` and
  `.claude/skills/lrh-closeout/SKILL.md` (mirrored to
  `src/lrh/skills/lrh-closeout/SKILL.md`).
- Pushed as commit `ec39369`.

**Round 2** — retriggered both reviewers against `95f7a2a` (Copilot
landed there directly; Codex's clean pass on the same commit arrived as
an issue comment, not a formal review — matches the known pattern).
Copilot's fresh pass on the test file raised 3 new suppressed comments,
all confirmed valid:
- `tests/skills_installer_test.py:97` — `names[1]` assumes ≥2 packaged
  skills exist with no explicit assertion; an IndexError on failure would
  be unclear. Added `assertGreaterEqual(len(names), 2, ...)`.
- `tests/skills_installer_test.py:135` — the "absent name with no
  existing dir creates nothing" test called `install_skills()` first,
  which itself creates `skills_dir` — so the test never actually
  exercised the mkdir-skip behavior the round-1 fix introduced. Removed
  that call so `skills_dir` genuinely doesn't exist beforehand, and added
  an assertion that it still doesn't exist afterward.
- `src/lrh/skills/installer.py:248` — `Sequence[str]` also accepts a bare
  `str` at runtime, which would iterate character-by-character (e.g.
  `"lrh-closeout"` → refresh attempts for `"l"`, `"r"`, ...). Added an
  explicit `isinstance(skill_names, str)` guard raising `TypeError`, plus
  a new test asserting it.
- Pushed as commit `edd9e6e`.

# Validation

- `python3 -m pytest tests/skills_installer_test.py`: 27/27 pass (26 →
  27 after the new bare-string-guard test)
- `scripts/format --check --diff`, `scripts/lint`: clean (after
  `scripts/lint --fix` reformatted the mkdir-hoist change)
- `lrh validate`: 0 errors, 1 pre-existing unrelated warning
- `diff -r .claude/skills/lrh-closeout src/lrh/skills/lrh-closeout`:
  identical
- Manual smoke test: `install_named_skills(['not-a-real-skill'], ...)`
  against an empty skills dir creates no directory (mkdir-hoist fix
  didn't change the all-absent behavior)

**Round 3** — retriggered both reviewers against `3f1381f`. Codex clean.
Copilot raised 1 new finding, confirmed valid: `install_named_skills()`
now iterates `skill_names` twice (round-1's mkdir-hoist intersection
check, then the main loop) — a caller passing a one-shot iterable (e.g.
a generator) that merely duck-types as `Sequence[str]` would have it
silently consumed by the first pass, refreshing nothing with no error.
Fixed by materializing `skill_names` into a `list` once at the top of
the function, used for both passes. Added a test with a generator
input to cover it. Pushed as commit `0489550`.

**Round 4** — retriggered both reviewers against `09511c6`. Codex clean.
Copilot raised 3 findings (2 duplicates of the same underlying issue),
all confirmed valid:
- The implementation record's `## Validation`/`## Result` sections
  reported stale test counts ("26/26", "4 new tests") that hadn't kept
  up with tests added in rounds 2–3. Fixed to the final accurate count
  (28/28, 6 new tests, named individually) — editing that record's body
  is normal authoring since PR #456 hasn't merged yet, not a rewrite of
  an already-landed record.
- The `installer.py` comment describing the double-iteration fix said a
  generator would "duck-type as `Sequence[str]`" — imprecise; a
  generator doesn't satisfy the `Sequence` protocol at all (no
  `__getitem__`/`__len__`), it's merely an `Iterable`. Reworded.
- Pushed as commit `1dbb9fe`.

**Round 5** — retriggered both reviewers against `80641dc`. Codex clean.
Copilot raised 5 findings (3 duplicates of one issue, across 3 lines
plus 2 duplicate copies of a second issue across both mirrored SKILL.md
files), both underlying issues confirmed valid:
- Round 3's materialize-once fix changed the function's actual accepted
  input to any one-shot-safe iterable (tested with a generator), but the
  type hint stayed `Sequence[str]` — inaccurate for callers and static
  type checkers. Changed the import and signature to `Iterable[str]`,
  and reworded the `TypeError` message/comment to match (no longer
  claiming the Sequence protocol).
- Step 2's checkout-freshness verification only branched on "`HEAD` and
  `origin/main` don't match" — it never explicitly said what to do if
  `git fetch origin main` itself fails (offline/auth/rate-limit), only
  implying it via a vague "if neither is possible" clause. Split into two
  explicit cases: fetch failure (skip this item immediately, same as the
  other anomaly cases) vs. fetch-succeeded-but-mismatched (attempt to get
  current, else skip).
- Pushed as commit `7f9326c`.

**Round 6** — retriggered against `f97130a`; both reviewers fully clean
(Copilot 0 comments, Codex "Didn't find any major issues"). Treated as
review-response complete and moved to `/lrh-confirm-fixes`.

**Confirm-fixes finding: 4 real threads missed during review-response.**
Confirm-fixes's cold-subagent verification (this session authored every
prior fix, so independence was required) found that 4 Codex threads
(P1/P2, all `outdated: false`) had accumulated across rounds 3–5 that
were never actually read or addressed — this session was checking
unresolved-thread *counts* each round but trusting the review-body
summary text ("Codex: clean") without re-reading the full thread list's
*content* each time, missing threads that arrived without a corresponding
summary-body mention. Verified each against the actual diff/repo before
accepting:
- P2 "Scope refreshes to checkouts containing the LRH package" —
  **confirmed valid**: `/lrh-closeout` is a reusable skill installed into
  independent client repos, which can have their own project-local
  `.claude/skills/<name>/` unrelated to LRH's own `src/lrh/skills/`
  package. Added an explicit precondition to Step 2: skip the entire
  skill-refresh item (not an anomaly, genuinely not-applicable) if
  `src/lrh/skills/` doesn't exist in the invoking checkout.
- P2 "Verify the checkout is actually on main" — **confirmed valid**: the
  prior check only compared commit SHAs (`HEAD` vs `origin/main`), which
  a detached HEAD or same-commit feature branch would pass without
  actually being on `main`. Added an explicit `git branch --show-current`
  check (must print exactly `main`) alongside the SHA comparison — smoke
  tested live: this session's own checkout shows `HEAD` can equal a
  fetched ref while `git branch --show-current` correctly reports the
  actual (non-`main`) branch name, confirming the gap was real.
- P2 "Defer checkout mutations until after confirmation" — **confirmed
  valid, and the most structural of the four**: Step 2's prior text ran
  `git checkout main && git pull` during the read-only assessment phase,
  before the Step 4 confirm gate that promises no files are touched
  beforehand. Redesigned so Step 2 computes *both* base-revision and
  current-`main` membership via pure `git ls-tree <rev>:src/lrh/skills`
  reads (smoke tested: `git ls-tree -d --name-only origin/main:src/lrh/skills`
  correctly lists all 14 current skills with zero working-tree mutation),
  eliminating the need for any checkout/Python-import in Step 2 at all.
  The actual `git checkout main && git pull` + branch-identity
  verification now happens only in Step 5, after the gate, immediately
  before invoking `install_named_skills`.
- P2 "Fetch the base SHA from PR metadata" — **confirmed valid**: the
  REST PR Files endpoint's response has no PR-level base-SHA field, so
  "the same PR API call above" was never a real way to obtain
  `<baseRefOid>` — only `gh pr view --json baseRefOid` (or the REST
  pull-request object's own `.base.sha`) works. Removed the false option;
  the base SHA is now sourced explicitly and only from PR metadata.
- Also updated the Quality Checklist and "What This Skill Does Not Do"
  to reflect the restructured (read-only Step 2 / mutating Step 5)
  design and the client-repo scoping decision.
- Pushed as commit `e2bda3b`.

**Round 7** — retriggered against `c967ef5`, explicitly re-reading full
thread content this time (not just review-body summaries). One thread
from the earlier missed batch was already resolved by the round-6
restructure (content-verified, though its `isOutdated` flag never
flipped — its anchor apparently wasn't tied to a line that specific fix
touched). 2 genuinely new threads, both confirmed valid, both fairly
significant:
- P1 "Reject PRs that were not merged into main" — **confirmed valid**:
  Step 2 item 1 checks only `state`/`mergeCommit`, never `baseRefName` —
  a PR merged into a release branch instead of `main` would still have
  this assessment read `origin/main` as "current," silently misreading
  which branch the merge actually landed on. Added a third precondition
  to Step 2 requiring `baseRefName == main`; skip (not-applicable, not an
  anomaly) otherwise.
- P2 "Accept the locked-main temporary branch" — **confirmed valid, and
  a real regression from round 6's own fix**: round 6 added a
  `git branch --show-current` == `"main"` requirement, which would
  reject `/lrh-land`'s own documented `tmp-<slug>` main-worktree-lock
  workaround (used earlier in this very session, for this WI's own
  creation-PR closeout) — that workaround never literally checks out a
  branch named `main` until the final push. Replaced the branch-name
  check with `git merge-base --is-ancestor origin/main HEAD`, which
  accepts both plain `main` and the `tmp-<slug>` case uniformly (smoke
  tested live: this session's own worktree, on a branch created before
  a concurrent PR #452 merged, correctly failed the check — proving it
  detects genuine staleness, not just branch-naming mismatches).
- Pushed as commit `48d7893`.

**Round 8** — retriggered against `60901f4`, again reading full thread
content. 2 new threads, both confirmed valid, both P1/P2 refinements of
round 7's own fixes:
- P1 "Pin refreshes to the merged main tree" — **confirmed valid, a real
  gap in round 7's own ancestry check**: `git merge-base --is-ancestor
  origin/main HEAD` accepts *every* descendant of `origin/main`,
  including one with an additional never-merged commit that further
  edits a touched skill — `install_named_skills` would then install
  those unmerged bytes while reporting `refreshed`. Replaced with a
  direct tree-hash comparison, `git rev-parse HEAD:src/lrh/skills` ==
  `git rev-parse origin/main:src/lrh/skills` (smoke tested live: this
  session's own checkout, which has committed changes to
  `src/lrh/skills` not yet on `origin/main`, correctly produces two
  *different* hashes) — precise in both directions, still accepts the
  `tmp-<slug>` workaround since closeout's own commits never touch
  `src/lrh/skills/` itself.
- P2 "Fetch the recorded base object before reading its tree" —
  **confirmed valid**: having `<baseRefOid>` as a string from PR
  metadata doesn't guarantee that commit object is present locally,
  particularly in a shallow clone where `git fetch origin main` only
  fetches `main`'s shallow tip. Added an explicit
  `git cat-file -e <baseRefOid> || git fetch origin <baseRefOid>` guard
  (with an `--unshallow`/`--deepen` fallback) before the `git ls-tree
  <baseRefOid>:...` read, treated as the same anomaly-and-skip pattern
  as other fetch failures if the object still can't be made available.
- Pushed as commit `906613a`.

**Round 9** — retriggered against `05cdc23`. 2 new threads, both
confirmed valid:
- P1 "Bind the refresh checkout to the PR repository" — **confirmed
  valid**: the `src/lrh/skills/` presence precondition rules out an
  unrelated client repo, but not a *different* LRH checkout (a fork or
  second clone) whose `origin/main` has genuinely diverged from the PR's
  own repository — the REST PR Files listing is always fetched from the
  PR's own `<owner>/<repo>`, but every git-level read used whatever
  `origin` locally pointed to. Added a third precondition: `git remote
  get-url origin` must resolve to the same `<owner>/<repo>` as the PR
  being closed out (smoke tested live: this checkout's origin correctly
  resolves to `xenotaur/logical_robotics_harness.git`).
- P1 "Replace the stale ancestry check in the checklist" — **confirmed
  valid, a self-inflicted consistency bug**: round 8 replaced the main
  narrative's ancestry check with an exact tree-hash comparison, but the
  Quality Checklist item still described the old (now-known-unsafe)
  ancestry check. Fixed the checklist to match.
- Pushed as commit `16277f2`.

Noting a pattern shift: this round's second finding was a propagation
slip in this session's own prior fix, not a new independent design gap
— a signal that the feature's documentation has grown complex enough to
create its own consistency surface area. Plan: one more retrigger; if it
surfaces only textual/consistency nits or false positives (not a new
substantive design gap), treat that as the natural stopping point and
move to a final self-review pass before merge, per the pattern that
worked well on the WI-creation PR (#454).

**Round 10** — retriggered against `ca55353`. 3 new findings, all
confirmed valid:
- Codex P1 "Check the working tree before installing" — **confirmed
  valid, a distinct failure mode from the earlier descendant-commit
  issue**: the tree-hash comparison only reads *committed* git objects;
  `install_named_skills` imports live via `PYTHONPATH`, which reads
  whatever bytes are actually on disk. An uncommitted or untracked
  change under `src/lrh/skills/<name>/` would leave both `rev-parse`
  hashes equal while the Python import picks up the dirty bytes anyway.
  Added a `git status --porcelain -- src/lrh/skills` (must be empty)
  requirement alongside the tree-hash check.
- Copilot: `install_named_skills()` doesn't validate that each element of
  `skill_names` is actually a `str` (a non-`str` element could produce
  confusing behavior or an unclear low-level error). **Confirmed valid,
  minor.** Added an explicit per-element `isinstance` check raising
  `TypeError`.
- Copilot: suggested test coverage for the above. Added
  `test_non_string_element_raises_type_error`.
- Pushed as commit `5d3d14b`.

10 rounds in, still finding genuinely distinct, valid data-correctness
gaps each time (not diminishing into nits) — this is a
`USER_MODIFIED`-bypassing mutation of the user's own machine, so the
scrutiny is proportionate to the stakes. Continuing the retrigger loop
rather than switching strategy, since each round is still closing real
gaps, not just consistency slips.

**Round 11** — retriggered against `62737c7`. Copilot fully clean. 1 new
Codex finding, confirmed valid: "Reject ignored files before refreshing
skills" (P1) — `git status --porcelain` doesn't report gitignored
entries by default, but `_copy_resource_tree` enumerates every real
filesystem entry under a skill directory regardless of `.gitignore`, so
a stray `.DS_Store` or similar sitting inside a confirmed skill directory
would be silently copied. Confirmed live: placed a `.DS_Store` inside
`src/lrh/skills/lrh-closeout/` — invisible to plain `git status
--porcelain`, reported as `!!` with `--ignored` (which also surfaced a
genuinely present `src/lrh/skills/__pycache__/` in this session's own
checkout). Added `--ignored` to the working-tree cleanliness check.
Pushed as commit `2072b8e`.

11 rounds in, this finding is narrower than the last several (requires a
stray file specifically inside a skill directory, a fairly contrived
scenario) — a possible signal of the working-tree/checkout-verification
vein running out of genuinely new gaps, though each round has still been
valid rather than a false positive. Plan: one more retrigger; if it
surfaces only a further narrow refinement of this same check (not a new
independent category of gap), switch to a final self-review pass and
close out review-response rather than continuing indefinitely.

**Round 12** — retriggered against `39eb0ad`. 2 findings, both confirmed
valid but narrower/more nuanced than prior rounds:
- Codex P2 "Move repository fetches behind the confirmation gate" —
  **partially valid, applied a precise fix rather than the literal
  ask**: the routine `git fetch origin main` is harmless git housekeeping
  (updates remote-tracking refs only, never touches tracked files or
  branches) and moving it behind the gate would be over-broad — but the
  shallow-clone fallback's `git fetch --unshallow` is a materially
  heavier, one-way operation (full-history download, permanent
  shallow→full conversion) that should not happen silently pre-gate.
  Removed the auto-unshallow escalation entirely — an unreachable base
  object now reports an anomaly and skips the item, same as any other
  fetch failure, rather than performing an undisclosed heavy mutation.
  Also corrected the imprecise "no command... writes to disk" claim to
  state precisely what the read-only guarantee actually covers (tracked
  files/branches/`~/.claude/skills/`, not git's own ref bookkeeping).
- Copilot: the implementation record's "Added 6 new tests" line was
  stale again (7 now, after round 10's addition). **Confirmed valid.**
  Fixed, and reworded to point to the `_REVIEW` record as the
  authoritative round-by-round count going forward, rather than trying
  to keep re-syncing a number in an increasingly-edited narrative section.
- Pushed as commit `a6708c3`.

**Strategy shift, per the plan noted after round 11.** This round's
findings were narrower/more nuanced than rounds 1–10 (a precision
refinement of an already-comprehensive design, plus a recurring
self-consistency nit) rather than a new fundamental correctness gap.
Doing one more retrigger to confirm this round lands clean; if so,
switching to a final self-review pass (the approach that worked well to
close out the WI-creation PR, #454) rather than continuing the bot
retrigger loop indefinitely.

**Round 13** — retriggered against `28d7b66`. Copilot clean. 1 new Codex
finding, confirmed valid and actually significant (reopening the
"narrowing" read from round 12): "Limit the cleanliness check to
refreshed skill directories" (P2) — the round-10/11 working-tree checks
scanned the whole `src/lrh/skills` package root, which self-sabotages:
any checkout that has ever run this skill's own Python imports (Step 2's
`_skill_names()` call, Step 5's `install_named_skills` call) leaves
`src/lrh/skills/__pycache__/` behind as a normal, expected Python
byproduct — the check would then block *every* refresh on *any* normal
dev checkout, permanently. Confirmed live in this session's own checkout
(exactly this `__pycache__` was already present from earlier smoke
tests). This also symmetrically affected the tree-hash check: an
unrelated sibling skill's divergence would block refreshing skills that
were actually fine. Rescoped **both** checks (tree-hash and
working-tree) to each confirmed skill's own subdirectory
(`src/lrh/skills/<name>/`) rather than the package root — smoke tested
live: the per-name working-tree check for `lrh-closeout` correctly
came back clean (excluding the package-root `__pycache__`), while the
per-name tree-hash check still correctly detected this branch's own
real divergence for that specific skill. A name that fails its own
check is now excluded individually rather than blocking the whole batch.
Pushed as commit `5d789e8`.

13 rounds on this PR (24 total across this WI's full lifecycle,
including the WI-creation PR #454). This round's finding was genuinely
significant — not a narrowing signal after all. Doing one final
retrigger to confirm this fix lands without immediate regression; after
that, moving to a fresh-context self-review pass and a merge-readiness
decision regardless of further findings' severity, given the volume of
iteration already invested and the current design's now-substantial
verification depth (4 independent layers: repo scope, base branch,
repo identity, per-skill exact state).

**Round 14** — retriggered against `28d7b66`'s successor. 4 findings, all
confirmed valid: established the checkout-to-`main` step before other
Step 5 actions run (ordering — a prior action could otherwise commit
against the wrong branch), switched the `main` pull to `--ff-only`
(refuses to silently merge/rebase over local divergence), extended
verification to `installer.py` itself (not just the skill data it
copies — the code performing the copy had never been checked), and fixed
a stale claim about reusing `baseRefName` from an earlier step. Pushed
as commit `ed39153`.

**Stop.** At this point the user interrupted mid-retrigger-poll and
asked directly: what kind of issues are these, and is this diminishing
returns? Reviewing the actual pattern across all 14 rounds honestly:
roughly the first ~9 rounds found genuinely distinct, structural
correctness gaps; rounds 10–14 were increasingly narrow refinements of
the *same* underlying mechanism (working-tree cleanliness → ignored
files → per-skill scoping → the installer module's own state) plus
self-inflicted consistency debt (stale counts, stale checklist text)
from patching the design forward incrementally under review pressure
rather than designing it once, coherently. The user characterized 14
rounds of review as itself a code smell indicating a design problem, not
just a long tail of edge cases, and asked for a fresh-context,
independent **go/no-go** review of the whole design — not further
incremental fixes.

**Fresh-context self-review verdict: NO-GO.** A cold subagent (PR URL,
full diff, governing WI — no session context) was asked to evaluate the
architecture itself, not re-verify individual fixes. Verdict:
`install_named_skills()` in `installer.py` is sound — small, fully
tested, converged in one round. The `/lrh-closeout` "skill refresh" step
is the problem: every one of rounds 6–14 was another angle on the same
root issue — trying to prove a live, mutable working tree matches a
specific verified commit before trusting a live filesystem read
(`PYTHONPATH` + `importlib.resources`) — rather than reading directly
from git's object database (`git show`/`git archive`/a detached
worktree at a verified SHA), which would eliminate that entire class of
finding by construction. The self-review also found a **new, still-open
bug** the 14 rounds never caught: a TOCTOU gap between Step 2's plan
(computed against `origin/main` at assessment time) and Step 5's
execution (re-fetches `origin/main` again before installing) — if
`origin/main` moves in between, Step 5 could install content the user
never actually saw approved at the Step 4 gate. It recommended reverting
the `/lrh-closeout` changes and, if the underlying goal is pursued again,
a small dedicated CLI command (`lrh skills refresh-from-commit <sha>`)
reading from a SHA pinned once at the confirm gate, instead of agent-
followed prose re-establishing trust from scratch on every invocation.

**Decision: revert the `/lrh-closeout` SKILL.md changes; keep
`install_named_skills()`; do not pursue the CLI-command redesign** (the
user judged it overkill for this case). Both SKILL.md trees restored to
byte-identical with `origin/main` (verified: `git diff origin/main --
.claude/skills/lrh-closeout/SKILL.md src/lrh/skills/lrh-closeout/SKILL.md`
is empty). `WI-CLOSEOUT-SKILLS-INSTALL-SYNC`'s acceptance criteria are
not met by this PR; its resolution is a separate decision. PR #456's
title/body updated to describe the actual final, reduced scope.

**Post-revert round** — retriggered both reviewers against the reverted,
scope-reduced diff (commit `4e9263e`). Codex fully clean ("Didn't find
any major issues"). Copilot: 1 minor docstring wording nit, confirmed
valid — the docstring said names are validated "before any filesystem
mutation," but `install_named_skills` can still create `skills_dir` via
`mkdir` before the per-name loop; only the *destructive* per-name copy is
actually gated by validation. Tightened the wording to say so precisely.
Pushed as commit `fe469b3`. With the design now reduced to just the
tested `installer.py` capability, review converged in a single round —
consistent with the self-review's read that this part was sound all
along.

# Follow-up

- `WI-CLOSEOUT-SKILLS-INSTALL-SYNC` needs a human decision: resolve with
  a scope note, leave `proposed`, or amend — out of scope for this
  record.
- If the underlying stale-global-skill problem is revisited, see the
  self-review's suggested CLI-command design (recorded here and in PR
  #456's body) rather than restarting from the reverted approach.
- Retrospective note for future sessions running long bot-retrigger
  loops: the signal that should have prompted a strategy check earlier
  was rounds 10–13 narrowing into refinements of one mechanism plus
  recurring self-inflicted consistency slips — that pattern, not just
  elapsed round count, is what a fresh-context go/no-go review is for.
