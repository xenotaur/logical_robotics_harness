---
id: PROP-LRH-PII-SCAN
type: design_proposal
title: "lrh pii scan — Repo-Wide PII and Misplaced-Document Detection for LRH-Managed Repos"
status: adopted
created_on: 2026-08-21
updated_on: 2026-08-31
implementation_status: implemented
implemented_by:
  - WI-PII-SCAN-RULE-TAXONOMY
  - WI-PII-SCAN-LAYER1-ENUMERATOR
  - WI-PII-SCAN-LAYER2-CONTENT
  - WI-PII-SCAN-ALLOWLIST-OUTPUT
  - WI-PII-SCAN-CLI
supersedes: []
superseded_by: null
related_design:
  - project/design/proposals/adopted/lrh-secrets-command/00_proposal.md
  - project/design/proposals/proposed/ci-capability-scaffolding.md
  - src/lrh/conversations/sensitivity.py
  - src/lrh/conversations/README.md
  - src/lrh/project/bootstrap.py
---

## Summary

This proposal establishes LRH's philosophy for detecting personally identifiable information (PII) in a repository — content that is sensitive because of what it *is* (a bank statement PDF, a scan of an ID) or where it *appears* out of context, as distinct from `lrh secrets`' credential-shaped findings — and introduces `lrh pii scan`, a new, separate, audit-only command implementing that philosophy: two-layer detection (file-type/path heuristics first, text-pattern content checks second, scoped only to already-flagged files) across full git history via lightweight git plumbing, with repo-configurable rules on disclosed, sensible defaults.

## Background / Motivation

`lrh secrets scan` (adopted via `PROP-LRH-SECRETS-COMMAND`) wraps `gitleaks` to find credential-shaped strings in git history — a real, working capability, but scoped deliberately narrowly: its own Non-Goals state it "does not expand `gitleaks`' default rule coverage" (`project/design/proposals/adopted/lrh-secrets-command/00_proposal.md`). Auditing a real personal repo (`taurscripts`) by hand with `grep` after a clean `lrh secrets scan` surfaced a real, adjacent gap: content that is sensitive because it's personally identifying — a hardcoded hostname, a personal file path, or (the sharper case that emerged during design discussion) an entire document that shouldn't be in a source repo at all, such as a bank statement PDF accidentally swept in during a doc reorganization — is invisible to a credential scanner by design, not by defect. A clean `lrh secrets scan` is a correct, precise statement about credentials; it says nothing about this different class of content.

This proposal is for *any* LRH-managed repo, not LRH's own repo alone, and must work for a genuinely heterogeneous user base — from a user who only wants LRH to generate prompts, through skill users, to an active LRH contributor extending the harness itself. That heterogeneity is not new to this proposal: LRH already addresses it for onboarding docs via tiered `project_bootstrap` templates (`full`/`prompt_workflow`/`common`, orchestrated by `src/lrh/project/bootstrap.py`) and, in a closely analogous in-progress effort, for CI setup via `PROP-CI-CAPABILITY-SCAFFOLDING`'s staged, documentation-first, non-mandatory approach to a similarly heterogeneous problem ("do not force all projects onto one template," "do not fully automate... without human review" — `project/design/proposals/proposed/ci-capability-scaffolding.md`).

Real, current evidence from the LCATS repo (a sibling repo, the source of the incident that motivated `lrh secrets` itself) directly informs this proposal's philosophy, not just its detector design:

- LCATS's live `.pre-commit-config.yaml` has **no secret/PII-scanning hook**, even after a real live-key leak (PR #315) — it relies on `nbstripout` (a structural, content-agnostic control on the one leak vector it could close cheaply: notebook cell outputs) plus general code hygiene (`trailing-whitespace`, `ruff`, `black`), leaving pattern-based secret detection entirely at the retroactive-audit layer.
- LCATS's own `.gitleaks.toml` documents a rejected companion rule that inflated findings from 7 to 59, "almost all false positives" — concrete, first-party evidence that content-pattern detection is too imprecise to gate a commit, and should stay advisory unless proven otherwise.

