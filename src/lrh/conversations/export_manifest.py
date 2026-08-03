"""Typed manifest helpers for private Codex conversation exports."""

from __future__ import annotations

import dataclasses
import re
from datetime import datetime, timezone
from typing import Mapping

KIND = "lrh_codex_conversation_export"
SCHEMA_VERSION = 1
SOURCE_TOOL_CODEX = "codex"
DEFAULT_SOURCE_ADAPTER = "codex_manual_export"
DEFAULT_PRIVACY = "private"
DEFAULT_AUTHORITY = "non_authoritative_context"
ADAPTER_VERSION = 1
SENSITIVITY_SCAN_FIELD_ORDER = (
    "status",
    "scanner",
    "scanner_version",
    "finding_count",
    "categories",
)


class ConversationExportManifestError(ValueError):
    """Raised when a conversation export manifest is malformed."""


@dataclasses.dataclass(frozen=True)
class TranscriptStatistics:
    """Stable transcript counts recorded in a conversation export manifest."""

    byte_count: int
    character_count: int
    line_count: int
    turn_count: int | None = None
    message_count: int | None = None

    def __post_init__(self) -> None:
        _require_non_negative_int(self.byte_count, "byte_count")
        _require_non_negative_int(self.character_count, "character_count")
        _require_non_negative_int(self.line_count, "line_count")
        _require_optional_non_negative_int(self.turn_count, "turn_count")
        _require_optional_non_negative_int(self.message_count, "message_count")

    def to_mapping(self) -> dict[str, object]:
        """Return deterministic manifest-ready statistics."""

        mapping: dict[str, object] = {
            "byte_count": self.byte_count,
            "character_count": self.character_count,
            "line_count": self.line_count,
        }
        if self.turn_count is not None:
            mapping["turn_count"] = self.turn_count
        if self.message_count is not None:
            mapping["message_count"] = self.message_count
        return mapping

    @classmethod
    def from_mapping(cls, mapping: Mapping[str, object]) -> "TranscriptStatistics":
        """Validate and load transcript statistics from manifest data."""

        return cls(
            byte_count=_required_int(mapping, "byte_count"),
            character_count=_required_int(mapping, "character_count"),
            line_count=_required_int(mapping, "line_count"),
            turn_count=_optional_int(mapping, "turn_count"),
            message_count=_optional_int(mapping, "message_count"),
        )


@dataclasses.dataclass(frozen=True)
class ConversationExportManifest:
    """Metadata contract for a private, non-authoritative Codex transcript."""

    source_sha256: str
    exported_at: str
    transcript_statistics: TranscriptStatistics
    sensitivity_scan: Mapping[str, object]
    kind: str = KIND
    schema_version: int = SCHEMA_VERSION
    source_tool: str = SOURCE_TOOL_CODEX
    source_adapter: str = DEFAULT_SOURCE_ADAPTER
    privacy: str = DEFAULT_PRIVACY
    authority: str = DEFAULT_AUTHORITY
    sensitivity: str = "unscanned"
    source_id: str | None = None
    adapter_version: int = ADAPTER_VERSION
    warnings: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        _require_exact(self.kind, KIND, "kind")
        _require_exact(self.schema_version, SCHEMA_VERSION, "schema_version")
        _require_exact(self.source_tool, SOURCE_TOOL_CODEX, "source_tool")
        _require_non_empty_string(self.source_adapter, "source_adapter")
        _require_exact(self.privacy, DEFAULT_PRIVACY, "privacy")
        _require_exact(self.authority, DEFAULT_AUTHORITY, "authority")
        _require_non_empty_string(self.sensitivity, "sensitivity")
        _require_sha256(self.source_sha256, "source_sha256")
        _require_iso_datetime(self.exported_at, "exported_at")
        _require_non_negative_int(self.adapter_version, "adapter_version")
        if self.source_id is not None:
            _require_non_empty_string(self.source_id, "source_id")
        for warning in self.warnings:
            _require_non_empty_string(warning, "warnings")

    def to_mapping(self) -> dict[str, object]:
        """Return a deterministic serializable manifest mapping."""

        mapping: dict[str, object] = {
            "kind": self.kind,
            "schema_version": self.schema_version,
            "source_tool": self.source_tool,
            "source_adapter": self.source_adapter,
            "privacy": self.privacy,
            "authority": self.authority,
            "sensitivity": self.sensitivity,
            "sensitivity_scan": _deterministic_mapping(
                self.sensitivity_scan,
                preferred_order=SENSITIVITY_SCAN_FIELD_ORDER,
            ),
        }
        if self.source_id is not None:
            mapping["source_id"] = self.source_id
        mapping.update(
            {
                "source_sha256": self.source_sha256,
                "exported_at": self.exported_at,
                "adapter_version": self.adapter_version,
                "warnings": list(self.warnings),
                "transcript_statistics": self.transcript_statistics.to_mapping(),
            }
        )
        return mapping

    def to_frontmatter(self) -> str:
        """Render the manifest as deterministic YAML frontmatter."""

        return f"---\n{_yaml_mapping(self.to_mapping())}---\n"

    @classmethod
    def from_mapping(
        cls, mapping: Mapping[str, object]
    ) -> "ConversationExportManifest":
        """Validate and load a manifest from serialized mapping data."""

        return cls(
            kind=_required_str(mapping, "kind"),
            schema_version=_required_int(mapping, "schema_version"),
            source_tool=_required_str(mapping, "source_tool"),
            source_adapter=_required_str(mapping, "source_adapter"),
            privacy=_required_str(mapping, "privacy"),
            authority=_required_str(mapping, "authority"),
            sensitivity=_required_str(mapping, "sensitivity"),
            sensitivity_scan=_required_mapping(mapping, "sensitivity_scan"),
            source_id=_optional_str(mapping, "source_id"),
            source_sha256=_required_str(mapping, "source_sha256"),
            exported_at=_required_str(mapping, "exported_at"),
            adapter_version=_required_int(mapping, "adapter_version"),
            warnings=_string_tuple(mapping.get("warnings", ()), "warnings"),
            transcript_statistics=TranscriptStatistics.from_mapping(
                _required_mapping(mapping, "transcript_statistics")
            ),
        )


