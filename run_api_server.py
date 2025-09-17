#!/usr/bin/env python3
"""
AI Sandbox Visualization API Server
Run this script alongside your simulation to enable web visualization.

Usage:
1. Start this server: python run_api_server.py
2. Start simulation: python core_sim.py 1000
3. Open index.html in browser
"""

import sys
import os
import time
from visualizer_api import run_api, save_world_state

def main():
    print("=" * 60)
    print("🤖 AI Sandbox Visualization API Server")
    print("=" * 60)
    print("📊 This server provides real-time data for web visualization")
    print("🌐 Open index.html in your browser to view the simulation")
    print("🔌 API Endpoint: http://127.0.0.1:5000/world_state")
    print("=" * 60)

    # Add some initial demo data
    save_world_state({
        'tick': 0,
        'season': 'Spring',
        'population': 0,
        'total_food': 0.0,
        'npcs': [],
        'factions': [],
        'chunks': []
    })

    try:
        run_api()
    except KeyboardInterrupt:
        print("\n👋 API Server stopped")
    except Exception as e:
        print(f"❌ Error starting API server: {e}")
        return 1

    return 0

if __name__ == "__main__":
    sys.exit(main())