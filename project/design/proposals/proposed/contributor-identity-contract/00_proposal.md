---
id: PROP-CONTRIBUTOR-IDENTITY-CONTRACT
type: design_proposal
title: Contributor Identity Contract — Stable Local id, GitHub Handle as Correlation Key
status: proposed
implementation_status: not_started
created_on: 2026-08-09
updated_on: 2026-08-09
related_design:
  - project/design/proposals/proposed/activity-lanes-and-observational-dashboard.md
implemented_by: []
evidence: []
supersedes: []
superseded_by: null
parent: null
---

# Contributor Identity Contract — Stable Local id, GitHub Handle as Correlation Key

## Summary

Formalize the contract LRH's contributor schema already implies but does not
enforce: `id` is a stable, repo-local identifier, and `github` is the external
handle used to correlate the same person or agent across repositories. Make
`github` load-bearing by validating it for human contributors, remediate the
repositories that omit it, and record explicitly that unifying `id` *values*
across repositories was considered and rejected as redundant.

## Background / Motivation

### The triggering observation, and why its premise was wrong

A session in the `prosocial` repository observed that LRH and LCATS had
diverged on contributor identity — LRH using `anthony`, LCATS using `xenotaur` —
and recommended standardizing on the GitHub handle, estimating roughly 150
references in LCATS.

Direct measurement contradicts that framing in three ways:

1. **The reference counts were inverted.** LCATS carries 180 contributor-id
   references (90 `owner:`, 90 list entries), all already `xenotaur`, so it needs
   zero changes to standardize on the GitHub handle. LRH carries 276 (140
   `owner:`, 135 list entries, 1 registry). LRH, not LCATS, would have absorbed
   the entire cost.
2. **The direction was backwards.** LRH's registry records `id: anthony` *and*
   `github: xenotaur` as distinct fields. LCATS's records `id: xenotaur` with
   `github:` empty. LCATS did not adopt a cleaner convention — it collapsed two
   fields into one and lost the explicit mapping.
3. **The unification it proposed is unnecessary.** The `github` field is the
   cross-repository correlation key. Once populated everywhere, tooling joins on
   it regardless of what each repository calls its local `id`.

This proposal records that analysis so the same conclusion is not re-derived
from the same wrong premise.

### Why a stable local id, separate from the GitHub handle

Three grounds, two of them observable in the repositories today:

- **The id space must accommodate actors with no GitHub account.** LRH's
  `project/contributors/agents/bootstrap-agent.md` is `type: agent` with `github`
  empty. Ids cannot universally be GitHub handles.
- **Agent ids and GitHub handles are genuinely different strings.** The
  `taurworks` registry is the clearest existing evidence: `id: github-copilot`
  maps to `github: copilot-pull-request-reviewer`; `id: jules` maps to
  `github: google-labs-jules`; `id: codex` maps to
  `github: chatgpt-codex-connector`. These are not cosmetic differences — they
  are the actual account names review tooling must match on, and no
  value-unification scheme could produce them.
- **This is the standard identity-modeling pattern.** RFC 7643 (SCIM Core
  Schema) §3.1 separates `id`, "a unique identifier for a SCIM resource as
  defined by the service provider," from `externalId`, an identifier "as defined
  by the provisioning client." A stable local key with external identifiers as
  correlatable attributes is the conventional shape, and `id`/`github` is an
  instance of it.

### Measured state across the fleet

Surveying every repository under `~/Workspace` with an LRH `project/contributors`
directory found seven, in four distinct states:

| Repository | `id` | `type` | `github` | State |
|---|---|---|---|---|
| `logical_robotics_harness` | `anthony` | human | `xenotaur` | Conformant |
| `taurcode` | `anthony` | human | `xenotaur` | Conformant |
| `taurworks` | `xenotaur` | human | `xenotaur` | Conformant |
| `taurworks` (4 agents) | `claude`, `codex`, `github-copilot`, `jules` | agent | empty, `chatgpt-codex-connector`, `copilot-pull-request-reviewer`, `google-labs-jules` | Conformant |
| `LCATS` | `xenotaur` | human | **empty** | Missing correlation key |
| `LCATS` | `unassigned` | human | empty | Placeholder |
| `replication_vector` | `project maintainers` | human | empty | Malformed id, missing key |
| `velumin` | `project maintainers` | human | empty | Malformed id, missing key |
| `taurworks-safety` | `CONTRIBUTORS-INIT` | **missing** | empty | Stub, missing a required field |
| `prosocial` | — | — | — | **No registry**, with an `owner:` reference |

Two observations worth stating plainly. First, **LRH's pattern is already used by
two other repositories** (`taurcode` identically, `taurworks` with
`id == github` but explicitly populated), so it is the de facto convention, not
an LRH idiosyncrasy. Second, **`taurworks-safety` is missing `type`, which is
already in `CONTRIBUTOR_REQUIRED_FIELDS`** — meaning that registry either fails
`lrh validate` today or is never validated. Registries are drifting unchecked.

