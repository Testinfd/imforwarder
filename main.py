# Copyright (c) 2025 devgagan : https://github.com/devgaganin.  
# Licensed under the GNU General Public License v3.0.  
# See LICENSE file in the repository root for full license text.

import asyncio
import os
import sys
import importlib
import time
import requests

# Make sure the current directory is in the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from shared_client import start_client
from config import BOT_TOKEN

# Check Telegram API connectivity
def check_telegram_api():
    print("Checking Telegram API connectivity...")
    try:
        response = requests.get(f"https://api.telegram.org/bot{BOT_TOKEN}/getMe", timeout=10)
        if response.status_code == 200:
            bot_info = response.json()
            if bot_info.get("ok"):
                print(f"Bot connection successful! Bot name: {bot_info['result']['first_name']}")
                return True
            else:
                print(f"Bot API returned error: {bot_info.get('description', 'Unknown error')}")
                return False
        else:
            print(f"Failed to connect to Telegram API: Status code {response.status_code}")
            return False
    except Exception as e:
        print(f"Error checking Telegram API connectivity: {e}")
        return False

async def load_and_run_plugins():
    # Start the client and handle any potential errors
    try:
        print("Attempting to start Telegram clients...")
        client, app, userbot = await start_client()
        print("All clients started successfully!")
    except Exception as e:
        print(f"Failed to start clients: {e}")
        sys.exit(1)
        
    # Load and run plugins
    print("Loading plugins...")
    plugin_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "plugins")
    plugins = [f[:-3] for f in os.listdir(plugin_dir) if f.endswith(".py") and f != "__init__.py"]
    print(f"Found plugins: {plugins}")

    for plugin in plugins:
        try:
            print(f"Loading plugin: {plugin}")
            module = importlib.import_module(f"plugins.{plugin}")
            if hasattr(module, f"run_{plugin}_plugin"):
                print(f"Running {plugin} plugin...")
                await getattr(module, f"run_{plugin}_plugin")()
            else:
                print(f"Plugin {plugin} doesn't have a run_{plugin}_plugin function")
        except Exception as e:
            print(f"Error loading plugin {plugin}: {e}")

async def main():
    # Check Telegram API connectivity first
    if not check_telegram_api():
        print("Failed to connect to Telegram API. Check your BOT_TOKEN and internet connection.")
        # Wait before retrying
        for i in range(5, 0, -1):
            print(f"Retrying in {i} seconds...")
            await asyncio.sleep(1)
        
        # Try again
        if not check_telegram_api():
            print("Still unable to connect to Telegram API. Exiting.")
            sys.exit(1)
    
    print("Starting bot...")
    await load_and_run_plugins()
    print("Bot is now running! Press Ctrl+C to stop.")
    # Keep the bot running
    try:
        while True:
            await asyncio.sleep(10)
            # Send a ping to the API every 10 seconds to keep the connection alive
            if not check_telegram_api():
                print("Lost connection to Telegram API. Attempting to reconnect...")
                # Try to restart clients
                try:
                    client, app, userbot = await start_client()
                    print("Reconnected successfully!")
                except Exception as e:
                    print(f"Failed to reconnect: {e}")
    except asyncio.CancelledError:
        # Allow the bot to gracefully shut down
        print("Received cancellation request. Shutting down...")
        pass

if __name__ == "__main__":
    # Create a new event loop
    try:
        if sys.platform == 'win32':
            asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
        
        # Use get_event_loop instead of create_new_loop to avoid deprecation warning
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        print("Starting clients ...")
        loop.run_until_complete(main())
    except KeyboardInterrupt:
        print("Shutting down...")
    except Exception as e:
        print(f"An error occurred: {e}")
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
