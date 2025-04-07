#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Simple script to run the Telegram bot without the web interface
"""

import logging
import os
import asyncio
from bot_only import main

if __name__ == "__main__":
    # Setup logging
    logging.basicConfig(
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        level=logging.INFO
    )
    logger = logging.getLogger(__name__)
    
    # Run the bot
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot stopped manually")
    except Exception as e:
        logger.error(f"Error running bot: {e}", exc_info=True)