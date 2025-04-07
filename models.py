#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Database models for the GBI Match Maker
"""

import os
from datetime import datetime
from sqlalchemy import Column, Integer, BigInteger, String, Text, DateTime, Boolean, ForeignKey, Table
from sqlalchemy.orm import relationship

from app import db

# User model
class User(db.Model):
    """User model for storing user profile data"""
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    telegram_id = Column(BigInteger, unique=True, nullable=False)
    name = Column(String(100), nullable=False)
    age = Column(Integer, nullable=False)
    gender = Column(String(20), nullable=False)  # 'male' or 'female'
    university = Column(String(100), nullable=False)
    bio = Column(Text, nullable=True)
    hobbies = Column(Text, nullable=True)
    relationship_preference = Column(String(50), nullable=True)  # 'serious', 'casual', etc.
    profile_pic_url = Column(String(255), nullable=True)
    profile_pic = Column(Text, nullable=True)  # Storing image as hex encoded string
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    target_universities = relationship("TargetUniversity", back_populates="user")
    sent_likes = relationship("Like", foreign_keys="Like.sender_id", back_populates="sender")
    received_likes = relationship("Like", foreign_keys="Like.receiver_id", back_populates="receiver")
    sent_messages = relationship("Message", foreign_keys="Message.sender_id", back_populates="sender")
    received_messages = relationship("Message", foreign_keys="Message.receiver_id", back_populates="receiver")
    sent_crushes = relationship("SecretCrush", foreign_keys="SecretCrush.crusher_id", back_populates="crusher")
    received_crushes = relationship("SecretCrush", foreign_keys="SecretCrush.crushee_id", back_populates="crushee")
    blocks_sent = relationship("Block", foreign_keys="Block.blocker_id", back_populates="blocker")
    blocks_received = relationship("Block", foreign_keys="Block.blocked_id", back_populates="blocked")
    reports_sent = relationship("Report", foreign_keys="Report.reporter_id", back_populates="reporter")
    reports_received = relationship("Report", foreign_keys="Report.reported_id", back_populates="reported")

# Target Universities model
class TargetUniversity(db.Model):
    """Model for storing user's target universities preferences"""
    __tablename__ = 'target_universities'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    university_name = Column(String(100), nullable=False)
    user = relationship("User", back_populates="target_universities")

# Matches (Likes) model
class Like(db.Model):
    """Model for storing likes between users"""
    __tablename__ = 'likes'
    
    id = Column(Integer, primary_key=True)
    sender_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    receiver_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    is_match = Column(Boolean, default=False)  # True when mutual like exists
    created_at = Column(DateTime, default=datetime.utcnow)
    
    sender = relationship("User", foreign_keys=[sender_id], back_populates="sent_likes")
    receiver = relationship("User", foreign_keys=[receiver_id], back_populates="received_likes")

# Messages model
class Message(db.Model):
    """Model for storing messages between matched users"""
    __tablename__ = 'messages'
    
    id = Column(Integer, primary_key=True)
    sender_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    receiver_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    text = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    is_read = Column(Boolean, default=False)
    
    sender = relationship("User", foreign_keys=[sender_id], back_populates="sent_messages")
    receiver = relationship("User", foreign_keys=[receiver_id], back_populates="received_messages")

# Secret Crush model
class SecretCrush(db.Model):
    """Model for storing secret crushes between users"""
    __tablename__ = 'secret_crushes'
    
    id = Column(Integer, primary_key=True)
    crusher_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    crushee_id = Column(Integer, ForeignKey('users.id'), nullable=True)  # Can be null for external crushes
    crush_name = Column(String(100), nullable=True)  # Name of the crush if not a user
    social_media_account = Column(String(100), nullable=True)  # Instagram or Telegram handle
    crush_photo = Column(Text, nullable=True)  # Photo stored as hex encoded string
    is_mutual = Column(Boolean, default=False)  # True when mutual crush exists
    created_at = Column(DateTime, default=datetime.utcnow)
    
    crusher = relationship("User", foreign_keys=[crusher_id], back_populates="sent_crushes")
    crushee = relationship("User", foreign_keys=[crushee_id], back_populates="received_crushes")

# Block model
class Block(db.Model):
    """Model for storing blocked users"""
    __tablename__ = 'blocks'
    
    id = Column(Integer, primary_key=True)
    blocker_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    blocked_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    blocker = relationship("User", foreign_keys=[blocker_id], back_populates="blocks_sent")
    blocked = relationship("User", foreign_keys=[blocked_id], back_populates="blocks_received")

# Report model
class Report(db.Model):
    """Model for storing user reports"""
    __tablename__ = 'reports'
    
    id = Column(Integer, primary_key=True)
    reporter_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    reported_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    reason = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    reporter = relationship("User", foreign_keys=[reporter_id], back_populates="reports_sent")
    reported = relationship("User", foreign_keys=[reported_id], back_populates="reports_received")