"""File-based Codex conversation export adapter."""

from __future__ import annotations

import argparse
import dataclasses
import hashlib
import sys
from datetime import datetime
from pathlib import Path
from typing import Sequence

from lrh.conversations import export_manifest, sensitivity

SOURCE_ADAPTER = "codex_file_export"
ADAPTER_VERSION = 1
SENSITIVE_CONTENT_WARNING = "potential_sensitive_content_detected"


class CodexFileExportError(ValueError):
    """Raised when a Codex source file cannot be exported."""


@dataclasses.dataclass(frozen=True)
class CodexFileExport:
    """Markdown export and metadata produced from an explicit local file."""

    markdown: str
    manifest: export_manifest.ConversationExportManifest
    sensitivity_result: sensitivity.SensitiveScanResult | None


def convert_codex_file(
    source_path: Path,
    *,
    output_path: Path,
    force: bool = False,
    source_id: str | None = None,
    scan_sensitive: bool = True,
    exported_at: datetime | str | None = None,
) -> CodexFileExport:
    """Convert an explicit local Codex transcript/source file to Markdown."""

    source = source_path.expanduser()
    destination = output_path.expanduser()
    if not source.exists():
        raise CodexFileExportError(f"Codex source does not exist: {source}")
    if not source.is_file():
        raise CodexFileExportError(f"Codex source is not a file: {source}")
    _reject_source_output_collision(source, destination)
    if destination.exists() and not force:
        raise CodexFileExportError(f"Output already exists: {destination}")

    try:
        source_bytes = source.read_bytes()
        transcript_text = source_bytes.decode("utf-8")
    except UnicodeDecodeError as err:
        raise CodexFileExportError(
            f"Codex source is not valid UTF-8: {source}"
        ) from err

    scan_result = (
        sensitivity.scan_text_for_sensitive_findings(transcript_text)
        if scan_sensitive
        else None
    )
    manifest = build_file_export_manifest(
        transcript_text=transcript_text,
        source_sha256=hashlib.sha256(source_bytes).hexdigest(),
        source_id=_normalized_source_id(source_id),
        scan_result=scan_result,
        exported_at=exported_at,
    )
    markdown = render_codex_markdown(transcript_text, manifest)
    try:
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(markdown.encode("utf-8"))
    except OSError as err:
        raise CodexFileExportError(f"Could not write output: {destination}") from err
    return CodexFileExport(
        markdown=markdown,
        manifest=manifest,
        sensitivity_result=scan_result,
    )


def build_file_export_manifest(
    *,
    transcript_text: str,
    source_sha256: str,
    source_id: str | None = None,
    scan_result: sensitivity.SensitiveScanResult | None = None,
    exported_at: datetime | str | None = None,
) -> export_manifest.ConversationExportManifest:
    """Build manifest metadata for the file-based Codex adapter."""

    sensitivity_status = export_manifest.SENSITIVITY_UNSCANNED
    scan_metadata: dict[str, object] = {
        "status": export_manifest.SCAN_STATUS_NOT_SCANNED
    }
    warnings: list[str] = []
    if scan_result is not None:
        sensitivity_status = (
            export_manifest.SENSITIVITY_POTENTIAL
            if scan_result.findings
            else export_manifest.SENSITIVITY_NONE_DETECTED
        )
        scan_metadata = {
            "status": export_manifest.SCAN_STATUS_SCANNED,
            "scanner": "lrh_builtin_sensitive_scan",
            "scanner_version": 1,
            "finding_count": scan_result.finding_count,
            "categories": list(scan_result.categories),
        }
        if scan_result.findings:
            warnings.append(SENSITIVE_CONTENT_WARNING)

    return export_manifest.build_codex_manifest(
        transcript_text=transcript_text,
        source_sha256=source_sha256,
        exported_at=exported_at,
        source_id=_normalized_source_id(source_id),
        source_adapter=SOURCE_ADAPTER,
        adapter_version=ADAPTER_VERSION,
        sensitivity=sensitivity_status,
        sensitivity_scan=scan_metadata,
        warnings=warnings,
    )


def render_codex_markdown(
    transcript_text: str,
    manifest: export_manifest.ConversationExportManifest,
) -> str:
    """Render manifest frontmatter and transcript text as Markdown."""

    body = transcript_text if transcript_text.endswith("\n") else f"{transcript_text}\n"
    return f"{manifest.to_frontmatter()}\n{body}"


def run_convert_codex_file_cli(
    argv: Sequence[str] | None = None,
    *,
    prog: str,
) -> int:
    """Run the file-based Codex export adapter CLI."""

    parser = argparse.ArgumentParser(
        prog=prog,
        description=(
            "Convert an explicit local Codex transcript/source text file into "
            "a private, non-authoritative Markdown export artifact. This "
            "command does not inspect Codex app storage internals."
        ),
    )
    parser.add_argument(
        "input_file", help="explicit local Codex transcript/source file"
    )
    parser.add_argument("--out", required=True, help="Markdown export output path")
    parser.add_argument("--force", action="store_true", help="overwrite output path")
    parser.add_argument(
        "--source-id",
        help="optional stable Codex session/thread identifier to record in metadata",
    )
    parser.add_argument(
        "--no-scan-sensitive",
        action="store_true",
        help=(
            "skip the local heuristic sensitivity scanner and mark frontmatter "
            "sensitivity as unscanned"
        ),
    )
    args = parser.parse_args(argv)
    try:
        result = convert_codex_file(
            Path(args.input_file),
            output_path=Path(args.out),
            force=args.force,
            source_id=args.source_id,
            scan_sensitive=not args.no_scan_sensitive,
        )
    except (OSError, CodexFileExportError) as err:
        print(f"error: {err}", file=sys.stderr)
        return 1

    if result.sensitivity_result is not None and result.sensitivity_result.findings:
        finding_count = len(result.sensitivity_result.findings)
        print(
            "warning: potential sensitive content detected "
            f"by heuristic scanner ({finding_count} finding(s))",
            file=sys.stderr,
        )

    print(f"Converted Codex transcript: {args.out}")
    print("Privacy: private")
    print(f"Sensitivity: {result.manifest.sensitivity}")
    print(f"Warnings: {len(result.manifest.warnings)}")
    return 0


def _normalized_source_id(source_id: str | None) -> str | None:
    if source_id is None:
        return None
    normalized = source_id.strip()
    if not normalized:
        raise CodexFileExportError("source_id must be non-empty when provided")
    return normalized


def _reject_source_output_collision(source: Path, destination: Path) -> None:
    if destination.exists():
        try:
            if source.samefile(destination):
                raise CodexFileExportError(
                    "Codex source and output path must refer to different files"
                )
        except OSError:
            pass
    try:
        same_path = source.resolve(strict=True) == destination.resolve(strict=False)
    except OSError:
        same_path = source.absolute() == destination.absolute()
    if same_path:
        raise CodexFileExportError(
            "Codex source and output path must refer to different files"
        )
