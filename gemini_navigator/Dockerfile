FROM python:3.12-bookworm

WORKDIR /app

RUN apt-get update && apt-get install -y xdotool gnome-screenshot

COPY . .

RUN pip3 install -r requirements.txt

RUN patchright install-deps && patchright install

ENTRYPOINT [ "python3", "gemini_navigator.py" ]
