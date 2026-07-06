# 🔥 THE GOD-MODE MONKEY PATCH V2 (Bypassing PyTgCalls Errors)
import pyrogram.errors
class GroupcallForbidden(Exception): pass
class GroupcallInvalid(Exception): pass
# Fake classes ko library ke andar inject kar do
pyrogram.errors.GroupcallForbidden = GroupcallForbidden
pyrogram.errors.GroupcallInvalid = GroupcallInvalid
# ==========================================
# 👇 Yahan se tumhara normal code shuru
from pyrogram import Client
from pytgcalls import PyTgCalls
# 🧠 Master Single-Queue Dictionary
music_queue = {}
# 🤖 Main Bot Client
app = Client(
    "AnnonMusicBot",
    api_id=1234567,              # ⚠️ CHANGE THIS
    api_hash="0d90955a2fa71aea7650f733",   # ⚠️ CHANGE THIS
    bot_token="8954993571:", # ⚠️ CHANGE THIS
    plugins=dict(root="plugins")
)
# 👤 Assistant Client
assistant = Client(
    "AnnonAssistant",
    api_id=123456,                # ⚠️ CHANGE THIS
    api_hash="YOUR_API_HASH",     # ⚠️ CHANGE THIS
    session_string="BQHdWNgA" # ⚠️ CHANGE THIS
)
# 📞 PyTgCalls Client
call = PyTgCalls(assistant)
