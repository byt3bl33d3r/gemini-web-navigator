import time
import asyncio
from io import BytesIO
from base64 import b64encode
from PIL import Image
from omniparser.omniparser import Omniparser
from typing import Annotated
from fastapi import FastAPI, Request

app = FastAPI()

@app.get("/healthcheck/")
async def healthcheck():
    return "OK"

@app.post("/omniparser/")
async def run_omniparser(request: Request):
    parser = Omniparser()

    #  time the parser
    s = time.time()

    image, parsed_content_list, label_coordinates = await asyncio.to_thread(
        parser.parse,
        Image.open(BytesIO(await request.body()))
    )

    byte_stream = BytesIO()
    image.save(byte_stream, format='PNG')

    print(f"parsed_content_list={len(parsed_content_list.keys())}")
    print(f"Time taken for Omniparser: {time.time() - s}")

    #print(type(byte_stream), type(parsed_content_list), type(label_coordinates))

    return {
        "annotated_image": b64encode(byte_stream.getvalue()).decode(),
        "content": parsed_content_list,
        "label_coordinates": { k: [float(f) for f in v] for k,v in label_coordinates.items() }
    }
