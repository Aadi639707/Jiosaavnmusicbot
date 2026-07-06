from pyrogram import Client
import asyncio
api_id = 1234567  # ⚠️ Apni API ID dalo
api_hash = "b69f8f202f9dd4781a"  # ⚠️ Apna API HASH dalo
session_string = "BQHdWNgAbOtmZo7vB3Pmbh2mafxx5WxFN7-aWSr3LIMUMXpBy_vqsiJsLouYlN2xAA"
async def main():
    print("Checking Session String...")
    try:
        app = Client("test_session", api_id=api_id, api_hash=api_hash, session_string=session_string, in_memory=True)
        await app.start()
        print("\n✅  BHAI! SESSION EKDUM ZINDA HAI! BOT START KAR SAKTE HAIN!")
        await app.stop()
    except Exception as e:
        print(f"\n❌  DEAD SESSION ERROR: {e}")
asyncio.run(main())
