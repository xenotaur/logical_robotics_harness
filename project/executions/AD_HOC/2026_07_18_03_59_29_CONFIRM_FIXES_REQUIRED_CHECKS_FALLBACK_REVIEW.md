---
execution_id: 2026_07_18_03_59_29_CONFIRM_FIXES_REQUIRED_CHECKS_FALLBACK_REVIEW
prompt_id: PROMPT(AD_HOC:CONFIRM_FIXES_REQUIRED_CHECKS_FALLBACK_REVIEW)[2026-07-18T03:25:23-04:00]
work_item: AD_HOC
status: landed
rerun_of: 2026_07_18_03_15_20_CONFIRM_FIXES_REQUIRED_CHECKS_FALLBACK
pr: https://github.com/xenotaur/logical_robotics_harness/pull/400
commit: a405f02bf79cecf159def4d1689294c0ece09bbf
created_at: 2026-07-18T03:59:29-04:00
agent: claude_app
instruction_source: https://github.com/xenotaur/logical_robotics_harness/pull/400
session_transcript: claude-app:e8331ce5-44b4-4ce4-bb6c-fa623700836f
---

# Summary

Addressed a P1 review comment from `chatgpt-codex-connector` on PR #400:
the original `--required`-empty fallback (added in the parent execution)
conflated "repo has no required-check branch protection" with "required
checks exist but haven't reported yet" — a real, documented `gh` CLI
limitation (upstream issue `cli/cli#8855`) most likely to trigger right
after Step 8's post-push CI re-check. Falling back unconditionally in that
window could report a false green built only from optional checks.

# Result

Triage: presence — confirmed present in the diff just pushed; validity —
confirmed against the installed `gh` v2.95.0 source
(`pkg/cmd/pr/checks/checks.go`: the "no required checks reported" error
fires whenever the required-filtered check list is empty, regardless of
cause) and the linked upstream issue; feasibility — a distinguishing check
exists and was verified live.

Added a branch-rules distinguishing check before deciding whether to fall
back: `gh api repos/<owner>/<repo>/rules/branches/<base-branch>`, filtered
to `type == "required_status_checks"`. This REST endpoint ("Get rules for a
branch") returns `200` with a plain array for both protected and
unprotected branches using ordinary read access — unlike the legacy
`branches/{branch}/protection` endpoint, which 404s when unprotected and
needs admin permissions when protected.

- Rule count `0` → confirmed no required-check protection → safe to fall
  back to the unfiltered `gh pr checks` aggregate (as before).
- Rule count `> 0` → required checks exist but `--required` reported none
  → treat CI as **pending**, do not fall back, do not report green.
- The rules API call itself failing → inconclusive → treat as **pending**,
  note that required-check status could not be verified.

Updated `src/lrh/skills/lrh-confirm-fixes/SKILL.md` (Step 2 and Step 8) and
`references/confirm-fixes-workflow.md` (renamed and rewrote the fallback
section as "`--required` error: two different causes, one message").
Mirrored to `.claude/skills/lrh-confirm-fixes/`.

# Validation

```
scripts/version tools  — lrh CLI present, Ruff 0.15.12, Black 26.3.1 (LRH conda env)
scripts/format --check --diff  — 179 files unchanged
scripts/lint  — All checks passed (ruff + black)
lrh validate  — 0 errors, 0 warnings
diff -r src/lrh/skills/lrh-confirm-fixes/ .claude/skills/lrh-confirm-fixes/  — no differences
Live verification against PR #400 (base branch main):
  gh api repos/xenotaur/logical_robotics_harness/rules/branches/main
    --jq '[.[] | select(.type=="required_status_checks")] | length'
  → 0 (confirms this repo's earlier "no required checks reported" result
    on PR #399/#389 was genuinely "no protection", not a timing race)
```

No Python was touched (skill docs only), so `scripts/test` was not run.

# Follow-up

- Update `session_transcript: pending` to the real session id after the
  session ends.
- After PR #400 merges, set `status: landed` and fill in `commit`.
- The distinguishing check has not yet been exercised against a repo that
  actually has `required_status_checks` branch protection configured (this
  repo has none) — the pending-vs-fallback branch is verified by code
  reading and the upstream issue, not by a live reproduction of the
  rule-count-`> 0` case. Worth confirming against a protected repo if one
  becomes available.
