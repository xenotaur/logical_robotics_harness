import importlib
import sys
import unittest
from pathlib import Path


def _import_guardrail_modules() -> tuple[object, object]:
    project_src = Path(__file__).resolve().parents[1] / "src"
    if str(project_src) not in sys.path:
        sys.path.insert(0, str(project_src))

    engine_module = importlib.import_module("lrh.guardrails.engine")
    models_module = importlib.import_module("lrh.guardrails.models")
    return engine_module, models_module


engine_module, models = _import_guardrail_modules()


class _FakeSafetyGuardrail:
    def __init__(self, warnings: list[str]) -> None:
        self._warnings = warnings

    def evaluate(self, proposal: models.ActionProposal) -> list[str]:
        del proposal
        return self._warnings


class _FakeCostGuardrail:
    def __init__(self, warnings: list[str]) -> None:
        self._warnings = warnings

    def evaluate(self, proposal: models.ActionProposal) -> list[str]:
        del proposal
        return self._warnings


class _FakeOpticsGuardrail:
    def __init__(self, warnings: list[str]) -> None:
        self._warnings = warnings

    def evaluate(self, proposal: models.ActionProposal) -> list[str]:
        del proposal
        return self._warnings


class _FakeApprovalGuardrail:
    def __init__(self, required: bool) -> None:
        self._required = required

    def requires_approval(self, proposal: models.ActionProposal) -> bool:
        del proposal
        return self._required


class TestGuardrailEngine(unittest.TestCase):
    def _make_proposal(self) -> models.ActionProposal:
        return models.ActionProposal(
            action_id="action-123",
            work_item_id="work-item-456",
            title="Test Proposal",
            description="A proposal used for guardrail tests.",
            proposed_by="test-author",
        )

    def test_assess_returns_consequence_assessment(self) -> None:
        proposal = self._make_proposal()
        engine = engine_module.GuardrailEngine(
            safety=_FakeSafetyGuardrail([]),
            cost=_FakeCostGuardrail([]),
            optics=_FakeOpticsGuardrail([]),
            approvals=_FakeApprovalGuardrail(False),
        )

        assessment = engine.assess(proposal)

        self.assertIsInstance(assessment, models.ConsequenceAssessment)

    def test_assess_propagates_action_id(self) -> None:
        proposal = self._make_proposal()
        engine = engine_module.GuardrailEngine(
            safety=_FakeSafetyGuardrail([]),
            cost=_FakeCostGuardrail([]),
            optics=_FakeOpticsGuardrail([]),
            approvals=_FakeApprovalGuardrail(False),
        )

        assessment = engine.assess(proposal)

        self.assertEqual(assessment.action_id, proposal.action_id)

    def test_assess_blocks_when_safety_has_warnings(self) -> None:
        proposal = self._make_proposal()
        engine = engine_module.GuardrailEngine(
            safety=_FakeSafetyGuardrail(["safety warning"]),
            cost=_FakeCostGuardrail([]),
            optics=_FakeOpticsGuardrail([]),
            approvals=_FakeApprovalGuardrail(False),
        )

        assessment = engine.assess(proposal)

        self.assertTrue(assessment.blocked)

    def test_assess_not_blocked_when_safety_has_no_warnings(self) -> None:
        proposal = self._make_proposal()
        engine = engine_module.GuardrailEngine(
            safety=_FakeSafetyGuardrail([]),
            cost=_FakeCostGuardrail([]),
            optics=_FakeOpticsGuardrail([]),
            approvals=_FakeApprovalGuardrail(False),
        )

        assessment = engine.assess(proposal)

        self.assertFalse(assessment.blocked)

    def test_assess_propagates_cost_warnings(self) -> None:
        proposal = self._make_proposal()
        cost_warnings = ["cost warning 1", "cost warning 2"]
        engine = engine_module.GuardrailEngine(
            safety=_FakeSafetyGuardrail([]),
            cost=_FakeCostGuardrail(cost_warnings),
            optics=_FakeOpticsGuardrail([]),
            approvals=_FakeApprovalGuardrail(False),
        )

        assessment = engine.assess(proposal)

        self.assertEqual(assessment.cost_warnings, cost_warnings)

    def test_assess_propagates_optics_warnings(self) -> None:
        proposal = self._make_proposal()
        optics_warnings = ["optics warning"]
        engine = engine_module.GuardrailEngine(
            safety=_FakeSafetyGuardrail([]),
            cost=_FakeCostGuardrail([]),
            optics=_FakeOpticsGuardrail(optics_warnings),
            approvals=_FakeApprovalGuardrail(False),
        )

        assessment = engine.assess(proposal)

        self.assertEqual(assessment.optics_warnings, optics_warnings)

    def test_assess_propagates_approval_requirement(self) -> None:
        proposal = self._make_proposal()
        engine = engine_module.GuardrailEngine(
            safety=_FakeSafetyGuardrail([]),
            cost=_FakeCostGuardrail([]),
            optics=_FakeOpticsGuardrail([]),
            approvals=_FakeApprovalGuardrail(True),
        )

        assessment = engine.assess(proposal)

        self.assertTrue(assessment.approval_required)

    def test_engine_constructs_with_default_guardrails(self) -> None:
        proposal = self._make_proposal()
        engine = engine_module.GuardrailEngine()

        assessment = engine.assess(proposal)

        self.assertIsInstance(assessment, models.ConsequenceAssessment)
        self.assertFalse(assessment.blocked)
        self.assertEqual(assessment.safety_warnings, [])
        self.assertEqual(assessment.cost_warnings, [])
        self.assertEqual(assessment.optics_warnings, [])
        self.assertFalse(assessment.approval_required)


if __name__ == "__main__":
    unittest.main()
