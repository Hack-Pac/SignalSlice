import json
import csv
import os
import logging
import sys
from datetime import datetime
import pytz

THRESHOLD = 25  # how much higher than baseline to consider an anomaly

def setup_logging():
    """Setup logging with UTF-8 encoding"""
    try:
        # Try to set UTF-8 encoding for stdout
        if hasattr(sys.stdout, 'reconfigure'):
            sys.stdout.reconfigure(encoding='utf-8')
        if hasattr(sys.stderr, 'reconfigure'):
            sys.stderr.reconfigure(encoding='utf-8')
    except:
        pass  # Fallback silently if reconfigure not available

# Setup UTF-8 logging
setup_logging()

def check_current_anomalies():
    """Check for anomalies in the current hour and return True if any found"""
    # Get current time in EST
    est = pytz.timezone('US/Eastern')
    current_time_est = datetime.now(est)
    current_weekday = current_time_est.strftime('%A')
    current_hour = str(current_time_est.hour)
    
    # Also show local time for debugging
    local_time = datetime.now()
    print(f"🌍 Local time: {local_time.strftime('%A %I:%M %p')}")
    print(f"🕐 Current EST time: {current_time_est.strftime('%A %I:%M %p')} (Hour {current_hour})")
    print(f"📅 Checking anomalies for {current_weekday} at {current_hour}:00\n")

    # Load the baseline
    baseline_path = os.path.join(os.path.dirname(__file__), "..", "baseline.json")
    with open(baseline_path, "r") as f:
        baseline = json.load(f)

    # Find the most recent current hour data file
    data_dir = os.path.join(os.path.dirname(__file__), "..", "data")
    current_hour_pattern = f"current_hour_{current_time_est.strftime('%Y%m%d_%H')}.csv"
    current_hour_file = os.path.join(data_dir, current_hour_pattern)
    
    if not os.path.exists(current_hour_file):
        print(f"⚠️ No current hour data file found: {current_hour_file}")
        return False

    print("🔍 Checking for anomalies...\n")
    anomalies_found = False

    with open(current_hour_file, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if not row["busyness_percent"]:
                continue
                
            current = int(row["busyness_percent"])
            expected = baseline.get(current_weekday, {}).get(current_hour)

            if expected is None:
                print(f"⚠️ No baseline for {current_weekday} {current_hour}:00")
                continue

            diff = current - expected
            data_type = "LIVE" if "LIVE DATA" in row["value"] else "HISTORICAL"
            
            if diff >= THRESHOLD:
                print(f"🚨 ANOMALY DETECTED at {row['restaurant_url']}")
                print(f"    📅 {current_weekday} {current_hour}:00")
                print(f"    📊 Current: {current}% | Baseline: {expected}% | Δ: +{diff}%")
                print(f"    🔴 Data type: {data_type}")
                print(f"    🕐 Detected at: {current_time_est.strftime('%Y-%m-%d %H:%M:%S EST')}\n")
                anomalies_found = True
            else:
                print(f"✅ Normal activity at {row['restaurant_url']}: {current}% (baseline: {expected}%) [{data_type}]")

    return anomalies_found

# Check for current anomalies when the script is run
if __name__ == "__main__":
    check_current_anomalies()
