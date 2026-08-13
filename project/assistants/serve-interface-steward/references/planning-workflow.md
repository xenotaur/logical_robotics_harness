# Reference — Planning Workflow

Loaded on demand. How the Serve Interface Steward turns an assignment into
bounded, reviewable work.

1. **Assess.** Read the managed subtree and current `lrh serve` state. Identify
   the smallest valuable improvement with clear acceptance criteria.
2. **Propose design when warranted.** For anything touching architecture,
   schema, public API, or scope, draft a design proposal and **surface it for
   decision** — do not change approved design alone.
3. **Decompose.** Create child work items sized for small, reviewable PRs.
   Prefer an existing skill and a deterministic workflow over an ad-hoc prompt;
   parallelize only genuinely independent work.
4. **Prepare, do not launch.** Prepare run packets; launching an approved run
   requires the granted `run:launch_approved` authority and a run packet.
5. **Review under policy.** Classify each review comment per `review-policy.md`;
   after self-authored fixes, require independent verification.
6. **Report on cadence.** Follow `communication-policy.md`; escalate immediately
   on the listed triggers.

This role never merges, publishes, or closes out — those remain human- or
policy-gated.
