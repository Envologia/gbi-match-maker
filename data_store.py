#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
In-memory data storage for user profiles, matches, and chats
"""

import logging
from typing import Dict, List, Any, Optional, Set, Tuple, Union
import time
import random
from constants import UNIVERSITY_LIST

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

logger = logging.getLogger(__name__)

# In-memory storage
user_profiles: Dict[int, Dict[str, Any]] = {}
matches: Dict[int, Set[int]] = {}  # user_id -> set of matched user_ids
likes: Dict[int, Set[int]] = {}  # user_id -> set of users they've liked
blocks: Dict[int, Set[int]] = {}  # user_id -> set of users they've blocked
reports: Dict[int, List[int]] = {}  # user_id -> list of users they've reported
secret_crushes: Dict[int, Set[int]] = {}  # user_id -> set of secret crushes
chats: Dict[tuple, List[Dict[str, Any]]] = {}  # (user1_id, user2_id) -> list of chat messages


def load_data_from_db():
    """Load data from the database into memory."""
    try:
        # Import here to avoid circular imports
        from app import db, app
        from models import User, Like, SecretCrush, Block, Message
        
        # Use Flask application context
        with app.app_context():
            # Load users
            db_users = db.session.query(User).all()
            logger.info(f"Found {len(db_users)} users in database")
            
            for user in db_users:
                logger.info(f"Loading user {user.telegram_id} from database")
                # Create basic profile
                user_profile = {
                    "name": user.name,
                    "age": user.age,
                    "gender": user.gender,
                    "university": user.university,
                    "bio": user.bio or "",
                    "hobbies": user.hobbies or "",
                    "relationship_preference": user.relationship_preference or "",
                    "profile_pic_url": user.profile_pic_url or "",
                    "profile_pic": user.profile_pic or "",
                    "profile_complete": True,  # If in DB, it's complete
                    "target_universities": [],
                    "username": ""  # Initialize username field
                }
                
                # Get target universities
                for target_uni in user.target_universities:
                    user_profile["target_universities"].append(target_uni.university_name)
                
                # Store in memory
                user_profiles[user.telegram_id] = user_profile
            
            # Load matches from likes
            db_likes = db.session.query(Like).all()
            for like in db_likes:
                # Get telegram IDs
                sender = db.session.query(User).filter_by(id=like.sender_id).first()
                receiver = db.session.query(User).filter_by(id=like.receiver_id).first()
                
                if sender and receiver:
                    # Add to likes
                    if sender.telegram_id not in likes:
                        likes[sender.telegram_id] = set()
                    likes[sender.telegram_id].add(receiver.telegram_id)
                    
                    # If it's a match, add to matches
                    if like.is_match:
                        if sender.telegram_id not in matches:
                            matches[sender.telegram_id] = set()
                        if receiver.telegram_id not in matches:
                            matches[receiver.telegram_id] = set()
                        
                        matches[sender.telegram_id].add(receiver.telegram_id)
                        matches[receiver.telegram_id].add(sender.telegram_id)
            
            # Load secret crushes
            db_crushes = db.session.query(SecretCrush).all()
            for crush in db_crushes:
                # Get telegram IDs
                crusher = db.session.query(User).filter_by(id=crush.crusher_id).first()
                crushee = db.session.query(User).filter_by(id=crush.crushee_id).first()
                
                if crusher and crushee:
                    # Add to secret crushes
                    if crusher.telegram_id not in secret_crushes:
                        secret_crushes[crusher.telegram_id] = set()
                    
                    secret_crushes[crusher.telegram_id].add(crushee.telegram_id)
            
            # Load blocks
            db_blocks = db.session.query(Block).all()
            for block in db_blocks:
                # Get telegram IDs
                blocker = db.session.query(User).filter_by(id=block.blocker_id).first()
                blocked = db.session.query(User).filter_by(id=block.blocked_id).first()
                
                if blocker and blocked:
                    # Add to blocks
                    if blocker.telegram_id not in blocks:
                        blocks[blocker.telegram_id] = set()
                    
                    blocks[blocker.telegram_id].add(blocked.telegram_id)
        
        logger.info(f"Loaded data from database: {len(user_profiles)} users, "
                  f"{sum(len(v) for v in matches.values()) // 2} matches, "
                  f"{sum(len(v) for v in secret_crushes.values())} secret crushes")
    except Exception as e:
        logger.error(f"Error loading data from database: {e}", exc_info=True)


def get_user_profile(user_id: int) -> Optional[Dict[str, Any]]:
    """Get a user's profile from storage."""
    profile = user_profiles.get(user_id)
    if profile is None:
        # Try to load directly from database if not in memory
        try:
            from app import db, app
            from models import User
            
            with app.app_context():
                db_user = db.session.query(User).filter_by(telegram_id=user_id).first()
                if db_user:
                    logger.info(f"Found user {user_id} in database that wasn't in memory, loading now")
                    profile = {
                        "name": db_user.name,
                        "age": db_user.age,
                        "gender": db_user.gender,
                        "university": db_user.university,
                        "bio": db_user.bio or "",
                        "hobbies": db_user.hobbies or "",
                        "relationship_preference": db_user.relationship_preference or "",
                        "profile_pic_url": db_user.profile_pic_url or "",
                        "profile_pic": db_user.profile_pic or "",
                        "profile_complete": True,  # If in DB, it's complete
                        "target_universities": [],
                        "username": ""  # Initialize username field
                    }
                    
                    # Get target universities
                    for target_uni in db_user.target_universities:
                        profile["target_universities"].append(target_uni.university_name)
                    
                    # Save to in-memory cache
                    user_profiles[user_id] = profile
        except Exception as e:
            logger.error(f"Error loading user profile from database: {e}", exc_info=True)
    
    return profile


