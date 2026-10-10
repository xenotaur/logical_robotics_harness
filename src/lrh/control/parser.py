"""Markdown + frontmatter parsing for LRH control artifacts."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

# PyYAML's libyaml-backed loader is several times faster. It is optional, so
# fall back to the pure-Python loader when PyYAML was built without libyaml.
_FAST_SAFE_LOADER: type = getattr(yaml, "CSafeLoader", yaml.SafeLoader)


@dataclass(frozen=True)
class ParsedMarkdown:
    """Parsed Markdown document with mapping frontmatter and body text."""

    frontmatter: dict[str, Any]
    body: str


def parse_markdown_file(path: Path) -> ParsedMarkdown:
    return parse_markdown_text(path.read_text(encoding="utf-8"))


def parse_markdown_text(text: str) -> ParsedMarkdown:
    if not text.startswith("---\n"):
        raise ValueError(
            "markdown file must begin with YAML frontmatter delimiter '---'"
        )

    frontmatter_text, body = split_frontmatter_and_body(text)
    frontmatter = parse_frontmatter_mapping(frontmatter_text)
    return ParsedMarkdown(frontmatter=frontmatter, body=body)


def split_frontmatter_and_body(text: str) -> tuple[str, str]:
    """Split raw Markdown text into its frontmatter text and body, without
    parsing the frontmatter as YAML.

    Public so callers that need the raw frontmatter text before it's known
    to be valid YAML (e.g. the frontmatter lint/migration tooling in
    ``control/frontmatter_lint.py`` and ``control/frontmatter_migration.py``)
    don't have to reach for the private delimiter-finding logic.
    """
    return _split_frontmatter_and_body(text)


def _split_frontmatter_and_body(text: str) -> tuple[str, str]:
    closing_start: int | None = None
    closing_end: int | None = None

    start = 4
    while True:
        idx = text.find("---", start)
        if idx == -1:
            break

        line_start = text.rfind("\n", 0, idx) + 1
        line_end = text.find("\n", idx)
        if line_end == -1:
            line_end = len(text)

        line = text[line_start:line_end]
        if line.strip() == "---":
            closing_start = line_start
            closing_end = line_end
            break

        start = idx + 3

    if closing_start is None or closing_end is None:
        raise ValueError("missing closing YAML frontmatter delimiter '---'")

    frontmatter_text = text[4:closing_start]
    body_start = closing_end + 1 if closing_end < len(text) else closing_end
    body = text[body_start:]
    return frontmatter_text, body


def safe_load_fast(text: str) -> Any:
    """``yaml.safe_load`` through libyaml when available.

    On a syntax error the text is parsed again with the pure-Python loader,
    so the exception (and every message built from it) is exactly the one
    ``yaml.safe_load`` raises. Errors are rare, so the second parse costs
    little.
    """

    try:
        return yaml.load(text, Loader=_FAST_SAFE_LOADER)  # noqa: S506 (safe loader)
    except yaml.YAMLError:
        if _FAST_SAFE_LOADER is yaml.SafeLoader:
            raise
        return yaml.safe_load(text)


def load_yaml_document(text: str) -> Any:
    """Parse a YAML document, wrapping syntax errors as ``ValueError``."""

    try:
        return safe_load_fast(text)
    except yaml.YAMLError as exc:
        raise ValueError(f"invalid YAML in frontmatter: {exc}") from exc


def parse_frontmatter_mapping(text: str) -> dict[str, Any]:
    """Parse frontmatter YAML text into a mapping, using PyYAML directly.

    An empty document parses to ``{}`` rather than ``None`` so callers always
    get a mapping back. Shared by ``control/validator.py`` so both the
    general validator and the work-item-specific tooling agree on what
    valid frontmatter is.
    """

    data = load_yaml_document(text)
    if data is None:
        return {}
    if not isinstance(data, dict):
        raise ValueError("frontmatter must parse to a mapping object")
    return data
