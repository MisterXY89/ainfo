"""Helpers for extracting job posting details from documents."""

from __future__ import annotations

from collections.abc import Iterable
import re

from ..models import Document, PageNode

__all__ = ["extract_job_postings"]


_JOB_KEYWORDS = {
    "job",
    "career",
    "position",
    "vacancy",
    "opening",
    "opportunity",
    "stelle",
    "stellenangebot",
    "stellenanzeige",
    "jobangebot",
    "karriere",
    "ausschreibung",
    "arbeitsplatz",
    "beruf",
}

_APPLY_KEYWORDS = {
    "apply",
    "bewerb",
    "jetzt bewerben",
    "zur bewerbung",
    "bewerbungsformular",
    "bewerbung abschicken",
}

_JOB_CONTAINER_TAGS = {"section", "article", "div", "li"}

_HEADING_TAGS = {f"h{i}" for i in range(1, 7)}

_TEXT_TAGS = {
    "p",
    "li",
    "span",
    "dd",
    "dt",
    "figcaption",
    "blockquote",
}

_FIELD_PATTERNS: dict[str, tuple[re.Pattern[str], ...]] = {
    "company": (
        re.compile(r"\b(?:Company|Employer)\s*[:\-–—]\s*(.+)", re.IGNORECASE),
        re.compile(r"\b(?:Firma|Unternehmen|Arbeitgeber)\s*[:\-–—]\s*(.+)", re.IGNORECASE),
    ),
    "position": (
        re.compile(r"\b(?:Position|Role|Title)\s*[:\-–—]\s*(.+)", re.IGNORECASE),
        re.compile(r"\b(?:Stellenbezeichnung|Jobtitel|Funktionsbezeichnung)\s*[:\-–—]\s*(.+)", re.IGNORECASE),
    ),
    "location": (
        re.compile(r"\b(?:Location|Work\s*Location)\s*[:\-–—]\s*(.+)", re.IGNORECASE),
        re.compile(r"\b(?:Standort|Ort|Arbeitsort|Einsatzort|Region)\s*[:\-–—]\s*(.+)", re.IGNORECASE),
    ),
    "employment_type": (
        re.compile(r"\b(?:Employment\s+Type|Job\s+Type|Type)\s*[:\-–—]\s*(.+)", re.IGNORECASE),
        re.compile(r"\bSchedule\s*[:\-–—]\s*(.+)", re.IGNORECASE),
        re.compile(r"\b(?:Anstellungsart|Beschäftigungsart|Beschäftigungsverhältnis|Arbeitszeit|Arbeitsmodell|Pensum|Arbeitsumfang)\s*[:\-–—]\s*(.+)", re.IGNORECASE),
    ),
    "salary": (
        re.compile(r"\b(?:Salary|Compensation|Pay)\s*[:\-–—]\s*(.+)", re.IGNORECASE),
        re.compile(r"\b(?:Gehalt|Vergütung|Lohn|Bezahlung|Entlohnung)\s*[:\-–—]\s*(.+)", re.IGNORECASE),
    ),
    "experience": (
        re.compile(r"\b(?:Experience|Experience\s+Level)\s*[:\-–—]\s*(.+)", re.IGNORECASE),
        re.compile(r"\b(?:Erfahrung|Berufserfahrung|Erfahrungsniveau|Erfahrungsstufe)\s*[:\-–—]\s*(.+)", re.IGNORECASE),
    ),
}


def _iter_nodes(nodes: Iterable[PageNode]) -> Iterable[PageNode]:
    for node in nodes:
        yield node
        if node.children:
            yield from _iter_nodes(node.children)


def _collect_segments(node: PageNode) -> list[str]:
    segments: list[str] = []

    for descendant in _iter_nodes(node.children):
        if not descendant.text:
            continue
        tag = descendant.tag.lower()
        if tag in _HEADING_TAGS or tag in _TEXT_TAGS:
            segments.extend(_split_segment(descendant.text))
        elif not descendant.children:
            segments.extend(_split_segment(descendant.text))

    return segments


def _split_segment(text: str) -> list[str]:
    parts = re.split(r"[\n\r\u2022•]+", text)
    cleaned = [re.sub(r"\s+", " ", part).strip() for part in parts]
    return [part for part in cleaned if part]


def _first_heading(node: PageNode) -> str | None:
    for descendant in _iter_nodes(node.children):
        if descendant.tag.lower() in _HEADING_TAGS and descendant.text:
            return descendant.text.strip()
    return None


def _collect_apply_link(node: PageNode) -> str | None:
    for descendant in _iter_nodes(node.children):
        if descendant.tag.lower() != "a":
            continue
        href = descendant.attrs.get("href")
        if not href:
            continue
        label = descendant.text.lower() if descendant.text else ""
        attr_tokens = " ".join(descendant.attrs.values()).lower()
        if any(keyword in label or keyword in attr_tokens for keyword in _APPLY_KEYWORDS):
            return href.strip()
    return None


def _extract_fields(segments: list[str]) -> dict[str, str]:
    fields: dict[str, str] = {}

    for segment in segments:
        for field, patterns in _FIELD_PATTERNS.items():
            if field in fields:
                continue
            for pattern in patterns:
                match = pattern.search(segment)
                if match:
                    value = match.group(1).strip()
                    # Remove trailing punctuation that often concludes inline sentences.
                    value = value.rstrip(".;, ")
                    if value:
                        fields[field] = value
                    break

    return fields


def _looks_like_job(node: PageNode, data: dict[str, str]) -> bool:
    attr_values = " ".join(node.attrs.values()).lower()
    if any(keyword in attr_values for keyword in _JOB_KEYWORDS):
        return True

    meaningful = {key: value for key, value in data.items() if key != "description"}
    return len(meaningful) >= 2


def extract_job_postings(doc: Document) -> list[dict[str, str]]:
    """Return job posting details found in ``doc``.

    The extractor searches for containers that look like job advertisements and
    returns the structured details (position, location, employment type, etc.)
    when available.
    """

    postings: list[dict[str, str]] = []

    for node in _iter_nodes(doc.nodes):
        if node.tag.lower() not in _JOB_CONTAINER_TAGS:
            continue

        segments = _collect_segments(node)
        if not segments:
            continue

        data = _extract_fields(segments)

        heading = _first_heading(node)
        if heading and "position" not in data:
            data["position"] = heading

        apply_link = _collect_apply_link(node)
        if apply_link:
            data.setdefault("apply_url", apply_link)

        if not data:
            continue

        if not _looks_like_job(node, data):
            continue

        postings.append(data)

    return postings
