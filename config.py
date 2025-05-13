# Copyright (c) 2025 devgagan : https://github.com/devgaganin.  
# Licensed under the GNU General Public License v3.0.  
# See LICENSE file in the repository root for full license text.

import os
import re
from dotenv import load_dotenv

load_dotenv()

# VPS --- FILL COOKIES 🍪 in """ ... """ 

INST_COOKIES = """
# wtite up here insta cookies
"""

YTUB_COOKIES = """
# write here yt cookies
"""

API_ID = os.getenv("API_ID", "")
API_HASH = os.getenv("API_HASH", "")
BOT_TOKEN = os.getenv("BOT_TOKEN", "")
MONGO_URI = os.getenv("MONGO_URI", "")  # Kept for backward compatibility
OWNER_ID = list(map(int, os.getenv("OWNER_ID", "").split())) # list seperated via space
DB_NAME = os.getenv("DB_NAME", "telegram_downloader")
STRING = os.getenv("STRING", None) # optional

# Simpler LOG_GROUP parsing
DEFAULT_LOG_GROUP = -1002019378706  # Define a default log group ID
LOG_GROUP = DEFAULT_LOG_GROUP # Default to a known safe integer value

log_group_env_val = os.getenv("LOG_GROUP")

if log_group_env_val:
    try:
        # Try to convert the environment variable directly
        LOG_GROUP = int(log_group_env_val)
        print(f"Using LOG_GROUP from environment: {LOG_GROUP}")
    except ValueError:
        # If conversion fails, try to extract numeric part
        # This handles cases like "-100xxxxxxP" by extracting "-100xxxxxx"
        numeric_part = "".join(filter(lambda x: x.isdigit() or x == '-', log_group_env_val))
        if numeric_part.startswith('-'):
            # Ensure only one leading '-' and it's at the start
            rest = numeric_part[1:].replace('-', '')
            numeric_part = '-' + rest
        else:
            numeric_part = numeric_part.replace('-', '')

        if numeric_part and (numeric_part == '-' or numeric_part.lstrip('-').isdigit()):
            try:
                LOG_GROUP = int(numeric_part)
                print(f"Successfully parsed numeric part of LOG_GROUP '{log_group_env_val}' to: {LOG_GROUP}")
            except ValueError:
                print(f"Could not parse numeric part '{numeric_part}' from LOG_GROUP '{log_group_env_val}'. Using default: {DEFAULT_LOG_GROUP}")
                LOG_GROUP = DEFAULT_LOG_GROUP # Fallback to default if numeric extraction also fails
        else:
            print(f"LOG_GROUP environment variable '{log_group_env_val}' is not a valid integer. Using default: {DEFAULT_LOG_GROUP}")
            LOG_GROUP = DEFAULT_LOG_GROUP # Fallback to default if no numeric part found or invalid
else:
    print(f"LOG_GROUP environment variable not set. Using default: {DEFAULT_LOG_GROUP}")
    # LOG_GROUP is already set to DEFAULT_LOG_GROUP

FORCE_SUB = None  # Disabled force subscription
MASTER_KEY = os.getenv("MASTER_KEY", "gK8HzLfT9QpViJcYeB5wRa3DmN7P2xUq") # for session encryption
IV_KEY = os.getenv("IV_KEY", "s7Yx5CpVmE3F") # for decryption
YT_COOKIES = os.getenv("YT_COOKIES", YTUB_COOKIES)
INSTA_COOKIES = os.getenv("INSTA_COOKIES", INST_COOKIES)
FREEMIUM_LIMIT = int(os.getenv("FREEMIUM_LIMIT", "100000"))  # Set high limit for free users
PREMIUM_LIMIT = int(os.getenv("PREMIUM_LIMIT", "100000"))  # Set high limit for all users

# In-memory database implementation
class InMemoryCollection:
    def __init__(self):
        self.data = {}
        
    def insert_one(self, document):
        _id = document.get("_id", str(len(self.data) + 1))
        document["_id"] = _id
        self.data[_id] = document
        return {"inserted_id": _id}
        
    def find_one(self, query):
        for doc in self.data.values():
            match = True
            for key, value in query.items():
                if key not in doc or doc[key] != value:
                    match = False
                    break
            if match:
                return doc
        return None
        
    def update_one(self, query, update, upsert=False):
        doc = self.find_one(query)
        if doc:
            if "$set" in update:
                for key, value in update["$set"].items():
                    doc[key] = value
            return {"modified_count": 1}
        elif upsert:
            new_doc = {}
            for key, value in query.items():
                new_doc[key] = value
            if "$set" in update:
                for key, value in update["$set"].items():
                    new_doc[key] = value
            return self.insert_one(new_doc)
        return {"modified_count": 0}
        
    def delete_one(self, query):
        for _id, doc in list(self.data.items()):
            match = True
            for key, value in query.items():
                if key not in doc or doc[key] != value:
                    match = False
                    break
            if match:
                del self.data[_id]
                return {"deleted_count": 1}
        return {"deleted_count": 0}
        
    def find(self, query=None):
        if query is None:
            return list(self.data.values())
        result = []
        for doc in self.data.values():
            match = True
            for key, value in query.items():
                if key not in doc or doc[key] != value:
                    match = False
                    break
            if match:
                result.append(doc)
        return result
    
    def create_index(self, key, expireAfterSeconds=0):
        # In-memory implementation doesn't need actual indexing
        # This is just a stub for compatibility
        return key

class InMemoryDatabase:
    def __init__(self):
        self.collections = {}
        
    def __getitem__(self, collection_name):
        if collection_name not in self.collections:
            self.collections[collection_name] = InMemoryCollection()
        return self.collections[collection_name]

# Always use in-memory database
print("Using in-memory database for all operations.")
MONGO_DB = InMemoryDatabase()
