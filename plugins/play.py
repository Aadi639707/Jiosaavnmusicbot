import os
import time
import urllib.parse
import asyncio
import aiohttp
import json
import base64
import pyDes
import yt_dlp
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from pytgcalls.types import MediaStream
from core import call, music_queue, app, assistant
os.makedirs("downloads", exist_ok=True)
# ==========================================
# 🛡️ ANTI-BLOCK HEADERS FOR JIOSAAVN
# ==========================================
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://www.jiosaavn.com/",
    "Origin": "https://www.jiosaavn.com"
}
DES_KEY = b"38346591"
def decrypt_url(encrypted_url):
    try:
        encrypted_url = encrypted_url.strip()
        missing_padding = len(encrypted_url) % 4
        if missing_padding:
            encrypted_url += '=' * (4 - missing_padding)
        crypto = pyDes.des(DES_KEY, pyDes.ECB, padmode=pyDes.PAD_PKCS5)
        decrypted_bytes = crypto.decrypt(base64.b64decode(encrypted_url), padmode=pyDes.PAD_PKCS5)
        return decrypted_bytes.decode('utf-8')
    except:
        return None
# ==========================================
# 🔒 PER-CHAT LOCKS
# Prevents race conditions during skips and stream ends
# ==========================================
chat_locks = {}
def get_lock(chat_id):
    if chat_id not in chat_locks:
        chat_locks[chat_id] = asyncio.Lock()
    return chat_locks[chat_id]
# ==========================================
# 🤖 ASSISTANT AUTO-JOIN (IMMORTAL BYPASS)
# ==========================================
async def ensure_assistant_in_chat(target_chat_id, processing_msg=None):
    try:
        # Check 1: Dekho assistant pehle se hai kya
        await app.get_chat_member(target_chat_id, (await assistant.get_me()).id)
        return True
    except Exception:
        pass
    if processing_msg:
        try:
            await processing_msg.edit_text("🔄 Adding Assistant to the Chat/Channel...")
        except Exception:
            pass
    # Check 2: Try with invite link (Master Bypass)
    try:
        invite_link = await app.export_chat_invite_link(target_chat_id)
        if invite_link:
            await assistant.join_chat(invite_link)
            await asyncio.sleep(1)
            return True
    except Exception as e:
        err_str = str(e).upper()
        # Agar pehle se add hai, ya link ka issue hai, toh error mat maano, aage badho!
        if "PARTICIPANT" in err_str or "EXPIRED" in err_str or "INVALID" in err_str:
            return True
        print(f"Export link issue bypassed: {e}")
    # Check 3: Try with username
    try:
        chat_info = await app.get_chat(target_chat_id)
        if chat_info.username:
            await assistant.join_chat(chat_info.username)
            await asyncio.sleep(1)
            return True
    except Exception as e:
        err_str = str(e).upper()
        if "PARTICIPANT" in err_str:
            return True
    # Agar sab fail ho jaye, toh True hi return karo taaki safe_play khud handle kar le
    return True
# ==========================================
# 🔁 RESILIENT PLAY (AUTO-RETRY)
# ==========================================
async def safe_play(chat_id, file_path, retries=2):
    last_err = None
    for attempt in range(retries + 1):
        try:
            await call.play(chat_id, MediaStream(file_path))
            return
        except Exception as e:
            last_err = e
            print(f"[safe_play] attempt {attempt + 1}/{retries + 1} failed for {chat_id}: {e}")
            try:
                await call.leave_call(chat_id)
            except Exception:
                pass
            await ensure_assistant_in_chat(chat_id)
            await asyncio.sleep(2)
    raise last_err
