# Prior Art Check — Procedure

<!-- CANONICAL SOURCE: src/lrh/skills/_shared/prior-art-check.md
     Per-skill copies live at references/prior-art-check.md in each
     consuming skill. If you edit this file, update all copies.
     See project/design/backlog.md for the deferred automated drift-check. -->

This procedure is required before any LRH skill commits a new design,
planning artifact, or implementation. It has two complementary sub-searches
with different verdicts and recommended actions.

---

## Sub-search 1 — Duplication search

**Question:** Does something like this already exist?

**Purpose:** Catch work that would duplicate an existing implementation.
Finding a duplicate is a potential **blocker** — stop and assess whether the
new work is needed or should instead extend/replace what exists.

**Search locations (in order):**

1. **In-repo:** grep `src/`, `project/design/proposals/`, and
   `.claude/skills/` for terms derived from the topic title/summary.
   Suppress errors for absent paths (some are optional in client repos).

   ```bash
   grep -rl "<key-term>" src/ project/design/proposals/ .claude/skills/ 2>/dev/null
   ```

2. **Sibling repos:** ask the user: "Are there sibling repositories that
   might already implement this capability?" If named, note them for manual
   inspection. If none named, record "no sibling repos identified."

3. **External libraries:** ask the model: "Is there a well-known library or
   service that already provides this capability?" If yes, assess whether
   adopting it is preferable to building. If no obvious match, record
   "no external library identified."

**Verdict format:**

```
### Duplication search
- In-repo: <No existing implementation found | Related: <path>>
- Sibling repos: <None identified | See: <repo/path>>
- External libraries: <None identified | Consider: <library name>>
- Recommendation: <Proceed | Block — extend existing <path> instead | Block — adopt <library> instead>
```

---

## Sub-search 2 — Demand search

**Question:** Is something like this already requested?

**Purpose:** Catch existing work items, proposals, or backlog entries that
are asking for what is about to be built. Finding a match is a potential
**closeout opportunity** — the current implementation may satisfy an open
request, allowing it to be closed or linked. This is not a blocker.

**Search locations:**

1. **Work items:** search `project/work_items/` for proposed items with
   overlapping titles or summaries.

   ```bash
   grep -rl "<key-term>" project/work_items/proposed/ 2>/dev/null
   ```

2. **Design proposals:** search `project/design/proposals/proposed/` for
   proposals asking for the same capability.

   ```bash
   grep -rl "<key-term>" project/design/proposals/proposed/ 2>/dev/null
   ```

3. **Backlog:** check `project/design/backlog.md` for entries matching the
   topic.

**Verdict format:**

```
### Demand search
- Work items: <None found | Found: WI-<ID> — "<title>" (may be satisfied)>
- Proposals: <None found | Found: PROP-<ID> — "<title>" (may be satisfied)>
- Backlog: <No matching entries | Found: <entry title> (may be satisfied)>
- Recommendation: <No action | Offer to close/link: <IDs>>
```

---

## Recording the verdict

Write both verdicts into the artifact being created or updated:

- **`/lrh-design`:** as a required sub-section at the end of Step 3a,
  before Step 3b (best practices review).
- **`/lrh-proposal`:** as a `## Prior Art Check` body section between
  Background/Motivation and Design Decisions.
- **`/lrh-workstream`:** as a `## Prior Art Check` body section between
  Scope and Work Items.
- **`/lrh-work-item`:** in the `## Problem / Context` body section,
  appended after the motivating context.
- **`/lrh-implement`:** in the execution record's Result section if a
  demand match is found and actioned.

## Escalation

- **Duplication found:** stop and present the finding to the user before
  proceeding. Do not implement or propose a design that knowingly duplicates
  existing work without explicit user approval.
- **Demand match found:** present as an offer at the end of the skill run
  (do not auto-close). The user decides whether to close/link the matched
  item. Re-state the offer in the final report so it is not buried.
