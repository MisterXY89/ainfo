"""HTML parsing utilities for the ``ainfo`` package."""

from __future__ import annotations

from typing import Iterable
import logging

from bs4 import BeautifulSoup, Tag

from ..models import Document, PageNode

logger = logging.getLogger(__name__)

# Tags and attribute keywords typically associated with navigation or ads.
_NAV_TAGS = {
    "nav",
    "header",
    "footer",
    "aside",
    "form",
    "script",
    "style",
    "noscript",
}
_NAV_ATTR_KEYWORDS = {
    "nav",
    "menu",
    "sidebar",
    "footer",
    "header",
    "advert",
    "ads",
    "promo",
    "banner",
    "social",
}


def _attr_tokens(tag: Tag) -> str:
    """Return a space separated string of attribute tokens for a tag."""
    tokens: list[str] = []
    for key in ("id", "class", "role", "aria-label"):
        value = tag.attrs.get(key)
        if not value:
            continue
        if isinstance(value, (list, tuple)):
            tokens.extend(str(v) for v in value)
        else:
            tokens.append(str(value))
    return " ".join(tokens).lower()


def _is_navigation(tag: Tag) -> bool:
    """Heuristically determine whether a tag is navigational or an advertisement."""
    if tag.name in _NAV_TAGS:
        return True
    attr_values = _attr_tokens(tag)
    return any(keyword in attr_values for keyword in _NAV_ATTR_KEYWORDS)


def _build_tree(elements: Iterable[Tag]) -> list[PageNode]:
    """Recursively convert BeautifulSoup elements into :class:`PageNode` objects."""

    nodes: list[PageNode] = []
    for el in elements:
        attrs = {
            k: " ".join(v) if isinstance(v, (list, tuple)) else str(v)
            for k, v in el.attrs.items()
        }
        text = el.get_text(" ", strip=True)
        nav = _is_navigation(el)
        is_content = not nav and len(text.split()) >= 5
        children = _build_tree(el.find_all(recursive=False))
        nodes.append(
            PageNode(
                tag=el.name,
                attrs=attrs,
                text=text,
                children=children,
                is_content=is_content,
            )
        )
    return nodes


def parse_html(html: str, url: str | None = None) -> Document:
    """Parse HTML into a :class:`Document` tree.

    Parameters
    ----------
    html:
        Raw HTML string to parse.
    url:
        Optional source URL associated with the HTML.

    Returns
    -------
    Document
        Structured representation of the parsed document.
    """
    logger.info("Parsing HTML from %s", url or "<string>")
    soup = BeautifulSoup(html, "html.parser")
    title = soup.title.string.strip() if soup.title and soup.title.string else None
    body = soup.body or soup
    nodes = _build_tree(body.find_all(recursive=False))
    logger.debug("Parsed %d top-level nodes", len(nodes))
    return Document(title=title, url=url, nodes=nodes)
