#!/usr/bin/env python3
"""
Standalone Flask API server for AI Sandbox visualization.
Run this script to start the API server, then open index.html in a browser.
"""

from flask import Flask, jsonify
from flask_cors import CORS
import threading

# This global variable will be shared between the simulation and the API
world_state = {
    'tick': 100,
    'season': 'Spring',
    'population': 50,
    'total_food': 200.0,
    'npcs': [
        {'id': 1, 'name': 'TestNPC1', 'coordinates': [10, 10], 'faction_id': 'TestFaction1', 'health': 100, 'age': 25},
        {'id': 2, 'name': 'TestNPC2', 'coordinates': [15, 15], 'faction_id': 'TestFaction2', 'health': 80, 'age': 30}
    ],
    'factions': [
        {'name': 'TestFaction1', 'population': 1, 'resources': {'food': 50.0, 'Wood': 25.0}},
        {'name': 'TestFaction2', 'population': 1, 'resources': {'food': 40.0, 'Wood': 30.0}}
    ],
    'chunks': [
        {'coordinates': [0, 0], 'terrain': 'PLAINS', 'is_active': True},
        {'coordinates': [1, 0], 'terrain': 'FOREST', 'is_active': True},
        {'coordinates': [0, 1], 'terrain': 'MOUNTAINS', 'is_active': True}
    ]
}

app = Flask(__name__)
CORS(app)  # This enables Cross-Origin Resource Sharing

@app.route('/world_state')
def get_world_state():
    """This endpoint returns the latest simulation state as JSON."""
    return jsonify(world_state)

@app.route('/')
def index():
    """Serve a simple test page."""
    return """
    <h1>AI Sandbox API Server</h1>
    <p>The API is running on port 5000.</p>
    <p>Open <a href="index.html">index.html</a> in your browser to view the visualization.</p>
    <p>Test the API: <a href="/world_state">/world_state</a></p>
    """

if __name__ == '__main__':
    print("[API] Starting Flask server on port 5000...")
    print("[API] Open index.html in your browser to view the visualization")
    print("[API] Test the API at: http://127.0.0.1:5000/world_state")
    app.run(port=5000, debug=False, use_reloader=False, threaded=True)