#!/usr/bin/env python3
"""
WSGI entry point for production deployment with Gunicorn
"""
from app import app, socketio

# For Gunicorn with eventlet worker, we need to expose the app directly
# The socketio instance is already attached to the app
application = app

if __name__ == "__main__":
    socketio.run(app)