def statistics_for_text(
    text: str,
    *,
    encoding: str = "utf-8",
    turn_count: int | None = None,
    message_count: int | None = None,
) -> TranscriptStatistics:
    """Compute deterministic transcript statistics for text."""

    return TranscriptStatistics(
        byte_count=len(text.encode(encoding)),
        character_count=len(text),
        line_count=len(text.splitlines()),
        turn_count=turn_count,
        message_count=message_count,
    )


def build_codex_manifest(
    *,
    transcript_text: str,
    source_sha256: str,
    exported_at: datetime | str | None = None,
    source_id: str | None = None,
    source_adapter: str = DEFAULT_SOURCE_ADAPTER,
    adapter_version: int = ADAPTER_VERSION,
    sensitivity: str = "unscanned",
    sensitivity_scan: Mapping[str, object] | None = None,
    warnings: tuple[str, ...] | list[str] = (),
    turn_count: int | None = None,
    message_count: int | None = None,
) -> ConversationExportManifest:
    """Build a default private, non-authoritative Codex export manifest."""

    return ConversationExportManifest(
        source_sha256=source_sha256,
        exported_at=_exported_at_value(exported_at),
        source_id=source_id,
        source_adapter=source_adapter,
        adapter_version=adapter_version,
        sensitivity=sensitivity,
        sensitivity_scan=(
            {"status": "not_scanned"}
            if sensitivity_scan is None
            else dict(sensitivity_scan)
        ),
        warnings=tuple(warnings),
        transcript_statistics=statistics_for_text(
            transcript_text,
            turn_count=turn_count,
            message_count=message_count,
        ),
    )


def _exported_at_value(value: datetime | str | None) -> str:
    if value is None:
        return datetime.now(timezone.utc).isoformat()
    if isinstance(value, datetime):
        if value.tzinfo is None:
            raise ConversationExportManifestError("exported_at must be timezone-aware")
        return value.isoformat()
    _require_iso_datetime(value, "exported_at")
    return value


def _required_str(mapping: Mapping[str, object], field: str) -> str:
    value = _required_value(mapping, field)
    if not isinstance(value, str):
        raise ConversationExportManifestError(f"{field} must be a string")
    _require_non_empty_string(value, field)
    return value


def _optional_str(mapping: Mapping[str, object], field: str) -> str | None:
    value = mapping.get(field)
    if value is None:
        return None
    if not isinstance(value, str):
        raise ConversationExportManifestError(f"{field} must be a string")
    _require_non_empty_string(value, field)
    return value


