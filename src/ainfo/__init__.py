"""Entry points for the ``ainfo`` package."""

from __future__ import annotations

import asyncio
import typer
from pathlib import Path

from .chunking import chunk_text, stream_chunks
from .crawler import crawl as crawl_urls
from .extraction import extract_information, extract_text
from .fetching import fetch_data, async_fetch_data
from .llm_service import LLMService
from .output import output_results, to_json
from .parsing import parse_data
from .schemas import ContactDetails

app = typer.Typer()


@app.command()
def run(
    url: str,
    render_js: bool = typer.Option(
        False, help="Render pages using a headless browser before extraction",
    ),
    use_llm: bool = typer.Option(
        False, help="Use an LLM instead of regex for information extraction",
    ),
    summarize: bool = typer.Option(
        False, help="Summarize page content using the LLM",
    ),
    output: Path | None = typer.Option(
        None, "--output", "-o", help="Write JSON results to PATH.",
    ),
    json_output: bool = typer.Option(
        False, "--json", help="Print extracted data as JSON to stdout",
    ),
) -> None:
    """Fetch ``url`` and display extracted contact information."""

    raw = fetch_data(url, render_js=render_js)
    document = parse_data(raw, url=url)
    method = "llm" if use_llm else "regex"

    if use_llm or summarize:
        with LLMService() as llm:
            llm_for_extraction = llm if use_llm else None
            results = extract_information(
                document, method=method, llm=llm_for_extraction
            )
            if json_output:
                typer.echo(to_json(results))
            else:
                output_results(results)
            if output is not None:
                to_json(results, path=output)
            if summarize:
                text = extract_text(document)
                typer.echo("summary:")
                typer.echo(llm.summarize(text))
    else:
        results = extract_information(document, method=method, llm=None)
        if json_output:
            typer.echo(to_json(results))
        else:
            output_results(results)
        if output is not None:
            to_json(results, path=output)


@app.command()
def crawl(
    url: str,
    depth: int = 1,
    render_js: bool = typer.Option(
        False, help="Render pages using a headless browser before extraction",
    ),
    use_llm: bool = typer.Option(
        False, help="Use an LLM instead of regex for information extraction",
    ),
    output: Path | None = typer.Option(
        None, "--output", "-o", help="Write JSON results to PATH.",
    ),
    json_output: bool = typer.Option(
        False, "--json", help="Print aggregated results as JSON to stdout",
    ),
) -> None:
    """Crawl ``url`` up to ``depth`` levels and extract contact info."""

    method = "llm" if use_llm else "regex"
    aggregated_results: dict[str, ContactDetails] = {}

    async def _crawl(llm: LLMService | None = None) -> None:
        async for link, raw in crawl_urls(url, depth, render_js=render_js):
            document = parse_data(raw, url=link)
            results = extract_information(document, method=method, llm=llm)
            aggregated_results[link] = results
            if not json_output:
                typer.echo(f"Results for {link}:")
                output_results(results)
                typer.echo()

    if use_llm:
        with LLMService() as llm:
            asyncio.run(_crawl(llm))
    else:
        asyncio.run(_crawl())

    if output is not None:
        to_json(aggregated_results, path=output)
    if json_output:
        typer.echo(to_json(aggregated_results))


def main() -> None:
    app()


__all__ = [
    "main",
    "run",
    "crawl",
    "app",
    "fetch_data",
    "async_fetch_data",
    "chunk_text",
    "stream_chunks",
    "ContactDetails",
]
