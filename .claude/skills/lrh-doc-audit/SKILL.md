---
name: lrh-doc-audit
description: >
  Audit a repository's documentation layout using the Diataxis framework.
  Walks the repository, classifies each doc by quadrant (tutorial, how-to,
  reference, explanation), identifies gaps and stale links, drafts a
  structured audit artifact, and — after explicit user confirmation — writes
  it to project/audits/docs/docs-audit-YYYY-MM-DD.md. Use before
  /lrh-doc-organize to produce the audit artifact that scopes reorganization.
disable-model-invocation: true
argument-hint: "[docs-root-path]"
---

# lrh-doc-audit Skill

This skill audits a repository's documentation against the Diataxis
four-quadrant framework (tutorial, how-to, reference, explanation),
identifies gaps and stale links, and writes a structured audit artifact
at `project/audits/docs/docs-audit-YYYY-MM-DD.md`. It does not reorganize
docs — that is `/lrh-doc-organize`.

---

## Inputs

Provide an optional path to scope the audit, or omit to auto-discover:

```
/lrh-doc-audit
/lrh-doc-audit docs/
/lrh-doc-audit src/mypackage/
```

Without an argument the skill discovers all documentation in the repository
(top-level `docs/`, READMEs, `CONTRIBUTING.md`, etc.). With a path argument
the discovery pass is scoped to that subtree but still checks top-level files.

---

## Reference Knowledge

Load these before running any step:

1. **`references/diataxis-criteria.md`** — Four-quadrant definitions and
   classification heuristics. Read at Step 2 and apply at Step 4.

2. **`references/audit-requirements.md`** — Discovery checklist, artifact
   schema (required sections including "Proposed First PR Scope"), and
   guardrails (no reorganization in this operation). Read at Step 2 and
   apply at Steps 3, 5, and 6.

<!-- Template counterpart: src/lrh/assist/templates/request/audit_docs.md -->

---

## Execution Steps

Work through these steps in order. Do not skip Step 7 (confirm gate).

### Step 1 — Parse input

If an argument was provided, record it as the `docs-root` scope for the
discovery pass. If omitted, the scope is the entire repository.

Identify the repository's key paths:

- `repo_root`: current working directory (`.`)
- `docs_root`: argument if provided, otherwise auto-discover from Step 3
- `project_root`: `project/` (LRH control plane)
- `audit_output`: `project/audits/docs/docs-audit-<YYYY-MM-DD>.md`
  where the date is today's date

### Step 2 — Load references

Read `references/diataxis-criteria.md` and `references/audit-requirements.md`
in full before proceeding. The discovery checklist (Step 3), classification
logic (Step 4), and artifact schema (Step 6) all derive from these files.

### Step 3 — Discovery pass

Walk the repository and collect all documentation files. Follow the discovery
checklist in `references/audit-requirements.md`:

- Top-level `docs/`, `doc/`, `documentation/` directories
- Top-level `README.md` and all package-level READMEs
- `CONTRIBUTING.md`, `CHANGELOG.md`, `SECURITY.md`, `CODE_OF_CONDUCT.md`
- `examples/`, `notebooks/`, `tutorials/` directories if present
- CLI help output (`--help` flags) if a CLI is present
- Docstrings in public modules (presence and completeness)
- Control-plane `project/` documentation if any

Do not assume fixed paths — discover the actual layout. Note any files that
are present but not obviously documentation (e.g., `AGENTS.md`, `STYLE.md`).

### Step 4 — Diataxis classification

Classify each file discovered in Step 3 into one of:

- **Tutorial** — learning-oriented, guides a newcomer through a working exercise
- **How-to** — problem-oriented, recipe for achieving a specific goal
- **Reference** — information-oriented, describes machinery accurately
- **Explanation** — understanding-oriented, illuminates concepts or rationale
- **Mixed** — contains content from multiple quadrants (flag for splitting)
- **Meta** — project management content (CONTRIBUTING, CHANGELOG, AGENTS, etc.)

