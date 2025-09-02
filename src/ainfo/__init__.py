from .fetching import fetch_data
from .parsing import parse_data
from .extraction import extract_information
from .output import output_results


def main() -> None:
    """Run the data pipeline."""
    raw = fetch_data()
    parsed = parse_data(raw)
    results = extract_information(parsed)
    output_results(results)
