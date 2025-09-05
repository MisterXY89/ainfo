"""Utilities for extracting structured information from documents."""

from __future__ import annotations

from collections.abc import Iterable
import json
import logging
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

logger = logging.getLogger(__name__)


def _gather_content_text(nodes: Iterable[PageNode]) -> list[str]:
    """Return text from nodes flagged as primary content."""

    parts: list[str] = []
    for node in nodes:
        if node.is_content and node.text:
            parts.append(node.text)
        if node.children:
            parts.extend(_gather_content_text(node.children))
    return parts


def extract_text(
    doc: Document, joiner: str = " ", as_list: bool = False
) -> str | list[str]:
    """Extract and clean the main textual content from ``doc``.

    Parameters
    ----------
    doc:
        Parsed :class:`Document` to process.
    joiner:
        String used to join individual text fragments when ``as_list`` is
        ``False``. Defaults to a single space.
    as_list:
        When ``True`` return a list of text fragments instead of a single
        string.
    """

    logger.info("Extracting text from document")
    parts = [re.sub(r"\s+", " ", p).strip() for p in _gather_content_text(doc.nodes)]
    if as_list:
        return [p for p in parts if p]
    text = joiner.join(parts)
    return text.strip()


def extract_information(
    doc: Document,
    method: str = "regex",
    llm: LLMService | None = None,
    instruction: str | None = None,
    model: str | None = None,
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

    logger.info("Extracting contact information using %s", method)
    text = extract_text(doc)
    if method == "llm":
        if llm is None:
            msg = "LLMService instance required when method='llm'"
            raise ValueError(msg)
        instruction = instruction or (
            "Extract any email addresses, phone numbers, street addresses and "
            "social media profiles from the following text. Respond in JSON "
            "with keys 'emails', 'phone_numbers', 'addresses' and "
            "'social_media'."
          )
        response = llm.extract(text, instruction, model=model)
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


def extract_custom(
    doc: Document,
    patterns: dict[str, str] | None = None,
    *,
    llm: LLMService | None = None,
    prompt: str | None = None,
    model: str | None = None,
) -> dict[str, list[str]]:
    """Extract arbitrary information from ``doc``.

    The extraction can be performed either using regular expression
    ``patterns`` or delegated to an LLM service when ``llm`` is provided.

    Parameters
    ----------
    doc:
        Parsed :class:`Document` to search.
    patterns:
        Mapping of field names to regular expression patterns. Required when
        ``llm`` is ``None``.
    llm:
        Optional :class:`LLMService` used to perform extraction via a large
        language model.
    prompt:
        Custom prompt supplied to the LLM. It should describe the desired JSON
        structure, for example ``"Extract product names as a list under the key
        'products'"``. If omitted a generic instruction is used.
    model:
        Identifier of the model to use when ``llm`` is provided.

    Returns
    -------
    dict[str, list[str]]
        A mapping of field names to lists of extracted strings.
    """

    logger.info("Extracting custom information")
    text = extract_text(doc)
    if llm is not None:
        instruction = prompt or "Extract the requested information as JSON."
        response = llm.extract(text, instruction, model=model)
        try:
            data = json.loads(response)
        except Exception:
            data = {}
        results: dict[str, list[str]] = {}
        for key, value in data.items():
            if isinstance(value, list):
                results[key] = value
            elif value is not None:
                results[key] = [value]
        return results

    if patterns is None:
        msg = "patterns required when llm is None"
        raise ValueError(msg)

    results: dict[str, list[str]] = {}
    for key, pattern in patterns.items():
        regex = re.compile(pattern, re.IGNORECASE)
        matches = [m.group(0) for m in regex.finditer(text)]
        results[key] = list(dict.fromkeys(matches))
    return results


__all__ = ["extract_information", "extract_text", "extract_custom"]
