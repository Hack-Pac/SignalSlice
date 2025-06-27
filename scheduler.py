import asyncio
import time
import logging
import os
import sys
from datetime import datetime, timedelta
import pytz
from scraping.gmapsScrape import scrape_current_hour
from script.anomalyDetect import check_current_anomalies
import re
import requests
import threading

# Configure logging with UTF-8 encoding
def setup_logging():
    """Setup logging with UTF-8 encoding to support emojis"""
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)
    
    # Remove existing handlers
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    
    # Create console handler with UTF-8 encoding
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    
    # Set UTF-8 encoding if possible
    if hasattr(console_handler.stream, 'reconfigure'):
        console_handler.stream.reconfigure(encoding='utf-8')
    
    # Create formatter
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    console_handler.setFormatter(formatter)
    
    logger.addHandler(console_handler)
    return logger
# Initialize logger with UTF-8 support
logger = setup_logging()

# EST timezone
EST = pytz.timezone('US/Eastern')

def get_next_hour_start():
    """Calculate seconds until the next hour starts"""
    now = datetime.now(EST)
    next_hour = (now + timedelta(hours=1)).replace(minute=0, second=0, microsecond=0)
    return (next_hour - now).total_seconds()

def clean_log_message(message):
    """Remove emojis from log messages for Windows compatibility"""
    # Remove emojis and other problematic Unicode characters
    emoji_pattern = re.compile("["
                              u"\U0001F600-\U0001F64F"  # emoticons
                              u"\U0001F300-\U0001F5FF"  # symbols & pictographs
                              u"\U0001F680-\U0001F6FF"  # transport & map symbols
                              u"\U0001F1E0-\U0001F1FF"  # flags (iOS)
                              u"\U00002702-\U000027B0"
                              u"\U000024C2-\U0001F251"
                              "]+", flags=re.UNICODE)
    return emoji_pattern.sub('', message).strip()

async def hourly_scan():
    """Perform one complete scan cycle"""
    try:
        current_time = datetime.now(EST)
        print(f"🕐 Starting hourly scan at {current_time.strftime('%Y-%m-%d %H:%M:%S EST')}")
        logger.info(clean_log_message(f"Starting hourly scan at {current_time.strftime('%Y-%m-%d %H:%M:%S EST')}"))
        
        # Step 1: Scrape current hour data
        logger.info("📡 Scraping current hour data...")
        await scrape_current_hour()
        
        # Step 2: Check for anomalies
        logger.info("🔍 Checking for anomalies...")
        anomalies_found = check_current_anomalies()
        
        if anomalies_found:
            logger.warning("🚨 ANOMALIES DETECTED! Check the output above.")
        else:
            logger.info("✅ No anomalies detected this hour.")
            
        logger.info(f"✅ Scan completed at {datetime.now(EST).strftime('%H:%M:%S EST')}")
        
    except Exception as e:
        logger.error(f"❌ Error during hourly scan: {e}")

async def main():
    """Main scheduler loop"""
    logger.info("🛰️ SignalSlice Scanner Starting...")
    logger.info("🔄 Running initial scan, then switching to hourly schedule")
    
    # Run initial scan
    await hourly_scan()
    
    while True:
        try:
            # Calculate time until next hour
            sleep_seconds = get_next_hour_start()
            next_run = datetime.now(EST) + timedelta(seconds=sleep_seconds)
            
            logger.info(f"⏰ Next scan scheduled for {next_run.strftime('%H:%M:%S EST')} ({sleep_seconds/60:.1f} minutes)")
            
            # Sleep until next hour (with small buffer to ensure we're past the hour mark)
            await asyncio.sleep(sleep_seconds + 30)
            
            # Run the scan
            await hourly_scan()
            
        except KeyboardInterrupt:
            logger.info("🛑 Scheduler stopped by user")
            break
        except Exception as e:
            logger.error(f"❌ Unexpected error in main loop: {e}")
            # Wait 5 minutes before retrying to avoid rapid failures
            await asyncio.sleep(300)

if __name__ == "__main__":
    asyncio.run(main())










