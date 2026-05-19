---
execution_id: 2026_05_19_19_05_02_META_SERVE_LOCAL_STATE_DESIGN_ALIGNMENT
prompt_id: PROMPT(AD_HOC:META_SERVE_LOCAL_STATE_DESIGN_ALIGNMENT)[2026-05-19T13:45:00-04:00]
work_item: AD_HOC
status: planned
rerun_of:
pr:
commit: 8112bcc
created_at: 2026-05-19T19:05:02+00:00
---

# Summary

Aligned LRH design/control-plane artifacts to define the meta local-state model required for serve operational triage: portable identity (`repo_locator`), optional local checkout binding (`local_repo_path`), relative `project_dir`, derived local resolution, last-observed check semantics, private-by-default local-state policy, trusted persistence opt-in, command responsibility split, and a staged PR1-PR7 implementation sequence.

# Result

Updated the meta control-plane MVP spec, the serve operational triage proposal, and current focus notes to make the register/refresh vs serve trust boundary explicit and to stage follow-on implementation without introducing behavior changes in this PR.

# Validation

- scripts/version tools
- scripts/test
- scripts/lint
- scripts/format --check
- lrh validate

# Follow-up

- PR1: implement typed identity/checkout/project/observation model and storage policy.
- PR2-PR7: implement config, refresh, typed field updates, setup-state visibility, and serve-state consumption sequence.
