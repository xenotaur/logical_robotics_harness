# Documentation Audit Requirements

Discovery checklist, artifact schema, and guardrails for `/lrh-doc-audit`.
Apply at Steps 3, 5, and 6.

<!-- Template counterpart: src/lrh/assist/templates/request/audit_docs.md -->

---

## Discovery Checklist

Walk the repository systematically. Do not assume fixed paths — discover
the actual layout. Check each of the following:

### Documentation directories

- `docs/` — primary documentation tree (most common)
- `doc/` — alternative spelling
- `documentation/` — alternative spelling
- `wiki/` — local wiki mirror if present
- `pages/` — GitHub Pages source if present

### Top-level files

- `README.md` — project overview; almost always present
- `CONTRIBUTING.md` — contributor guide
- `CHANGELOG.md` or `CHANGES.md` — release history
- `SECURITY.md` — vulnerability disclosure policy
- `CODE_OF_CONDUCT.md` — community standards
- `AGENTS.md` — AI agent instructions (LRH / Claude Code projects)
- `STYLE.md` — code style guide
- `PROMPTS.md` — prompt conventions

### Package-level READMEs

- `src/<package>/README.md`
- `src/<package>/<subpackage>/README.md`
- `<package>/README.md` (non-src layout)

### Example and tutorial content

- `examples/` — example scripts or projects
- `notebooks/` — Jupyter notebooks
- `tutorials/` — tutorial files
- `demos/` — demo content

### CLI documentation

If the project exposes a CLI, run `<cli> --help` and record the output
structure. Check whether each subcommand has a corresponding how-to or
reference doc.

### Inline documentation

- Docstrings in public modules: are they present? Do they cover the public
  API surface?
- Inline comments explaining non-obvious behavior (not classified as docs,
  but note absence of docstrings as a reference gap)

### Control plane (LRH projects)

- `project/` — LRH control-plane files. These are meta; do not classify as
  docs. Note whether the control-plane itself is documented anywhere.
- `project/design/proposals/` — proposals that may warrant explanation docs
- `.claude/skills/` — skill files; their `SKILL.md` files are a form of
  reference/how-to for Claude Code users

---

## Stale Link and Navigation Gap Check

### Stale internal links

For each markdown file, extract all `[text](path)` links where `path` does
not start with `http://` or `https://`. Verify each target exists relative
to the file's location. Report:

- File containing the broken link
- Broken link target
- Expected resolved path

### Navigation gaps

Check for missing cross-references:
- How-to guides that assume concepts not explained anywhere (missing Explanation)
- Tutorials that reference config options with no Reference doc
- Reference docs for features with no corresponding How-to

---

## Artifact Schema

The audit artifact must include all of the following sections in order.
Omitting "Proposed First PR Scope" is not permitted — it is consumed by
`/lrh-doc-organize`.

```markdown
# Documentation Audit — <repository-name> — YYYY-MM-DD

## Repository Overview

Brief description of the repository: its purpose, primary audience, and
scale of existing documentation (rough file count, directory structure).

## Documentation Inventory

Table or annotated list of all discovered documentation files:

| Path | Current Type | Diataxis Quadrant | Notes |
|---|---|---|---|
| README.md | Mixed | Tutorial + Reference | Quickstart + config table |
| docs/how-to/deploy.md | How-to | How-to | Clear; no issues |
| docs/concepts/auth.md | Explanation | Explanation | Good coverage |
| ... | | | |

## Diataxis Coverage

Assessment of each quadrant:

**Tutorial:** [present / thin / absent] — [details]
**How-to:** [present / thin / absent] — [details]
**Reference:** [present / thin / absent] — [details]
**Explanation:** [present / thin / absent] — [details]

## Stale Links and Navigation Gaps

List of broken internal links, with file and target.
List of navigation gaps (missing cross-references).
If none: "No stale links found. No navigation gaps identified."

## Gaps and Recommendations

Prioritized list of missing or underserved documentation. For each item:
- Recommended content (specific, not vague)
- Diataxis quadrant it would fill
- Rationale (evidence-backed: reference specific files or absence thereof)

## Proposed First PR Scope

A scoped list of changes appropriate for a single reviewable PR — consumed
directly by `/lrh-doc-organize`. Should be achievable in one PR without
reorganizing everything at once:

- [Move/rename/create]: specific file action with source and destination
- [Create stub]: new file with title and target quadrant
- [Update README]: specific section to add, move, or remove

Keep this section actionable and concrete. Scope it to changes that are
clearly improvements and carry low regression risk.

## Notes

Any constraints, caveats, or context that does not fit elsewhere:
- Paths intentionally excluded from the audit and why
- Uncertainty about classification decisions
- Content identified as planned (not yet implemented) vs. current reality
- Suggestions for future audit passes
```

---

## Guardrails

These rules apply throughout the audit. Violating them turns the audit into
a reorganization, which defeats the purpose of separating the two operations.

1. **Do not reorganize documentation.** The audit identifies what exists and
   what is missing. Moving, renaming, or deleting files happens in
   `/lrh-doc-organize`, not here.

2. **Do not create content.** The audit describes gaps; it does not fill them.
   The only file written by this skill is the audit artifact itself.

3. **Allow only trivial link fixes.** If a stale link is clearly a typo and
   the fix is unambiguous, it may be noted in the audit Notes section as a
   "safe inline fix" — but it still requires user confirmation and a separate
   commit, not bundled with the audit artifact.

4. **Base gaps on current reality, not templates.** Do not flag the absence
   of documentation that "should" exist based on convention if there is no
   evidence the project intends to ship that feature or follow that convention.

5. **Distinguish planned from implemented.** If the repository has work items,
   proposals, or in-progress branches for documentation, note them as "planned"
   rather than "gap" in the inventory and recommendations.

6. **Keep all findings evidence-backed.** Every gap, stale link, and
   recommendation must cite specific file paths or absence thereof. Vague
   observations ("the docs could be better") are not audit findings.
