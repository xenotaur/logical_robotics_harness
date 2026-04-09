"""Minimal guardrail review engine."""

from lrh.guardrails import approvals as approvals_module
from lrh.guardrails import cost as cost_module
from lrh.guardrails import models
from lrh.guardrails import optics as optics_module
from lrh.guardrails import safety as safety_module


class GuardrailEngine:
    """Runs guardrail checks for an action proposal."""

    def __init__(
        self,
        safety: safety_module.SafetyGuardrail | None = None,
        cost: cost_module.CostGuardrail | None = None,
        optics: optics_module.OpticsGuardrail | None = None,
        approvals: approvals_module.ApprovalGuardrail | None = None,
    ) -> None:
        self.safety = safety or safety_module.SafetyGuardrail()
        self.cost = cost or cost_module.CostGuardrail()
        self.optics = optics or optics_module.OpticsGuardrail()
        self.approvals = approvals or approvals_module.ApprovalGuardrail()

    def assess(self, proposal: models.ActionProposal) -> models.ConsequenceAssessment:
        """Return a consolidated consequence assessment for a proposal."""
        safety_warnings = self.safety.evaluate(proposal)
        cost_warnings = self.cost.evaluate(proposal)
        optics_warnings = self.optics.evaluate(proposal)
        approval_required = self.approvals.requires_approval(proposal)

        blocked = bool(safety_warnings)

        return models.ConsequenceAssessment(
            action_id=proposal.action_id,
            safety_warnings=safety_warnings,
            cost_warnings=cost_warnings,
            optics_warnings=optics_warnings,
            approval_required=approval_required,
            blocked=blocked,
        )
