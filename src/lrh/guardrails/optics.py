"""Optics guardrail checks."""

from .models import ActionProposal


class OpticsGuardrail:
    """Minimal optics guardrail evaluator."""

    def evaluate(self, proposal: ActionProposal) -> list[str]:
        """Return optics warnings for a proposal."""
        del proposal
        return []
