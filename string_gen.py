import asyncio
from pyrogram import Client
api_id = 39637283  # ⚠️ Yahan apni asli API ID dalo (Numbers mein)
api_hash = "0d90955a2fa71aea7650f733f23a9656"  # ⚠️ Yahan apna asli API HASH
dalo (Quotes ke andar)
async def main():
    app = Client("my_account", api_id=api_id, api_hash=api_hash, in_memory=True)
    await app.start()
    session_string = await app.export_session_string()
    print("\n\n✅  YEH RAHA TUMHARA NAYA SESSION STRING. ISKO COPY KAR LO:\n")    print(session_string)
    print("\n")
    await app.stop()
asyncio.run(main())
