"""Deterministic YAML-frontmatter rendering helpers for conversation artifacts."""

from __future__ import annotations

from typing import Mapping, Sequence


def yaml_mapping(mapping: Mapping[str, object], *, indent: int = 0) -> str:
    """Render a small deterministic YAML mapping for conversation metadata."""

    lines: list[str] = []
    prefix = " " * indent
    for key, value in mapping.items():
        if isinstance(value, Mapping):
            lines.append(f"{prefix}{key}:")
            lines.append(yaml_mapping(value, indent=indent + 2).rstrip("\n"))
        elif _is_sequence(value):
            lines.append(f"{prefix}{key}:")
            lines.extend(_yaml_sequence(value, indent=indent + 2))
            if not value:
                lines[-1] = f"{prefix}{key}: []"
        else:
            lines.append(f"{prefix}{key}: {yaml_scalar(value)}")
    return "\n".join(lines) + "\n"


def yaml_scalar(value: object) -> str:
    """Render a scalar for the limited YAML subset LRH writes."""

    if value is None:
        return "null"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, int):
        return str(value)
    text = str(value)
    escaped = (
        text.replace("\\", "\\\\")
        .replace('"', '\\"')
        .replace("\n", "\\n")
        .replace("\r", "\\r")
        .replace("\t", "\\t")
    )
    return f'"{escaped}"'


def _yaml_sequence(value: Sequence[object], *, indent: int) -> list[str]:
    lines: list[str] = []
    prefix = " " * indent
    for item in value:
        if isinstance(item, Mapping):
            lines.append(f"{prefix}-")
            lines.append(yaml_mapping(item, indent=indent + 2).rstrip("\n"))
        elif _is_sequence(item):
            lines.append(f"{prefix}-")
            lines.extend(_yaml_sequence(item, indent=indent + 2))
        else:
            lines.append(f"{prefix}- {yaml_scalar(item)}")
    return lines


def _is_sequence(value: object) -> bool:
    return isinstance(value, (list, tuple)) and not isinstance(value, (str, bytes))