### Why the field is not currently load-bearing

`Contributor.github` is declared at `src/lrh/control/models.py:114`, but it has
**no consumer** anywhere in `src/lrh/`, and `github` does not appear in
`src/lrh/control/validator.py` at all —
`CONTRIBUTOR_REQUIRED_FIELDS` is `{"id", "type", "roles", "display_name",
"status"}` (`validator.py:11`). The field is currently declarative intent.

This cuts both ways, honestly: it makes the field free to populate, but it also
means "LRH is more correct" is a claim about design intent rather than enforced
architecture. Making the field load-bearing is what converts intent into a
guarantee, and is therefore part of this proposal rather than a follow-up.

## Prior Art Check

### Duplication search

- **In-repo:** No existing proposal, work item, or workstream addresses
  contributor identity. One keyword match
  (`src/lrh/skills/lrh-work-item/references/work-item-schema.md`) documents the
  `owner:` field's contributor reference but does not address the `id`/`github`
  relationship.
- **Sibling repos:** The `taurworks` registry is prior *art* rather than
  duplication — it demonstrates the target pattern, including agent handle
  mappings, and should be cited as the reference example rather than re-derived.
- **External libraries:** Not applicable; this is schema and convention, not a
  library-shaped problem. RFC 7643 supplies the pattern, not an implementation.
- **Recommendation:** Proceed.

### Demand search

- **Work items:** None found requesting this.
- **Proposals:** None requesting it.
  `PROP-ACTIVITY-LANES-AND-OBSERVATIONAL-DASHBOARD` is adjacent: it lists
  "cross-repo centralized service requirements" as out of MVP
  (`activity-lanes-and-observational-dashboard.md:231`), which is why no
  functional need for cross-repository correlation exists *today* — but it is
  the consumer that would eventually need this key.
- **Backlog:** No matching entries.
- **Recommendation:** No action. Cross-link the dashboard proposal as the
  eventual consumer.

## Design Decisions

### Decision 1: `id` is repo-local and stable; `github` is the correlation key

Options considered:

- Treat the GitHub handle as the canonical contributor id everywhere.
- Keep `id` as a stable local identifier and treat `github` as an external
  correlation attribute.

**Chosen: stable local `id`, `github` as correlation key.** The GitHub handle is
mutable (accounts can be renamed), absent for some actors (`bootstrap-agent`),
and genuinely different from the natural id for agents
(`github-copilot` → `copilot-pull-request-reviewer`). Binding the primary key to
a mutable external identifier would make every handle change a repository-wide
rename.

`id` values remain repo-local by design. Two repositories may legitimately use
different ids for the same person; `github` is what makes them the same person to
any tool that needs to know.

### Decision 2: id-value unification across repositories is rejected as redundant

Options considered:

- Rename LRH's `anthony` → `xenotaur` (276 references) so all repositories read
  identically.
- Rename LCATS/PROSOC's `xenotaur` → `anthony` (190 references) to match LRH.
- Populate `github` everywhere and leave `id` values repo-local.

**Chosen: populate `github`; do not unify id values.** Once every registry
carries the correlation key, unification delivers visual uniformity only — the
functional problem it would solve is already solved by the field that exists for
that purpose.

Recorded explicitly because this is the conclusion a future session is most
likely to re-litigate: a reader noticing `anthony` in one repository and
`xenotaur` in another will reasonably read it as drift. It is not drift; it is
the intended shape, and the correlation key is where consistency belongs.

For the record, the rejected options are *safe*, merely unnecessary. An earlier
draft of this analysis characterized renaming in LCATS as dangerous because of
its 8,506 `github.com/xenotaur` URLs; that overstated the risk, since anchored
patterns (`^owner: `, `^  - `) never match a URL and `owner:` is validated
(`validator.py:1371-1403`), so an incomplete rename fails loudly. The real
argument against it is reviewability: LCATS carries roughly 250 additional
look-alike non-id uses — `repos/xenotaur/LCATS` API paths, `xenotaur/feat/...`
branch names, a `xenotaur/gutenbergpy` fork — that a reviewer would have to
distinguish by eye, for no functional gain.

### Decision 3: `github` becomes required for human contributors, optional for agents

Options considered:

- Leave `github` optional and rely on convention.
- Require `github` for every contributor.
- Require `github` for `type: human`; keep it optional for `type: agent`.

**Chosen: required for humans, optional for agents.** The fleet survey shows why
the split matters: three of four `taurworks` agents have meaningful GitHub app
handles, but `claude` legitimately has none. Requiring it universally would force
a fabricated value; leaving it universally optional is what allowed LCATS to lose
it silently.

