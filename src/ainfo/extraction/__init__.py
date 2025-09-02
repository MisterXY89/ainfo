"""Utilities for extracting structured information from documents."""

from __future__ import annotations

from collections.abc import Iterable

from ..models import Document, PageNode
from ..extractors.contact import (
    extract_addresses,
    extract_emails,
    extract_phone_numbers,
)


def _gather_text(nodes: Iterable[PageNode]) -> str:
    """Recursively concatenate text from ``nodes`` into a single string."""

    parts: list[str] = []
    for node in nodes:
        if node.text:
            parts.append(node.text)
        if node.children:
            parts.append(_gather_text(node.children))
    return " ".join(parts)


def extract_information(doc: Document) -> dict[str, list[str]]:
    """Extract contact details from a parsed document."""

    text = _gather_text(doc.nodes)
    return {
        "emails": extract_emails(text),
        "phone_numbers": extract_phone_numbers(text),
        "addresses": extract_addresses(text),
    }


__all__ = ["extract_information"]

