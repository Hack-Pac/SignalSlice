#!/usr/bin/env python3
"""
Data validation module for SignalSlice
Provides comprehensive validation for scraped data and API inputs
"""

from typing import Dict, List, Optional, Union, Any
from datetime import datetime
import re

# Valid ranges and constants
VALID_WEEKDAYS = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
VALID_HOURS_24 = list(range(0, 25))  # 0-24 (24 represents midnight of previous day)
VALID_HOURS_12 = list(range(1, 13))  # 1-12
VALID_MERIDIEMS = ["AM", "PM"]
VALID_DATA_TYPES = ["LIVE", "HISTORICAL", "NO_DATA"]
VALID_VENUE_TYPES = ["restaurant", "gay_bar"]
BUSYNESS_MIN = 0
BUSYNESS_MAX = 100

# URL validation pattern
URL_PATTERN = re.compile(
    r'^https?://'  # http:// or https://
    r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain...
    r'localhost|'  # localhost...
    r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
    r'(?::\d+)?'  # optional port
    r'(?:/?|[/?]\S+)$', re.IGNORECASE)

class ValidationError(Exception):
    """Custom validation error with field information"""
    def __init__(self, field: str, value: Any, message: str):
        self.field = field
        self.value = value
        self.message = message
        super().__init__(f"Validation error for field '{field}': {message} (value: {value})")

def validate_busyness_percent(value: Optional[Union[int, str]]) -> Optional[int]:
    """
    Validate and convert busyness percentage
    Returns None for missing data, raises ValidationError for invalid data
    """
    if value is None or value == "" or value == "None":
        return None
    
    try:
        if isinstance(value, str):
            value = int(value)
        elif not isinstance(value, int):
            raise ValidationError("busyness_percent", value, f"Must be integer or string, got {type(value).__name__}")
        
        if not (BUSYNESS_MIN <= value <= BUSYNESS_MAX):
            raise ValidationError("busyness_percent", value, f"Must be between {BUSYNESS_MIN} and {BUSYNESS_MAX}")
        
        return value
    except ValueError:
        raise ValidationError("busyness_percent", value, "Cannot convert to integer")

def validate_hour_24(value: Union[int, str]) -> int:
    """Validate 24-hour format hour"""
    try:
        hour = int(value)
        if hour not in VALID_HOURS_24:
            raise ValidationError("hour_24", value, f"Must be between 0 and 24, got {hour}")
        return hour
    except ValueError:
        raise ValidationError("hour_24", value, "Cannot convert to integer")

def validate_hour_12(value: Union[int, str]) -> int:
    """Validate 12-hour format hour"""
    try:
        hour = int(value)
        if hour not in VALID_HOURS_12:
            raise ValidationError("hour_12", value, f"Must be between 1 and 12, got {hour}")
        return hour
    except ValueError:
        raise ValidationError("hour_12", value, "Cannot convert to integer")

def validate_weekday(value: str) -> str:
    """Validate weekday name"""
    if value not in VALID_WEEKDAYS:
        raise ValidationError("weekday", value, f"Must be one of {VALID_WEEKDAYS}")
    return value

def validate_meridiem(value: str) -> str:
    """Validate AM/PM"""
    if value not in VALID_MERIDIEMS:
        raise ValidationError("meridiem", value, f"Must be one of {VALID_MERIDIEMS}")
    return value

def validate_data_type(value: str) -> str:
    """Validate data type"""
    if value not in VALID_DATA_TYPES:
        raise ValidationError("data_type", value, f"Must be one of {VALID_DATA_TYPES}")
    return value

def validate_venue_type(value: str) -> str:
    """Validate venue type"""
    if value not in VALID_VENUE_TYPES:
        raise ValidationError("venue_type", value, f"Must be one of {VALID_VENUE_TYPES}")
    return value

def validate_url(value: str) -> str:
    """Validate URL format"""
    if not isinstance(value, str):
        raise ValidationError("url", value, "Must be a string")
    
    if not URL_PATTERN.match(value):
        raise ValidationError("url", value, "Invalid URL format")
    
    return value

def validate_timestamp(value: str) -> str:
    """Validate ISO format timestamp"""
    try:
        datetime.fromisoformat(value.replace('Z', '+00:00'))
        return value
    except (ValueError, AttributeError):
        raise ValidationError("timestamp", value, "Invalid ISO timestamp format")

