"""Helpers for extracting contact information from free-form text."""

from __future__ import annotations

import re

try:  # pragma: no cover - optional dependency
    import phonenumbers
except Exception:  # pragma: no cover
    phonenumbers = None  # type: ignore[assignment]

EMAIL_PATTERN = re.compile(
    r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+"
)

PHONE_PATTERN = re.compile(
    r"(?:\+?\d{1,3}[\s-]?)?(?:\(?\d{3}\)?[\s-]?|\d{3}[\s-]?)\d{3}[\s-]?\d{4}\b"
)

ADDRESS_PATTERN = re.compile(
    r"\b\d{1,5}\s+[\w#.]+(?:\s+[\w#.]+)*\s+"
    r"(?:Street|St\.?|Road|Rd\.?|Avenue|Ave\.?|Boulevard|Blvd\.?|Lane|Ln\.?|Drive|Dr\.?)"
    r"(?:\s+\w+)*\b",
    re.IGNORECASE,
)


__all__ = ["extract_emails", "extract_phone_numbers", "extract_addresses"]


def extract_emails(text: str) -> list[str]:
    """Return a list of email addresses found in ``text``."""
    return list(dict.fromkeys(m.group(0) for m in EMAIL_PATTERN.finditer(text)))


def extract_phone_numbers(text: str, region: str | None = None) -> list[str]:
    """Return phone numbers detected in ``text``.

    If the :mod:`phonenumbers` package is installed, numbers are parsed and
    formatted using that library. Otherwise the raw matches are returned with
    non-digit characters removed.
    """
    if phonenumbers is not None:
        numbers: list[str] = []
        for match in phonenumbers.PhoneNumberMatcher(text, region or "US"):
            formatted = phonenumbers.format_number(
                match.number, phonenumbers.PhoneNumberFormat.E164
            )
            numbers.append(formatted)
        return numbers

    return [re.sub(r"\D", "", m.group(0)) for m in PHONE_PATTERN.finditer(text)]


def extract_addresses(text: str) -> list[str]:
    """Return street addresses found in ``text``.

    The regex is conservative and tuned for common US-style street addresses,
    so it may not match every possible address format.
    """
    return [m.group(0).strip() for m in ADDRESS_PATTERN.finditer(text)]
