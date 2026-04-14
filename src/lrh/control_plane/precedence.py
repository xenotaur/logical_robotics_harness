"""Deterministic precedence resolution for LRH control-plane artifacts."""

from __future__ import annotations

import dataclasses


@dataclasses.dataclass(frozen=True)
class RuntimeInvocation:
    """Runtime narrowing directives for a single resolver invocation."""

    focus_id: str | None = None
    work_item_ids: tuple[str, ...] = ()
    contributor_ids: tuple[str, ...] = ()


@dataclasses.dataclass(frozen=True)
class ControlPlaneState:
    """Already-loaded control-plane artifacts used for precedence resolution."""

    principles: tuple[dict[str, object], ...] = ()
    goal: dict[str, object] | None = None
    roadmap: tuple[dict[str, object], ...] = ()
    focus: dict[str, object] | None = None
    work_items: tuple[dict[str, object], ...] = ()
    guardrails: dict[str, object] | None = None


@dataclasses.dataclass(frozen=True)
class ResolvedState:
    """Effective operational state after applying precedence rules."""

    active_focus: dict[str, object] | None
    in_scope_work_items: tuple[dict[str, object], ...]
    active_contributors: tuple[str, ...]
    consistency_issues: tuple[str, ...] = ()


def resolve_precedence(
    state: ControlPlaneState,
    runtime_invocation: RuntimeInvocation | None = None,
) -> ResolvedState:
    """Resolve effective focus, work items, and contributors.

    Precedence order is applied from broader intent to narrower execution:
    principles -> goal -> roadmap -> focus -> work items -> guardrails -> runtime.
    Guardrails may restrict, while runtime may only narrow.
    """

    invocation = runtime_invocation or RuntimeInvocation()
    consistency_issues: list[str] = []

    active_focus = _resolve_active_focus(state.focus, invocation, consistency_issues)
    focus_id = _focus_id(active_focus)

    ordered_items = _stable_sort_work_items(state.work_items)
    in_scope = _resolve_work_items(ordered_items, focus_id, invocation.work_item_ids)

    guardrails = state.guardrails or {}
    in_scope = _apply_guardrail_work_item_restrictions(in_scope, guardrails)

    contributors = _resolve_contributors(active_focus, in_scope)
    contributors = _apply_guardrail_contributor_restrictions(contributors, guardrails)
    contributors = _apply_runtime_contributor_narrowing(
        contributors,
        invocation.contributor_ids,
    )

    return ResolvedState(
        active_focus=active_focus,
        in_scope_work_items=in_scope,
        active_contributors=contributors,
        consistency_issues=tuple(consistency_issues),
    )


def _resolve_active_focus(
    focus: dict[str, object] | None,
    invocation: RuntimeInvocation,
    consistency_issues: list[str],
) -> dict[str, object] | None:
    if focus is None:
        return None

    focus_id = _focus_id(focus)
    if invocation.focus_id is None:
        if focus.get("status") == "active":
            return focus
        return None

    if focus_id is None:
        consistency_issues.append(
            "runtime focus_id was provided but the loaded focus artifact has no id"
        )
        return None

    if invocation.focus_id != focus_id:
        consistency_issues.append(
            "runtime focus_id does not match loaded current focus id"
        )
        return None

    return focus


def _resolve_work_items(
    ordered_items: tuple[dict[str, object], ...],
    focus_id: str | None,
    runtime_work_item_ids: tuple[str, ...],
) -> tuple[dict[str, object], ...]:
    scoped = ordered_items

    if focus_id is not None:
        scoped = tuple(
            work_item
            for work_item in scoped
            if _related_focus_contains(work_item, focus_id)
        )

    if runtime_work_item_ids:
        allowed = set(runtime_work_item_ids)
        scoped = tuple(
            work_item
            for work_item in scoped
            if isinstance(work_item.get("id"), str) and work_item["id"] in allowed
        )

    return scoped


def _resolve_contributors(
    active_focus: dict[str, object] | None,
    in_scope_work_items: tuple[dict[str, object], ...],
) -> tuple[str, ...]:
    contributor_ids: set[str] = set()

    if active_focus is not None:
        active_contributors = active_focus.get("active_contributors")
        if isinstance(active_contributors, list):
            contributor_ids.update(
                contributor_id
                for contributor_id in active_contributors
                if isinstance(contributor_id, str)
            )

    for work_item in in_scope_work_items:
        owner = work_item.get("owner")
        if isinstance(owner, str):
            contributor_ids.add(owner)

        for contributor_field in ("contributors", "assigned_agents"):
            values = work_item.get(contributor_field)
            if isinstance(values, list):
                contributor_ids.update(
                    value for value in values if isinstance(value, str)
                )

    return tuple(sorted(contributor_ids))


def _apply_guardrail_work_item_restrictions(
    in_scope_work_items: tuple[dict[str, object], ...],
    guardrails: dict[str, object],
) -> tuple[dict[str, object], ...]:
    blocked = guardrails.get("blocked_work_item_ids")
    if not isinstance(blocked, list):
        return in_scope_work_items

    blocked_ids = {
        work_item_id for work_item_id in blocked if isinstance(work_item_id, str)
    }
    if not blocked_ids:
        return in_scope_work_items

    return tuple(
        work_item
        for work_item in in_scope_work_items
        if isinstance(work_item.get("id"), str) and work_item["id"] not in blocked_ids
    )


def _apply_guardrail_contributor_restrictions(
    contributors: tuple[str, ...],
    guardrails: dict[str, object],
) -> tuple[str, ...]:
    blocked = guardrails.get("blocked_contributor_ids")
    if not isinstance(blocked, list):
        return contributors

    blocked_ids = {
        contributor_id for contributor_id in blocked if isinstance(contributor_id, str)
    }
    if not blocked_ids:
        return contributors

    return tuple(
        contributor for contributor in contributors if contributor not in blocked_ids
    )


def _apply_runtime_contributor_narrowing(
    contributors: tuple[str, ...],
    runtime_contributor_ids: tuple[str, ...],
) -> tuple[str, ...]:
    if not runtime_contributor_ids:
        return contributors

    allowed = set(runtime_contributor_ids)
    return tuple(contributor for contributor in contributors if contributor in allowed)


def _focus_id(focus: dict[str, object] | None) -> str | None:
    if focus is None:
        return None
    value = focus.get("id")
    if isinstance(value, str):
        return value
    return None


def _related_focus_contains(work_item: dict[str, object], focus_id: str) -> bool:
    related_focus = work_item.get("related_focus")
    if not isinstance(related_focus, list):
        return False
    return focus_id in related_focus


def _stable_sort_work_items(
    work_items: tuple[dict[str, object], ...],
) -> tuple[dict[str, object], ...]:
    enumerated = enumerate(work_items)
    sorted_items = sorted(
        enumerated,
        key=lambda pair: (
            _sortable_work_item_id(pair[1]),
            pair[0],
        ),
    )
    return tuple(item for _, item in sorted_items)


def _sortable_work_item_id(work_item: dict[str, object]) -> str:
    work_item_id = work_item.get("id")
    if isinstance(work_item_id, str):
        return work_item_id
    return ""
