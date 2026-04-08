"""Safety guardrail checks."""

from .models import ActionProposal


class SafetyGuardrail:
    """Minimal safety guardrail evaluator."""

    def evaluate(self, proposal: ActionProposal) -> list[str]:
        """Return safety warnings for a proposal."""
        del proposal
        return []
