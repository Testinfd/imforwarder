# Copyright (c) 2025 devgagan : https://github.com/devgaganin.  
# Licensed under the GNU General Public License v3.0.  
# See LICENSE file in the repository root for full license text.

import os
from dotenv import load_dotenv

load_dotenv()

# VPS --- FILL COOKIES 🍪 in """ ... """ 

INST_COOKIES = """
# wtite up here insta cookies
"""

YTUB_COOKIES = """
# write here yt cookies
"""

# Essential for bot & user functionality
API_ID = os.getenv("API_ID", "")
API_HASH = os.getenv("API_HASH", "")
BOT_TOKEN = os.getenv("BOT_TOKEN", "")

# Database configuration
MONGO_URI = os.getenv("MONGO_URI", "")
DB_NAME = os.getenv("DB_NAME", "telegram_downloader")

# User authentication & management
OWNER_ID = list(map(int, os.getenv("OWNER_ID", "").split())) # list separated by space
AUTH = os.getenv("AUTH", None)  # Optional: Additional auth users separated by space
FORCESUB = os.getenv("FORCESUB", None)  # Optional: Force subscription channel

# Session string for user account to access restricted content
SESSION = os.getenv("SESSION", None)  # For backward compatibility with imforwarderBot
STRING = os.getenv("STRING", SESSION)  # Primary session string

# Channel configuration
LOG_GROUP = int(os.getenv("LOG_GROUP", "-1001234456")) # optional with -100
FORCE_SUB = int(os.getenv("FORCE_SUB", "-10012345567")) # optional with -100

# Security & encryption
MASTER_KEY = os.getenv("MASTER_KEY", "gK8HzLfT9QpViJcYeB5wRa3DmN7P2xUq") # for session encryption
IV_KEY = os.getenv("IV_KEY", "s7Yx5CpVmE3F") # for decryption

# Feature configuration
YT_COOKIES = os.getenv("YT_COOKIES", YTUB_COOKIES)
INSTA_COOKIES = os.getenv("INSTA_COOKIES", INST_COOKIES)
FREEMIUM_LIMIT = int(os.getenv("FREEMIUM_LIMIT", "0"))
PREMIUM_LIMIT = int(os.getenv("PREMIUM_LIMIT", "500"))
