---
execution_id: 2026_07_18_18_36_36_VERIFY_CONFIRM_FIXES_REQUIRED_CHECKS_GAP
prompt_id: PROMPT(AD_HOC:VERIFY_CONFIRM_FIXES_REQUIRED_CHECKS_GAP)[2026-07-18T18:36:27-04:00]
work_item: AD_HOC
status: landed
rerun_of: 2026_07_18_03_15_20_CONFIRM_FIXES_REQUIRED_CHECKS_FALLBACK
pr: https://github.com/xenotaur/logical_robotics_harness/pull/401
commit: 5d2f29c9ab9ae153a1effc9f784f42381366ff10
created_at: 2026-07-18T18:36:36-04:00
agent: claude_app
instruction_source: ad-hoc task — close the "count is > 0" verification gap flagged as follow-up in PR #400
session_transcript: claude-app:49a80683-68ef-40ff-a81c-28253a11ca8e
---

# Summary

Close the verification gap flagged as follow-up in PR #400: the
`--required` distinguishing check's `count is > 0` branch had only been
verified by code-reading and the linked upstream issue, not against a real
repo where a `required_status_checks` rule actually exists.

`rerun_of` links back to PR #400's primary execution record manually — this
work is on a new branch/slug (not a `-review`/`-confirm` continuation of
that branch), so the standard `rerun_of` search convention does not find it
automatically.

# Result

Surveyed ~15 public repos (`microsoft/vscode`, `facebook/react`,
`kubernetes/kubernetes`, `rust-lang/rust`, `python/cpython`, `cli/cli`,
`pallets/flask`, `psf/requests`, `actions/checkout`, `tiangolo/fastapi`,
`denoland/deno`, `oven-sh/bun`, `vitejs/vite`, `withastro/astro`) via
`gh api repos/<repo>/rules/branches/<default-branch>` — all returned `200`
with real ruleset data (confirming the API itself works correctly and isn't
permission-gated for outside readers) but none had a `required_status_checks`
rule; most gate merges via required reviews or other rule types instead.

Found a real example: **`vercel/next.js`** (default branch `canary`) has an
active `required_status_checks` rule with 3 named contexts (`thank you,
next`, `thank you, build`, `Potentially publish release`). Verified both
halves of the fix's logic against it:

1. The distinguishing-check query itself
   (`gh api repos/vercel/next.js/rules/branches/canary`, filtered to
   `required_status_checks`) returns the real non-empty rule — confirms the
   query correctly detects a `count > 0` case in the wild, not just in
   theory.
2. `gh pr checks --required` against a live open PR there (#95928) succeeded
   and returned the correctly filtered checks rather than erroring —
   confirms `--required` behaves normally once required checks exist and
   have posted status, i.e. the "no required checks reported" error this
   fallback handles really is specific to the empty/not-yet-posted timing
   case (per `cli/cli#8855`), not a general property of `--required` on
   protected repos.

Updated `references/confirm-fixes-workflow.md`'s "`--required` error: two
different causes, one message" section with this evidence. No logic
changed — the distinguishing check documented in PR #400 was already
correct; this closes the previously-honest "not yet exercised" caveat with
real evidence. Mirrored to `.claude/skills/`.

# Validation

```
lrh validate  — 0 errors, 0 warnings
diff -r src/lrh/skills/lrh-confirm-fixes/ .claude/skills/lrh-confirm-fixes/  — identical
gh api repos/vercel/next.js/rules/branches/canary --jq '[.[] | select(.type=="required_status_checks")]'
  → non-empty, 3 named contexts (thank you, next / thank you, build / Potentially publish release)
gh pr checks 95928 --repo vercel/next.js --required --json name,state,bucket
  → exit 0, 5 checks returned (2 pass, 3 skipping), no error
```

No Python was touched (docs only), so `scripts/format`/`lint`/`test` were
not run.

# Follow-up

- Update `session_transcript: pending` to `claude-app:<session-id>` after
  the session ends.
- After this PR merges: land this execution record (`status: landed`,
  `pr:`/`commit:`) — no work item to resolve (ad-hoc, matching PR #400's
  own precedent).
