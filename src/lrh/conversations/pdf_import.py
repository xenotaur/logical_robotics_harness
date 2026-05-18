"""Local ChatGPT PDF conversation transcript import helpers."""

from __future__ import annotations

import argparse
import dataclasses
import hashlib
import re
import sys
import zlib
from datetime import datetime, timezone
from pathlib import Path
from typing import Sequence

from lrh.conversations import sensitivity

ADAPTER_VERSION = 1


class PdfImportError(ValueError):
    """Raised when a PDF cannot be converted by the lightweight importer."""


@dataclasses.dataclass(frozen=True)
class PdfExtraction:
    """Text and metadata extracted from a supported local PDF."""

    text: str
    page_count: int | None
    warnings: tuple[str, ...]


@dataclasses.dataclass(frozen=True)
class ConversationPdfTranscript:
    """Markdown transcript and metadata produced from a local PDF."""

    markdown: str
    extraction: PdfExtraction
    sensitivity_result: sensitivity.SensitiveScanResult | None


def convert_pdf_file(
    input_path: Path,
    *,
    output_path: Path | None = None,
    force: bool = False,
    include_frontmatter: bool = True,
    scan_sensitive: bool = True,
) -> ConversationPdfTranscript:
    """Convert a local text-layer PDF into a Markdown conversation transcript."""

    source_path = input_path.expanduser()
    if not source_path.exists():
        raise PdfImportError(f"PDF input does not exist: {source_path}")
    if not source_path.is_file():
        raise PdfImportError(f"PDF input is not a file: {source_path}")
    pdf_bytes = source_path.read_bytes()
    source_hash = hashlib.sha256(pdf_bytes).hexdigest()
    extraction = extract_pdf_text(pdf_bytes)
    scan_result = (
        sensitivity.scan_text_for_sensitive_findings(extraction.text)
        if scan_sensitive
        else None
    )
    markdown = render_markdown_transcript(
        extraction=extraction,
        source_file=source_path.name,
        source_file_sha256=source_hash,
        include_frontmatter=include_frontmatter,
        scan_result=scan_result,
        scan_sensitive=scan_sensitive,
    )
    if output_path is not None:
        destination = output_path.expanduser()
        if destination.exists() and not force:
            raise PdfImportError(f"Output already exists: {destination}")
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(markdown, encoding="utf-8")
    return ConversationPdfTranscript(
        markdown=markdown,
        extraction=extraction,
        sensitivity_result=scan_result,
    )


def extract_pdf_text(pdf_bytes: bytes) -> PdfExtraction:
    """Extract text from simple PDF text-showing operators.

    This intentionally remains a lightweight, dependency-free text-layer extractor.
    It handles PDF literal-string escapes, `Tj` string operands, and `TJ` array
    operands in raw and Flate-decoded streams. It is not OCR and does not claim
    complete PDF layout reconstruction.
    """

    if not pdf_bytes.startswith(b"%PDF-"):
        raise PdfImportError("Input is not a PDF file")
    if _has_trailer_encrypt_key(pdf_bytes):
        raise PdfImportError("Encrypted PDF is not supported")

    warnings: list[str] = []
    stream_payloads = _extract_stream_payloads(pdf_bytes)
    if not stream_payloads:
        warnings.append("no_pdf_streams_found")
        stream_payloads = [pdf_bytes]

    chunks: list[str] = []
    for payload in stream_payloads:
        chunks.extend(_extract_text_showing_chunks(payload))
    text = _normalize_extracted_text(chunks)
    if not text:
        raise PdfImportError("PDF does not appear to contain an extractable text layer")

    page_count = _extract_page_count(pdf_bytes)
    if page_count is None:
        warnings.append("page_count_unknown")
    warnings.append("turn_boundaries_not_inferred")
    return PdfExtraction(text=text, page_count=page_count, warnings=tuple(warnings))


