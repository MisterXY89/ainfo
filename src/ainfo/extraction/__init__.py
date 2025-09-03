"""Utilities for extracting structured information from documents."""

from __future__ import annotations

from collections.abc import Iterable
import json
import re

from ..models import Document, PageNode
from ..extractors.contact import (
    extract_addresses,
    extract_emails,
    extract_phone_numbers,
)
from ..extractors.social import extract_social_profiles
from ..schemas import ContactDetails
from ..llm_service import LLMService


def _gather_content_text(nodes: Iterable[PageNode]) -> list[str]:
    """Return text from nodes flagged as primary content."""

    parts: list[str] = []
    for node in nodes:
        if node.is_content and node.text:
            parts.append(node.text)
        if node.children:
            parts.extend(_gather_content_text(node.children))
    return parts


def extract_text(doc: Document) -> str:
    """Extract and clean the main textual content from ``doc``."""

    text = " ".join(_gather_content_text(doc.nodes))
    return re.sub(r"\s+", " ", text).strip()


def extract_information(
    doc: Document, method: str = "regex", llm: LLMService | None = None
) -> ContactDetails:
    """Extract contact details from a parsed document.

    Parameters
    ----------
    doc:
        Parsed :class:`Document` to process.
    method:
        ``"regex"`` to use the built-in regular expressions or ``"llm"`` to
        delegate extraction to an LLM service.
    llm:
        Instance of :class:`LLMService` required when ``method`` is ``"llm"``.
    """

    text = extract_text(doc)
    if method == "llm":
        if llm is None:
            msg = "LLMService instance required when method='llm'"
            raise ValueError(msg)
        instruction = (
            "Extract any email addresses, phone numbers, street addresses and "
            "social media profiles from the following text. Respond in JSON "
            "with keys 'emails', 'phone_numbers', 'addresses' and "
            "'social_media'."
        )
        response = llm.extract(text, instruction)
        try:
            data = json.loads(response)
        except Exception:
            data = {}
        return ContactDetails(
            emails=data.get("emails", []),
            phone_numbers=data.get("phone_numbers", []),
            addresses=data.get("addresses", []),
            social_media=data.get("social_media", []),
        )

    # Default to regex based extraction
    return ContactDetails(
        emails=extract_emails(text),
        phone_numbers=extract_phone_numbers(text),
        addresses=extract_addresses(text),
        social_media=extract_social_profiles(text),
    )


def extract_custom(doc: Document, patterns: dict[str, str]) -> dict[str, list[str]]:
    """Extract arbitrary information from ``doc`` using regex ``patterns``.

    Parameters
    ----------
    doc:
        Parsed :class:`Document` to search.
    patterns:
        Mapping of field names to regular expression patterns. Each pattern is
        applied to the page's primary text content and all matches are returned
        in a list.

    Returns
    -------
    dict[str, list[str]]
        A mapping of the provided field names to lists of matched strings.
    """

    text = extract_text(doc)
    results: dict[str, list[str]] = {}
    for key, pattern in patterns.items():
        regex = re.compile(pattern, re.IGNORECASE)
        matches = [m.group(0) for m in regex.finditer(text)]
        results[key] = list(dict.fromkeys(matches))
    return results


__all__ = ["extract_information", "extract_text", "extract_custom"]
