"""Lightweight HTTP API exposing the ainfo extraction features."""

from __future__ import annotations

import os
from typing import Any, List, Optional

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Query, Security, status
from fastapi.security import APIKeyHeader
from pydantic import BaseModel, Field, HttpUrl

from ainfo import LLMService, extract_site
from ainfo.config import LLMConfig

load_dotenv()

API_KEY_ENV = "AINFO_API_KEY"
API_KEY_HEADER_NAME = "X-API-Key"
API_KEY = os.getenv(API_KEY_ENV)

if not API_KEY:
    raise RuntimeError(
        f"Environment variable {API_KEY_ENV} must be set to secure the API"
    )

api_key_header = APIKeyHeader(name=API_KEY_HEADER_NAME, auto_error=False)
DEFAULT_SUMMARY_LANGUAGE = LLMConfig().summary_language or "German"

app = FastAPI()


class RunRequest(BaseModel):
    """Payload describing a crawl and extraction request."""

    url: HttpUrl = Field(..., description="URL to process")
    depth: int = Field(
        0,
        ge=0,
        description="Crawl depth when following links from the starting URL",
    )
    render_js: bool = Field(
        False,
        description="Render pages with a headless browser before extraction",
    )
    use_llm: bool = Field(
        False, description="Use LLM-backed extractors where available"
    )
    extract: List[str] = Field(
        default_factory=lambda: ["contacts"],
        description="Names of extractors to run for each page",
    )
    include_text: bool = Field(
        False,
        description="Include the raw page text in the response",
    )
    summarize: bool = Field(
        False, description="Generate an LLM summary for each processed page"
    )
    summary_language: Optional[str] = Field(
        None, description="Language to use for generated summaries"
    )
    summary_prompt: Optional[str] = Field(
        None, description="Custom prompt supplied to the LLM when summarising"
    )


def require_api_key(provided_key: str = Security(api_key_header)) -> str:
    """Verify that the request supplies the expected API key."""

    if provided_key == API_KEY:
        return provided_key

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or missing API key",
    )


def _serialise_value(value: Any) -> Any:
    if hasattr(value, "model_dump"):
        return value.model_dump()
    if isinstance(value, dict):
        return {k: _serialise_value(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_serialise_value(v) for v in value]
    return value


def _serialise_results(results: dict[str, dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {url: {k: _serialise_value(v) for k, v in data.items()} for url, data in results.items()}


def _execute_request(request: RunRequest) -> dict[str, dict[str, Any]]:
    llm: Optional[LLMService] = None
    config = LLMConfig()
    summary_language = (
        request.summary_language or config.summary_language or DEFAULT_SUMMARY_LANGUAGE
    )

    include_text = request.include_text or request.summarize

    try:
        if request.use_llm or request.summarize:
            config.summary_language = summary_language
            if request.summary_prompt is not None:
                config.summary_prompt = request.summary_prompt
            llm = LLMService(config)

        results = extract_site(
            str(request.url),
            depth=request.depth,
            render_js=request.render_js,
            extract=request.extract,
            include_text=include_text,
            use_llm=request.use_llm,
            llm=llm,
        )

        if request.summarize:
            if llm is None:
                raise RuntimeError("LLM service not available for summarisation")
            for page_data in results.values():
                if not isinstance(page_data, dict):
                    continue
                text_value = page_data.get("text")
                if isinstance(text_value, str) and text_value.strip():
                    page_data["summary"] = llm.summarize(
                        text_value,
                        language=summary_language,
                        prompt=request.summary_prompt,
                    )

        if request.summarize and not request.include_text:
            for page_data in results.values():
                if isinstance(page_data, dict):
                    page_data.pop("text", None)

        return _serialise_results(results)
    except HTTPException:
        raise
    except Exception as exc:  # pragma: no cover - bubbled to API response
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    finally:
        if llm is not None:
            llm.close()


@app.get("/run")
def run_get(
    url: HttpUrl = Query(..., description="URL to process"),
    summary_language: str = Query(
        DEFAULT_SUMMARY_LANGUAGE, description="Language for the LLM summary"
    ),
    _: str = Security(require_api_key),
):
    """Maintain the legacy behaviour of summarising a single page."""

    request = RunRequest(
        url=url,
        summary_language=summary_language,
        summarize=True,
        include_text=False,
        render_js=True,
        use_llm=True,
        extract=["contacts"],
        depth=0,
    )
    results = _execute_request(request)
    key = str(url)
    if key not in results and results:
        key = next(iter(results))
    return results.get(key, {})


@app.post("/run")
def run_post(payload: RunRequest, _: str = Security(require_api_key)):
    """Process a crawl/extraction request supplied in the request body."""

    return _execute_request(payload)
