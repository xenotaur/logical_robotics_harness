# Findings — cross-agent writes to Claude's memory store

Discovered 2026-08-17 while preparing the memory migration in `plan.md`. This
is **independent of the repository relocation** and is recorded here so the
rescue is not confused with it.

## What was observed

Codex writes memory files into Claude Code's memory area
(`~/.claude/projects/<project-slug>/memory/`), in a different format, without
maintaining the index Claude actually loads.

The trigger was Codex's own narration during an LCATS closeout:

> I found the Claude memory area, but this Codex GenrePilot path does not
> appear to have an existing memory folder yet. […] I'm adding only the
> relocated-worktree closeout note and a minimal `MEMORY.md` pointer because
> this project memory folder has memory files but no index yet.

That claim was wrong on the facts: `…Workspace-LCATS-LCATS/memory/MEMORY.md`
existed with 129 lines. It was **not** overwritten — verified byte-identical
against a snapshot taken ten minutes earlier — so no data was lost. But the
file Codex did write,
`feedback_genrepilot_closeout_writes_need_escalation.md` (2026-08-17 20:37),
has no frontmatter and **zero references in `MEMORY.md`**.

## Scope

Scanned all 461 memory files under `~/.claude/projects/*/memory/`, treating
"missing `---` frontmatter with a `name:` field" as the detector.

| Bucket | Non-conforming | Range |
| :--- | ---: | :--- |
| `…Workspace-LCATS-LCATS` | 8 | Aug 12 – Aug 17 |
| `…Workspace-Velumin-velumin` | 5 | Aug 3 – Aug 7 |
| `…Workspace-…-Codex-ReviewPreference-…` | 3 | Aug 17 |
| `…Workspace-…-logical-robotics-harness` | 2 | Aug 6 |
| `…Workspace-ReplicationVector-replication_vector` | 1 | Aug 3 |
| **Total** | **19 of 461** | |

## This predates the repository move

The relocation happened 2026-08-17 15:43. Non-conforming writes start
**2026-08-03**, two weeks earlier.

The benign alternative — "the memory format changed over time, and these are
just old files" — is ruled out by interleaving. Conforming and non-conforming
files were written on the *same days*:

| Day | Conforming | Non-conforming |
| :--- | ---: | ---: |
| Aug 3 | 5 | 4 |
| Aug 6 | 8 | 2 |
| Aug 7 | 15 | 2 |
| Aug 12 | 5 | 2 |
| Aug 13 | 25 | 5 |
| Aug 17 | 0 | 4 |

A format migration would show a clean cutoff. This shows two writers with two
conventions, concurrently. (Aug 17 has no conforming writes because Claude has
been memory-blind since 15:43 while Codex kept writing.)

## Defects

1. **No frontmatter.** Claude memories carry `name`, `description`, and
   `metadata.type`; `description` is what drives relevance during recall.
2. **Index not maintained.** Files written without a `MEMORY.md` entry are
   unreachable, so the memory is stored but never recalled.
3. **Index written to the wrong path.** In the Codex-ReviewPreference bucket,
   `MEMORY.md` sits at the *bucket root*; `memory/MEMORY.md` — the one loaded
   — is absent. All three files there are orphaned.
4. **Semantic contamination.** The new LCATS memory is Codex-specific sandbox
   guidance ("rerun the closeout write with explicit escalation"), stored where
   a *Claude* LCATS session would read it as guidance for itself. Nothing
   records which agent authored a memory or which agents it applies to.

## Attribution confidence

Solid for the recent files: the Aug 17 LCATS file matches Codex's own
narration verbatim, and the Aug 6 LRH pair are named `feedback_codex_*`. For
the Aug 3 Velumin files it is inference from naming (`codex-thread-id-…`), not
proof. The frontmatter detector finds *non-conforming* files, which is a proxy
for foreign authorship rather than direct evidence of it.

## Effect on the rescue

None on correctness. Migration is a byte-exact copy and is format-agnostic; it
neither improves nor worsens these files, and the unindexed ones were already
unreachable. Two operational consequences only:

- A snapshot taken before a Codex write goes stale. Re-snapshot immediately
  before migrating.
- Migration carries 8 non-conforming LCATS files and 2 LRH files forward,
  which is the correct behaviour: preserve everything, clean up separately.

## Proposed direction

An `lrh memory` command (or equivalent) that agents call instead of writing
files directly, so a malformed memory cannot be created in the first place:

- Validate frontmatter on write; reject or normalize what does not conform.
- Update `MEMORY.md` as part of the same operation, so an unindexed memory is
  not representable.
- Resolve the corpus path itself, removing the "wrong location" failure and
  the whole path-keyed class of problems this directory exists to clean up.
- Record `authored_by` (and optionally `applies_to`) so memories can be
  filtered by agent, addressing the contamination case.
- Offer a read path so an agent recalls without needing to know the layout.

This is a natural fit for LRH's existing role as the control plane over agent
session state, and it would make the failure mode structurally impossible
rather than merely detectable. Not designed here — see
`project/design/backlog.md`.
