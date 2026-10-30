# Documentation Organize Constraints

Rules that govern every `/lrh-doc-organize` run. Apply at Steps 4 and 7:
review scope against these rules before confirming with the user (Step 4),
and enforce them during implementation (Step 7).

<!-- Template counterpart: src/lrh/assist/templates/request/organize_docs.md -->

---

## Scope source rules

### Audit mode (preferred)

When a docs-audit artifact is provided, read its "Proposed first PR scope"
(phase 1) or the relevant entry in "Recommended phased PRs" (phase N).
Treat the listed file actions as the default scope.

**Do not expand scope beyond what the audit phase specifies.** If a
tempting improvement is not in the phase, note it and defer it.

### Discovery mode (fallback)

When no audit artifact is available, run a minimal discovery pass:
- Scope conservatively — no more than 5–8 concrete, low-risk actions
- Focus on obvious mis-placements and clearly broken links
- Do not infer a full reorganization plan from convention alone

Always flag discovery mode to the user at the confirm gate and recommend
running `/lrh-doc-audit` before implementing a broader reorganization.

---

## Path preservation

Moving or renaming a file can silently break any markdown link that points
to the old path. Before and after every move:

1. **Search for existing links** — grep the repository for any markdown
   link pointing to the old path (relative and absolute variants).
2. **Update links or create a stub** — either update every link to the new
   path, or create a redirect stub at the old path containing a forward
   reference:

   ```markdown
   <!-- This file has moved. See: <new-path> -->
   ```

3. **Prefer link updates** for internal files you are already touching.
   Use stubs only when the old path is referenced from external sources
   (other repos, published docs) that cannot be updated in this PR.

Never leave a dangling reference without either updating it or stubbing it.

---

## README update rules

Every directory that changes its file set must have an accurate `README.md`:

- **File added to a directory:** ensure the README mentions it or, if the
  README is a navigation index, add an entry.
- **File removed from a directory:** remove or update the stale reference.
- **Directory created:** create a minimal `README.md` describing the
  directory's purpose and contents.
- **Directory emptied or deleted:** update the parent directory's README.

Keep README updates minimal — update only what reflects the actual change.
Do not rewrite, re-style, or expand README prose beyond what the file change
requires.

---

## Diataxis boundary rules

The four quadrants must remain distinct. When moving a file into a
quadrant-named folder (e.g., `docs/how-to/`):

1. **Verify the content matches the quadrant** using `diataxis-criteria.md`.
   If it does not, do not force the move — note the mismatch in the PR
   description and flag it for a future pass.
2. **Keep tutorials, how-to guides, reference, and explanations separate.**
   A file that serves multiple quadrants should be split, not relocated
   to the "closest" quadrant.
3. **Diataxis is a reader-need model, not just a folder recipe.** A
   reorganization that creates the right folder structure but places content
   in the wrong folder is worse than the status quo.

---

## Project–docs boundary rule

The `project/` directory is the LRH control plane (work items, proposals,
execution records, workstreams). The `docs/` directory is the human-facing
documentation layer. These must remain separate:

- Do not move files from `docs/` into `project/` or vice versa.
- Do not reorganize `project/` files as part of a documentation organize run.
- Do not present `project/` control-plane artifacts as human-facing docs.

If a file currently lives in the wrong layer, flag it in the PR description
as a separate cleanup task — do not move it as part of this run.

---

## Planned vs. implemented rule

Do not create documentation for features that do not yet exist in the
codebase:

- If an audit scope item creates a stub for a planned feature, mark it
  explicitly: include "Coming soon" or a link to the relevant work item
  at the top of the stub.
- Do not fill stub content with speculative descriptions of how a feature
  will behave.
- If you are uncertain whether a feature is implemented, check the code
  before creating a reference or how-to doc for it.

---

## One-phase-per-PR rule

Each `/lrh-doc-organize` invocation implements exactly one phase. Resist
scope creep:

- If an improvement is clearly outside the confirmed phase, do not include it.
- If the user adds scope at the confirm gate (Step 5), re-evaluate whether
  it still fits in one reviewable PR.
- If the expanded scope no longer fits, recommend splitting into two
  invocations.

Small, focused PRs are easier to review, less likely to cause merge
conflicts with content edits, and easier to roll back if a move turns out
to be wrong.