def render_markdown_transcript(
    *,
    extraction: PdfExtraction,
    source_file: str,
    source_file_sha256: str,
    include_frontmatter: bool = True,
    scan_result: sensitivity.SensitiveScanResult | None = None,
    scan_sensitive: bool = True,
) -> str:
    """Render extracted PDF text as a Markdown transcript."""

    body = extraction.text.strip() + "\n"
    if not include_frontmatter:
        return body

    sensitivity_status = "unscanned"
    scan_metadata: dict[str, object] = {"status": "not_scanned"}
    if scan_result is not None:
        sensitivity_status = "potential" if scan_result.findings else "none_detected"
        categories = sorted({finding.category for finding in scan_result.findings})
        scan_metadata = {
            "status": "scanned",
            "scanner": "lrh_builtin_sensitive_scan",
            "scanner_version": 1,
            "finding_count": len(scan_result.findings),
            "categories": categories,
        }
    elif scan_sensitive:
        scan_metadata = {"status": "failed_or_unavailable"}

    metadata: dict[str, object] = {
        "kind": "lrh_conversation_transcript",
        "schema_version": 1,
        "source_format": "pdf",
        "source_tool": "chatgpt",
        "source_adapter": "chatgpt_pdf",
        "privacy": "private",
        "sensitivity": sensitivity_status,
        "sensitivity_scan": scan_metadata,
        "authority": "non_authoritative_context",
        "source_file": source_file,
        "source_file_sha256": source_file_sha256,
        "page_count": extraction.page_count,
        "extracted_at": datetime.now(timezone.utc).isoformat(),
        "adapter_version": ADAPTER_VERSION,
        "warnings": list(extraction.warnings),
    }
    return f"---\n{_yaml_mapping(metadata)}---\n\n{body}"


def _extract_stream_payloads(pdf_bytes: bytes) -> list[bytes]:
    payloads: list[bytes] = []
    for match in re.finditer(rb"stream\r?\n(.*?)\r?\nendstream", pdf_bytes, re.DOTALL):
        stream_start = match.start()
        header = pdf_bytes[max(0, stream_start - 300) : stream_start]
        payload = match.group(1)
        if b"/FlateDecode" in header:
            try:
                payload = zlib.decompress(payload)
            except zlib.error:
                continue
        payloads.append(payload)
    return payloads


def _extract_text_showing_chunks(content: bytes) -> list[str]:
    chunks: list[str] = []
    index = 0
    while index < len(content):
        byte = content[index]
        if byte == ord("("):
            raw_string, next_index = _parse_pdf_literal_string(content, index)
            operator_index = _skip_pdf_whitespace(content, next_index)
            if content[operator_index : operator_index + 2] == b"Tj":
                chunks.append(_decode_pdf_string(raw_string))
                index = operator_index + 2
                continue
            index = next_index
            continue
        if byte == ord("["):
            raw_strings, next_index = _parse_pdf_array_strings(content, index)
            operator_index = _skip_pdf_whitespace(content, next_index)
            if content[operator_index : operator_index + 2] == b"TJ":
                chunks.append("".join(_decode_pdf_string(part) for part in raw_strings))
                index = operator_index + 2
                continue
            index = next_index
            continue
        index += 1
    return chunks


def _parse_pdf_array_strings(content: bytes, start: int) -> tuple[list[bytes], int]:
    strings: list[bytes] = []
    depth = 1
    index = start + 1
    while index < len(content) and depth > 0:
        byte = content[index]
        if byte == ord("("):
            raw_string, index = _parse_pdf_literal_string(content, index)
            strings.append(raw_string)
            continue
        if byte == ord("["):
            depth += 1
        elif byte == ord("]"):
            depth -= 1
        index += 1
    return strings, index


def _parse_pdf_literal_string(content: bytes, start: int) -> tuple[bytes, int]:
    result = bytearray()
    depth = 1
    index = start + 1
    while index < len(content) and depth > 0:
        byte = content[index]
        if byte == ord("\\"):
            if index + 1 < len(content):
                result.append(byte)
                index += 1
                result.append(content[index])
            index += 1
            continue
        if byte == ord("("):
            depth += 1
            result.append(byte)
        elif byte == ord(")"):
            depth -= 1
            if depth > 0:
                result.append(byte)
        else:
            result.append(byte)
        index += 1
    return bytes(result), index


def _decode_pdf_string(raw: bytes) -> str:
    unescaped = _unescape_pdf_text(raw)
    for encoding in ("utf-8", "utf-16-be", "latin-1"):
        try:
            return unescaped.decode(encoding)
        except UnicodeDecodeError:
            continue
    return unescaped.decode("latin-1", errors="replace")


