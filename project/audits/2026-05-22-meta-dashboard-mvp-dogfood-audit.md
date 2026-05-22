# Meta Dashboard MVP Dogfood Audit (2026-05-22)

Prompt ID: `PROMPT(AD_HOC:META_DASHBOARD_MVP_DOGFOOD_AUDIT)[2026-05-22T09:00:00-04:00]`
Date: 2026-05-22

## 1) Summary

This audit reviews the LRH meta dashboard MVP after the recent meta local-state and serve operational-triage work. The dashboard now appears to classify projects into useful swimlanes and surfaces actionable setup guidance for remote-only projects, but several trust and actionability gaps remain: missing validation diagnostics on error cards, stale/contradictory source-state capability-gap messaging, ambiguous setup-state semantics, and potentially misleading “Stable” presentation when focus exists but executable leaves are zero.

## 2) Scope

In-scope:

- Dashboard triage lane behavior and classifier assumptions.
- Meta local-state vs setup-state semantics in CLI/docs/tests.
- Card/detail actionability for validation failures.
- Capability-gap consistency and UX trust.
- Recommended implementation sequence for follow-up PRs.

Out-of-scope:

- Implementing fixes in `src/` or tests.
- Changing lane logic, API contracts, or CLI behavior in this PR.

## 3) Evidence reviewed

### Repository evidence (directly inspected)

- Design/control docs:
  - `project/design/proposals/proposed/lrh-serve-operational-triage-mvp/00_proposal.md`
  - `project/design/meta_control_plane_mvp_spec.md`
  - `project/design/execution_framework_mvp.md`
  - `project/focus/development_agenda.md`
- Meta semantics/docs:
  - `docs/reference/cli/meta.md`
  - `docs/how-to/register-a-project-with-meta.md`
- Dashboard/serve implementation and related tests:
  - `src/lrh/ux/dashboard.py`
  - `src/lrh/serve.py`
  - `tests/cli_tests/serve_test.py`
  - `tests/ux_tests/dashboard_test.py`
  - `tests/meta_tests/*` (setup/source-state semantics)
- Recent related execution records:
  - `project/executions/AD_HOC/2026_05_19_19_05_02_META_SERVE_LOCAL_STATE_DESIGN_ALIGNMENT.md`
  - `project/executions/AD_HOC/2026_05_20_12_33_16_META_INSPECT_LIST_SETUP_STATE.md`

### User-provided dogfood evidence

The prompt includes concrete dogfood observations (CLI output and dashboard state) that are treated as operator evidence for this audit. Exact saved HTML/log packet artifacts for that run were not found in-repo during this audit pass.

Recommendation: preserve future dogfood packets (commands + stdout/stderr + dashboard HTML/screenshots) under a stable path such as `project/evidence/meta_dashboard_dogfood/` and cross-link from future audits.

## 4) Current system behavior (audited view)

- The dashboard has deterministic lane ordering and conservative status derivation precedence (`blocked` > validation errors/warnings > review > active > explicit stable > unknown).
- Project cards expose source-state, validation summary fields, focus/workstream/work-item counts, readiness counts, capability gaps, and diagnostics slots.
- Detail pages now prioritize operational summary and “next useful action” before diagnostics.
- Meta state modeling distinguishes source availability (`remote_only`, `local_available`, etc.) from setup-state values (including `not_checked` in remote/truth-limited cases).

## 5) What appears to work

- Swimlane grouping and order exist and are tested.
- Remote-only setup guidance path (`lrh meta set ... --local-repo-path`) is present in meta and detail surfaces.
- Local-state model/test coverage for trusted vs private persistence exists.
- Validation status and count fields are available on cards/detail pages, supporting richer triage if populated.

## 6) Findings / issues

### F1 — Validation error diagnostics missing on error cards

Observed: projects in `Needs Attention` with `Validation status: error` but `Diagnostics: None`.

Assessment:

- Lane classification is probably correct when validation errors are known (by design precedence).
- Actionability is insufficient when error-bearing cards omit error specifics or reproduction hints.
- This looks like a **UX + shared-data-contract gap** (and may also be a bug in card-data population for diagnostics).

Impact:

- Operators cannot rapidly determine whether failures are setup, schema, reference, or environment issues.
- Increases context-switch cost (must leave dashboard/guess commands).

Recommended direction:

- Surface at least: error count, first N messages, and one command-to-reproduce.
- Add detail-page link anchoring to validation diagnostics for full context.

### F2 — Stale/contradictory `source_state` capability gap

Observed: card shows concrete `Source state` (e.g., `live` or `needs_local_checkout`) while also showing capability gap text indicating source-state live/cache inspection is “not implemented.”

