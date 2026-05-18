"""Structured request-name catalog for assist request workflows."""

from __future__ import annotations

import dataclasses


@dataclasses.dataclass(frozen=True)
class RequestMetadata:
    """Metadata for one user-facing assist request."""

    canonical_name: str
    legacy_names: tuple[str, ...]
    category: str
    template_name: str
    description: str
    status: str = "canonical"
    implementation_target: str = "template"

    def all_names(self) -> tuple[str, ...]:
        """Return every supported invocation name for this request."""
        return (self.canonical_name, *self.legacy_names)


_REQUESTS: tuple[RequestMetadata, ...] = (
    RequestMetadata(
        canonical_name="ready-work-item",
        legacy_names=(),
        category="work-items",
        template_name="ready_work_item",
        description=("Render a non-mutating refinement request for a thin work item."),
        implementation_target="structured_ready_work_item",
    ),
    RequestMetadata(
        canonical_name="prompt-from-work-item",
        legacy_names=("codex-prompt-from-work-item", "codex_prompt_from_work_item"),
        category="work-items",
        template_name="codex_prompt_from_work_item",
        description="Generate a coding-assistant prompt from one LRH work item.",
        implementation_target="structured_work_item_prompt",
    ),
    RequestMetadata(
        canonical_name="run-packet-from-work-item",
        legacy_names=("run_packet_from_work_item",),
        category="work-items",
        template_name="run_packet_from_work_item",
        description=(
            "Render a non-mutating dry-run run packet from an "
            "execution-ready work item."
        ),
        implementation_target="structured_run_packet",
    ),
    RequestMetadata(
        canonical_name="run-report-from-work-item",
        legacy_names=("run_report_from_work_item",),
        category="work-items",
        template_name="run_report_from_work_item",
        description=(
            "Render a non-mutating manual/dry-run run report from "
            "an execution-ready work item and supplied evidence."
        ),
        implementation_target="structured_run_report",
    ),
    RequestMetadata(
        canonical_name="review-pull-request-against-work-item",
        legacy_names=(
            "review-pr-against-work-item",
            "pr-against-work-item",
            "pr_against_work_item",
        ),
        category="review",
        template_name="pr_against_work_item",
        description="Review a pull-request patch against a source work item.",
    ),
    RequestMetadata(
        canonical_name="work-items-from-audit",
        legacy_names=("work_items_from_audit",),
        category="planning",
        template_name="work_items_from_audit",
        description="Convert an audit report into proposed LRH work items.",
    ),
    RequestMetadata(
        canonical_name="assess-repository",
        legacy_names=("assessment",),
        category="assessment",
        template_name="assessment",
        description="Assess repository, focus, or work-item state.",
    ),
    RequestMetadata(
        canonical_name="bootstrap-project",
        legacy_names=("bootstrap_project",),
        category="bootstrap",
        template_name="bootstrap_project",
        description="Generate a request to bootstrap LRH project control files.",
    ),
    RequestMetadata(
        canonical_name="assess-continuous-integration-status",
        legacy_names=("assess-ci-status", "ci-assess-status", "ci_assess_status"),
        category="ci",
        template_name="ci_assess_status",
        description="Assess whether LRH-style CI migration is appropriate.",
    ),
    RequestMetadata(
        canonical_name="implement-continuous-integration-workflow",
        legacy_names=(
            "implement-ci-workflow",
            "ci-implement-workflow",
            "ci_implement_workflow",
        ),
        category="ci",
        template_name="ci_implement_workflow",
        description="Generate an assessment-gated CI workflow implementation request.",
    ),
    RequestMetadata(
        canonical_name="improve-coverage",
        legacy_names=("improve_coverage",),
        category="testing",
        template_name="improve_coverage",
        description="Generate a tests-focused request for one module.",
    ),
    RequestMetadata(
        canonical_name="review-response",
        legacy_names=("review_response",),
        category="review",
        template_name="review_response",
        description=(
            "Generate a response request for unresolved pull-request review " "threads."
        ),
    ),
)


def all_requests() -> tuple[RequestMetadata, ...]:
    """Return all cataloged requests in display order."""
    return _REQUESTS


def request_names() -> tuple[str, ...]:
    """Return every supported catalog request name in sorted order."""
    names: set[str] = set()
    for metadata in _REQUESTS:
        names.update(metadata.all_names())
    return tuple(sorted(names))


def canonical_names() -> tuple[str, ...]:
    """Return canonical request names in display order."""
    return tuple(metadata.canonical_name for metadata in _REQUESTS)


def resolve(name: str) -> RequestMetadata | None:
    """Resolve a canonical or legacy request name to catalog metadata."""
    normalized = name.strip()
    for metadata in _REQUESTS:
        if normalized in metadata.all_names():
            return metadata
    return None


def require(name: str) -> RequestMetadata:
    """Resolve a request name or raise a clear error for unknown names."""
    metadata = resolve(name)
    if metadata is None:
        raise ValueError(f"unknown request name: {name}")
    return metadata