def _unescape_pdf_text(raw: bytes) -> bytes:
    result = bytearray()
    index = 0
    escapes = {
        ord("n"): b"\n",
        ord("r"): b"\r",
        ord("t"): b"\t",
        ord("b"): b"\b",
        ord("f"): b"\f",
        ord("("): b"(",
        ord(")"): b")",
        ord("\\"): b"\\",
    }
    while index < len(raw):
        byte = raw[index]
        if byte != ord("\\"):
            result.append(byte)
            index += 1
            continue
        if index + 1 >= len(raw):
            index += 1
            continue
        next_byte = raw[index + 1]
        if next_byte in (ord("\n"), ord("\r")):
            index += 2
            if next_byte == ord("\r") and index < len(raw) and raw[index] == ord("\n"):
                index += 1
            continue
        if ord("0") <= next_byte <= ord("7"):
            end = index + 1
            while end < min(index + 4, len(raw)) and ord("0") <= raw[end] <= ord("7"):
                end += 1
            result.append(int(raw[index + 1 : end], 8))
            index = end
            continue
        replacement = escapes.get(next_byte)
        if replacement is None:
            result.append(next_byte)
        else:
            result.extend(replacement)
        index += 2
    return bytes(result)


def _skip_pdf_whitespace(content: bytes, index: int) -> int:
    while index < len(content) and content[index] in b"\x00\t\n\f\r ":
        index += 1
    return index


def _normalize_extracted_text(chunks: Sequence[str]) -> str:
    lines = [chunk.strip() for chunk in chunks if chunk.strip()]
    return "\n".join(lines).strip()


def _has_trailer_encrypt_key(pdf_bytes: bytes) -> bool:
    trailer_key = b"trailer"
    index = 0
    while True:
        trailer_index = pdf_bytes.find(trailer_key, index)
        if trailer_index < 0:
            return False
        dict_start = pdf_bytes.find(b"<<", trailer_index + len(trailer_key))
        if dict_start < 0:
            return False
        dict_end = pdf_bytes.find(b">>", dict_start + 2)
        if dict_end < 0:
            return False
        trailer_dict = pdf_bytes[dict_start : dict_end + 2]
        if re.search(rb"(?<![A-Za-z0-9_])\/Encrypt(?![A-Za-z0-9_])", trailer_dict):
            return True
        index = dict_end + 2


def _extract_page_count(pdf_bytes: bytes) -> int | None:
    patterns = (
        rb"/Type\s*/Pages\b(?:(?!endobj).)*?/Count\s+(\d+)",
        rb"/Count\s+(\d+)(?:(?!endobj).)*?/Type\s*/Pages\b",
    )
    counts: list[int] = []
    for pattern in patterns:
        for match in re.finditer(pattern, pdf_bytes, re.DOTALL):
            counts.append(int(match.group(1)))
    if not counts:
        return None
    return max(counts)


def _yaml_mapping(mapping: dict[str, object], *, indent: int = 0) -> str:
    lines: list[str] = []
    prefix = " " * indent
    for key, value in mapping.items():
        if isinstance(value, dict):
            lines.append(f"{prefix}{key}:")
            lines.append(_yaml_mapping(value, indent=indent + 2).rstrip("\n"))
        elif isinstance(value, list):
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


def run_convert_pdf_cli(argv: Sequence[str] | None = None, *, prog: str) -> int:
    parser = argparse.ArgumentParser(prog=prog)
    parser.add_argument("input_pdf", help="local ChatGPT/browser Save-as-PDF input")
    parser.add_argument("--out", required=True, help="Markdown transcript output path")
    parser.add_argument("--force", action="store_true", help="overwrite output path")
    parser.add_argument(
        "--no-frontmatter",
        action="store_true",
        help="write only extracted Markdown text",
    )
    parser.add_argument(
        "--no-scan-sensitive",
        action="store_true",
        help="skip the local deterministic sensitivity scanner",
    )
    args = parser.parse_args(argv)
    try:
        result = convert_pdf_file(
            Path(args.input_pdf),
            output_path=Path(args.out),
            force=args.force,
            include_frontmatter=not args.no_frontmatter,
            scan_sensitive=not args.no_scan_sensitive,
        )
    except PdfImportError as err:
        print(f"error: {err}", file=sys.stderr)
        return 1
    print(f"wrote {args.out}")
    for warning in result.extraction.warnings:
        print(f"warning: {warning}", file=sys.stderr)
    return 0
