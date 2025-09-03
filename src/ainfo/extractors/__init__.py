"""Collection of built-in information extractors."""

from __future__ import annotations

from typing import Any, Callable

from ..models import Document
from .links import extract_links
from .headings import extract_headings

Extractor = Callable[[Document], Any]


def extract_contacts(doc: Document, **kwargs: Any) -> Any:
    """Proxy to :func:`ainfo.extraction.extract_information`.

    Imported lazily to avoid circular imports between modules.
    """
    from ..extraction import extract_information

    return extract_information(doc, **kwargs)


AVAILABLE_EXTRACTORS: dict[str, Extractor] = {
    "contacts": extract_contacts,
    "links": extract_links,
    "headings": extract_headings,
}

__all__ = [
    "AVAILABLE_EXTRACTORS",
    "extract_links",
    "extract_headings",
    "extract_contacts",
]
