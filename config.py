"""
SignalSlice Configuration Module
Centralizes all configuration settings for the application
"""
import os
import pytz
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Flask Configuration
FLASK_SECRET_KEY = os.getenv('FLASK_SECRET_KEY', 'signalslice-pizza-monitor-2024')
FLASK_HOST = os.getenv('FLASK_HOST', '0.0.0.0')
FLASK_PORT = int(os.getenv('FLASK_PORT', 5000))
FLASK_DEBUG = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'

# Timezone Configuration
TIMEZONE = pytz.timezone('US/Eastern')

# Scanner Configuration
SCANNER_INITIAL_DELAY = 30  # seconds before first scan
SCANNER_RETRY_DELAY = 300   # 5 minutes retry delay on error
SCANNER_HOUR_BUFFER = 30    # seconds buffer after hour mark

# Dashboard Configuration
DASHBOARD_DEFAULTS = {
    'pizza_index': 3.42,
    'gay_bar_index': 6.58,
    'active_locations': 127,
    'scan_count': 0,
    'anomaly_count': 0,
    'last_scan_time': None,
    'scanning': False,
    'activity_feed': [],
    'scanner_running': False
}

# Activity Feed Configuration
MAX_ACTIVITY_FEED_ITEMS = 10

# Index Calculation Configuration
INDEX_CONFIG = {
    'pizza': {
        'min': 0,
        'max': 10,
        'normal_adjustment': 0.5,  # Max adjustment for normal scans
        'anomaly_boost': 1.5       # Boost when anomaly detected
    },
    'gay_bar': {
        'min': 0,
        'max': 10,
        'inverse': True  # Higher busyness = lower index
    }
}

# Scraping Configuration
SCRAPING_CONFIG = {
    'headless': True,
    'page_timeout': 60000,  # milliseconds
    'page_settle_time': 4000,  # milliseconds
    'delay_between_urls': 2,  # seconds
    'random_delay_range': (5, 10),  # seconds
    'max_time_entries': 140,  # Max 7 days × 20 hours
    'start_hour': 6,
    'hours_per_day': 20
}

# Data Storage Configuration
DATA_DIR = 'data'
DATA_FILE_PATTERNS = {
    'scraped_data': 'all_scraped_data_{timestamp}.csv',
    'current_hour': 'current_hour_{timestamp}.csv'
}

# Venue URLs Configuration
RESTAURANT_URLS = [
    "https://maps.app.goo.gl/KqSr8hH5GV4ZGJP27",
    # Add more restaurant URLs here
]

GAY_BAR_URLS = [
    "https://maps.app.goo.gl/PKRdT6pYjJ4uKEUJA",
    # Add more gay bar URLs here
]

# Live Data Detection Patterns
LIVE_TEXT_PATTERNS = {
    r"busier than usual": {"flag": True, "confidence": "HIGH", "estimated_percentage": 75},
    r"as busy as it gets": {"flag": True, "confidence": "MAXIMUM", "estimated_percentage": 100},
    r"not busy": {"flag": False, "confidence": "LOW", "estimated_percentage": 10},
    r"not too busy": {"flag": False, "confidence": "LOW", "estimated_percentage": 15},
    r"usually not busy": {"flag": False, "confidence": "LOW", "estimated_percentage": 15},
}

LIVE_PERCENTAGE_SELECTORS = [
    '[aria-label*="% busy"], [aria-label*="% Busy"]',
    '[aria-label*="right now"], [aria-label*="Right now"]',
    '[aria-label*="currently"], [aria-label*="Currently"]',
]

# Logging Configuration
LOGGING_CONFIG = {
    'level': 'INFO',
    'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    'datefmt': '%Y-%m-%d %H:%M:%S'
}

# WebSocket Configuration
SOCKETIO_CONFIG = {
    'cors_allowed_origins': "*",
    'async_mode': 'threading'
}