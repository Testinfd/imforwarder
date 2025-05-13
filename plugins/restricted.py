# Copyright (c) 2025 devgagan : https://github.com/devgaganin.  
# Licensed under the GNU General Public License v3.0.  
# See LICENSE file in the repository root for full license text.

import asyncio
import os
import re
import time
import sys
import logging
from typing import Union, Optional

from pyrogram import Client, filters
from pyrogram.errors import (
    ChannelBanned, ChannelInvalid, ChannelPrivate, ChatIdInvalid, 
    ChatInvalid, PeerIdInvalid, FloodWait, UserNotParticipant,
    InviteHashExpired, UsernameNotOccupied
)
from pyrogram.enums import MessageMediaType
from telethon import events
from telethon.tl.types import DocumentAttributeVideo

# Import the shared clients
from ..shared_client import client, app, userbot
from ..utils.func import fast_upload, get_video_metadata, screenshot, progress_callback

# Cache to store already verified chat access
VERIFIED_CHATS = {}

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def thumbnail(sender):
    """Get the custom thumbnail for a user if it exists"""
    if os.path.exists(f'{sender}.jpg'):
        return f'{sender}.jpg'
    else:
        return None

def normalize_chat_id(chat_id):
    """Normalize different formats of chat IDs to the correct format"""
    # If already properly formatted with -100 prefix
    if isinstance(chat_id, int) and str(chat_id).startswith('-100'):
        return chat_id
    
    # Convert string channel IDs to proper format
    if isinstance(chat_id, str):
        if chat_id.isdigit():
            # Add -100 prefix to numeric string
            return int(f"-100{chat_id}")
        elif chat_id.startswith('-100') and chat_id[4:].isdigit():
            # Already formatted correctly as string, convert to int
            return int(chat_id)
    
    # If it's an int without -100 prefix
    if isinstance(chat_id, int) and not str(chat_id).startswith('-'):
        return int(f"-100{chat_id}")
    
    # Return as is if we can't normalize
    return chat_id

async def extract_info_from_link(msg_link):
    """Extract chat ID and message ID from different link formats"""
    # Format: t.me/c/1234567890/123
    if 't.me/c/' in msg_link:
        match = re.search(r't\.me\/c\/(\d+)\/(\d+)', msg_link)
        if match:
            chat_id = normalize_chat_id(match.group(1))
            msg_id = int(match.group(2))
            return chat_id, msg_id, "private"
    
    # Format: t.me/b/bot_username/123
    elif 't.me/b/' in msg_link:
        match = re.search(r't\.me\/b\/([^\/]+)\/(\d+)', msg_link)
        if match:
            chat_username = match.group(1)
            msg_id = int(match.group(2))
            return chat_username, msg_id, "bot"
    
    # Format: t.me/username/123
    else:
        match = re.search(r't\.me\/([^\/]+)\/(\d+)', msg_link)
        if match:
            chat_username = match.group(1)
            msg_id = int(match.group(2))
            return chat_username, msg_id, "public"
    
    return None, None, None

async def verify_channel_access(user_client, chat_id, user_id=None):
    """Verify that the user client has access to the specified chat"""
    # Skip verification if already verified
    chat_key = str(chat_id)
    if chat_key in VERIFIED_CHATS:
        return VERIFIED_CHATS[chat_key], "Already verified"
    
    try:
        # Try to get basic info about the chat
        chat = await user_client.get_chat(chat_id)
        VERIFIED_CHATS[chat_key] = True
        return True, chat
    except ChannelPrivate:
        return False, "This is a private channel that requires joining"
    except ChannelInvalid:
        return False, "Invalid channel"
    except ChannelBanned:
        return False, "Channel is banned"
    except PeerIdInvalid:
        return False, "Invalid username or channel ID"
    except FloodWait as e:
        logger.warning(f"FloodWait: {e.value} seconds")
        return False, f"Rate limited. Try again in {e.value} seconds"
    except Exception as e:
        logger.error(f"Error verifying channel access: {str(e)}")
        return False, str(e)

async def attempt_channel_join(user_client, invite_link, user_id=None):
    """Attempt to join a channel using an invite link"""
    try:
        await user_client.join_chat(invite_link)
        return True
    except InviteHashExpired:
        return False
    except UserNotParticipant:
        return False
    except Exception as e:
        logger.error(f"Error joining channel: {str(e)}")
        return False

async def process_link(msg_link, offset=0):
    """Process a Telegram link and extract necessary information"""
    if "?single" in msg_link:
        msg_link = msg_link.split("?single")[0]
    
    # Extract info from link
    chat, msg_id, chat_type = await extract_info_from_link(msg_link)
    
    # Adjust message ID if offset is provided
    if offset != 0:
        msg_id = msg_id + int(offset)
        
    return chat, msg_id, chat_type

