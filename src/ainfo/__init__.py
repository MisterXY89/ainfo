"""Entry points for the ``ainfo`` package."""

from __future__ import annotations

import asyncio
import json
import logging
from pathlib import Path

import typer

__version__ = "0.2.2"

from .chunking import chunk_text, stream_chunks
from .crawler import crawl as crawl_urls
from .extraction import extract_information, extract_text, extract_custom
from .fetching import fetch_data, async_fetch_data
from .llm_service import LLMService
from .output import output_results, to_json, json_schema
from .parsing import parse_data
from .schemas import ContactDetails
from .extractors import AVAILABLE_EXTRACTORS

app = typer.Typer()
logger = logging.getLogger(__name__)


@app.callback()
def cli(
    verbose: bool = typer.Option(
        False, "--verbose", "-v", help="Enable verbose logging"
    )
) -> None:
    """Configure global CLI options such as logging verbosity."""

    level = logging.DEBUG if verbose else logging.WARNING
    logging.basicConfig(
        level=level, format="%(levelname)s: %(message)s", force=True
    )


@app.command()
def run(
    url: str,
    render_js: bool = typer.Option(
        False, help="Render pages using a headless browser before extraction",
    ),
    use_llm: bool = typer.Option(
        False, help="Use an LLM instead of regex for contact extraction",
    ),
    summarize: bool = typer.Option(
        False, help="Summarize page content using the LLM",
    ),
    extract: list[str] = typer.Option(
        [], "--extract", "-e", help="Additional extractors to run",
    ),
    output: Path | None = typer.Option(
        None, "--output", "-o", help="Write JSON results to PATH.",
    ),
    json_output: bool = typer.Option(
        False, "--json", help="Print extracted data as JSON to stdout",
    ),
    include_text: bool = typer.Option(
        True,
        "--text/--no-text",
        help="Include page text in the results",
    ),
) -> None:
    """Fetch ``url`` and display extracted text and optional information."""

    raw = fetch_data(url, render_js=render_js)
    document = parse_data(raw, url=url)
    text: str | None = None
    if include_text or summarize:
        text = extract_text(document)

    results: dict[str, object] = {}
    if include_text and text is not None:
        results["text"] = text

    needs_llm = summarize or (use_llm and "contacts" in extract)

    if needs_llm:
        with LLMService() as llm:
            for name in extract:
                func = AVAILABLE_EXTRACTORS.get(name)
                if func is None:
                    raise typer.BadParameter(f"Unknown extractor: {name}")
                if name == "contacts":
                    results[name] = func(
                        document, method="llm" if use_llm else "regex", llm=llm
                    )
                else:
                    results[name] = func(document)
            if summarize and text is not None:
                results["summary"] = llm.summarize(text)
    else:
        for name in extract:
            func = AVAILABLE_EXTRACTORS.get(name)
            if func is None:
                raise typer.BadParameter(f"Unknown extractor: {name}")
            if name == "contacts":
                results[name] = func(document, method="regex", llm=None)
            else:
                results[name] = func(document)

    if output is not None:
        serialisable = {
            k: (v.model_dump() if isinstance(v, ContactDetails) else v)
            for k, v in results.items()
        }
        output.write_text(json.dumps(serialisable))

    if json_output:
        serialisable = {
            k: (v.model_dump() if isinstance(v, ContactDetails) else v)
            for k, v in results.items()
        }
        typer.echo(json.dumps(serialisable))
    else:
        if include_text and text is not None:
            typer.echo(text)
        for name in extract:
            value = results.get(name)
            if name == "contacts" and isinstance(value, ContactDetails):
                output_results(value)
            else:
                typer.echo(f"{name}:")
                if isinstance(value, dict):
                    for key, items in value.items():
                        typer.echo(f"  {key}: {', '.join(items)}")
                elif isinstance(value, list):
                    for item in value:
                        typer.echo(f"  - {item}")
                elif value is not None:
                    typer.echo(f"  {value}")
        if summarize and "summary" in results:
            typer.echo("summary:")
            typer.echo(results["summary"])


@app.command()
def crawl(
    url: str,
    depth: int = 1,
    render_js: bool = typer.Option(
        False, help="Render pages using a headless browser before extraction",
    ),
    use_llm: bool = typer.Option(
        False, help="Use an LLM instead of regex for contact extraction",
    ),
    extract: list[str] = typer.Option(
        [], "--extract", "-e", help="Additional extractors to run",
    ),
    output: Path | None = typer.Option(
        None, "--output", "-o", help="Write JSON results to PATH.",
    ),
    json_output: bool = typer.Option(
        False, "--json", help="Print aggregated results as JSON to stdout",
    ),
    include_text: bool = typer.Option(
        True,
        "--text/--no-text",
        help="Include page text in the results",
    ),
) -> None:
    """Crawl ``url`` up to ``depth`` levels and extract text and data."""

    method = "llm" if use_llm else "regex"
    aggregated_results: dict[str, dict[str, object]] = {}

    async def _crawl(llm: LLMService | None = None) -> None:
        async for link, raw in crawl_urls(url, depth, render_js=render_js):
            document = parse_data(raw, url=link)
            page_results: dict[str, object] = {}
            text = ""
            if include_text:
                text = extract_text(document)
                page_results["text"] = text
            for name in extract:
                func = AVAILABLE_EXTRACTORS.get(name)
                if func is None:
                    raise typer.BadParameter(f"Unknown extractor: {name}")
                if name == "contacts":
                    page_results[name] = func(document, method=method, llm=llm)
                else:
                    page_results[name] = func(document)
            aggregated_results[link] = page_results
            if not json_output:
                typer.echo(f"Results for {link}:")
                if include_text:
                    typer.echo(text)
                for name in extract:
                    value = page_results.get(name)
                    if name == "contacts" and isinstance(value, ContactDetails):
                        output_results(value)
                    else:
                        typer.echo(f"{name}: {value}")
                typer.echo()

    if use_llm:
        with LLMService() as llm:
            asyncio.run(_crawl(llm))
    else:
        asyncio.run(_crawl())

    if output is not None:
        serialisable = {
            url: {
                k: (v.model_dump() if isinstance(v, ContactDetails) else v)
                for k, v in res.items()
            }
            for url, res in aggregated_results.items()
        }
        output.write_text(json.dumps(serialisable))
    if json_output:
        serialisable = {
            url: {
                k: (v.model_dump() if isinstance(v, ContactDetails) else v)
                for k, v in res.items()
            }
            for url, res in aggregated_results.items()
        }
        typer.echo(json.dumps(serialisable))


def main() -> None:
    app()


__all__ = [
    "main",
    "run",
    "crawl",
    "app",
    "fetch_data",
    "async_fetch_data",
    "parse_data",
    "extract_information",
    "extract_text",
    "extract_custom",
    "output_results",
    "to_json",
    "json_schema",
    "chunk_text",
    "stream_chunks",
    "LLMService",
    "ContactDetails",
    "__version__",
]
