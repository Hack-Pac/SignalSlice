# SignalSlice Refactoring Guide

## Overview
This guide documents the refactoring of the SignalSlice codebase from a monolithic structure to a modular, maintainable architecture.

## Key Changes

### 1. Configuration Module (`config.py`)
- **Purpose**: Centralized configuration management
- **Features**:
  - All configuration values in one place
  - Environment variable support via `.env`
  - Organized by functional areas (Flask, Scanner, Scraping, etc.)
  - Type-safe configuration with defaults

### 2. State Management (`state_manager.py`)
- **Purpose**: Thread-safe application state management
- **Features**:
  - Singleton StateManager class
  - Thread-safe operations with locks
  - Observer pattern for state change notifications
  - Centralized state updates

### 3. Scanner Service (`services/scanner_service.py`)
- **Purpose**: Extracted scanner logic from app.py
- **Features**:
  - Encapsulated scanner operations
  - Clean separation of concerns
  - Reusable scanner logic
  - Better error handling and recovery

### 4. Refactored Scraper (`scraping/scraper_refactored.py`)
- **Purpose**: Break down the massive 326-line scrape_current_hour function
- **Features**:
  - GoogleMapsScraper class with focused methods
  - Separated live data extraction from historical data
  - Modular data processing functions
  - Better error handling and logging
  - Improved readability and maintainability

### 5. Main App Refactoring (`app_refactored.py`)
- **Purpose**: Simplified main application file
- **Features**:
  - Uses dependency injection for services
  - Cleaner route handlers
  - Separated concerns
  - Better organization

## Migration Steps

### Step 1: Install Dependencies
Ensure all required packages are installed:
```bash
pip install python-dotenv
```

### Step 2: Create Environment File
Create a `.env` file in the project root with your configuration:
```env
FLASK_SECRET_KEY=your-secret-key-here
FLASK_HOST=0.0.0.0
FLASK_PORT=5000
FLASK_DEBUG=False
```

### Step 3: Update Imports
Replace imports in your existing code:

**Old:**
```python
from scraping.gmapsScrape import scrape_current_hour
```

**New:**
```python
from scraping.scraper_adapter import scrape_current_hour
```

### Step 4: Use State Manager
Replace global state access with state manager:

**Old:**
```python
dashboard_state['pizza_index'] = new_value
```

**New:**
```python
from state_manager import state_manager
state_manager.update_pizza_index(new_value, change_percent)
```

### Step 5: Use Configuration
Replace hardcoded values with configuration:

**Old:**
```python
app.config['SECRET_KEY'] = 'signalslice-pizza-monitor-2024'
```

**New:**
```python
from config import FLASK_SECRET_KEY
app.config['SECRET_KEY'] = FLASK_SECRET_KEY
```

## Benefits of Refactoring

1. **Maintainability**: Smaller, focused modules are easier to understand and modify
2. **Testability**: Each module can be tested independently
3. **Reusability**: Components can be reused in different contexts
4. **Scalability**: Easier to add new features without affecting existing code
5. **Error Handling**: Better error isolation and recovery
6. **Configuration Management**: All settings in one place
7. **State Management**: Thread-safe state updates with observer pattern

## Next Steps

1. **Testing**: Add unit tests for each module
2. **Documentation**: Add docstrings to all functions and classes
3. **Logging**: Implement structured logging across all modules
4. **Error Handling**: Add comprehensive error handling and recovery
5. **Performance**: Profile and optimize critical paths
6. **Security**: Review and enhance security measures

## Backward Compatibility

The refactored code maintains backward compatibility through adapter modules. Existing code can continue to work while gradually migrating to the new structure.

## File Structure

```
SignalSlice/
├── config.py                    # Centralized configuration
├── state_manager.py            # State management
├── services/
│   ├── __init__.py
│   └── scanner_service.py      # Scanner service
├── scraping/
│   ├── gmapsScrape.py         # Original scraper (kept for compatibility)
│   ├── scraper_refactored.py  # Refactored scraper
│   └── scraper_adapter.py     # Adapter for backward compatibility
├── app.py                      # Original app (kept for compatibility)
└── app_refactored.py          # Refactored app
```

## Running the Refactored Version

To run the refactored version:

```bash
python app_refactored.py
```

The original version remains available:

```bash
python app.py
```