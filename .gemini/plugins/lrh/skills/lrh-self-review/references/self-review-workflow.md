# `/lrh-self-review` Workflow Reference

The shared dispatch procedure, the two prompt shapes, and the
execution-record convention. Read this before Step 3 (dispatch) and Step 6
(execution record) of `SKILL.md`.

---

## Why one skill, two modes

Both modes share the identical core procedure: dispatch a fresh
`general-purpose` `Agent` subagent, cold context, instruct it to verify
claims against real files rather than trust prose, independently
re-verify its own top finding before accepting it, write an execution
record. Only the *target* differs — a local diff plus task/WI orientation
context (diff-mode), or a PR URL, `HEAD` SHA, and comment history
(PR-mode, the shape already used ad hoc in this project's own evidence
PRs). Splitting this into two skills would duplicate the procedure in two
files for no benefit — the same anti-duplication reasoning
`src/lrh/skills/_shared/lifecycle-chain.md` documents for chain-report
text applies here to review-dispatch procedure.

The subagent task is report-only and must not ask the subagent to invoke
`/lrh-self-review`, run other LRH skills, or spawn another review agent. This
skill's frontmatter carries `disallowed-tools: Skill` as the primary,
platform-enforced recursion guard (see `DEC-SELF-REVIEW-RECURSION-GUARD`),
empirically verified to remove the `Skill` tool from both the invoking
session and the dispatched subagent. Codex installations separately carry
`agents/openai.yaml` with `policy.allow_implicit_invocation: false` for this
skill. The narrow prompt and the required main-session re-verification remain
load-bearing regardless — the guard bounds recursion, not review quality.

---

## Dispatch prompt shapes

### Diff-mode prompt

Give the subagent, and nothing else:

```
You are doing an independent, cold-context review of an in-progress
change. You have NOT seen any prior conversation about this — verify
every claim against the actual current repository state; do not trust
this prompt's own prose without checking it.

Do not invoke /lrh-self-review, run other LRH skills, or spawn another
review agent. This pass is report-only.

This branch implements <WI-ID or task description>. Its stated
requirements: <Required Changes / Acceptance Criteria from the WI, or the
ad-hoc task description>.

Diff to review (git diff main):
<diff>

Review this diff against its stated requirements. Verify any factual
claims (citations, line numbers, described behavior) directly against the
actual files — don't take the diff's own comments or commit message at
face value. Report:
- Any real, verifiable issues, each with what's wrong and how you
  verified it.
- Whether the diff plausibly satisfies its stated requirements.
```

### PR-mode prompt

Give the subagent, and nothing else:

```
You are doing an independent, cold-context review of a real GitHub pull
request. You have NOT seen any prior conversation about this — verify
every claim against the actual current repository state; do not trust
this prompt's own prose without checking it.

Do not invoke /lrh-self-review, run other LRH skills, or spawn another
review agent. This pass is report-only.

PR: <pr-url>
Current HEAD SHA: <sha>

Read the full diff (`gh pr diff <pr-url>`) and the PR's title/body/comment
history. Verify any factual claims directly against the actual files —
don't take the diff's own comments, commit messages, or PR description at
face value. Report:
- Any real, verifiable issues, each with what's wrong and how you
  verified it.
- Whether you consider this PR safe to merge as-is.
```

Both shapes explicitly withhold this session's own prior findings and
conversation — that's what makes the pass genuinely independent, not a
same-context echo (the property `--subagent` mode already relies on in
`/lrh-confirm-fixes` Decision 7, generalized here to a dedicated skill).

---

## Independent re-verification (mandatory)

Before accepting the subagent's report, the *invoking session* — not a
second subagent — re-verifies its single most severe finding directly:
read the file(s) it cites, run the command(s) it claims to have run,
confirm the claim holds under direct inspection. This is not optional
diligence; it is a documented step because leaving it as an implicit habit
means it depends on which session happens to remember to do it. This
exact discipline caught a fabricated citation during this skill's own
design session — a subagent's claim that a specific line of a specific
file said something it did not, caught only because the citation was
independently re-read rather than trusted.

If re-verification finds the top finding does *not* hold up, report that
explicitly — do not silently drop it, and do not treat the rest of the
subagent's report as untrustworthy by association without checking those
too.

---

## Execution-record convention

**Bucket and suffix:** `AD_HOC`, `_SELFREVIEW.md` filename suffix —
parallel to `/lrh-review-response`'s `_REVIEW.md` and
`/lrh-confirm-fixes`'s `_CONFIRM.md`.

```bash
lrh prompt label --slug <slug>-selfreview
lrh prompt record-execution \
  --prompt-id "<id>" \
  --work-item AD_HOC \
  --slug <slug>-selfreview \
  --status in_progress \
  --project-root .
```

**`rerun_of` — differs by mode:**

- **PR-mode** always has a primary record to link to, since it only fires
  from inside `/lrh-confirm-fixes` Step 8, which runs after
  `/lrh-implement` Step 9 already created one. Find it the same way
  `/lrh-confirm-fixes` Step 7 does: convert the branch slug to
  upper-underscore, exclude `_REVIEW.md`/`_CONFIRM.md`/`_SELFREVIEW.md`
  suffixed files, search `project/executions/`.
- **Diff-mode** runs from `/lrh-implement` Step 7.5, which precedes Step
  8's `gh pr create` and Step 9's primary-record creation — there is no
  primary record yet at diff-mode dispatch time. Leave `rerun_of` empty;
  this is the designed sequencing, not a gap to work around (see this
  skill's own creation record,
  `project/executions/AD_HOC/2026_08_02_02_16_47_LRH_SELF_REVIEW.md`, for
  the identical pattern — an empty `rerun_of` because no primary existed
  yet when it was authored).

**CHAIN-NOTE fields (PR-mode substitutions, recorded at `/lrh-land`
closeout, not by this skill directly):** `self_review_rounds=<N>` counts
`_SELFREVIEW` PR-mode records used as substitute review signals in this run.
`bot_rounds=<N>` is optional and should only describe hosted review-bot
rounds that occurred outside `/lrh-confirm-fixes` Step 8's manual workflow,
such as automatic first-push review or a human-reported external reviewer
run. Stage 1 removed the in-skill manual retrigger counter; do not infer bot
rounds from the no-progress review cap.

**What's recorded, since no GitHub API exposes per-review credit cost**
(Decision 3): occurrence, not currency. Mode, findings (count and one-line
description each), whether diff-mode was report-only or `--apply` was used,
whether fixes were applied, whether findings were routed to
`/lrh-confirm-fixes` (PR-mode), and — PR-mode only — whether the pass was a
substitute review signal or a follow-up signal for a non-thread finding.

---

## Primary-record search collision — a known, separate risk

`_SELFREVIEW.md` was added to `/lrh-review-response`'s, `/lrh-confirm-fixes`'s,
and `/lrh-land`'s primary-record exclusion globs alongside `_REVIEW.md` and
`_CONFIRM.md` (see each skill's own primary-record search). That exclusion
is a bare filename-suffix match, not a check for the actual slug-suffix
convention those skills append — a *primary* record whose own topic slug
happens to end in "review," "confirm," or "selfreview" self-excludes from
the search. This is a pre-existing, documented risk
(`feedback_lrh_land_step1_primary_record_substring_exclusion` in agent
memory; also `src/lrh/skills/lrh-review-response/SKILL.md`'s own note on
why side-record filenames must end in the literal suffix these greps
match), not something this skill's own `_SELFREVIEW.md` addition
introduces or fixes. If a work item or PR about `/lrh-self-review` itself
is ever revisited, expect this collision to recur.