Assessment:

- Likely stale capability-gap messaging after partial source-state implementation landed.
- Contradiction weakens trust and makes operators doubt current facts.
- This is best treated as a **bugfix/UX consistency issue**.

Recommended direction:

- Remove/retire stale “not implemented” message where concrete source-state is already resolved.
- If remaining capability is only cache freshness/remote inspection depth, rename gap to that narrower limitation.

### F3 — Active focus with zero workstreams/items/leaves semantics

Observed: LRH appears Stable with active focus text, but active/ready/readiness-deficient counts are all zero.

Assessment:

- Could reflect true control-plane state (focus exists but no currently active executable leaves).
- Could also indicate missing derivation/aggregation logic.
- Regardless, semantics are ambiguous for operators.

Classification:

- Primarily a **design/UX semantics gap**, potentially with minor implementation follow-up.

Recommended direction:

- Explicitly label this state (e.g., “Planning needed: focus active, no executable leaves”).
- Decide whether this remains `Stable` or should downgrade to `Needs Attention`/`Unknown`/new substate based on product intent.

### F4 — `setup_state: not_checked` vs `source_state: local_available/live`

Observed: local path checks and source-state can be positive while setup-state remains `not_checked`.

Assessment:

- Current docs/tests suggest this is mostly intentional: source-state answers source availability; setup-state is a separate setup-validation truth (and remote locators can remain not checked).
- However, naming and UI framing are easy to misread as contradiction.

Classification:

- **Semantics + naming clarity gap** (not necessarily a functional bug).

Recommended direction:

- Clarify field definitions in CLI/dashboard text and docs with explicit “what this means / what it does not mean.”
- Consider renaming or supplementing `setup_state` with clearer status labels (e.g., `setup_verification_state`).

### F5 — Additional opportunities/gaps

1. **Lane semantics vs setup/source precedence should be documented in one place** (currently inferred across code/tests/docs).
2. **Project-detail drill-down could include explicit validation diagnostics section parity** with command references.
3. **Adopted design implementation-count behavior should be either populated consistently or explicitly deferred** to avoid half-known metrics.
4. **Dogfood evidence retention is ad hoc**; reproducibility would improve with a standard packet path.
5. **Safe-default boundaries remain visible and should be preserved** (offline/file-based meta, read-only dashboard posture) while improving diagnostics.

## 7) Recommended next steps

### Bugfix-focused

1. Retire stale `source_state` capability-gap messaging when source-state is already resolved.
2. Ensure validation-error cards always include minimally actionable diagnostics payload.

### UX/semantics-focused

3. Clarify `setup_state` vs `source_state` labels/help text in meta surfaces and docs.
4. Add explicit operator-facing state for “focus active but no executable leaves.”

### Implementation-gap/data-contract-focused

5. Define shared dashboard diagnostic payload contract (`error_count`, `top_errors[]`, `repro_command`, `detail_link`).
6. Decide and document whether adopted-design implementation counts are in-scope now or explicitly deferred.

### Process/evidence-focused

7. Add a small “dogfood packet” convention for future audits under `project/evidence/`.
8. Reconcile/prioritize follow-ons in `project/focus/development_agenda.md` after above triage fixes.

## 8) Suggested implementation PR sequence

1. **PR-A (bugfix):** remove stale/contradictory `source_state` capability gap text.
2. **PR-B (dashboard diagnostics):** populate and render validation diagnostics summary + repro command + detail link.
3. **PR-C (semantics/docs):** `setup_state` vs `source_state` terminology and UI-copy alignment.
4. **PR-D (classification semantics):** define handling for active focus with zero executable leaves (lane/substate decision).
5. **PR-E (metrics scope):** adopted-design implementation count: implement or explicitly defer with stable messaging.
6. **PR-F (evidence workflow):** add lightweight dogfood packet storage convention and reference template.

## 9) Open questions

1. Should validation diagnostics come from a shared API model or be assembled in serve-specific code?
2. Is `Stable` intended to mean “valid with no active executable work,” or should that be a distinct planning-needed state?
3. Should `setup_state` remain separate but renamed, or should dashboard surfaces primarily emphasize `source_state` + explicit validation freshness?
4. What minimum diagnostic detail is acceptable in card view vs detail view?
5. When should adopted-design implementation counts become authoritative enough for lane/classification influence?

## 10) Validation performed for this audit PR

Commands run for this PR:

- `scripts/version tools`
- `lrh validate`
- `scripts/test`
- `scripts/lint`
- `scripts/format --check`

All command results are recorded in the PR summary and execution record for this prompt.
