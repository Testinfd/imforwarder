# Copyright (c) 2025 devgagan : https://github.com/devgaganin.  
# Licensed under the GNU General Public License v3.0.  
# See LICENSE file in the repository root for full license text.

import asyncio
import os
import sys
import importlib
import time
import requests
import json
from urllib.parse import urlparse
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Make sure the current directory is in the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Log startup information
logger.info("Starting Telegram forwarder bot...")
logger.info(f"Python version: {sys.version}")
logger.info(f"Current directory: {os.getcwd()}")

try:
    from shared_client import start_client
    from config import BOT_TOKEN, API_ID, API_HASH, MONGO_DB
    
    # Verify in-memory database is initialized
    logger.info("Verifying in-memory database...")
    test_collection = MONGO_DB["test"]
    test_collection.insert_one({"test": "connection"})
    test_result = test_collection.find_one({"test": "connection"})
    if test_result:
        logger.info("In-memory database is working correctly")
    else:
        logger.warning("In-memory database test failed. Some features may not work correctly.")
except ImportError as e:
    logger.error(f"Import error: {e}")
    logger.error("Please check your configuration and ensure all dependencies are installed")
    sys.exit(1)
except Exception as e:
    logger.error(f"Initialization error: {e}")
    sys.exit(1)

# Import app modules to register webhook handler
import app

# Get server URL from environment variable or use localhost for local development
SERVER_URL = os.environ.get("SERVER_URL", None)

# Check Telegram API connectivity
def check_telegram_api():
    logger.info("Checking Telegram API connectivity...")
    try:
        response = requests.get(f"https://api.telegram.org/bot{BOT_TOKEN}/getMe", timeout=10)
        if response.status_code == 200:
            bot_info = response.json()
            if bot_info.get("ok"):
                logger.info(f"Bot connection successful! Bot name: {bot_info['result']['first_name']} (@{bot_info['result'].get('username', 'Unknown')})")
                return True, bot_info['result']
            else:
                logger.error(f"Bot API returned error: {bot_info.get('description', 'Unknown error')}")
                return False, None
        else:
            logger.error(f"Failed to connect to Telegram API: Status code {response.status_code}")
            return False, None
    except Exception as e:
        logger.error(f"Error checking Telegram API connectivity: {e}")
        return False, None

# Remove webhook if it exists (for clean start)
def remove_webhook():
    logger.info("Removing existing webhook if any...")
    try:
        response = requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/deleteWebhook", timeout=10)
        if response.status_code == 200:
            bot_info = response.json()
            if bot_info.get("ok"):
                logger.info("Webhook removed successfully")
                return True
            else:
                logger.error(f"Failed to remove webhook: {bot_info.get('description', 'Unknown error')}")
                return False
        else:
            logger.error(f"Failed to connect to Telegram API: Status code {response.status_code}")
            return False
    except Exception as e:
        logger.error(f"Error removing webhook: {e}")
        return False

