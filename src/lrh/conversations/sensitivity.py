"""Local heuristic sensitivity scanner for conversation transcripts.

This module provides deterministic, local checks that flag potential sensitive
content in imported conversations. The scanner is a safety rail, not a
compliance system: it does not certify that text is safe, does not redact the
source content, and does not replace human review before public export.
"""

import bisect
import dataclasses
import re

STATUS_NONE_DETECTED = "none_detected"
STATUS_POTENTIAL = "potential"

SEVERITY_MEDIUM = "medium"
SEVERITY_HIGH = "high"

CONFIDENCE_MEDIUM = "medium"
CONFIDENCE_HIGH = "high"


@dataclasses.dataclass(frozen=True)
class SensitiveFinding:
    """A single potential sensitive-content finding."""

    category: str
    severity: str
    confidence: str
    line_number: int | None
    start_offset: int | None
    end_offset: int | None
    rule_id: str
    redacted_preview: str


@dataclasses.dataclass(frozen=True)
class SensitiveScanResult:
    """Result of scanning text for potential sensitive content."""

    status: str
    finding_count: int
    categories: tuple[str, ...]
    findings: tuple[SensitiveFinding, ...]


@dataclasses.dataclass(frozen=True)
class _Rule:
    rule_id: str
    category: str
    severity: str
    confidence: str
    pattern: re.Pattern[str]
    preview: str


_EMAIL_PATTERN = re.compile(
    r"(?<![\w.+-])[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]*[A-Za-z0-9]\.[A-Za-z]{2,}\b"
)
_SSN_PATTERN = re.compile(r"(?<!\d)\d{3}-\d{2}-\d{4}(?!\d)")
_PRIVATE_KEY_PATTERN = re.compile(
    r"-----BEGIN [A-Z ]*PRIVATE KEY-----.*?-----END [A-Z ]*PRIVATE KEY-----",
    re.DOTALL,
)
_SECRET_ASSIGNMENT_PATTERN = re.compile(
    r"(?i)\b(?P<key>password|passwd|secret|token|api_key|apikey|access_key|private_key)\b"
    r"\s*(?:=|:|:=)\s*"
    r"(?P<quote>['\"]?)"
    r"(?P<value>[^\s'\"]{4,})"
)
_TOKEN_PREFIX_PATTERN = re.compile(
    r"(?<![A-Za-z0-9_])(?:sk-[A-Za-z0-9_-]{16,}|ghp_[A-Za-z0-9_]{16,}|github_pat_[A-Za-z0-9_]{20,})"
)
_URL_CREDENTIALS_PATTERN = re.compile(
    r"\b[a-z][a-z0-9+.-]*://[^\s/@:]+:[^\s/@]+@[^\s]+",
    re.IGNORECASE,
)
_IP_ADDRESS_PATTERN = re.compile(r"(?<!\d)(?:\d{1,3}\.){3}\d{1,3}(?!\d)")
_PHONE_PATTERN = re.compile(
    r"(?<!\d)(?:\+1[-.\s]?)?(?:\(\d{3}\)|\d{3})[-.\s]\d{3}[-.\s]\d{4}(?!\d)"
)
_CREDIT_CARD_CANDIDATE_PATTERN = re.compile(r"(?<!\d)(?:\d[ -]?){12,18}\d(?!\d)")

_BASIC_RULES = (
    _Rule(
        rule_id="email.basic",
        category="email",
        severity=SEVERITY_MEDIUM,
        confidence=CONFIDENCE_HIGH,
        pattern=_EMAIL_PATTERN,
        preview="<EMAIL>",
    ),
    _Rule(
        rule_id="ssn.us",
        category="government_id",
        severity=SEVERITY_HIGH,
        confidence=CONFIDENCE_HIGH,
        pattern=_SSN_PATTERN,
        preview="<US_SSN>",
    ),
    _Rule(
        rule_id="private_key.pem_block",
        category="private_key",
        severity=SEVERITY_HIGH,
        confidence=CONFIDENCE_HIGH,
        pattern=_PRIVATE_KEY_PATTERN,
        preview="<PRIVATE_KEY_BLOCK>",
    ),
    _Rule(
        rule_id="token.known_prefix",
        category="token",
        severity=SEVERITY_HIGH,
        confidence=CONFIDENCE_HIGH,
        pattern=_TOKEN_PREFIX_PATTERN,
        preview="<TOKEN>",
    ),
    _Rule(
        rule_id="url.credentials",
        category="url_credentials",
        severity=SEVERITY_HIGH,
        confidence=CONFIDENCE_HIGH,
        pattern=_URL_CREDENTIALS_PATTERN,
        preview="<URL_WITH_CREDENTIALS>",
    ),
    _Rule(
        rule_id="phone.us_like",
        category="phone",
        severity=SEVERITY_MEDIUM,
        confidence=CONFIDENCE_MEDIUM,
        pattern=_PHONE_PATTERN,
        preview="<US_PHONE>",
    ),
)


