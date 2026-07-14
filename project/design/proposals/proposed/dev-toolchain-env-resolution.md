---
id: PROP-DEV-TOOLCHAIN-ENV-RESOLUTION
type: design_proposal
title: Dev Toolchain Environment Resolution — Reliance on Taurworks Activation
status: proposed
created_on: 2026-07-14
updated_on: 2026-07-14
implementation_status: not_started
supersedes: []
superseded_by: null
---

# Dev Toolchain Environment Resolution: Reliance on Taurworks Activation

> Documentation-only design proposal. It frames a decision and recommends a
> direction; it introduces no CLI, schema, script, or runtime change. Related
> alignment doc: [`project/design/dev_toolchain_reconciliation.md`](../../dev_toolchain_reconciliation.md).

## 1) Decision this proposal frames

**Should LRH-managed projects rely on Taurworks — specifically
`.taurworks/config.toml [activation.environment]` plus the shipped sourced
`tw activate` helper — to resolve *which* environment their canonical
`scripts/format` / `scripts/lint` / `scripts/test` run in? Or should LRH own an
independent, Taurworks-free mechanism?**

This is deliberately a coupling question, not a formatter question. Formatting
drift is only the presenting symptom.

## 2) Motivating incident (2026-07-14)

On a clean checkout of `taurworks` `master`, `scripts/lint` reported that
`src/taurworks/manager.py` "would be reformatted" and a maintainer nearly opened
a chore PR to fix it. Investigation showed the opposite of the assumed cause:

- The **CI-pinned** Black (`black==26.3.1`, from `constraints-dev.txt`) considers
  the file **already correct**; CI lint is green.
- The reformatting was produced only by a **stale base-anaconda Black 25.11.0**,
  which wraps `f.write(f"""…""")` heredoc calls that 26.3.1 leaves compact.
- Formatting under the stale tool would have injected an out-of-scope diff that
  CI's Black then *rejects* — a net-negative "fix."

The `taurworks` project already carries a correctly-versioned environment (a
`Taurworks` conda env whose Black matches the pin); the failure existed purely
because the invoking session had **no environment resolved** and fell back to
base anaconda. This is exactly the class of cross-environment drift that
`dev_toolchain_reconciliation.md` sets out to eliminate.

## 3) Two axes, often conflated

`dev_toolchain_reconciliation.md` states the invariant well: *for the same commit
SHA and canonical commands, every environment (local, CI, Codex Cloud, Claude
Code, …) should produce the same validation result.* Achieving it has two
separable parts:

1. **Version enforcement** — the tools that run are the *right versions*
   (pinning + runtime version guardrails + fail-fast). `dev_toolchain_reconciliation.md`
   already leans LRH-native here, and that direction is sound: it works in bare
   CI checkouts and needs no external project.
2. **Environment resolution** — *which* interpreter/environment the canonical
   scripts run inside in the first place. This is the unaddressed half, and the
   place where "rely on Taurworks?" actually bites. The canonical scripts invoke
   bare `python -m black`; the answer depends entirely on what env is active,
   which no artifact currently pins for non-interactive/agent callers.

Keeping these axes distinct is the main analytical move of this proposal.

## 4) What Taurworks already provides

- **Consumer (shipped):** `.taurworks/config.toml` `[activation.environment]
  type = "conda"` → `taurworks project activate --shell` → sourced `tw activate`
  switches the conda env and `cd`s into `working_dir`. Verified working across
  the user's migrated projects.
- **Producer (queued, not shipped):** `WI-ACTIVATION-PRODUCERS-0001` in
  `taurworks` adds the writer (`project env set`, `--env` on create/init, legacy
  convergence) so a fresh user can author `[activation.environment]` with shipped
  commands.
- **Layout:** `.taurworks/` is a *sibling* of the git repo
  (`<Project>/.taurworks/` next to `<Project>/git_repo/`), so it is out of source
  control by construction — and, notably, **absent from bare CI checkouts** and
  fresh agent clones.

## 5) Options

### Option A — Rely on Taurworks activation
Canonical scripts (and agent guidance) resolve the environment via Taurworks:
read `.taurworks/config.toml [activation.environment]` / go through `tw activate`
before running tools.

- **Pros:** reuses shipped, already-dogfooded machinery; single source of truth
  the user already maintains across projects; solves resolution uniformly for
  every Taurworks-managed repo; no new mechanism to invent.
