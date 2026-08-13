---
execution_id: 2026_08_07_19_02_48_WI_LRH_CHAIN_DEFAULTS_INCREMENT_1
prompt_id: PROMPT(AD_HOC:WI_LRH_CHAIN_DEFAULTS_INCREMENT_1)[2026-08-07T19:02:36+00:00]
work_item: WI-LRH-CHAIN-DEFAULTS-INCREMENT-1
status: landed
rerun_of: 
pr: https://github.com/xenotaur/logical_robotics_harness/pull/512
commit: b11841c98a1d0e4fa1f1a40f1c53566834b6be36
created_at: 2026-08-07T19:02:48+00:00
agent: claude_app
instruction_source: project/work_items/proposed/WI-LRH-CHAIN-DEFAULTS-INCREMENT-1.md
session_transcript: claude-app:23a15fdd-6d6c-4d84-a7be-960a54769157
---

# Summary

Implemented Increment 1 of `PROP-LRH-CHAIN-DEFAULTS`: the chain-defaults
profile schema, the propose-and-confirm flow at `/lrh-land`/`/lrh-execute`
Step 2, and `chain_init_confirmation` in both modes per all five of
`DEC-CHAIN-INIT-SKIP-CONSENT`'s numbered requirements. Per the user's new
standing self-review-only policy (never retrigger GitHub bots beyond the
unavoidable first-push trigger), this record's own review round used
`/lrh-self-review` diff-mode rather than waiting on or retriggering
Copilot/Codex.

# Result

Delivered exactly as `PROP-LRH-CHAIN-DEFAULTS`'s Implementation Plan and
this WI's Required Changes specify: pure markdown/YAML procedure, no new
Python code (this project's convention for durable gate-owned state,
matching `round-cap-gate.md`'s own bash+git precedent rather than
inventing a new CLI surface).

- `project/config/chain-defaults.yaml`: repo-level, git-tracked, the three
  steelmanned defaults pre-populated, `confirmed_commit: null` until a
  human live-confirms it in this repo.
- `src/lrh/skills/_shared/chain-defaults.md`: canonical propose-and-confirm
  flow doc (maintainer-only, per the installer's `_`-prefix exclusion),
  inlined at both consuming sites.
- `/lrh-land` Step 2 + `references/land-workflow.md`: full inlined copy.
- `/lrh-execute` Step 2: cross-references `/lrh-land`'s inlined copy
  (already a loaded Reference Knowledge item) rather than a third
  duplicate copy.
- `chain_init_confirmation: always_confirm | skip_if_opted_in` implements
  all five `DEC-CHAIN-INIT-SKIP-CONSENT` requirements: initiation act
  preserved (no code change needed — the slash-command invocation itself),
  two-step consent (`git config --local` distinct from profile storage),
  user-local-only storage (never the shared YAML), value-hash binding via
  `git hash-object` with dogfooded round-trip verification, and an
  unconditional special-conditions checklist.
- Decision 4's profile-update offer and Decision 5's staleness fallback
  both implemented with real mechanics.
- `.claude/` mirrors byte-identical (`diff -r` clean both directions).

**Self-review (diff-mode subagent, independently re-verified) found 4 real
issues before this push, all fixed:**

1. **Severe, independently re-verified:** the staleness-check snippet
   would crash (`fatal: bad revision 'null'`) if executed against the
   shipped `confirmed_commit: null` in isolation from the surrounding
   flow's branching logic. Reproduced myself
   (`git diff --quiet "null" HEAD -- ...` → `fatal: bad revision 'null'`,
   exit 128) before fixing. Added an explicit null-guard directly inside
   the Decision 5 section so it can't be misread or misrun standalone.
   Re-dogfooded post-fix: correctly prints the "no prior confirmation"
   message and exits 0.
2. The "Consuming sites" table falsely claimed `/lrh-execute` carries its
   own inlined copy of the flow; it doesn't — it cross-references
   `/lrh-land`'s copy. Corrected the table to describe the actual design.
3. An inaccurate `backlog.md` citation claimed a `lifecycle-chain.md`
   cross-reference in the "Validator drift-check" entry that doesn't
   exist (grepped `backlog.md` directly — zero hits). Corrected to cite
   the actual entry accurately without the false claim.
4. No new Python code exists in this change. Flagged explicitly rather
   than silently claiming the WI's Validation section's "new unit tests"
   requirement is satisfied — it's structurally inapplicable to a
   pure-markdown/bash implementation.

# Validation

- `lrh validate`: 0 errors, 1 pre-existing unrelated warning
  (`PLANNING_ACTIVE_WORKSTREAM_NO_ACTIONABLE_LEAF` on
  `WS-SESSION-ARCHIVE-SYNC`, from concurrent unrelated work, not this PR)
- `diff -r src/lrh/skills/lrh-land/ .claude/skills/lrh-land/`: no
  differences
- `diff -r src/lrh/skills/lrh-execute/ .claude/skills/lrh-execute/`: no
  differences
- Manual dogfood: `git hash-object` + `git config --local` round-trip
  for skip-consent grant/validate/revoke, verified match and mismatch
  cases both work correctly
- Manual dogfood: staleness-check null-guard, before and after the fix,
  confirmed the crash and confirmed the fix
- `test_new_python` (required_evidence): **not applicable** — no new
  Python code exists in this change; see Follow-up

# Follow-up

- Manual end-to-end dogfooding (an actual `/lrh-land` run using the new
  `always_confirm` pre-filled defaults, and one exercising the
  `skip_if_opted_in` opt-in flow end to end, per the WI's own Validation
  section) has not happened yet — this record covers implementation, not
  live dogfooding. The very next `/lrh-land` invocation on this PR itself
  will be the first real dogfood of the `always_confirm` path.
- Increment 2 (`confirm_fixes_batch` autopilot) remains unimplemented and
  explicitly out of scope here, per its own separate work item.
