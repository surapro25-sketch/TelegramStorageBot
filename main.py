import os
import asyncio

# Fix for Python 3.14 event loop handling in Pyrogram
try:
    asyncio.get_running_loop()
except RuntimeError:
    asyncio.set_event_loop(asyncio.new_event_loop())

import aiohttp
from pyrogram import Client, filters
from pyrogram.types import Message

# ================= CONFIGURATION =================
API_ID = 32740276
API_HASH = "4880a0847fc23cfee0fc6d562389b2bd"
BOT_TOKEN = "8828493327:AAGMJSsaUp-JKiTvdCbKjtuxF_FAJvx5FPw"  # Update with your new token from @BotFather

STORAGE_TO_URL = "https://storage.to/api/sharex/upload"
# =================================================

app = Client("storage_uploader_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)


class MediaStreamer:
    """Streams byte chunks directly from MTProto servers to the HTTP request."""
    def __init__(self, client: Client, message: Message):
        self.client = client
        self.message = message

    async def __aiter__(self):
        # Stream chunks directly from Telegram without chunk_size parameter
        async for chunk in self.client.stream_media(self.message):
            yield chunk


@app.on_message(filters.command("start"))
async def start_cmd(client: Client, message: Message):
    await message.reply_text("⚡ **SURA BOT Direct Stream Online!**\nSend or forward any file to stream directly to Storage.to.")


@app.on_message()
async def direct_stream_handler(client: Client, message: Message):
    if not (message.document or message.video or message.audio or message.photo):
        return

    media = message.document or message.video or message.audio or message.photo
    file_name = getattr(media, "file_name", "file.bin") or "file.bin"
    file_size = getattr(media, "file_size", 0)
    size_mb = round(file_size / (1024 * 1024), 2)

    status_msg = await message.reply_text(f"🚀 **Streaming Pipeline Started:** `{file_name}` ({size_mb} MB)...")

    try:
        async with aiohttp.ClientSession() as session:
            form = aiohttp.FormData()
            form.add_field(
                name="file",
                value=MediaStreamer(client, message),
                filename=file_name
            )

            async with session.post(STORAGE_TO_URL, data=form) as response:
                if response.status in (200, 201):
                    res = await response.json()
                    link = res.get("url") or res.get("download_link") or res.get("link", "Uploaded")
                    await status_msg.edit_text(
                        f"✅ **Stream Complete!**\n\n"
                        f"📁 **File:** `{file_name}`\n"
                        f"💾 **Size:** {size_mb} MB\n\n"
                        f"🔗 **Download Link:** {link}"
                    )
                else:
                    err = await response.text()
                    await status_msg.edit_text(f"❌ **Upload Failed ({response.status}):** {err}")

    except Exception as e:
        await status_msg.edit_text(f"❌ **Streaming Error:** {str(e)}")


if __name__ == "__main__":
    print("SURA BOT Backend actively listening...")
    app.run()