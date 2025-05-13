# Copyright (c) 2025 devgagan : https://github.com/devgaganin.  
# Licensed under the GNU General Public License v3.0.  
# See LICENSE file in the repository root for full license text.

import os
import sys
# Add the parent directory to sys.path to fix import issues
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from telethon import TelegramClient
from config import API_ID, API_HASH, BOT_TOKEN, STRING, SESSION
from pyrogram import Client

# Debug environment variables
print(f"Environment variables loaded:")
print(f"API_ID value: {API_ID}, type: {type(API_ID)}")
print(f"API_HASH value: {API_HASH}, type: {type(API_HASH)}")
print(f"BOT_TOKEN available: {'Yes' if BOT_TOKEN else 'No'}")
print(f"SESSION available: {'Yes' if SESSION else 'No'}")
print(f"STRING available: {'Yes' if STRING else 'No'}")

# Make sure API_ID is an integer
try:
    api_id = int(API_ID)
    print(f"Successfully converted API_ID to integer: {api_id}")
except ValueError:
    print(f"Error: API_ID must be an integer, got: {API_ID}")
    sys.exit(1)

# Ensure other required environment variables are set
if not API_HASH:
    print("Error: API_HASH environment variable is not set")
    sys.exit(1)

if not BOT_TOKEN:
    print("Error: BOT_TOKEN environment variable is not set")
    sys.exit(1)

# Use SESSION as fallback for STRING for backward compatibility
session_string = STRING if STRING else SESSION

# Initialize the clients
client = TelegramClient("telethonbot", api_id, API_HASH)
app = Client("pyrogrambot", api_id=api_id, api_hash=API_HASH, bot_token=BOT_TOKEN)

# Initialize userbot only if we have a session string
userbot = None
if session_string:
    userbot = Client("saverestricted", api_id=api_id, api_hash=API_HASH, session_string=session_string)
    print("Userbot initialized with session string")
else:
    print("WARNING: No session string provided. Some features related to accessing restricted content will be limited.")

async def start_client():
    try:
        if not client.is_connected():
            await client.start(bot_token=BOT_TOKEN)
            print("Telethon bot started...")
        
        await app.start()
        print("Pyrogram bot started...")
        
        if userbot:
            try:
                await userbot.start()
                print("Userbot started successfully!")
                print("Bot is ready to access restricted content!")
            except Exception as e:
                print(f"Error starting userbot: {e}")
                print("Please check your SESSION or STRING environment variable.")
                print("The bot will continue running with limited functionality.")
                # Don't exit if userbot fails - continue with limited functionality
        
        return client, app, userbot
    except Exception as e:
        print(f"Critical error starting clients: {e}")
        sys.exit(1)