This proposal treats that evidence as load-bearing: `lrh pii scan` is audit-only in this phase, and the accompanying doc states why, not just what.

## Prior Art Check

### Duplication search
- In-repo: No existing repo-history PII or file-classification scanner. `lrh.conversations.sensitivity` (`src/lrh/conversations/sensitivity.py`) is related but distinct: a text-string regex scanner built for conversation-transcript export privacy, with no git-awareness and no file-type/path classification. It is purely advisory — `sensitivity_scan` fields in `export_manifest.py` are informational only, with no gating behavior in any of the four export adapters. `lrh secrets` (`src/lrh/secrets/{scan,review,purge}.py`) is related but distinct: a gitleaks-wrapped, credential-only scanner with a decisions-file/marker-gated purge pipeline; its Non-Goals explicitly exclude expanding detection beyond gitleaks' own rule coverage.
- Sibling repos: LCATS's `.gitleaks.toml`/`.pre-commit-config.yaml` are prior art for *pattern* (gitleaks config) and *prevention-layer philosophy* (pre-commit scope), not for PII/file-classification detection itself — LCATS has no PII scanner either.
- External libraries: DLP/PII tools exist (Microsoft Presidio, cloud DLP services) but are either cloud-dependent (a privacy-relevant liability for a tool whose job is finding sensitive content) or NLP/ML-based (a heavier dependency than any existing LRH command carries). None is a drop-in local, dependency-free CLI binary the way `gitleaks`/`git-filter-repo` are.
- Recommendation: **Proceed.**

### Demand search
- Work items: None found under `project/work_items/`.
- Proposals: None found under `project/design/proposals/` prior to this one.
- Backlog: No matching entries in `project/design/backlog.md`.
- Recommendation: **No action** — net-new territory.

## Design Decisions

### Decision 1: A separate `lrh pii` command, not a new `lrh secrets` category

Options considered:
- Fold PII detection into `lrh secrets scan` as a new finding category, sharing `findings.json`/`review`/`purge`.
- Generalize `lrh.conversations.sensitivity` into the repo-scanning target.
- A new, separate command reusing selected machinery (rule taxonomy, purge safety scaffolding) without sharing orchestration.

**Chosen: a new, separate command family, `lrh pii`.** Folding into `lrh secrets` would contradict that command's own written Non-Goal against expanding rule coverage beyond gitleaks, and would corrupt the "clean scan" trust signal `lrh secrets scan` Decision 7 established by mixing gitleaks' high-precision structural findings with heuristic, lower-precision PII findings in one `findings.json`. `lrh.conversations.sensitivity`'s runtime has no git-awareness and would need a full history-walking harness built regardless of where the code lives, so "generalizing" it is not meaningfully cheaper than building fresh — only its rule *taxonomy* (category/severity/confidence shapes, regex table) is genuinely reusable, not its orchestration.

### Decision 2: Detection is two-layer, file-type/path first

Options considered:
- Text-pattern-only detection (email/phone/SSN/etc. regex across all files), matching `sensitivity.py`'s existing approach.
- File-type/path/filename heuristics as the sole signal.
- Two layers: file-type/path/filename heuristics as the primary signal; text-pattern content checks applied only within files the first layer already flagged.

**Chosen: two-layer, file-type first.** A pure text-pattern approach flags a contributor's public email in `CODEOWNERS` exactly as readily as a leaked customer list — indistinguishable without context, and expensive in false-positive noise (per LCATS's own 7→59 evidence). File-type/path/filename heuristics ("why is a `.pdf`/`.xlsx`/scan-like file here at all") catch the sharper failure mode this proposal was motivated by (an entire misplaced document, which may contain zero regex-matchable strings) while sidestepping the false-positive-prone case. Restricting Layer 2 to already-flagged files by default keeps text-pattern checks from ever running indiscriminately.

