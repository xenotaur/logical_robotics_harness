"""Cost guardrail checks."""

from .models import ActionProposal


class CostGuardrail:
    """Minimal cost guardrail evaluator."""

    def evaluate(self, proposal: ActionProposal) -> list[str]:
        """Return cost warnings for a proposal."""
        del proposal
        return []
