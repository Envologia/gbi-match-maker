#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Web application runner for the GBI Match Maker
"""

from app import app  # Import the Flask app

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