@client.on(events.NewMessage(pattern=r'/s(ave)?'))
async def save_restricted_content(event):
    """Command handler to save restricted content from links"""
    user_id = event.sender_id
    
    # Check if userbot is available
    if not userbot:
        await event.reply(
            "⚠️ Unable to access restricted content: No user session provided.\n\n"
            "The bot administrator needs to set the SESSION or STRING environment variable "
            "with a valid Telegram session string to enable this feature."
        )
        return
    
    # Get command arguments
    args = event.text.split(' ', 1)
    if len(args) < 2:
        await event.reply(
            "📋 **How to use:**\n"
            "Send a command in this format:\n"
            "`/save https://t.me/c/channelid/messageid`\n\n"
            "For public channels:\n"
            "`/save https://t.me/channelname/messageid`\n\n"
            "For bot messages:\n"
            "`/save https://t.me/b/botusername/messageid`"
        )
        return
    
    msg_link = args[1].strip()
    status_msg = await event.reply("⏳ Processing your request...")
    
    # Process the link
    chat, msg_id, chat_type = await process_link(msg_link)
    if not chat or not msg_id:
        await status_msg.edit("🚫 Invalid link format. Please check your link.")
        return
    
    try:
        # Verify access to the chat
        await status_msg.edit("🔍 Checking access to content...")
        access_result, chat_info = await verify_channel_access(userbot, chat)
        
        if not access_result:
            # Try to join if it's a channel invite link
            if msg_link.startswith('https://t.me/+') or msg_link.startswith('https://t.me/joinchat/'):
                await status_msg.edit("🔑 Trying to join channel with invite link...")
                join_success = await attempt_channel_join(userbot, msg_link)
                if not join_success:
                    await status_msg.edit(
                        "🔒 Failed to join channel. The invite link may be expired or invalid."
                    )
                    return
            else:
                await status_msg.edit(
                    "🔒 Cannot access this content. Please make sure:\n"
                    "1. The user session has access to this channel/chat\n"
                    "2. For private channels, try sending an invite link first"
                )
                return
        
        # Get the message
        await status_msg.edit("📥 Accessing message...")
        try:
            msg = await userbot.get_messages(chat, msg_id)
            if not msg:
                await status_msg.edit("❌ Message not found or you don't have access to it.")
                return
        except Exception as e:
            await status_msg.edit(f"❌ Failed to get message: {str(e)}")
            return
        
        # Handle text messages
        if not msg.media and msg.text:
            await status_msg.edit("📋 Forwarding text message...")
            await app.send_message(user_id, msg.text)
            await status_msg.delete()
            return
        
        # Handle media messages
        await status_msg.edit("⬇️ Downloading content...")
        
        # Download the media
        download_path = f"downloads/{user_id}_{int(time.time())}"
        os.makedirs(os.path.dirname(download_path), exist_ok=True)
        
        try:
            file_path = await userbot.download_media(
                msg,
                file_name=download_path,
                progress=progress_callback,
                progress_args=(user_id, app, status_msg, "Downloading")
            )
            
            if not file_path:
                await status_msg.edit("❌ Failed to download media.")
                return
            
            # Prepare caption
            caption = msg.caption if msg.caption else ""
            
            # Get thumbnail
            thumb_path = thumbnail(user_id) or await screenshot(file_path, 0, user_id)
            
            # Upload the file
            await status_msg.edit("📤 Uploading to Telegram...")
            
            if msg.video:
                # Get video metadata
                metadata = get_video_metadata(file_path)
                width = metadata.get('width', 0)
                height = metadata.get('height', 0)
                duration = metadata.get('duration', 0)
                
                # Upload with Telethon for better handling of large files
                uploaded_file = await fast_upload(client, file_path, progress_callback=lambda d, t: progress_callback(d, t, user_id))
                
                # Send the video
                await client.send_file(
                    user_id,
                    uploaded_file,
                    thumb=thumb_path,
                    caption=caption,
                    supports_streaming=True,
                    attributes=[
                        DocumentAttributeVideo(
                            duration=duration,
                            w=width,
                            h=height,
                            supports_streaming=True
                        )
                    ]
                )
            else:
                # For other types of media
                await app.send_document(
                    user_id,
                    file_path,
                    thumb=thumb_path,
                    caption=caption,
                    progress=progress_callback,
                    progress_args=(user_id, app, status_msg, "Uploading")
                )
            
            # Delete status message and cleanup
            await status_msg.delete()
            if os.path.exists(file_path):
                os.remove(file_path)
            if thumb_path and os.path.exists(thumb_path) and thumb_path != thumbnail(user_id):
                os.remove(thumb_path)
                
        except Exception as e:
            await status_msg.edit(f"❌ Error processing media: {str(e)}")
            logger.error(f"Error in save_restricted_content: {str(e)}")
            
    except Exception as e:
        await status_msg.edit(f"❌ An error occurred: {str(e)}")
        logger.error(f"Error in save_restricted_content: {str(e)}")

# Run the plugin
async def run_restricted_plugin():
    logger.info("Restricted content plugin loaded")
    # Any initialization code can go here 