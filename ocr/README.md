# OCR Server

This is a simple FastAPI-based microservice that just wraps the PaddleOCR library and returns its output via JSON. The URL to this needs to be passed to the Omniparser service in this repo via the `OCR_SERVICE_URL` environment variable.

## Running

`uv run uvicorn ocr.server:app`