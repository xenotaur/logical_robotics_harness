"""Minimal guardrail review engine."""

from .approvals import ApprovalGuardrail
from .cost import CostGuardrail
from .models import ActionProposal, ConsequenceAssessment
from .optics import OpticsGuardrail
from .safety import SafetyGuardrail


class GuardrailEngine:
    """Runs guardrail checks for an action proposal."""

    def __init__(
        self,
        safety: SafetyGuardrail | None = None,
        cost: CostGuardrail | None = None,
        optics: OpticsGuardrail | None = None,
        approvals: ApprovalGuardrail | None = None,
    ) -> None:
        self.safety = safety or SafetyGuardrail()
        self.cost = cost or CostGuardrail()
        self.optics = optics or OpticsGuardrail()
        self.approvals = approvals or ApprovalGuardrail()

    def assess(self, proposal: ActionProposal) -> ConsequenceAssessment:
        """Return a consolidated consequence assessment for a proposal."""
        safety_warnings = self.safety.evaluate(proposal)
        cost_warnings = self.cost.evaluate(proposal)
        optics_warnings = self.optics.evaluate(proposal)
        approval_required = self.approvals.requires_approval(proposal)

        blocked = bool(safety_warnings)

        return ConsequenceAssessment(
            action_id=proposal.action_id,
            safety_warnings=safety_warnings,
            cost_warnings=cost_warnings,
            optics_warnings=optics_warnings,
            approval_required=approval_required,
            blocked=blocked,
        )
