"""Approval guardrail checks."""

from lrh.guardrails import models


class ApprovalGuardrail:
    """Minimal approval guardrail evaluator."""

    def requires_approval(self, proposal: models.ActionProposal) -> bool:
        """Return whether the proposal requires explicit approval."""
        del proposal
        return False