def save_user_profile(user_id: int, profile_data: Dict[str, Any]) -> None:
    """Save a user's profile to storage (both in-memory and database)."""
    # Save to in-memory storage first
    user_profiles[user_id] = profile_data
    logger.info(f"Saving profile for user {user_id} to in-memory storage: {profile_data}")
    
    # Only skip database save if there's no meaningful data yet
    if not profile_data:
        logger.info(f"Skipping database save for user {user_id} - empty profile data")
        return
    
    try:
        # Import here to avoid circular imports
        from app import db, app
        from models import User, TargetUniversity
        
        logger.info(f"Starting database save for user {user_id}")
        
        # Use Flask application context
        with app.app_context():
            # Check if user exists in database
            db_user = db.session.query(User).filter_by(telegram_id=user_id).first()
            logger.info(f"User {user_id} exists in database: {db_user is not None}")
            
            if not db_user:
                # Create new user
                logger.info(f"Creating new user for {user_id} in database")
                db_user = User(
                    telegram_id=user_id,
                    name=profile_data.get("name", ""),
                    age=profile_data.get("age", 18),
                    gender=profile_data.get("gender", ""),
                    university=profile_data.get("university", ""),
                    bio=profile_data.get("bio", ""),
                    hobbies=profile_data.get("hobbies", ""),
                    relationship_preference=profile_data.get("relationship_preference", ""),
                    profile_pic_url=profile_data.get("profile_pic_url", ""),
                    profile_pic=profile_data.get("profile_pic", "")
                )
                db.session.add(db_user)
                db.session.flush()  # Flush to get the user ID
                logger.info(f"User {user_id} added to session with DB id {db_user.id}")
                
                # Add target universities if they exist
                if "target_universities" in profile_data:
                    target_unis = profile_data.get("target_universities", [])
                    logger.info(f"Adding {len(target_unis)} target universities for user {user_id}")
                    for uni in target_unis:
                        target_uni = TargetUniversity(
                            user_id=db_user.id,
                            university_name=uni
                        )
                        db.session.add(target_uni)
            
            elif db_user:
                # Update existing user
                logger.info(f"Updating existing user {user_id} in database")
                db_user.name = profile_data.get("name", db_user.name)
                db_user.age = profile_data.get("age", db_user.age)
                db_user.gender = profile_data.get("gender", db_user.gender)
                db_user.university = profile_data.get("university", db_user.university)
                db_user.bio = profile_data.get("bio", db_user.bio)
                db_user.hobbies = profile_data.get("hobbies", db_user.hobbies)
                db_user.relationship_preference = profile_data.get("relationship_preference", db_user.relationship_preference)
                db_user.profile_pic_url = profile_data.get("profile_pic_url", db_user.profile_pic_url)
                
                # Update profile picture if provided
                if "profile_pic" in profile_data:
                    db_user.profile_pic = profile_data["profile_pic"]
                
                # Update target universities if they exist in the profile data
                if "target_universities" in profile_data:
                    # Remove existing target universities
                    logger.info(f"Updating target universities for user {user_id}")
                    db.session.query(TargetUniversity).filter_by(user_id=db_user.id).delete()
                    
                    # Add new target universities
                    target_unis = profile_data.get("target_universities", [])
                    for uni in target_unis:
                        target_uni = TargetUniversity(
                            user_id=db_user.id,
                            university_name=uni
                        )
                        db.session.add(target_uni)
            
            # Commit the transaction
            logger.info(f"Committing database transaction for user {user_id}")
            db.session.commit()
            logger.info(f"Successfully saved profile for user {user_id} to database")
            
    except Exception as e:
        logger.error(f"Error saving user profile to database: {e}", exc_info=True)
    
    logger.info(f"Completed profile save for user {user_id}")