async def _advance_queue(chat_id):
    lock = get_lock(chat_id)
    async with lock:
        if chat_id not in music_queue or not music_queue[chat_id]:
            return
        music_queue[chat_id].pop(0)
        if not music_queue[chat_id]:
            music_queue.pop(chat_id, None)
            try:
                await call.leave_call(chat_id)
            except Exception:
                pass
            return
        next_song = music_queue[chat_id][0]
        rejoined = await ensure_assistant_in_chat(chat_id)
        if not rejoined:
            print(f"[_advance_queue] Could not keep assistant in {chat_id}, dropping queue.")
            music_queue.pop(chat_id, None)
            return
        next_song["started_at"] = time.time()
        try:
            await safe_play(chat_id, next_song["file_path"])
        except Exception as e:
            print(f"[_advance_queue] Giving up on {chat_id}: {e}")
            music_queue.pop(chat_id, None)
            return
        try:
            await app.send_photo(
                chat_id,
                photo=next_song['thumbnail'],
                caption=(
                    f"⏭️ **Now Playing:**\n\n"
                    f"**Title:** {next_song['title']}\n"
                    f"**Requested By:** {next_song['requester']}"
                )
            )
        except Exception:
            pass
try:
    @call.on_stream_end()
    async def on_stream_end_handler(client, update):
        try:
            await _advance_queue(update.chat_id)
        except Exception as e:
            print(f"[on_stream_end] error for {update.chat_id}: {e}")
except AttributeError:
    print("[startup] call.on_stream_end() not available in this pytgcalls version")