Adding `github` to a required-fields set for humans is the change that converts
this proposal from convention into contract. Validation is what makes the
correlation key trustworthy enough for the dashboard proposal to build on later.

### Decision 4: Remediate non-conformant registries, including the missing one

The survey found four distinct defects, remediated as follows:

- **Missing `github`** (`LCATS`) — populate `github: xenotaur`.
- **No registry at all** (`prosocial`) — create one; it currently has an
  `owner:` reference pointing at an undefined contributor.
- **Missing required `type`** (`taurworks-safety`) — a pre-existing validation
  failure surfaced by this survey, fixed opportunistically.
- **Malformed ids** (`replication_vector`, `velumin`, both `project maintainers`)
  — see Decision 5.

### Decision 5: Constrain the `id` format

Options considered:

- Leave `id` unconstrained.
- Require a slug-shaped id (lowercase, no spaces).

**Chosen: require a slug-shaped id.** Two repositories use
`id: project maintainers`, with a space. An id is referenced from `owner:` and
`contributors:` fields in YAML frontmatter, where an unquoted value containing a
space is fragile, and it is a poor key for any future join. This is scoped
narrowly — a format rule, not a renaming of anyone's id beyond the two malformed
cases.

Flagged as the most arguable decision here: it slightly widens scope beyond the
`id`/`github` contract proper, and could reasonably be split into its own work
item if review prefers.

## Non-Goals

- **Does not unify `id` values across repositories.** See Decision 2; this is
  the explicit non-goal the proposal exists partly to record.
- **Does not rename any conformant contributor id.** LRH's `anthony`, LCATS's
  `xenotaur`, and `taurworks`'s agent ids all stay as they are.
- **Does not build cross-repository tooling.** This establishes the correlation
  key; consuming it is `PROP-ACTIVITY-LANES-AND-OBSERVATIONAL-DASHBOARD`'s
  scope, which currently lists cross-repo service requirements as out of MVP.
- **Does not add a consumer for `github` beyond validation.** Making the field
  required is deliberately the minimum that makes it trustworthy.
- **Does not modify execution records** that mention contributor ids in
  narrative text; those are immutable historical accounts.
- **Does not change `owner:` or `contributors:` semantics** in work items,
  workstreams, or proposals.

## Implementation Plan

Sequenced so the LRH-side contract lands before the repositories that must
conform to it.

1. **Document the contract** in the contributor schema reference: `id` is
   repo-local and stable, slug-shaped; `github` is the external correlation key,
   required for humans.
2. **Add validator enforcement** — `github` required for `type: human`, and an
   id-format check. Both need unit tests, per this project's requirement that
   new Python carry tests.
3. **Fix LRH's own registry if needed** and confirm `lrh validate` stays clean.
4. **Remediate the other repositories** — one small PR each, per Decision 4.
   These are independent and can proceed in parallel once step 2 ships.

**Sequencing against other work.** This is cosmetic-adjacent and non-urgent:
nothing consumes `github` today, so nothing is functionally broken. It should
land in a quiet window rather than competing with in-flight work — the same
reasoning applied to any low-urgency, wide-surface change. Steps 1–3 are
confined to LRH and are small; step 4 crosses repository boundaries and is
carried out per-repo by hand, since LRH's planning artifacts govern only this
repository.

## Open Questions

1. **Decision 5's scope** — keep the id-format rule here, or split it into its
   own work item? It is adjacent to the `id`/`github` contract rather than part
   of it.
2. **`replication_vector` and `velumin` ids** — `project maintainers` appears to
   be a placeholder rather than a real contributor. Should these become
   `xenotaur`, a properly-slugged `project-maintainers`, or be removed in favor
   of a real registry?
3. **`taurworks-safety`'s `CONTRIBUTORS-INIT` stub** — is that repository
   actively validated, or is the stub intentional scaffolding? Determines
   whether the missing `type` is a bug or a known placeholder.
4. **Backfill scope** — should existing `owner:`/`contributors:` references be
   audited for ids absent from their registry (as `prosocial`'s single `owner:`
   reference currently is), or is fixing the registries sufficient?

## Cross-references

- `src/lrh/control/models.py:114` — `Contributor.github`, declared and
  currently unconsumed.
- `src/lrh/control/validator.py:11` — `CONTRIBUTOR_REQUIRED_FIELDS`, the set
  Decision 3 extends.
- `src/lrh/control/validator.py:1371-1403` — `owner:` cross-validation against
  contributor ids, the safety net that makes any id change atomic.
- `project/design/proposals/proposed/activity-lanes-and-observational-dashboard.md:231`
  — cross-repo requirements out of MVP; the eventual consumer of the
  correlation key.
- RFC 7643 (SCIM Core Schema) §3.1 — the `id` / `externalId` pattern this
  contract instantiates.