def get_university_list() -> List[str]:
    """Get the list of universities."""
    return UNIVERSITY_LIST


def get_matches(user_id: int) -> List[int]:
    """Get a user's matches."""
    return list(matches.get(user_id, set()))


def save_match(user_id: int, match_id: int) -> None:
    """Save a match between two users."""
    if user_id not in matches:
        matches[user_id] = set()
    if match_id not in matches:
        matches[match_id] = set()
    
    matches[user_id].add(match_id)
    matches[match_id].add(user_id)
    logger.info(f"Match saved between {user_id} and {match_id}")


def get_potential_matches(user_id: int) -> List[int]:
    """
    Get potential matches for a user based on gender and university only.
    
    This simplified algorithm:
    1. Only matches users of opposite gender
    2. Only considers university preferences
    3. Excludes users already matched, liked, or blocked
    """
    user_profile = get_user_profile(user_id)
    if not user_profile or not user_profile.get("profile_complete"):
        return []
    
    # Get user's gender and university
    user_gender = user_profile.get("gender")
    user_university = user_profile.get("university")
    target_universities = user_profile.get("target_universities", [])
    
    # Users to exclude (matches, likes, blocks)
    excluded_users = set()
    
    # Add users this user has already liked
    if user_id in likes:
        excluded_users.update(likes[user_id])
    
    # Add users this user has blocked
    if user_id in blocks:
        excluded_users.update(blocks[user_id])
    
    # Add users who have blocked this user
    for other_id, other_blocked in blocks.items():
        if user_id in other_blocked:
            excluded_users.add(other_id)
    
    # Add existing matches
    if user_id in matches:
        excluded_users.update(matches[user_id])
    
    logger.info(f"Finding potential matches for user {user_id}")
    potential_matches = []
    
    for other_id, other_profile in user_profiles.items():
        # Skip if it's the same user, not a complete profile, or already excluded
        if (other_id == user_id or 
            not other_profile.get("profile_complete") or
            other_id in excluded_users):
            continue
        
        # Only match opposite gender
        other_gender = other_profile.get("gender")
        if (user_gender == "male" and other_gender != "female") or (user_gender == "female" and other_gender != "male"):
            continue
        
        # Check university preferences
        other_university = other_profile.get("university")
        
        # Only include this user if their university is in the target list
        # or if "All" is selected
        if "All" in target_universities or other_university in target_universities:
            potential_matches.append(other_id)
            logger.info(f"Found potential match: {other_id} ({other_profile.get('name')}) for user {user_id}")
    
    # Randomize order
    random.shuffle(potential_matches)
    logger.info(f"Found {len(potential_matches)} potential matches for user {user_id}")
    
    return potential_matches


