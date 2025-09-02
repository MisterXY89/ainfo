"""Data models for representing parsed HTML documents."""

from __future__ import annotations

from typing import Dict, List, Optional

from pydantic import BaseModel, Field


class PageNode(BaseModel):
    """Representation of a single HTML element in a document tree."""

    tag: str = Field(..., description="HTML tag name, e.g. 'div' or 'p'.")
    attrs: Dict[str, str] = Field(
        default_factory=dict, description="Attributes associated with the tag."
    )
    text: str = Field(
        default="", description="Text content contained within this element."
    )
    children: List["PageNode"] = Field(
        default_factory=list, description="Child elements of this node."
    )
    is_content: bool = Field(
        default=False,
        description="Whether heuristics determined this node contains primary content.",
    )


class Document(BaseModel):
    """Structured representation of a parsed HTML document."""

    title: Optional[str] = Field(
        default=None, description="Contents of the <title> element if present."
    )
    url: Optional[str] = Field(
        default=None, description="Original source URL of the document."
    )
    nodes: List[PageNode] = Field(
        default_factory=list, description="Top-level nodes within the document body."
    )


# Rebuild models to resolve forward references
PageNode.model_rebuild()
