"""ChatGPT PDF conversation import helpers."""

import dataclasses
import datetime
import hashlib
import pathlib
import re

from lrh.conversations import sensitivity

SOURCE_TOOL = "chatgpt"
SOURCE_ADAPTER = "chatgpt_pdf"
AUTHORITY = "non_authoritative_context"
SCANNER_NAME = "lrh_builtin_sensitive_scan"
SCANNER_VERSION = 1
ADAPTER_VERSION = 1
PDFCROWD_FOOTER = "Printed using ChatGPT to PDF, powered by PDFCrowd HTML to PDF API."


class PdfImportError(ValueError):
    """Raised when a ChatGPT PDF transcript cannot be imported."""


@dataclasses.dataclass(frozen=True)
class PdfConversationSource:
    path: pathlib.Path
    source_tool: str
    source_adapter: str
    sha256: str
    page_count: int


@dataclasses.dataclass(frozen=True)
class ConversionWarning:
    code: str
    message: str


@dataclasses.dataclass(frozen=True)
class MarkdownTranscript:
    title: str
    frontmatter: dict[str, object]
    body: str
    warnings: tuple[ConversionWarning, ...]
    sensitivity: sensitivity.SensitiveScanResult | None

    def to_markdown(self) -> str:
        return "\n".join(
            ("---", _yaml_dump(self.frontmatter), "---", "", self.body, "")
        )


def convert_chatgpt_pdf_to_markdown(
    pdf_path: pathlib.Path,
    *,
    privacy: str = "private",
    scan_sensitive: bool = True,
    include_page_breaks: bool = False,
    extracted_at: datetime.datetime | None = None,
) -> MarkdownTranscript:
    source = _build_source(pdf_path)
    title, extracted_text = _extract_pdf_text(
        source.path, include_page_breaks=include_page_breaks
    )
    cleaned_text = _clean_extracted_text(extracted_text, title)
    if not cleaned_text.strip():
        raise PdfImportError(
            f"No non-empty transcript text found in PDF: {source.path}"
        )

    warnings: list[ConversionWarning] = []
    sensitivity_status = "unscanned"
    scan_metadata: dict[str, object] = {"status": "not_run"}
    scan_result: sensitivity.SensitiveScanResult | None = None
    if scan_sensitive:
        scan_result = sensitivity.scan_text_for_sensitive_findings(cleaned_text)
        if scan_result.finding_count:
            sensitivity_status = "potential"
            warnings.append(
                ConversionWarning(
                    code="sensitivity_potential",
                    message=(
                        "Potential sensitive content detected; "
                        "review before sharing."
                    ),
                )
            )
        else:
            sensitivity_status = "none_detected"
        scan_metadata = {
            "status": "scanned",
            "scanner": SCANNER_NAME,
            "scanner_version": SCANNER_VERSION,
            "finding_count": scan_result.finding_count,
            "categories": list(scan_result.categories),
        }

    frontmatter = {
        "kind": "lrh_conversation_transcript",
        "schema_version": 1,
        "source_format": "pdf",
        "source_tool": source.source_tool,
        "source_adapter": source.source_adapter,
        "privacy": privacy,
        "sensitivity": sensitivity_status,
        "sensitivity_scan": scan_metadata,
        "authority": AUTHORITY,
        "source_file": source.path.name,
        "source_file_sha256": source.sha256,
        "page_count": source.page_count,
        "extracted_at": (
            extracted_at or datetime.datetime.now(datetime.UTC)
        ).isoformat(),
        "adapter_version": ADAPTER_VERSION,
        "warnings": [{"code": w.code, "message": w.message} for w in warnings],
    }

    body = "\n".join(
        (
            f"# {title}",
            "",
            "> Imported from a ChatGPT PDF export. Review before publication.",
            "",
            "## Extraction Notes",
            f"- Source file: `{source.path.name}`",
            f"- Source adapter: `{SOURCE_ADAPTER}`",
            "",
            "## Extracted Transcript",
            cleaned_text,
            "",
        )
    )
    return MarkdownTranscript(
        title=title,
        frontmatter=frontmatter,
        body=body,
        warnings=tuple(warnings),
        sensitivity=scan_result,
    )