def process_match_decision(user_id: int, other_id: int, is_like: bool) -> str:
    """
    Process a user's decision to like or pass on another user.
    
    Returns:
    - "match" if it's a mutual like and a match is created
    - "liked" if the user liked but there's no match yet
    - "passed" if the user passed
    """
    if not is_like:
        # User passed on this profile
        return "passed"
    
    # Add to in-memory liked users
    if user_id not in likes:
        likes[user_id] = set()
    likes[user_id].add(other_id)
    
    try:
        # Import here to avoid circular imports
        from app import db, app
        from models import Like, User
        
        # Use Flask application context
        with app.app_context():
            # Get user IDs from database
            sender = db.session.query(User).filter_by(telegram_id=user_id).first()
            receiver = db.session.query(User).filter_by(telegram_id=other_id).first()
            
            if sender and receiver:
                # Check if like already exists
                existing_like = db.session.query(Like).filter_by(
                    sender_id=sender.id, 
                    receiver_id=receiver.id
                ).first()
                
                if not existing_like:
                    # Create new like
                    like = Like(
                        sender_id=sender.id,
                        receiver_id=receiver.id,
                        is_match=False
                    )
                    db.session.add(like)
                    
                    # Check if there's a reverse like (other user liked this user)
                    reverse_like = db.session.query(Like).filter_by(
                        sender_id=receiver.id, 
                        receiver_id=sender.id
                    ).first()
                    
                    if reverse_like:
                        # It's a match!
                        like.is_match = True
                        reverse_like.is_match = True
                        
                        # Update in-memory matches
                        if user_id not in matches:
                            matches[user_id] = set()
                        if other_id not in matches:
                            matches[other_id] = set()
                        
                        matches[user_id].add(other_id)
                        matches[other_id].add(user_id)
                        
                        db.session.commit()
                        logger.info(f"New match created between {user_id} and {other_id}")
                        return "match"
                
                # Commit changes to database
                db.session.commit()
        
        logger.info(f"User {user_id} liked user {other_id}, saved to database")
    except Exception as e:
        logger.error(f"Error saving like to database: {e}", exc_info=True)
    
    # Check if other user liked this user back (in-memory check)
    if other_id in likes and user_id in likes[other_id]:
        # It's a match!
        if user_id not in matches:
            matches[user_id] = set()
        if other_id not in matches:
            matches[other_id] = set()
        
        matches[user_id].add(other_id)
        matches[other_id].add(user_id)
        
        logger.info(f"New match created between {user_id} and {other_id}")
        return "match"
    
    return "liked"


