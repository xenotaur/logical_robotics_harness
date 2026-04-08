"""Core action and guardrail model skeletons."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime


@dataclass(slots=True)
class ActionProposal:
    """A proposed execution action derived from a work item."""

    action_id: str
    work_item_id: str
    title: str
    description: str
    proposed_by: str
    proposed_at: datetime = field(default_factory=datetime.utcnow)
    expected_effects: list[str] = field(default_factory=list)


@dataclass(slots=True)
class ConsequenceAssessment:
    """A consolidated guardrail assessment for an action proposal."""

    action_id: str
    safety_warnings: list[str] = field(default_factory=list)
    cost_warnings: list[str] = field(default_factory=list)
    optics_warnings: list[str] = field(default_factory=list)
    approval_required: bool = False
    blocked: bool = False


@dataclass(slots=True)
class ActionDecision:
    """A minimal decision record for an action proposal after guardrail review."""

    action_id: str
    decision: str
    rationale: str
    decided_by: str
    decided_at: datetime = field(default_factory=datetime.utcnow)


@dataclass(slots=True)
class ApprovalRecord:
    """Tracks approval metadata for guardrail-governed actions."""

    action_id: str
    approver: str
    decision: str
    scope: str
    recorded_at: datetime = field(default_factory=datetime.utcnow)
    notes: str = ""