Apply the classification heuristics from `references/diataxis-criteria.md`.
When a file is clearly mixed, note which quadrants it spans.

### Step 5 — Gap and stale-link analysis

**Stale links:** scan all markdown files for internal links. For each
`[text](path)` target that does not begin with `http://` or `https://`:

1. **Skip pure fragment links** — if the entire target is `#something`,
   it is an in-page anchor; skip the filesystem check entirely.
2. **Strip fragment before checking** — if the target is `file.md#section`,
   check only `file.md` for existence; ignore the `#section` suffix.
3. **Resolve relative to the containing file** — check the resulting path
   relative to the directory of the file being scanned.

List any target that fails after these normalizations, with the file and line.

**Navigation gaps:** check for missing cross-links between related docs
(e.g., a how-to that references a concept with no explanation doc to link to).

**Quadrant gaps:** based on Step 4 results, identify which Diataxis quadrants
are underserved or entirely absent. Note specific missing content.

### Step 6 — Draft audit artifact

Using the schema from `references/audit-requirements.md`, draft the full
audit artifact in memory (do not write yet). The schema is the v1 convention
from `docs/reference/docs-audit-artifact-convention.md` — see that file and
`audit-requirements.md` for the full required frontmatter and heading list.

### Step 7 — Confirm gate (human gate)

Before writing any file, show the user:

- `audit_output` path
- Summary of findings (counts: files discovered, quadrant distribution,
  stale links, gap count)
- The "Proposed First PR Scope" section of the draft artifact

**Wait for explicit confirmation.** If the user wants to adjust scope or
findings, incorporate the feedback and re-show. Do not write the file without
approval.

### Step 8 — Write audit artifact

Write the confirmed artifact to `audit_output`:

```
project/audits/docs/docs-audit-YYYY-MM-DD.md
```

Create the `project/audits/docs/` directory if it does not exist. Do not
overwrite an existing artifact at the same path without explicit user consent.

### Step 9 — Validate

```bash
lrh validate
```

The audit artifact is a new file in `project/`; verify the validator accepts
it. If validation fails, report the error — do not commit a failing artifact.

### Step 10 — Offer commit

The audit artifact is an additive new planning document with no regression
risk. Offer:

- **Commit directly to main** — appropriate for a planning artifact. Stage the
  file and commit with a short message: `Add docs audit artifact YYYY-MM-DD`.
- **Open a PR** — if the user prefers review before merging. On this path,
  report the next steps: run `/lrh-review-response <pr-url>` to address
  reviewer comments (repeat as needed), then `/lrh-confirm-fixes <pr-url>` to
  verify the fixes against the current diff and resolve the review threads
  before merge. This skill creates no execution record itself, but
  `/lrh-review-response` and `/lrh-confirm-fixes` do — so after merging, run
  `/lrh-closeout <pr-url>` to land any records the review rounds created
  (skip it only if the PR merged with no review activity). The
  commit-to-main path has no PR at all, so none of the chain applies to it.

Do not commit without explicit direction.

---

## Quality Checklist

Before reporting completion, verify:

- [ ] References read at Step 2 before any discovery work
- [ ] Discovery followed the checklist in `audit-requirements.md`
- [ ] Every discovered file has a Diataxis classification
- [ ] Stale link scan run with command evidence
- [ ] All gap findings are evidence-backed (file paths cited)
- [ ] Draft artifact includes all required sections including "Proposed First PR Scope"
- [ ] User confirmed at Step 7 before any file was written
- [ ] `lrh validate` passes with 0 errors after write
- [ ] Commit or PR offered, not automatically executed

---

## What This Skill Does Not Do

- Does not reorganize documentation — that is `/lrh-doc-organize`
- Does not update docs to reflect new work — that is `/lrh-doc-work`
- Does not open a PR automatically — offers commit to main or PR after confirm
- Does not write to any path outside `project/audits/docs/`
- Discovers `project/` control-plane files and classifies them as **Meta** — does not force them into Diataxis quadrants or treat them as documentation