def add_secret_crush(user_id: int, crush_id: int = None, crush_name: str = None,
                  social_media_account: str = None, crush_photo: str = None) -> str:
    """
    Add a secret crush.
    
    Args:
        user_id: The telegram ID of the user adding the crush
        crush_id: The telegram ID of the crush (if they're a registered user), can be None for external crushes
        crush_name: The name of the crush (required for external crushes)
        social_media_account: The social media account of the crush (optional for external crushes)
        crush_photo: The photo of the crush in hex-encoded format (optional for external crushes)
    
    Returns:
        - "added" if the crush was added
        - "added_external" if an external crush was added
        - "already_added" if the user already has this person as a crush
    """
    # For registered users, handle as before
    if crush_id is not None:
        # Add to in-memory storage
        if user_id not in secret_crushes:
            secret_crushes[user_id] = set()
        
        if crush_id in secret_crushes[user_id]:
            return "already_added"
        
        secret_crushes[user_id].add(crush_id)
        
        try:
            # Import here to avoid circular imports
            from app import db, app
            from models import SecretCrush, User
            
            # Use Flask application context
            with app.app_context():
                # Get user IDs from database
                crusher = db.session.query(User).filter_by(telegram_id=user_id).first()
                crushee = db.session.query(User).filter_by(telegram_id=crush_id).first()
                
                if crusher and crushee:
                    # Check if crush already exists
                    existing_crush = db.session.query(SecretCrush).filter_by(
                        crusher_id=crusher.id, 
                        crushee_id=crushee.id
                    ).first()
                    
                    if not existing_crush:
                        # Check for mutual crush
                        mutual_crush = db.session.query(SecretCrush).filter_by(
                            crusher_id=crushee.id,
                            crushee_id=crusher.id
                        ).first()
                        
                        is_mutual = mutual_crush is not None
                        
                        # Create new crush
                        crush = SecretCrush(
                            crusher_id=crusher.id,
                            crushee_id=crushee.id,
                            is_mutual=is_mutual
                        )
                        db.session.add(crush)
                        
                        # Update mutual status if needed
                        if mutual_crush:
                            mutual_crush.is_mutual = True
                    
                    # Commit changes to database
                    db.session.commit()
            
            logger.info(f"User {user_id} added secret crush on {crush_id}, saved to database")
        except Exception as e:
            logger.error(f"Error saving secret crush to database: {e}", exc_info=True)
        
        logger.info(f"User {user_id} added secret crush on {crush_id}")
        
        return "added"
    
    # For external crushes (not registered in the system)
    else:
        if not crush_name:
            logger.error(f"Error adding external crush: crush_name is required")
            return "error"
        
        try:
            # Import here to avoid circular imports
            from app import db, app
            from models import SecretCrush, User
            
            # Use Flask application context
            with app.app_context():
                # Get user ID from database
                crusher = db.session.query(User).filter_by(telegram_id=user_id).first()
                
                if crusher:
                    # Create new external crush
                    crush = SecretCrush(
                        crusher_id=crusher.id,
                        crushee_id=None,  # No user ID for external crushes
                        crush_name=crush_name,
                        social_media_account=social_media_account,
                        crush_photo=crush_photo,
                        is_mutual=False  # External crushes can't be mutual
                    )
                    db.session.add(crush)
                    db.session.commit()
            
            logger.info(f"User {user_id} added external secret crush {crush_name}, saved to database")
        except Exception as e:
            logger.error(f"Error saving external secret crush to database: {e}", exc_info=True)
        
        logger.info(f"User {user_id} added external secret crush {crush_name}")
        
        return "added_external"


def get_secret_crushes(user_id: int) -> Tuple[List[int], List[Dict[str, Any]]]:
    """
    Get a user's secret crushes.
    
    Returns:
        Tuple containing:
        - List of Telegram IDs for registered user crushes
        - List of dictionaries with details for external crushes
          Each dict contains: 'id', 'name', 'social_media', 'photo'
    """
    registered_crushes = list(secret_crushes.get(user_id, set()))
    external_crushes = []
    
    try:
        # Import here to avoid circular imports
        from app import db, app
        from models import SecretCrush, User
        
        # Use Flask application context
        with app.app_context():
            user = db.session.query(User).filter_by(telegram_id=user_id).first()
            
            if user:
                # Get crushes from database
                db_crushes = db.session.query(SecretCrush).filter_by(crusher_id=user.id).all()
                
                # Process each crush
                for crush in db_crushes:
                    if crush.crushee_id is not None:
                        # This is a registered user crush
                        crushee = db.session.query(User).filter_by(id=crush.crushee_id).first()
                        if crushee and crushee.telegram_id not in registered_crushes:
                            registered_crushes.append(crushee.telegram_id)
                    else:
                        # This is an external crush
                        external_crushes.append({
                            'id': crush.id,  # Database ID for the crush entry
                            'name': crush.crush_name,
                            'social_media': crush.social_media_account,
                            'photo': crush.crush_photo
                        })
            
            # No need to commit as we're just reading
    except Exception as e:
        logger.error(f"Error retrieving secret crushes from database: {e}", exc_info=True)
    
    return registered_crushes, external_crushes


