from fastapi import FastAPI, HTTPException, Query
import subprocess
import json
import os
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()


@app.get("/run")
def run(url: str = Query(..., description="URL to process")):
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
