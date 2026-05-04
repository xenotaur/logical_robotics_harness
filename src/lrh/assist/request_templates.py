"""Helpers for request-template discovery and loading."""

import importlib.resources as resources
import pathlib

from lrh.assist import template_resolver


def get_template_root() -> resources.abc.Traversable:
    """Return the package-owned request-template directory."""
    return resources.files("lrh.assist.templates").joinpath("request")


def get_template_path(
    template_name: str,
    template_root: pathlib.Path | None = None,
) -> pathlib.Path:
    """Resolve a request template name to a markdown file path.

    Args:
        template_name: Request template base name without the ``.md`` suffix.
        template_root: Optional filesystem override used by tests.

    Returns:
        Resolved filesystem path for the requested template.

    Raises:
        FileNotFoundError: If the template is not present under ``template_root``.
    """
    if template_root is None:
        raise ValueError(
            "get_template_path requires template_root. "
            "Use load_template_text without template_root for package resources."
        )

    template_path = template_root / f"{template_name}.md"
    if not template_path.exists():
        raise FileNotFoundError(
            f"Template not found: {template_path}\n"
            f"Expected: {template_root}/{template_name}.md"
        )
    return template_path


def resolve_template(
    template_name: str,
    template_root: pathlib.Path | None = None,
    project_root: pathlib.Path | None = None,
    template_dirs: list[pathlib.Path | str] | None = None,
    environ: dict[str, str] | None = None,
) -> template_resolver.TemplateResolution:
    """Resolve a request template and return source metadata."""
    if template_root is not None:
        template_path = get_template_path(template_name, template_root)
        return template_resolver.TemplateResolution(
            logical_name=f"request/{template_name}.md",
            source="explicit",
            origin=str(template_path),
            path=template_path,
        )

    resolver = template_resolver.TemplateResolver(
        template_dirs=template_dirs,
        project_root=project_root,
        environ=environ,
    )
    return resolver.resolve(f"request/{template_name}.md")


def load_template_text(
    template_name: str,
    template_root: pathlib.Path | None = None,
    project_root: pathlib.Path | None = None,
    template_dirs: list[pathlib.Path | str] | None = None,
    environ: dict[str, str] | None = None,
) -> str:
    """Load a request template as UTF-8 text."""
    if template_root is not None:
        resolution = resolve_template(
            template_name,
            template_root=template_root,
            project_root=project_root,
            template_dirs=template_dirs,
            environ=environ,
        )
        if resolution.path is not None:
            return resolution.path.read_text(encoding="utf-8")

    resolver = template_resolver.TemplateResolver(
        template_dirs=template_dirs,
        project_root=project_root,
        environ=environ,
    )
    return resolver.read_text(f"request/{template_name}.md")


def request_template_names(
    *,
    project_root: pathlib.Path | None = None,
    template_dirs: list[pathlib.Path | str] | None = None,
    environ: dict[str, str] | None = None,
) -> list[str]:
    """Return sorted request-template base names from overrides and package data."""
    resolver = template_resolver.TemplateResolver(
        template_dirs=template_dirs,
        project_root=project_root,
        environ=environ,
    )
    names: set[str] = set()
    for logical_name in resolver.list_logical_names():
        if not logical_name.startswith("request/"):
            continue
        if logical_name.count("/") != 1:
            continue
        if not logical_name.endswith(".md"):
            continue
        names.add(logical_name[len("request/") : -len(".md")])
    return sorted(names)
