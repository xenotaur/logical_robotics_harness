---
execution_id: 2026_08_18_07_52_13_RESCUE_CLAUDE_SESSIONS_SELFREVIEW
prompt_id: PROMPT(AD_HOC:RESCUE_CLAUDE_SESSIONS_SELFREVIEW)[2026-08-18T07:35:08+00:00]
work_item: AD_HOC
status: in_progress
rerun_of: 
pr: https://github.com/xenotaur/logical_robotics_harness/pull/561
commit: 
created_at: 2026-08-18T07:52:13+00:00
agent: claude-code
instruction_source: https://github.com/xenotaur/logical_robotics_harness/pull/561
session_transcript: pending
---

# Summary

PR-mode substitute review signal for PR #561 at `HEAD` `6d7e0bb0`, dispatched
from `/lrh-confirm-fixes` Step 8 after no automatic reviewer response appeared
for that commit. Both hosted bot reviews target `a134995e`, the first push;
nine commits postdate it, and the current `HEAD` carries live code changes no
hosted reviewer has seen.

This was a **substitute review signal**, not a follow-up signal for a
non-thread finding.

`rerun_of` is empty: the reference states PR-mode "always has a primary record
to link to" because it fires after `/lrh-implement` Step 9 creates one, but PR
#561 was opened by hand rather than through `/lrh-implement`, so no primary
record exists. The `pr:`-field fallback returns nothing for #561 as well. Only
`_REVIEW`, `_CONFIRM`, and this `_SELFREVIEW` side record exist for the branch.

# Result

Cold `general-purpose` subagent, no session memory, given only the PR URL,
`HEAD` SHA, repo path, and the environment-activation note. It exercised all
four tools against throwaway fixtures under `CLAUDE_CONFIG_DIR`, never
`--apply` against the real `~/.claude`.

**Verdict returned: safe to merge as-is.** Five findings, none capable of data
loss.

## Findings (5)

1. **Dry-run exit code masks refusals** (`archive_split_transcripts.py:168-174`).
   When at least one candidate is stageable *and* others are refused, dry-run
   returns 0 while `--apply` on identical state returns 1. A runbook gating
   `dry-run && --apply` would read the state as clean.
2. **`memory_count()` and the copy path disagree on what a corpus is**
   (`bucketlib.py:72-81` vs `migrate_memory.py:36`, `:62`). The gate at
   `migrate_memory.py:169` and `memory_orphaned` at `audit_buckets.py:41` both
   key on a non-recursive, `.md`-only count, while the copy path uses
   `rglob("*")` over all files. A corpus of nested or non-`.md` files is
   reported as no corpus and silently skipped.
3. **`choose_keeper` prefers length over canonicality, undocumented**
   (`archive_split_transcripts.py:49-65`). The docstring's "ties go to the
   canonical bucket" is literally true but there is no canonical preference
   when sizes differ; a partially-written canonical copy can be archived in
   favour of a longer stale one.
4. **PR body contradicts committed `plan.md`.** The body's table says 5
   duplicated sessions; `plan.md:38` says "4 (2 divergent, 2 identical)".
5. **Two doc nits.** `README.md:153` calls the mutators "safe to re-run", but
   re-running `migrate_memory.py --apply` after a successful apply refuses and
   exits 1 — safe, not idempotent. Tool tables at `README.md:149` / `plan.md:70`
   still say snapshot writes "to `/private/tmp`" although the code now falls
   back to `$TMPDIR`.

## Independent re-verification (Step 4, mandatory)

The subagent nominated finding 2 as the most severe. Re-verified directly by
this session, not re-delegated:

- All four citations read and confirmed accurate: `bucketlib.py:72-81` uses
  `self.memory_dir.glob("*.md")`; `migrate_memory.py:36` and `:62` use
  `rglob("*")`; the gate at `:169` is `old.memory_count() <= 0`;
  `audit_buckets.py:41` computes `memory_orphaned` from the same count.
- Reproduced on a fixture whose corpus held `memory/sub/deep.md` and
  `memory/notes.txt` — two real files. Output: `0 corpus/corpora considered,
  0 failure(s)`, `EXIT=0`. Silently skipped, exactly as reported.
- The stated mitigation also holds: scanned all real corpora — 16 scanned,
  **0** containing non-`.md` or nested files. Not reachable in current state.

Finding 1 was additionally re-verified: same fixture, dry-run `EXIT=0` and
`--apply` `EXIT=1`, with `archive_split_transcripts.py:171-174` returning 0
unconditionally in the dry-run branch. Finding 4 confirmed by reading
`plan.md:38` against the live PR body.

No fabricated citation was found in this report; every claim checked held up.

# Validation

No files were edited by this pass — PR-mode is report-only and does not push
(Decision 4 / Step 5). `lrh validate` unchanged at 0 errors, 0 warnings.

# Follow-up

- Findings route back to `/lrh-confirm-fixes` Step 3's taxonomy for
  classification and its Step 4 confirm gate; this record does not action them.
- This pass counts as one substitute review round against
  `/lrh-confirm-fixes` Step 8's provisional no-progress cap. It surfaced
  genuine new findings, so the no-progress counter resets to zero.
- `session_transcript: pending` — update when a durable pointer exists.
