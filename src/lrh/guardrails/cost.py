"""Cost guardrail checks."""

from lrh.guardrails import models


class CostGuardrail:
    """Minimal cost guardrail evaluator."""

    def evaluate(self, proposal: models.ActionProposal) -> list[str]:
        """Return cost warnings for a proposal."""
        del proposal
        return []
