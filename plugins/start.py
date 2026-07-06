from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
# 🖼️ YAHAN APNI IMAGE KA LINK DAALO
START_IMG_URL = "https://i.ibb.co/dwxMbZnj/file-68.jpg"
@Client.on_message(filters.command("start") & filters.private)
async def start_command(client: Client, message: Message):
    # Bot ka naam aur username automatic fetch hoga
    bot_name = client.me.first_name
    bot_username = client.me.username
    # 👇 Yahan maine har line ke baad \n\n laga diya hai exact spacing ke liye
    caption_text = (
        f"ʜᴇʏ {message.from_user.mention} , 🥀\n\n"
        f"⊙ ᴛʜɪs ɪs {bot_name} 🌸\n\n"
        f"➻ ᴀ ғᴀsᴛ & ᴘᴏᴡᴇʀғᴜʟ ᴛᴇʟᴇɢʀᴀᴍ ᴍᴜsɪᴄ ᴘʟᴀʏᴇʀ ʙᴏᴛ ᴡɪᴛʜ sᴏᴍᴇ ᴀᴡᴇsᴏᴍᴇ ғᴇᴀᴛᴜʀᴇs.\n\n"
        f"⊙ ᴄʟɪᴄᴋ ᴏɴ ᴛʜᴇ ʜᴇʟᴘ ʙᴜᴛᴛᴏɴ ᴛᴏ ɢᴇᴛ ɪɴғᴏʀᴍᴀᴛɪᴏɴ ᴀʙᴏᴜᴛ ᴍʏ ᴍᴏᴅᴜʟᴇs ᴀɴᴅ
ᴄᴏᴍᴍᴀɴᴅs."
    )
    # 👇 Buttons ekdum screenshot wale style mein (2 full width, 1 half width)
    buttons = InlineKeyboardMarkup([
        [InlineKeyboardButton("ᴀᴅᴅ ᴍᴇ ɪɴ ʏᴏᴜʀ ɢʀᴏᴜᴘ ⁺", url=f"https://t.me/{bot_username}?startgroup=true")],
        [InlineKeyboardButton("ʜᴇʟᴘ & ᴄᴏᴍᴍᴀɴᴅs", callback_data="help_menu")],
        [
            InlineKeyboardButton("ᴅᴇᴠᴇʟᴏᴘᴇʀ ↗", url="https://t.me/rushdeveloper"),
            InlineKeyboardButton("ᴄʜᴀɴɴᴇʟ ↗", url="https://t.me/rushbots")
        ]
    ])
    try:
        await message.reply_photo(
            photo=START_IMG_URL,
            caption=caption_text,
            reply_markup=buttons
        )
    except Exception as e:
        print(f"Image load failed: {e}")
        # Agar image fail ho toh text bhejega
        await message.reply_text(
            text=caption_text,
            reply_markup=buttons
        )