def scan_text_for_sensitive_findings(text: str) -> SensitiveScanResult:
    """Return deterministic potential sensitive-content findings for text."""
    line_starts = _line_starts(text)
    findings: list[SensitiveFinding] = []

    for rule in _BASIC_RULES:
        for match in rule.pattern.finditer(text):
            findings.append(_finding_for_match(rule, match, line_starts, rule.preview))

    for match in _SECRET_ASSIGNMENT_PATTERN.finditer(text):
        key = match.group("key")
        preview = f"{key}=<REDACTED>"
        findings.append(
            _finding_for_match(
                _Rule(
                    rule_id="secret.keyword_assignment",
                    category="secret",
                    severity=SEVERITY_HIGH,
                    confidence=CONFIDENCE_HIGH,
                    pattern=_SECRET_ASSIGNMENT_PATTERN,
                    preview=preview,
                ),
                match,
                line_starts,
                preview,
            )
        )

    for match in _IP_ADDRESS_PATTERN.finditer(text):
        candidate = match.group(0)
        if _is_valid_ipv4_address(candidate):
            findings.append(
                _finding_for_match(
                    _Rule(
                        rule_id="ip_address.basic",
                        category="ip_address",
                        severity=SEVERITY_MEDIUM,
                        confidence=CONFIDENCE_MEDIUM,
                        pattern=_IP_ADDRESS_PATTERN,
                        preview="<IP_ADDRESS>",
                    ),
                    match,
                    line_starts,
                    "<IP_ADDRESS>",
                )
            )

    for match in _CREDIT_CARD_CANDIDATE_PATTERN.finditer(text):
        candidate = match.group(0)
        digits = _digits_only(candidate)
        if 13 <= len(digits) <= 19 and _passes_luhn_check(digits):
            findings.append(
                _finding_for_match(
                    _Rule(
                        rule_id="credit_card.luhn",
                        category="credit_card",
                        severity=SEVERITY_HIGH,
                        confidence=CONFIDENCE_HIGH,
                        pattern=_CREDIT_CARD_CANDIDATE_PATTERN,
                        preview="<CREDIT_CARD>",
                    ),
                    match,
                    line_starts,
                    "<CREDIT_CARD>",
                )
            )

    ordered_findings = tuple(
        sorted(
            findings,
            key=lambda finding: (
                finding.start_offset if finding.start_offset is not None else -1,
                finding.end_offset if finding.end_offset is not None else -1,
                finding.rule_id,
            ),
        )
    )
    categories = tuple(sorted({finding.category for finding in ordered_findings}))
    status = STATUS_POTENTIAL if ordered_findings else STATUS_NONE_DETECTED

    return SensitiveScanResult(
        status=status,
        finding_count=len(ordered_findings),
        categories=categories,
        findings=ordered_findings,
    )


def _line_starts(text: str) -> tuple[int, ...]:
    starts = [0]
    starts.extend(match.end() for match in re.finditer("\n", text))
    return tuple(starts)


def _line_number_for_offset(line_starts: tuple[int, ...], offset: int) -> int:
    return bisect.bisect_right(line_starts, offset)


def _finding_for_match(
    rule: _Rule,
    match: re.Match[str],
    line_starts: tuple[int, ...],
    preview: str,
) -> SensitiveFinding:
    return SensitiveFinding(
        category=rule.category,
        severity=rule.severity,
        confidence=rule.confidence,
        line_number=_line_number_for_offset(line_starts, match.start()),
        start_offset=match.start(),
        end_offset=match.end(),
        rule_id=rule.rule_id,
        redacted_preview=preview,
    )


def _digits_only(text: str) -> str:
    return "".join(character for character in text if character.isdigit())


def _passes_luhn_check(digits: str) -> bool:
    total = 0
    should_double = False

    for character in reversed(digits):
        value = int(character)
        if should_double:
            value *= 2
            if value > 9:
                value -= 9
        total += value
        should_double = not should_double

    return total % 10 == 0


def _is_valid_ipv4_address(candidate: str) -> bool:
    octets = candidate.split(".")
    if len(octets) != 4:
        return False
    return all(0 <= int(octet) <= 255 for octet in octets)