- **Cons:** couples LRH to Taurworks as a runtime dependency; Taurworks must be
  installed and on PATH in *every* LRH environment including CI/Codex/fresh
  agents; `.taurworks/` is sibling-only so bare CI checkouts lack it; producer
  side is not shipped yet. **And a direction problem (see §6).**

### Option B — LRH-native, Taurworks-free
Extend `dev_toolchain_reconciliation.md`'s direction to resolution too: canonical
scripts self-guard with pinned versions + runtime version checks that fail fast,
and (optionally) an LRH-native env pointer LRH fully owns.

- **Pros:** no cross-project dependency; works in bare CI and any agent clone;
  LRH owns its own invariant end-to-end.
- **Cons:** duplicates activation logic Taurworks already has; version checks
  *validate* the active env but do not *resolve/switch* to the right one, so a
  human/agent must still activate correctly per environment; more surface for LRH
  to maintain.

### Option C — Native enforcement, optional Taurworks resolution (recommended framing)
Split by axis: LRH **owns version enforcement natively** (guardrails in canonical
scripts, effective everywhere including bare CI), and **opportunistically consumes
Taurworks for resolution when present** through a narrow, Taurworks-*optional*
interface: if `.taurworks/` + `tw` are detected, scripts resolve/activate through
them; otherwise they fall back to the active env and rely on the native
guardrail to fail fast on drift.

- **Pros:** keeps the hard dependency out (CI/Codex still work with no Taurworks);
  reuses Taurworks where it genuinely helps (the user's own multi-project
  workflow); the native guardrail is the safety net that makes a *missed*
  resolution loud instead of silent (it would have caught the motivating
  incident regardless of Taurworks).
- **Cons:** two code paths to keep coherent; requires a stable, documented
  detection/interface contract with Taurworks.

## 6) Decision drivers

- **Dependency direction / circularity.** Taurworks is itself an *LRH-managed*
  project — it depends on `lrh` for project management. A *hard* LRH→Taurworks
  runtime dependency for dev-env activation would make the two mutually
  dependent. This is the strongest argument for keeping Taurworks **optional** to
  LRH (Options B or C) rather than required (Option A).
- **Environments without `.taurworks/`.** Bare CI checkouts, Codex Cloud, and
  fresh agent clones have no sibling `.taurworks/`. Any resolution mechanism LRH
  *depends on* must degrade cleanly where it is absent — again favoring a native
  safety net.
- **Single source of truth vs duplication.** The user already maintains
  `[activation.environment]` per project; ignoring it (pure Option B) duplicates
  a fact that already exists, while requiring it (Option A) over-commits.
- **Resolve vs validate.** Version guardrails only *validate* the active env;
  they never *switch* it. Taurworks activation is currently the only mechanism
  that actually *resolves and switches* to the right env. If LRH wants
  hands-off correctness (not just loud failure), it needs a resolver — and
  Taurworks is the one that exists.

## 7) Recommendation

Adopt **Option C**: make **version enforcement LRH-native and mandatory**
(the safety net that would have turned the motivating incident from a silent
near-miss into an immediate, explanatory failure in any environment), and treat
**Taurworks activation as an optional, detected resolver** for environments that
have it — never a hard dependency. This resolves the coupling question in the
direction that avoids the LRH↔Taurworks circularity while still reusing the
shipped activation machinery where it earns its keep.

This proposal does not itself implement either half. If adopted, it would spawn:
(1) an LRH work item for native version guardrails in the canonical scripts
(coordinated with `dev_toolchain_reconciliation.md`), and (2) a definition of the
optional Taurworks detection/interface contract, coordinated with
`taurworks`'s `WI-ACTIVATION-PRODUCERS-0001`.

## 8) Non-goals

- No implementation of guardrails, scripts, or activation in this proposal.
- No change to Taurworks' `[activation.environment]` schema or `tw activate`.
- No decision on non-conda environment strategies (venv/Docker) — out of scope.
- No new hard runtime dependency is being adopted by writing this document.

## 9) Open questions

- Where should a native env guardrail live — inside `scripts/*`, a shared
  `scripts/_env.sh` sourced by each, or CI bootstrap only?
- What is the minimal, stable Taurworks detection contract (presence of `tw` on
  PATH? a `taurworks project activate --print` probe?) that LRH can depend on
  without pinning Taurworks internals?
- Should LRH ship a fallback for contributors who use neither Taurworks nor the
  documented env (e.g. a clear "activate X, or run under Taurworks" error)?
