---
id: "PROP-LRH-PROFILES"
type: "design_proposal"
title: "LRH Profiles: Named, Isolated Meta and Console Configuration"
status: "proposed"
created_on: "2026-10-09"
updated_on: "2026-10-09"
implementation_status: "not_started"
implemented_by: []
evidence: []
supersedes: []
superseded_by: null
related_design:
- "docs/explanations/workspace-and-meta-model.md"
- "docs/how-to/lrh-console-local-dogfood.md"
- "project/design/proposals/proposed/lrh-console-local-dogfood/00_proposal.md"
- "project/workstreams/active/WS-LRH-CONSOLE-LOCAL-DOGFOOD.md"
---

# LRH Profiles: named, isolated Meta and Console configuration

## Summary

Add a Chrome-style "profile" to LRH: a named, isolated set of Meta config,
state and cache, plus its own LRH Console app config. A profile is selected by
`LRH_PROFILE` or `--profile`, resolved by one shared module that both the
`lrh` CLI and LRH Console use. The `default` profile is today's layout, so
nothing migrates.

## Background / Motivation

An installed LRH Console always reads one `config.json`
(`apps/desktop/src-tauri/src/shell.rs:1064-1068`; identity fixed by
`tauri.conf.json:4`). The backend it launches resolves one global Meta
workspace from flags, `LRH_CONFIG`, `LRH_WORKSPACE`, local `.lrh/config.toml`
discovery, then `$XDG_CONFIG_HOME/lrh/config.toml`
(`src/lrh/meta/workspace.py:905-1004`, `1280-1298`; `src/lrh/serve.py:141`).
The app's `Config` has no Meta field (`settings.rs:71-80`); Meta isolation
comes only from the backend's environment. Users cannot keep two starting
projects with different configs, and developers cannot try a new LRH
installation against a fresh Meta directory.

An existing developer override (`LRH_CONSOLE_*`, `shell.rs:37-47`) covers part
of testing but has a hazard: `save_settings` writes the shared `config.json`
before checking for the override (`shell.rs:1387` vs `1391`), so a Save during
a test session overwrites the real configuration.

## Prior Art Check

### Duplication search
- In-repo: No existing implementation found. "Profile" already means bootstrap
  profile (`src/lrh/cli/main.py:344`), the chain-defaults profile, and
  `AssistantProfile` (WI-LRH-ASSISTANTS-STAGE-2): naming collisions, not
  duplicates.
- Sibling repos: None identified (owner not asked beyond this session).
- External libraries: None identified. Chrome/Firefox profiles are the model.
- Recommendation: Proceed

### Demand search
- Work items: None found (hits for "profile" are unrelated).
- Proposals: None found. Related context: PROP-LRH-CONSOLE-LOCAL-DOGFOOD.
- Backlog: No matching entries checked beyond a text search.
- Recommendation: No action

## Design Decisions

### Decision 1: Where a profile sits in resolution

Options: above local discovery; replace only the global (XDG) tier; replace
everything. **Chosen: a profile replaces only the global tier** (resolution
step 7). Placing it higher would make `lrh meta` inside a repo ignore that
repo's `.lrh/config.toml`. Because `serve` resolves from `cwd=project_root`,
local discovery would defeat the app's isolation, so the app additionally sets
`LRH_CONFIG` to the profile config (step 4).

### Decision 2: Isolation mechanism

Options: inject `XDG_*` into the child; LRH-resolved profile paths.
**Chosen: LRH-resolved paths.** `XDG_CONFIG_HOME` is also how `git` and `gh`
find global config, so injecting it would break them for the `serve` child.

### Decision 3: Shared resolver and layout

A new `lrh.meta.profiles` module: `resolve_profile(name, environ)` returns
config path, state dir, cache dir and templates dir. `default` returns today's
paths. Other profiles use `~/.config/lrh/profiles/<name>/config.toml`,
`~/.local/state/lrh/profiles/<name>/` and `~/.cache/lrh/profiles/<name>/`.
Config files keep explicit absolute dirs, as `_configured_path` already
supports. Names match `[a-z0-9][a-z0-9_-]{0,31}`; `default` is reserved.
The existing `environ` parameters on the init functions make
`lrh meta init --profile X` a small change.

### Decision 4: Selection surface

`LRH_PROFILE` and `--profile` on `lrh meta` and `lrh serve` only; bootstrap's
`--profile` is untouched. No persisted "active profile" in v1: one source of
truth, always explicit.

### Decision 5: Console app

`--profile` or `LRH_CONSOLE_PROFILE` selects
`app_config_dir()/profiles/<name>/config.json`. `launch_config`
(`settings.rs:190-214`) adds `LRH_PROFILE` and `LRH_CONFIG` to the child. The
webview store uses a deterministic `data_store_identifier` derived from the
name (macOS >= 14; Tauri 2.12 `webview_window.rs:1199`), and the profile name
appears in the window title. A second profile launches with
`open -n -a "LRH Console" --args --profile X` (no single-instance plugin,
`Cargo.toml:17-20`).

### Decision 6: New profiles start empty

Inheriting would silently copy a project registry pointing at real checkouts.
An explicit `--from <profile>` copy is optional (see Open Questions).

### Decision 7: Fix the Save hazard regardless

In env-override mode Save must not write the shared file. Independently
valuable and shippable first.

## Non-Goals

- Does not change bootstrap or chain-defaults "profile" behavior.
- Does not add a persisted active profile, an in-app profile picker, or
  `lrh profile list/create/use` commands in v1.
- Does not migrate existing config; `default` is unchanged.
- Does not isolate anything via global `XDG_*` overrides.

## Implementation Plan

Multi-PR; governed by workstream `WS-LRH-PROFILES`. Proposed order:

1. Fix `save_settings` in env-override mode (standalone).
2. `lrh.meta.profiles` resolver plus tests.
3. Wire the resolver into `resolve_meta_workspace`, `meta init`, `serve`, and
   the assist template resolver; update help text and release-smoke
   sanitising.
4. Console: per-profile app config dir, child env, window title, webview store.
5. Docs: how-to, plus the naming disambiguation.

## Open Questions

- Flag name: `--profile` or the more explicit `--meta-profile`?
- Are assist templates per-profile or shared (`template_resolver.py:210`)?
- Is `--from` copy in scope for v1?
- Should the Save-hazard fix ship as its own work item first?
- Does `_mode_for_config_path` infer the right mode for
  `profiles/<name>/config.toml`? Not traced.
- Does WKWebView actually isolate stores by `data_store_identifier`, and does
  `open -n` behave as expected? Both untested.

## Cross-References

- `docs/how-to/lrh-console-local-dogfood.md`
- `project/design/proposals/proposed/lrh-console-local-dogfood/00_proposal.md`
- `project/workstreams/active/WS-LRH-CONSOLE-LOCAL-DOGFOOD.md`