def check_mutual_crush(user_id: int, crush_id: int) -> bool:
    """Check if two users have a mutual crush."""
    # Check in-memory
    mutual_in_memory = (crush_id in secret_crushes.get(user_id, set()) and 
                       user_id in secret_crushes.get(crush_id, set()))
    
    if mutual_in_memory:
        return True
        
    try:
        # Import here to avoid circular imports
        from app import db, app
        from models import SecretCrush, User
        
        # Use Flask application context
        with app.app_context():
            user1 = db.session.query(User).filter_by(telegram_id=user_id).first()
            user2 = db.session.query(User).filter_by(telegram_id=crush_id).first()
            
            if user1 and user2:
                # Check for mutual crush in database
                crush1 = db.session.query(SecretCrush).filter_by(
                    crusher_id=user1.id,
                    crushee_id=user2.id
                ).first()
                
                crush2 = db.session.query(SecretCrush).filter_by(
                    crusher_id=user2.id,
                    crushee_id=user1.id
                ).first()
                
                return crush1 is not None and crush2 is not None
    except Exception as e:
        logger.error(f"Error checking mutual crush in database: {e}", exc_info=True)
    
    return mutual_in_memory


def get_chat_history(user1_id: int, user2_id: int) -> List[Dict[str, Any]]:
    """Get chat history between two users."""
    # Sort IDs to ensure consistent key
    chat_key = tuple(sorted([user1_id, user2_id]))
    
    # Get from in-memory storage
    in_memory_chats = chats.get(chat_key, [])
    
    try:
        # Import here to avoid circular imports
        from app import db, app
        from models import Message, User
        from datetime import datetime
        
        # Use Flask application context
        with app.app_context():
            # Get user IDs from database
            user1 = db.session.query(User).filter_by(telegram_id=user1_id).first()
            user2 = db.session.query(User).filter_by(telegram_id=user2_id).first()
            
            if user1 and user2:
                # Get messages
                messages = db.session.query(Message).filter(
                    ((Message.sender_id == user1.id) & (Message.receiver_id == user2.id)) |
                    ((Message.sender_id == user2.id) & (Message.receiver_id == user1.id))
                ).order_by(Message.created_at).all()
                
                # Convert to dict format
                for msg in messages:
                    # Check if sender is user1 or user2
                    sender_telegram_id = user1_id if msg.sender_id == user1.id else user2_id
                    
                    # Convert datetime to timestamp
                    timestamp = msg.created_at.timestamp() if msg.created_at else time.time()
                    
                    # Add to in-memory chats if not already there
                    chat_msg = {
                        "sender_id": sender_telegram_id,
                        "timestamp": timestamp,
                        "text": msg.text
                    }
                    
                    # Simple check to avoid duplicates (not perfect but should work for most cases)
                    if not any(m["text"] == msg.text and abs(m["timestamp"] - timestamp) < 1 for m in in_memory_chats):
                        in_memory_chats.append(chat_msg)
                
                # Sort by timestamp
                in_memory_chats.sort(key=lambda m: m["timestamp"])
    except Exception as e:
        logger.error(f"Error retrieving chat history from database: {e}", exc_info=True)
    
    return in_memory_chats


def add_chat_message(sender_id: int, recipient_id: int, text: str) -> None:
    """Add a chat message between two users."""
    # Sort IDs to ensure consistent key for in-memory storage
    chat_key = tuple(sorted([sender_id, recipient_id]))
    
    if chat_key not in chats:
        chats[chat_key] = []
    
    # Add to in-memory storage
    chats[chat_key].append({
        "sender_id": sender_id,
        "timestamp": time.time(),
        "text": text
    })
    
    try:
        # Import here to avoid circular imports
        from app import db, app
        from models import Message, User
        
        # Use Flask application context
        with app.app_context():
            # Get user IDs from database
            sender = db.session.query(User).filter_by(telegram_id=sender_id).first()
            receiver = db.session.query(User).filter_by(telegram_id=recipient_id).first()
            
            if sender and receiver:
                # Create message
                message = Message(
                    sender_id=sender.id,
                    receiver_id=receiver.id,
                    text=text,
                    is_read=False
                )
                db.session.add(message)
                db.session.commit()
        
        logger.info(f"Message added to database between {sender_id} and {recipient_id}")
    except Exception as e:
        logger.error(f"Error saving chat message to database: {e}", exc_info=True)
    
    logger.info(f"Message added to in-memory chat between {sender_id} and {recipient_id}")


