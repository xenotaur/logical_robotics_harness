---
execution_id: 2026_08_18_05_05_33_RESCUE_CLAUDE_SESSIONS_CONFIRM
prompt_id: PROMPT(AD_HOC:RESCUE_CLAUDE_SESSIONS_CONFIRM)[2026-08-18T02:25:44+00:00]
work_item: AD_HOC
status: in_progress
rerun_of: 
pr: https://github.com/xenotaur/logical_robotics_harness/pull/561
commit: 
created_at: 2026-08-18T05:05:33+00:00
agent: claude-code
instruction_source: https://github.com/xenotaur/logical_robotics_harness/pull/561
session_transcript: pending
---

# Summary

Pre-merge verification of PR #561 against `HEAD` `05902ea5`. Five unresolved
review threads verified and resolved; three previously-unreported defects
surfaced by the verification pass, two fixed here and one recorded as a known
limitation.

`rerun_of` is empty by the provenance check: no primary record with slug
`RESCUE_CLAUDE_SESSIONS` exists, and the `pr:`-field fallback also returns
nothing for PR #561. Only a `_REVIEW` side record exists for this branch. The
PR was opened by hand rather than through `/lrh-implement`, so there is no
primary implementation record to link.

# Result

## Verification was delegated to a cold subagent

`/lrh-review-response` authored all five fixes earlier in this same session, so
an inline pass would have been self-attestation — the property this skill
exists to avoid. Step 3's `--subagent` offer fired and was accepted. The
subagent received only the PR URL, the diff, and the five comment bodies: no
session memory, no access to the reasoning behind the fixes.

It did not verify by reading. For each comment it reproduced the original
defect against the parent commit `a556e5ae^` using throwaway fixtures under a
fake `CLAUDE_CONFIG_DIR`, then re-ran the same fixture against `HEAD`.

## Threads resolved (5 of 5, all Clear-satisfied, all bot-authored)

- **`PRRT_…7XJh`** (chatgpt-codex-connector, P1) — divergent memory-file
  collisions. Pre-fix fixture reproduced the exact reported failure: `a.md`
  migrated, destination index left in place, exit 0. On `HEAD` the run refuses,
  exits 1, and the destination is byte-unchanged. The refusal at
  `migrate_memory.py:83-95` precedes every write (`:97`, `:101-105`), so no
  partial migration is reachable.
- **`PRRT_…7XJj`** (chatgpt-codex-connector, P2) — alias root bucket skipped.
  Pre-fix fixture reproduced "0 corpus/corpora considered, EXIT=0" verbatim;
  post-fix both `audit_buckets.py` and `migrate_memory.py` find the bucket. The
  adversarial sibling `-fake-old-repoExtra` is still correctly rejected, so the
  fix did not over-correct.
- **`PRRT_…7XdV`** (copilot-pull-request-reviewer) — `choose_keeper` unbounded
  `startswith`. Unit-tested both versions against tied equal-size copies:
  pre-fix elected `-fake-new-repoX` (a bare-prefix match) as canonical and would
  have archived the real copy; post-fix refuses. Two further cases that
  previously false-tied into a refusal now resolve correctly.
- **`PRRT_…7Xdr`** (copilot-pull-request-reviewer) — snapshot `/private/tmp`.
  Fallback branch exercised across four `TMPDIR` states.
- **`PRRT_…7Xd8`** (copilot-pull-request-reviewer) — `DEFAULT_ARCHIVE`
  `/private/tmp`. Same, with one deviation, recorded as finding 1 below.

Both judgment calls flagged for scrutiny held up. The P1 comment explicitly
offered "either reconcile or refuse", so refusal-without-override is one of the
two remedies asked for. Copilot's own text said "or detecting `/private/tmp`
when present", so the adapted fix is the literal ask rather than a departure
from it.

## New findings from the verification pass

1. **Fixed.** `archive_split_transcripts.py` used
   `os.environ.get("TMPDIR", "/tmp")`, which substitutes only when the variable
   is *absent*. With `TMPDIR` set-but-empty on a non-macOS host the result was
   the **relative** path `claude-rescue-archive`, so `--apply` would have staged
   private transcripts under the caller's working directory — which the README
   instructs to be the LRH checkout, contradicting `experimental/README.md:13`
   ("Keep raw private transcript captures out of Git"). The sibling
   `snapshot_state.sh` used correct `${TMPDIR:-/tmp}` semantics, so the two
   tools disagreed on the same condition. Now `os.environ.get("TMPDIR") or
   "/tmp"`; verified across four `TMPDIR` states, all absolute.
2. **Fixed.** `snapshot_state.sh` `--help` hardcoded the pre-fix default,
   printing `/private/tmp/...` unconditionally — wrong on exactly the
   non-macOS hosts the reviewed comment was about. Now describes both branches.
3. **Recorded, not fixed.** `migrate_memory.py --allow-merge` has an unwarned
   mirror of the collision case it does refuse: copying a source `MEMORY.md`
   into a destination holding memory files but no index leaves those files
   unreferenced, and the run reports success. Narrow (needs `--allow-merge`
   plus an index-less destination) and outside the reviewed comment's scope,
   which covered same-path collisions only. Logged under `plan.md`'s Open
   Questions with a suggested mitigation.

None of the three re-opens a reviewed comment.

# Validation

Run inside the `LRH` conda environment:

    scripts/format --check --diff  — exit 0
    scripts/lint                   — exit 0
    lrh validate                   — 0 errors, 0 warnings

Thread state re-queried after resolution via
`lrh github threads --mode raw --state all`, filtered client-side to
`isResolved == false`: **5 total, 0 unresolved**. Step 6 thread-resolution
verdict: **green**.

Note the two thread listings legitimately disagreed at Step 2:
`lrh request review_response` reported one thread, the authoritative
`isResolved`-only list reported five. Four were `isOutdated: true` — open
concerns whose commented-on lines had moved — which the narrower filter drops.
Verifying against the narrower list alone would have silently skipped four of
the five comments, including the P1.

# Follow-up

- `session_transcript: pending` — update to the durable session pointer once
  available.
- Finding 3 remains open as a known limitation in `plan.md`.
- CI and REVIEW-LANDED are re-checked against the post-push `HEAD` in Step 8;
  this record's own commit moves `HEAD`, so its verdict does not describe the
  commit a merge would land.
