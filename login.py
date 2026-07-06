from pyrogram import Client
api_id = 31283416 # Tumhari API ID
api_hash = "b69f8f202f9dd4781ac4c79677a5ea9e"
with Client("AnnonAssistant", api_id=api_id, api_hash=api_hash) as app:
    print("Session generated successfully!")
