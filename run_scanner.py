#!/usr/bin/env python3
"""
SignalSlice Real-time Scanner
Runs continuous hourly monitoring of pizza activity around the Pentagon
"""
import asyncio
import sys
import os
import logging
# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)
# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from scheduler import main
if __name__ == "__main__":
    logger.info("🛰️ SignalSlice Real-time Scanner")
    logger.info("Press Ctrl+C to stop")
    logger.info("-" * 50)
    try:
        asyncio.run(main())  # Starts the scheduler
    except KeyboardInterrupt:
        logger.info("\n🛑 Scanner stopped. Stay vigilant! 🍕")
    except Exception as e:
        logger.error(f"\n❌ Fatal error: {e}", exc_info=True)
        sys.exit(1)









































