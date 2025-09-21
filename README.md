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

### Command line

Install the project and run the CLI against a URL:

```bash
pip install ainfo
ainfo run https://example.com
```

The command fetches the page, parses its content and prints the page text.
Specify one or more built-in extractors with ``--extract`` to pull extra
information. For example, to collect contact details and hyperlinks:

```bash
ainfo run https://example.com --extract contacts --extract links
```

Available extractors include:

- ``contacts`` – emails, phone numbers, addresses and social profiles
- ``links`` – all hyperlinks on the page
- ``headings`` – text of headings (h1–h6)
- ``job_postings`` – structured job advertisement details like position and location

Use ``--json`` to emit machine-readable JSON instead of the default
human-friendly format. The JSON keys mirror the selected extractors, with
``text`` included by default. Pass ``--no-text`` when you only need the
extraction results. Retrieve the JSON schema for contact details with
``ainfo.output.json_schema``.

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

Summaries are generated in German by default. Override the language with
`--summary-language <LANG>` on the CLI or by setting the `AINFO_SUMMARY_LANGUAGE`
environment variable.

If the target site relies on client-side JavaScript, enable rendering with a
headless browser:

```bash
ainfo run https://example.com --render-js
```

To crawl multiple pages starting from a URL and optionally run extractors
on each page:

```bash
ainfo crawl https://example.com --depth 2 --extract contacts
```

The crawler visits pages breadth-first up to the specified depth and prints
results for every page encountered. Pass ``--json`` to output the aggregated
results as JSON instead.

Both commands accept `--render-js` to execute JavaScript before scraping, which
uses [Playwright](https://playwright.dev/). Installing the browser drivers may
require running `playwright install`.

Utilities ``chunk_text`` and ``stream_chunks`` are available to break large
pages into manageable pieces when sending content to LLMs.

### Programmatic API

Most components can also be used directly from Python. Fetch and parse a page,
then run the extractors yourself:

```python
from ainfo.extractors import AVAILABLE_EXTRACTORS

from ainfo import fetch_data, parse_data, extract_information, extract_custom

html = fetch_data("https://example.com")
doc = parse_data(html, url="https://example.com")

# Contact details via built-in extractor
contacts = AVAILABLE_EXTRACTORS["contacts"](doc)

# All links
links = AVAILABLE_EXTRACTORS["links"](doc)

# Any additional data via regular expressions
extra = extract_custom(doc, {"prices": r"\$\d+(?:\.\d{2})?"})
print(contacts.emails, extra["prices"])
```

Serialise results with ``to_json`` or inspect the JSON schema with
``json_schema(ContactDetails)``.

To crawl multiple pages of the same site and aggregate the results in code,
use ``extract_site``. Pages are fetched breadth-first, deduplicated using a
content hash and restricted to the starting domain by default:

```python
from ainfo import extract_site

pages = extract_site("https://example.com", depth=2, include_text=True)

for url, data in pages.items():
    print(url, data["contacts"].emails)
```

#### Custom extractors

Define your own extractor by writing a function that accepts a
``Document`` and registering it in ``ainfo.extractors.AVAILABLE_EXTRACTORS``.

```python
# my_extractors.py
from ainfo.models import Document
from ainfo.extraction import extract_custom
from ainfo.extractors import AVAILABLE_EXTRACTORS

def extract_prices(doc: Document) -> list[str]:
    data = extract_custom(doc, {"prices": r"\$\d+(?:\.\d{2})?"})
    return data.get("prices", [])

AVAILABLE_EXTRACTORS["prices"] = extract_prices
```

After importing ``my_extractors`` your extractor becomes available on the
command line:

```bash
ainfo run https://example.com --extract prices --no-text
```

#### LLM-based extraction

``extract_custom`` can also delegate to a large language model. Supply an
``LLMService`` and a prompt describing the desired output:

```python
from ainfo import fetch_data, parse_data
from ainfo.extraction import extract_custom
from ainfo.llm_service import LLMService

html = fetch_data("https://example.com")
doc = parse_data(html, url="https://example.com")

with LLMService() as llm:
    data = extract_custom(
        doc,
        llm=llm,
        prompt="List all products with their prices as JSON under 'products'",
    )
print(data["products"])
```

### Workflow examples

#### Save contact details to JSON

```bash
pip install ainfo
ainfo run https://example.com --json > contacts.json
```

#### Summarize a large page with `chunk_text`

```python
from ainfo import fetch_data, parse_data, chunk_text
from some_llm import summarize  # pseudo-code

html = fetch_data("https://example.com")
doc = parse_data(html, url="https://example.com")

parts = [summarize(chunk) for chunk in chunk_text(doc.text_content(), 1000)]
print(" ".join(parts))
```

#### Stream chunks on the fly

Fetch and chunk a page directly by URL or pass in raw text:

```python
from ainfo import stream_chunks

for chunk in stream_chunks("https://example.com", size=1000):
    handle(chunk)  # send to LLM or other processor
```

### Environment configuration

Copy `.env.example` to `.env` and fill in `OPENROUTER_API_KEY`, `OPENROUTER_MODEL`, and `OPENROUTER_BASE_URL` to enable LLM-powered features.

## Development & Releases

For automated version bumping and releases, see [RELEASE.md](RELEASE.md) for documentation on using the `release.sh` script.


## n8n integration

A minimal FastAPI wrapper and accompanying Dockerfile live in the `integration/` directory. Build the container and run the service:

```bash
docker build -f integration/Dockerfile -t ainfo-api .
docker run -p 8000:8000 -e OPENROUTER_API_KEY=your_key -e AINFO_API_KEY=choose_a_secret ainfo-api
# or use an env file
docker run -p 8000:8000 --env-file .env ainfo-api
```

The server exposes a `/run` endpoint that executes:

```bash
ainfo run <url> --use-llm --summarize --render-js --extract contacts --no-text --json
```

Pass an optional `summary_language` query parameter to control the summary
language (default: German).

`integration/api.py` uses [`python-dotenv`](https://pypi.org/project/python-dotenv/) to load a `.env` file, so sensitive values
such as `OPENROUTER_API_KEY` can be supplied via environment variables. Protect the endpoint by setting `AINFO_API_KEY` and
include an `X-API-Key` header with that value on every request. This makes it easy to call `ainfo` from workflow tools like
[n8n](https://n8n.io/).

## Limitations

- The built-in ``extract_information`` targets contact and social media
  details. Use ``extract_custom`` for other patterns or implement your own
  domain-specific extractors.
