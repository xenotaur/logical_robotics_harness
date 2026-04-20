"""Helpers for request-template discovery and loading."""

import pathlib


def get_template_root() -> pathlib.Path:
    """Return the default request-template directory for this repository."""
    repo_root = pathlib.Path(__file__).resolve().parents[3]
    return repo_root / "scripts" / "aiprog" / "templates" / "request"


def get_template_path(
    template_name: str,
    template_root: pathlib.Path | None = None,
) -> pathlib.Path:
    """Resolve a request template name to a markdown file path."""
    root = template_root if template_root is not None else get_template_root()
    template_path = root / f"{template_name}.md"
    if not template_path.exists():
        raise FileNotFoundError(
            f"Template not found: {template_path}\n"
            f"Expected: scripts/aiprog/templates/request/{template_name}.md"
        )
    return template_path


def load_template_text(
    template_name: str,
    template_root: pathlib.Path | None = None,
) -> str:
    """Load a request template as UTF-8 text."""
    template_path = get_template_path(template_name, template_root)
    return template_path.read_text(encoding="utf-8")
