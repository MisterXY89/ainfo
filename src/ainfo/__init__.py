"""Entry points for the ``ainfo`` package."""

from __future__ import annotations

import asyncio
import typer

from .crawler import crawl as crawl_urls
from .extraction import extract_information
from .fetching import fetch_data
from .output import output_results
from .parsing import parse_data

app = typer.Typer()


@app.command()
def run(
    url: str,
    render_js: bool = typer.Option(
        False, help="Render pages using a headless browser before extraction"
    ),
) -> None:
    """Fetch ``url`` and display extracted contact information."""

    raw = fetch_data(url, render_js=render_js)
    document = parse_data(raw, url=url)
    results = extract_information(document)
    output_results(results)


@app.command()
def crawl(
    url: str,
    depth: int = 1,
    render_js: bool = typer.Option(
        False, help="Render pages using a headless browser before extraction"
    ),
) -> None:
    """Crawl ``url`` up to ``depth`` levels and extract contact info."""

    urls = asyncio.run(crawl_urls(url, depth, render_js=render_js))
    for link in urls:
        raw = fetch_data(link, render_js=render_js)
        document = parse_data(raw, url=link)
        results = extract_information(document)
        typer.echo(f"Results for {link}:")
        output_results(results)
        typer.echo()


def main() -> None:
    app()


__all__ = ["main", "run", "crawl", "app"]

