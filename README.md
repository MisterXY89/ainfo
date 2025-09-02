# ainfo

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
phone numbers or addresses that were detected.

To crawl multiple pages starting from a URL and extract contact details from
each one:

```bash
ainfo crawl https://example.com --depth 2
```

The crawler visits pages breadth-first up to the specified depth and prints
results for every page encountered.

## Limitations

- Crawling retrieves each page twice: once for discovery and once for
  extraction, which may impact performance on large sites.
- Extraction focuses on basic contact details; more extractors can be added.
