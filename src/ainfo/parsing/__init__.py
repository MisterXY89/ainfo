"""Helpers for turning raw HTML into structured documents."""

from __future__ import annotations

from ..models import Document
from .html import parse_html


def parse_data(raw: str, url: str | None = None) -> Document:
    """Parse raw HTML into a :class:`~ainfo.models.Document`.

    Parameters
    ----------
    raw:
        The raw HTML string.
    url:
        Optional source URL associated with the HTML.
    """

    return parse_html(raw, url=url)


__all__ = ["parse_data", "parse_html"]

