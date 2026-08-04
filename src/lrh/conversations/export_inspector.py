"""Inspect private Codex conversation export artifacts."""

from __future__ import annotations

import argparse
import dataclasses
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Mapping, Sequence

import yaml

from lrh.conversations import export_manifest


class ConversationExportInspectionError(ValueError):
    """Raised when an export artifact cannot be inspected as a file."""


@dataclasses.dataclass(frozen=True)
class StatisticComparison:
    """Comparison between manifest statistics and artifact body statistics."""

    manifest: export_manifest.TranscriptStatistics | None
    artifact: export_manifest.TranscriptStatistics | None
    status: str
    mismatches: tuple[str, ...] = ()

    def to_mapping(self) -> dict[str, object]:
        return {
            "status": self.status,
            "mismatches": list(self.mismatches),
            "manifest": (None if self.manifest is None else self.manifest.to_mapping()),
            "artifact": (None if self.artifact is None else self.artifact.to_mapping()),
        }


@dataclasses.dataclass(frozen=True)
class SourceHashVerification:
    """Optional source-file hash verification result."""

    status: str
    expected_sha256: str | None
    actual_sha256: str | None = None
    source_path: str | None = None

    def to_mapping(self) -> dict[str, object]:
        return {
            "status": self.status,
            "expected_sha256": self.expected_sha256,
            "actual_sha256": self.actual_sha256,
            "source_path": self.source_path,
        }


@dataclasses.dataclass(frozen=True)
class ConversationExportInspection:
    """Structured inspection report for a Codex conversation export."""

    path: str
    valid: bool
    manifest_valid: bool
    manifest: export_manifest.ConversationExportManifest | None
    statistic_comparison: StatisticComparison
    source_hash: SourceHashVerification
    errors: tuple[str, ...] = ()

    def to_mapping(self) -> dict[str, object]:
        manifest_mapping = (
            None if self.manifest is None else _manifest_summary(self.manifest)
        )
        return {
            "path": self.path,
            "valid": self.valid,
            "manifest_valid": self.manifest_valid,
            "errors": list(self.errors),
            "manifest": manifest_mapping,
            "privacy": None if self.manifest is None else self.manifest.privacy,
            "authority": None if self.manifest is None else self.manifest.authority,
            "sensitivity": None if self.manifest is None else self.manifest.sensitivity,
            "warning_count": (
                0 if self.manifest is None else len(self.manifest.warnings)
            ),
            "transcript_statistics": self.statistic_comparison.to_mapping(),
            "source_hash": self.source_hash.to_mapping(),
        }


def inspect_export(
    export_path: Path,
    *,
    source_path: Path | None = None,
) -> ConversationExportInspection:
    """Inspect a Codex Markdown export artifact without echoing transcript text."""

    path = export_path.expanduser()
    if not path.exists():
        raise ConversationExportInspectionError(f"export does not exist: {path}")
    if not path.is_file():
        raise ConversationExportInspectionError(f"export is not a file: {path}")
    try:
        raw_bytes = path.read_bytes()
    except OSError as err:
        raise ConversationExportInspectionError(
            f"could not read export: {path}"
        ) from err
    try:
        text = raw_bytes.decode("utf-8")
    except UnicodeDecodeError as err:
        raise ConversationExportInspectionError(
            f"export is not valid UTF-8: {path}"
        ) from err

    manifest: export_manifest.ConversationExportManifest | None = None
    manifest_valid = False
    errors: list[str] = []
    transcript_text = ""
    try:
        manifest_text, body = _split_frontmatter(text)
        loaded = yaml.safe_load(manifest_text)
        if not isinstance(loaded, Mapping):
            raise export_manifest.ConversationExportManifestError(
                "frontmatter must be a mapping"
            )
        manifest = export_manifest.ConversationExportManifest.from_mapping(loaded)
        manifest_valid = True
        transcript_text = _artifact_transcript_body(body)
    except (
        ValueError,
        yaml.YAMLError,
        export_manifest.ConversationExportManifestError,
    ) as err:
        errors.append(f"manifest: {err}")

    statistic_comparison = _compare_statistics(manifest, transcript_text)
    if statistic_comparison.status == "mismatch":
        errors.append("transcript_statistics: artifact body does not match manifest")

    source_hash = _verify_source_hash(manifest, source_path)
    if source_hash.status in {
        "mismatch",
        "source_missing",
        "source_not_file",
        "source_unreadable",
    }:
        errors.append(f"source_hash: {source_hash.status}")
    valid = manifest_valid and not errors
    return ConversationExportInspection(
        path=str(path),
        valid=valid,
        manifest_valid=manifest_valid,
        manifest=manifest,
        statistic_comparison=statistic_comparison,
        source_hash=source_hash,
        errors=tuple(errors),
    )


