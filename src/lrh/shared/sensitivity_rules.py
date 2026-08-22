"""Shared PII/secret detection rule taxonomy.

Extracted from `lrh.conversations.sensitivity` (`PROP-LRH-PII-SCAN` Decision
5, `WI-PII-SCAN-RULE-TAXONOMY`) so its category/severity/confidence taxonomy
and regex rule table can be reused by other local scanners without a second,
parallel definition of what counts as an email/SSN/IP/etc. This module
defines detection primitives only - it has no notion of transcripts, git
history, or file content, and does not itself produce findings.
"""

import dataclasses
import re

SEVERITY_MEDIUM = "medium"
SEVERITY_HIGH = "high"

CONFIDENCE_MEDIUM = "medium"
CONFIDENCE_HIGH = "high"


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