**Revision (PR #591 review, `chatgpt-codex-connector` P1):** restricting Layer 2 to Layer-1-flagged files *unconditionally* has a real cost this decision under-stated: an email, SSN, hostname, or personal path embedded in an ordinary `.py`, `.yaml`, or similar file whose path never trips Layer 1 is then never checked at all — silently missing exactly the "content sensitive because of where it appears out of context" case this proposal's own Background/Motivation names as a real, motivating example (personal hostnames, embedded email addresses). Narrowing Layer 2's scope by default was the right call for precision (the CODEOWNERS case above is real), but it should not be the *only* scope available. Fix: `.lrh-pii.toml` gains an opt-in `content_scan_scope` setting — `"flagged"` (default, current behavior: Layer 2 runs only inside Layer-1-flagged files) or `"all-text"` (Layer 2 runs across every text file in the enumerated path set, at the cost of the higher false-positive rate this decision already documented). Repos with a low tolerance for the CODEOWNERS-style false positive keep the default; repos willing to trade precision for recall on ordinary-file PII can opt in. This preserves the deliberate default this decision was built around while closing the coverage gap the review identified.

### Decision 3: Full-history coverage via lightweight git plumbing, not a bespoke blob-walker

Options considered:
- Working-tree-only scan (cheapest, matches how the motivating gap was found by hand).
- Full git history via a bespoke commit/blob-walking engine (gitleaks-equivalent scope of effort).
- Full git history via existing git plumbing (`git log --all --diff-filter=A --name-only`, `git rev-list --objects --all` — documented at https://git-scm.com/docs/git-log and https://git-scm.com/docs/git-rev-list) to enumerate every path ever added across all refs, fetching blob content on demand (`git show <commit>:<path>`) only for paths Layer 1 already flags.

**Chosen: full history via lightweight plumbing.** A clean `lrh pii scan` run should mean something comparable to a clean `lrh secrets scan` run — working-tree-only coverage would silently miss PII that was committed and later deleted, understating what the tool claims to check. Git's own plumbing supplies path enumeration without requiring a gitleaks-scale scanning engine; content-fetching cost scales with flagged-file count, not repo size, keeping this tractable. Rename/merge behavior under `--diff-filter=A` needs explicit test coverage before this ships, since add/rename can behave surprisingly depending on rename-detection settings.

**Revision (PR #591 review, `chatgpt-codex-connector` P1):** the description above under-specified which commit(s) get their content fetched for a flagged path. `--diff-filter=A` identifies only the *add* commit; fetching content only there means a file committed with benign content and modified later to add sensitive content is never inspected in its sensitive state — a real gap against this decision's own "full-history coverage" claim, since a file can be flagged by Layer 1 at add time yet still hide its sensitive revision from Layer 2. Fix: for each Layer-1-flagged path, enumerate every commit that touched that path across all refs (`git log --all --follow --name-only -- <path>`, or equivalently every entry from `git rev-list --objects --all` whose path matches), not only its add commit, and fetch content at each such commit for Layer 2. This is still bounded by flagged-file count, not repo size — the added cost is per-path commit count for already-flagged paths, not a new full-repo pass.

### Decision 4: Rule config — `.lrh-pii.toml`, auto-discovered, `useDefault`-extendable

Options considered:
- Hardcoded, non-configurable defaults.
- CLI-flag-only configuration (no repo-committed file).
- A repo-committed, auto-discovered TOML file extending built-in defaults, modeled directly on `.gitleaks.toml`.

**Chosen: `.lrh-pii.toml`**, auto-discovered at `--project-root`, `[extend] useDefault = true` shape — the same convention LCATS's own live `.gitleaks.toml` already uses in production. Built-in defaults are a disclosed, reviewable starter list (file-extension/path-glob signals — `*.pdf`, `*.docx`, `*.xlsx`, `*.pem`, image formats outside designated `docs/assets`-style directories — plus filename-keyword signals such as `statement`, `ssn`, `passport`, `w-9`, `medical`), not a claim of completeness. This directly satisfies "repo-configurable with sensible defaults" while reusing a pattern this repo has already validated in production rather than inventing a new discovery mechanism.

### Decision 5: Rule-taxonomy sharing, not runtime sharing

**Chosen:** extract `sensitivity.py`'s `_Rule`/category/severity/confidence dataclasses and regex table into a new shared module (e.g. `src/lrh/shared/sensitivity_rules.py`), imported by both a refactored `lrh.conversations.sensitivity` (pure, behavior-preserving extraction, with its own test coverage) and the new `lrh.pii.scan`. `sensitivity.py`'s git-unaware, transcript-string runtime is not reused — only its taxonomy. This directly implements this session's "shared taxonomy, not shared orchestration" conclusion, avoiding a second, parallel invention of "what counts as an email/SSN/IP" while keeping the two subsystems' actual scanning engines independent.

### Decision 6: Allowlist — lighter than `lrh secrets review`'s decisions-file/marker gate

Options considered:
- Reuse `lrh secrets review`'s full decisions-file + `# lrh-secrets-reviewed v1` marker-gate model.
- A lighter, repo-committed, fingerprint-keyed allowlist file (`.lrh-pii-allowlist`), `.gitleaksignore`-style.
- No allowlist mechanism in v1.

**Chosen: the lighter allowlist file.** `lrh secrets`' marker-gate exists specifically to guarantee an unreviewed finding set can never reach `purge`'s irreversible history rewrite — that hazard doesn't exist here, since `lrh pii scan` has no purge/remediation subcommand in v1. A fingerprint-keyed allowlist (optional reason comment) gives repos a way to suppress reviewed-and-accepted findings without the heavier ceremony a purge-gate would justify. If a purge-style remediation path is added later, this decision may need revisiting toward the heavier model — noted in Open Questions.

**Revision (PR #591 review, `chatgpt-codex-connector` P1):** the original fingerprint, `sha256(path + rule_id)`, identifies a *location and rule*, not a specific finding instance. A repository that reviews and accepts one benign match at a given path/rule (e.g. a placeholder value that happens to pass the credit-card Luhn check) would have that same fingerprint silently suppress a genuinely sensitive value introduced at the same path under the same rule later — the allowlist entry outlives the specific content it was reviewed against. Fix: bind the fingerprint to content identity as well as location — `sha256(path + rule_id + content_digest)`, where `content_digest` is the git blob SHA (for a Layer-1 file-type/path match, the flagged file's blob at the commit in question) or a hash of the specific matched substring (for a Layer-2 content match). Approving one instance now scopes the suppression to that exact content; a later change to the same path under the same rule gets a new fingerprint and surfaces as a fresh finding.

### Decision 7: Output schema — not gitleaks-shaped

**Chosen:** `pii_findings.json` as a list of `{path, rule_id, category, severity, confidence, commit, content_digest, still_in_working_tree, matched_layer: "path"|"content"}`, deliberately distinct from gitleaks' `{Secret, RuleID}` shape. A file-level finding is not secret-value-shaped — forcing it into `lrh secrets`' schema was considered and rejected during design discussion. Output ends with a disclosure block (no OCR, no ML/NLP content classification, heuristic only), mirroring `lrh secrets scan`'s Decision 7 discipline of stating known gaps in the tool's own output rather than only in prose documentation.

**Revision (PR #591 review, follow-on from Decisions 3 and 6 above):** the original schema's `first_seen_commit` implied one finding per path, tied to its add commit — no longer accurate once Decision 3 enumerates every commit touching a flagged path, and Decision 6's content-bound allowlist fingerprint needs a `content_digest` field to bind against. `first_seen_commit` becomes `commit` (the specific commit this finding instance was observed at, which may recur per-path across multiple findings once Decision 3's multi-commit enumeration is in effect), and `content_digest` is added (the git blob SHA for a Layer 1 match, or a hash of the matched substring for a Layer 2 match) so each finding carries the content identity Decision 6's allowlist fingerprint is computed from.

### Decision 8: Companion doc — `docs/how-to/project-setup/pii.md`, delivered through the existing tiering mechanism

**Chosen:** a new how-to doc stating LRH's PII philosophy (opt-in never mandated; audit-first; precision scales with consequence; structural prevention preferred where available; disclose gaps in-tool; human-in-the-loop remediation always; deliver through existing bootstrap tiers; repo owns its own exceptions), grounded in the LCATS evidence above, paralleling `docs/how-to/project-setup/ci.md`'s role for `PROP-CI-CAPABILITY-SCAFFOLDING`. Actual placement of this doc within `project_bootstrap`'s `full`/`prompt_workflow`/`common` tiers is noted as design intent for a follow-on work item, not implemented by this proposal — this proposal's own PR adds the doc to `docs/how-to/project-setup/` only.

## Non-Goals

- Does not implement a purge/remediation subcommand or any history-rewrite capability for PII findings — `lrh pii scan` is read-only, matching `lrh secrets scan`'s own "this command only reads and reports" posture.
- Does not implement OCR or any image/scanned-document text extraction.
- Does not implement ML/NLP-based content classification, and does not call any cloud DLP service — detection stays local and deterministic, matching `sensitivity.py`'s own stated posture.
- Does not wire `lrh pii scan` into pre-commit hooks or CI for any repo, LRH's own included — audit-only, on-demand, consistent with the LCATS precedent and this proposal's philosophy.
- Does not wire the CLI tool itself into `project_bootstrap` tiers in this phase — only the doc's eventual tier placement is noted as intent (Decision 8); implementing that placement is deferred to follow-on work.
- Does not create the implementing workstream or work items — those are a deliberately separate, later step per this session's direction.
- Does not modify `lrh secrets`' behavior, schema, or Non-Goals in any way.

## Implementation Plan

This proposal is documentation-and-design only; no code changes ship in this PR. Implementation is expected to require multiple PRs and at least one genuinely novel low-level build (the git-plumbing-based history enumerator), so a governing workstream is the appropriate next artifact — but per this session's explicit direction, that workstream (and any work items) is created as a separate, later step, not as part of this proposal.

Likely follow-on work items, if/when a workstream is created:
- Extract `sensitivity.py`'s rule taxonomy into `src/lrh/shared/sensitivity_rules.py` (behavior-preserving refactor, own test coverage).
- Implement the git-plumbing-based path enumerator and Layer 1 (file-type/path/filename) detector, with `.lrh-pii.toml` config discovery and defaults.
- Implement Layer 2 (content-pattern detection scoped to Layer-1-flagged files), reusing extracted rules and `lrh.conversations.pdf_import`'s existing non-OCR PDF text extraction.
- Implement the `.lrh-pii-allowlist` mechanism and `pii_findings.json`/text-summary output.
- Wire `lrh pii scan` into `src/lrh/cli/main.py`.

## Cross-References

- Sibling command precedent: `project/design/proposals/adopted/lrh-secrets-command/00_proposal.md`
- Analogous heterogeneous-repo capability design: `project/design/proposals/proposed/ci-capability-scaffolding.md`
- Rule-taxonomy source for extraction: `src/lrh/conversations/sensitivity.py`, `src/lrh/conversations/README.md`
- Existing tiering mechanism: `src/lrh/project/bootstrap.py`, `src/lrh/templates/project_bootstrap/{full,prompt_workflow,common}/`
- Companion doc (this PR): `docs/how-to/project-setup/pii.md`
- External, currently-live prior art referenced: LCATS `.gitleaks.toml`, `.pre-commit-config.yaml`

## Open Questions

- Full-history plumbing-based scan vs. a smaller working-tree-only v1 — this proposal recommends full history (Decision 3), but it is a real effort tradeoff worth revisiting if implementation cost proves higher than expected.
- Allowlist auditability (Decision 6) — the lighter `.gitleaksignore`-style file is recommended for v1; may need to grow toward `lrh secrets review`'s heavier decisions-file/marker model if a purge-style remediation path is ever added.
- The filename-keyword default list (Decision 4) is sketched, not exhaustive — a concrete starter set is left to the implementing work item, the same way `lrh secrets`' decisions-file format was left open in `PROP-LRH-SECRETS-COMMAND`.
- Exact placement of `docs/how-to/project-setup/pii.md` within `project_bootstrap`'s tiers (Decision 8) is unresolved — noted as intent, not decided here.
