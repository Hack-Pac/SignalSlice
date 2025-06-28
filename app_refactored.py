#!/usr/bin/env python3
"""
SignalSlice Web Application - Refactored Version
Real-time dashboard for Pentagon Pizza Index monitoring
"""
import asyncio
import threading
from datetime import datetime
from flask import Flask, render_template, jsonify, request
from flask_socketio import SocketIO, emit

from config import (
    FLASK_SECRET_KEY, FLASK_HOST, FLASK_PORT, FLASK_DEBUG,
    SOCKETIO_CONFIG, TIMEZONE
)
from state_manager import state_manager
from services.scanner_service import ScannerService


# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = FLASK_SECRET_KEY
socketio = SocketIO(app, **SOCKETIO_CONFIG)

# Initialize scanner service
scanner_service = ScannerService(socketio)


# WebSocket event handlers
@socketio.on('connect')
def handle_connect():
    """Handle client connection"""
    print(f"🔗 Client connected: {request.sid}")
    
    # Get current state
    current_state = state_manager.get_state()
    
    # Format for client
    initial_state = {
        'pizza_index': current_state.get('pizza_index', 0),
        'gay_bar_index': current_state.get('gay_bar_index', 0),
        'active_locations': current_state.get('active_locations', 0),
        'scan_count': current_state.get('scan_count', 0),
        'anomaly_count': current_state.get('anomaly_count', 0),
        'last_scan_time': current_state['last_scan_time'].strftime('%H:%M:%S') if current_state.get('last_scan_time') else 'Never',
        'activity_feed': current_state.get('activity_feed', []),
        'scanner_running': current_state.get('scanner_running', False)
    }
    
    print(f"DEBUG: Sending initial_state: {initial_state}")
    emit('initial_state', initial_state)
    
    scanner_service.add_activity('CONNECT', f'Dashboard client connected ({request.sid[:8]})', 'normal')


@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection"""
    print(f"🔌 Client disconnected: {request.sid}")
    scanner_service.add_activity('DISCONNECT', f'Dashboard client disconnected ({request.sid[:8]})', 'normal')


@socketio.on('manual_scan')
def handle_manual_scan():
    """Handle manual scan request from client"""
    def run_async_scan():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(scanner_service.run_manual_scan())
        loop.close()
    
    threading.Thread(target=run_async_scan).start()


# Flask routes
@app.route('/')
def index():
    """Serve the main dashboard"""
    return render_template('index.html')


@app.route('/api/status')
def get_status():
    """API endpoint to get current status"""
    current_state = state_manager.get_state()
    
    return jsonify({
        'pizza_index': current_state.get('pizza_index', 0),
        'gay_bar_index': current_state.get('gay_bar_index', 0),
        'active_locations': current_state.get('active_locations', 0),
        'scan_count': current_state.get('scan_count', 0),
        'anomaly_count': current_state.get('anomaly_count', 0),
        'last_scan_time': current_state['last_scan_time'].isoformat() if current_state.get('last_scan_time') else None,
        'scanning': current_state.get('scanning', False),
        'scanner_running': current_state.get('scanner_running', False),
        'activity_feed': current_state.get('activity_feed', [])
    })


@app.route('/api/activity_feed')
def get_activity_feed():
    """API endpoint to get current activity feed"""
    return jsonify({
        'activity_feed': state_manager.get('activity_feed', []),
        'timestamp': datetime.now(TIMEZONE).isoformat()
    })


@app.route('/api/trigger_scan')
def trigger_manual_scan():
    """Trigger a manual scan"""
    def run_async_scan():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(scanner_service.run_manual_scan())
        loop.close()
    
    # Run in separate thread to avoid blocking
    threading.Thread(target=run_async_scan).start()
    
    return jsonify({'status': 'scan_triggered'})


@app.route('/api/start_scanner')
def start_scanner_endpoint():
    """Start the automated scanner"""
    if not state_manager.get('scanner_running', False):
        scanner_service.start()
        return jsonify({'status': 'scanner_started'})
    else:
        return jsonify({'status': 'scanner_already_running'})


@app.route('/api/stop_scanner')
def stop_scanner_endpoint():
    """Stop the automated scanner"""
    if state_manager.get('scanner_running', False):
        scanner_service.stop()
        return jsonify({'status': 'scanner_stopped'})
    else:
        return jsonify({'status': 'scanner_not_running'})


# Initialize application
def initialize_app():
    """Initialize the application with default state"""
    scanner_service.add_activity('INIT', 'SignalSlice dashboard initialized', 'normal')
    scanner_service.add_activity('SYSTEM', 'Monitoring 127 pizza locations in 50-mile radius', 'normal')
    scanner_service.add_activity('GAYBAR', '🏳️‍🌈 Gay Bar Index monitoring active', 'normal')


def main():
    """Main entry point"""
    print("🛰️ SignalSlice Dashboard Starting...")
    print("🌐 Access the dashboard at: http://localhost:5000")
    print("📡 Real-time data will appear when scanner runs")
    
    # Initialize app
    initialize_app()
    
    # Start the scanner automatically
    scanner_service.start()
    
    try:
        socketio.run(app, debug=FLASK_DEBUG, host=FLASK_HOST, port=FLASK_PORT, allow_unsafe_werkzeug=True)
    except KeyboardInterrupt:
        print("\n🛑 Shutting down...")
        scanner_service.stop()
        print("SignalSlice stopped. Stay vigilant! 🍕")


if __name__ == '__main__':
    main()