# CI Feasibility Assessment Request (Read-Only)

Assess whether this repository is a good candidate for LRH-style Python CI.

This is an assessment-only request.

- Do NOT edit files.
- Do NOT generate a patch.
- Do NOT open a PR.
- Do NOT propose speculative implementation details not grounded in repository evidence.

==================================================
INPUT CONTEXT
==================================================

Optional background:
{{BACKGROUND_CONTEXT}}

==================================================
OBJECTIVE
==================================================

Inspect the repository and produce a conservative CI migration feasibility assessment.

The assessment must determine whether LRH-style Python CI is appropriate, whether adaptation is needed, or whether CI migration should be aborted.

==================================================
REQUIRED INSPECTION CHECKLIST
==================================================

Inspect and summarize evidence for all of the following:

1. Primary language(s)
   - Identify dominant language(s) based on repository contents.
   - Note if repository is Python-first, mixed-language, or non-Python.

2. Build/package/dependency system
   - Examples: pyproject/pip/uv/poetry/hatch/tox/nox/Makefile/npm/cargo/etc.

3. Existing CI/workflow baseline
   - Inspect `.github/workflows/` (or equivalent CI if present).
   - Summarize workflows and what they enforce.

4. Test framework and test layout
   - Determine current test framework(s): unittest / pytest / others / none.
   - Summarize test folder/file patterns and maturity.

5. Formatter/linter/tooling choices
   - Examples: black, ruff, flake8, mypy, isort, prettier, eslint, cargo fmt/clippy.

6. Dependency/install instructions
   - Summarize documented local setup and test commands.
   - Highlight gaps that block confident CI setup.

7. Repository shape classification
   - Classify as one of:
     - importable Python package
     - Python scripts/tools collection
     - notebook-heavy project
     - mixed-language repository
     - documentation/content-only repository
     - other (explain)

8. CI suitability judgment
   - Is LRH-style Python CI appropriate as-is?
   - Would adaptation be required?
   - Would native non-Python CI be more appropriate?

9. Risks and unknowns
   - Explicitly list uncertainty and evidence gaps.

10. Recommended next step
   - Recommend proceed/adapt/abort with rationale.

==================================================
STATUS VOCABULARY (REQUIRED)
==================================================

End the assessment with exactly one final status from this set:

- PROCEED_PYTHON_LRH_STYLE
- PROCEED_WITH_ADAPTATION
- ABORT_NOT_PYTHON
- ABORT_DOCS_OR_CONTENT_ONLY
- ABORT_EXISTING_CI_IS_SUFFICIENT
- ABORT_INSUFFICIENT_EVIDENCE

==================================================
OUTPUT FORMAT (REQUIRED)
==================================================

# CI Feasibility Assessment

## Repository Signals
- Primary language(s):
- Package/build system:
- Existing workflows:
- Test framework/layout:
- Formatter/linter choices:
- Dependency/install instructions:
- Repository shape classification:

## Suitability Analysis
- LRH-style Python CI fit:
- Native/non-Python CI fit:
- Risks:
- Unknowns:

## Recommendation
- Next step recommendation:

If final status is `PROCEED_PYTHON_LRH_STYLE` or `PROCEED_WITH_ADAPTATION`, also include:
- Minimal likely implementation slice (scripts/workflows/docs):
- Expected local command entry points to add or align:

## Final Status
`<ONE_REQUIRED_STATUS_TOKEN>`

==================================================
DECISION RULES
==================================================

- Be conservative.
- Prefer abort status over speculative migration when evidence is weak.
- Do not recommend blindly copying LRH CI into non-Python or weak-fit repositories.
- If the repository already has sufficient CI for its stack and maturity, prefer `ABORT_EXISTING_CI_IS_SUFFICIENT`.
