# CI Feasibility Assessment Request (Read-Only)

Assess whether this repository is a good candidate for CI work using the LRH CI setup and debugging playbook at `docs/project-setup/ci.md`.

This is an assessment-only request.

- Do NOT edit files.
- Do NOT generate a patch.
- Do NOT open a PR.
- Do NOT propose speculative implementation details not grounded in repository evidence.
- Do NOT assume one universal workflow template before discovering project family, commands, and existing CI state.

==================================================
INPUT CONTEXT
==================================================

Optional background:
{{BACKGROUND_CONTEXT}}

==================================================
OBJECTIVE
==================================================

Inspect the repository and produce a conservative CI migration feasibility assessment.

The assessment must apply the playbook at `docs/project-setup/ci.md`, determine the project family before recommending workflows, discover canonical repository commands before proposing validation steps, and decide whether CI migration should proceed, adapt to repository conventions, or abort.

==================================================
REQUIRED INSPECTION CHECKLIST
==================================================

Inspect and summarize evidence for all of the following:

1. Project family and primary language(s)
   - Identify the repository family described by `docs/project-setup/ci.md`: Python package/tool, Python scripts/tools collection, Unix command/tool repository, Rust/Cargo, Rust/WASM/WebGPU, JavaScript/TypeScript, game/simulation, documentation/static site, mixed repository, or other.
   - Identify dominant language(s) based on repository contents.
   - Note if repository is Python-first, mixed-language, or non-Python.

2. Build/package/dependency system
   - Examples: pyproject/pip/uv/poetry/hatch/tox/nox/Makefile/npm/cargo/etc.
   - Separate setup/bootstrap commands from validation commands.

3. Existing CI/workflow baseline
   - Inspect `.github/workflows/` (or equivalent CI if present).
   - Summarize workflows and what they enforce.
   - If workflows exist, identify whether the repository has `scripts/check-workflows` or a closest project-approved workflow YAML check.

4. Test framework and test layout
   - Determine current test framework(s): unittest / pytest / others / none.
   - Summarize test folder/file patterns and maturity.

5. Formatter/linter/tooling choices
   - Examples: black, ruff, flake8, mypy, isort, prettier, eslint, cargo fmt/clippy.
   - Treat stronger tooling such as actionlint, pre-commit, tox/nox, dev containers, or lockfile changes as deliberate follow-ups unless explicitly requested by the task or already established by the repository.

6. Dependency/install instructions and canonical commands
   - Inspect repository scripts, docs, and config before proposing commands.
   - Summarize documented local setup and test commands.
   - Identify canonical commands for setup/bootstrap, tool/version reporting, workflow YAML checks, format checks, lint checks, tests, smoke checks, and coverage where present.
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
   - Would the existing CI be sufficient without migration?

9. Risks and unknowns
   - Explicitly list uncertainty and evidence gaps.
   - Do not say "cannot reproduce", "pre-existing failure", "flaky", or "fixed" without concrete evidence such as commit, working tree status, tool versions, command output, logs, reports, screenshots, or review notes.

10. Recommended next step
   - Recommend proceed/adapt/abort with rationale.
   - Keep recommendations repository-specific and tied to discovered commands and existing CI state.

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

## Playbook Reference
- CI playbook: `docs/project-setup/ci.md`

## Repository Signals
- Project family:
- Primary language(s):
- Package/build system:
- Existing workflows:
- Workflow YAML check:
- Test framework/layout:
- Formatter/linter choices:
- Setup/bootstrap instructions:
- Canonical validation commands:
- Repository shape classification:

## Suitability Analysis
- LRH-style Python CI fit:
- Native/non-Python CI fit:
- Existing CI sufficiency:
- Risks:
- Unknowns:

## Evidence Notes
- Commands inspected:
- Files inspected:
- Evidence gaps:

## Recommendation
- Next step recommendation:

If final status is `PROCEED_PYTHON_LRH_STYLE` or `PROCEED_WITH_ADAPTATION`, also include:
- Minimal likely implementation slice (scripts/workflows/docs):
- Expected local command entry points to add or align:
- Setup/bootstrap vs validation boundary:
- Workflow YAML validation command (`scripts/check-workflows` or closest approved equivalent):

## Final Status
`<ONE_REQUIRED_STATUS_TOKEN>`

==================================================
DECISION RULES
==================================================

- Follow `docs/project-setup/ci.md`.
- Be conservative.
- Prefer abort status over speculative migration when evidence is weak.
- Do not recommend blindly copying LRH CI into non-Python, mixed-stack, or weak-fit repositories.
- Do not recommend actionlint, pre-commit, tox/nox, dev containers, or lockfile/toolchain changes unless the task explicitly calls for them or repository evidence shows they are already canonical.
- If the repository already has sufficient CI for its stack and maturity, prefer `ABORT_EXISTING_CI_IS_SUFFICIENT`.
