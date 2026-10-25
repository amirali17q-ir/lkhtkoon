"""Telegram bot + tiny local helper for the camera page.

- /start  -> button that opens the Mini App (the GitHub Pages site)
- Owner only: the button link carries a per-run secret key, and photos/videos
  captured in the page are uploaded to this script (127.0.0.1) and forwarded
  to the owner's Telegram chat. Nothing is saved on the phone.
- Everyone else gets the plain page: no capture, no key.
"""
import asyncio
import hmac
import io
import secrets
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, InputFile, Update, WebAppInfo
from telegram.ext import Application, CommandHandler, ContextTypes

BASE = Path(__file__).parent
PORT = 8765
MAX_BYTES = 45 * 1024 * 1024  # Telegram bot upload limit is 50 MB
KEY = secrets.token_urlsafe(9)  # new key every run
LOOP = None
APP = None


def read(name, required=True):
    path = BASE / name
    if path.exists():
        return path.read_text().strip()
    if required:
        raise SystemExit(f"{name} not found. Run: bash setup.sh")
    return ""


TOKEN = read("token.txt")
URL = read("url.txt").rstrip("/") + "/"
_owner = read("owner.txt", required=False)
OWNER_ID = int(_owner) if _owner.isdigit() else None


async def deliver(kind: str, data: bytes, ext: str):
    bot = APP.bot
    if kind == "photo":
        await bot.send_photo(OWNER_ID, io.BytesIO(data))
    elif ext == "mp4":
        await bot.send_video(OWNER_ID, InputFile(io.BytesIO(data), filename="clip.mp4"), supports_streaming=True)
    else:
        await bot.send_document(OWNER_ID, InputFile(io.BytesIO(data), filename=f"clip.{ext}"))


class Handler(BaseHTTPRequestHandler):
    def _cors(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "X-Key, Content-Type")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Private-Network", "true")

    def _reply(self, code, text=""):
        body = text.encode()
        self.send_response(code)
        self._cors()
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self):
        self._reply(204)

    def do_GET(self):
        self._reply(200, "ok") if urlparse(self.path).path == "/ping" else self._reply(404)

    def do_POST(self):
        url = urlparse(self.path)
        if url.path != "/upload":
            return self._reply(404)
        if OWNER_ID is None or not hmac.compare_digest(self.headers.get("X-Key", ""), KEY):
            return self._reply(403)
        size = int(self.headers.get("Content-Length", 0))
        if size <= 0 or size > MAX_BYTES:
            return self._reply(413)
        data = self.rfile.read(size)
        q = parse_qs(url.query)
        kind = q.get("kind", ["photo"])[0]
        ext = q.get("ext", ["jpg"])[0]
        if kind not in ("photo", "video") or ext not in ("jpg", "mp4", "webm"):
            return self._reply(400)
        try:
            asyncio.run_coroutine_threadsafe(deliver(kind, data, ext), LOOP).result(timeout=120)
            self._reply(200, "sent")
        except Exception as e:  # noqa: BLE001
            print("send failed:", e)
            self._reply(500)

    def log_message(self, *args):
        pass


async def start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    is_owner = OWNER_ID is not None and update.effective_user.id == OWNER_ID
    if is_owner:
        link = f"{URL}?k={KEY}"
        rows = [
            [InlineKeyboardButton("👁 حقایق دنیا", web_app=WebAppInfo(url=link))],
            [InlineKeyboardButton("🌐 باز کردن در کروم", url=link)],
        ]
    else:
        rows = [[InlineKeyboardButton("👁 حقایق دنیا", web_app=WebAppInfo(url=URL))]]
    await update.message.reply_text("برای دیدن حقایق دنیا، کلید رو بزن", reply_markup=InlineKeyboardMarkup(rows))


async def my_id(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(str(update.effective_user.id))


async def post_init(app: Application):
    global LOOP, APP
    LOOP, APP = asyncio.get_running_loop(), app
    server = ThreadingHTTPServer(("127.0.0.1", PORT), Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    if OWNER_ID is None:
        print("! owner.txt missing: capture is OFF. Send /id to the bot, then: echo ID > owner.txt")
    print(f"Bot running. Local helper on 127.0.0.1:{PORT}. Send /start to the bot.")


def main():
    app = Application.builder().token(TOKEN).post_init(post_init).build()
    app.add_handler(CommandHandler(["start", "dino"], start))
    app.add_handler(CommandHandler("id", my_id))
    app.run_polling()


if __name__ == "__main__":
    main()
