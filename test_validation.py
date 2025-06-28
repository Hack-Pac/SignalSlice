#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test script for validation improvements
"""

import sys
from validation import (
    ValidationError, validate_busyness_percent, validate_hour_24,
    validate_hour_12, validate_weekday, validate_meridiem,
    validate_data_type, validate_venue_type, validate_url,
    validate_timestamp, validate_scraped_data, validate_index_value,
    validate_batch_data, sanitize_string, validate_activity_item
)

def test_busyness_validation():
    """Test busyness percentage validation"""
    print("\n=== Testing Busyness Percentage Validation ===")
    
    test_cases = [
        (50, 50, "Valid integer"),
        ("75", 75, "Valid string"),
        (0, 0, "Minimum value"),
        (100, 100, "Maximum value"),
        (None, None, "None value"),
        ("", None, "Empty string"),
        ("None", None, "String 'None'"),
        (101, "Error", "Above maximum"),
        (-1, "Error", "Below minimum"),
        ("abc", "Error", "Non-numeric string"),
    ]
    
    for input_val, expected, description in test_cases:
        try:
            result = validate_busyness_percent(input_val)
            status = "✅" if result == expected else "❌"
            print(f"{status} {description}: {input_val} -> {result}")
        except ValidationError as e:
            status = "✅" if expected == "Error" else "❌"
            print(f"{status} {description}: {input_val} -> ValidationError: {e.message}")

def test_hour_validation():
    """Test hour validation"""
    print("\n=== Testing Hour Validation ===")
    
    # Test 24-hour format
    print("\n24-hour format:")
    for val in [0, 12, 24, "0", "24", 25, -1, "abc"]:
        try:
            result = validate_hour_24(val)
            print(f"✅ Hour 24: {val} -> {result}")
        except ValidationError as e:
            print(f"❌ Hour 24: {val} -> Error: {e.message}")
    
    # Test 12-hour format
    print("\n12-hour format:")
    for val in [1, 12, "1", "12", 0, 13, "abc"]:
        try:
            result = validate_hour_12(val)
            print(f"✅ Hour 12: {val} -> {result}")
        except ValidationError as e:
            print(f"❌ Hour 12: {val} -> Error: {e.message}")

def test_url_validation():
    """Test URL validation"""
    print("\n=== Testing URL Validation ===")
    
    urls = [
        ("https://maps.app.goo.gl/KqSr8hH5GV4ZGJP27", True),
        ("http://example.com", True),
        ("https://localhost:5000", True),
        ("not-a-url", False),
        ("ftp://example.com", False),
        ("", False),
        (None, False),
    ]
    
    for url, should_pass in urls:
        try:
            result = validate_url(url)
            status = "✅" if should_pass else "❌"
            print(f"{status} {url} -> Valid")
        except ValidationError as e:
            status = "✅" if not should_pass else "❌"
            print(f"{status} {url} -> Error: {e.message}")

def test_scraped_data_validation():
    """Test scraped data validation"""
    print("\n=== Testing Scraped Data Validation ===")
    
    test_data = [
        {
            "restaurant_url": "https://maps.app.goo.gl/test",
            "weekday": "Monday",
            "hour_24": 14,
            "busyness_percent": 75,
            "data_type": "LIVE",
            "venue_type": "restaurant"
        },
        {
            "restaurant_url": "invalid-url",
            "weekday": "Monday",
            "hour_24": 14,
            "busyness_percent": 75
        },
        {
            "restaurant_url": "https://maps.app.goo.gl/test",
            "weekday": "InvalidDay",
            "hour_24": 14,
            "busyness_percent": 75
        },
        {
            "restaurant_url": "https://maps.app.goo.gl/test",
            "weekday": "Monday",
            "hour_24": 25,  # Invalid hour
            "busyness_percent": 150  # Invalid percentage
        }
    ]
    
    for i, data in enumerate(test_data):
        print(f"\nTest case {i + 1}:")
        try:
            result = validate_scraped_data(data)
            print(f"✅ Valid data: {result}")
        except ValidationError as e:
            print(f"❌ Validation error: {e}")

def test_index_validation():
    """Test index value validation"""
    print("\n=== Testing Index Value Validation ===")
    
    test_values = [
        (5.5, 5.5, "Valid float"),
        (3, 3.0, "Valid integer"),
        ("7.25", 7.25, "Valid string"),
        (0, 0.0, "Minimum value"),
        (10, 10.0, "Maximum value"),
        (10.1, "Error", "Above maximum"),
        (-0.1, "Error", "Below minimum"),
        ("abc", "Error", "Non-numeric"),
    ]
    
    for input_val, expected, description in test_values:
        try:
            result = validate_index_value(input_val)
            status = "✅" if (isinstance(expected, (int, float)) and result == expected) else "❌"
            print(f"{status} {description}: {input_val} -> {result}")
        except ValidationError as e:
            status = "✅" if expected == "Error" else "❌"
            print(f"{status} {description}: {input_val} -> Error: {e.message}")

def test_sanitization():
    """Test string sanitization"""
    print("\n=== Testing String Sanitization ===")
    
    test_strings = [
        ("Normal string", "Normal string"),
        ("String with\x00control\x01chars", "String withcontrolchars"),
        ("Very " + "long " * 250 + "string", 1000),  # Should be truncated
        ("<script>alert('xss')</script>", "<script>alert('xss')</script>"),  # HTML not escaped (that's frontend's job)
        ("   Whitespace   ", "Whitespace"),
    ]
    
    for input_str, expected in test_strings:
        result = sanitize_string(input_str)
        if isinstance(expected, int):
            status = "✅" if len(result) <= expected else "❌"
            print(f"{status} Length test: {len(input_str)} chars -> {len(result)} chars (max {expected})")
        else:
            status = "✅" if result == expected else "❌"
            print(f"{status} '{input_str[:50]}...' -> '{result}'")

def test_batch_validation():
    """Test batch data validation"""
    print("\n=== Testing Batch Data Validation ===")
    
    batch_data = [
        {
            "restaurant_url": "https://maps.app.goo.gl/valid1",
            "weekday": "Monday",
            "busyness_percent": 50
        },
        {
            "restaurant_url": "invalid-url",
            "weekday": "Tuesday",
            "busyness_percent": 75
        },
        {
            "restaurant_url": "https://maps.app.goo.gl/valid2",
            "weekday": "Wednesday",
            "busyness_percent": 200  # Invalid
        },
        {
            "restaurant_url": "https://maps.app.goo.gl/valid3",
            "weekday": "Thursday",
            "busyness_percent": None  # Valid None
        }
    ]
    
    print(f"Processing {len(batch_data)} records...")
    validated = validate_batch_data(batch_data)
    print(f"✅ Successfully validated {len(validated)} records")

def test_activity_validation():
    """Test activity item validation"""
    print("\n=== Testing Activity Item Validation ===")
    
    test_items = [
        ("SCAN", "Starting scan", "normal", True),
        ("INVALID_TYPE", "Test message", "normal", False),
        ("ERROR", "Error message", "invalid_level", False),
        ("PIZZA", "A" * 600, "critical", True),  # Long message should be truncated
    ]
    
    for activity_type, message, level, should_pass in test_items:
        try:
            result = validate_activity_item(activity_type, message, level)
            status = "✅" if should_pass else "❌"
            print(f"{status} Type: {activity_type}, Level: {level} -> Valid")
            if len(message) > 50:
                print(f"   Message truncated: {len(message)} -> {len(result['message'])} chars")
        except ValidationError as e:
            status = "✅" if not should_pass else "❌"
            print(f"{status} Type: {activity_type}, Level: {level} -> Error: {e.message}")

def main():
    """Run all validation tests"""
    print("🧪 Running SignalSlice Validation Tests")
    print("=" * 50)
    
    test_busyness_validation()
    test_hour_validation()
    test_url_validation()
    test_scraped_data_validation()
    test_index_validation()
    test_sanitization()
    test_batch_validation()
    test_activity_validation()
    
    print("\n✅ All validation tests completed!")

if __name__ == "__main__":
    main()