import asyncio
import csv
import random
import time
from playwright.async_api import async_playwright

RESTAURANT_URLS = [
    "https://maps.app.goo.gl/KqSr8hH5GV4ZGJP27",  
    # More links here
]

OUTPUT_FILE = "signalslice_popular_times.csv"

async def scrape_popular_times(page, restaurant_url):
    try:
        await page.goto(restaurant_url, timeout=60000)
        elements = await page.query_selector_all('div[aria-label*="Popular times"] [aria-label*="at"]')

        for el in elements:
            aria = await el.get_attribute('aria-label')
            if aria:
                data.append(aria)
        return data
    except Exception as e:
        print("Failed to scrape {restaurant_url}: {e}")
        return []

async def main():
    results = []
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)

        for url in RESTAURANT_URLS:
            print("🔍 Scraping: {url}")
            data = await scrape_popular_times(page, url)
            for entry in data:
                results.append({"url": url, "popular_time": entry})

            delay = random.uniform(5, 10)
            print("Waiting {delay:.2f} seconds...\n")
            time.sleep(delay)

        await browser.close()
    # Write to CSV
    with open(OUTPUT_FILE, "w", newline='', encoding="utf-8") as csvfile:
        writer.writerows(results)
    print("Done! Data saved to `{OUTPUT_FILE}`.")

# --- RUN ---
if __name__ == "__main__":
    asyncio.run(main())

















