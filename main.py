#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Main entry point for the GBI Match Maker
"""

import logging
import threading
import os
import asyncio
import time
import aiohttp
from bot import setup_bot
from app import app  # Import Flask app for gunicorn

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

logger = logging.getLogger(__name__)


async def self_ping(loop):
    """Ping the application every 13 minutes to prevent idling on Render's free plan."""
    app_url = os.environ.get('APP_URL')
    if not app_url:
        # If APP_URL is not set, try to use common Render URL pattern with app name
        app_name = os.environ.get('RENDER_SERVICE_NAME', 'gbi-match-maker')
        app_url = f"https://{app_name}.onrender.com"
    
    logger.info(f"Self-ping service will ping {app_url} every 13 minutes")
    
    while True:
        try:
            # Wait for 13 minutes (780 seconds)
            await asyncio.sleep(780)
            
            # Ping the application
            async with aiohttp.ClientSession() as session:
                start_time = time.time()
                async with session.get(app_url) as response:
                    elapsed = time.time() - start_time
                    logger.info(f"Self-ping to {app_url} completed with status {response.status} in {elapsed:.2f}s")
        except Exception as e:
            logger.error(f"Error in self-ping to {app_url}: {str(e)}", exc_info=True)
            # Continue the loop even if there's an error

def run_bot():
    """Start the Telegram bot in a separate thread."""
    try:
        import asyncio
        logger.info("Starting the Telegram bot...")
        # Create a new event loop for this thread
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        bot_app = setup_bot()
        loop.run_until_complete(bot_app.initialize())
        loop.run_until_complete(bot_app.updater.start_polling())
        
        # Start self-ping task to prevent idling on Render's free plan
        asyncio.ensure_future(self_ping(loop), loop=loop)
        logger.info("Self-ping service started")
        
        loop.run_forever()
    except Exception as e:
        logger.error(f"Error running bot: {e}", exc_info=True)


def run_web_app():
    """Start the Flask web application."""
    try:
        port = int(os.environ.get("PORT", 5000))
        app.run(host="0.0.0.0", port=port)
    except Exception as e:
        logger.error(f"Error running web app: {e}", exc_info=True)


if __name__ == "__main__":
    # Start the bot in a separate thread
    bot_thread = threading.Thread(target=run_bot)
    bot_thread.daemon = True  # Make thread a daemon so it exits when main thread exits
    bot_thread.start()
    
    # Run the web app in the main thread
    run_web_app()