# ==========================================
# 🐕 WATCHDOG
# ==========================================
_watchdog_task = None
async def queue_watchdog():
    while True:
        await asyncio.sleep(45)
        try:
            for chat_id in list(music_queue.keys()):
                queue = music_queue.get(chat_id)
                if not queue:
                    continue
                current = queue[0]
                started_at = current.get("started_at")
                duration = current.get("duration") or 0
                if started_at and duration and (time.time() - started_at) > duration + 40:
                    print(f"[watchdog] Stalled stream detected in {chat_id},
forcing reconnect...")
                    await _advance_queue(chat_id)
        except Exception as e:
            print(f"[watchdog] loop error: {e}")
def start_watchdog_if_needed():
    global _watchdog_task
    if _watchdog_task is None or _watchdog_task.done():
        _watchdog_task = asyncio.create_task(queue_watchdog())
# ==========================================
# 🎵 PLAY COMMAND LOGIC
# ==========================================
@Client.on_message(filters.command(["play", "cplay"]) & filters.group)
async def play_command(client: Client, message: Message):
    start_watchdog_if_needed()
    try:
        command_used = message.command[0].lower()
        if len(message.command) < 2:
            return await message.reply_text("⚠️ Please provide a song name to play.")
        query = message.text.split(None, 1)[1]
        processing_msg = await message.reply_text("🔍 Searching track...")
        target_chat_id = message.chat.id
        chat_type_text = "Group"
        if command_used == "cplay":
            try:
                chat_info = await app.get_chat(message.chat.id)
                if not chat_info.linked_chat:
                    return await processing_msg.edit_text(
                        "⚠️ **No Linked Channel Found!**\n"
                        "Please link a channel to this group in the settings
first."
                    )
                target_chat_id = chat_info.linked_chat.id
                chat_type_text = "Channel"
            except Exception as e:
                return await processing_msg.edit_text(f"⚠️ **Channel Fetch Error:** Make sure bot is admin.\nDetails: {e}")
        await ensure_assistant_in_chat(target_chat_id, processing_msg)
        requester = "Anonymous"
        if message.from_user:
            requester = message.from_user.mention
        elif message.sender_chat:
            requester = message.sender_chat.title
        song_details = None
        # ------------------------------------------
        # PLAN A: JIOSAAVN ENGINE
        # ------------------------------------------
        async with aiohttp.ClientSession() as session:
            try:
                encoded_query = urllib.parse.quote(query)
                search_url = f"https://www.jiosaavn.com/api.php?__call=autocomplete.get&_format=json&_marker=0&cc=in&includeMetaTags=1&query={encoded_query}"
                async with session.get(search_url, headers=HEADERS, timeout=4) as resp:
                    search_data = json.loads(await resp.text())
                if search_data.get("songs") and search_data["songs"].get("data"):
                    song_id = search_data["songs"]["data"][0]["id"]
                    details_url = f"https://www.jiosaavn.com/api.php?__call=song.getDetails&cc=in&_marker=0%3F_marker%3D0&_format=json&pids={song_id}"
                    async with session.get(details_url, headers=HEADERS, timeout=4) as resp:
                        details_data = json.loads(await resp.text())
                        track = details_data[song_id]
                        title = track.get("song", "Unknown").replace("&quot;", '"')
                        duration = int(track.get("duration", 0))
                        thumbnail = track.get("image", "").replace("150x150", "500x500")
                        encrypted_media_url = track.get("encrypted_media_url", "")
                        dec_url = decrypt_url(encrypted_media_url) if encrypted_media_url else None
                        if dec_url:
                            stream_url = dec_url.replace("_96.mp4", "_320.mp4").replace("_96_p.mp4", "_320.mp4")
                            file_path = f"downloads/{target_chat_id}_saavn_{song_id}.m4a"
                            if not os.path.exists(file_path):
                                async with session.get(stream_url, headers=HEADERS) as dl_resp:
                                    if dl_resp.status == 200:
                                        audio_bytes = await dl_resp.read()
                                        loop = asyncio.get_running_loop()
                                        await loop.run_in_executor(None, lambda: open(file_path, "wb").write(audio_bytes))
                            song_details = {
                                "title": title,
                                "file_path": file_path,
                                "duration": duration,
                                "thumbnail": thumbnail,
                                "requester": requester
                            }
            except Exception as e:
                print(f"[play_command] JioSaavn failed, falling back to YouTube: {e}")
        # ------------------------------------------
        # PLAN B: YOUTUBE FALLBACK (NEVER FAILS)
        # ------------------------------------------
        if not song_details:
            try:
                loop = asyncio.get_running_loop()
                def fetch_yt():
                    ydl_opts = {
                        'format': 'm4a/bestaudio/best',
                        'outtmpl': f'downloads/{target_chat_id}_yt_%(id)s.%(ext)s',
                        'noplaylist': True,
                        'quiet': True,
                        'no_warnings': True
                    }
                    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                        info = ydl.extract_info(f"ytsearch:{query}", download=True)
                        if 'entries' in info and len(info['entries']) > 0:
                            entry = info['entries'][0]
                            return {
                                "title": entry.get('title', 'Unknown Title'),                                "duration": int(entry.get('duration', 0)),
                                "file_path": ydl.prepare_filename(entry),
                                "thumbnail": entry.get('thumbnail', '')
                            }
                        return None
                yt_data = await loop.run_in_executor(None, fetch_yt)
                if yt_data:
                    song_details = {
                        "title": yt_data["title"],
                        "file_path": yt_data["file_path"],
                        "duration": yt_data["duration"],
                        "thumbnail": yt_data["thumbnail"],
                        "requester": requester
                    }
            except Exception as yt_err:
                print(f"YouTube Fallback Error: {yt_err}")
        # ------------------------------------------
        # FINAL EXECUTION
        # ------------------------------------------
        if not song_details:
            return await processing_msg.edit_text(
                "⚠️ **Track Not Found!**\n"
                "Could not find this song anywhere. Please check the spelling."
            )
        async with get_lock(target_chat_id):
            if target_chat_id not in music_queue:
                music_queue[target_chat_id] = []
            music_queue[target_chat_id].append(song_details)
            queue_len = len(music_queue[target_chat_id])
        bot_username = client.me.username
        play_buttons = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("▷", callback_data="resume"),
                InlineKeyboardButton("II", callback_data="pause"),
                InlineKeyboardButton("⏭", callback_data="skip"),
                InlineKeyboardButton("⏹", callback_data="stop")
            ],
            [
                InlineKeyboardButton("Developer", url="https://t.me/rushdeveloper"),
                InlineKeyboardButton("Support", url="https://t.me/rushbots")
            ],
            [InlineKeyboardButton("+ Add Me To Your Group +", url=f"https://t.me/{bot_username}?startgroup=true")]
        ])
        if queue_len == 1:
            try:
                song_details["started_at"] = time.time()
                await safe_play(target_chat_id, song_details["file_path"])
            except Exception as vc_err:
                music_queue.pop(target_chat_id, None)
                err_str = str(vc_err).lower()
                if "chat_admin_required" in err_str:
                    return await processing_msg.edit_text("⚠️ **Voice Chat Error:** Please make the bot an **Admin** with Manage Voice Chats permission.")                elif any(x in err_str for x in ["not found", "no active", "not in call", "groupcall"]):
                    return await processing_msg.edit_text(f"⚠️ **Voice Chat Not Active:** Please start a **Voice Chat** in the {chat_type_text} first.")
                else:
                    return await processing_msg.edit_text(f"⚠️ **Stream Error:** {str(vc_err)[:100]}")
            play_text = (
                f"▶️ **Started Streaming in {chat_type_text}**\n\n"
                f"**Title:** {song_details['title']}\n"
                f"**Duration:** {song_details['duration']} Seconds\n"
                f"**Requested By:** {song_details['requester']}"
            )
            await message.reply_photo(photo=song_details['thumbnail'], caption=play_text, reply_markup=play_buttons)
            await processing_msg.delete()
        else:
            position = queue_len - 1
            queue_text = (
                f"⏳  **Added to {chat_type_text} Queue at #{position}**\n\n"
                f"**Title:** {song_details['title']}\n"
                f"**Duration:** {song_details['duration']} Seconds\n"
                f"**Requested By:** {song_details['requester']}"
            )
            await processing_msg.edit_text(text=queue_text, reply_markup=play_buttons)
    except Exception as e:
        print(f"[play_command] critical error: {e}")
        try:
            await processing_msg.edit_text(f"⚠️ **Critical Error:** {str(e)[:100]}")
        except:
            await message.reply_text(f"⚠️ **Critical Error:** {str(e)[:100]}")