def _build_source(pdf_path: pathlib.Path) -> PdfConversationSource:
    if not pdf_path.exists() or not pdf_path.is_file():
        raise PdfImportError(f"PDF file does not exist: {pdf_path}")
    raw_bytes = pdf_path.read_bytes()
    if not raw_bytes.startswith(b"%PDF-"):
        raise PdfImportError(f"Unreadable PDF: {pdf_path}")
    if b"/Encrypt" in raw_bytes:
        raise PdfImportError(f"Encrypted PDF is not supported: {pdf_path}")
    return PdfConversationSource(
        path=pdf_path,
        source_tool=SOURCE_TOOL,
        source_adapter=SOURCE_ADAPTER,
        sha256=hashlib.sha256(raw_bytes).hexdigest(),
        page_count=max(1, len(re.findall(rb"/Type\s*/Page\b", raw_bytes))),
    )


def _extract_pdf_text(
    pdf_path: pathlib.Path, *, include_page_breaks: bool
) -> tuple[str, str]:
    raw = pdf_path.read_bytes().decode("latin-1", errors="ignore")
    matches = re.findall(r"\((.*?)\)\s*Tj", raw, flags=re.DOTALL)
    chunks = [_unescape_pdf_text(token) for token in matches if token]
    if not chunks:
        raise PdfImportError(f"No extractable text found in PDF: {pdf_path}")
    combined = "\n".join(chunks).replace("\r\n", "\n")
    combined = combined.replace("\\n", "\n")
    if include_page_breaks:
        combined = combined.replace("\n\f\n", "\n\n---\n\n")
    combined = combined.strip()
    if not combined:
        raise PdfImportError(f"Empty extracted PDF transcript for file: {pdf_path}")
    first = next((line.strip() for line in combined.splitlines() if line.strip()), "")
    return (first or pdf_path.stem), combined


def _unescape_pdf_text(text: str) -> str:
    return text.replace(r"\(", "(").replace(r"\)", ")").replace(r"\\", "\\")


def _clean_extracted_text(text: str, title: str) -> str:
    cleaned_lines: list[str] = []
    title_seen = False
    for raw_line in text.splitlines():
        line = raw_line.rstrip()
        stripped = line.strip()
        if not stripped:
            cleaned_lines.append("")
            continue
        if stripped == PDFCROWD_FOOTER or re.fullmatch(r"\d+/\d+", stripped):
            continue
        if stripped == title and title_seen:
            continue
        if stripped == title:
            title_seen = True
        cleaned_lines.append(line)
    return re.sub(r"\n{3,}", "\n\n", "\n".join(cleaned_lines)).strip()


def _yaml_dump(data: dict[str, object]) -> str:
    return "\n".join(_yaml_lines(data, 0))


def _yaml_lines(value: object, indent: int) -> list[str]:
    prefix = " " * indent
    if isinstance(value, dict):
        lines: list[str] = []
        for key, nested_value in value.items():
            if isinstance(nested_value, (dict, list)):
                lines.append(f"{prefix}{key}:")
                lines.extend(_yaml_lines(nested_value, indent + 2))
            else:
                lines.append(f"{prefix}{key}: {_yaml_scalar(nested_value)}")
        return lines
    if isinstance(value, list):
        lines = []
        for item in value:
            if isinstance(item, (dict, list)):
                lines.append(f"{prefix}-")
                lines.extend(_yaml_lines(item, indent + 2))
            else:
                lines.append(f"{prefix}- {_yaml_scalar(item)}")
        return lines
    return [f"{prefix}{_yaml_scalar(value)}"]


def _yaml_scalar(value: object) -> str:
    if isinstance(value, str):
        if value == "" or any(ch in value for ch in [":", "#", "\n", '"']):
            escaped = value.replace("\\", "\\\\").replace('"', '\\"')
            return f'"{escaped}"'
        return value
    if isinstance(value, bool):
        return "true" if value else "false"
    if value is None:
        return "null"
    return str(value)
