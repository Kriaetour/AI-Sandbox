#!/usr/bin/env python3
"""
Test NPC safety decision logic to verify the fix for NPCs seeking safety when they already have max safety.
"""

import sys
import os

# Add the main directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from npcs.npc import NPC
from world.chunk import Chunk
from world.weather import WeatherType


def test_npc_maxed_safety_behavior():
    """Test that NPCs with maxed safety don't seek safety during normal conditions."""
    print("Testing NPC safety behavior with maxed safety...")

    # Create a test NPC with maxed safety
    npc = NPC("TestNPC", "TestFaction", "TestFaction")
    npc.needs = {
        "food": 100.0,
        "safety": 100.0,  # Maxed safety
        "rest": 100.0,
        "social": 50.0,
    }

    # Create a test chunk
    chunk = Chunk((0, 0))
    chunk.npcs = [npc]

    # Create world context
    world_context = {
        "current_chunk": chunk,
        "nearby_chunks": [Chunk((1, 0)), Chunk((0, 1))],
        "tick": 100,
        "time_of_day": {"hour": 14, "season": "spring", "day": 1},  # Daytime, spring
        "weather": None,  # Clear weather
    }

    print(f"NPC {npc.name} has safety: {npc.needs['safety']}")

    # Create faction memory (minimal for testing)
    faction_memory = {}

    # Test normal conditions - should not seek safety
    action = npc._decide_action(world_context, faction_memory)
    print(f"Normal conditions action: {action}")

    if action and action.get("reason") == "seeking_safety":
        print("❌ FAILED: NPC with maxed safety is seeking safety during normal conditions!")
        return False
    else:
        print("✅ PASSED: NPC with maxed safety does not seek safety during normal conditions")

    # Test storm conditions - should only seek safety if safety is actually low
    chunk.weather = WeatherType.STORM  # Set weather on the chunk
    action = npc._decide_action(world_context, faction_memory)
    print(f"Storm conditions action: {action}")

    if action and action.get("reason") == "seeking_safety":
        print("❌ FAILED: NPC with maxed safety is seeking safety during storm!")
        return False
    else:
        print("✅ PASSED: NPC with maxed safety does not seek safety during storm")

    # Test heatwave conditions - should only seek safety if safety is actually low
    chunk.weather = WeatherType.HEATWAVE  # Set weather on the chunk
    action = npc._decide_action(world_context, faction_memory)
    print(f"Heatwave conditions action: {action}")

    if action and action.get("reason") == "seeking_safety":
        print("❌ FAILED: NPC with maxed safety is seeking safety during heatwave!")
        return False
    else:
        print("✅ PASSED: NPC with maxed safety does not seek safety during heatwave")

    return True


def test_npc_low_safety_behavior():
    """Test that NPCs with low safety do seek safety during weather conditions."""
    print("\nTesting NPC safety behavior with low safety...")

    # Create a test NPC with low safety
    npc = NPC("TestNPC", "TestFaction", "TestFaction")
    npc.needs = {
        "food": 100.0,
        "safety": 60.0,  # Low safety (below storm threshold of 80)
        "rest": 100.0,
        "social": 50.0,
    }

    # Enable debug logging for the NPC
    import logging

    logging.basicConfig(level=logging.DEBUG)
    npc.logger = logging.getLogger("TestNPC")

    # Create a test chunk
    chunk = Chunk((0, 0))
    chunk.npcs = [npc]

    # Create world context
    world_context = {
        "current_chunk": chunk,
        "nearby_chunks": [Chunk((1, 0)), Chunk((0, 1))],
        "tick": 100,
        "time_of_day": {"hour": 14, "season": "spring", "day": 1},  # Daytime, spring
        "weather": WeatherType.STORM,
    }

    print(f"NPC {npc.name} has safety: {npc.needs['safety']}")

    # Create faction memory (minimal for testing)
    faction_memory = {}

    # Test storm conditions with low safety - should seek safety
    chunk.weather = WeatherType.STORM  # Set weather on the chunk
    action = npc._decide_action(world_context, faction_memory)
    print(f"Storm conditions action: {action}")

    if action and action.get("reason") == "seeking_safety":
        print("✅ PASSED: NPC with low safety correctly seeks safety during storm")
        return True
    else:
        print("❌ FAILED: NPC with low safety did not seek safety during storm!")
        return False


if __name__ == "__main__":
    print("Running NPC safety decision logic tests...\n")

    test1_passed = test_npc_maxed_safety_behavior()
    test2_passed = test_npc_low_safety_behavior()

    print(f"\n{'='*50}")
    if test1_passed and test2_passed:
        print("🎉 ALL TESTS PASSED! Safety logic is working correctly.")
    else:
        print("❌ SOME TESTS FAILED! Safety logic needs more work.")
    print(f"{'='*50}")
