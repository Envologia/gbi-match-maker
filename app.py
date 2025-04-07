#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Web interface for GBI Match Maker
"""

import os
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


db = SQLAlchemy(model_class=Base)
# create the app
app = Flask(__name__)
# setup a secret key, required by sessions
app.secret_key = os.environ.get("SESSION_SECRET", "development_secret_key")
# configure the database, relative to the app instance folder
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL")
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}
# initialize the app with the extension, flask-sqlalchemy >= 3.0.x
db.init_app(app)

@app.route('/')
def home():
    """Home page route"""
    return render_template('index.html', title="GBI Match Maker")
    
@app.route('/about')
def about():
    """About page route"""
    return render_template('about.html', title="About")
    
@app.route('/status')
def status():
    """API status endpoint"""
    return jsonify({"status": "running"})

# Initialize database tables
with app.app_context():
    # Import models after app and db are created to avoid circular imports
    import models
    db.create_all()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)