def format_json(inspection: ConversationExportInspection) -> str:
    """Format inspection as deterministic JSON."""

    return json.dumps(inspection.to_mapping(), indent=2, sort_keys=True) + "\n"


def format_text(inspection: ConversationExportInspection) -> str:
    """Format inspection as concise text without transcript content."""

    lines = [
        f"Export: {inspection.path}",
        f"Valid: {'yes' if inspection.valid else 'no'}",
        f"Manifest: {'valid' if inspection.manifest_valid else 'invalid'}",
    ]
    manifest = inspection.manifest
    if manifest is not None:
        lines.extend(
            [
                f"Kind: {manifest.kind}",
                f"Schema version: {manifest.schema_version}",
                f"Source tool: {manifest.source_tool}",
                f"Source adapter: {manifest.source_adapter}",
                f"Privacy: {manifest.privacy}",
                f"Authority: {manifest.authority}",
                f"Sensitivity: {manifest.sensitivity}",
                f"Warnings: {len(manifest.warnings)}",
            ]
        )
    stats = inspection.statistic_comparison
    lines.append(f"Transcript statistics: {stats.status}")
    if stats.artifact is not None:
        lines.extend(
            [
                f"  bytes: {stats.artifact.byte_count}",
                f"  characters: {stats.artifact.character_count}",
                f"  lines: {stats.artifact.line_count}",
            ]
        )
    for mismatch in stats.mismatches:
        lines.append(f"  mismatch: {mismatch}")
    source_hash = inspection.source_hash
    lines.append(f"Source hash: {source_hash.status}")
    if source_hash.expected_sha256 is not None:
        lines.append(f"  expected: {source_hash.expected_sha256}")
    if source_hash.actual_sha256 is not None:
        lines.append(f"  actual: {source_hash.actual_sha256}")
    if inspection.errors:
        lines.append("Errors:")
        for error in inspection.errors:
            lines.append(f"  - {error}")
    return "\n".join(lines) + "\n"


def run_inspect_export_cli(
    argv: Sequence[str] | None = None,
    *,
    prog: str,
) -> int:
    """Run the Codex export inspector CLI."""

    parser = argparse.ArgumentParser(
        prog=prog,
        description=(
            "Inspect a private, non-authoritative Codex conversation export "
            "Markdown artifact without printing transcript content."
        ),
    )
    parser.add_argument("export", help="Markdown export artifact to inspect")
    parser.add_argument(
        "--source",
        help="optional original source file for SHA-256 verification",
    )
    parser.add_argument(
        "--format",
        choices=("text", "json"),
        default="text",
        help="output format (default: text)",
    )
    args = parser.parse_args(argv)
    try:
        inspection = inspect_export(
            Path(args.export),
            source_path=None if args.source is None else Path(args.source),
        )
    except ConversationExportInspectionError as err:
        print(f"error: {err}", file=sys.stderr)
        return 2

    if args.format == "json":
        print(format_json(inspection), end="")
    else:
        print(format_text(inspection), end="")
    return 0 if inspection.valid else 1


