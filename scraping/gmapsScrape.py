import asyncio
import csv
import random
import time
import re
import os
from playwright.async_api import async_playwright
import pytz
from datetime import datetime, timedelta

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
    
    # Adjust for Google Maps' day structure: 12 AM belongs to previous day
    if current_hour_24 == 0:
        # 12 AM belongs to previous day as hour 24
        target_weekday = (current_time - timedelta(days=1)).strftime('%A')
        target_hour = 24  # Treat as hour 24 of previous day
        print(f"🕐 Current EST time: {current_time.strftime('%A %I:%M %p')} (Hour {current_hour_24})")
        print(f"📅 Looking for PREVIOUS day's ({target_weekday}) data at hour 24 (12 AM)")
        print(f"🔍 Logic: 12 AM on {current_weekday} = Hour 24 of {target_weekday}")
    else:
        target_weekday = current_weekday
        target_hour = current_hour_24
        print(f"🕐 Current EST time: {current_time.strftime('%A %I:%M %p')} (Hour {current_hour_24})")
        print(f"📅 Looking for TODAY's ({target_weekday}) data at hour {target_hour}")
    
    results = []
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        for url in RESTAURANT_URLS:
            try:
                print(f"\n🔍 Checking current hour for: {url}")
                
                await page.goto(url, timeout=60000)
                await page.wait_for_timeout(4000)

                # Get all Popular Times elements
                elements = await page.query_selector_all('div[aria-label*="Popular times"] [aria-label*="at"]')
                print(f"  📊 Found {len(elements)} total time elements")
                
                # Parse all time data first
                all_time_data = []
                for i, el in enumerate(elements):
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
                        
                        # Convert hour 0 to hour 24 for Google Maps logic
                        display_hour = 24 if hour_24 == 0 else hour_24
                        
                        # Extract busyness percentage
                        percent_match = re.search(r"(\d+)%", aria)
                        busyness_percent = int(percent_match.group(1)) if percent_match else None
                        
                        all_time_data.append({
                            "index": i,
                            "hour_24": hour_24,
                            "display_hour": display_hour,  # Hour 24 for 12 AM
                            "hour_12": hour_12,
                            "meridiem": meridiem,
                            "busyness": busyness_percent,
                            "raw": aria
                        })

                if not all_time_data:
                    print("  ❌ No time data found")
                    continue

                # Debug: Show raw hour sequence before cycle detection
                hour_sequence = [d["display_hour"] for d in all_time_data]
                print(f"  📋 Raw hour sequence: {hour_sequence}")

                # Detect day cycles based on hour patterns
                day_cycles = []
                current_cycle = []
                
                print(f"  🔄 Analyzing hour cycles to detect days...")
                print(f"     Looking for 6 AM to mark new day boundaries...")
                
                for idx, data in enumerate(all_time_data):
                    hour = data["hour_24"]
                    
                    # If we see hour 6 (6 AM) and we already have data, start a new cycle
                    if hour == 6 and current_cycle:
                        print(f"    📅 Day boundary detected at element {data['index']} (6 AM)")
                        print(f"       Previous cycle had {len(current_cycle)} hours: {[d['display_hour'] for d in current_cycle]}")
                        day_cycles.append(current_cycle)
                        current_cycle = []
                    
                    current_cycle.append(data)
                    print(f"       Added hour {data['display_hour']} to current cycle (total: {len(current_cycle)})")

                # Add the last cycle
                if current_cycle:
                    print(f"    📅 Final cycle has {len(current_cycle)} hours: {[d['display_hour'] for d in current_cycle]}")
                    day_cycles.append(current_cycle)

                print(f"  📊 Detected {len(day_cycles)} day cycles total")
                
                # Assign days to cycles with better logic
                # The issue is determining which cycle represents "today"
                print(f"  📅 Assigning day names to cycles...")
                print(f"     Current day: {current_weekday}")
                print(f"     Target day for search: {target_weekday}")
                
                # Try to identify today's cycle by looking for the most complete recent cycle
                today_cycle_idx = None
                for cycle_idx, cycle in enumerate(day_cycles):
                    cycle_hours = sorted(set(d["display_hour"] for d in cycle))
                    cycle_start_hour = min(cycle_hours) if cycle_hours else None
                    cycle_end_hour = max(cycle_hours) if cycle_hours else None
                    
                    print(f"    Cycle {cycle_idx}: {len(cycle_hours)} unique hours")
                    print(f"       Hours: {cycle_hours}")
                    print(f"       Range: {cycle_start_hour} to {cycle_end_hour}")
                    
                    # Heuristic: Look for a cycle that starts around 6-10 and has reasonable coverage
                    if cycle_start_hour and cycle_start_hour <= 10 and len(cycle_hours) >= 10:
                        if today_cycle_idx is None:  # Take the first reasonable cycle as "today"
                            today_cycle_idx = cycle_idx
                            print(f"       🎯 Marking this as TODAY's cycle (first complete cycle)")

                # If we couldn't identify today's cycle, default to cycle 1 (second cycle)
                if today_cycle_idx is None and len(day_cycles) > 1:
                    today_cycle_idx = 1
                    print(f"    🎯 Defaulting to cycle 1 as TODAY's cycle")

                # Build day mapping based on today's cycle
                day_names = {}
                if today_cycle_idx is not None:
                    for i in range(len(day_cycles)):
                        day_offset = i - today_cycle_idx  # Offset from today's cycle
                        target_date = current_time + timedelta(days=day_offset)
                        day_names[i] = target_date.strftime('%A')
                        print(f"    Cycle {i} = {day_names[i]} (offset: {day_offset} days)")

                # Find target data
                target_data = None
                print(f"  🎯 Searching for {target_weekday} hour {target_hour}...")
                
                for cycle_idx, cycle in enumerate(day_cycles):
                    cycle_day_name = day_names.get(cycle_idx, "Unknown")
                    cycle_hours = [d["display_hour"] for d in cycle]
                    
                    print(f"    Checking Cycle {cycle_idx} ({cycle_day_name})")
                    print(f"       Available hours: {sorted(set(cycle_hours))}")
                    
                    # Check if this cycle matches our target day and contains our target hour
                    if cycle_day_name == target_weekday:
                        print(f"    ✅ Found target day cycle {cycle_idx} ({target_weekday})")
                        for data in cycle:
                            if data["display_hour"] == target_hour:
                                target_data = {
                                    "restaurant_url": url,
                                    "weekday": target_weekday,
                                    "hour_24": current_hour_24,  # Use actual current hour for filename
                                    "hour_label": f"{data['hour_12']} {data['meridiem']}",
                                    "timestamp": current_time.isoformat(),
                                    "value": data["raw"] + f" ({target_weekday} Hour {target_hour} - Cycle {cycle_idx})",
                                    "busyness_percent": data["busyness"]
                                }
                                print(f"      🎯 FOUND target data: {data['busyness']}% at {data['hour_12']} {data['meridiem']} on {target_weekday}")
                                break
                        break
                    else:
                        print(f"       ❌ Not target day (looking for {target_weekday})")

                # Add the data we found (if any)
                if target_data:
                    results.append(target_data)
                    print(f"✅ Using {target_weekday} data: {target_data['busyness_percent']}%")
                else:
                    print(f"⚠️ No data found for {target_weekday} at hour {target_hour}")
                    print(f"   Available cycles: {list(day_names.values())}")
                    
                    # Still create a record to show we checked
                    results.append({
                        "restaurant_url": url,
                        "weekday": target_weekday,
                        "hour_24": current_hour_24,
                        "hour_label": f"{current_hour_24 % 12 or 12} {'AM' if current_hour_24 < 12 else 'PM'}",
                        "timestamp": current_time.isoformat(),
                        "value": f"No data available for {target_weekday} at hour {target_hour}",
                        "busyness_percent": None
                    })
                            
            except Exception as e:
                print(f"❌ Error scraping {url}: {e}")
                
            # Small delay between restaurants
            await asyncio.sleep(2)

        await browser.close()

    # Use EST time for filename (keep current hour for file naming)
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
    asyncio.run(main())
