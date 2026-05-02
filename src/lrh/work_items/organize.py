"""Conservative work-item organization planning and application."""

from __future__ import annotations

import dataclasses
import re
from pathlib import Path

WI_ID_PATTERN = re.compile(r"\b(WI-[A-Z0-9][A-Z0-9_-]*)\b")
H1_PATTERN = re.compile(r"^#\s+(.+)$", re.MULTILINE)
STATUS_BUCKETS = ("proposed", "active", "resolved", "abandoned")


@dataclasses.dataclass(frozen=True)
class WorkItemPlan:
    source: Path
    target: Path
    work_item_id: str | None
    inferred_status: str | None
    add_frontmatter: bool
    add_id: bool
    add_status: bool
    skipped_reason: str | None
    warnings: tuple[str, ...] = ()

    def needs_change(self) -> bool:
        return (
            self.add_frontmatter
            or self.add_id
            or self.add_status
            or self.source != self.target
        )


@dataclasses.dataclass(frozen=True)
class OrganizationPlan:
    project_root: Path
    work_items_dir: Path
    inspected: tuple[WorkItemPlan, ...]

    def planned_changes(self) -> list[WorkItemPlan]:
        return [item for item in self.inspected if item.needs_change()]


def plan_organization(project_root: Path) -> OrganizationPlan:
    root = project_root / "project" / "work_items"
    if not root.exists():
        return OrganizationPlan(
            project_root=project_root, work_items_dir=root, inspected=()
        )

    files = sorted(set(root.glob("*.md")).union(root.glob("**/*.md")))
    plans: list[WorkItemPlan] = []
    for path in files:
        text = path.read_text(encoding="utf-8")
        parsed = _parse_doc(text)
        work_item_id = (
            parsed["id"] or _extract_h1_id(parsed["body"]) or _extract_filename_id(path)
        )
        if work_item_id is None:
            plans.append(
                WorkItemPlan(
                    path,
                    path,
                    None,
                    None,
                    False,
                    False,
                    False,
                    "no reliable WI-* id",
                    (),
                )
            )
            continue
        status = parsed["status"] or _infer_status(parsed["body"])
        warnings: list[str] = []
        if parsed["status"] is None and status == "proposed":
            warnings.append("status inference ambiguous; defaulted to proposed")
        target = root / status / path.name
        plans.append(
            WorkItemPlan(
                path,
                target,
                work_item_id,
                status,
                not parsed["has_frontmatter"],
                parsed["has_frontmatter"] and parsed["id"] is None,
                parsed["has_frontmatter"] and parsed["status"] is None,
                None,
                tuple(warnings),
            )
        )
    return OrganizationPlan(
        project_root=project_root, work_items_dir=root, inspected=tuple(plans)
    )


def apply_plan(plan: OrganizationPlan) -> None:
    for item in plan.inspected:
        if item.skipped_reason or not item.needs_change():
            continue
        text = item.source.read_text(encoding="utf-8")
        updated = _apply_frontmatter_updates(text=text, item=item)
        if item.source != item.target:
            item.target.parent.mkdir(parents=True, exist_ok=True)
            item.source.unlink()
            item.target.write_text(updated, encoding="utf-8")
        else:
            item.source.write_text(updated, encoding="utf-8")


def build_text_report(plan: OrganizationPlan, applied: bool = False) -> str:
    lines = [
        f"inspected: {len(plan.inspected)}",
        f"skipped: {sum(1 for i in plan.inspected if i.skipped_reason)}",
        f"changes: {len(plan.planned_changes())}",
    ]
    for item in plan.inspected:
        rel = item.source.relative_to(plan.project_root)
        if item.skipped_reason:
            lines.append(f"- skip {rel}: {item.skipped_reason}")
            continue
        actions: list[str] = []
        if item.add_frontmatter:
            actions.append("add_frontmatter")
        if item.add_id:
            actions.append("add_id")
        if item.add_status:
            actions.append("add_status")
        if item.source != item.target:
            actions.append(f"move->{item.target.relative_to(plan.project_root)}")
        if actions:
            action_text = ", ".join(actions)
            lines.append(
                f"- {'applied' if applied else 'plan'} {rel}: "
                f"{action_text} status={item.inferred_status}"
            )
        for warning in item.warnings:
            lines.append(f"  warning: {warning}")
    return "\n".join(lines)


def _apply_frontmatter_updates(text: str, item: WorkItemPlan) -> str:
    if item.add_frontmatter:
        body = text.lstrip("\n")
        frontmatter = (
            f"---\nid: {item.work_item_id}\nstatus: {item.inferred_status}\n---\n\n"
        )
        return f"{frontmatter}{body}"
    if text.startswith("---\n"):
        end = text.find("\n---\n", 4)
        if end == -1:
            return text
        front = text[4:end]
        body = text[end + 5 :]
        new_front = front
        if item.add_id:
            new_front = new_front.rstrip("\n") + f"\nid: {item.work_item_id}\n"
        if item.add_status:
            new_front = new_front.rstrip("\n") + f"\nstatus: {item.inferred_status}\n"
        return f"---\n{new_front}---\n{body}"
    return text


def _parse_doc(text: str) -> dict[str, str | bool | None]:
    has_frontmatter = text.startswith("---\n") and "\n---\n" in text[4:]
    front = ""
    body = text
    if has_frontmatter:
        split_index = text.find("\n---\n", 4)
        front = text[4:split_index]
        body = text[split_index + 5 :]
    id_match = re.search(r"^id:\s*(\S.*?)\s*$", front, flags=re.MULTILINE)
    status_match = re.search(r"^status:\s*(\S.*?)\s*$", front, flags=re.MULTILINE)
    item_id = _extract_inline_wi_id(id_match.group(1)) if id_match else None
    status = status_match.group(1).strip() if status_match else None
    if status not in STATUS_BUCKETS:
        status = None
    return {
        "has_frontmatter": has_frontmatter,
        "id": item_id,
        "status": status,
        "body": body,
    }


def _extract_h1_id(body: str) -> str | None:
    for match in H1_PATTERN.finditer(body):
        wi = _extract_inline_wi_id(match.group(1))
        if wi:
            return wi
    return None


def _extract_filename_id(path: Path) -> str | None:
    return _extract_inline_wi_id(path.stem)


def _extract_inline_wi_id(text: str) -> str | None:
    match = WI_ID_PATTERN.search(text.upper())
    if not match:
        return None
    return match.group(1)


def _infer_status(body: str) -> str:
    lower = body.lower()
    if re.search(r"\b(abandoned|cancelled|canceled|rejected|superseded)\b", lower):
        return "abandoned"
    if re.search(
        r"\b(resolved|complete|completed|done|implemented|landed|satisfied)\b", lower
    ):
        return "resolved"
    if re.search(r"\b(in progress|in-progress|active|ongoing|current focus)\b", lower):
        return "active"
    return "proposed"
