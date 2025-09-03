"""Helpers for extracting hyperlinks from documents."""

from __future__ import annotations

from ..models import Document, PageNode

__all__ = ["extract_links"]


def extract_links(doc: Document) -> list[str]:
    """Return all hyperlink URLs from ``doc``."""
    links: list[str] = []

    def _visit(nodes: list[PageNode]) -> None:
        for node in nodes:
            if node.tag == "a":
                href = node.attrs.get("href")
                if href:
                    links.append(href)
            if node.children:
                _visit(node.children)

    _visit(doc.nodes)
    return list(dict.fromkeys(links))
