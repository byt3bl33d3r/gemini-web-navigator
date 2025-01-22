import time
import os
from io import BytesIO
from PIL import Image
from typing import Annotated
from fastapi import FastAPI, Request
from paddleocr import PaddleOCR
import numpy as np

app = FastAPI()

paddle_ocr = PaddleOCR(
    lang='en',  # other lang also available
    use_angle_cls=False,
    use_gpu=True if bool(os.environ.get('USE_GPU')) else False,  # using cuda will conflict with pytorch in the same process
    show_log=False,
    max_batch_size=1024,
    use_dilation=True,  # improves accuracy
    det_db_score_mode='slow',  # improves accuracy
    rec_batch_num=1024
    #det_model_dir="/app/.paddleocr/det",
    #rec_model_dir="/app/.paddleocr/rec"
)

@app.get("/healthcheck/")
async def healthcheck():
    return "OK"

@app.post("/ocr/")
async def do_ocr(request: Request):
    #  time the parser
    s = time.time()

    image_array = np.array(Image.open(BytesIO(await request.body())))

    result = paddle_ocr.ocr(image_array, cls=False)[0]
    coord = [item[0] for item in result]
    text = [item[1][0] for item in result]

    print(f"Time taken for OCR: {time.time() - s}")

    return {
        "coord": coord,
        "text": text
    }
