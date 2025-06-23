import asyncio
import csv
import random
import time
import re
import os
from playwright.async_api import async_playwright
import pytz
from datetime import datetime

RESTAURANT_URLS = [
    "https://maps.app.goo.gl/KqSr8hH5GV4ZGJP27",
    # Add more URLs here
]

OUTPUT_FILE = "structured_popular_times.csv"
DAYS = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
START_HOUR = 6
HOURS_PER_DAY = 20
EST = pytz.timezone('US/Eastern')

async def scrape_popular_times(page, restaurant_url, index_offset):
    data = []
    await page.goto(restaurant_url, timeout=60000)
    await page.wait_for_timeout(4000)  # Let the page settle/load

    elements = await page.query_selector_all('div[aria-label*="Popular times"] [aria-label*="at"]')
    aria_labels = []
    
    for el in elements:
        aria = await el.get_attribute('aria-label')
        if aria and re.search(r"\d+% busy", aria):
            aria_labels.append(aria.strip())

    print(f"📊 Found {len(aria_labels)} time entries")
    
    structured = []
    for i, label in enumerate(aria_labels[:140]):  # Max 7 days × 20 hours
        day_index = i // HOURS_PER_DAY
        
        # Debug: print first few labels to see what we're working with
        if i < 5:
            print(f"🔍 Processing label {i}: '{label}'")
            print(f"   Pattern test with period: {bool(re.search(r'at (\d{1,2}) (AM|PM)\.', label))}")
            print(f"   Pattern test without period: {bool(re.search(r'at (\d{1,2}) (AM|PM)', label))}")
          # Extract the actual hour from the aria-label text - this is the source of truth
        # Note: Google Maps uses Unicode narrow no-break space (\u202f) between hour and AM/PM
        time_match = re.search(r"at (\d{1,2})\u202f(AM|PM)\.?", label)
        if not time_match:
            # Fallback: try with regular space in case some use normal spaces
            time_match = re.search(r"at (\d{1,2}) (AM|PM)\.?", label)
        
        if time_match:
            hour_12 = int(time_match.group(1))
            meridiem = time_match.group(2)
            
            # Convert to 24-hour format
            if meridiem == "AM":
                hour_24 = hour_12 if hour_12 != 12 else 0
            else:  # PM
                hour_24 = hour_12 if hour_12 == 12 else hour_12 + 12
            
            hour_label = f"{hour_12} {meridiem}"
            
            # Debug: print successful extraction
            if i < 5:
                print(f"✅ Extracted: {hour_12} {meridiem} -> {hour_24}")
                
            if day_index >= len(DAYS): 
                break

            percent_match = re.search(r"(\d+)%", label)
            busyness_percent = int(percent_match.group(1)) if percent_match else None

            structured.append({
                "restaurant_url": restaurant_url,
                "weekday": DAYS[day_index],
                "hour_24": hour_24,
                "hour_label": hour_label,
                "index": index_offset + i,
                "value": label,
                "busyness_percent": busyness_percent
            })
        else:
            # Skip entries where we can't extract the time
            print(f"⚠️ Could not extract time from: '{label}'")
            print(f"   Raw bytes: {repr(label)}")

    return structured

