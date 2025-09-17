"""Helpers for extracting contact information from free-form text."""

from __future__ import annotations

import re
from typing import TYPE_CHECKING, Union

if TYPE_CHECKING:
    from ..models import Document, PageNode

try:  # pragma: no cover - optional dependency
    import phonenumbers
except Exception:  # pragma: no cover
    phonenumbers = None  # type: ignore[assignment]

EMAIL_PATTERN = re.compile(
    r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+"
)

MAILTO_PATTERN = re.compile(
    r"mailto:([a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+)",
    re.IGNORECASE
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


def _extract_emails_from_nodes(nodes: list["PageNode"]) -> list[str]:
    """Extract emails from HTML attributes (like mailto links) in document nodes."""
    emails: list[str] = []
    
    def _visit(node_list: list["PageNode"]) -> None:
        for node in node_list:
            # Check href attributes for mailto links
            if node.tag == "a" and "href" in node.attrs:
                href = node.attrs["href"]
                mailto_match = MAILTO_PATTERN.search(href)
                if mailto_match:
                    emails.append(mailto_match.group(1))
            
            # Recursively check child nodes
            if node.children:
                _visit(node.children)
    
    _visit(nodes)
    return emails


def extract_emails(source: str | "Document") -> list[str]:
    """Extract emails from text or from both text content and HTML attributes in a document.
    
    When passed a string, searches for email addresses in the text.
    When passed a Document, searches for email addresses in:
    1. Text content of the document
    2. HTML attributes like href="mailto:..." links
    
    Parameters
    ----------
    source:
        Either a text string or a parsed Document to search for email addresses.
        
    Returns
    -------
    list[str]
        List of unique email addresses found, with duplicates removed.
    """
    if isinstance(source, str):
        # Backward compatibility: handle string input
        return list(dict.fromkeys(m.group(0) for m in EMAIL_PATTERN.finditer(source)))
    
    # Handle Document input
    doc = source
    
    # Get emails from text content
    from ..extraction import extract_text
    text = extract_text(doc, content_only=False)
    text_emails = list(dict.fromkeys(m.group(0) for m in EMAIL_PATTERN.finditer(text)))
    
    # Get emails from HTML attributes (like mailto links)
    attr_emails = _extract_emails_from_nodes(doc.nodes)
    
    # Combine and deduplicate
    all_emails = text_emails + attr_emails
    return list(dict.fromkeys(all_emails))


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
