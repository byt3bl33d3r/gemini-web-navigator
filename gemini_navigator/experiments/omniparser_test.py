import httpx
import base64
import json
import sys
from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict
from PIL import Image
import google.generativeai as genai

SCREENSHOT_PROMPT = """
<instructions>
Given the element requested by the user, you are tasked with finding the appropriate bounding box number based on the provided screenshot and the content/coordinates given to you in <box_coordinates></box_coordinates> tags.

Always verify you found the correct element by comparing the bounding box number to the element indexes given to you in the JSON data in <box_coordinates></box_coordinates> tags before returning the bounding box number.

Return only the bounding box number and nothing else.

GUIDELINES:
    - Use the provided image to understand the page layout
    - Bounding boxes with labels correspond to the element indexes in the JSON data given to you in the <box_coordinates></box_coordinates> tags
    - Most often the label is inside the bounding box, on the top right
    - Visual context helps verify element locations and relationships
    - sometimes labels overlap, so use the JSON data given to you in the <box_coordinates></box_coordinates> tags to verify the correct element
</instructions>

<box_coordinates>
{JSON_ELEMENT_COORDINATES}
</box_coordinates>
"""

class Settings(BaseSettings):
    model_config: SettingsConfigDict = SettingsConfigDict(env_file='.env', extra='ignore')
    gemini_api_key: SecretStr

def request_annotation():
    with open('experiments/test_screen.png', 'rb') as f:
        r = httpx.post('http://localhost:8080/omniparser/', content=f.read(), timeout=120)

    result = r.json()
    image_data = result.pop('annotated_image')

    with open('experiments/annotated.png', 'wb') as fa:
        fa.write(base64.b64decode(image_data))
    
    with open('experiments/parsed_data.json', 'w') as fj:
        json.dump(result, fj, indent=4)

def get_bounding_box(prompt: str):
    settings = Settings()
    genai.configure(api_key=settings.gemini_api_key.get_secret_value())

    with open('experiments/parsed_data.json') as f:
        omniparser_results = json.load(f)

    model = genai.GenerativeModel(
        model_name='gemini-1.5-pro',
        system_instruction=SCREENSHOT_PROMPT.format(
            JSON_ELEMENT_COORDINATES=json.dumps(omniparser_results, indent=2)
        )
    )

    screenshot = Image.open(
        "experiments/annotated.png"
    )

    content = model.generate_content([screenshot, prompt])
    bb_number = content.text
    print(bb_number, omniparser_results['content'][bb_number], omniparser_results['label_coordinates'][bb_number])

    screenshot.close()

if __name__ == "__main__":
    #request_annotation()
    get_bounding_box(sys.argv[1])
