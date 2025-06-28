#!/bin/bash
# SignalSlice Production Deployment Script

echo "🚀 Deploying SignalSlice..."

# Kill existing processes
echo "Stopping existing services..."
pkill -f gunicorn || true
pkill -f "python.*app.py" || true

# Install/update dependencies
echo "Installing dependencies..."
pip install -r requirements.txt
playwright install chromium

# Create required directories
mkdir -p logs data

# Start Gunicorn with eventlet worker for WebSocket support
echo "Starting Gunicorn with Socket.IO support..."
gunicorn --worker-class eventlet \
         --workers 1 \
         --bind 127.0.0.1:6003 \
         --timeout 120 \
         --keep-alive 5 \
         --log-file logs/gunicorn.log \
         --log-level info \
         --daemon \
         wsgi:app

echo "✅ SignalSlice deployed successfully!"
echo "📊 Check logs at: logs/gunicorn.log"
echo "🌐 Access at: https://signalslice.sebastianalexis.com"