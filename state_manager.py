"""
SignalSlice State Management Module
Handles application state in a thread-safe manner
"""
import threading
from datetime import datetime
from typing import Dict, List, Any, Optional
from config import DASHBOARD_DEFAULTS, MAX_ACTIVITY_FEED_ITEMS, TIMEZONE


class StateManager:
    """Thread-safe state management for the SignalSlice application"""
    
    def __init__(self):
        self._state = DASHBOARD_DEFAULTS.copy()
        self._lock = threading.Lock()
        self._observers = []
    
    def get_state(self) -> Dict[str, Any]:
        """Get a copy of the current state"""
        with self._lock:
            return self._state.copy()
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get a specific state value"""
        with self._lock:
            return self._state.get(key, default)
    
    def set(self, key: str, value: Any) -> None:
        """Set a specific state value"""
        with self._lock:
            self._state[key] = value
            self._notify_observers(key, value)
    
    def update(self, updates: Dict[str, Any]) -> None:
        """Update multiple state values at once"""
        with self._lock:
            self._state.update(updates)
            for key, value in updates.items():
                self._notify_observers(key, value)
    
    def add_activity(self, activity_type: str, message: str, level: str = 'normal') -> Dict[str, Any]:
        """Add an activity to the feed and return the activity item"""
        timestamp = datetime.now(TIMEZONE).strftime('%H:%M:%S')
        
        activity = {
            'type': activity_type,
            'message': message,
            'level': level,
            'timestamp': timestamp
        }
        
        with self._lock:
            feed = self._state.get('activity_feed', [])
            feed.insert(0, activity)
            self._state['activity_feed'] = feed[:MAX_ACTIVITY_FEED_ITEMS]
        
        self._notify_observers('activity_feed', self._state['activity_feed'])
        return activity
    
    def update_pizza_index(self, new_value: float, change_percent: float = 0) -> Dict[str, Any]:
        """Update pizza index and return the update data"""
        with self._lock:
            old_value = self._state.get('pizza_index', 0)
            self._state['pizza_index'] = new_value
            
            data = {
                'value': new_value,
                'change': change_percent,
                'old_value': old_value
            }
        
        self._notify_observers('pizza_index', data)
        return data
    
    def update_gay_bar_index(self, new_value: float, change_percent: float = 0) -> Dict[str, Any]:
        """Update gay bar index and return the update data"""
        with self._lock:
            old_value = self._state.get('gay_bar_index', 0)
            self._state['gay_bar_index'] = new_value
            
            data = {
                'value': new_value,
                'change': change_percent,
                'old_value': old_value
            }
        
        self._notify_observers('gay_bar_index', data)
        return data
    
    def increment_scan_count(self) -> Dict[str, Any]:
        """Increment scan count and update last scan time"""
        with self._lock:
            self._state['scan_count'] = self._state.get('scan_count', 0) + 1
            self._state['last_scan_time'] = datetime.now(TIMEZONE)
            
            stats = {
                'scan_count': self._state['scan_count'],
                'last_scan_time': self._state['last_scan_time'].strftime('%H:%M:%S')
            }
        
        self._notify_observers('scan_stats', stats)
        return stats
    
    def increment_anomaly_count(self) -> int:
        """Increment anomaly count and return new count"""
        with self._lock:
            self._state['anomaly_count'] = self._state.get('anomaly_count', 0) + 1
            count = self._state['anomaly_count']
        
        self._notify_observers('anomaly_count', count)
        return count
    
    def set_scanning_status(self, scanning: bool) -> None:
        """Set scanning status"""
        with self._lock:
            self._state['scanning'] = scanning
        
        self._notify_observers('scanning', scanning)
    
    def set_scanner_running(self, running: bool) -> None:
        """Set scanner running status"""
        with self._lock:
            self._state['scanner_running'] = running
        
        self._notify_observers('scanner_running', running)
    
    def register_observer(self, callback) -> None:
        """Register a callback to be notified of state changes"""
        self._observers.append(callback)
    
    def unregister_observer(self, callback) -> None:
        """Unregister a callback"""
        if callback in self._observers:
            self._observers.remove(callback)
    
    def _notify_observers(self, key: str, value: Any) -> None:
        """Notify all observers of a state change"""
        for observer in self._observers:
            try:
                observer(key, value)
            except Exception as e:
                print(f"Error notifying observer: {e}")


# Global state manager instance
state_manager = StateManager()