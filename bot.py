#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Bot setup and configuration module
"""

import os
import logging
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, CallbackQueryHandler, ConversationHandler
from handlers import (
    start, help_command, cancel, register_command, handle_name, handle_age, 
    handle_gender, handle_profile_pic, handle_university, handle_target_universities,
    handle_hobbies, handle_bio, handle_relationship_preference, view_profile,
    handle_match, handle_callback_query, handle_secret_crush, handle_chat_message,
    block_user, report_user, unmatch_user, show_matches, profile_completed,
    edit_profile_command, match_command, handle_photo
)

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

logger = logging.getLogger(__name__)

# Define conversation states
NAME, AGE, GENDER, PROFILE_PIC, UNIVERSITY, TARGET_UNIVERSITIES, HOBBIES, BIO, RELATIONSHIP_PREFERENCE, COMPLETED = range(10)


def setup_bot():
    """Setup and configure the bot with all required handlers"""
    
    # Get the token from environment variable
    token = os.environ.get("TELEGRAM_BOT_TOKEN", "")
    if not token:
        logger.error("No token provided. Set the TELEGRAM_BOT_TOKEN environment variable.")
        exit(1)
    
    # Load data from database into memory
    from data_store import load_data_from_db
    try:
        logger.info("Loading data from database...")
        load_data_from_db()
        logger.info("Data loaded successfully")
    except Exception as e:
        logger.error(f"Error loading data from database: {e}", exc_info=True)
    
    # Create the application
    application = ApplicationBuilder().token(token).build()
    
    # Registration conversation handler
    registration_handler = ConversationHandler(
        entry_points=[CommandHandler("register", register_command)],
        states={
            NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_name)],
            AGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_age)],
            GENDER: [CallbackQueryHandler(handle_gender)],
            PROFILE_PIC: [MessageHandler(filters.PHOTO, handle_profile_pic)],
            UNIVERSITY: [CallbackQueryHandler(handle_university)],
            TARGET_UNIVERSITIES: [CallbackQueryHandler(handle_target_universities)],
            HOBBIES: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_hobbies)],
            BIO: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_bio)],
            RELATIONSHIP_PREFERENCE: [CallbackQueryHandler(handle_relationship_preference)],
            COMPLETED: [CallbackQueryHandler(profile_completed)]
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        name="registration",
        persistent=False
    )
    
    # Add handlers to the application
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("profile", view_profile))
    application.add_handler(CommandHandler("edit_profile", edit_profile_command))
    application.add_handler(CommandHandler("match", match_command))
    application.add_handler(CommandHandler("matches", show_matches))
    # Add handlers for both "secret_crush" and "secretcrush" commands
    application.add_handler(CommandHandler("secret_crush", handle_secret_crush))
    application.add_handler(CommandHandler("secretcrush", handle_secret_crush))
    application.add_handler(registration_handler)
    
    # Handler for inline button callbacks (used in matching, blocking, etc.)
    application.add_handler(CallbackQueryHandler(handle_callback_query))
    
    # Handler for chat messages
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_chat_message))
    
    # Handler for photo uploads (for external crushes and profile picture updates)
    application.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    
    logger.info("Bot setup completed")
    return application
