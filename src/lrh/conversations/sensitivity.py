"""Local heuristic sensitivity scanner for conversation transcripts.

This module provides deterministic, local checks that flag potential sensitive
content in imported conversations. The scanner is a safety rail, not a
compliance system: it does not certify that text is safe, does not redact the
source content, and does not replace human review before public export.
"""

import bisect
import dataclasses
import re

from lrh.shared import sensitivity_rules

STATUS_NONE_DETECTED = "none_detected"
STATUS_POTENTIAL = "potential"


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


def scan_text_for_sensitive_findings(text: str) -> SensitiveScanResult:
    """Return deterministic potential sensitive-content findings for text."""
    line_starts = _line_starts(text)
    findings: list[SensitiveFinding] = []

    for rule in sensitivity_rules._BASIC_RULES:
        for match in rule.pattern.finditer(text):
            findings.append(_finding_for_match(rule, match, line_starts, rule.preview))

    for match in sensitivity_rules._SECRET_ASSIGNMENT_PATTERN.finditer(text):
        key = match.group("key")
        preview = f"{key}=<REDACTED>"
        findings.append(
            _finding_for_match(
                sensitivity_rules._Rule(
                    rule_id="secret.keyword_assignment",
                    category="secret",
                    severity=sensitivity_rules.SEVERITY_HIGH,
                    confidence=sensitivity_rules.CONFIDENCE_HIGH,
                    pattern=sensitivity_rules._SECRET_ASSIGNMENT_PATTERN,
                    preview=preview,
                ),
                match,
                line_starts,
                preview,
            )
        )

    for match in sensitivity_rules._IP_ADDRESS_PATTERN.finditer(text):
        candidate = match.group(0)
        if sensitivity_rules._is_valid_ipv4_address(candidate):
            findings.append(
                _finding_for_match(
                    sensitivity_rules._Rule(
                        rule_id="ip_address.basic",
                        category="ip_address",
                        severity=sensitivity_rules.SEVERITY_MEDIUM,
                        confidence=sensitivity_rules.CONFIDENCE_MEDIUM,
                        pattern=sensitivity_rules._IP_ADDRESS_PATTERN,
                        preview="<IP_ADDRESS>",
                    ),
                    match,
                    line_starts,
                    "<IP_ADDRESS>",
                )
            )

    for match in sensitivity_rules._CREDIT_CARD_CANDIDATE_PATTERN.finditer(text):
        candidate = match.group(0)
        digits = sensitivity_rules._digits_only(candidate)
        if 13 <= len(digits) <= 19 and sensitivity_rules._passes_luhn_check(digits):
            findings.append(
                _finding_for_match(
                    sensitivity_rules._Rule(
                        rule_id="credit_card.luhn",
                        category="credit_card",
                        severity=sensitivity_rules.SEVERITY_HIGH,
                        confidence=sensitivity_rules.CONFIDENCE_HIGH,
                        pattern=sensitivity_rules._CREDIT_CARD_CANDIDATE_PATTERN,
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
    rule: sensitivity_rules._Rule,
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