def _required_int(mapping: Mapping[str, object], field: str) -> int:
    value = _required_value(mapping, field)
    if not isinstance(value, int) or isinstance(value, bool):
        raise ConversationExportManifestError(f"{field} must be an integer")
    _require_non_negative_int(value, field)
    return value


def _optional_int(mapping: Mapping[str, object], field: str) -> int | None:
    value = mapping.get(field)
    if value is None:
        return None
    if not isinstance(value, int) or isinstance(value, bool):
        raise ConversationExportManifestError(f"{field} must be an integer")
    _require_non_negative_int(value, field)
    return value


def _required_mapping(
    mapping: Mapping[str, object], field: str
) -> Mapping[str, object]:
    value = _required_value(mapping, field)
    if not isinstance(value, Mapping):
        raise ConversationExportManifestError(f"{field} must be a mapping")
    return value


def _deterministic_mapping(
    mapping: Mapping[str, object],
    *,
    preferred_order: tuple[str, ...] = (),
) -> dict[str, object]:
    """Return a recursively deterministic copy of a serialized mapping."""

    ordered: dict[str, object] = {}
    seen: set[str] = set()
    for key in preferred_order:
        if key in mapping:
            ordered[key] = _deterministic_value(mapping[key])
            seen.add(key)
    for key in sorted(mapping):
        if key not in seen:
            ordered[key] = _deterministic_value(mapping[key])
    return ordered


def _deterministic_value(value: object) -> object:
    if isinstance(value, Mapping):
        return _deterministic_mapping(value)
    if isinstance(value, (list, tuple)):
        return [_deterministic_value(item) for item in value]
    return value


def _required_value(mapping: Mapping[str, object], field: str) -> object:
    if field not in mapping:
        raise ConversationExportManifestError(f"missing required field: {field}")
    return mapping[field]


def _string_tuple(value: object, field: str) -> tuple[str, ...]:
    if value is None:
        return ()
    if not isinstance(value, (list, tuple)):
        raise ConversationExportManifestError(f"{field} must be a list of strings")
    items: list[str] = []
    for item in value:
        if not isinstance(item, str):
            raise ConversationExportManifestError(f"{field} must be a list of strings")
        _require_non_empty_string(item, field)
        items.append(item)
    return tuple(items)


def _require_exact(value: object, expected: object, field: str) -> None:
    if type(value) is not type(expected) or value != expected:
        raise ConversationExportManifestError(
            f"{field} must be {expected!r}, got {value!r}"
        )


def _require_non_empty_string(value: str, field: str) -> None:
    if not value.strip():
        raise ConversationExportManifestError(f"{field} must be non-empty")


def _require_non_negative_int(value: int, field: str) -> None:
    if not isinstance(value, int) or isinstance(value, bool) or value < 0:
        raise ConversationExportManifestError(f"{field} must be a non-negative integer")


def _require_optional_non_negative_int(value: int | None, field: str) -> None:
    if value is not None:
        _require_non_negative_int(value, field)


def _require_sha256(value: str, field: str) -> None:
    if re.fullmatch(r"[0-9a-f]{64}", value) is None:
        raise ConversationExportManifestError(
            f"{field} must be a lowercase SHA-256 hex digest"
        )


def _require_iso_datetime(value: str, field: str) -> None:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as err:
        raise ConversationExportManifestError(
            f"{field} must be an ISO-8601 datetime"
        ) from err
    if parsed.tzinfo is None:
        raise ConversationExportManifestError(f"{field} must be timezone-aware")


def _yaml_mapping(mapping: Mapping[str, object], *, indent: int = 0) -> str:
    lines: list[str] = []
    prefix = " " * indent
    for key, value in mapping.items():
        if isinstance(value, Mapping):
            lines.append(f"{prefix}{key}:")
            lines.append(_yaml_mapping(value, indent=indent + 2).rstrip("\n"))
        elif isinstance(value, (list, tuple)):
            lines.append(f"{prefix}{key}:")
            if value:
                for item in value:
                    lines.append(f"{prefix}  - {_yaml_scalar(item)}")
            else:
                lines[-1] = f"{prefix}{key}: []"
        else:
            lines.append(f"{prefix}{key}: {_yaml_scalar(value)}")
    return "\n".join(lines) + "\n"


def _yaml_scalar(value: object) -> str:
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
