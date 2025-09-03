# ainfo

[![Publish documentation](https://github.com/MisterXY89/ainfo/actions/workflows/publish-docs.yml/badge.svg)](https://github.com/MisterXY89/ainfo/actions/workflows/publish-docs.yml) [![Upload Python Package](https://github.com/MisterXY89/ainfo/actions/workflows/python-publish.yml/badge.svg)](https://github.com/MisterXY89/ainfo/actions/workflows/python-publish.yml)

gather structured information from any website - ready for LLMs

## Architecture

The project separates concerns into distinct modules:

- `fetching` – obtain raw data from a source
- `parsing` – transform raw data into a structured form
- `extraction` – pull relevant information from the parsed data
- `output` – handle presentation of the extracted results

## Usage

Install the project and run the CLI against a URL:

```bash
pip install -e .
ainfo run https://example.com
```

The command fetches the page, parses its content and prints any emails,
phone numbers, street addresses or social media profiles that were detected.
Use ``--json`` to emit machine-readable JSON instead of the default
human-friendly format. The JSON conforms to the
``ainfo.schemas.ContactDetails`` Pydantic model so consumers can rely on a
stable schema. Retrieve the JSON schema with ``ainfo.output.json_schema``.

For use within an existing asyncio application, the package exposes an
``async_fetch_data`` coroutine:

```python
import asyncio
from ainfo import async_fetch_data

async def main():
    html = await async_fetch_data("https://example.com")
    print(html[:60])

asyncio.run(main())
```

To delegate information extraction or summarisation to an LLM, provide an
OpenRouter API key via the ``OPENROUTER_API_KEY`` environment variable and pass
``--use-llm`` or ``--summarize``:

```bash
export OPENROUTER_API_KEY=your_key
ainfo run https://example.com --use-llm --summarize
```

If the target site relies on client-side JavaScript, enable rendering with a
headless browser:

```bash
ainfo run https://example.com --render-js
```

To crawl multiple pages starting from a URL and extract contact details from
each one:

```bash
ainfo crawl https://example.com --depth 2
```

The crawler visits pages breadth-first up to the specified depth and prints
results for every page encountered. Pass ``--json`` to output the aggregated
results as JSON instead.

Both commands accept `--render-js` to execute JavaScript before scraping, which
uses [Playwright](https://playwright.dev/). Installing the browser drivers may
require running `playwright install`.

Utilities ``chunk_text`` and ``stream_chunks`` are available to break large
pages into manageable pieces when sending content to LLMs.

### Environment configuration

Copy `.env.example` to `.env` and fill in `OPENROUTER_API_KEY`, `OPENROUTER_MODEL`, and `OPENROUTER_BASE_URL` to enable LLM-powered features.

## Limitations

- Extraction currently focuses on contact and social media details; additional
  domain-specific extractors can be added.
