import asyncio
from pyrogram import idle
from core import app, assistant, call
async def start_bot():
    print("Starting Bot Client...")
    await app.start()
    print("Starting Assistant Client...")
    await assistant.start()
    print("Starting PyTgCalls (VC Client)...")
    await call.start()
    print("Bot is Alive and Lightning Fast! 🚀")
    # Yeh line bot ko 24/7 zinda rakhegi
    await idle()
if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(start_bot())