def _manifest_summary(
    manifest: export_manifest.ConversationExportManifest,
) -> dict[str, object]:
    return {
        "kind": manifest.kind,
        "schema_version": manifest.schema_version,
        "source_tool": manifest.source_tool,
        "source_adapter": manifest.source_adapter,
        "source_id_present": manifest.source_id is not None,
        "adapter_version": manifest.adapter_version,
        "exported_at": manifest.exported_at,
        "privacy": manifest.privacy,
        "authority": manifest.authority,
        "sensitivity": manifest.sensitivity,
        "sensitivity_scan": _sensitivity_scan_summary(manifest.sensitivity_scan),
        "warning_count": len(manifest.warnings),
    }


def _sensitivity_scan_summary(scan: Mapping[str, object]) -> dict[str, object]:
    categories = scan.get("categories")
    return {
        "status": scan.get("status"),
        "scanner": scan.get("scanner"),
        "scanner_version": scan.get("scanner_version"),
        "finding_count": scan.get("finding_count"),
        "category_count": len(categories) if isinstance(categories, list) else None,
    }


def _split_frontmatter(text: str) -> tuple[str, str]:
    match = re.match(
        r"\A---\r?\n(?P<frontmatter>.*?)\r?\n---[ \t]*\r?\n?(?P<body>.*)\Z",
        text,
        re.DOTALL,
    )
    if match is None:
        raise ValueError("markdown file must begin with YAML frontmatter")
    return match.group("frontmatter"), match.group("body")


def _artifact_transcript_body(body: str) -> str:
    return body[1:] if body.startswith("\n") else body


def _compare_statistics(
    manifest: export_manifest.ConversationExportManifest | None,
    transcript_text: str,
) -> StatisticComparison:
    if manifest is None:
        return StatisticComparison(None, None, "not_available")
    manifest_stats = manifest.transcript_statistics
    artifact_stats = export_manifest.statistics_for_text(transcript_text)
    exact_mismatches = _statistic_mismatches(manifest_stats, artifact_stats)
    if not exact_mismatches:
        return StatisticComparison(manifest_stats, artifact_stats, "match")

    if (
        transcript_text.endswith("\n")
        and artifact_stats.line_count == manifest_stats.line_count
    ):
        trimmed_text = transcript_text[:-1]
        trimmed_stats = export_manifest.statistics_for_text(trimmed_text)
        trimmed_mismatches = _statistic_mismatches(manifest_stats, trimmed_stats)
        if not trimmed_mismatches:
            return StatisticComparison(manifest_stats, trimmed_stats, "match")

    return StatisticComparison(
        manifest_stats,
        artifact_stats,
        "mismatch",
        exact_mismatches,
    )


def _statistic_mismatches(
    manifest_stats: export_manifest.TranscriptStatistics,
    artifact_stats: export_manifest.TranscriptStatistics,
) -> tuple[str, ...]:
    mismatches: list[str] = []
    for field in ("byte_count", "character_count", "line_count"):
        if getattr(manifest_stats, field) != getattr(artifact_stats, field):
            mismatches.append(field)
    return tuple(mismatches)


def _verify_source_hash(
    manifest: export_manifest.ConversationExportManifest | None,
    source_path: Path | None,
) -> SourceHashVerification:
    expected = None if manifest is None else manifest.source_sha256
    if source_path is None:
        return SourceHashVerification("not_supplied", expected)
    source = source_path.expanduser()
    if not source.exists():
        return SourceHashVerification(
            "source_missing", expected, source_path=str(source)
        )
    if not source.is_file():
        return SourceHashVerification(
            "source_not_file", expected, source_path=str(source)
        )
    try:
        actual = hashlib.sha256(source.read_bytes()).hexdigest()
    except OSError:
        return SourceHashVerification(
            "source_unreadable", expected, source_path=str(source)
        )
    if expected is None:
        return SourceHashVerification(
            "not_available",
            expected,
            actual_sha256=actual,
            source_path=str(source),
        )
    return SourceHashVerification(
        "match" if actual == expected else "mismatch",
        expected,
        actual_sha256=actual,
        source_path=str(source),
    )
