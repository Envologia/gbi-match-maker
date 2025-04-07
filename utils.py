#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Utility functions for the bot
"""

import re
from io import BytesIO
from typing import Dict, Any, Optional, Tuple, Union
from telegram import Update, Message, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from data_store import get_user_profile


def is_valid_age(age_text: str) -> bool:
    """
    Check if the provided age is valid.
    
    - Must be numeric
    - Must be between 18 and 30 inclusive
    """
    if not age_text.isdigit():
        return False
    
    age = int(age_text)
    return 18 <= age <= 30


def format_profile(profile: Dict[str, Any], include_personal: bool = True) -> str:
    """
    Format a user profile for display.
    
    Args:
        profile: The user profile dictionary
        include_personal: Whether to include personal details (name, etc.)
    
    Returns:
        A formatted string representation of the profile
    """
    formatted = ""
    
    if include_personal:
        formatted += f"*{profile.get('name', 'N/A')}*, {profile.get('age', 'N/A')}\n"
    else:
        formatted += f"*{profile.get('name', 'N/A')}*, {profile.get('age', 'N/A')}\n"
    
    formatted += f"*Gender:* {profile.get('gender', 'N/A').capitalize()}\n"
    formatted += f"*University:* {profile.get('university', 'N/A')}\n"
    
    if include_personal:
        formatted += f"*Looking for matches from:* {', '.join(profile.get('target_universities', ['N/A']))}\n"
    
    formatted += f"*Looking for:* {profile.get('relationship_preference', 'N/A')}\n\n"
    formatted += f"*Hobbies:* {profile.get('hobbies', 'N/A')}\n\n"
    formatted += f"*About me:*\n{profile.get('bio', 'N/A')}"
    
    return formatted


def get_profile_picture(profile: Dict[str, Any]) -> Optional[BytesIO]:
    """
    Get a user's profile picture as a BytesIO object.
    
    Args:
        profile: The user profile dictionary
    
    Returns:
        BytesIO object containing the profile picture, or None if no picture
    """
    if "profile_pic" in profile and profile["profile_pic"]:
        try:
            photo_bytes = bytes.fromhex(profile["profile_pic"])
            return BytesIO(photo_bytes)
        except Exception:
            return None
    return None


async def send_profile_with_photo(
    update: Update, 
    profile: Dict[str, Any], 
    caption: Optional[str] = None, 
    reply_markup: Optional[InlineKeyboardMarkup] = None,
    include_personal: bool = True
) -> Union[Message, None]:
    """
    Send a profile with its photo.
    
    Args:
        update: The update object
        profile: The user profile dictionary
        caption: Optional caption to use instead of the formatted profile
        reply_markup: Optional inline keyboard markup
        include_personal: Whether to include personal details in the formatted profile
    
    Returns:
        The sent message
    """
    if not caption:
        caption = format_profile(profile, include_personal=include_personal)
    
    photo_io = get_profile_picture(profile)
    
    # Check if this is a regular Update or our CustomUpdate
    is_custom_update = not hasattr(update, 'effective_message') and hasattr(update, 'message')
    
    if photo_io:
        if is_custom_update:
            # This is a CustomUpdate with a direct bot reference
            chat_id = update.effective_chat.id if hasattr(update, 'effective_chat') else update.message.chat_id
            return await update.message.reply_photo(
                chat_id=chat_id,
                photo=photo_io,
                caption=caption,
                reply_markup=reply_markup,
                parse_mode="Markdown"
            )
        else:
            # Regular update
            return await update.message.reply_photo(
                photo=photo_io,
                caption=caption,
                reply_markup=reply_markup,
                parse_mode="Markdown"
            )
    else:
        if is_custom_update:
            # This is a CustomUpdate with a direct bot reference
            chat_id = update.effective_chat.id if hasattr(update, 'effective_chat') else update.message.chat_id
            return await update.message.reply_text(
                chat_id=chat_id,
                text=caption,
                reply_markup=reply_markup,
                parse_mode="Markdown"
            )
        else:
            # Regular update
            return await update.message.reply_text(
                caption,
                reply_markup=reply_markup,
                parse_mode="Markdown"
            )


async def check_if_registered(update: Update, user_id: int) -> bool:
    """
    Check if a user is registered and has a complete profile.
    
    Returns:
        True if the user is registered, False otherwise
    """
    user_profile = get_user_profile(user_id)
    
    if not user_profile or not user_profile.get("profile_complete"):
        await update.message.reply_text(
            "You need to complete your profile first. Use /register to create your profile."
        )
        return False
    
    return True


async def send_mutual_crush_notification(context, user_id: int, crush_id: int) -> None:
    """
    Send notifications to both users when there's a mutual crush match.
    This uses profile pictures and formatted text for better presentation.
    
    Args:
        context: The context object containing the bot
        user_id: The ID of the first user
        crush_id: The ID of the second user (crush)
    """
    user_profile = get_user_profile(user_id)
    crush_profile = get_user_profile(crush_id)
    
    if not user_profile or not crush_profile:
        return
    
    # Message for the user
    user_msg = f"💞 *Secret Crush Match!* 💞\n\n" \
              f"Good news! {crush_profile.get('name', 'Your crush')} has a crush on you too! " \
              f"You both like each other. Why not start a conversation?"
    
    # Message for the crush
    crush_msg = f"💞 *Secret Crush Match!* 💞\n\n" \
               f"Good news! {user_profile.get('name', 'Someone')} has a crush on you too! " \
               f"You both like each other. Why not start a conversation?"
    
    # Get profile pictures
    user_photo = get_profile_picture(user_profile)
    crush_photo = get_profile_picture(crush_profile)
    
    # Send notification to user with crush's photo
    if crush_photo:
        await context.bot.send_photo(
            chat_id=user_id,
            photo=crush_photo,
            caption=user_msg,
            parse_mode="Markdown"
        )
    else:
        await context.bot.send_message(
            chat_id=user_id,
            text=user_msg,
            parse_mode="Markdown"
        )
    
    # Send notification to crush with user's photo
    if user_photo:
        await context.bot.send_photo(
            chat_id=crush_id,
            photo=user_photo,
            caption=crush_msg,
            parse_mode="Markdown"
        )
    else:
        await context.bot.send_message(
            chat_id=crush_id,
            text=crush_msg,
            parse_mode="Markdown"
        )
