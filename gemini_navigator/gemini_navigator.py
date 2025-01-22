import asyncio
import argparse
import io
import json
import sys
import base64
import google.generativeai as genai
import shutil
import shlex
import itertools
import yaml
import tempfile
import tkinter as tk
from yaml import Loader
from uuid import uuid4
from pathlib import Path
from markitdown import MarkItDown
from collections import namedtuple
from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict
from patchright.async_api import async_playwright
from PIL import Image, ImageDraw
from utils import run

OUTPUT_DIR = '/tmp/outputs'

Coordinates = namedtuple("Coordinates", ["ymin", "xmin", "ymax", "xmax"])

class ComputerUseError(Exception):
    pass

class Settings(BaseSettings):
    model_config: SettingsConfigDict = SettingsConfigDict(env_file='.env', extra='ignore')
    gemini_api_key: SecretStr

class ComputerUse:
    _SCREENSHOT_DELAY = 2.0
    _TYPING_DELAY_MS = 12
    _TYPING_GROUP_SIZE = 50

    async def key(self, text: str):
        return await self.shell(f"xdotool key -- {text}")

    async def type(self, text: str, delay: int | None  = None):
        for chunk in itertools.batched(text, n=self._TYPING_GROUP_SIZE):
            await self.shell(
                f"xdotool type --delay {delay or self._TYPING_DELAY_MS} -- {shlex.quote(''.join(chunk))}",
                take_screenshot=False
            )

        return (await self.screenshot())[2]

    async def left_click(self):
        return await self.shell("xdotool click 1")

    async def mouse_move(self, x: int, y: int):
        return await self.shell(f"xdotool mousemove --sync {x} {y}")

    async def screenshot(self):
        """Take a screenshot of the current screen and return the base64 encoded image."""
        output_dir = Path(OUTPUT_DIR)
        output_dir.mkdir(parents=True, exist_ok=True)
        path = output_dir / f"screenshot_{uuid4().hex}.png"

        if not shutil.which("gnome-screenshot"):
            raise ComputerUseError("Unable to find gnome-screenshot")

        screenshot_cmd = f"gnome-screenshot -f {path} -p"            

        stdout,stderr,_ = await self.shell(screenshot_cmd, take_screenshot=False)
        if path.exists():
            return stdout, stderr, base64.b64encode(path.read_bytes()).decode()

        raise ComputerUseError(f"Failed to take screenshot: {stderr}")

    async def shell(self, command: str, take_screenshot=True) -> tuple:
        """Run a shell command and return the output, error, and optionally a screenshot."""
        _, stdout, stderr = await run(command)
        base64_image = None

        if take_screenshot:
            # delay to let things settle before taking a screenshot
            await asyncio.sleep(self._SCREENSHOT_DELAY)
            base64_image = (await self.screenshot())[2]

        return stdout, stderr, base64_image

class GeminiVision:
    def __init__(self, computer_use: ComputerUse):
        self.computer_use = computer_use
        self.screen_width, self.screen_height = self.get_screen_size()
        self.model = genai.GenerativeModel(model_name='gemini-1.5-pro')

    def get_screen_size(self) -> tuple[int,int]:
        # Create a tkinter root window
        root = tk.Tk()

        # Get screen dimensions
        screen_width = root.winfo_screenwidth()
        screen_height = root.winfo_screenheight()

        root.destroy()

        return screen_width, screen_height

    async def get_bounding_box_center(self, element_description: str):

        ymin, xmin, ymax, xmax = await self.get_bounding_box(element_description)

        center_x = (xmin + xmax) / 2
        center_y = (ymin + ymax) / 2

        print(center_x, center_y)

        return center_x, center_y

    async def get_bounding_box(self, element_description: str) -> tuple:
        prompt = f"Return a bounding box for the {element_description} in [ymin, xmin, ymax, xmax] format."

        screenshot = base64.b64decode(
            (await self.computer_use.screenshot())[2]
        )
        screenshot = Image.open(
            io.BytesIO(screenshot)
        )

        while True:
            try:
                response = json.loads(
                    (await self.model.generate_content_async([screenshot, prompt])).text
                )
                break
            except json.JSONDecodeError:
                print("json decode error")

        print(response)
        box = Coordinates(*response)

        draw = ImageDraw.Draw(screenshot)
        ymin = (box.ymin / 1000) * self.screen_height
        ymax = (box.ymax / 1000) * self.screen_height
        xmin = (box.xmin / 1000) * self.screen_width
        xmax = (box.xmax / 1000) * self.screen_width

        draw.rectangle([xmin, ymin, xmax, ymax], outline="red", width=2)
        screenshot.save('pic.png')

        return ymin, xmin, ymax, xmax

def convert_to_markdown(html: str):
    md = MarkItDown()
    with io.StringIO(html) as s:
        return md.convert_stream(s, file_extensions='.html').text_content

def manual_mode():
    parser = argparse.ArgumentParser()
    parser.add_argument('workflow_yaml_file', type=Path, metavar="workflow_yaml_file")
    args = parser.parse_args()

    if not args.workflow_yaml_file.exists():
        print('path to workflow yaml file does not exist!')
        sys.exit(1)

    settings = Settings()
    genai.configure(api_key=settings.gemini_api_key.get_secret_value())

    async def main():
        computer_use = ComputerUse()
        gemini_vision = GeminiVision(computer_use)

        with tempfile.TemporaryDirectory() as tmpdir:
            async with async_playwright() as p:
                context = await p.chromium.launch_persistent_context(
                    user_data_dir=tmpdir,
                    channel='chromium',
                    headless=False,
                    no_viewport=True,
                    # args=[
                    #     '--no-first-run',
                    #     '--no-default-browser-check',
                    #     '--no-startup-window',
                    #     '--window-position=0,0',
                    # ]
                )

                page = await context.new_page()

                with args.workflow_yaml_file.open() as f:
                    workflow: dict= yaml.load(f, Loader=Loader)
                    url: dict = workflow['url']
                    config: dict = workflow['config']

                await page.goto(url=url, wait_until=config.get('wait_until', 'networkidle'))

                for action in workflow['actions']:
                    await asyncio.sleep(config['interaction_pause'])

                    center_x, center_y = await gemini_vision.get_bounding_box_center(action['element'])

                    for desktop_action in action['do']:
                        for name,action_config in desktop_action.items():

                            if name == 'click':
                                await computer_use.mouse_move(x=center_x, y=center_y)
                                await computer_use.left_click()

                            if name == 'type':
                                await computer_use.type(desktop_action.get('type'))

                            if name == 'screenshot':
                                await page.screenshot(path='final_screenshot.png')

                            if name == 'markdownify':
                                with open('final_page.md', 'w') as f:
                                    f.write(
                                        await asyncio.to_thread(
                                            convert_to_markdown,
                                            await page.content()
                                    ))

    asyncio.run(main())

if __name__ == '__main__':
    manual_mode()
