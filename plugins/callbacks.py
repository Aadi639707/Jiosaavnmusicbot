from pyrogram import Client, filters
from pyrogram.types import CallbackQuery, Message, InlineKeyboardMarkup, InlineKeyboardButton
from pytgcalls.types import MediaStream, Update
import asyncio
from core import call, music_queue, app
# 🛡️ BULLETPROOF ADMIN CHECK
async def is_admin(client, chat_id, user_id):
    if user_id in [client.me.id, chat_id]: return True
    try:
        member = await client.get_chat_member(chat_id, user_id)
        if "ADMINISTRATOR" in str(member.status).upper() or "OWNER" in str(member.status).upper():
            return True
        return False
    except: return False
# ==========================================
# 🧠 VERIFIED PLAY_NEXT SYSTEM (With Pre-Download)
# ==========================================
async def play_next_system(chat_id, is_auto=False):
    if chat_id not in music_queue or not music_queue[chat_id]:
        try: await call.leave_call(chat_id)
        except: pass
        return
    import os
    old_song = music_queue[chat_id].pop(0)
    try:
        if os.path.exists(old_song["file_path"]):
            os.remove(old_song["file_path"])
    except: pass
    if not music_queue[chat_id]:
        try: await call.leave_call(chat_id)
        except: pass
        return
    next_song = music_queue[chat_id][0]
    try:
        if is_auto: await asyncio.sleep(0.5)
        try:
            await call.change_stream(chat_id, MediaStream(next_song["file_path"]))
        except Exception:
            try:
                await call.play(chat_id, MediaStream(next_song["file_path"]))            except Exception:
                await call.leave_call(chat_id)
                await asyncio.sleep(0.5)
                await call.play(chat_id, MediaStream(next_song["file_path"]))
        bot_username = app.me.username
        play_text = f"⏭ <b>sᴋɪᴘᴘᴇᴅ ᴛᴏ ɴᴇxᴛ ᴛʀᴀᴄᴋ</b>\n\nᴛɪᴛʟᴇ : {next_song['title']}\nᴅᴜʀᴀᴛɪᴏɴ : {next_song['duration']} sᴇᴄᴏɴᴅs\nʀᴇǫᴜᴇsᴛᴇᴅ ʙʏ : {next_song['requester']}"
        play_buttons = InlineKeyboardMarkup([
            [InlineKeyboardButton("▷", callback_data="resume"), InlineKeyboardButton("II", callback_data="pause"), InlineKeyboardButton("⏭", callback_data="skip"), InlineKeyboardButton("⏹", callback_data="stop")],
            [InlineKeyboardButton("ᴅᴇᴠᴇʟᴏᴘᴇʀ ↗", url="https://t.me/rushdeveloper"), InlineKeyboardButton("sᴜᴘᴘᴏʀᴛ ↗", url="https://t.me/rushbots")],
            [InlineKeyboardButton("+ ᴀᴅᴅ ᴍᴇ +", url=f"https://t.me/{bot_username}?startgroup=true")]
        ])
        await app.send_photo(chat_id, photo=next_song['thumbnail'], caption=play_text, reply_markup=play_buttons)
    except Exception as e:
        print(f"Local stream failure: {e}")
        await play_next_system(chat_id, is_auto=True)
# ==========================================
# 🤖 MASTER EVENT LISTENER
# ==========================================
@call.on_update()
async def global_update_handler(client, update: Update):
    try:
        chat_id = getattr(update, "chat_id", None)
        if not chat_id: return
        update_type = type(update).__name__
        if "ChatUpdate" in update_type or hasattr(update, "status"):
            status = str(getattr(update, "status", "")).lower()
            if any(x in status for x in ["kicked", "left", "closed", "dropped"]):
                music_queue.pop(chat_id, None)
                return
        if "Ended" in update_type or "Stop" in update_type:
            await play_next_system(chat_id, is_auto=True)
    except Exception as e: pass
