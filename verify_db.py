from app import db, app
from models import User
import json

with app.app_context():
    users = db.session.query(User).all()
    print('Number of users:', len(users))
    if users and len(users) > 0:
        user_data = {}
        for c in User.__table__.columns:
            value = getattr(users[0], c.name)
            if isinstance(value, bytes) or str(type(value)).startswith('<class'):
                user_data[c.name] = str(type(value))
            else:
                user_data[c.name] = value
        print('First user columns:', json.dumps(user_data))
    else:
        print('No users')