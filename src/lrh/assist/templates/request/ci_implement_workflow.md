# CI Migration Implementation Request (Assessment-Gated)

Implement a focused CI migration PR only if this repository is an appropriate candidate.

==================================================
INPUT CONTEXT
==================================================

Optional background / prior assessment:
{{BACKGROUND_CONTEXT}}

Treat any supplied assessment as advisory context only.
You must independently inspect the repository before changing files.

==================================================
MANDATORY GATE: RE-ASSESS BEFORE EDITING
==================================================

Before editing any file:

1. Inspect the repository and produce a brief suitability gate covering:
   - language profile
   - packaging/build/test/tooling baseline
   - existing CI workflows
2. Decide whether LRH-style Python CI is appropriate.
3. If not appropriate, ABORT with a clear explanation and no file changes.

Acceptable abort reasons include (not exhaustive):
- repository is primarily non-Python (Rust/JS/C++/etc.)
- docs/content/art/book-only repository
- existing CI is already sufficient for project conventions
- insufficient evidence to make safe CI changes

==================================================
IMPLEMENTATION OBJECTIVE (ONLY IF GATE PASSES)
==================================================

Create a minimal, maintainable CI slice aligned to existing repository conventions.

Prefer this order:
1. local developer command entry points
2. GitHub Actions workflows that call those local commands

For appropriate Python projects, consider adding/updating only what is needed:
- `scripts/format`
- `scripts/lint`
- `scripts/test`
- `scripts/smoke`
- `.github/workflows/`
- `pyproject.toml`
- `README.md`
- `AGENTS.md`
- `STYLE.md`
- `CONTRIBUTING.md`

Only edit files that are truly appropriate for the target repository.

==================================================
COMMAND SEMANTICS GUIDANCE
==================================================

Adapt to repository reality; do not force a mismatch.

Expected semantics for LRH-style Python repositories:

- `scripts/format`
  - formatting in write mode (typically Black)
  - optionally Ruff fixes if already appropriate

- `scripts/lint`
  - Black check/diff mode
  - Ruff lint checks

- `scripts/test`
  - unittest discovery for `tests/*_test.py` when appropriate

- `scripts/smoke`
  - unittest discovery for `tests/smoke/*_smoke.py` when appropriate

If repository already uses pytest, nox, tox, uv, poetry, hatch, or similar:
- preserve established workflows
- integrate rather than replacing conventions

==================================================
SECURITY / SAFETY REQUIREMENTS
==================================================

GitHub Actions must use least privilege by default.

Prefer:

```yaml
permissions: read-all
```

or job-specific read-only permissions unless stronger permissions are genuinely required and explicitly justified.

Explicitly avoid:
- secrets/deploy/publish workflows
- write-token workflows
- `pull_request_target` unless there is a specific, security-reviewed need
- weakening existing checks

Action version pinning requirement:
- document your pinning choice
- for normal personal/development repos, major tags (e.g. `actions/checkout@v4`) may be acceptable
- for hardened/security-sensitive repos, full-length commit SHA pinning is the immutable option and should be considered

==================================================
STRICT PROHIBITIONS
==================================================

Do NOT:
- perform broad refactors
- perform language migration
- replace established non-unittest test framework without strong reason
- add fake/vacuous tests
- mass-format unrelated files
- edit unrelated subsystems

==================================================
VALIDATION REQUIREMENTS
==================================================

If you implement changes:

1. Run newly added/updated local scripts when feasible.
2. Run relevant tests when feasible.
3. Report exact commands and outcomes.
4. If a command cannot run, explain why.
5. Do not claim checks passed unless they actually ran.

==================================================
PR SUMMARY REQUIREMENTS
==================================================

Your final summary must include:
- assessment gate result
- files changed
- workflows/scripts added or updated
- validation commands and results
- intentional aborts or skipped pieces
- follow-up recommendations

==================================================
ABORT HANDLING
==================================================

If the gate fails, stop without edits and provide:
- concise evidence-based rationale
- recommended next step (for example native CI approach for the repository stack)
