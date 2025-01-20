# Gemini Web Navigator Experiments

This repo contains Proof-of-Concept code, experiments & notes about using Google Gemini's Vision capabilities and [Computer Use](https://docs.anthropic.com/en/docs/build-with-claude/computer-use)-style desktop manipulation for LLM enabled browser control.

## Background

One of the most unique features of [Google Gemini](https://gemini.google.com/?hl=en-GB) is it's ability to [return bounding box coordinates](https://ai.google.dev/gemini-api/docs/vision?lang=python#bbox) on objects in images (see [this blog post](https://simonwillison.net/2024/Aug/26/gemini-bounding-box-visualization/) for a nice overview).

This got me thinking: how does it perform when asked to return bounding box coordinates for web page elements? Turns out it works suprisingly well on simple/medium complexity web pages.

As this is a *PURELY* vision based LLM browser control system, you have the ability to select web page elements to interact with through screenshots using natural language but it also gives you a lot of the same cabilities of other projects like [browser-use](https://github.com/browser-use/browser-use) or [skyvern](https://github.com/Skyvern-AI/skyvern) "on the cheap": no injecting custom JS into the browser context to highlight interactive elements on the webpage or complicated Agentic systems.

Just to be clear I'm not saying this is better than the other projects I mentioned above, I'm just saying it's cheaper: this is ~200 lines of Python, no agentic system necessary and works suprisingly well on simple/medium complexity webpages. Choose the best tool for your use case.

## Bypassing non-captcha based anti-bot products

An interesting consequence to using this approach is that you're able to bypass most non-captcha based anti-bot products out of the box like [Cloudflare Turnstile](https://www.cloudflare.com/application-services/products/turnstile/). It's probably also effective against the "press and hold left mouse button"-style bot shields as well.

From what I can surmise, this works mainly because of the following:
1. We're using [patchright](https://github.com/Kaliiiiiiiiii-Vinyzu/patchright-python)
2. We're not starting the browser in headless mode (we have a containerized desktop environment)
3. We're not injecting custom JS into browser context.
4. We're not disabling the Chrome sandbox (we're passing a `seccomp` profile to the docker container to start Chromium with all security features enabled)
5. Mouse/Keyboard inputs are done through the desktop using a "Computer Use" style system, not using browser events (e.g. `mouseup`, `mousedown` etc..)

Below is a video demonstration of this approach: the LLM bypasses Cloudflare Turnstyle and automatically navigates through a website to perform a search:

[![Demo Video](https://img.youtube.com/vi/JO8jMHpOW90/0.jpg)](https://www.youtube.com/watch?v=JO8jMHpOW90)

The "secret sauce" (if you can call it that) to bypass Turnstile are the following lines in the workflow YAML file we're passing on the command line ([full workflow file here](https://github.com/byt3bl33d3r/gemini-web-navigator/blob/29ec97781fd7e66f813ec6dabcd1a705439833c2/examples/securitytrails.yaml)):

```yaml
actions:

  # This bypasses Cloudflare Turnstile
  - element: checkbox to the left of "Verify you are human"
    do:
      - click:

```

This is just asking Gemini to return the bounding box coordinates in the screenshot it takes under the hood for the `checkbox to the left of "Verify you are human"` and then clicking on the returned coordinates through the desktop 💀.

## Installation

Easiest way to play around with this:

1. Install Docker Desktop
2. Clone this repo and open in VScode
3. Install the Dev Containers extension
4. Click "Re-open in devcontainer" when prompted or through the command pallete.
5. Create a `.env` file or export your `GEMINI_API_KEY=`.

Once everything is started, you'll have a `noVnc` session at `localhost:6081` that you can use to interact with the containerized desktop env and to watch the LLM control the browser.

It's obviously possible to make a standalone `Dockefile` for this it's just a lot easier for my workflow this way. (PRs welcome!)

## Usage

You just need to give the path to a workflow YAML file to `gemini_navigator.py`. Workflow files are pretty self explanitory. Below is an example, check out the `examples` folder in this repo for more:

```yaml
url: https://securitytrails.com # Starting URL

config:
  interaction_pause: 3 # delay between each action
  wait_until: networkidle # Playwright .goto() wait_until argument

actions:

  # This bypasses Cloudflare Turnstile
  - element: checkbox to the left of "Verify you are human"
    do:
      - click:

  - element: main search bar # You can select any element to interact with using natural language
    do:
      - click:
      - type: example.com

  - element: search button
    do:
      - click:
      - screenshot:
```

They'll be a `pic.png` file created on each action that will have the screenshot with a drawn bounding box represting the coordinates Gemini returned.