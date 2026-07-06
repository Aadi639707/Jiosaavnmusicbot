from pyrogram import Client, filters
from pyrogram.types import Message
import asyncio
import os
OWNER_IDS = [8924549820, 8306853454]
@Client.on_message(filters.command("broadcast") & filters.user(OWNER_IDS))
async def broadcast_system(client: Client, message: Message):
    if not message.reply_to_message:
        return await message.reply_text("⚠️ <b>ᴇʀʀᴏʀ:</b> ᴋɪsɪ ᴍᴇssᴀɢᴇ ᴋᴏ ʀᴇᴘʟʏ ᴋᴀʀᴋᴇ `/broadcast` ʟɪᴋʜᴏ!")
    # Check karo ki database file exist karti hai ya nahi
    if not os.path.exists("chats.txt"):
        return await message.reply_text("⚠️ <b>ᴅᴀᴛᴀʙᴀsᴇ ᴇᴍᴘᴛʏ:</b> ʙᴏᴛ ɴᴇ ᴀʙʜɪ ᴛᴀᴋ ᴋᴏɪ ᴄʜᴀᴛ sᴀᴠᴇ ɴᴀʜɪ ᴋɪ ʜᴀɪ.")
    m = await message.reply_text("⏳  <b>ʙʀᴏᴀᴅᴄᴀsᴛ ɪɴ ᴘʀᴏɢʀᴇss...</b>\nᴘʟᴇᴀsᴇ
ᴡᴀɪᴛ, DM, Groups ᴀᴜʀ Channels ᴍᴇɪɴ ᴍᴇssᴀɢᴇ ᴊᴀᴀ ʀᴀʜᴀ ʜᴀɪ.")
    # Save ki hui IDs padho
    with open("chats.txt", "r") as f:
        chats = f.read().splitlines()
    successful = 0
    failed = 0
    # Har ID par message copy karke bhejo
    for chat_id in chats:
        try:
            await message.reply_to_message.copy(int(chat_id))
            successful += 1
            await asyncio.sleep(0.3) # Spam ban se bachne ke liye delay
        except Exception:
            failed += 1
    report = (
        f"✅  <b>ʙʀᴏᴀᴅᴄᴀsᴛ ᴄᴏᴍᴘʟᴇᴛᴇ!</b>\n\n"
        f"🟢 sᴜᴄᴄᴇssғᴜʟ : {successful}\n"
        f"🔴 ғᴀɪʟᴇᴅ / ʙʟᴏᴄᴋᴇᴅ : {failed}"
    )
    await m.edit_text(report)
