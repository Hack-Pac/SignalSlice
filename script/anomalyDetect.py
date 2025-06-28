import json
import csv
import os
import logging
import sys
from datetime import datetime, timedelta
import pytz
import traceback
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from validation import validate_busyness_percent, ValidationError

# Configure logging
logger = logging.getLogger(__name__)

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
    # Adjust for Google Maps' day structure: 12 AM belongs to previous day
    if current_time_est.hour == 0:
        # 12 AM belongs to previous day
        baseline_weekday = (current_time_est - timedelta(days=1)).strftime('%A')
        baseline_hour = "24"  # Treat as hour 24 of previous day
        logger.info(f"🌍 Local time: {datetime.now().strftime('%A %I:%M %p')}")
        logger.info(f"🕐 Current EST time: {current_time_est.strftime('%A %I:%M %p')} (Hour {current_hour})")
        logger.info(f"📅 Checking anomalies for PREVIOUS day ({baseline_weekday}) at hour 24 (12 AM)\n")
    else:
        baseline_weekday = current_weekday
        baseline_hour = current_hour
        logger.info(f"🌍 Local time: {datetime.now().strftime('%A %I:%M %p')}")
        logger.info(f"🕐 Current EST time: {current_time_est.strftime('%A %I:%M %p')} (Hour {current_hour})")
        logger.info(f"📅 Checking anomalies for {baseline_weekday} at {baseline_hour}:00\n")

    # Load the baseline
    baseline_path = os.path.join(os.path.dirname(__file__), "..", "baseline.json")
    try:
        with open(baseline_path, "r") as f:
            baseline = json.load(f)
    except FileNotFoundError:
        logger.error(f"Baseline file not found at {baseline_path}")
        return False
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in baseline file: {e}")
        return False
    # Find the most recent current hour data file
    data_dir = os.path.join(os.path.dirname(__file__), "..", "data")
    current_hour_pattern = f"current_hour_{current_time_est.strftime('%Y%m%d_%H')}.csv"
    current_hour_file = os.path.join(data_dir, current_hour_pattern)
    if not os.path.exists(current_hour_file):
        logger.info(f"⚠️ No current hour data file found: {current_hour_file}")
        return False
    logger.info("🔍 Checking for anomalies...\n")
    anomalies_found = False
    with open(current_hour_file, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            logger.info(f"📊 Processing row: {row['restaurant_url']}")
            logger.info(f"   Raw busyness_percent: '{row['busyness_percent']}'")
            logger.info(f"   Value field: '{row['value']}'")
            logger.info(f"   Data weekday: {row['weekday']}")
            logger.info(f"   Data type: {row.get('data_type', 'UNKNOWN')}")
            # Check for live text flags
            value_text = row.get('value', '').lower()
            has_live_text_flag = any(flag in value_text for flag in [
                "busier than usual", "as busy as it gets"
            ])
            if has_live_text_flag:
                logger.info(f"   🚨 LIVE TEXT FLAG detected!")
            elif "not busy" in value_text:
                logger.info(f"   ✅ LIVE TEXT: 'Not busy' - no flag")
            
            # Skip rows with no busyness data
            if not row["busyness_percent"] or row["busyness_percent"] == "None":
                logger.info(f"ℹ️ No busyness data available for {row['restaurant_url']} at this hour")
                continue
            
            # Validate and convert busyness percentage
            try:
                current = validate_busyness_percent(row["busyness_percent"])
                if current is None:
                    continue
            except ValidationError as e:
                logger.error(f"Invalid busyness data: {e}")
                continue
            expected = baseline.get(baseline_weekday, {}).get(baseline_hour)
            data_type = row.get('data_type', 'UNKNOWN')
            logger.info(f"   Current busyness: {current}% ({data_type})")
            logger.info(f"   Expected baseline ({baseline_weekday} hour {baseline_hour}): {expected}%")

            if expected is None:
                logger.warning(f"No baseline for {baseline_weekday} {baseline_hour}:00")
                continue
            
            # Ensure expected is a valid number
            try:
                expected = float(expected)
            except (TypeError, ValueError):
                logger.error(f"Invalid baseline value: {expected}")
                continue

            diff = current - expected
            logger.info(f"   Difference: {diff}% (threshold: {THRESHOLD}%)")
            
            # Enhanced anomaly detection with text flags
            is_threshold_anomaly = diff >= THRESHOLD
            if is_threshold_anomaly or has_live_text_flag:
                if data_type == "LIVE" and has_live_text_flag:
                    anomaly_prefix = "🚨🔴🚨 CRITICAL LIVE ANOMALY"
                elif data_type == "LIVE":
                    anomaly_prefix = "🚨🔴 LIVE ANOMALY"
                elif has_live_text_flag:
                    anomaly_prefix = "🚨📝 TEXT FLAG ANOMALY"
                else:
                    anomaly_prefix = "🚨 ANOMALY"
                    
                logger.info(f"{anomaly_prefix} DETECTED at {row['restaurant_url']}")
                logger.info(f"    📅 {baseline_weekday} {baseline_hour}:00")
                logger.info(f"    📊 Current: {current}% | Baseline: {expected}% | Δ: +{diff}%")
                logger.info(f"    🎯 Data type: {data_type}")
                
                if has_live_text_flag:
                    logger.info(f"    🚨 LIVE TEXT FLAG detected!")
                if data_type == "LIVE":
                    logger.info(f"    🔥 This is REAL-TIME activity - high confidence!")
                logger.info(f"    🕐 Detected at: {current_time_est.strftime('%Y-%m-%d %H:%M:%S EST')}\n")
                anomalies_found = True
            else:
                status_icon = "✅🔴" if data_type == "LIVE" else "✅"
                logger.info(f"{status_icon} Normal activity at {row['restaurant_url']}: {current}% (baseline: {expected}%) [{data_type}]")
    return anomalies_found
# Check for current anomalies when the script is run
if __name__ == "__main__":
    try:
        anomalies_found = check_current_anomalies()
        sys.exit(0 if anomalies_found else 1)
    except Exception as e:
        logger.error(f"Anomaly detection failed: {e}")
        logger.error(traceback.format_exc())
        sys.exit(2)


















































