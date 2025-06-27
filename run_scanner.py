#!/usr/bin/env python3
"""
SignalSlice Real-time Scanner
Runs continuous hourly monitoring of pizza activity around the Pentagon
"""
import asyncio
import sys
import os

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from scheduler import main

if __name__ == "__main__":
    print("🛰️ SignalSlice Real-time Scanner")
    print("Press Ctrl+C to stop")
    print("-" * 50)
    
    try:
        asyncio.run(main())  # Starts the scheduler
    except KeyboardInterrupt:
        print("\n🛑 Scanner stopped. Stay vigilant! 🍕")
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        sys.exit(1)


