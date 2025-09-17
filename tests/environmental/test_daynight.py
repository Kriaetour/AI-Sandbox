#!/usr/bin/env python3
"""
Test script for day/night cycle NPC behavior
"""

import logging
import sys
import os

from world.engine import WorldEngine
from npcs.npc import NPC
from world.chunk import Chunk

# Add current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Set up logging to show DEBUG messages
logging.basicConfig(
    level=logging.DEBUG,
    format="%(levelname)s: %(message)s",
    handlers=[logging.StreamHandler()],
)


def test_time_advancement():
    """Test that time advances correctly"""
    print("=== Testing Time Advancement ===")

    engine = WorldEngine(seed=42)

    print(
        f"Initial time: {engine.current_hour}:00 (minute {engine.current_minute}), Day {engine.current_day}, Season {engine.season_names[engine.current_season]}"
    )

    # Force time to advance by running world ticks
    # Each tick = 1 minute, so we need 60 ticks to advance 1 hour
    times_to_check = [30, 60, 90, 120]  # 30 minutes, 1 hour, 1.5 hours, 2 hours

    for tick_target in times_to_check:
        # Run ticks up to the target
        while engine.total_minutes < tick_target:
            engine.world_tick()

        print(
            f"After {tick_target} minutes: {engine.current_hour}:00 (minute {engine.current_minute}), Day {engine.current_day}, Season {engine.season_names[engine.current_season]}"
        )


def test_npc_time_behavior():
    """Test that NPCs respond to time of day"""
    print("\n=== Testing NPC Time-Based Behavior ===")

    engine = WorldEngine(seed=42)

    # Create a test chunk and NPC
    test_chunk = Chunk((0, 0))
    test_npc = NPC("test_npc", (0, 0))
    test_chunk.npcs.append(test_npc)
    engine.active_chunks[(0, 0)] = test_chunk

    # Test different times of day
    test_times = [
        (2, "Night - should prioritize rest/safety"),
        (7, "Dawn - should be moderately active"),
        (12, "Day - should be most active"),
        (19, "Dusk - should wind down activities"),
    ]

    for hour, description in test_times:
        print(f"\n--- Testing {description} ---")

        # Set the time manually
        engine.current_hour = hour
        engine.total_minutes = hour * 60

        # Create world context with time info
        world_context = {
            "current_chunk": test_chunk,
            "nearby_chunks": [],
            "all_chunks": [test_chunk],
            "time": {
                "hour": engine.current_hour,
                "day": engine.current_day,
                "season": engine.current_season,
                "season_name": engine.season_names[engine.current_season],
                "total_minutes": engine.total_minutes,
            },
        }

        print(f"Time: {hour}:00")

        # Update the NPC with time context
        test_npc.update(world_context, {})


if __name__ == "__main__":
    test_time_advancement()
    test_npc_time_behavior()
    print("\n=== Test Complete ===")