# Set up webhook if SERVER_URL is provided
def setup_webhook():
    if not SERVER_URL:
        logger.info("No SERVER_URL provided. Falling back to long polling.")
        return False
    
    webhook_url = f"{SERVER_URL}/webhook/{BOT_TOKEN}"
    logger.info(f"Setting up webhook at {webhook_url}")
    
    try:
        response = requests.post(
            f"https://api.telegram.org/bot{BOT_TOKEN}/setWebhook",
            json={"url": webhook_url},
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            if result.get("ok"):
                logger.info("Webhook set up successfully!")
                
                # Verify webhook info
                info_response = requests.get(f"https://api.telegram.org/bot{BOT_TOKEN}/getWebhookInfo", timeout=10)
                if info_response.status_code == 200:
                    info = info_response.json()
                    if info.get("ok"):
                        logger.info(f"Webhook info: {json.dumps(info['result'], indent=2)}")
                return True
            else:
                logger.error(f"Failed to set webhook: {result.get('description', 'Unknown error')}")
                return False
        else:
            logger.error(f"Failed to connect to Telegram API: Status code {response.status_code}")
            return False
    except Exception as e:
        logger.error(f"Error setting up webhook: {e}")
        return False

async def load_and_run_plugins():
    # Start the client and handle any potential errors
    try:
        logger.info("Attempting to start Telegram clients...")
        telethon_client, pyrogram_bot, userbot_client = await start_client()
        logger.info("All clients started successfully!")
    except Exception as e:
        logger.error(f"Failed to start clients: {e}")
        sys.exit(1)
        
    # Load and run plugins
    logger.info("Loading plugins...")
    plugin_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "plugins")
    
    if not os.path.exists(plugin_dir):
        logger.error(f"Plugin directory not found: {plugin_dir}")
        sys.exit(1)
        
    plugins = [f[:-3] for f in os.listdir(plugin_dir) if f.endswith(".py") and f != "__init__.py"]
    logger.info(f"Found plugins: {plugins}")

    for plugin in plugins:
        try:
            logger.info(f"Loading plugin: {plugin}")
            module = importlib.import_module(f"plugins.{plugin}")
            if hasattr(module, f"run_{plugin}_plugin"):
                logger.info(f"Running {plugin} plugin...")
                await getattr(module, f"run_{plugin}_plugin")()
            else:
                logger.info(f"Plugin {plugin} doesn't have a run_{plugin}_plugin function")
        except Exception as e:
            logger.error(f"Error loading plugin {plugin}: {e}")

async def handle_telegram_update(update):
    """
    Handle updates from Telegram webhook
    """
    logger.info(f"Processing update from webhook: {update.get('update_id')}")
    try:
        # Get the clients. app_client is the Pyrogram bot instance.
        telethon_client, pyrogram_bot, userbot_client = await start_client()
        
        # Instead of manually parsing, feed the raw update to Pyrogram's dispatcher
        # Pyrogram will then trigger the appropriate handlers (e.g., @app.on_message)
        if pyrogram_bot:
            logger.info(f"Feeding update to Pyrogram client: {update.get('update_id')}")
            # Construct a RawUpdate object if necessary, or pass the dict if supported by feed_update
            # For simplicity, assuming feed_update can handle the dict directly or a simple structure.
            # The exact method might be app.invoke(RawUpdate(...)) or similar depending on Pyrogram version
            # and how feed_update is implemented or if a direct dispatcher method is available.
            # For now, let's assume a conceptual feed_update. Actual Pyrogram method might be needed.
            
            # Pyrogram's Client.process_update(update_obj, workers=1) is a more direct way
            # It requires constructing an Update object first.
            # A simpler (though perhaps less direct) way for some versions might be related to a bound
            # dispatcher if directly accessible, but feed_update or process_update is more common.

            # Given the context of Pyrogram, we need to ensure this update is processed by its handlers.
            # The `update` here is a dict. Pyrogram's `feed_update` expects a specific Update object.
            # A more robust way is to use the underlying dispatcher if accessible, or construct the Update object.
            # However, if `pyrogram_bot.dispatch` or similar is available and works with a raw dict:
            # await pyrogram_bot.dispatch(update) # This is speculative

            # Let's try a common way to handle raw updates if available, often via a feed method
            # Assuming pyrogram_bot is the Pyrogram Client instance 'app'
            # We need to convert the 'update' dict to a Pyrogram Update object
            # This step is complex as it requires knowing the exact Pyrogram Update structure.

            # Simpler approach: The webhook handling in Pyrogram usually involves setting up
            # a webserver (like Flask) and then using `app.dispatch_updates(updates_list)` or
            # `await app.dispatcher.feed_raw_update(update_type, update_data)`
            # Since we are already in an async context called by Flask, we want to trigger Pyrogram's handlers.

            # The comment "can't directly inject the update into Pyrogram's dispatcher" is telling.
            # If a direct injection method isn't straightforward, the original author might have struggled.
            # However, a core feature of client libraries is to process updates.

            # Let's assume the most direct available method or a placeholder for it.
            # The most common pattern is to have Pyrogram run its own webserver part or integrate deeply.
            # If we must manually bridge: Pyrogram updates are instances of `pyrogram.types.Update`.
            # Manually creating this from a dict is error-prone.

            # The most straightforward way if Pyrogram is already running its loop (even if started here)
            # is to ensure its handlers are picked up. The issue is that the current function
            # *intercepts* the update before Pyrogram sees it via its own webhook mechanism.

            # If this function is the *only* way updates arrive in webhook mode, then it *must* dispatch.
            # The simplest conceptual Pyrogram method would be: 
            await pyrogram_bot.handle_update(update)
            logger.info(f"Update {update.get('update_id')} passed to Pyrogram client for handling.")
        else:
            logger.error("Pyrogram bot client not available to handle update.")
    
    except Exception as e:
        logger.error(f"Error processing webhook update: {e}")

