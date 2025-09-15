FROM python:3.11-slim

WORKDIR /app
COPY . /app

RUN pip install --no-cache-dir fastapi uvicorn python-dotenv playwright
RUN pip install --no-cache-dir .

# Install Playwright browsers to support --render-js
RUN python -m playwright install --with-deps

EXPOSE 8877
CMD ["uvicorn", "integration.api:app", "--host", "0.0.0.0", "--port", "8877"]
