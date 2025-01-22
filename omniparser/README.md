# Omniparser Server

This is a FastAPI microservice that runs [Omniparser](https://github.com/microsoft/OmniParser) and returns the annotated image, captions and label coordinates as JSON.

Before using, follow the instructions in the Omniparser repo's readme to download the model weights under the `wights/` folder.

See the `CHANGES` file for a list of changes from the original codebase.

## Running 

This service depends on the `ocr` service in this repo, you need to pass the URL to the `ocr` service via the `OCR_SERVICE_URL` environment variable.

`OCR_SERVICE_URL=http://localhost:8000/ocr/ uv run uvicorn omniparser.server:app --port 8080`