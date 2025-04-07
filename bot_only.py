#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Standalone entry point for the GBI Match Maker Telegram bot
"""

import logging
import asyncio
import os
import time
import aiohttp
from aiohttp import web
from bot import setup_bot

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

logger = logging.getLogger(__name__)

# Create a simple HTTP server for health checks
async def healthcheck(request):
    """Simple health check endpoint."""
    return web.Response(text="GBI Match Maker Bot is running!", content_type="text/plain")

async def setup_health_server():
    """Set up a simple health check server."""
    app = web.Application()
    app.router.add_get('/', healthcheck)
    
    port = int(os.environ.get('PORT', 5000))
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()
    logger.info(f"Health check server running on port {port}")

async def self_ping():
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

async def main():
    """Run the bot and health check server."""
    try:
        logger.info("Starting the Telegram bot...")
        # Set up and start the bot
        bot_app = setup_bot()
        await bot_app.initialize()
        await bot_app.start()
        await bot_app.updater.start_polling()
        logger.info("Bot is running...")
        
        # Set up health check server
        await setup_health_server()
        
        # Start self-ping task to prevent idling on Render's free plan
        asyncio.create_task(self_ping())
        logger.info("Self-ping service started")
        
        # Keep the bot running until manually stopped
        await asyncio.Event().wait()  # Run forever
    except Exception as e:
        logger.error(f"Error running bot: {e}", exc_info=True)


if __name__ == "__main__":
    # Run the bot in the asyncio event loop
    asyncio.run(main())