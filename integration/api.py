from fastapi import FastAPI, HTTPException, Query, Security, status
from fastapi.security import APIKeyHeader
import subprocess
import json
import os
from dotenv import load_dotenv

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


def require_api_key(provided_key: str = Security(api_key_header)) -> str:
    """Verify that the request supplies the expected API key."""

    if provided_key == API_KEY:
        return provided_key

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or missing API key",
    )


@app.get("/run")
def run(
    url: str = Query(..., description="URL to process"),
    summary_language: str = Query(
        DEFAULT_SUMMARY_LANGUAGE, description="Language for the LLM summary"
    ),
    _: str = Security(require_api_key),
):
    """Execute the ainfo CLI against the provided URL.

    The command runs with LLM support enabled, summarisation, JavaScript rendering
    and the contacts extractor. Only extractor results are returned as JSON.
    """
    cmd = [
        "ainfo",
        "run",
        url,
        "--use-llm",
        "--summarize",
        "--render-js",
        "--summary-language",
        summary_language,
        "--extract",
        "contacts",
        "--no-text",
        "--json",
    ]
    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True, check=True, env=os.environ
        )
    except subprocess.CalledProcessError as exc:
        raise HTTPException(status_code=500, detail=exc.stderr.strip())

    try:
        return json.loads(result.stdout or "{}")
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=500, detail=str(exc))