# ==========================================
# ⏭️ SKIP COMMAND LOGIC
# ==========================================
@Client.on_message(filters.command(["skip", "cskip", "next"]) & filters.group)
async def skip_command(client: Client, message: Message):
    try:
        command = message.command[0].lower()
        target_chat_id = message.chat.id
        chat_type = "Group"
        if command.startswith("c"):
            chat_info = await app.get_chat(message.chat.id)
            if not chat_info.linked_chat:
                return await message.reply_text("⚠️ No linked channel found.")
            target_chat_id = chat_info.linked_chat.id
            chat_type = "Channel"
        async with get_lock(target_chat_id):
            if target_chat_id not in music_queue or not music_queue[target_chat_id]:
                return await message.reply_text(f"⚠️ Nothing is playing in the {chat_type}.")
            music_queue[target_chat_id].pop(0)
            if not music_queue[target_chat_id]:
                music_queue.pop(target_chat_id, None)
                try:
                    await call.leave_call(target_chat_id)
                except:
                    pass
                return await message.reply_text(f"⏹️ {chat_type} queue finished.")
            next_song = music_queue[target_chat_id][0]
            await ensure_assistant_in_chat(target_chat_id)
            next_song["started_at"] = time.time()
            await safe_play(target_chat_id, next_song["file_path"])
        await message.reply_photo(
            photo=next_song['thumbnail'],
            caption=f"⏭️ **Skipped! Playing Next:**\n\n**Title:** {next_song['title']}\n**Requested By:** {next_song['requester']}"
        )
    except Exception as e:
        print(f"[skip_command] error: {e}")
        await message.reply_text(f"⚠️ Error skipping song: {e}")
# ==========================================
# ⏹️ STOP/END COMMAND LOGIC
# ==========================================
@Client.on_message(filters.command(["end", "cend", "stop", "cstop"]) & filters.group)
async def end_command(client: Client, message: Message):
    try:
        command = message.command[0].lower()
        target_chat_id = message.chat.id
        chat_type = "Group"
        if command.startswith("c"):
            chat_info = await app.get_chat(message.chat.id)
            if not chat_info.linked_chat:
                return await message.reply_text("⚠️ No linked channel found.")
            target_chat_id = chat_info.linked_chat.id
            chat_type = "Channel"
        async with get_lock(target_chat_id):
            music_queue.pop(target_chat_id, None)
            try:
                await call.leave_call(target_chat_id)
            except Exception:
                pass
        await message.reply_text(f"⏹️ Music stopped and queue cleared in {chat_type}.")
    except Exception as e:
        print(f"[end_command] error: {e}")
        try:
            await message.reply_text(f"⚠️ Error stopping playback: {str(e)[:100]}")
        except Exception:
            pass
