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
not start with `http://` or `https://`. Apply these normalizations before
the filesystem existence check:

1. **Skip pure fragment links** — if the entire target is `#something` (an
   in-page anchor), skip it; there is no file to check.
2. **Strip fragment suffix** — if the target is `file.md#section`, check
   only `file.md`; ignore the `#section` part.
3. **Resolve relative to the containing file** — check the normalized path
   relative to the directory of the file being scanned.

Report any target that still fails after these normalizations:

- File containing the broken link
- Broken link target (as written)
- Expected resolved path (after normalization)

### Navigation gaps

Check for missing cross-references:
- How-to guides that assume concepts not explained anywhere (missing Explanation)
- Tutorials that reference config options with no Reference doc
- Reference docs for features with no corresponding How-to

---

## Artifact Schema (v1)

The audit artifact must conform to the v1 convention defined in
`docs/reference/docs-audit-artifact-convention.md`. That file is the
authoritative reference; this section summarizes the required elements.

### Required frontmatter

```yaml
---
id: AUDIT-DOCS-YYYY-MM-DD
audit_type: docs
schema_version: 1
status: proposed
repo_root: .
project_root: .
docs_root: docs
control_root: project
package_roots: []
framework: diataxis
recommended_next_prompt: organize_docs
recommended_phase: scaffold
---
```

Populate `repo_root`, `project_root`, `docs_root`, `control_root`, and
`package_roots` with the actual paths discovered in Step 3. These fields
make the artifact portable and consumable by future tooling.

### Required headings (in order)

All 14 sections must be present. Small subheadings are permitted; the
top-level headings must match exactly so downstream prompts and future
validators can reliably consume the artifact.

```
## Summary
## Scope and roots inspected
## Current documentation inventory
## Current project and package layout
## Diataxis classification
## Navigation findings
## Accuracy findings
## Stale or ambiguous links
## Project-control-plane vs human-docs boundary
## Recommended target documentation structure
## Recommended phased PRs
## Proposed first PR scope
## Risks and cautions
## Validation commands for follow-up PRs
```

**"Proposed first PR scope" is mandatory.** It is consumed directly by
`/lrh-doc-organize` to scope the first reorganization PR. Keep it
actionable and concrete: specific file moves, stub creations, or README
edits — no vague recommendations.

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
   the fix is unambiguous, it may be noted in the "Risks and cautions" section
   as a "safe inline fix" — but it still requires user confirmation and a
   separate commit, not bundled with the audit artifact.

4. **Base gaps on current reality, not templates.** Do not flag the absence
   of documentation that "should" exist based on convention if there is no
   evidence the project intends to ship that feature or follow that convention.

5. **Distinguish planned from implemented.** If the repository has work items,
   proposals, or in-progress branches for documentation, note them as "planned"
   rather than "gap" in the inventory and recommendations.

6. **Keep all findings evidence-backed.** Every gap, stale link, and
   recommendation must cite specific file paths or absence thereof. Vague
   observations ("the docs could be better") are not audit findings.
