"""Helpers for request-template discovery and loading."""

import importlib.resources
import pathlib


def get_template_root() -> importlib.resources.abc.Traversable:
    """Return the package-owned request-template directory."""
    return importlib.resources.files("lrh.assist").joinpath("templates", "request")


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


def load_template_text(
    template_name: str,
    template_root: pathlib.Path | None = None,
) -> str:
    """Load a request template as UTF-8 text."""
    if template_root is not None:
        template_path = get_template_path(template_name, template_root)
        return template_path.read_text(encoding="utf-8")

    template_file = get_template_root().joinpath(f"{template_name}.md")
    if not template_file.is_file():
        raise FileNotFoundError(
            "Template not found in package resources: "
            f"lrh/assist/templates/request/{template_name}.md"
        )

    return template_file.read_text(encoding="utf-8")