# ==========================================
# 🎮 CONTROLS ENGINE
# ==========================================
async def process_action(client, chat_id, action, user_id, query=None, message=None):
    if not await is_admin(client, chat_id, user_id):
        err_msg = "ᴏɴʟʏ ᴀᴅᴍɪɴs ᴄᴀɴ ᴜsᴇ ᴛʜɪs ᴄᴍᴅ."
        if query: return await query.answer(err_msg, show_alert=True)
        if message: return await message.reply_text(err_msg)
    if action in ["stop", "end"]:
        music_queue.pop(chat_id, None)
        try: await call.leave_call(chat_id)
        except: pass
        if query:
            try: await query.message.delete()
            except: pass
            return await query.answer("Stopped!")
        if message: return await message.reply_text("sᴛʀᴇᴀᴍ ᴇɴᴅᴇᴅ & ʟᴇғᴛ ᴠᴄ.")
    if chat_id not in music_queue or len(music_queue[chat_id]) == 0:
        if query: return await query.answer("Nothing playing!", show_alert=True)
        if message: return await message.reply_text("ɴᴏᴛʜɪɴɢ ɪs ᴘʟᴀʏɪɴɢ.")
    try:
        if action == "pause":
            await call.pause(chat_id)
            if query: await query.answer("Paused!")
            if message: await message.reply_text("sᴛʀᴇᴀᴍ ᴘᴀᴜsᴇᴅ.")
        elif action == "resume":
            await call.resume(chat_id)
            if query: await query.answer("Resumed!")
            if message: await message.reply_text("sᴛʀᴇᴀᴍ ʀᴇsᴜᴍᴇᴅ.")
        elif action == "skip":
            if len(music_queue[chat_id]) > 1:
                if query: await query.answer("Skipping...")
                if query:
                    try: await query.message.delete()
                    except: pass
                await play_next_system(chat_id, is_auto=False)
            else:
                music_queue.pop(chat_id, None)
                try: await call.leave_call(chat_id)
                except: pass
                if query:
                    try: await query.message.delete()
                    except: pass
                    await query.answer("Queue empty!")
                if message: await message.reply_text("ǫᴜᴇᴜᴇ ᴇᴍᴘᴛʏ. ʟᴇᴀᴠɪɴɢ ᴠᴄ.")
    except Exception as e:
        if query: await query.answer(f"Error: {str(e)[:40]}", show_alert=True)
@Client.on_callback_query(filters.regex("^(pause|resume|skip|stop|end)$"))
async def button_route(client: Client, query: CallbackQuery):
    await process_action(client, query.message.chat.id, query.data, query.from_user.id, query=query)
@Client.on_message(filters.command(["skip", "stop", "end", "pause", "resume"]) & filters.group)
async def text_route(client: Client, message: Message):
    action = message.command[0].lower().split("@")[0]
    user_id = message.from_user.id if message.from_user else message.sender_chat.id
    await process_action(client, message.chat.id, action, user_id, message=message)
# 📚 HELP MENU & BACK BUTTON (Dynamic Names)
@Client.on_callback_query(filters.regex("^help_menu$"))
async def help_menu_handler(client: Client, query: CallbackQuery):
    bot_name = client.me.first_name
    help_text = f"˹ {bot_name} ˼ ♪ ʜᴇʟᴘ ᴍᴇɴᴜ\n\n➻ /play [sᴏɴɢ] - ᴘʟᴀʏ ᴀ sᴏɴɢ\n➻ /skip - sᴋɪᴘ ᴛʀᴀᴄᴋ\n➻ /pause - ᴘᴀᴜsᴇ\n➻ /resume - ʀᴇsᴜᴍᴇ\n➻ /end ᴏʀ /stop
- ᴇɴᴅ sᴛʀᴇᴀᴍ & ʟᴇᴀᴠᴇ ᴠᴄ"
    back_button = InlineKeyboardMarkup([[InlineKeyboardButton("◁ ʙᴀᴄᴋ", callback_data="close_help")]])
    await query.message.edit_caption(caption=help_text, reply_markup=back_button)
@Client.on_callback_query(filters.regex("^close_help$"))
async def close_help_handler(client: Client, query: CallbackQuery):
    bot_name = client.me.first_name
    bot_username = client.me.username
    caption_text = (
        f"ʜᴇʏ {query.from_user.mention} , 🥀\n\n"
        f"⊙ ᴛʜɪs ɪs ˹ {bot_name} ˼ ♪ [ 𝘕ο 𝘈𝘥𝘴 ] ™ !\n\n"
        f"➻ ᴀ ғᴀsᴛ & ᴘᴏᴡᴇʀғᴜʟ ᴛᴇʟᴇɢʀᴀᴍ ᴍᴜsɪᴄ ᴘʟᴀʏᴇʀ ʙᴏᴛ ᴡɪᴛʜ sᴏᴍᴇ ᴀᴡᴇsᴏᴍᴇ ғᴇᴀᴛᴜʀᴇs.\n\n"
        f"⊙ ᴄʟɪᴄᴋ ᴏɴ ᴛʜᴇ ʜᴇʟᴘ ʙᴜᴛᴛᴏɴ ᴛᴏ ɢᴇᴛ ɪɴғᴏʀᴍᴀᴛɪᴏɴ ᴀʙᴏᴜᴛ ᴍʏ ᴍᴏᴅᴜʟᴇs ᴀɴᴅ
ᴄᴏᴍᴍᴀɴᴅs."
    )
    Buttons = InlineKeyboardMarkup([
        [InlineKeyboardButton("ᴀᴅᴅ ᴍᴇ ɪɴ ʏᴏᴜʀ ɢʀᴏᴜᴘ ⁺", url=f"https://t.me/{bot_username}?startgroup=true")],
        [InlineKeyboardButton("ʜᴇʟᴘ & ᴄᴏᴍᴍᴀɴᴅs", callback_data="help_menu")]
    ])
    await query.message.edit_caption(caption=caption_text, reply_markup=Buttons)
