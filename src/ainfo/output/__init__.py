"""Simple output helpers for displaying extracted information."""

from __future__ import annotations

from collections.abc import Mapping


def output_results(results: Mapping[str, list[str]]) -> None:
    """Pretty-print ``results`` to the console."""

    for key, values in results.items():
        print(f"{key}:")
        for value in values:
            print(f"  - {value}")


__all__ = ["output_results"]

