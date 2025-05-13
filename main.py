# Copyright (c) 2025 devgagan : https://github.com/devgaganin.  
# Licensed under the GNU General Public License v3.0.  
# See LICENSE file in the repository root for full license text.

import asyncio
import os
import sys
import importlib
import logging

# Configure logging
logging.basicConfig(
    format='[%(levelname) 5s/%(asctime)s] %(name)s: %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Make sure the current directory is in the path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.dirname(current_dir))

# Create required directories
os.makedirs(os.path.join(current_dir, "downloads"), exist_ok=True)

# Import after path setup to avoid import errors
from imforware.shared_client import start_client

async def load_and_run_plugins():
    # Start the client and handle any potential errors
    try:
        client, app, userbot = await start_client()
        logger.info("All clients started successfully!")
    except Exception as e:
        logger.error(f"Failed to start clients: {e}")
        sys.exit(1)
        
    # Load and run plugins
    plugin_dir = os.path.join(current_dir, "plugins")
    plugins = [f[:-3] for f in os.listdir(plugin_dir) if f.endswith(".py") and f != "__init__.py"]

    for plugin in plugins:
        try:
            logger.info(f"Loading plugin: {plugin}")
            module = importlib.import_module(f"imforware.plugins.{plugin}")
            if hasattr(module, f"run_{plugin}_plugin"):
                logger.info(f"Running {plugin} plugin...")
                await getattr(module, f"run_{plugin}_plugin")()
            else:
                logger.info(f"Plugin {plugin} loaded (no runner function)")
        except Exception as e:
            logger.error(f"Error loading plugin {plugin}: {e}")

async def main():
    await load_and_run_plugins()
    logger.info("Bot is now running! Press Ctrl+C to stop.")
    # Keep the bot running
    while True:
        await asyncio.sleep(1)  

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    logger.info("Starting imforwarder Bot...")
    try:
        loop.run_until_complete(main())
    except KeyboardInterrupt:
        logger.info("Shutting down...")
    except Exception as e:
        logger.error(f"An error occurred: {e}")
        sys.exit(1)
    finally:
        try:
            loop.close()
        except Exception:
            pass
