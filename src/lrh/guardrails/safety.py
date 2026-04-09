"""Safety guardrail checks."""

from lrh.guardrails import models


class SafetyGuardrail:
    """Minimal safety guardrail evaluator."""

    def evaluate(self, proposal: models.ActionProposal) -> list[str]:
        """Return safety warnings for a proposal."""
        del proposal
        return []