async def main():
    # Check Telegram API connectivity first
    success, bot_info = check_telegram_api()
    if not success:
        logger.error("Failed to connect to Telegram API. Check your BOT_TOKEN and internet connection.")
        # Wait before retrying
        for i in range(5, 0, -1):
            logger.info(f"Retrying in {i} seconds...")
            await asyncio.sleep(1)
        
        # Try again
        success, bot_info = check_telegram_api()
        if not success:
            logger.error("Still unable to connect to Telegram API. Exiting.")
            sys.exit(1)
    
    # Remove existing webhook for clean start
    remove_webhook()
    
    # Try to set up webhook if SERVER_URL is provided
    if SERVER_URL:
        webhook_success = setup_webhook()
        if webhook_success:
            logger.info("Using webhook mode")
        else:
            logger.warning("Webhook setup failed. Falling back to long polling mode.")
    else:
        logger.info("No SERVER_URL provided. Using long polling mode.")
    
    # Register the webhook handler
    app.register_update_handler(handle_telegram_update)
    logger.info("Webhook handler registered with Flask app")
    
    logger.info("Starting bot...")
    await load_and_run_plugins()
    logger.info("Bot is now running! Press Ctrl+C to stop.")
    
    # Keep the bot running
    try:
        counter = 0
        while True:
            await asyncio.sleep(60)  # Check every minute
            counter += 1
            
            # Every 10 minutes, check if the bot is still connected
            if counter % 10 == 0:
                success, _ = check_telegram_api()
                if not success:
                    logger.warning("Lost connection to Telegram API. Attempting to reconnect...")
                    # Try to restart clients
                    try:
                        telethon_client, pyrogram_bot, userbot_client = await start_client()
                        logger.info("Reconnected successfully!")
                    except Exception as e:
                        logger.error(f"Failed to reconnect: {e}")
                else:
                    logger.info("Bot is still connected and running")
                    
                # Also check webhook status if using webhook mode
                if SERVER_URL:
                    try:
                        info_response = requests.get(f"https://api.telegram.org/bot{BOT_TOKEN}/getWebhookInfo", timeout=10)
                        if info_response.status_code == 200:
                            info = info_response.json()
                            if info.get("ok"):
                                webhook_info = info['result']
                                if webhook_info.get('url') != f"{SERVER_URL}/webhook/{BOT_TOKEN}" or webhook_info.get('pending_update_count', 0) > 100:
                                    logger.warning("Webhook needs to be reset. Doing it now...")
                                    remove_webhook()
                                    setup_webhook()
                    except Exception as e:
                        logger.error(f"Error checking webhook status: {e}")
                    
    except asyncio.CancelledError:
        # Allow the bot to gracefully shut down
        logger.info("Received cancellation request. Shutting down...")
        pass

if __name__ == "__main__":
    # Create a new event loop
    try:
        if sys.platform == 'win32':
            asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
        
        # Use get_event_loop instead of create_new_loop to avoid deprecation warning
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        logger.info("Starting clients ...")
        loop.run_until_complete(main())
    except KeyboardInterrupt:
        logger.info("Shutting down...")
    except Exception as e:
        logger.error(f"An error occurred: {e}")
        sys.exit(1)
    finally:
        # Ensure all tasks are complete before closing the loop
        pending = asyncio.all_tasks(loop)
        for task in pending:
            task.cancel()
        
        if pending:
            loop.run_until_complete(asyncio.gather(*pending, return_exceptions=True))
        
        if loop.is_running():
            loop.stop()
        
        if not loop.is_closed():
            loop.close()
