#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Script to recreate database tables with updated schema
"""

import os
from app import app, db
import models  # Import all models

def recreate_tables():
    """Drop all tables and recreate them"""
    with app.app_context():
        print("Dropping all tables...")
        db.drop_all()
        
        print("Creating all tables with updated schema...")
        db.create_all()
        
        print("Database tables recreated successfully!")

if __name__ == "__main__":
    recreate_tables()