# Doc-Work Scope Reference

Guidance for identifying which documentation is affected by recently completed
work and how to scope the updates. Read before Steps 4–6 of `/lrh-doc-work`.

---

## Identifying Affected Docs from a Work Reference

### From a merged PR

1. **Read the PR diff** — identify all non-doc files that changed (source
   code, config, CLI, schemas, migrations). For each change, ask: "Does
   any existing doc describe the old behavior or would a new doc help a user
   use the new behavior?"

2. **Read the PR body** — PRs often describe what was added and why. The
   "Summary" and "Test plan" sections usually name new features, changed
   commands, or updated config options that need documentation.

3. **Focus on user-visible changes:**
   - New CLI commands or flags → Reference doc; possibly How-to
   - New config options → Reference doc
   - Changed APIs or schemas → Reference doc; possibly Explanation
   - New concepts introduced → Explanation
   - New workflows enabled → How-to; possibly Tutorial

4. **Ignore internal changes** that are not user-visible: refactors,
   internal renaming, test additions, CI fixes. These do not require doc
   updates unless they change the public interface.

### From a resolved work item (WI-*)

1. **Read the Acceptance Criteria** — these define what was delivered. Each
   criterion typically maps to observable behavior that may need documentation.

2. **Read the Required Changes** — explicit file changes may include docs;
   if they don't, use the criteria to infer what docs are now stale or missing.

3. **Read the Summary and Scope sections** — these describe the problem and
   intended solution. The solution description often reveals new concepts
   (Explanation) or new tasks (How-to / Tutorial).

4. **Check the PR linked to the WI** (if any) and apply PR rules above.

### From a closed workstream (WS-*)

1. **Read the workstream summary** — describes the full scope of work that
   was delivered. Treat it like a high-level PR body.

2. **Read all resolved work items** under the workstream — apply WI rules to
   each, then consolidate. Look for cross-cutting themes that warrant a new
   Explanation or overview How-to that didn't make sense at the individual
   WI level.

3. **Check for a completion PR** if the workstream has one; apply PR rules.

### Auto-detect mode

When no argument is provided, inspect recent git history:

```bash
git log --oneline --merges -10
```

Identify the most recently merged branch or PR number. If ambiguous, report
the candidates and ask the user to confirm before proceeding.

---

## Scope Rules

### Update only — do not audit or reorganize

`/lrh-doc-work` updates docs to reflect completed work. It does not:

- Audit the full documentation structure (use `/lrh-doc-audit` for that)
- Reorganize existing docs into Diataxis quadrants (use `/lrh-doc-organize`)
- Rewrite docs that are unrelated to the completed work
- Reformat, lint, or clean up docs beyond what the update requires

**If you notice structural issues** while reading affected docs (a file in
the wrong place, a mixed-quadrant README), flag them in the PR description
as candidates for a future `/lrh-doc-audit` or `/lrh-doc-organize` run.
Do not fix them in this PR.

### One work reference per invocation

Each `/lrh-doc-work` invocation handles one work reference (one PR, one WI,
or one WS). If multiple work references need doc updates, run the skill
separately for each.

**Exception:** if a WI was the only work item in a WS and both are now
closed, use the WS as the reference (broader context) rather than the WI.

### Minimal, targeted updates

Apply the minimum change that makes the documentation accurate. Do not:

- Expand scope because adjacent content looks stale
- Rewrite sections that are still accurate
- Add "nice to have" content not implied by the work reference

If a full update would require knowledge beyond what the work reference
provides (e.g., a complete tutorial for a new feature), create a stub and
mark it clearly:

```markdown
> **Stub:** This document is a placeholder. Full content will be added after
> the feature is exercised in production. See PR #<N> for context.
```

### Stale doc handling

If the completed work makes an existing doc stale and a full update is out
of scope for this run, add a stale notice at the top rather than leaving it
silently wrong:

```markdown
> **Note:** This doc is under review. Some content may not reflect recent
> changes. See PR #<N> for context.
```

Do not delete docs that have become stale — mark them and leave removal for
a future `/lrh-doc-organize` phase.

---

## PR vs. Direct-Commit Guidance

Use a PR (the default) for all doc updates that:
- Create new files
- Substantially rewrite existing sections
- Affect multiple files
- Would benefit from review before publication

Use a direct commit to main (skip the PR) only for:
- Single-file updates of ≤ 5 lines (e.g., updating a version number in a
  reference table)
- Fixes to obvious factual errors (typos in a command name, wrong flag value)

If in doubt, use a PR.

---

## Mapping Changes to Doc Types

Use this table as a starting heuristic. Diataxis classification in Step 6
overrides these defaults.

| Change type | Likely doc action |
|---|---|
| New CLI command | Reference: add command to CLI reference |
| New CLI flag | Reference: add flag to relevant command entry |
| New config option | Reference: add to config reference |
| Changed API signature | Reference: update API docs |
| Changed schema | Reference: update schema docs |
| New workflow the user performs | How-to: add or update guide |
| New concept introduced | Explanation: add or update overview |
| Major behavioral change | How-to + Reference; possibly Explanation |
| Bug fix (behavior unchanged) | Usually no doc update needed |
| Internal refactor | Usually no doc update needed |

---

## What Counts as a Doc

`/lrh-doc-work` operates on:
- Files in `docs/` (all subdirectories)
- Top-level `README.md`, `CHANGELOG.md` (if they are user-facing)
- Files in `docs/` symlinked or cross-referenced from elsewhere

It does not update:
- `project/` control-plane files (those are not user docs)
- Source code comments (in-source docs belong to the code review, not this skill)
- `CONTRIBUTING.md`, `AGENTS.md`, `STYLE.md` (contributor meta, not user docs)
