"""
Adapter module to bridge the refactored scraper with the existing codebase
"""
import sys
from pathlib import Path

# Add parent directory to path to allow imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from scraping.scraper_refactored import scrape_current_hour as scrape_current_hour_refactored

# Export the refactored function with the same name
scrape_current_hour = scrape_current_hour_refactored