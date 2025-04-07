#!/usr/bin/env python
# -*- coding: utf-8 -*-

from app import app, db
from models import User, Like, SecretCrush, Block, Report, Message, TargetUniversity

def check_database():
    with app.app_context():
        print(f"Users in DB: {db.session.query(User).count()}")
        print(f"Target Universities in DB: {db.session.query(TargetUniversity).count()}")
        print(f"Likes in DB: {db.session.query(Like).count()}")
        print(f"Secret Crushes in DB: {db.session.query(SecretCrush).count()}")
        print(f"Blocks in DB: {db.session.query(Block).count()}")
        print(f"Reports in DB: {db.session.query(Report).count()}")
        print(f"Messages in DB: {db.session.query(Message).count()}")
        
        # Print users details if any exist
        users = db.session.query(User).all()
        for user in users:
            print(f"\nUser: {user.telegram_id}, Name: {user.name}, Age: {user.age}")
            print(f"Gender: {user.gender}, University: {user.university}")
            print(f"Target Universities: {[tu.university_name for tu in user.target_universities]}")

if __name__ == "__main__":
    check_database()