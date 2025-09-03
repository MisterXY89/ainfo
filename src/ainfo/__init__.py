"""Entry points for the ``ainfo`` package."""

from __future__ import annotations

import asyncio
import typer

from .crawler import crawl as crawl_urls
from .extraction import extract_information, extract_text
from .fetching import fetch_data
from .llm_service import LLMService
from .output import output_results
from .parsing import parse_data

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
) -> None:
    """Fetch ``url`` and display extracted contact information."""

    raw = fetch_data(url, render_js=render_js)
    document = parse_data(raw, url=url)
    llm = LLMService() if use_llm or summarize else None
    method = "llm" if use_llm else "regex"
    results = extract_information(document, method=method, llm=llm)
    output_results(results)
    if summarize and llm is not None:
        text = extract_text(document)
        typer.echo("summary:")
        typer.echo(llm.summarize(text))


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
) -> None:
    """Crawl ``url`` up to ``depth`` levels and extract contact info."""

    llm = LLMService() if use_llm else None
    method = "llm" if use_llm else "regex"
    urls = asyncio.run(crawl_urls(url, depth, render_js=render_js))
    for link in urls:
        raw = fetch_data(link, render_js=render_js)
        document = parse_data(raw, url=link)
        results = extract_information(document, method=method, llm=llm)
        typer.echo(f"Results for {link}:")
        output_results(results)
        typer.echo()


def main() -> None:
    app()


__all__ = ["main", "run", "crawl", "app"]
