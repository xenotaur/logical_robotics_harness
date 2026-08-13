# Assistant Policy Token Vocabulary

This file is the **authoritative catalog** of the namespaced string tokens an
assistant package may use in its `policy.md`, `preferences.md`,
`communication-policy.md`, and workstream binding. Per Decision 9 of
[`PROP-LRH-ASSISTANTS`](../design/proposals/adopted/lrh-assistants/00_proposal.md),
the vocabulary ships with the convention so that a token is never silently
mistyped or invented. This is the **markdown** source of truth; the Python
validating catalog that enforces it arrives in Stage 3.

Tokens are flat `namespace:verb` (or `namespace:noun`) strings, chosen because
the LRH frontmatter parser rejects nested mappings. A token that is not listed
here is invalid — **except** for the explicitly soft, extensible preference
lists called out under [Preference tokens](#preference-tokens)
(`preferred_skills`, `preferred_execution`, `preferred_quality_tradeoffs`),
which are ordered advisory guidance rather than a closed catalog.

## `capabilities` / `permission_ceiling` tokens

What a role knows how to do (`capabilities`) and the maximum that may ever be
granted (`permission_ceiling`). The active grant is a subset, supplied by the
workstream binding's `assistant_contract`.

| Token | Meaning |
|---|---|
| `planning:assess` | Assess a workstream or work item |
| `planning:propose_design` | Draft or propose a design |
| `planning:create_child_workstream` | Create a child planning node |
| `planning:create_work_item` | Create a work item |
| `execution:prepare_run_packet` | Prepare an authorized run attempt |
| `execution:launch_approved_run` | Launch a run that is already approved |
| `execution:monitor` | Observe run state and events |
| `review:triage` | Triage review comments |
| `review:fix_mechanical` | Apply deterministic, semantics-preserving fixes |
| `review:fix_within_scope` | Apply in-scope fixes that preserve the design |
| `review:edit_agent_branch` | Edit the agent's working branch |
| `reporting:progress` | Report progress to the human |
| `reporting:decision_request` | Request a human decision |
| `memory:propose` | Propose (never accept) a memory item |

## `permission_ceiling`-only artifact/run tokens

Coarser authorities that may appear in a ceiling and be granted by a binding:

| Token | Meaning |
|---|---|
| `artifact:create:design_proposal` | May create a design-proposal artifact |
| `artifact:create:workstream` | May create a workstream artifact |
| `artifact:create:work_item` | May create a work-item artifact |
| `run:prepare` | May prepare a run leaf |
| `run:launch_approved` | May launch an approved run |
| `run:observe` | May observe a run |
| `skill:invoke:<skill-name>` | May invoke the named LRH skill |
| `delegate:cold_verifier` | May delegate independent verification to a cold context |

## `obligations` tokens

Requirements the role must satisfy; accumulate across layers (never removed by a
narrower layer):

| Token | Meaning |
|---|---|
| `validation:canonical` | Run the canonical validation sequence |
| `evidence:report` | Report evidence for truth claims |
| `review:use_live_diff` | Verify against the live diff, not prior claims |
| `review:independent_verification_after_self_authored_fixes` | Independently verify self-authored fixes |
| `merge:human` | Merge remains a human action |
| `closeout:human` | Closeout remains a human action |

## `prohibitions` tokens

Hard denials; a narrower layer may add but never remove them:

| Token | Meaning |
|---|---|
| `repo:merge` | May not merge |
| `repo:force_push` | May not force-push |
| `release:publish` | May not publish a release |
| `secrets:read` | May not read secrets |
| `scope:expand_unilaterally` | May not expand its own scope |
| `design:change_unilaterally` | May not change approved design alone |
| `acceptance:change` | May not change acceptance criteria |
| `assistant:modify_own_policy` | May not modify its own policy |
| `assistant:self_promote_memory` | May not accept its own memory |
| `review:approve_own_work` | May not approve its own work |

## `mandatory_escalations` / escalation-trigger tokens

Conditions that must be surfaced to the human; used in `mandatory_escalations`,
`assistant_escalates_on`, and `immediate_report_triggers`:

`security`, `privacy`, `permissions`, `design_change`, `schema_change`,
`public_api_change`, `scope_expansion`, `scope_change`, `acceptance_change`,
`ambiguous_requirement`, `conflicting_review`, `evidence_conflict`,
`iteration_limit`, `blocker`, `approval_required`, `completion_candidate`,
`milestone`.

## Communication tokens

- **`message_intents`**: `inform`, `request`, `direct`, `respond`,
  `acknowledge`.
- **`message_topics`**: `progress`, `completion`, `blocker`, `decision`,
  `scope`, `risk`, `review`, `handoff`, `control`.
- **`message_urgencies`**: `routine`, `elevated`, `urgent`, `critical`.

## Review-outcome tokens

Used by `review-policy.md`:

`fix_mechanical`, `fix_within_scope`, `surface_for_decision`,
`reject_with_rationale`.

## Preference tokens

Used by `preferences.md`. The **namespaced** preference tokens below are part of
the closed catalog. The other preference lists — `preferred_skills` (LRH skill
IDs), `preferred_execution`, and `preferred_quality_tradeoffs` — are ordered
**soft guidance**: advisory, intentionally extensible, and *not* governed as a
closed token set.

`preferred_context_modes`:

| Token | Meaning |
|---|---|
| `verification:cold` | Verify in a cold, isolated context |
| `implementation:continuity` | Implement with conversational continuity |
| `broad_research:isolated` | Do broad research in an isolated context |

`fallbacks` (`condition:action`):

| Token | Meaning |
|---|---|
| `cold_verifier_unavailable:require_human_verification` | If no cold verifier is available, require human verification |
| `preferred_skill_unavailable:render_manual_packet` | If the preferred skill is unavailable, render a manual packet |
| `backend_policy_unsupported:stop_and_report` | If the backend cannot enforce a hard policy, stop and report |

## Adapter policy-report tokens

How a backend adapter must report each hard policy:

`enforced`, `prompt_enforced_only`, `unsupported`, `requires_human_gate`.

---

**Maintenance.** New tokens are added here first (with a one-line meaning),
then referenced by packages. When Stage 3 lands, this table becomes the fixture
the Python catalog is checked against; drift between the two is a validation
error.
