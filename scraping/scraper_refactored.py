"""
Refactored SignalSlice Web Scraper
Modular approach to scraping Google Maps data
"""
import asyncio
import csv
import os
import re
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
from playwright.async_api import async_playwright, Page

from config import (
    TIMEZONE, RESTAURANT_URLS, GAY_BAR_URLS, SCRAPING_CONFIG,
    LIVE_TEXT_PATTERNS, LIVE_PERCENTAGE_SELECTORS, DATA_DIR,
    DATA_FILE_PATTERNS
)


class GoogleMapsScraper:
    """Handles Google Maps scraping operations"""
    
    def __init__(self):
        self.current_time = datetime.now(TIMEZONE)
        self.target_weekday, self.target_hour = self._calculate_target_time()
    
    def _calculate_target_time(self) -> Tuple[str, int]:
        """Calculate the target weekday and hour based on current time"""
        current_weekday = self.current_time.strftime('%A')
        current_hour_24 = self.current_time.hour
        
        # Adjust for Google Maps' day structure: 12 AM belongs to previous day
        if current_hour_24 == 0:
            target_weekday = (self.current_time - timedelta(days=1)).strftime('%A')
            target_hour = 24
            print(f"🕐 Current EST time: {self.current_time.strftime('%A %I:%M %p')} (Hour {current_hour_24})")
            print(f"📅 Looking for PREVIOUS day's ({target_weekday}) data at hour 24 (12 AM)")
            print(f"🔍 Logic: 12 AM on {current_weekday} = Hour 24 of {target_weekday}")
        else:
            target_weekday = current_weekday
            target_hour = current_hour_24
            print(f"🕐 Current EST time: {self.current_time.strftime('%A %I:%M %p')} (Hour {current_hour_24})")
            print(f"📅 Looking for TODAY's ({target_weekday}) data at hour {target_hour}")
        
        print(f"🎯 Priority: LIVE data > Historical data > No data")
        return target_weekday, target_hour
    
    async def scrape_all_venues(self) -> List[Dict[str, Any]]:
        """Main entry point to scrape all venues"""
        results = []
        all_scraped_data = []
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=SCRAPING_CONFIG['headless'])
            page = await browser.new_page()
            
            # Prepare all URLs with venue types
            all_urls = []
            for url in RESTAURANT_URLS:
                all_urls.append((url, "restaurant"))
            for url in GAY_BAR_URLS:
                all_urls.append((url, "gay_bar"))
            
            # Scrape each venue
            for url, venue_type in all_urls:
                try:
                    venue_data = await self._scrape_venue(page, url, venue_type)
                    results.append(venue_data['final_data'])
                    
                    if venue_data.get('all_time_data'):
                        all_scraped_data.extend(venue_data['all_time_data'])
                        
                except Exception as e:
                    print(f"❌ Error scraping {url}: {e}")
                
                await asyncio.sleep(SCRAPING_CONFIG['delay_between_urls'])
            
            await browser.close()
        
        # Save scraped data
        self._save_scraped_data(all_scraped_data)
        self._save_current_hour_data(results)
        
        return results
    
    async def _scrape_venue(self, page: Page, url: str, venue_type: str) -> Dict[str, Any]:
        """Scrape a single venue"""
        print(f"\n🔍 Checking current hour for: {url} (Type: {venue_type})")
        
        await page.goto(url, timeout=SCRAPING_CONFIG['page_timeout'])
        await page.wait_for_timeout(SCRAPING_CONFIG['page_settle_time'])
        
        # Try to get live data first
        live_data = await self._extract_live_data(page, url, venue_type)
        
        # If no live data, get historical data
        historical_data = None
        all_time_data = []
        
        if not live_data:
            historical_result = await self._extract_historical_data(page, url, venue_type)
            historical_data = historical_result['target_data']
            all_time_data = historical_result['all_data']
        
        # Determine final data
        final_data = self._determine_final_data(live_data, historical_data, url, venue_type)
        
        return {
            'final_data': final_data,
            'all_time_data': all_time_data
        }
    
    async def _extract_live_data(self, page: Page, url: str, venue_type: str) -> Optional[Dict[str, Any]]:
        """Extract live data from the page"""
        print(f"  🔴 Step 1: Searching for LIVE data...")
        
        # Check for live text indicators
        live_text_indicator = await self._check_live_text_indicators(page)
        
        # Check for live percentage data
        live_percentage_data = await self._check_live_percentages(page)
        
        if live_percentage_data:
            return self._format_live_data(live_percentage_data, url, venue_type, "percentage")
        elif live_text_indicator:
            return self._format_live_data(live_text_indicator, url, venue_type, "text")
        
        return None
    
    async def _check_live_text_indicators(self, page: Page) -> Optional[Dict[str, Any]]:
        """Check for live text indicators on the page"""
        page_text = await page.evaluate('document.body.innerText')
        print(f"    📝 Scanning page text for live indicators...")
        
        for pattern, info in LIVE_TEXT_PATTERNS.items():
            if re.search(pattern, page_text, re.IGNORECASE):
                flag_emoji = "🚨" if info["flag"] else "✅"
                print(f"    {flag_emoji} FOUND LIVE TEXT: '{pattern}' (Flag: {info['flag']}, Confidence: {info['confidence']})")
                
                return {
                    "text": pattern,
                    "flag": info["flag"],
                    "confidence": info["confidence"],
                    "estimated_percentage": info["estimated_percentage"]
                }
        
        return None
    
    async def _check_live_percentages(self, page: Page) -> Optional[Dict[str, Any]]:
        """Check for live percentage data on the page"""
        for selector in LIVE_PERCENTAGE_SELECTORS:
            try:
                elements = await page.query_selector_all(selector)
                print(f"    📊 Checking selector '{selector}': found {len(elements)} elements")
                
                for el in elements:
                    aria = await el.get_attribute('aria-label')
                    if not aria:
                        continue
                    
                    print(f"      Examining: {aria}")
                    
                    # Look for live data patterns (busyness % without time reference)
                    if re.search(r"\d+% busy", aria, re.IGNORECASE) and "at" not in aria.lower():
                        percent_match = re.search(r"(\d+)%", aria)
                        if percent_match:
                            live_percentage = int(percent_match.group(1))
                            print(f"      🔴 FOUND LIVE PERCENTAGE: {live_percentage}% busy right now!")
                            return {
                                "percentage": live_percentage,
                                "aria_label": aria
                            }
            except Exception as e:
                print(f"        Error with selector {selector}: {e}")
        
        return None
    
    def _format_live_data(self, data: Dict[str, Any], url: str, venue_type: str, data_source: str) -> Dict[str, Any]:
        """Format live data into standard structure"""
        current_hour_24 = self.current_time.hour
        hour_label = f"{current_hour_24 % 12 or 12} {'AM' if current_hour_24 < 12 else 'PM'}"
        
        if data_source == "percentage":
            return {
                "restaurant_url": url,
                "weekday": self.target_weekday,
                "hour_24": current_hour_24,
                "hour_label": hour_label,
                "timestamp": self.current_time.isoformat(),
                "value": f"{data['aria_label']} (LIVE DATA - {self.current_time.strftime('%I:%M %p')})",
                "busyness_percent": data['percentage'],
                "data_type": "LIVE",
                "venue_type": venue_type
            }
        else:  # text indicator
            return {
                "restaurant_url": url,
                "weekday": self.target_weekday,
                "hour_24": current_hour_24,
                "hour_label": hour_label,
                "timestamp": self.current_time.isoformat(),
                "value": f"Live text indicator: '{data['text']}' (LIVE DATA - {self.current_time.strftime('%I:%M %p')})",
                "busyness_percent": data["estimated_percentage"],
                "data_type": "LIVE",
                "live_flag": data["flag"],
                "confidence": data["confidence"],
                "venue_type": venue_type
            }
    
    async def _extract_historical_data(self, page: Page, url: str, venue_type: str) -> Dict[str, Any]:
        """Extract historical data from the page"""
        print(f"  📊 Step 2: No live data found, using historical data...")
        
        elements = await page.query_selector_all('div[aria-label*="Popular times"] [aria-label*="at"]')
        print(f"  📊 Found {len(elements)} total time elements")
        
        all_time_data = []
        
        for i, el in enumerate(elements):
            aria = await el.get_attribute('aria-label')
            if not aria or not re.search(r"\d+% busy", aria):
                continue
            
            time_data = self._parse_time_element(aria, i, url)
            if time_data:
                all_time_data.append(time_data)
        
        # Detect day cycles and find target data
        target_data = None
        if all_time_data:
            day_cycles = self._detect_day_cycles(all_time_data)
            target_data = self._find_target_historical_data(day_cycles, url, venue_type)
        
        return {
            'target_data': target_data,
            'all_data': all_time_data
        }
    
    def _parse_time_element(self, aria_label: str, index: int, url: str) -> Optional[Dict[str, Any]]:
        """Parse a time element from aria-label"""
        time_match = re.search(r"at (\d{1,2})\u202f(AM|PM)\.?", aria_label)
        if not time_match:
            time_match = re.search(r"at (\d{1,2}) (AM|PM)\.?", aria_label)
        
        if not time_match:
            return None
        
        hour_12 = int(time_match.group(1))
        meridiem = time_match.group(2)
        
        # Convert to 24-hour format
        if meridiem == "AM":
            hour_24 = hour_12 if hour_12 != 12 else 0
        else:
            hour_24 = hour_12 if hour_12 == 12 else hour_12 + 12
        
        display_hour = 24 if hour_24 == 0 else hour_24
        percent_match = re.search(r"(\d+)%", aria_label)
        busyness_percent = int(percent_match.group(1)) if percent_match else None
        
        return {
            "scrape_timestamp": self.current_time.isoformat(),
            "restaurant_url": url,
            "element_index": index,
            "hour_24": hour_24,
            "display_hour": display_hour,
            "hour_12": hour_12,
            "meridiem": meridiem,
            "hour_label": f"{hour_12} {meridiem}",
            "busyness_percent": busyness_percent,
            "raw_aria_label": aria_label,
            "is_target_hour": display_hour == self.target_hour,
            "target_weekday": self.target_weekday,
            "target_hour": self.target_hour
        }
    
    def _detect_day_cycles(self, all_time_data: List[Dict[str, Any]]) -> List[List[Dict[str, Any]]]:
        """Detect day cycles from time data"""
        hour_sequence = [d["display_hour"] for d in all_time_data]
        print(f"  📋 Raw hour sequence: {hour_sequence}")
        
        day_cycles = []
        current_cycle = []
        
        print(f"  🔄 Analyzing hour cycles to detect days...")
        print(f"     Looking for 6 AM to mark new day boundaries...")
        
        for data in all_time_data:
            hour = data["hour_24"]
            
            # If we see hour 6 (6 AM) and we already have data, start a new cycle
            if hour == 6 and current_cycle:
                print(f"    📅 Day boundary detected at element {data['element_index']} (6 AM)")
                print(f"       Previous cycle had {len(current_cycle)} hours: {[d['display_hour'] for d in current_cycle]}")
                day_cycles.append(current_cycle)
                current_cycle = []
            
            current_cycle.append(data)
        
        # Add the last cycle
        if current_cycle:
            print(f"    📅 Final cycle has {len(current_cycle)} hours: {[d['display_hour'] for d in current_cycle]}")
            day_cycles.append(current_cycle)
        
        print(f"  📊 Detected {len(day_cycles)} day cycles total")
        
        # Assign day names to cycles
        self._assign_day_names_to_cycles(day_cycles)
        
        return day_cycles
    
    def _assign_day_names_to_cycles(self, day_cycles: List[List[Dict[str, Any]]]) -> None:
        """Assign day names to detected cycles"""
        print(f"  📅 Assigning day names to cycles...")
        print(f"     Current day: {self.current_time.strftime('%A')}")
        print(f"     Target day for search: {self.target_weekday}")
        
        weekdays = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        current_day_index = weekdays.index(self.current_time.strftime('%A'))
        
        for cycle_idx, cycle in enumerate(day_cycles):
            # Calculate the day offset from today
            day_offset = cycle_idx
            actual_day_index = (current_day_index + day_offset) % 7
            assigned_weekday = weekdays[actual_day_index]
            
            cycle_hours = sorted(set(d["display_hour"] for d in cycle))
            
            for data in cycle:
                data["detected_cycle"] = cycle_idx
                data["cycle_hours_count"] = len(cycle_hours)
                data["cycle_start_hour"] = min(cycle_hours) if cycle_hours else None
                data["cycle_end_hour"] = max(cycle_hours) if cycle_hours else None
                data["assigned_weekday"] = assigned_weekday
                data["day_offset"] = day_offset
                data["is_today_cycle"] = cycle_idx == 0
            
            print(f"    Cycle {cycle_idx} = {assigned_weekday} (today + {day_offset} days)")
            print(f"       Hours: {cycle_hours}")
    
    def _find_target_historical_data(self, day_cycles: List[List[Dict[str, Any]]], url: str, venue_type: str) -> Optional[Dict[str, Any]]:
        """Find target historical data from day cycles"""
        for cycle_idx, cycle in enumerate(day_cycles):
            if cycle and cycle[0].get("assigned_weekday") == self.target_weekday:
                print(f"    ✅ Found target day cycle {cycle_idx} ({self.target_weekday})")
                
                for data in cycle:
                    if data["display_hour"] == self.target_hour:
                        return {
                            "restaurant_url": url,
                            "weekday": self.target_weekday,
                            "hour_24": self.current_time.hour,
                            "hour_label": f"{data['hour_12']} {data['meridiem']}",
                            "timestamp": self.current_time.isoformat(),
                            "value": data["raw_aria_label"] + f" (HISTORICAL - Cycle {cycle_idx})",
                            "busyness_percent": data["busyness_percent"],
                            "data_type": "HISTORICAL",
                            "venue_type": venue_type
                        }
        
        return None
    
    def _determine_final_data(self, live_data: Optional[Dict[str, Any]], historical_data: Optional[Dict[str, Any]], 
                             url: str, venue_type: str) -> Dict[str, Any]:
        """Determine the final data to use"""
        if live_data:
            live_flag = live_data.get("live_flag", "N/A")
            print(f"  ✅ Using LIVE data: {live_data['busyness_percent']}% (Flag: {live_flag})")
            return live_data
        elif historical_data:
            print(f"  ✅ Using HISTORICAL data: {historical_data['busyness_percent']}% (fallback)")
            return historical_data
        else:
            print(f"  ❌ No data available for {self.target_weekday} at hour {self.target_hour}")
            return {
                "restaurant_url": url,
                "weekday": self.target_weekday,
                "hour_24": self.current_time.hour,
                "hour_label": f"{self.current_time.hour % 12 or 12} {'AM' if self.current_time.hour < 12 else 'PM'}",
                "timestamp": self.current_time.isoformat(),
                "value": f"No data available for {self.target_weekday} at hour {self.target_hour}",
                "busyness_percent": None,
                "data_type": "NO_DATA",
                "venue_type": venue_type
            }
    
    def _save_scraped_data(self, all_scraped_data: List[Dict[str, Any]]) -> None:
        """Save all scraped data to CSV"""
        if not all_scraped_data:
            return
        
        timestamp = self.current_time.strftime('%Y%m%d_%H%M%S')
        scraped_data_file = os.path.join(DATA_DIR, DATA_FILE_PATTERNS['scraped_data'].format(timestamp=timestamp))
        
        os.makedirs(DATA_DIR, exist_ok=True)
        
        fieldnames = [
            "scrape_timestamp", "restaurant_url", "element_index", "hour_24", "display_hour",
            "hour_12", "meridiem", "hour_label", "busyness_percent", "raw_aria_label",
            "is_target_hour", "target_weekday", "target_hour", "detected_cycle",
            "cycle_hours_count", "cycle_start_hour", "cycle_end_hour", "assigned_weekday",
            "day_offset", "is_today_cycle"
        ]
        
        with open(scraped_data_file, "w", newline='', encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for data in all_scraped_data:
                # Fill in missing fields with default values
                for field in fieldnames:
                    if field not in data:
                        data[field] = None
                writer.writerow(data)
        
        print(f"📊 All scraped data saved to {scraped_data_file}")
    
    def _save_current_hour_data(self, results: List[Dict[str, Any]]) -> None:
        """Save current hour results"""
        timestamp = self.current_time.strftime('%Y%m%d_%H')
        current_hour_file = os.path.join(DATA_DIR, DATA_FILE_PATTERNS['current_hour'].format(timestamp=timestamp))
        
        os.makedirs(DATA_DIR, exist_ok=True)
        
        fieldnames = ["restaurant_url", "weekday", "hour_24", "hour_label", "timestamp", 
                     "value", "busyness_percent", "data_type", "venue_type"]
        
        with open(current_hour_file, "w", newline='', encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(results)
        
        print(f"✅ Current hour data saved to {current_hour_file}")


# Backward compatibility function
async def scrape_current_hour() -> List[Dict[str, Any]]:
    """Backward compatible wrapper for the refactored scraper"""
    scraper = GoogleMapsScraper()
    return await scraper.scrape_all_venues()