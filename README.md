# 👁 Camera AR Dino

A mobile-first web experience that opens the camera and drops an animated 3D dinosaur on the floor of your room. Built with plain HTML + three.js (no build step), hostable on GitHub Pages, and optionally wired to a Telegram bot (Mini App) that forwards photos and videos straight to your chat.

## Features

- Live camera background (`getUserMedia`, rear camera) with a three.js scene on top
- Procedural low-poly dinosaur: walking cycle, tail wag, breathing, roar
- Tap the floor to make the dino walk there; scale up/down; stop
- Gyroscope mode: the dino stays put in the room while you turn the phone
- Clear permission diagnostics (HTTPS check, blocked camera, in-app browser, busy camera)
- Telegram Mini App entry via a bot
- Photo and video capture (dino + camera) sent directly to Telegram, nothing stored on the phone
- Capture is opt-in per tap and only enabled for the bot owner

## Project structure

```
index.html        the whole web app (HTML + CSS + JS, three.js from CDN)
bot.py            Telegram bot + local helper that forwards captures
setup.sh          one-time Termux setup (installs deps, writes local config)
requirements.txt  python-telegram-bot
.gitignore        keeps token/owner/url files out of git
```

## Run the web app

1. Put `index.html` at the root of a public repo.
2. Settings → Pages → Deploy from branch → `main` / `/ (root)`.
3. Open the HTTPS URL in Chrome (cameras do not work on plain HTTP or `file://`).

Add `?debug` to the URL to show the no-camera test mode and diagnostics line.

## Run the bot (Termux on Android)

```bash
pkg install git
git clone https://github.com/<you>/<repo>.git && cd <repo>
bash setup.sh          # asks for token, page URL, optional owner ID
termux-wake-lock; python bot.py
```

Then send `/start` to the bot. To enable capture, send `/id` to the bot, save the number with `echo ID > owner.txt`, restart `bot.py`, and send `/start` again.

## How capture works

The page is served over HTTPS, the bot runs on the same phone. The owner's button opens the page with a random per-run key. The page checks `http://127.0.0.1:8765/ping`; if the bot is running it shows 📸 / ⏺ buttons and uploads the result to the local helper, which forwards it with the Bot API. If the bot is off, or someone else opens the page, the buttons never appear and the page behaves normally.

## Security notes

- The bot token never leaves `token.txt` and is never sent to the browser.
- The helper only listens on `127.0.0.1` and requires the per-run key.
- Rotate the token with `/revoke` in @BotFather if it is ever exposed.
- The camera feed is processed locally in the browser; nothing is recorded unless you tap the capture buttons.

## Roadmap

- Replace the procedural dino with a `.glb` model
- Multiple creatures to choose from
- Real surface detection with WebXR
