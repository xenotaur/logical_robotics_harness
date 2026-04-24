---
id: FOCUS-CONTROL-PLANE-SEMANTICS
title: Harden assist packaging and keep survey expansion scoped
status: active
priority: high
owner: anthony
related_principles:
  - PRINCIPLES-ENGINEERING
  - PRINCIPLES-EVALUATION
---

# Current Focus

The immediate priority is to keep assist package behavior hardened and treat survey capability growth as scoped follow-on work.

Recently completed:

- request-system extraction into `src/lrh/assist/`
- thin CLI wrappers wired to `lrh request` and `lrh snapshot`
- package-owned assist templates under `src/lrh/assist/templates/`
- canonical `lrh survey` delegation to `src/lrh/assist/sourcetree_surveyor.py`
- assist README updates documenting canonical CLI usage

## Why this is active now

LRH now has canonical assist interfaces (`lrh request`, `lrh snapshot`, and `lrh survey`) backed by package-owned runtime code and assets.

The next risk is not migration mechanics; it is protecting installability guarantees and keeping any survey capability expansion intentionally separate from packaging/runtime stability work.

## Priorities

1. Keep package-owned templates and resource loading behavior stable for installed usage.
2. Maintain packaging/build/install hardening and smoke-test expectations for installed behavior.
3. Keep `lrh survey` canonical on `src/lrh/assist/sourcetree_surveyor.py`.
4. Handle sourcetree capability expansion only as a separate follow-on work item.

## Non-Goals

- Reopening already completed mechanical migration work in docs or planning.
- Broad redesign of request/snapshot/survey semantics.
- Unrelated refactors outside assist packaging and scoped follow-on expansion planning.

## Exit Criteria

This focus is complete when:

1. package-owned templates remain the runtime source of truth
2. installed `lrh request`/`lrh snapshot` behavior does not rely on repo-relative template discovery
3. packaging/install smoke checks are defined and passing
4. `lrh survey` remains canonical on package code, with capability expansion explicitly deferred
