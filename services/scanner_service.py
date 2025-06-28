"""
SignalSlice Scanner Service
Handles all scanner-related operations
"""
import asyncio
import threading
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional

from config import (
    TIMEZONE, SCANNER_INITIAL_DELAY, SCANNER_RETRY_DELAY, 
    SCANNER_HOUR_BUFFER, INDEX_CONFIG
)
from state_manager import state_manager
from scraping.gmapsScrape import scrape_current_hour
from script.anomalyDetect import check_current_anomalies


class ScannerService:
    """Service for managing scanner operations"""
    
    def __init__(self, socketio=None):
        self.socketio = socketio
        self.scanner_loop = None
        self.scanner_task = None
        self.scanner_thread = None
    
    def emit_update(self, event: str, data: Any) -> None:
        """Emit update via WebSocket if socketio is available"""
        if self.socketio:
            self.socketio.emit(event, data)
    
    def add_activity(self, activity_type: str, message: str, level: str = 'normal') -> None:
        """Add activity and emit update"""
        activity = state_manager.add_activity(activity_type, message, level)
        self.emit_update('activity_update', activity)
        print(f"[{activity['timestamp']}] {activity_type}: {message}")
    
    def update_pizza_index(self, new_value: float, change_percent: float = 0) -> None:
        """Update pizza index and emit update"""
        data = state_manager.update_pizza_index(new_value, change_percent)
        self.emit_update('pizza_index_update', data)
        print(f"DEBUG: Pizza index updated to {new_value:.2f}")
    
    def update_gay_bar_index(self, new_value: float, change_percent: float = 0) -> None:
        """Update gay bar index and emit update"""
        data = state_manager.update_gay_bar_index(new_value, change_percent)
        self.emit_update('gay_bar_index_update', data)
        print(f"DEBUG: Gay bar index updated to {new_value:.2f}")
    
    def update_scan_stats(self) -> None:
        """Update scan statistics and emit update"""
        stats = state_manager.increment_scan_count()
        self.emit_update('scan_stats_update', stats)
    
    @staticmethod
    def get_next_hour_start() -> float:
        """Calculate seconds until the next hour starts"""
        now = datetime.now(TIMEZONE)
        next_hour = (now + timedelta(hours=1)).replace(minute=0, second=0, microsecond=0)
        return (next_hour - now).total_seconds()
    
    async def process_scraped_data(self, scraped_data: List[Dict[str, Any]]) -> None:
        """Process scraped data and update indices"""
        # Separate restaurant and gay bar data
        restaurant_data = [d for d in scraped_data if d.get('venue_type') == 'restaurant']
        gay_bar_data = [d for d in scraped_data if d.get('venue_type') == 'gay_bar']
        
        print(f"DEBUG: Found {len(restaurant_data)} restaurant data points, {len(gay_bar_data)} gay bar data points")
        
        # Calculate and update pizza index
        if restaurant_data:
            restaurant_with_data = [d for d in restaurant_data if d.get('busyness_percent') is not None]
            if restaurant_with_data:
                avg_restaurant_busy = sum(d['busyness_percent'] for d in restaurant_with_data) / len(restaurant_with_data)
                # Convert to 0-10 scale
                new_pizza_index = avg_restaurant_busy / 10
                current_index = state_manager.get('pizza_index', 0)
                change_percent = ((new_pizza_index - current_index) / current_index) * 100 if current_index > 0 else 0
                
                self.update_pizza_index(new_pizza_index, change_percent)
                self.add_activity('PIZZA', f'🍕 Pizza Index updated: {new_pizza_index:.2f} ({avg_restaurant_busy:.0f}% busy)', 'normal')
        
        # Calculate and update gay bar index
        if gay_bar_data:
            gay_bar_with_data = [d for d in gay_bar_data if d.get('busyness_percent') is not None]
            if gay_bar_with_data:
                avg_gay_bar_busy = sum(d['busyness_percent'] for d in gay_bar_with_data) / len(gay_bar_with_data)
                # Convert to 0-10 scale inversely
                new_gay_bar_index = 10 - (avg_gay_bar_busy / 10)
                current_index = state_manager.get('gay_bar_index', 0)
                change_percent = ((new_gay_bar_index - current_index) / current_index) * 100 if current_index > 0 else 0
                
                self.update_gay_bar_index(new_gay_bar_index, change_percent)
                self.add_activity('GAYBAR', f'🏳️‍🌈 Gay Bar Index updated: {new_gay_bar_index:.2f} ({avg_gay_bar_busy:.0f}% busy)', 'normal')
        else:
            self.add_activity('GAYBAR', '⚠️ No gay bar data available this scan', 'warning')
    
    async def handle_anomaly_detection(self, anomalies_found: bool) -> None:
        """Handle anomaly detection results"""
        if anomalies_found:
            anomaly_count = state_manager.increment_anomaly_count()
            
            self.add_activity('ANOMALY', '🚨🔴 LIVE ANOMALY DETECTED!', 'critical')
            self.add_activity('ANOMALY', 'Unusual pizza activity patterns found', 'critical')
            self.add_activity('ANOMALY', '🔥 This is REAL-TIME activity - high confidence!', 'critical')
            
            # Calculate new pizza index based on anomaly
            current_index = state_manager.get('pizza_index', 0)
            pizza_config = INDEX_CONFIG['pizza']
            new_index = min(pizza_config['max'], current_index + pizza_config['anomaly_boost'])
            change_percent = ((new_index - current_index) / current_index) * 100
            
            self.update_pizza_index(new_index, change_percent)
            
            # Emit anomaly alert
            self.emit_update('anomaly_detected', {
                'title': 'ANOMALY DETECTED',
                'message': 'Unusual pizza activity patterns detected - check logs for details',
                'timestamp': datetime.now(TIMEZONE).strftime('%H:%M:%S'),
                'anomaly_count': anomaly_count
            })
        else:
            self.add_activity('ANALYZE', '✅ No anomalies detected this hour', 'success')
            self.add_activity('SCAN', 'All locations within normal parameters', 'success')
            
            # Slight adjustment to pizza index for normal activity
            current_index = state_manager.get('pizza_index', 0)
            pizza_config = INDEX_CONFIG['pizza']
            
            # Small random adjustment
            base_change = ((hash(str(datetime.now())) % 21 - 10) / 100) * pizza_config['normal_adjustment']
            new_index = max(pizza_config['min'], min(pizza_config['max'], current_index + base_change))
            change_percent = ((new_index - current_index) / current_index) * 100 if current_index > 0 else 0
            
            self.update_pizza_index(new_index, change_percent)
    
    async def run_scanner_cycle(self) -> None:
        """Run one complete scanner cycle"""
        try:
            state_manager.set_scanning_status(True)
            self.emit_update('scanning_start', {})
            
            current_time = datetime.now(TIMEZONE)
            self.add_activity('SCAN', f'🕐 Starting hourly scan at {current_time.strftime("%Y-%m-%d %H:%M:%S EST")}', 'normal')
            
            # Step 1: Scrape data
            self.add_activity('SCRAPE', f'📡 Scraping current hour data for {current_time.strftime("%A %I:%M %p")}...', 'normal')
            self.add_activity('SCRAPE', f'📅 Looking for TODAY\'s ({current_time.strftime("%A")}) data at hour {current_time.hour}', 'normal')
            self.add_activity('SCRAPE', '🎯 Priority: LIVE data > Historical data > No data', 'normal')
            
            try:
                scraped_data = await scrape_current_hour()
                print(f"DEBUG: Scraped {len(scraped_data)} data points")
                
                self.add_activity('SCRAPE', '✅ Current hour data saved successfully', 'success')
                self.add_activity('SCRAPE', 'Data scraping completed', 'success')
                
                # Process scraped data
                await self.process_scraped_data(scraped_data)
                
            except Exception as e:
                self.add_activity('ERROR', f'❌ Scraping failed: {str(e)}', 'critical')
                print(f"ERROR in scraping: {e}")
                import traceback
                traceback.print_exc()
            
            # Step 2: Check for anomalies
            self.add_activity('ANALYZE', '🔍 Checking for anomalies...', 'normal')
            self.add_activity('ANALYZE', f'🌍 Local time: {datetime.now().strftime("%A %I:%M %p")}', 'normal')
            self.add_activity('ANALYZE', f'🕐 Current EST time: {current_time.strftime("%A %I:%M %p")} (Hour {current_time.hour})', 'normal')
            self.add_activity('ANALYZE', f'📅 Checking anomalies for {current_time.strftime("%A")} at {current_time.hour}:00', 'normal')
            
            # Run anomaly detection
            anomalies_found = check_current_anomalies()
            
            # Update statistics and handle anomalies
            self.update_scan_stats()
            await self.handle_anomaly_detection(anomalies_found)
            
            # Complete scan
            state_manager.set_scanning_status(False)
            self.emit_update('scanning_complete', {})
            
            completion_time = datetime.now(TIMEZONE)
            self.add_activity('SYSTEM', f'✅ Scan completed at {completion_time.strftime("%H:%M:%S EST")}', 'success')
            
            # Calculate and announce next scan
            next_scan_seconds = self.get_next_hour_start()
            next_scan_time = datetime.now(TIMEZONE) + timedelta(seconds=next_scan_seconds)
            self.add_activity('SYSTEM', f'⏰ Next scan scheduled for {next_scan_time.strftime("%H:%M:%S EST")} ({next_scan_seconds/60:.0f} minutes)', 'normal')
            
        except Exception as e:
            state_manager.set_scanning_status(False)
            self.add_activity('ERROR', f'❌ Scanner error: {str(e)}', 'critical')
            self.emit_update('scanning_complete', {})
            print(f"Scanner error: {e}")
    
    async def hourly_scanner(self) -> None:
        """Main scanner loop that runs hourly"""
        print("🛰️ SignalSlice Integrated Scanner Starting...")
        self.add_activity('INIT', '🛰️ SignalSlice integrated scanner starting...', 'normal')
        self.add_activity('INIT', '🔄 Running initial scan, then switching to hourly schedule', 'normal')
        
        # Run initial scan
        await self.run_scanner_cycle()
        
        while state_manager.get('scanner_running', False):
            try:
                # Calculate time until next hour
                sleep_seconds = self.get_next_hour_start()
                next_run = datetime.now(TIMEZONE) + timedelta(seconds=sleep_seconds)
                
                print(f"⏰ Next scan scheduled for {next_run.strftime('%H:%M:%S EST')} ({sleep_seconds/60:.1f} minutes)")
                self.add_activity('SYSTEM', f'Scanner on standby - next automated scan in {sleep_seconds/60:.0f} minutes', 'normal')
                
                # Sleep until next hour
                await asyncio.sleep(min(sleep_seconds + SCANNER_HOUR_BUFFER, 3600))
                
                # Check if scanner is still running
                if state_manager.get('scanner_running', False):
                    self.add_activity('SYSTEM', 'Hourly scan interval reached - initiating new scan cycle', 'normal')
                    await self.run_scanner_cycle()
                    
            except asyncio.CancelledError:
                self.add_activity('SYSTEM', '🛑 Scanner stopped by user request', 'warning')
                break
            except Exception as e:
                self.add_activity('ERROR', f'❌ Scanner loop error: {str(e)}', 'critical')
                print(f"❌ Unexpected error in scanner loop: {e}")
                # Wait before retrying
                self.add_activity('SYSTEM', f'Waiting {SCANNER_RETRY_DELAY/60:.0f} minutes before retry to avoid rapid failures', 'warning')
                await asyncio.sleep(SCANNER_RETRY_DELAY)
    
    def start(self) -> threading.Thread:
        """Start the scanner in a separate thread"""
        def run_scanner_loop():
            self.scanner_loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self.scanner_loop)
            
            state_manager.set_scanner_running(True)
            self.scanner_task = self.scanner_loop.create_task(self.hourly_scanner())
            
            try:
                self.scanner_loop.run_until_complete(self.scanner_task)
            except Exception as e:
                print(f"Scanner thread error: {e}")
            finally:
                self.scanner_loop.close()
        
        self.scanner_thread = threading.Thread(target=run_scanner_loop)
        self.scanner_thread.daemon = True
        self.scanner_thread.start()
        return self.scanner_thread
    
    def stop(self) -> None:
        """Stop the scanner"""
        state_manager.set_scanner_running(False)
        
        if self.scanner_task and not self.scanner_task.done():
            self.scanner_task.cancel()
        
        if self.scanner_loop:
            self.scanner_loop.call_soon_threadsafe(self.scanner_loop.stop)
    
    async def run_manual_scan(self) -> None:
        """Run a manual scan cycle"""
        await self.run_scanner_cycle()