def block_user_from_db(user_id: int, blocked_id: int) -> None:
    """Block a user."""
    # Add to in-memory storage
    if user_id not in blocks:
        blocks[user_id] = set()
    
    blocks[user_id].add(blocked_id)
    
    # Remove from matches if exists
    if user_id in matches and blocked_id in matches[user_id]:
        matches[user_id].remove(blocked_id)
    
    if blocked_id in matches and user_id in matches[blocked_id]:
        matches[blocked_id].remove(user_id)
    
    try:
        # Import here to avoid circular imports
        from app import db, app
        from models import Block, User, Like
        
        # Use Flask application context
        with app.app_context():
            # Get user IDs from database
            blocker = db.session.query(User).filter_by(telegram_id=user_id).first()
            blocked = db.session.query(User).filter_by(telegram_id=blocked_id).first()
            
            if blocker and blocked:
                # Check if block already exists
                existing_block = db.session.query(Block).filter_by(
                    blocker_id=blocker.id, 
                    blocked_id=blocked.id
                ).first()
                
                if not existing_block:
                    # Create block
                    block = Block(
                        blocker_id=blocker.id,
                        blocked_id=blocked.id
                    )
                    db.session.add(block)
                
                # Remove from matches in database
                # Find all likes between these users and set is_match to False
                db.session.query(Like).filter(
                    ((Like.sender_id == blocker.id) & (Like.receiver_id == blocked.id)) |
                    ((Like.sender_id == blocked.id) & (Like.receiver_id == blocker.id))
                ).update({"is_match": False})
                
                # Commit changes
                db.session.commit()
        
        logger.info(f"User {user_id} blocked user {blocked_id} in database")
    except Exception as e:
        logger.error(f"Error saving block to database: {e}", exc_info=True)
    
    logger.info(f"User {user_id} blocked user {blocked_id} in memory")


def report_user_to_db(reporter_id: int, reported_id: int, reason: Optional[str] = None) -> None:
    """Report a user."""
    # Add to in-memory storage
    if reporter_id not in reports:
        reports[reporter_id] = []
    
    reports[reporter_id].append(reported_id)
    
    try:
        # Import here to avoid circular imports
        from app import db, app
        from models import Report, User
        
        # Use Flask application context
        with app.app_context():
            # Get user IDs from database
            reporter = db.session.query(User).filter_by(telegram_id=reporter_id).first()
            reported = db.session.query(User).filter_by(telegram_id=reported_id).first()
            
            if reporter and reported:
                # Create report
                report = Report(
                    reporter_id=reporter.id,
                    reported_id=reported.id,
                    reason=reason
                )
                db.session.add(report)
                db.session.commit()
        
        logger.info(f"User {reporter_id} reported user {reported_id} in database")
    except Exception as e:
        logger.error(f"Error saving report to database: {e}", exc_info=True)
    
    logger.info(f"User {reporter_id} reported user {reported_id} in memory")


def unmatch_user_from_db(user_id: int, unmatched_id: int) -> None:
    """Unmatch a user."""
    # Update in-memory storage
    if user_id in matches and unmatched_id in matches[user_id]:
        matches[user_id].remove(unmatched_id)
    
    if unmatched_id in matches and user_id in matches[unmatched_id]:
        matches[unmatched_id].remove(user_id)
    
    try:
        # Import here to avoid circular imports
        from app import db, app
        from models import Like, User
        
        # Use Flask application context
        with app.app_context():
            # Get user IDs from database
            user = db.session.query(User).filter_by(telegram_id=user_id).first()
            unmatched = db.session.query(User).filter_by(telegram_id=unmatched_id).first()
            
            if user and unmatched:
                # Find all likes between these users and set is_match to False
                db.session.query(Like).filter(
                    ((Like.sender_id == user.id) & (Like.receiver_id == unmatched.id)) |
                    ((Like.sender_id == unmatched.id) & (Like.receiver_id == user.id))
                ).update({"is_match": False})
                
                # Commit changes
                db.session.commit()
        
        logger.info(f"User {user_id} unmatched with user {unmatched_id} in database")
    except Exception as e:
        logger.error(f"Error unmatching in database: {e}", exc_info=True)
    
    logger.info(f"User {user_id} unmatched with user {unmatched_id} in memory")