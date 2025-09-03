"""Simple output helpers for displaying extracted information."""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
import json


def output_results(results: Mapping[str, list[str]]) -> None:
    """Pretty-print ``results`` to the console."""

    for key, values in results.items():
        print(f"{key}:")
        for value in values:
            print(f"  - {value}")


def to_json(results: Mapping[str, object], path: str | Path | None = None) -> str:
    """Serialize ``results`` to JSON and optionally write to ``path``.

    Parameters
    ----------
    results:
        A mapping containing the extracted information.
    path:
        Optional path to a file where the JSON representation should be
        written. If omitted, the JSON string is returned without writing to
        disk.

    Returns
    -------
    str
        The JSON representation of ``results``.
    """

    json_data = json.dumps(results)
    if path is not None:
        Path(path).write_text(json_data)
    return json_data


__all__ = ["output_results", "to_json"]

