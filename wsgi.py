#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
WSGI entry point for the GBI Match Maker
"""

import logging
import threading
import os
from bot import setup_bot
from app import app  # Import Flask app for gunicorn

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

logger = logging.getLogger(__name__)


def run_bot():
    """Start the Telegram bot in a separate thread."""
    try:
        logger.info("Starting the Telegram bot...")
        bot_app = setup_bot()
        bot_app.run_polling()
    except Exception as e:
        logger.error(f"Error running bot: {e}", exc_info=True)


# Start the bot in a separate thread when loaded by gunicorn
bot_thread = threading.Thread(target=run_bot)
bot_thread.daemon = True  # Make thread a daemon so it exits when main thread exits
bot_thread.start()

# Export the Flask app for gunicorn
application = app