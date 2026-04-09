"""Optics guardrail checks."""

from lrh.guardrails import models


class OpticsGuardrail:
    """Minimal optics guardrail evaluator."""

    def evaluate(self, proposal: models.ActionProposal) -> list[str]:
        """Return optics warnings for a proposal."""
        del proposal
        return []
