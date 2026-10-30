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
   branch ahead/behind) for the truly-unpushed-anywhere case. **This alone
   misses a branch that's fully pushed to its remote but not yet merged
   into the default branch** — `git log --branches --not --remotes`
   excludes any commit reachable from a remote-tracking ref, so a pushed
   branch's commits are excluded from that diff even though they're not
   merged (see [git-scm.com/docs/gitrevisions](https://git-scm.com/docs/gitrevisions)
   on `--not`/`--remotes` semantics). **Do not hard-code `main`** — this
   skill may run in a client repo whose default branch is `master`,
   `develop`, or something else; resolve it first:
   `git symbolic-ref refs/remotes/origin/HEAD` (or
   `gh repo view --json defaultBranchRef --jq .defaultBranchRef.name` as a
   fallback), then use that value in `git branch --no-merged <default-branch>`
   to find local branches not merged into it, regardless of push state.
   For each such branch, **don't just check whether a remote copy
   exists, and don't hard-code the remote name `origin`** — a client
   repo's remote may be named differently, or a local branch may track a
   differently-named remote branch, in which case an `origin/<branch>`
   comparison fails or checks the wrong ref even when the branch is fully
   pushed, falsely reporting it as unpushed. Compare each branch against
   its own configured upstream instead:
   `git rev-parse <branch>` vs. `git rev-parse <branch>@{upstream}` (or
   `git rev-list --left-right --count <branch>@{upstream}...<branch>` for
   an ahead/behind count — see
   [git-scm.com/docs/gitrevisions](https://git-scm.com/docs/gitrevisions#Documentation/gitrevisions.txt-emltbranchnamegtupstreamegmasterupstreamu)
   on `@{upstream}` syntax). If a branch has no configured upstream at
   all, treat that as its own distinct case (never pushed) rather than
   folding it into either the pushed or unpushed bucket silently.
5. **Open PRs not yet merged** — `gh pr list --author @me --state open`;
   for the current branch specifically, `gh pr view --json state,url`
6. **Unaddressed comments on PRs** — `lrh request review_response <pr-url>`
   for comment data; `lrh github threads <pr-url> --mode raw --state all`
   filtered to `isResolved == false` for the authoritative live count
7. **Incomplete closeouts of PRs** — `grep -rl '^status: in_progress'
   project/executions/ --include='*.md'`, then cross-check each record's
   `pr:` field against `gh pr view <pr-url> --json state,mergeCommit` —
   a `MERGED` PR with an `in_progress` record is an incomplete closeout.
   **Read this against fresh remote state, not a stale local checkout or a
   prior session's own closeout report** — a record correctly landed by an
   earlier PR can be silently reverted back to `in_progress` by a later,
   unrelated merge (a real incident: PR #512 reverted 3 already-landed
   records from PR #506 with no conflict and no warning). **Use a
   read-only remote query, never `git pull`** — this skill never mutates
   git state, and `git pull` fetches *and* integrates changes into the
   current branch, modifying refs and the working tree (see
   [git-scm.com/docs/git-pull](https://git-scm.com/docs/git-pull)), which
   is exactly the kind of side effect to avoid, especially at session end
   with local work present. Read the file's actual content on the remote
   default branch directly instead:
   `gh api -H "Accept: application/vnd.github.raw" repos/<owner>/<repo>/contents/<path>?ref=<default-branch>`
   (resolve `<default-branch>` the same way category 4 does) — **the
   Contents API returns JSON with the file body base64-encoded in
   `.content` by default** (confirmed: a plain call returns
   `"encoding": "base64"` and an unreadable `.content` blob); the raw
   media-type header above returns the plain-text body directly instead —
   without it, the frontmatter `status:` value isn't actually readable
   from the response, defeating the point of this check. This is pure
   network read either way, no local git state touched — before trusting
   a record's `status:` field, rather than assuming a status reported
   earlier in this same session, or in a prior closeout, still holds.
8. **Stray files** — `git status --short` (untracked files outside expected
   output paths), and check the session's own scratchpad directory for
   leftover files that should have been cleaned up or delivered
9. **Stale branches** — `git branch -a --sort=-committerdate`, cross-checked
   against `gh pr list --state all --limit 1000 --json headRefName,state`
   — **`gh pr list` defaults to `--limit 30`**
   ([manual](https://cli.github.com/manual/gh_pr_list)); in a repo with
   more than 30 historical PRs (this repo has far more), the default
   silently misses older merged/closed PRs, making their branches look
   like they have no associated PR and falsely reporting them as stale —
   exactly the noise this category is trying to avoid, recreated by a
   different path. Always pass an explicit high `--limit` (or paginate)
   here. **Check
   `gh api repos/<owner>/<repo> --jq .delete_branch_on_merge` first** — if
   `false` (common; this repo has 200+ accumulated branches this way), a
   branch whose PR already merged or closed is the *expected*, low-value
   case, not a signal — do not flag it. The real signal is a branch with
   **no** merged or closed PR associated with it at all (never had one, or
   its PR is still open but the branch has had no commits in a long
   while) — that is what "stale" means here. Flagging every
   merged-but-undeleted branch buries the one abandoned in-progress branch
   under expected repo-wide noise.
10. **Unsaved memories** — manual eyeball of this session's actual decisions
    and corrected assumptions against `MEMORY.md`
    (`~/.claude/projects/<project-slug>/memory/MEMORY.md`, outside this
    repo) — not an automated keyword search. Apply the standing bar for
    what's memory-worthy: surprising, non-obvious, durable, and not
    already captured by an existing memory or derivable by reading the
    current project state. **State the exact directory
    path checked** (the `<project-slug>` actually used), not just "memory
    was checked" — a forked or relocated session can end up writing to a
    *different* project-slug directory than its predecessor without
    either session noticing, silently splitting one session's memories
    across two namespaces.
11. **Untaken offers** — review this session's transcript for offers made
    ("want me to also...", "should I...") that were never confirmed or
    declined. **Also cross-check any skill invoked this session against
    its own mandatory-offer steps** — e.g. `/lrh-closeout` Step 8 requires
    offering `/export`; if that skill ran this session, confirm the offer
    was actually made, not just that *some* offer was made somewhere. A
    freeform transcript scan alone can miss a specific offer another
    skill's own checklist requires.
12. **Unaddressed issues** — `gh issue list --assignee @me --state open` if
    the repo uses GitHub issues; otherwise note that no issue tracker is in
    use for this check
13. **Control plane updates** — `lrh validate` (report errors and warnings
    verbatim, don't summarize away a warning)
14. **Open work items** — **always inspect session-touched work-item files
    directly**: `grep -l '^status: proposed' project/work_items/proposed/*.md`
    and `grep -l '^status: active' project/work_items/active/*.md`, scoped to
    items touched or created this session. Do not rely on
    `lrh snapshot current_focus --stdout` for this, even when `lrh` is
    installed — its `Relevant Work Items` section
    (`relevant_work_items()` in `src/lrh/assist/snapshot_cli.py:607-631`)
    filters to work items whose `related_focus` list contains the current
    focus id, and only falls back to "include all" if *zero* work items
    repo-wide match that focus id. A session-touched WI with an unrelated
    or empty `related_focus` (a real case: the WI implementing this very
    skill has `related_focus: []`) can be silently excluded from that
    output while other, unrelated WIs still satisfy the fallback
    condition — `lrh snapshot` is a useful cross-check, not a substitute
    for reading the files directly.
15. **Unfinished workstreams** — **always** read
    `project/workstreams/active/*.md` frontmatter (`work_items:`,
    `exit_criteria:`) directly and cross-check each listed WI's status. Do
    not rely on `lrh snapshot current_focus --stdout` for this even when
    `lrh` is installed — its `current_focus` scope
    (`generate_current_focus_context()` in
    `src/lrh/assist/snapshot_cli.py:746-810`) has no `## Workstreams`
    section at all (that section only exists in the separate `work_item`
    scope, `generate_work_item_context()`, a different command). Calling
    `lrh snapshot current_focus --stdout` for workstream data will always
    return nothing on this point, regardless of whether `lrh` is
    installed or what state the workstreams are actually in — it is not a
    fallback-only limitation.
16. **Documentation updates** — check whether files this session touched
    have corresponding doc references (e.g. `CLAUDE.md`, a skill's own
    index entry, a README) that still need updating to reflect the change
17. **Dogfooding of user-facing features** — if this session built or
    changed a user-facing feature (a skill, a CLI command, a UI), check
    whether it was actually invoked/exercised this session or only written.
    **Also check the inverse case:** did this session discover mid-session
    that a relevant skill *already existed*, then manually re-derive its
    documented pattern by hand (e.g. raw tool calls replicating what a
    skill would have done) instead of actually invoking that skill? Look
    for a documented skill's pattern appearing in the transcript without a
    corresponding invocation of it.
18. **Other unfinished scope of work** — catch-all; anything raised in
    conversation that doesn't fit categories 1–17 but is still open

## Cross-session ownership

Before reporting a branch, PR, or WI as outstanding, check whether it looks
owned by a different session (e.g. a branch/PR never touched in this
session's own transcript). Do not auto-classify — surface it and ask the
user to confirm whether it's theirs from this session or something another
session already owns, so it isn't duplicated or reported as this session's
own unfinished work.

**No single signal is reliable alone — cross-reference multiple sources
before concluding an item is (or isn't) already claimed:**

- The candidate WI's own `assigned_agents:`/`blocked:` frontmatter fields
- `gh pr list --state open`, checked by **actual file list**
  (`gh pr view <n> --json files`), not just by title — two open PRs with
  generic-sounding titles can still turn out to overlap or not overlap
  only once their touched files are compared
- `git worktree list` across all active local worktrees, to see if another
  worktree already has the candidate's branch checked out
- Remote branch names via `gh api repos/<owner>/<repo>/branches`, in case
  a branch exists remotely that no local worktree has fetched yet
- `project/focus/current_focus.md` and `project/focus/development_agenda.md`
  for a stated current owner or priority

Report which of these were actually checked, not just the conclusion —
the same way this section's own citation trail was verified before being
folded into this skill's design.
