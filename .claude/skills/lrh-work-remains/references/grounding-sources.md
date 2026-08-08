# Grounding Sources

For each checklist category, run the listed command(s) and report only what
the tool output actually shows — never substitute conversational recall for
a command that could answer the question. If a command isn't applicable
(e.g. `gh` unavailable, not a git repo), say so explicitly rather than
skipping the category silently.

1. **Incomplete work** — no single command; review this session's own
   transcript against what was actually completed vs. stated as a plan.
2. **Unanswered questions** — review this session's transcript for questions
   posed (by either party) that were never resolved.
3. **Uncommitted files** — `git status --short`
4. **Feature branches not pushed to main** — `git status -sb` (current
   branch ahead/behind), `git log --branches --not --remotes --oneline`
   (commits on local branches not on any remote)
5. **Open PRs not yet merged** — `gh pr list --author @me --state open`;
   for the current branch specifically, `gh pr view --json state,url`
6. **Unaddressed comments on PRs** — `lrh request review_response <pr-url>`
   for comment data; `lrh github threads <pr-url> --mode raw --state all`
   filtered to `isResolved == false` for the authoritative live count
7. **Incomplete closeouts of PRs** — `grep -rl '^status: in_progress'
   project/executions/ --include='*.md'`, then cross-check each record's
   `pr:` field against `gh pr view <pr-url> --json state,mergeCommit` —
   a `MERGED` PR with an `in_progress` record is an incomplete closeout
8. **Stray files** — `git status --short` (untracked files outside expected
   output paths), and check the session's own scratchpad directory for
   leftover files that should have been cleaned up or delivered
9. **Stale branches** — `git branch -a --sort=-committerdate`, cross-checked
   against `gh pr list --state all` to find branches whose PR already merged
   or closed but the branch wasn't deleted
10. **Unsaved memories** — manual eyeball of this session's actual decisions
    and corrected assumptions against `MEMORY.md`
    (`~/.claude/projects/<project-slug>/memory/MEMORY.md`, outside this
    repo) — not an automated keyword search; see the parent SKILL.md's
    Step 4 for what counts as memory-worthy
11. **Untaken offers** — review this session's transcript for offers made
    ("want me to also...", "should I...") that were never confirmed or
    declined
12. **Unaddressed issues** — `gh issue list --assignee @me --state open` if
    the repo uses GitHub issues; otherwise note that no issue tracker is in
    use for this check
13. **Control plane updates** — `lrh validate` (report errors and warnings
    verbatim, don't summarize away a warning)
14. **Open work items** — `lrh snapshot current_focus --stdout` if `lrh` is
    on PATH; otherwise `grep -l '^status: proposed' project/work_items/proposed/*.md`
    and `grep -l '^status: active' project/work_items/active/*.md`, scoped to
    items touched or created this session
15. **Unfinished workstreams** — `lrh snapshot current_focus --stdout` if
    available; otherwise read `project/workstreams/active/*.md` frontmatter
    (`work_items:`, `exit_criteria:`) directly and cross-check each listed
    WI's status
16. **Documentation updates** — check whether files this session touched
    have corresponding doc references (e.g. `CLAUDE.md`, a skill's own
    index entry, a README) that still need updating to reflect the change
17. **Dogfooding of user-facing features** — if this session built or
    changed a user-facing feature (a skill, a CLI command, a UI), check
    whether it was actually invoked/exercised this session or only written
18. **Other unfinished scope of work** — catch-all; anything raised in
    conversation that doesn't fit categories 1–17 but is still open

## Cross-session ownership

Before reporting a branch, PR, or WI as outstanding, check whether it looks
owned by a different session (e.g. a branch/PR never touched in this
session's own transcript). Do not auto-classify — surface it and ask the
user to confirm whether it's theirs from this session or something another
session already owns, so it isn't duplicated or reported as this session's
own unfinished work.
