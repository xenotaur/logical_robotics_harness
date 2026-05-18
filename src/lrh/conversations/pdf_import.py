"""ChatGPT PDF conversation import helpers."""

import dataclasses
import datetime
import hashlib
import json
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
    if _has_trailer_encrypt_key(raw_bytes):
        raise PdfImportError(f"Encrypted PDF is not supported: {pdf_path}")

    return PdfConversationSource(
        path=pdf_path,
        source_tool=SOURCE_TOOL,
        source_adapter=SOURCE_ADAPTER,
        sha256=hashlib.sha256(raw_bytes).hexdigest(),
        page_count=_extract_page_count(raw_bytes),
    )


def _has_trailer_encrypt_key(raw_bytes: bytes) -> bool:
    for trailer_match in re.finditer(
        rb"trailer\s*<<(.*?)>>", raw_bytes, flags=re.DOTALL
    ):
        trailer_body = trailer_match.group(1)
        if re.search(rb"/Encrypt(?![#A-Za-z0-9_.+-])", trailer_body):
            return True
    return False


def _extract_page_count(raw_bytes: bytes) -> int:
    counts = [
        int(match.group(1))
        for match in re.finditer(
            rb"/Type\s*/Pages\b(?:(?!endobj).)*?/Count\s+(\d+)",
            raw_bytes,
            flags=re.DOTALL,
        )
    ]
    if counts:
        return max(counts)
    return len(re.findall(rb"/Type\s*/Page\b", raw_bytes))


def _extract_pdf_text(
    pdf_path: pathlib.Path, *, include_page_breaks: bool
) -> tuple[str, str]:
    raw = pdf_path.read_bytes().decode("latin-1", errors="ignore")
    chunks = _extract_text_showing_chunks(raw)
    if not chunks:
        raise PdfImportError(f"No extractable text found in PDF: {pdf_path}")

    combined = "\n".join(chunks).replace("\r\n", "\n").replace("\r", "\n")
    if include_page_breaks:
        combined = combined.replace("\n\f\n", "\n\n---\n\n")
    combined = combined.strip()
    if not combined:
        raise PdfImportError(f"Empty extracted PDF transcript for file: {pdf_path}")
    first = next((line.strip() for line in combined.splitlines() if line.strip()), "")
    return (first or pdf_path.stem), combined


def _extract_text_showing_chunks(raw: str) -> list[str]:
    tokens = _parse_pdf_tokens(raw)
    chunks: list[str] = []
    for index, token in enumerate(tokens):
        previous = tokens[index - 1] if index else None
        if token == "Tj" and isinstance(previous, _PdfString):
            chunks.append(previous.text)
        elif token == "TJ" and isinstance(previous, _PdfArray):
            array_text = "".join(
                item.text for item in previous.items if isinstance(item, _PdfString)
            )
            if array_text:
                chunks.append(array_text)
    return chunks


@dataclasses.dataclass(frozen=True)
class _PdfString:
    text: str


@dataclasses.dataclass(frozen=True)
class _PdfArray:
    items: tuple[object, ...]


def _parse_pdf_tokens(
    raw: str, start: int = 0, stop: str | None = None
) -> list[object]:
    tokens: list[object] = []
    index = start
    while index < len(raw):
        char = raw[index]
        if stop is not None and char == stop:
            return tokens
        if char.isspace():
            index += 1
            continue
        if char == "%":
            index = raw.find("\n", index)
            if index == -1:
                return tokens
            continue
        if char == "(":
            value, index = _parse_pdf_literal_string(raw, index)
            tokens.append(_PdfString(value))
            continue
        if char == "[":
            array, index = _parse_pdf_array(raw, index)
            tokens.append(array)
            continue
        if char in "]<>{}/":
            index += 1
            continue

        end = index
        while end < len(raw) and not raw[end].isspace() and raw[end] not in "[]<>{}/()":
            end += 1
        tokens.append(raw[index:end])
        index = end
    return tokens


def _parse_pdf_array(raw: str, start: int) -> tuple[_PdfArray, int]:
    items: list[object] = []
    index = start + 1
    while index < len(raw):
        char = raw[index]
        if char.isspace():
            index += 1
            continue
        if char == "]":
            return _PdfArray(tuple(items)), index + 1
        if char == "(":
            value, index = _parse_pdf_literal_string(raw, index)
            items.append(_PdfString(value))
            continue
        if char == "[":
            nested, index = _parse_pdf_array(raw, index)
            items.append(nested)
            continue
        end = index
        while end < len(raw) and not raw[end].isspace() and raw[end] not in "[]()":
            end += 1
        items.append(raw[index:end])
        index = end
    return _PdfArray(tuple(items)), index


def _parse_pdf_literal_string(raw: str, start: int) -> tuple[str, int]:
    chars: list[str] = []
    index = start + 1
    depth = 1
    while index < len(raw):
        char = raw[index]
        if char == "\\":
            unescaped, index = _parse_pdf_escape(raw, index)
            chars.append(unescaped)
            continue
        if char == "(":
            depth += 1
            chars.append(char)
            index += 1
            continue
        if char == ")":
            depth -= 1
            index += 1
            if depth == 0:
                return "".join(chars), index
            chars.append(char)
            continue
        chars.append(char)
        index += 1
    return "".join(chars), index


def _parse_pdf_escape(raw: str, start: int) -> tuple[str, int]:
    if start + 1 >= len(raw):
        return "", start + 1

    char = raw[start + 1]
    escapes = {
        "n": "\n",
        "r": "\r",
        "t": "\t",
        "b": "\b",
        "f": "\f",
        "(": "(",
        ")": ")",
        "\\": "\\",
    }
    if char in escapes:
        return escapes[char], start + 2
    if char in "\n\r":
        index = start + 2
        if char == "\r" and index < len(raw) and raw[index] == "\n":
            index += 1
        return "", index
    if char in "01234567":
        end = start + 2
        while end < len(raw) and end < start + 4 and raw[end] in "01234567":
            end += 1
        return chr(int(raw[start + 1 : end], 8)), end
    return char, start + 2


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
        return json.dumps(value, ensure_ascii=False)
    if isinstance(value, bool):
        return "true" if value else "false"
    if value is None:
        return "null"
    return str(value)
