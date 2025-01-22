FROM mcr.microsoft.com/devcontainers/python:1-3.12-bookworm
WORKDIR /app
COPY . .

RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1-mesa-glx \
    && rm -rf /var/lib/apt/lists/*

RUN pip3 install .

CMD [ "uvicorn", "--host", "0.0.0.0", "omniparser.server:app" ]