def validate_scraped_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate a scraped data record
    Returns validated and cleaned data
    """
    validated = {}
    
    # Required fields
    try:
        validated['restaurant_url'] = validate_url(data.get('restaurant_url', ''))
    except ValidationError as e:
        raise ValidationError('restaurant_url', data.get('restaurant_url'), "Invalid or missing URL")
    
    # Validate weekday
    try:
        validated['weekday'] = validate_weekday(data.get('weekday', ''))
    except ValidationError as e:
        raise ValidationError('weekday', data.get('weekday'), "Invalid or missing weekday")
    
    # Validate hours
    if 'hour_24' in data:
        validated['hour_24'] = validate_hour_24(data['hour_24'])
    
    if 'hour_12' in data and 'meridiem' in data:
        validated['hour_12'] = validate_hour_12(data['hour_12'])
        validated['meridiem'] = validate_meridiem(data['meridiem'])
    
    # Validate busyness (can be None)
    validated['busyness_percent'] = validate_busyness_percent(data.get('busyness_percent'))
    
    # Validate optional fields
    if 'data_type' in data:
        validated['data_type'] = validate_data_type(data['data_type'])
    
    if 'venue_type' in data:
        validated['venue_type'] = validate_venue_type(data['venue_type'])
    
    if 'timestamp' in data:
        validated['timestamp'] = validate_timestamp(data['timestamp'])
    
    # Copy over other fields that don't need validation
    for key in ['hour_label', 'value', 'index', 'element_index', 'raw_aria_label']:
        if key in data:
            validated[key] = data[key]
    
    return validated

def validate_api_input(endpoint: str, data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate API endpoint inputs
    Returns validated data or raises ValidationError
    """
    validated = {}
    
    if endpoint == '/api/activity_feed':
        # No input validation needed
        pass
        
    elif endpoint == '/api/trigger_scan':
        # No input validation needed
        pass
        
    elif endpoint == '/api/start_scanner':
        # No input validation needed
        pass
        
    elif endpoint == '/api/stop_scanner':
        # No input validation needed
        pass
    
    # Add more endpoint validations as needed
    
    return validated

def validate_index_value(value: Union[float, int, str], field_name: str = "index") -> float:
    """
    Validate index values (pizza_index, gay_bar_index)
    Must be between 0 and 10
    """
    try:
        index_value = float(value)
        if not (0 <= index_value <= 10):
            raise ValidationError(field_name, value, "Must be between 0 and 10")
        return round(index_value, 2)  # Round to 2 decimal places
    except (ValueError, TypeError):
        raise ValidationError(field_name, value, "Cannot convert to float")

def validate_batch_data(data_list: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Validate a batch of scraped data records
    Returns list of validated records, logs errors for invalid records
    """
    validated_records = []
    errors = []
    
    for i, record in enumerate(data_list):
        try:
            validated_record = validate_scraped_data(record)
            validated_records.append(validated_record)
        except ValidationError as e:
            errors.append({
                'record_index': i,
                'field': e.field,
                'value': e.value,
                'error': e.message,
                'url': record.get('restaurant_url', 'unknown')
            })
    
    if errors:
        print(f"⚠️ Validation errors found in {len(errors)} records:")
        for error in errors[:5]:  # Show first 5 errors
            print(f"  - Record {error['record_index']} ({error['url']}): {error['field']} - {error['error']}")
        if len(errors) > 5:
            print(f"  ... and {len(errors) - 5} more errors")
    
    return validated_records

def sanitize_string(value: str, max_length: int = 1000) -> str:
    """
    Sanitize string inputs to prevent injection attacks
    """
    if not isinstance(value, str):
        return str(value)
    
    # Remove control characters
    value = ''.join(char for char in value if ord(char) >= 32 or char in '\n\r\t')
    
    # Truncate to max length
    if len(value) > max_length:
        value = value[:max_length]
    
    return value.strip()

def validate_activity_item(activity_type: str, message: str, level: str) -> Dict[str, str]:
    """
    Validate activity feed item
    """
    valid_types = ['SCAN', 'SCRAPE', 'ANALYZE', 'ANOMALY', 'ERROR', 'SYSTEM', 'INIT', 'CONNECT', 'PIZZA', 'GAYBAR']
    valid_levels = ['normal', 'success', 'warning', 'critical']
    
    if activity_type not in valid_types:
        raise ValidationError('activity_type', activity_type, f"Must be one of {valid_types}")
    
    if level not in valid_levels:
        raise ValidationError('level', level, f"Must be one of {valid_levels}")
    
    return {
        'type': activity_type,
        'message': sanitize_string(message, 500),
        'level': level
    }