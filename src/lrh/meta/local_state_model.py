"""Typed meta local-state model and resolver helpers."""

from __future__ import annotations

import dataclasses
import datetime
import pathlib
from typing import Literal

from lrh.meta import workspace

StorageSource = Literal[
    "private_runtime",
    "trusted_workspace",
    "registry_record",
    "runtime_override",
    "none",
]


@dataclasses.dataclass(frozen=True)
class MetaStoragePolicy:
    """Storage policy for identity, checkout, and observation state."""

    trusted_persistent_local_state: bool = False
    identity_storage: StorageSource = "registry_record"
    checkout_binding_storage: StorageSource = "private_runtime"
    observation_storage: StorageSource = "private_runtime"


def storage_policy_from_trust(
    *, trusted_persistent_local_state: bool
) -> MetaStoragePolicy:
    """Create storage policy from trusted workspace persistence toggle."""
    if trusted_persistent_local_state:
        return MetaStoragePolicy(
            trusted_persistent_local_state=True,
            identity_storage="registry_record",
            checkout_binding_storage="trusted_workspace",
            observation_storage="trusted_workspace",
        )
    return MetaStoragePolicy()


@dataclasses.dataclass(frozen=True)
class CheckoutBinding:
    """Optional local checkout binding for one registered project."""

    local_repo_path: pathlib.Path
    storage_source: StorageSource


@dataclasses.dataclass(frozen=True)
class ObservationCheck:
    """Time-scoped observation check state."""

    status: str
    checked_as_of: datetime.datetime
    detail: str | None = None
    source: str | None = None

    def to_json_dict(self) -> dict[str, str]:
        """Return JSON-serializable dict representation."""
        payload: dict[str, str] = {
            "status": self.status,
            "checked_as_of": self.checked_as_of.isoformat(),
        }
        if self.detail is not None:
            payload["detail"] = self.detail
        if self.source is not None:
            payload["source"] = self.source
        return payload


@dataclasses.dataclass(frozen=True)
class ResolvedProjectContext:
    """Resolved project context for meta/serve consumers."""

    identity: workspace.MetaProjectRecord
    resolved_repo_path: pathlib.Path | None
    resolved_repo_path_source: str
    resolved_project_path: pathlib.Path | None
    source_state: str
    setup_state: str | None
    checks: dict[str, ObservationCheck]
    storage_policy: MetaStoragePolicy


@dataclasses.dataclass(frozen=True)
class ResolveContextRequest:
    """Resolution inputs from runtime, private bindings, and storage policy."""

    runtime_repo_override: pathlib.Path | None = None
    private_checkout_binding: CheckoutBinding | None = None
    trusted_checkout_binding: CheckoutBinding | None = None
    checks: dict[str, ObservationCheck] | None = None
    storage_policy: MetaStoragePolicy = dataclasses.field(
        default_factory=MetaStoragePolicy
    )


def resolve_project_context(
    record: workspace.MetaProjectRecord,
    *,
    workspace_context: workspace.MetaWorkspace,
    request: ResolveContextRequest | None = None,
) -> ResolvedProjectContext:
    """Resolve local repo/project paths with layered source precedence."""
    if request is None:
        request = ResolveContextRequest()

    resolved_repo_path: pathlib.Path | None = None
    resolved_source = "none"
    source_state = "remote_only"

    if request.runtime_repo_override is not None:
        resolved_repo_path = _normalize_runtime_path(request.runtime_repo_override)
        resolved_source = "runtime_override"
        source_state = "local_available"
    elif request.private_checkout_binding is not None:
        resolved_repo_path = _normalize_runtime_path(
            request.private_checkout_binding.local_repo_path
        )
        resolved_source = "private_checkout_binding"
        source_state = "local_available"
    elif (
        request.storage_policy.trusted_persistent_local_state
        and request.trusted_checkout_binding is not None
    ):
        resolved_repo_path = _normalize_runtime_path(
            request.trusted_checkout_binding.local_repo_path
        )
        resolved_source = "trusted_workspace_checkout_binding"
        source_state = "local_available"
    else:
        inferred_repo = _resolved_repo_from_locator(record, workspace_context)
        if inferred_repo is not None:
            resolved_repo_path = inferred_repo
            resolved_source = "repo_locator_local_path"
            source_state = "local_available"
        elif record.repo_locator:
            resolved_source = "repo_locator_remote_url"

    resolved_project_path: pathlib.Path | None = None
    if resolved_repo_path is not None and record.project_dir is not None:
        resolved_project_path = _resolve_project_path(
            resolved_repo_path=resolved_repo_path,
            project_dir=record.project_dir,
        )

    return ResolvedProjectContext(
        identity=record,
        resolved_repo_path=resolved_repo_path,
        resolved_repo_path_source=resolved_source,
        resolved_project_path=resolved_project_path,
        source_state=source_state,
        setup_state=record.setup_state,
        checks=request.checks or {},
        storage_policy=request.storage_policy,
    )


def _resolved_repo_from_locator(
    record: workspace.MetaProjectRecord,
    workspace_context: workspace.MetaWorkspace,
) -> pathlib.Path | None:
    return workspace._resolved_local_repo_path(
        record.repo_locator,
        workspace=workspace_context,
    )


def _resolve_project_path(
    *,
    resolved_repo_path: pathlib.Path,
    project_dir: str,
) -> pathlib.Path | None:
    project_subpath = pathlib.Path(project_dir)
    if project_subpath.is_absolute():
        return None

    candidate = workspace._normalize_path(resolved_repo_path / project_subpath)
    try:
        candidate.relative_to(resolved_repo_path)
    except ValueError:
        return None
    return candidate


def _normalize_runtime_path(path: pathlib.Path) -> pathlib.Path:
    return workspace._normalize_path(path.expanduser())
