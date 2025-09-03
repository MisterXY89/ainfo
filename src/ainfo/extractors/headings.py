"""Helpers for extracting heading text from documents."""

from __future__ import annotations

from ..models import Document, PageNode

__all__ = ["extract_headings"]


def extract_headings(doc: Document) -> dict[str, list[str]]:
    """Return headings grouped by level from ``doc``."""
    headings: dict[str, list[str]] = {f"h{i}": [] for i in range(1, 7)}

    def _visit(nodes: list[PageNode]) -> None:
        for node in nodes:
            if node.tag in headings and node.text:
                headings[node.tag].append(node.text)
            if node.children:
                _visit(node.children)

    _visit(doc.nodes)
    return {level: items for level, items in headings.items() if items}
