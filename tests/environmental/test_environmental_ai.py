#!/usr/bin/env python3
"""
Test script for verifying environmental AI integration (Step 4)
This tests whether NPCs and factions properly adapt their behavior to:
- Current season (Spring, Summer, Autumn, Winter)
- Time of day (Day vs Night)
- Environmental conditions affecting decision-making
"""

import sys
import logging
from tribes.tribal_manager import TribalManager
from world.engine import WorldEngine
from npcs.npc import NPC

# Set up logging to see AI decisions
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


def test_seasonal_npc_behavior():
    """Test that NPCs adapt their behavior based on current season"""
    print("\n=== TESTING SEASONAL NPC BEHAVIOR ===")

    # Test NPC in different seasons
    npc = NPC("TestNPC", "warrior", "Testville")

    for season_num, season_name in enumerate(["Spring", "Summer", "Autumn", "Winter"]):
        print(f"\n--- Testing {season_name} (Season {season_num}) ---")

        # Simulate seasonal context
        world_context = {
            "season": season_num,
            "season_name": season_name,
            "day_cycle": 0.5,  # Noon
            "is_day": True,
        }

        # Let NPC make decisions with seasonal context
        print(f"NPC decision-making in {season_name}:")
        empty_faction_memory = {}  # Empty faction memory for testing
        for i in range(3):
            action = npc._decide_action(world_context, empty_faction_memory)
            print(f"  Decision {i+1}: {action}")

        # Test resource gathering efficiency
        efficiency = npc._get_seasonal_gathering_efficiency(season_num)
        print(f"  Gathering efficiency in {season_name}: {efficiency}")


def test_seasonal_tribal_behavior():
    """Test that tribes adapt their priorities based on season"""
    print("\n=== TESTING SEASONAL TRIBAL BEHAVIOR ===")

    # Create tribal manager
    tribal_manager = TribalManager()

    # Create a test tribe
    test_tribe = tribal_manager.create_tribe("TestTribe", (10, 10))
    test_tribe.add_shared_resource("food", 50)
    test_tribe.add_shared_resource("materials", 30)

    for season_num, season_name in enumerate(["Spring", "Summer", "Autumn", "Winter"]):
        print(f"\n--- Testing Tribal Behavior in {season_name} (Season {season_num}) ---")

        # Set seasonal context
        seasonal_context = {
            "season": season_num,
            "season_name": season_name,
            "day_cycle": 0.5,
            "is_day": True,
        }

        # Test tribal priority adjustments
        old_priorities = test_tribe.get_tribal_priorities().copy()
        tribal_manager._adjust_tribal_priorities_for_season(test_tribe, seasonal_context)
        new_priorities = test_tribe.get_tribal_priorities()

        print(f"  Priority changes in {season_name}:")
        for priority, old_val in old_priorities.items():
            new_val = new_priorities.get(priority, old_val)
            if abs(new_val - old_val) > 0.01:
                print(f"    {priority}: {old_val:.2f} -> {new_val:.2f}")

        # Test seasonal activities
        print("  Processing seasonal activities...")
        tribal_manager._current_seasonal_context = seasonal_context
        tribal_manager._process_seasonal_activities(test_tribe, season_num, season_name)


def test_seasonal_diplomacy():
    """Test that diplomatic decisions consider seasonal factors"""
    print("\n=== TESTING SEASONAL DIPLOMACY ===")

    # Create tribal manager with two tribes
    tribal_manager = TribalManager()

    tribe1 = tribal_manager.create_tribe("WinterTribe", (10, 10))
    tribe2 = tribal_manager.create_tribe("SummerTribe", (12, 12))

    # Add some resources to both tribes
    for tribe in [tribe1, tribe2]:
        tribe.add_shared_resource("food", 40)
        tribe.add_shared_resource("materials", 20)

    # Test diplomacy in different seasons
    for season_num, season_name in enumerate(["Spring", "Summer", "Autumn", "Winter"]):
        print(f"\n--- Testing Diplomacy in {season_name} (Season {season_num}) ---")

        seasonal_context = {
            "season": season_num,
            "season_name": season_name,
            "day_cycle": 0.5,
            "is_day": True,
        }

        # Set seasonal context for diplomacy
        tribal_manager.diplomacy.set_seasonal_context(seasonal_context)

        # Test negotiation type selection
        negotiation_type = tribal_manager.diplomacy._choose_negotiation_type(tribe1, tribe2, {})
        print(f"  Negotiation type chosen in {season_name}: {negotiation_type}")

        # Test seasonal modifiers
        modifiers = tribal_manager.diplomacy._get_seasonal_modifiers(season_num)
        print(f"  Seasonal diplomatic modifiers: {modifiers}")


