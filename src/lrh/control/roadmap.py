"""Typed, read-only loader for the roadmap documents in ``project/roadmap/``.

A roadmap document without a ``parent`` (today ``roadmap.md``,
``ROADMAP-CORE``) is the roadmap root. Every other document is a phase with a
numeric ``order``, which may be fractional (``1.5``). Problems become
diagnostics; loading never raises for a malformed or missing file.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from lrh.control.parser import parse_markdown_file


@dataclass(frozen=True)
class RoadmapRoot:
    """The parentless document that the phases hang from."""

    id: str
    title: str
    status: str
    path: Path


@dataclass(frozen=True)
class RoadmapPhase:
    """One ordered roadmap phase."""

    id: str
    title: str
    status: str
    parent: str
    order: float
    path: Path


@dataclass(frozen=True)
class RoadmapDiagnostic:
    """A roadmap file that could not be read as a root or a phase."""

    path: Path
    code: str
    message: str


@dataclass(frozen=True)
class Roadmap:
    """The roadmap root (if any), its phases in order, and any diagnostics."""

    root: RoadmapRoot | None
    phases: tuple[RoadmapPhase, ...]
    diagnostics: tuple[RoadmapDiagnostic, ...]

    def phase(self, phase_id: str) -> RoadmapPhase | None:
        return next((phase for phase in self.phases if phase.id == phase_id), None)


def load_roadmap(project_dir: Path) -> Roadmap:
    """Load ``<project_dir>/roadmap/*.md`` as a root and ordered phases."""

    directory = project_dir / "roadmap"
    if not directory.is_dir():
        return Roadmap(
            root=None,
            phases=(),
            diagnostics=(
                RoadmapDiagnostic(
                    path=directory,
                    code="ROADMAP_DIR_MISSING",
                    message="The project has no roadmap directory.",
                ),
            ),
        )

    root: RoadmapRoot | None = None
    phases: list[RoadmapPhase] = []
    diagnostics: list[RoadmapDiagnostic] = []
    for path in sorted(directory.glob("*.md")):
        try:
            frontmatter = parse_markdown_file(path).frontmatter
        except (OSError, UnicodeDecodeError, ValueError) as error:
            diagnostics.append(
                RoadmapDiagnostic(path, "ROADMAP_UNREADABLE", f"{path.name}: {error}")
            )
            continue
        doc_id = _text(frontmatter.get("id"))
        if not doc_id:
            diagnostics.append(
                RoadmapDiagnostic(path, "ROADMAP_MISSING_ID", f"{path.name}: no id.")
            )
            continue
        title = _text(frontmatter.get("title")) or doc_id
        status = _text(frontmatter.get("status")) or "unknown"
        parent = _text(frontmatter.get("parent"))
        if not parent:
            if root is not None:
                diagnostics.append(
                    RoadmapDiagnostic(
                        path,
                        "ROADMAP_EXTRA_ROOT",
                        f"{path.name}: {doc_id} has no parent, but {root.id} is "
                        "already the roadmap root.",
                    )
                )
                continue
            root = RoadmapRoot(id=doc_id, title=title, status=status, path=path)
            continue
        order = _order(frontmatter.get("order"))
        if order is None:
            diagnostics.append(
                RoadmapDiagnostic(
                    path,
                    "ROADMAP_PHASE_ORDER",
                    f"{path.name}: phase {doc_id} needs a numeric order.",
                )
            )
            continue
        phases.append(
            RoadmapPhase(
                id=doc_id,
                title=title,
                status=status,
                parent=parent,
                order=order,
                path=path,
            )
        )
    phases.sort(key=lambda phase: (phase.order, phase.id))
    return Roadmap(root=root, phases=tuple(phases), diagnostics=tuple(diagnostics))


def _text(value: object) -> str:
    return value.strip() if isinstance(value, str) else ""


def _order(value: object) -> float | None:
    # bool is an int subclass; "order: true" is not a position.
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    return float(value)
