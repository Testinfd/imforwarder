# Copyright (c) 2025 devgagan : https://github.com/devgaganin.  
# Licensed under the GNU General Public License v3.0.  
# See LICENSE file in the repository root for full license text.

import asyncio
import os
import sys
import importlib

# Make sure the current directory is in the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from shared_client import start_client

async def load_and_run_plugins():
    # Start the client and handle any potential errors
    try:
        client, app, userbot = await start_client()
        print("All clients started successfully!")
    except Exception as e:
        print(f"Failed to start clients: {e}")
        sys.exit(1)
        
    # Load and run plugins
    plugin_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "plugins")
    plugins = [f[:-3] for f in os.listdir(plugin_dir) if f.endswith(".py") and f != "__init__.py"]

    for plugin in plugins:
        try:
            module = importlib.import_module(f"plugins.{plugin}")
            if hasattr(module, f"run_{plugin}_plugin"):
                print(f"Running {plugin} plugin...")
                await getattr(module, f"run_{plugin}_plugin")()
        except Exception as e:
            print(f"Error loading plugin {plugin}: {e}")

async def main():
    await load_and_run_plugins()
    print("Bot is now running! Press Ctrl+C to stop.")
    # Keep the bot running
    try:
        while True:
            await asyncio.sleep(1)
    except asyncio.CancelledError:
        # Allow the bot to gracefully shut down
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