async def scrape_current_hour():
    """Scrape only the current hour's data for all restaurants"""
    # Get current time in EST
    current_time = datetime.now(EST)
    current_weekday = current_time.strftime('%A')
    current_hour_24 = current_time.hour
    
    print(f"🕐 Current EST time: {current_time.strftime('%A %I:%M %p')} (Hour {current_hour_24})")
    print(f"📅 Looking for LIVE data at {current_weekday} {current_hour_24}:00")
    
    results = []
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        for url in RESTAURANT_URLS:
            try:
                print(f"🔍 Checking current hour for: {url}")
                
                await page.goto(url, timeout=60000)
                await page.wait_for_timeout(4000)

                # Look for live busyness data first (this is what you see as "100% busy")
                live_elements = await page.query_selector_all('[aria-label*="% busy"]')
                
                current_live_busyness = None
                for el in live_elements:
                    aria = await el.get_attribute('aria-label')
                    if aria:
                        print(f"  Found live element: {aria}")
                        # Look for current live busyness (not time-specific)
                        live_match = re.search(r"(\d+)% busy", aria)
                        if live_match and not re.search(r"at \d", aria):  # Not time-specific
                            current_live_busyness = int(live_match.group(1))
                            print(f"🔴 LIVE busyness right now: {current_live_busyness}%")
                            break

                # If we found live data, use that
                if current_live_busyness is not None:
                    result = {
                        "restaurant_url": url,
                        "weekday": current_weekday,
                        "hour_24": current_hour_24,
                        "hour_label": f"{current_hour_24 % 12 or 12} {'AM' if current_hour_24 < 12 else 'PM'}",
                        "timestamp": current_time.isoformat(),
                        "value": f"{current_live_busyness}% busy (LIVE DATA)",
                        "busyness_percent": current_live_busyness
                    }
                    results.append(result)
                    print(f"✅ Found LIVE data: {current_live_busyness}% busy")
                    continue

                # Fallback: look in popular times chart for historical data
                print("  No live data found, checking popular times chart...")
                elements = await page.query_selector_all('div[aria-label*="Popular times"] [aria-label*="at"]')
                
                found_current_hour = False
                for el in elements:
                    aria = await el.get_attribute('aria-label')
                    if not aria or not re.search(r"\d+% busy", aria):
                        continue
                    
                    # Extract hour from aria-label
                    time_match = re.search(r"at (\d{1,2})\u202f(AM|PM)\.?", aria)
                    if not time_match:
                        time_match = re.search(r"at (\d{1,2}) (AM|PM)\.?", aria)
                    
                    if time_match:
                        hour_12 = int(time_match.group(1))
                        meridiem = time_match.group(2)
                        
                        # Convert to 24-hour format
                        if meridiem == "AM":
                            hour_24 = hour_12 if hour_12 != 12 else 0
                        else:  # PM
                            hour_24 = hour_12 if hour_12 == 12 else hour_12 + 12
                        
                        # Only process if this matches current EST hour
                        if hour_24 == current_hour_24:
                            percent_match = re.search(r"(\d+)%", aria)
                            busyness_percent = int(percent_match.group(1)) if percent_match else None
                            
                            result = {
                                "restaurant_url": url,
                                "weekday": current_weekday,
                                "hour_24": hour_24,
                                "hour_label": f"{hour_12} {meridiem}",
                                "timestamp": current_time.isoformat(),
                                "value": aria.strip(),
                                "busyness_percent": busyness_percent
                            }
                            results.append(result)
                            print(f"✅ Found historical data: {busyness_percent}% busy at {hour_12} {meridiem} EST")
                            found_current_hour = True
                            break
                
                if not found_current_hour and current_live_busyness is None:
                    print(f"⚠️ No data found for current hour {current_hour_24} EST")
                            
            except Exception as e:
                print(f"❌ Error scraping {url}: {e}")
                
            # Small delay between restaurants
            await asyncio.sleep(2)

        await browser.close()

    # Use EST time for filename
    current_hour_file = f"data/current_hour_{current_time.strftime('%Y%m%d_%H')}.csv"
    os.makedirs("data", exist_ok=True)
    
    fieldnames = ["restaurant_url", "weekday", "hour_24", "hour_label", "timestamp", "value", "busyness_percent"]
    with open(current_hour_file, "w", newline='', encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)

    print(f"✅ Current hour data saved to {current_hour_file}")
    return results

async def main():
    results = []
    index_offset = 0
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()

        for url in RESTAURANT_URLS:
            print(f"🔍 Scraping: {url}")
            try:
                data = await scrape_popular_times(page, url, index_offset)
                results.extend(data)
                index_offset += len(data)
            except Exception as e:
                print(f"❌ Error scraping {url}: {e}")

            delay = random.uniform(5, 10)
            print(f"⏳ Waiting {delay:.2f} seconds...\n")
            time.sleep(delay)

        await browser.close()

    # Save to CSV
    fieldnames = ["restaurant_url", "weekday", "hour_24", "hour_label", "index", "value", "busyness_percent"]
    with open(OUTPUT_FILE, "w", newline='', encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)

    print(f"✅ Done! Data saved to `{OUTPUT_FILE}`.")

# --- RUN ---
if __name__ == "__main__":
    asyncio.run(main())
