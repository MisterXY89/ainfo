"""Simple output helpers for displaying extracted information."""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
import json
from pydantic import BaseModel


def _to_mapping(results: Mapping[str, list[str]] | BaseModel) -> Mapping[str, list[str]]:
    if isinstance(results, BaseModel):
        return results.model_dump()
    return results


def output_results(results: Mapping[str, list[str]] | BaseModel) -> None:
    """Pretty-print ``results`` to the console."""

    data = _to_mapping(results)
    for key, values in data.items():
        print(f"{key}:")
        for value in values:
            print(f"  - {value}")


def _serialize(obj: object) -> object:
    if isinstance(obj, BaseModel):
        return obj.model_dump()
    if isinstance(obj, Mapping):
        return {k: _serialize(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_serialize(v) for v in obj]
    return obj


def to_json(results: Mapping[str, object] | BaseModel, path: str | Path | None = None) -> str:
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

    json_data = json.dumps(_serialize(results))
    if path is not None:
        Path(path).write_text(json_data)
    return json_data


def json_schema(model: type[BaseModel]) -> dict[str, object]:
    """Return the JSON schema for ``model``."""

    return model.model_json_schema()


__all__ = ["output_results", "to_json", "json_schema"]

