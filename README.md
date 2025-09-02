# ainfo

gather structured information from any website - ready for LLMs

## Architecture

The project separates concerns into distinct modules:

- `fetching` – obtain raw data from a source
- `parsing` – transform raw data into a structured form
- `extraction` – pull relevant information from the parsed data
- `output` – handle presentation of the extracted results