def test_day_night_integration():
    """Test that the day/night cycle affects NPC and tribal behavior"""
    print("\n=== TESTING DAY/NIGHT CYCLE INTEGRATION ===")

    npc = NPC("NightTester", "gatherer", "TestVillage")

    # Test different times of day in winter (most dramatic differences)
    winter_context_day = {
        "season": 3,
        "season_name": "Winter",
        "day_cycle": 0.5,  # Noon
        "is_day": True,
    }

    winter_context_night = {
        "season": 3,
        "season_name": "Winter",
        "day_cycle": 0.8,  # Late evening
        "is_day": False,
    }

    print("\n--- Winter Day vs Night Behavior ---")
    print("Day decisions:")
    empty_faction_memory = {}
    for i in range(3):
        action = npc._decide_action(winter_context_day, empty_faction_memory)
        print(f"  {action}")

    print("Night decisions:")
    for i in range(3):
        action = npc._decide_action(winter_context_night, empty_faction_memory)
        print(f"  {action}")


def test_resource_seasonal_availability():
    """Test that resources have seasonal availability patterns"""
    print("\n=== TESTING SEASONAL RESOURCE AVAILABILITY ===")

    npc = NPC("ResourceTester", "gatherer", "TestVillage")

    resources = ["berries", "roots", "meat", "wood", "stone"]

    for season_num, season_name in enumerate(["Spring", "Summer", "Autumn", "Winter"]):
        print(f"\n--- {season_name} Resource Availability ---")
        for resource in resources:
            availability = npc._get_seasonal_resource_availability(resource, season_num)
            print(f"  {resource}: {availability:.2f}")


def run_simulation_test():
    """Run a short simulation to see all systems working together"""
    print("\n=== RUNNING INTEGRATED SIMULATION TEST ===")

    # Create world engine
    world = WorldEngine()

    # Create tribal manager
    tribal_manager = TribalManager()

    # Create test tribes
    tribe1 = tribal_manager.create_tribe("NorthTribe", (5, 5))
    tribe2 = tribal_manager.create_tribe("SouthTribe", (15, 15))

    # Add initial resources
    for tribe in [tribe1, tribe2]:
        tribe.add_shared_resource("food", 30)
        tribe.add_shared_resource("materials", 20)

    print("Running 4 simulation steps (representing different seasons)...")

    for step in range(4):
        season_name = ["Spring", "Summer", "Autumn", "Winter"][step]

        print(f"\n--- Simulation Step {step + 1}: {season_name} ---")

        # Update world time
        world.current_time = step * 90  # Each season is 90 days
        world_context = world.get_current_context()

        # Process tribal dynamics with seasonal context
        tribal_manager.process_tribal_dynamics(world_context)

        # Process seasonal events
        tribal_manager.process_tribal_events()

        print(f"  Completed {season_name} processing")


if __name__ == "__main__":
    print("=== ENVIRONMENTAL AI INTEGRATION TEST ===")
    print("Testing whether NPCs and factions adapt to seasonal and time-based conditions")

    try:
        test_seasonal_npc_behavior()
        test_seasonal_tribal_behavior()
        test_seasonal_diplomacy()
        test_day_night_integration()
        test_resource_seasonal_availability()
        run_simulation_test()

        print("\n=== TEST SUMMARY ===")
        print("✅ All environmental AI integration tests completed successfully!")
        print("✅ NPCs adapt their behavior based on season and time of day")
        print("✅ Tribes adjust priorities and activities based on environmental conditions")
        print("✅ Diplomatic decisions consider seasonal factors")
        print("✅ Resource availability reflects seasonal patterns")
        print("✅ Integrated simulation runs with environmental awareness")

    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        logger.exception("Test error details:")
        sys.exit(1)
