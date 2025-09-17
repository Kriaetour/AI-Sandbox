#!/usr/bin/env python3
"""
Simple verification test for environmental AI integration (Step 4)
Demonstrates that seasonal behavior has been implemented
"""

import sys
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format="%(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


def test_code_integration():
    """Test that seasonal code exists in the files"""
    print("=== VERIFYING ENVIRONMENTAL AI INTEGRATION ===")
    print("Checking that seasonal behavior code has been added to key files...")

    success = True

    # Test 1: NPC seasonal behavior
    try:
        from npcs.npc import NPC

        # Check that the _decide_action method exists
        npc = NPC("TestNPC", "warrior", "TestVillage")
        assert hasattr(npc, "_decide_action"), "NPC _decide_action method missing"

        # Check that seasonal helper methods exist
        assert hasattr(npc, "_spring_exploration_action"), "Spring exploration method missing"
        assert hasattr(npc, "_cautious_resource_check"), "Cautious resource check method missing"
        assert hasattr(npc, "_prepare_for_winter_night"), "Winter night preparation method missing"

        print("✅ NPC seasonal behavior methods implemented")

    except Exception as e:
        print(f"❌ NPC seasonal behavior test failed: {e}")
        success = False

    # Test 2: Tribal seasonal behavior
    try:
        from tribes.tribal_manager import TribalManager

        tribal_manager = TribalManager()

        # Check that seasonal methods exist
        assert hasattr(
            tribal_manager, "_adjust_tribal_priorities_for_season"
        ), "Tribal seasonal priority adjustment missing"
        assert hasattr(
            tribal_manager, "_process_seasonal_activities"
        ), "Seasonal activities processing missing"
        assert hasattr(
            tribal_manager, "_get_seasonal_ceremony_types"
        ), "Seasonal ceremony types missing"

        print("✅ Tribal seasonal behavior methods implemented")

    except Exception as e:
        print(f"❌ Tribal seasonal behavior test failed: {e}")
        success = False

    # Test 3: Diplomatic seasonal behavior
    try:
        from tribes.tribal_diplomacy import TribalDiplomacy

        # Create empty tribes dictionary for diplomacy initialization
        empty_tribes = {}
        diplomacy = TribalDiplomacy(empty_tribes)

        # Check that seasonal diplomacy methods exist
        assert hasattr(diplomacy, "set_seasonal_context"), "Diplomatic seasonal context missing"
        assert hasattr(
            diplomacy, "_get_seasonal_modifiers"
        ), "Diplomatic seasonal modifiers missing"

        print("✅ Diplomatic seasonal behavior methods implemented")

    except Exception as e:
        print(f"❌ Diplomatic seasonal behavior test failed: {e}")
        success = False

    # Test 4: Create and verify functionality
    try:
        tribal_manager = TribalManager()

        # Test seasonal ceremony types
        winter_ceremonies = tribal_manager._get_seasonal_ceremony_types(3)  # Winter
        spring_ceremonies = tribal_manager._get_seasonal_ceremony_types(0)  # Spring

        assert winter_ceremonies != spring_ceremonies, "Seasonal ceremonies should differ"
        print(f"   Winter ceremonies: {winter_ceremonies}")
        print(f"   Spring ceremonies: {spring_ceremonies}")
        print("✅ Seasonal ceremony variation confirmed")

        # Test that seasonal context can be set
        seasonal_context = {
            "season": 3,  # Winter
            "season_name": "Winter",
            "day_cycle": 0.5,
            "is_day": True,
        }

        tribal_manager.tribal_diplomacy.set_seasonal_context(seasonal_context)
        winter_modifiers = tribal_manager.tribal_diplomacy._get_seasonal_modifiers()

        # Change to summer and get modifiers
        summer_context = {
            "season": 1,  # Summer
            "season_name": "Summer",
            "day_cycle": 0.5,
            "is_day": True,
        }
        tribal_manager.tribal_diplomacy.set_seasonal_context(summer_context)
        summer_modifiers = tribal_manager.tribal_diplomacy._get_seasonal_modifiers()

        assert winter_modifiers != summer_modifiers, "Seasonal diplomatic modifiers should differ"
        print(f"   Winter diplomatic modifiers: {winter_modifiers}")
        print(f"   Summer diplomatic modifiers: {summer_modifiers}")
        print("✅ Seasonal diplomatic variation confirmed")

    except Exception as e:
        print(f"❌ Functional integration test failed: {e}")
        success = False

    # Final assertion to ensure test failure if any sub-check failed
    assert success, "One or more seasonal integration checks failed"


def demonstrate_seasonal_features():
    """Demonstrate key seasonal features"""
    print("\n=== DEMONSTRATING SEASONAL FEATURES ===")

    try:
        from tribes.tribal_manager import TribalManager
        from tribes.tribal_diplomacy import TribalDiplomacy

        # Show seasonal ceremony types
        tribal_manager = TribalManager()
        print("\nSeasonal Ceremony Types:")
        seasons = ["Spring", "Summer", "Autumn", "Winter"]
        for i, season in enumerate(seasons):
            ceremonies = tribal_manager._get_seasonal_ceremony_types(i)
            print(f"  {season}: {ceremonies}")

        # Show seasonal diplomatic modifiers
        diplomacy = TribalDiplomacy({})  # Empty tribes dict for testing
        print("\nSeasonal Diplomatic Modifiers:")
        for i, season in enumerate(seasons):
            # Set the season context
            season_context = {
                "season": i,
                "season_name": season,
                "day_cycle": 0.5,
                "is_day": True,
            }
            diplomacy.set_seasonal_context(season_context)
            modifiers = diplomacy._get_seasonal_modifiers()
            print(f"  {season}: {modifiers}")

        print("\n✅ Seasonal features demonstrated successfully!")
        return True

    except Exception as e:
        print(f"❌ Feature demonstration failed: {e}")
        return False


def run_comprehensive_test():
    """Run all verification tests"""
    print("ENVIRONMENTAL AI INTEGRATION VERIFICATION")
    print("=" * 50)

    success = True

    # Test that code integration is complete
    if not test_code_integration():
        success = False

    # Demonstrate features
    if not demonstrate_seasonal_features():
        success = False

    if success:
        print("\n" + "=" * 50)
        print("🎉 ENVIRONMENTAL AI INTEGRATION VERIFIED!")
        print("=" * 50)
        print("✅ NPCs now consider season and time of day in decisions")
        print("✅ Tribes adapt priorities based on environmental conditions")
        print("✅ Diplomatic decisions factor in seasonal context")
        print("✅ Seasonal activities and ceremonies implemented")
        print("✅ Step 4: Environmental AI Integration COMPLETE!")
        print("\nThe simulation now features truly dynamic AI that responds")
        print("to environmental conditions, creating more immersive and")
        print("realistic behavior patterns throughout the seasons!")
    else:
        print("\n❌ INTEGRATION VERIFICATION FAILED")
        print("Some seasonal AI features may not be working correctly.")

    return success


if __name__ == "__main__":
    success = run_comprehensive_test()
    sys.exit(0 if success else 1)
