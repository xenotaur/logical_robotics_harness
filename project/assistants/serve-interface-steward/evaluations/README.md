# Serve Interface Steward — Evaluations

Evaluation material for this assistant role. Evaluations let the same role be
compared across instantiations (manual, Claude, Codex, another backend) and
guard the invariants the role must uphold.

Per the proposal's evaluation strategy, evaluations fall into families:

- **Structural** — the package loads; missing companion files, path escapes,
  duplicate IDs, invalid tokens, invalid bindings, and self-promoted memory all
  fail. (Enforced once Stage 3 validation exists.)
- **Policy** — a mechanical lint fix is allowed; a security finding escalates; a
  design-changing review escalates; an out-of-scope edit is denied; no run
  packet means no mutation; the assistant cannot approve its own work.
- **Context** — orientation includes stable role information only; the current
  view reflects planning state; the changes view reports incomplete event
  coverage honestly.
- **Communication** — a blocker triggers an immediate report; routine progress
  respects cadence; acknowledgment is not treated as approval; completion
  renders as a candidate pending verification.
- **Behavioral** — compare instantiations on planning quality, decomposition,
  scope discipline, escalation precision/recall, review classification,
  evidence quality, human-supervision burden, and consistency across backends.

`EVAL-EXAMPLE-PLANNING-QUALITY.md` is a worked example of a behavioral
evaluation. These are documentation today; the executable fixtures arrive in
Stage 7.
