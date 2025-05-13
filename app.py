# Copyright (c) 2025 devgagan : https://github.com/devgaganin.  
# Licensed under the GNU General Public License v3.0.  
# See LICENSE file in the repository root for full license text.

import os
import json
import asyncio
import threading
import logging
from flask import Flask, render_template, request, jsonify

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Global variable to hold reference to the bot's update handler
bot_update_handler = None

@app.route("/")
def welcome():
    # Render the welcome page with animated "Team SPY" text
    return render_template("welcome.html")

@app.route("/webhook/<token>", methods=["POST"])
def webhook(token):
    """
    Handle webhook requests from Telegram
    """
    # Check if the token is valid
    from config import BOT_TOKEN
    if token != BOT_TOKEN:
        logger.warning(f"Invalid token: {token}")
        return jsonify({"ok": False, "description": "Invalid token"}), 403
    
    # Get the update from the request
    try:
        update = request.get_json()
        logger.info(f"Received update: {json.dumps(update, indent=2)}")
        
        # Process the update if bot_update_handler is available
        if bot_update_handler:
            threading.Thread(
                target=lambda: asyncio.run(bot_update_handler(update)),
                daemon=True
            ).start()
            return jsonify({"ok": True})
        else:
            # If no handler is available, just acknowledge the update
            logger.warning("No update handler available. Update acknowledged but not processed.")
            return jsonify({"ok": True, "warning": "Update acknowledged but not processed"})
    except Exception as e:
        logger.error(f"Error processing webhook update: {e}")
        return jsonify({"ok": False, "description": str(e)}), 500

@app.route("/health")
def health_check():
    """
    Simple health check endpoint
    """
    return jsonify({"status": "ok", "bot_handler_available": bot_update_handler is not None})

def register_update_handler(handler):
    """
    Register a function to handle Telegram updates
    """
    global bot_update_handler
    bot_update_handler = handler
    logger.info("Update handler registered successfully")

if __name__ == "__main__":
    # Default to port 5000 if PORT is not set in the environment
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
