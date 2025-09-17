import json
import os
import time
from flask import Flask, jsonify
from flask_cors import CORS
import threading
from typing import Dict, Any

# Shared data file for inter-process communication
WORLD_STATE_FILE = 'world_state.json'
_WORLD_STATE_TMP = WORLD_STATE_FILE + '.tmp'

# This global variable will be shared between the simulation and the API
world_state: Dict[str, Any] = {}
_world_state_lock = threading.Lock()

app = Flask(__name__)
CORS(app)  # This enables Cross-Origin Resource Sharing

def load_world_state(previous: Dict[str, Any] | None = None) -> Dict[str, Any]:
    """Load world state from shared file.

    Uses a resilient strategy: if reading or parsing fails, returns the previous
    state (to avoid front-end flicker / resets)."""
    try:
        if os.path.exists(WORLD_STATE_FILE):
            with open(WORLD_STATE_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if isinstance(data, dict):
                    return data
    except Exception as e:
        # Keep last good state
        print(f"[API] Error loading world state (keeping previous): {e}")
    return previous or {}

def save_world_state(state: Dict[str, Any]):
    """Save world state to shared file atomically.

    Writes to a temporary file first then replaces the target to avoid readers
    encountering partial JSON content."""
    try:
        # Augment with timestamp so frontend can detect staleness
        state['last_updated'] = time.time()
        tmp_path = _WORLD_STATE_TMP
        with open(tmp_path, 'w', encoding='utf-8') as f:
            json.dump(state, f, separators=(',', ':'), ensure_ascii=False)
        os.replace(tmp_path, WORLD_STATE_FILE)
    except Exception as e:
        print(f"[API] Error saving world state: {e}")

def update_world_state():
    """Background thread to periodically load world state from file.

    Maintains last good state to prevent empty snapshots due to transient
    read/write races."""
    global world_state
    prev: Dict[str, Any] | None = None
    while True:
        new_state = load_world_state(prev)
        if new_state is not prev:  # Identity check; changed or first load
            with _world_state_lock:
                world_state = new_state
            prev = new_state
        time.sleep(0.5)  # Update every 500ms

@app.route('/world_state')
def get_world_state():
    """This endpoint returns the latest simulation state as JSON."""
    with _world_state_lock:
        return jsonify(world_state)

@app.route('/health')
def get_health():
    """Simple health/freshness endpoint for frontend connection logic."""
    with _world_state_lock:
        ts = world_state.get('last_updated') if isinstance(world_state, dict) else None
    now = time.time()
    freshness = None
    if ts:
        freshness = max(0.0, now - ts)
    return jsonify({
        'status': 'ok',
        'has_state': bool(world_state),
        'last_updated': ts,
        'age_seconds': freshness
    })

def run_api():
    """Function to run the Flask API server."""
    try:
        print("[API] Starting Flask server on port 5000...")
        # Start background thread to load world state from file
        update_thread = threading.Thread(target=update_world_state, daemon=True)
        update_thread.start()
        print("[API] World state update thread started")

        # Use host='0.0.0.0' to allow external connections and threaded=True for better performance
        app.run(host='0.0.0.0', port=5000, debug=False, use_reloader=False, threaded=True)
    except Exception as e:
        print(f"[API] Error starting Flask server: {e}")
        # Fallback: try without threading
        try:
            app.run(host='127.0.0.1', port=5000, debug=False, use_reloader=False)
        except Exception as e2:
            print(f"[API] Failed to start Flask server: {e2}")

# In your main simulation file (e.g., core_sim.py), you would add this:
#
# from visualizer_api import run_api, world_state
#
# def main_simulation_loop(world_engine):
#     # Start the API in a separate thread
#     api_thread = threading.Thread(target=run_api, daemon=True)
#     api_thread.start()
#
#     while True:  # Your existing simulation loop
#         world_engine.tick()
#
#         # Every N ticks, update the shared world_state for the API
#         if world_engine.get_tick() % 10 == 0:
#             latest_state = {
#                 'tick': world_engine.get_tick(),
#                 'season': world_engine.get_season(),
#                 'npcs': [npc.serialize() for npc in world_engine.get_all_npcs()],
#                 'factions': [faction.serialize() for faction in world_engine.get_all_factions()],
#                 'chunks': [chunk.serialize() for chunk in world_engine.get_active_chunks()]
#             }
#             world_state.update(latest_state)