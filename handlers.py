#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Handlers for bot commands and conversations
"""

import logging
import re
from io import BytesIO
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler
from data_store import (
    get_user_profile, save_user_profile, get_matches, save_match, 
    get_potential_matches, process_match_decision, get_secret_crushes,
    add_secret_crush, check_mutual_crush, get_chat_history, add_chat_message,
    block_user_from_db, report_user_to_db, unmatch_user_from_db, get_university_list
)
from utils import (
    is_valid_age, format_profile, check_if_registered, 
    send_profile_with_photo, send_mutual_crush_notification,
    get_profile_picture
)
from constants import UNIVERSITY_LIST, RELATIONSHIP_TYPES

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

logger = logging.getLogger(__name__)

# Define conversation states
NAME, AGE, GENDER, PROFILE_PIC, UNIVERSITY, TARGET_UNIVERSITIES, HOBBIES, BIO, RELATIONSHIP_PREFERENCE, COMPLETED = range(10)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a welcome message when the command /start is issued."""
    user = update.effective_user
    await update.message.reply_html(
        f"Hi {user.mention_html()}! 👋\n\n"
        f"Welcome to Ethiopian University Dating Bot! 💘\n\n"
        f"Find your perfect match among university students across Ethiopia.\n\n"
        f"To get started, use /register to create your profile.\n"
        f"Use /match to find and connect with potential matches.\n"
        f"Use /secret_crush to add someone special (either a bot user or external crush).\n"
        f"Use /help to see all available commands."
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /help is issued."""
    help_text = (
        "🌟 *Ethiopian University Dating Bot Help* 🌟\n\n"
        "*Available Commands:*\n"
        "/start - Start the bot\n"
        "/register - Create your profile (one-time process)\n"
        "/edit_profile - Edit your existing profile\n"
        "/profile - View your profile\n"
        "/match - Find new potential matches to like or pass\n"
        "/matches - See your current matches and start chatting\n"
        "/secret_crush or /secretcrush - Add a secret crush (bot user or external)\n"
        "/help - Show this help message\n"
        "/cancel - Cancel current operation\n\n"
        
        "*How it works:*\n"
        "1. Register your profile with your details\n"
        "2. Browse potential matches\n"
        "3. When you both like each other, you'll match!\n"
        "4. Chat anonymously with your matches\n"
        "5. Use the Secret Crush feature to let someone know you're interested:\n"
        "   - Add users already on the bot\n"
        "   - Add external crushes with their name, social media and photo\n\n"
        
        "*Profile Tips:*\n"
        "• A good profile picture greatly increases your chances of matching\n"
        "• Your profile picture should clearly show your face\n"
        "• Profile pictures are mandatory for all users\n"
        "• Only you and your matches can see your profile picture\n\n"
        
        "Happy dating! 💖"
    )
    await update.message.reply_markdown(help_text)


async def register_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Start the registration process."""
    user_id = update.effective_user.id
    user = update.effective_user
    
    # Always create or update user profile when they start registration
    logger.info(f"Starting registration for user {user_id} ({user.username})")
    
    # Get existing profile or create new one
    user_profile = get_user_profile(user_id)
    
    if not user_profile:
        # Create a new profile with basic info
        user_profile = {
            "telegram_id": user_id,
            "username": user.username if user.username else ""
        }
        logger.info(f"Created new user profile for {user_id}")
    else:
        # Update username if it changed
        if user.username and (not "username" in user_profile or user_profile["username"] != user.username):
            user_profile["username"] = user.username
            logger.info(f"Updated username for {user_id} to {user.username}")
    
    # Save user profile immediately to ensure they exist in the database
    save_user_profile(user_id, user_profile)
    logger.info(f"Saved initial profile for {user_id}")
    
    if user_profile and user_profile.get("profile_complete"):
        # If the user already has a complete profile, direct them to /edit_profile
        await update.message.reply_text(
            "You already have a complete profile. To make changes, please use /edit_profile instead.\n"
            "To view your current profile, use /profile."
        )
        return ConversationHandler.END
    elif "name" in user_profile:
        # If they have started but not completed registration
        await update.message.reply_text(
            "Let's complete your dating profile! 📝\n"
            "You can use /cancel at any time to stop the process.\n\n"
            "Let's start with your full name:"
        )
    else:
        # New user starting registration
        await update.message.reply_text(
            "Let's create your dating profile! 📝\n"
            "You can use /cancel at any time to stop the process.\n\n"
            "What's your full name?"
        )
    
    return NAME


async def handle_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle the user's name input."""
    user_id = update.effective_user.id
    name = update.message.text.strip()
    
    if len(name) < 3 or len(name) > 50:
        await update.message.reply_text(
            "Please enter a valid name between 3 and 50 characters."
        )
        return NAME
    
    # Save the name to user data
    user_profile = get_user_profile(user_id) or {}
    user_profile["name"] = name
    
    # Set username if available (helps with lookups for secret crush)
    if update.effective_user.username and "username" not in user_profile:
        user_profile["username"] = update.effective_user.username
    
    # Create the user in the database immediately
    # We're setting partial=True to indicate this is a partial profile being saved
    save_user_profile(user_id, user_profile)
    
    await update.message.reply_text(
        f"Nice to meet you, {name}! 👋\n"
        f"How old are you? (Must be 18+)"
    )
    
    return AGE


async def handle_age(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle the user's age input."""
    user_id = update.effective_user.id
    age_text = update.message.text.strip()
    
    if not is_valid_age(age_text):
        await update.message.reply_text(
            "Please enter a valid age (must be a number 18 or older)."
        )
        return AGE
    
    age = int(age_text)
    
    # Save the age to user data
    user_profile = get_user_profile(user_id)
    user_profile["age"] = age
    save_user_profile(user_id, user_profile)
    
    # Create gender selection keyboard
    keyboard = [
        [
            InlineKeyboardButton("Male", callback_data="gender_male"),
            InlineKeyboardButton("Female", callback_data="gender_female"),
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "What's your gender?",
        reply_markup=reply_markup
    )
    
    return GENDER


async def handle_gender(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle the user's gender selection."""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    gender = query.data.split("_")[1]  # gender_male or gender_female
    
    # Save the gender to user data
    user_profile = get_user_profile(user_id)
    user_profile["gender"] = gender
    save_user_profile(user_id, user_profile)
    
    await query.edit_message_text(
        f"Gender: {gender.capitalize()}\n\n"
        f"Please send your profile picture (send as a photo, not as a file)"
    )
    
    return PROFILE_PIC


async def handle_profile_pic(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle the user's profile picture."""
    user_id = update.effective_user.id
    
    # Get the largest photo (best quality)
    photo_file = await update.message.photo[-1].get_file()
    
    # Download the photo as bytes
    photo_bytes = await photo_file.download_as_bytearray()
    
    # Save the profile picture to user data (as bytes)
    user_profile = get_user_profile(user_id)
    user_profile["profile_pic"] = photo_bytes.hex()  # Convert to hex string for storage
    save_user_profile(user_id, user_profile)
    
    # Create university selection keyboard
    keyboard = []
    university_list = get_university_list()
    
    # Create buttons in rows of 2
    for i in range(0, len(university_list), 2):
        row = []
        row.append(InlineKeyboardButton(university_list[i], callback_data=f"uni_{i}"))
        if i + 1 < len(university_list):
            row.append(InlineKeyboardButton(university_list[i+1], callback_data=f"uni_{i+1}"))
        keyboard.append(row)
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "Great! Now, select your university:",
        reply_markup=reply_markup
    )
    
    return UNIVERSITY


async def handle_university(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle the user's university selection."""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    university_idx = int(query.data.split("_")[1])
    university_list = get_university_list()
    university = university_list[university_idx]
    
    # Save the university to user data
    user_profile = get_user_profile(user_id)
    user_profile["university"] = university
    save_user_profile(user_id, user_profile)
    
    # Create target universities selection keyboard
    keyboard = []
    
    # Add "All Universities" option
    keyboard.append([InlineKeyboardButton("All Universities", callback_data="target_all")])
    
    # Create buttons in rows of 2 for specific universities
    for i in range(0, len(university_list), 2):
        row = []
        row.append(InlineKeyboardButton(university_list[i], callback_data=f"target_{i}"))
        if i + 1 < len(university_list):
            row.append(InlineKeyboardButton(university_list[i+1], callback_data=f"target_{i+1}"))
        keyboard.append(row)
    
    # Add Done button
    keyboard.append([InlineKeyboardButton("Done Selecting", callback_data="target_done")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Initialize target_universities as an empty list
    user_profile["target_universities"] = []
    save_user_profile(user_id, user_profile)
    
    await query.edit_message_text(
        f"Your university: {university}\n\n"
        f"Now, select universities you want to date from (you can select multiple):",
        reply_markup=reply_markup
    )
    
    return TARGET_UNIVERSITIES


async def handle_target_universities(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle the user's target universities selection."""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    user_profile = get_user_profile(user_id)
    
    if query.data == "target_all":
        # User selected all universities
        user_profile["target_universities"] = ["All"]
        save_user_profile(user_id, user_profile)
        
        await query.edit_message_text(
            "You've selected all universities.\n\n"
            "What are your hobbies and interests? (separate with commas)"
        )
        return HOBBIES
    
    elif query.data == "target_done":
        # User is done selecting
        if not user_profile.get("target_universities"):
            # If no universities selected, prompt to select at least one
            await query.answer("Please select at least one university")
            return TARGET_UNIVERSITIES
        
        await query.edit_message_text(
            "Universities selected!\n\n"
            "What are your hobbies and interests? (separate with commas)"
        )
        return HOBBIES
    
    else:
        # User selected a specific university
        university_idx = int(query.data.split("_")[1])
        university_list = get_university_list()
        selected_university = university_list[university_idx]
        
        # Add to the list if not already there
        if "target_universities" not in user_profile:
            user_profile["target_universities"] = []
            
        if "All" in user_profile["target_universities"]:
            # If "All" was previously selected, clear it
            user_profile["target_universities"] = []
            
        if selected_university not in user_profile["target_universities"]:
            user_profile["target_universities"].append(selected_university)
        
        save_user_profile(user_id, user_profile)
        
        # Recreate the keyboard with selected universities marked
        keyboard = []
        keyboard.append([InlineKeyboardButton("All Universities", callback_data="target_all")])
        
        for i in range(0, len(university_list), 2):
            row = []
            uni1 = university_list[i]
            selected1 = "✅ " if uni1 in user_profile["target_universities"] else ""
            row.append(InlineKeyboardButton(f"{selected1}{uni1}", callback_data=f"target_{i}"))
            
            if i + 1 < len(university_list):
                uni2 = university_list[i+1]
                selected2 = "✅ " if uni2 in user_profile["target_universities"] else ""
                row.append(InlineKeyboardButton(f"{selected2}{uni2}", callback_data=f"target_{i+1}"))
            
            keyboard.append(row)
        
        keyboard.append([InlineKeyboardButton("Done Selecting", callback_data="target_done")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        selected_text = ", ".join(user_profile["target_universities"])
        await query.edit_message_text(
            f"Your university: {user_profile['university']}\n\n"
            f"Selected universities: {selected_text}\n\n"
            f"Continue selecting or press 'Done Selecting' when finished:",
            reply_markup=reply_markup
        )
        
        return TARGET_UNIVERSITIES


async def handle_hobbies(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle the user's hobbies input."""
    user_id = update.effective_user.id
    hobbies_text = update.message.text.strip()
    
    if len(hobbies_text) < 3 or len(hobbies_text) > 200:
        await update.message.reply_text(
            "Please enter valid hobbies between 3 and 200 characters."
        )
        return HOBBIES
    
    # Save the hobbies to user data
    user_profile = get_user_profile(user_id)
    user_profile["hobbies"] = hobbies_text
    save_user_profile(user_id, user_profile)
    
    await update.message.reply_text(
        f"Great! Now, write a short bio about yourself (max 500 characters):"
    )
    
    return BIO


async def handle_bio(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle the user's bio input."""
    user_id = update.effective_user.id
    bio_text = update.message.text.strip()
    
    if len(bio_text) < 10 or len(bio_text) > 500:
        await update.message.reply_text(
            "Please enter a bio between 10 and 500 characters."
        )
        return BIO
    
    # Save the bio to user data
    user_profile = get_user_profile(user_id)
    user_profile["bio"] = bio_text
    save_user_profile(user_id, user_profile)
    
    # Create relationship preference keyboard
    keyboard = []
    for i in range(0, len(RELATIONSHIP_TYPES), 2):
        row = []
        row.append(InlineKeyboardButton(RELATIONSHIP_TYPES[i], callback_data=f"rel_{i}"))
        if i + 1 < len(RELATIONSHIP_TYPES):
            row.append(InlineKeyboardButton(RELATIONSHIP_TYPES[i+1], callback_data=f"rel_{i+1}"))
        keyboard.append(row)
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "Finally, what type of relationship are you looking for?",
        reply_markup=reply_markup
    )
    
    # Add a safety measure to make sure we're registered for the next callback
    context.user_data["waiting_for_relationship"] = True
    
    return RELATIONSHIP_PREFERENCE


async def handle_relationship_preference(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle the user's relationship preference selection."""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    rel_idx = int(query.data.split("_")[1])
    relationship = RELATIONSHIP_TYPES[rel_idx]
    
    # Save the relationship preference to user data
    user_profile = get_user_profile(user_id)
    user_profile["relationship_preference"] = relationship
    
    # Mark profile as complete
    user_profile["profile_complete"] = True
    save_user_profile(user_id, user_profile)
    
    # Create profile review keyboard
    keyboard = [
        [InlineKeyboardButton("Start Matching", callback_data="start_matching")],
        [InlineKeyboardButton("Edit Profile", callback_data="edit_profile")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    profile_text = format_profile(user_profile)
    
    await query.edit_message_text(
        f"🎉 Your profile is complete! Here's how it looks:\n\n{profile_text}\n\n"
        f"What would you like to do next?",
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )
    
    return COMPLETED


async def profile_completed(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle the user's choice after completing the profile."""
    query = update.callback_query
    await query.answer()
    
    if query.data == "start_matching":
        await query.edit_message_text(
            "Great! You're now ready to start matching. Use the /match command to find new potential matches."
        )
        return ConversationHandler.END
    
    elif query.data == "edit_profile":
        await query.edit_message_text(
            "You can edit your profile by using the /edit_profile command."
        )
        return ConversationHandler.END
    
    return COMPLETED


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancel and end the conversation."""
    await update.message.reply_text(
        "Profile creation cancelled. You can start again with /register"
    )
    return ConversationHandler.END


async def view_profile(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Display the user's profile."""
    user_id = update.effective_user.id
    user_profile = get_user_profile(user_id)
    
    if not user_profile or not user_profile.get("profile_complete"):
        await update.message.reply_text(
            "You don't have a complete profile yet. Use /register to create one."
        )
        return
    
    # Send profile with photo using the utility function
    await send_profile_with_photo(update, user_profile)


async def match_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show potential matches for the user to like or pass on."""
    user_id = update.effective_user.id
    
    if not await check_if_registered(update, user_id):
        return
    
    # Show potential matches
    potential_matches = get_potential_matches(user_id)
    
    if potential_matches:
        await update.message.reply_text("📱 *Finding Your Match* 📱\n\nSwipe through potential matches and like the ones you're interested in!", parse_mode="Markdown")
        
        # Show multiple potential matches (up to 3 for a better experience)
        max_matches_to_show = min(3, len(potential_matches))
        for i in range(max_matches_to_show):
            match_id = potential_matches[i]
            match_profile = get_user_profile(match_id)
            
            if match_profile:
                profile_text = format_profile(match_profile, include_personal=False)
                
                # Create match decision keyboard
                keyboard = [
                    [
                        InlineKeyboardButton("👎 Pass", callback_data=f"pass_{match_id}"),
                        InlineKeyboardButton("👍 Like", callback_data=f"like_{match_id}")
                    ]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                # Send profile with photo using the utility function
                await send_profile_with_photo(
                    update, 
                    match_profile, 
                    caption=profile_text, 
                    reply_markup=reply_markup,
                    include_personal=False
                )
    else:
        await update.message.reply_text(
            "No potential matches found at the moment. Check back later!"
        )


async def show_matches(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show user's existing matches for chat."""
    user_id = update.effective_user.id
    
    if not await check_if_registered(update, user_id):
        return
    
    # Get user's existing matches
    matches = get_matches(user_id)
    
    if matches:
        # User has matches
        await update.message.reply_text("Here are your current matches:")
        
        for match_id in matches:
            match_profile = get_user_profile(match_id)
            if match_profile:
                profile_text = format_profile(match_profile, include_personal=False)
                
                # Create chat keyboard
                keyboard = [
                    [InlineKeyboardButton("Chat", callback_data=f"chat_{match_id}")],
                    [
                        InlineKeyboardButton("Unmatch", callback_data=f"unmatch_{match_id}"),
                        InlineKeyboardButton("Block", callback_data=f"block_{match_id}")
                    ],
                    [InlineKeyboardButton("Report", callback_data=f"report_{match_id}")]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                # Send profile with photo using the utility function
                await send_profile_with_photo(
                    update, 
                    match_profile, 
                    caption=profile_text, 
                    reply_markup=reply_markup,
                    include_personal=False
                )
    else:
        await update.message.reply_text(
            "You don't have any matches yet. Use /match to find potential matches!"
        )


async def handle_match(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle a match decision (like or pass)."""
    query = update.callback_query
    await query.answer()
    
    action, match_id = query.data.split("_")
    match_id = int(match_id)
    user_id = update.effective_user.id
    
    result = process_match_decision(user_id, match_id, action == "like")
    
    if result == "match":
        # It's a match!
        await query.edit_message_reply_markup(reply_markup=None)
        await query.edit_message_caption(
            caption=f"{query.message.caption}\n\n✨ It's a match! You can now chat with this person."
        )
        
        # Send a message to both users
        keyboard = [
            [InlineKeyboardButton("Start Chatting", callback_data=f"chat_{match_id}")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await context.bot.send_message(
            chat_id=user_id,
            text="🎉 You have a new match! Start chatting now.",
            reply_markup=reply_markup
        )
        
        user_profile = get_user_profile(user_id)
        await context.bot.send_message(
            chat_id=match_id,
            text=f"🎉 You have a new match with {user_profile.get('name', 'someone')}! They liked you back.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("Start Chatting", callback_data=f"chat_{user_id}")]
            ])
        )
    
    elif result == "liked":
        # User liked but no match yet
        await query.edit_message_reply_markup(reply_markup=None)
        await query.edit_message_caption(
            caption=f"{query.message.caption}\n\n❤️ You liked this profile! You'll be notified if they like you back."
        )
    
    elif result == "passed":
        # User passed
        await query.edit_message_reply_markup(reply_markup=None)
        await query.edit_message_caption(
            caption=f"{query.message.caption}\n\n👎 You passed on this profile."
        )
    
    # Show next potential match if available
    potential_matches = get_potential_matches(user_id)
    
    if potential_matches:
        next_match_id = potential_matches[0]
        next_match_profile = get_user_profile(next_match_id)
        
        if next_match_profile:
            profile_text = format_profile(next_match_profile, include_personal=False)
            
            # Create match decision keyboard
            keyboard = [
                [
                    InlineKeyboardButton("👎 Pass", callback_data=f"pass_{next_match_id}"),
                    InlineKeyboardButton("👍 Like", callback_data=f"like_{next_match_id}")
                ]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await context.bot.send_message(
                chat_id=user_id,
                text="Here's another potential match for you:"
            )
            
            # Create a custom update object to pass to send_profile_with_photo
            class CustomUpdate:
                def __init__(self, user_id):
                    self.message = type('obj', (object,), {
                        'chat_id': user_id,
                        'from_user': type('obj', (object,), {'id': user_id}),
                        'reply_photo': context.bot.send_photo,
                        'reply_text': context.bot.send_message
                    })
                    self.effective_chat = type('obj', (object,), {'id': user_id})
                    self.effective_user = type('obj', (object,), {'id': user_id})
            
            custom_update = CustomUpdate(user_id)
            
            # Send profile with photo using the utility function
            await send_profile_with_photo(
                custom_update, 
                next_match_profile, 
                caption=profile_text, 
                reply_markup=reply_markup,
                include_personal=False
            )
    else:
        await context.bot.send_message(
            chat_id=user_id,
            text="No more potential matches found at the moment. Check back later!"
        )


async def handle_secret_crush(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle the secret crush command."""
    user_id = update.effective_user.id
    
    if not await check_if_registered(update, user_id):
        return
    
    # Create a keyboard for crush type selection
    keyboard = [
        [InlineKeyboardButton("Add a user from this bot", callback_data="crush_registered")],
        [InlineKeyboardButton("Add someone not on this bot", callback_data="crush_external")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "💖 *Secret Crush* 💖\n\n"
        "Add someone as your secret crush! Choose an option below:\n\n"
        "- *Add a user from this bot*: Choose someone already using this dating bot\n"
        "- *Add someone not on this bot*: Add details about your crush who is not using this bot",
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )
    
    # Clear any previous states
    context.user_data.pop("expecting_crush", None)
    context.user_data.pop("external_crush_step", None)
    context.user_data.pop("external_crush_data", None)


async def edit_profile_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Start the profile editing process."""
    user_id = update.effective_user.id
    user_profile = get_user_profile(user_id)
    
    if not user_profile:
        await update.message.reply_text(
            "You don't have a profile yet. Use /register to create one."
        )
        return
    
    # Create edit options keyboard
    keyboard = [
        [InlineKeyboardButton("Edit Name", callback_data="edit_name")],
        [InlineKeyboardButton("Edit Age", callback_data="edit_age")],
        [InlineKeyboardButton("Edit Gender", callback_data="edit_gender")],
        [InlineKeyboardButton("Edit Profile Picture", callback_data="edit_pic")],
        [InlineKeyboardButton("Edit University", callback_data="edit_university")],
        [InlineKeyboardButton("Edit Target Universities", callback_data="edit_target_unis")],
        [InlineKeyboardButton("Edit Hobbies", callback_data="edit_hobbies")],
        [InlineKeyboardButton("Edit Bio", callback_data="edit_bio")],
        [InlineKeyboardButton("Edit Relationship Preference", callback_data="edit_rel")],
        [InlineKeyboardButton("Cancel", callback_data="cancel_edit")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "What would you like to edit in your profile?",
        reply_markup=reply_markup
    )
    
    # Set the user state for handling responses
    context.user_data["editing_profile"] = True


async def handle_chat_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle regular chat messages."""
    user_id = update.effective_user.id
    text = update.message.text
    
    # Check if we're editing a profile field
    if context.user_data.get("editing_field"):
        field = context.user_data["editing_field"]
        user_profile = get_user_profile(user_id)
        
        if field == "name":
            # Edit name
            if len(text.strip()) < 3:
                await update.message.reply_text("Please enter a valid name (at least 3 characters).")
                return
            user_profile["name"] = text.strip()
            
        elif field == "age":
            # Edit age
            if not is_valid_age(text):
                await update.message.reply_text("Please enter a valid age (between 18 and 30).")
                return
            user_profile["age"] = int(text)
            
        elif field == "hobbies":
            # Edit hobbies
            if len(text.strip()) < 5:
                await update.message.reply_text("Please enter valid hobbies (at least 5 characters).")
                return
            user_profile["hobbies"] = text.strip()
            
        elif field == "bio":
            # Edit bio
            if len(text.strip()) < 10 or len(text.strip()) > 500:
                await update.message.reply_text("Please enter a bio between 10 and 500 characters.")
                return
            user_profile["bio"] = text.strip()
        
        # Save the updated profile
        save_user_profile(user_id, user_profile)
        
        # Clear the editing state
        context.user_data.pop("editing_field")
        
        await update.message.reply_text(
            f"Your {field.replace('_', ' ')} has been updated. Use /profile to see your complete profile."
        )
        return
    
    # Check if we're in the external crush flow
    elif context.user_data.get("external_crush_step"):
        step = context.user_data["external_crush_step"]
        external_crush_data = context.user_data.get("external_crush_data", {})
        
        if step == "name":
            # Validate name
            if len(text.strip()) < 3:
                await update.message.reply_text("Please enter a valid name (at least 3 characters).")
                return
            
            # Save name
            external_crush_data["name"] = text.strip()
            
            # Move to next step
            context.user_data["external_crush_step"] = "social_media"
            context.user_data["external_crush_data"] = external_crush_data
            
            await update.message.reply_text(
                "Great! Now please enter your crush's social media account (Instagram or Telegram handle). "
                "If you don't know it, you can type 'skip'."
            )
            return
        
        elif step == "social_media":
            # Save social media (optional)
            if text.lower() != "skip":
                external_crush_data["social_media"] = text.strip()
            
            # Move to next step
            context.user_data["external_crush_step"] = "photo"
            context.user_data["external_crush_data"] = external_crush_data
            
            await update.message.reply_text(
                "Now, if you have a photo of your crush, please send it. "
                "If not, you can type 'skip'."
            )
            return
        
        elif step == "photo":
            # Save photo (optional)
            if text.lower() == "skip":
                # Add crush without photo
                name = external_crush_data.get("name", "")
                social_media = external_crush_data.get("social_media", "")
                
                result = add_secret_crush(
                    user_id=user_id,
                    crush_id=None,
                    crush_name=name,
                    social_media_account=social_media
                )
                
                if result == "added_external":
                    await update.message.reply_text(
                        f"✅ Your external crush {name} has been added! "
                        f"This will remain secret unless they join the bot and add you back."
                    )
                else:
                    await update.message.reply_text(
                        "❌ There was an error adding your crush. Please try again later."
                    )
                
                # Clear the state
                context.user_data.pop("external_crush_step", None)
                context.user_data.pop("external_crush_data", None)
            
            # If not skip, they should send a photo, so we keep the state
            return
    
    # Check if we're expecting a secret crush username
    elif context.user_data.get("expecting_crush"):
        # Handle secret crush username
        context.user_data["expecting_crush"] = False
        
        # Check if it's either a number for the list index or a valid username
        if text.isdigit():
            # Try to use the index from the displayed list
            try:
                crush_index = int(text) - 1  # Convert to 0-based index
                
                from app import db, app
                from models import User
                
                with app.app_context():
                    users = db.session.query(User).filter(User.telegram_id != user_id).all()
                    
                    if crush_index < 0 or crush_index >= len(users):
                        await update.message.reply_text(
                            f"Invalid number. Please choose a number between 1 and {len(users)}."
                        )
                        return
                    
                    crush_user = users[crush_index]
                    crush_id = crush_user.telegram_id
            except Exception as e:
                logging.error(f"Error processing crush by index: {e}")
                await update.message.reply_text(
                    "An error occurred while processing your selection. Please try again."
                )
                return
        elif text.startswith("@") and len(text) >= 2:
            # Handle username format
            crush_username = text[1:]  # Remove the @ symbol
        else:
            await update.message.reply_text(
                "That doesn't look like a valid input. Please use the format @username or enter a number from the list."
            )
            return
        
        # We need to search for users by username or user ID
        try:
            # First check if the text is a number (direct Telegram ID)
            if crush_username.isdigit():
                crush_id = int(crush_username)
                crush_profile = get_user_profile(crush_id)
                if not crush_profile:
                    await update.message.reply_text(
                        "No user found with that ID. They need to register with the bot first."
                    )
                    return
            else:
                # Try to look up user by username in our database
                from app import db, app
                from models import User
                
                with app.app_context():
                    # Search for any user who might have saved this username
                    # This is a simplified search - in a real app, you'd integrate with Telegram's getChat API
                    # to resolve usernames to user IDs
                    users = db.session.query(User).all()
                    crush_user = None
                    
                    for user in users:
                        user_profile = get_user_profile(user.telegram_id)
                        if user_profile and "username" in user_profile and user_profile["username"] == crush_username:
                            crush_user = user
                            break
                    
                    if not crush_user:
                        await update.message.reply_text(
                            "I couldn't find that user. They might not have registered with the bot yet, or you might "
                            "have entered the wrong username."
                        )
                        return
                    
                    crush_id = crush_user.telegram_id
        except Exception as e:
            logging.error(f"Error looking up crush by username: {e}")
            await update.message.reply_text(
                "An error occurred while looking up that user. Please try again later."
            )
            return
        
        # Don't allow self-crush
        if crush_id == user_id:
            await update.message.reply_text(
                "You can't add yourself as a secret crush! Try someone else 😊"
            )
            return
            
        # Add the secret crush
        result = add_secret_crush(user_id, crush_id)
        
        if result == "added":
            # Get the crush's profile to show their name and photo
            crush_profile = get_user_profile(crush_id)
            if crush_profile:
                # Send a confirmation with the crush's photo if available
                await update.message.reply_text(
                    f"Secret crush on {crush_profile.get('name', 'your crush')} added! "
                    f"They won't be notified unless they add you as a crush too."
                )
                
                # If they have a profile picture, send it as well
                photo_bytes = get_profile_picture(crush_profile)
                if photo_bytes:
                    await update.message.reply_photo(
                        photo=photo_bytes,
                        caption="This is your secret crush 💘"
                    )
            else:
                await update.message.reply_text(
                    f"Secret crush added! They won't be notified unless they add you as a crush too."
                )
            
            # Check if it's a mutual crush
            if check_mutual_crush(user_id, crush_id):
                # It's a mutual crush! Send enhanced notifications with profile pictures
                await send_mutual_crush_notification(context, user_id, crush_id)
        
        elif result == "already_added":
            crush_profile = get_user_profile(crush_id)
            crush_name = crush_profile.get('name', 'this person') if crush_profile else 'this person'
            
            await update.message.reply_text(
                f"You've already added {crush_name} as a secret crush."
            )
    
    # Check if we're in a chat with someone
    elif "chatting_with" in context.user_data:
        recipient_id = context.user_data["chatting_with"]
        
        # Add message to chat history
        add_chat_message(user_id, recipient_id, text)
        
        # Forward the message to the recipient
        sender_profile = get_user_profile(user_id)
        sender_name = sender_profile.get("name", "Anonymous")
        
        await context.bot.send_message(
            chat_id=recipient_id,
            text=f"Message from {sender_name}:\n\n{text}"
        )
    
    else:
        # Regular message, provide help
        await update.message.reply_text(
            "I didn't understand that command. Use /help to see available commands."
        )


async def handle_callback_query(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle inline button callbacks."""
    query = update.callback_query
    await query.answer()
    
    # Parse the callback data
    data = query.data
    user_id = update.effective_user.id
    user_profile = get_user_profile(user_id)
    
    # Handle Secret Crush registration flow
    if data == "crush_registered":
        # Show registered users for crush selection
        from app import db, app
        from models import User
        
        with app.app_context():
            # Get a list of users that could be selected as crush
            users = db.session.query(User).filter(User.telegram_id != user_id).all()
            
            if not users:
                await query.edit_message_text(
                    "💔 There are no other registered users in the system yet. "
                    "Please try again when more people have joined the dating bot."
                )
                return
            
            # Create a message showing registered users to help the person choose
            user_list = "Here are some registered users you might want to add as a crush:\n\n"
            for idx, user in enumerate(users, 1):
                user_profile = get_user_profile(user.telegram_id)
                if user_profile:
                    name = user_profile.get("name", "Anonymous")
                    gender = user_profile.get("gender", "Unknown")
                    university = user_profile.get("university", "Unknown University")
                    user_list += f"{idx}. {name} - {gender} at {university}\n"
            
            user_list += "\n"
            
            await query.edit_message_text(
                "💖 *Secret Crush* 💖\n\n"
                "Add someone as your secret crush and they'll only be notified if they add you too!\n\n" + 
                user_list +
                "Send me the Telegram username of your crush (e.g., @username) or their ID number:\n\n"
                "Note: If you know their Telegram username, use @username format.\n"
                "If you know their ID number (from the list above), you can use that directly.",
                parse_mode="Markdown"
            )
            
            # Set the next state
            context.user_data["expecting_crush"] = True
            
    elif data == "crush_external":
        # Start external crush registration flow
        await query.edit_message_text(
            "💖 *External Secret Crush* 💖\n\n"
            "You can add a crush who is not using this bot. "
            "Please tell me about your crush's name:",
            parse_mode="Markdown"
        )
        
        # Initialize external crush data
        context.user_data["external_crush_step"] = "name"
        context.user_data["external_crush_data"] = {}
    
    # Handle editing profile options
    if data.startswith("edit_"):
        parts = data.split("_")
        edit_field = parts[1] if len(parts) > 1 else ""
        
        if edit_field == "name":
            await query.edit_message_text("Please send me your new name:")
            context.user_data["editing_field"] = "name"
            return
            
        elif edit_field == "age":
            await query.edit_message_text("Please send me your new age (must be between 18 and 30):")
            context.user_data["editing_field"] = "age"
            return
            
        elif edit_field == "gender":
            keyboard = [
                [
                    InlineKeyboardButton("Male", callback_data="gender_male"),
                    InlineKeyboardButton("Female", callback_data="gender_female")
                ]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(
                "Please select your gender:",
                reply_markup=reply_markup
            )
            return
            
        elif edit_field == "pic":
            await query.edit_message_text("Please send me your new profile picture:")
            context.user_data["editing_field"] = "profile_pic"
            return
            
        elif edit_field == "university":
            # Create university selection keyboard
            universities = get_university_list()
            keyboard = []
            for i in range(0, len(universities), 2):
                row = []
                row.append(InlineKeyboardButton(universities[i], callback_data=f"uni_{i}"))
                if i + 1 < len(universities):
                    row.append(InlineKeyboardButton(universities[i+1], callback_data=f"uni_{i+1}"))
                keyboard.append(row)
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(
                "Please select your university:",
                reply_markup=reply_markup
            )
            return
            
        elif edit_field == "target_unis":
            # Create target university selection keyboard
            universities = get_university_list()
            keyboard = []
            for i in range(0, len(universities), 2):
                row = []
                row.append(InlineKeyboardButton(universities[i], callback_data=f"target_uni_{i}"))
                if i + 1 < len(universities):
                    row.append(InlineKeyboardButton(universities[i+1], callback_data=f"target_uni_{i+1}"))
                keyboard.append(row)
            
            # Add "All Universities" option
            keyboard.append([InlineKeyboardButton("All Universities", callback_data="target_uni_all")])
            
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(
                "Please select which universities you want to match with:",
                reply_markup=reply_markup
            )
            return
            
        elif edit_field == "hobbies":
            await query.edit_message_text("Please send me your new hobbies:")
            context.user_data["editing_field"] = "hobbies"
            return
            
        elif edit_field == "bio":
            await query.edit_message_text("Please send me your new bio (between 10 and 500 characters):")
            context.user_data["editing_field"] = "bio"
            return
            
        elif edit_field == "rel":
            # Create relationship preference keyboard
            keyboard = []
            for i in range(0, len(RELATIONSHIP_TYPES), 2):
                row = []
                row.append(InlineKeyboardButton(RELATIONSHIP_TYPES[i], callback_data=f"edit_rel_{i}"))
                if i + 1 < len(RELATIONSHIP_TYPES):
                    row.append(InlineKeyboardButton(RELATIONSHIP_TYPES[i+1], callback_data=f"edit_rel_{i+1}"))
                keyboard.append(row)
            
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(
                "What type of relationship are you looking for?",
                reply_markup=reply_markup
            )
            return
    
    # Handle gender selection for profile editing
    elif data.startswith("gender_"):
        gender = data.split("_")[1]
        if user_profile:
            user_profile["gender"] = gender
            save_user_profile(user_id, user_profile)
        
        await query.edit_message_text(
            f"Your gender has been updated to {gender}. Use /profile to see your updated profile."
        )
        return
    
    # Handle university selection for profile editing
    elif data.startswith("uni_"):
        uni_idx = int(data.split("_")[1])
        universities = get_university_list()
        uni = universities[uni_idx]
        
        if user_profile:
            user_profile["university"] = uni
            save_user_profile(user_id, user_profile)
        
        await query.edit_message_text(
            f"Your university has been updated to {uni}. Use /profile to see your updated profile."
        )
        return
    
    # Handle target university selection for profile editing
    elif data.startswith("target_uni_"):
        target = data.split("_")[2]
        
        if user_profile:
            if target == "all":
                user_profile["target_universities"] = ["All Universities"]
            else:
                uni_idx = int(target)
                universities = get_university_list()
                uni = universities[uni_idx]
                user_profile["target_universities"] = [uni]
            
            save_user_profile(user_id, user_profile)
            
            target_unis = ", ".join(user_profile["target_universities"])
            await query.edit_message_text(
                f"Your target universities have been updated to {target_unis}. Use /profile to see your updated profile."
            )
        else:
            await query.edit_message_text(
                "Error updating profile. Please try again."
            )
        return
    
    # Handle relationship preference selection for profile editing
    elif data.startswith("edit_rel_"):
        rel_idx = int(data.split("_")[2])
        relationship = RELATIONSHIP_TYPES[rel_idx]
        
        if user_profile:
            user_profile["relationship_preference"] = relationship
            save_user_profile(user_id, user_profile)
            
            await query.edit_message_text(
                f"Your relationship preference has been updated to {relationship}. Use /profile to see your updated profile."
            )
        else:
            await query.edit_message_text(
                "Error updating profile. Please try again."
            )
        return
    
    # Handle cancel edit
    elif data == "cancel_edit":
        context.user_data.pop("editing_profile", None)
        context.user_data.pop("editing_field", None)
        
        await query.edit_message_text(
            "Profile editing cancelled. Use /profile to see your current profile."
        )
        return
    
    # Parse the original callback data
    parts = data.split("_")
    action = parts[0]
    
    if action in ["like", "pass"]:
        # Handle match decisions
        await handle_match(update, context)
    
    elif action == "chat":
        # Start a chat with a match
        match_id = int(parts[1])
        user_id = update.effective_user.id
        
        # Set the active chat
        context.user_data["chatting_with"] = match_id
        
        # Get chat history
        chat_history = get_chat_history(user_id, match_id)
        
        if chat_history:
            # Display chat history
            history_text = "--- Chat History ---\n\n"
            for msg in chat_history:
                sender_id = msg["sender_id"]
                sender_profile = get_user_profile(sender_id)
                sender_name = sender_profile.get("name", "Anonymous")
                history_text += f"{sender_name}: {msg['text']}\n"
            
            await query.edit_message_text(
                text=f"{history_text}\n\nYou are now chatting with your match. Simply type messages to chat."
            )
        else:
            # No chat history
            match_profile = get_user_profile(match_id)
            match_name = match_profile.get("name", "your match")
            
            await query.edit_message_text(
                text=f"You are now chatting with {match_name}. This is the beginning of your conversation. "
                     f"Simply type messages to chat."
            )
    
    elif action == "block":
        # Block a user
        match_id = int(parts[1])
        user_id = update.effective_user.id
        
        block_user_from_db(user_id, match_id)
        
        await query.edit_message_reply_markup(reply_markup=None)
        await query.edit_message_text(
            text="You have blocked this user. They can no longer contact you."
        )
    
    elif action == "report":
        # Report a user
        match_id = int(parts[1])
        user_id = update.effective_user.id
        
        report_user_to_db(user_id, match_id)
        
        await query.edit_message_reply_markup(reply_markup=None)
        await query.edit_message_text(
            text="Thank you for your report. We'll review this user's profile."
        )
    
    elif action == "unmatch":
        # Unmatch a user
        match_id = int(parts[1])
        user_id = update.effective_user.id
        
        unmatch_user_from_db(user_id, match_id)
        
        await query.edit_message_reply_markup(reply_markup=None)
        await query.edit_message_text(
            text="You have unmatched with this user."
        )


async def block_user(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Block a user."""
    # This will be handled by the callback query handler
    pass


async def report_user(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Report a user."""
    # This will be handled by the callback query handler
    pass


async def unmatch_user(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Unmatch a user."""
    # This will be handled by the callback query handler
    pass


async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle photo uploads, including for external crushes."""
    user_id = update.effective_user.id
    
    # Check if we're in the external crush flow and expecting a photo
    if context.user_data.get("external_crush_step") == "photo":
        external_crush_data = context.user_data.get("external_crush_data", {})
        
        # Get the photo with best resolution
        photo = update.message.photo[-1]
        photo_file = await context.bot.get_file(photo.file_id)
        photo_bytes = await photo_file.download_as_bytearray()
        
        # Convert to hex string for storage
        photo_hex = photo_bytes.hex()
        
        # Add crush with photo
        name = external_crush_data.get("name", "")
        social_media = external_crush_data.get("social_media", "")
        
        result = add_secret_crush(
            user_id=user_id,
            crush_id=None,
            crush_name=name,
            social_media_account=social_media,
            crush_photo=photo_hex
        )
        
        if result == "added_external":
            await update.message.reply_text(
                f"✅ Your external crush {name} has been added with photo! "
                f"This will remain secret unless they join the bot and add you back."
            )
            
            # Echo back the photo they sent
            await update.message.reply_photo(
                photo=photo_bytes,
                caption=f"This is your secret crush: {name} 💘"
            )
        else:
            await update.message.reply_text(
                "❌ There was an error adding your crush. Please try again later."
            )
        
        # Clear the state
        context.user_data.pop("external_crush_step", None)
        context.user_data.pop("external_crush_data", None)
    
    # If we're editing the profile picture
    elif context.user_data.get("editing_field") == "profile_pic":
        user_profile = get_user_profile(user_id)
        if user_profile:
            # Get the photo with best resolution
            photo = update.message.photo[-1]
            photo_file = await context.bot.get_file(photo.file_id)
            photo_bytes = await photo_file.download_as_bytearray()
            
            # Convert to hex string for storage
            photo_hex = photo_bytes.hex()
            
            # Update profile
            user_profile["profile_pic"] = photo_hex
            save_user_profile(user_id, user_profile)
            
            # Send confirmation
            await update.message.reply_text(
                "Your profile picture has been updated. Use /profile to see your updated profile."
            )
            
            # Clear editing state
            context.user_data.pop("editing_field", None)
    
    # If not expecting any photo, just provide help
    else:
        await update.message.reply_text(
            "I've received your photo, but I'm not sure what to do with it. "
            "Use /help to see available commands."
        )
