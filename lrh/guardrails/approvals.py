"""Approval guardrail checks."""

from .models import ActionProposal


class ApprovalGuardrail:
    """Minimal approval guardrail evaluator."""

    def requires_approval(self, proposal: ActionProposal) -> bool:
        """Return whether the proposal requires explicit approval."""
        del proposal
        return False
