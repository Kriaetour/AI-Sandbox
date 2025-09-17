#!/usr/bin/env python3
"""
Test script for NPC Individual Ambition System
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from npcs.npc import NPC
from world.weather import WeatherType
import random
import time

def create_test_npcs():
    """Create test NPCs with different traits and ambitions."""
    npcs = []

    # Create NPCs with different personalities
    npc1 = NPC("Ambitious Warrior", (0, 0))
    npc1.traits = ["ambitious", "leader"]
    npc1.skills = {"combat": 80, "social": 60, "crafting": 40}
    npcs.append(npc1)

    npc2 = NPC("Cunning Trader", (0, 0))
    npc2.traits = ["diplomat", "crafting"]
    npc2.skills = {"combat": 30, "social": 85, "crafting": 70}
    npcs.append(npc2)

    npc3 = NPC("Resourceful Crafter", (0, 0))
    npc3.traits = ["crafting", "explorer"]
    npc3.skills = {"combat": 40, "social": 50, "crafting": 90}
    npcs.append(npc3)

    npc4 = NPC("Wise Elder", (0, 0))
    npc4.traits = ["content", "leader"]
    npc4.age = 60  # Old enough to potentially develop ambition
    npc4.skills = {"combat": 50, "social": 80, "crafting": 60}
    npcs.append(npc4)

    return npcs

def create_mock_world_context(npcs):
    """Create a mock world context for testing."""
    # Create a mock chunk with NPCs
    class MockChunk:
        def __init__(self, coordinates, npcs_list):
            self.coordinates = coordinates
            self.npcs = npcs_list
            self.resources = {"food": 50, "ore": 30, "wood": 40, "precious_stones": 10}
            self.weather = WeatherType.CLEAR

    mock_chunk = MockChunk((0, 0), npcs)

    return {
        "current_chunk": mock_chunk,
        "nearby_chunks": [],
        "time": {
            "hour": 12,
            "season": 1,  # Summer
            "season_name": "Summer",
            "total_minutes": 0
        },
        "world": None,
        "event_manager": None
    }

def test_ambition_system():
    """Test the ambition system with multiple NPCs."""
    print("🧪 Testing NPC Individual Ambition System")
    print("=" * 50)

    # Create test NPCs
    npcs = create_test_npcs()
    world_context = create_mock_world_context(npcs)

    print(f"Created {len(npcs)} test NPCs:")
    for npc in npcs:
        print(f"  - {npc.name}: traits={npc.traits}, skills={npc.skills}")
    print()

    # Run simulation for several ticks
    ticks = 20
    for tick in range(ticks):
        print(f"\n📊 Tick {tick + 1}/{ticks}")
        print("-" * 30)

        # Age all NPCs to make them eligible for ambitions
        for npc in npcs:
            npc.age = max(npc.age, 60)  # Make sure they're old enough

        # Update each NPC
        for npc in npcs:
            action = npc.update(world_context, {})
            if action:
                print(f"  {npc.name}: {action.get('action', 'none')} - {action.get('reason', 'no reason')}")

        # Show ambition status
        ambitious_npcs = [npc for npc in npcs if npc.ambition.get("type")]
        if ambitious_npcs:
            print("\n🎯 Current Ambitions:")
            for npc in ambitious_npcs:
                ambition = npc.ambition
                print(f"  {npc.name}: {ambition['type']} -> {ambition['target']} (progress: {ambition.get('progress', 0):.2f})")
                if ambition.get("allies"):
                    print(f"    Allies: {ambition['allies']}")
                if ambition.get("rivals"):
                    print(f"    Rivals: {ambition['rivals']}")

        # Small delay for readability
        time.sleep(0.1)

    print("\n🏁 Test Complete!")
    print("=" * 50)

    # Final ambition summary
    print("\n📈 Final Ambition Summary:")
    for npc in npcs:
        if npc.ambition.get("type"):
            ambition = npc.ambition
            print(f"  {npc.name}: {ambition['type']} (progress: {ambition.get('progress', 0):.2f})")
            print(f"    Influence: {ambition.get('influence_level', 0):.2f}")
            if ambition.get("allies"):
                print(f"    Allies: {ambition['allies']}")
            if ambition.get("rivals"):
                print(f"    Rivals: {ambition['rivals']}")
        else:
            print(f"  {npc.name}: No ambition developed")

if __name__ == "__main__":
    test_ambition_system()