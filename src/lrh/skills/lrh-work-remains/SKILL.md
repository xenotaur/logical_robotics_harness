---
name: lrh-work-remains
description: >
  Summarize what this session accomplished and report what work remains,
  grounded in actual tracked repo state (git, gh pr, lrh snapshot
  current_focus) rather than conversational recall. Strictly read-only —
  reports only, never writes files, runs lrh prompt commands, or mutates
  git state. Reports against a fixed 18-item checklist (uncommitted files,
  unpushed branches, open PRs, unaddressed review comments, incomplete
  closeouts, stray/stale files or branches, unsaved memories, untaken
  offers, open work items, unfinished workstreams, doc updates,
  dogfooding, and more) and flags candidates that may belong to a
  different session instead of auto-classifying them. Use at the end of a
  session, or any time you want a grounded picture of what's left.
when_to_use: >
  Use when the user wants a grounded picture of what work remains in the
  current session — at session end, or any time an explicit "what's left"
  check is wanted. Do not invoke merely because a session has touched many
  files; wait for the user to actually ask. Report-only — never writes
  files, runs `lrh prompt` commands, or mutates git state, so there is
  nothing for a confirm-before-write gate to protect.
---

# lrh-work-remains Skill

This skill answers "what work remains?" for the current session. It is
strictly read-only: it never creates, edits, or moves any file, never runs
`lrh prompt` or `git` mutation commands, and ends at a report — there is no
offer-and-write step, unlike this skill's action-oriented siblings
(`/lrh-closeout`, `/lrh-confirm-fixes`).

---

## Inputs

No argument required. Invoke as:

```
/lrh-work-remains
```

---

## Reference Knowledge

Load these before running any step:

1. **`references/remains-checklist.md`** — The fixed 18-item checklist this
   skill reports against, copied verbatim from its source. Do not
   paraphrase or reorder it.

2. **`references/grounding-sources.md`** — Which command(s) ground each
   checklist category, plus the cross-session-ownership rule (surface and
   ask, never auto-classify).

---

## Execution Steps

### Step 1 — Summarize session accomplishments

Review this session's actual transcript. In one paragraph, state what was
accomplished and what prompted it — grounded in what actually happened this
session, not a restatement of stated plans that weren't carried out.

### Step 2 — Ground each checklist category

For each of the 18 items in `references/remains-checklist.md`, in order, run
the command(s) `references/grounding-sources.md` lists for that category and
report only what the tool output actually shows. If a category has no
findings, report that explicitly ("Uncommitted files: none — `git status
--short` is clean") rather than omitting it — a skipped line is
indistinguishable from a checked-and-clean one.

Do not substitute conversational memory for a command that could answer the
question. If a command isn't applicable in this environment (e.g. `gh`
unavailable, `lrh` not on PATH, not a git repository), say so explicitly for
that category rather than skipping it silently — fall back to the next
available signal `references/grounding-sources.md` lists for that category
where one exists (e.g. direct `project/` reads when `lrh snapshot` isn't
available).

### Step 3 — Flag cross-session ownership candidates

For any branch, PR, or work item surfaced in Step 2 that this session's own
transcript never touched, do not report it as this session's own unfinished
work and do not silently exclude it either — surface it separately and ask
the user to confirm whether it belongs to this session or is already owned
by a different one, per `references/grounding-sources.md`'s cross-session
ownership rule.

### Step 4 — State the next step

If Step 2 surfaced any category with real outstanding work, state the single
most logical next step to address it. If everything is clean, say so
plainly — do not manufacture a next step where none exists.

### Step 5 — Report

Present the Step 1 summary, the full per-category results from Step 2 (all
18 items, including explicit "nothing outstanding" lines), the Step 3
ownership flags (if any), and the Step 4 next step. This is the end of the
skill's job — do not offer to act on any finding; if the user wants to act
on one, that is a separate, explicit invocation of whichever skill fits.

---

## Quality Checklist

Before reporting completion, verify:

- [ ] All 18 checklist categories from `references/remains-checklist.md`
      were reported on, in order, none silently omitted
- [ ] Each category's claim is grounded in an actual command's output, not
      conversational recall
- [ ] Categories with no findings were reported as "nothing outstanding"
      explicitly, not left out
- [ ] Any branch/PR/WI not touched by this session's own transcript was
      flagged as a possible cross-session item and asked about, not
      auto-classified either way
- [ ] No file was written, no `git`/`lrh prompt` mutation command was run
- [ ] A single next step was stated if outstanding work exists, or an
      explicit "nothing outstanding" if not

---

## What This Skill Does Not Do

- Does not write files, run `lrh prompt` commands, resolve review threads,
  or mutate git state in any way — report only.
- Does not automatically classify a branch/PR/WI as belonging to another
  session — surfaces the candidate and asks.
- Does not offer to act on any finding — that is a separate, explicit
  invocation of the relevant skill (`/lrh-review-response`,
  `/lrh-closeout`, `/lrh-work-item`, etc.).
- Does not modify `src/lrh/assist/snapshot_cli.py` — consumes
  `lrh snapshot current_focus --stdout` as-is.
- Does not implement the Taurcode-repo `:remains` prompt port-back — that
  lives in the separate Taurcode repo.
