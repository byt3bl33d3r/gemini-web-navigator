FROM mcr.microsoft.com/devcontainers/python:1-3.12-bookworm
WORKDIR /app
COPY . .

RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1-mesa-glx \
    && rm -rf /var/lib/apt/lists/*

RUN pip3 install .

# This core dumps for some reason....
#RUN python3 -c 'from paddleocr import PaddleOCR; ocr = PaddleOCR(lang="en")'

# Pre-downloads the model
#RUN mkdir -p .paddleocr/det .paddleocr/rec .paddleocr/cls && \
#    curl -O -P .paddleocr/det https://paddleocr.bj.bcebos.com/PP-OCRv3/english/en_PP-OCRv3_det_infer.tar && \
#    curl -O -P .paddleocr/rec https://paddleocr.bj.bcebos.com/PP-OCRv4/english/en_PP-OCRv4_rec_infer.tar && \
#    #curl -O -P .padddleocr/cls https://paddleocr.bj.bcebos.com/dygraph_v2.0/ch/ch_ppocr_mobile_v2.0_cls_infer.tar && \
#    tar -xf .paddleocr/det/en_PP-OCRv3_det_infer.tar -C .paddleocr/det && \
#    tar -xf .paddleocr/rec/en_PP-OCRv4_rec_infer.tar -C .paddleocr/rec
#    #tar -xf .paddleocr/cls/ch_ppocr_mobile_v2.0_cls_infer.tar -C .paddleocr/cls

CMD [ "uvicorn", "--host", "0.0.0.0", "ocr.server:app" ]