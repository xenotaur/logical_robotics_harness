"""Markdown + frontmatter parsing for LRH control artifacts."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any


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

    frontmatter_text, body = _split_frontmatter_and_body(text)
    frontmatter = _parse_frontmatter_mapping(frontmatter_text)
    return ParsedMarkdown(frontmatter=frontmatter, body=body)


def _split_frontmatter_and_body(text: str) -> tuple[str, str]:
    closing_start: int | None = None
    closing_end: int | None = None

    scan_index = 4
    while scan_index <= len(text):
        line_end = text.find("\n", scan_index)
        if line_end == -1:
            line_end = len(text)
        line = text[scan_index:line_end]

        if line.strip() == "---":
            closing_start = scan_index
            closing_end = line_end
            break

        if line_end == len(text):
            break
        scan_index = line_end + 1

    if closing_start is None or closing_end is None:
        raise ValueError("missing closing YAML frontmatter delimiter '---'")

    frontmatter_text = text[4:closing_start]
    body_start = closing_end + 1 if closing_end < len(text) else closing_end
    body = text[body_start:]
    return frontmatter_text, body


def _parse_frontmatter_mapping(text: str) -> dict[str, Any]:
    data: dict[str, Any] = {}
    lines = text.splitlines()
    index = 0
    while index < len(lines):
        line = lines[index]
        if not line.strip() or line.lstrip().startswith("#"):
            index += 1
            continue

        if line.startswith(" "):
            raise ValueError(f"unexpected indentation in frontmatter: {line!r}")

        if ":" not in line:
            raise ValueError(f"invalid frontmatter entry: {line!r}")

        key, raw_value = line.split(":", 1)
        key = key.strip()
        value_text = raw_value.strip()

        if value_text == "":
            block_values: list[str] = []
            index += 1
            while index < len(lines):
                candidate = lines[index]
                stripped_candidate = candidate.lstrip()
                if stripped_candidate.startswith("- "):
                    block_values.append(stripped_candidate[2:].strip())
                    index += 1
                    continue
                if not candidate.strip():
                    index += 1
                    continue
                if candidate.startswith("  "):
                    raise ValueError(
                        f"unsupported nested mapping for key '{key}': {candidate!r}"
                    )
                break
            data[key] = block_values if block_values else None
            continue

        if value_text == ">":
            index += 1
            folded_lines: list[str] = []
            while index < len(lines) and (
                not lines[index].strip() or lines[index].startswith("  ")
            ):
                raw_folded = lines[index]
                folded_lines.append(
                    raw_folded[2:] if raw_folded.startswith("  ") else ""
                )
                index += 1
            data[key] = " ".join(part for part in folded_lines if part).strip()
            continue

        data[key] = _parse_scalar(value_text)
        index += 1

    return data


def _parse_scalar(value: str) -> Any:
    if value == "[]":
        return []
    if value.startswith("[") and value.endswith("]"):
        inner = value[1:-1].strip()
        if not inner:
            return []
        return [_strip_quotes(part.strip()) for part in inner.split(",")]
    if value.startswith('"') and value.endswith('"'):
        return value[1:-1]
    if value.startswith("'") and value.endswith("'"):
        return value[1:-1]
    if value == "null":
        return None
    if value == "true":
        return True
    if value == "false":
        return False
    if value.isdigit() or (value.startswith("-") and value[1:].isdigit()):
        return int(value)
    return value


def _strip_quotes(value: str) -> str:
    if value.startswith('"') and value.endswith('"'):
        return value[1:-1]
    if value.startswith("'") and value.endswith("'"):
        return value[1:-1]
    return value
