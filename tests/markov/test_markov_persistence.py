#!/usr/bin/env python3
"""
Test script to verify Markov chain persistence and learning system
"""
import sys
import os

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from markov_behavior import global_tribal_markov, save_markov_state, load_markov_state
from persistence_manager import PersistenceManager


def test_markov_persistence_and_learning():
    """Test the complete Markov chain persistence and learning system."""

    print("Testing Markov chain persistence and learning system...")

    # Test 1: Basic learning
    print("\n1. Testing Markov learning...")

    # Simulate successful diplomatic event
    global_tribal_markov.learn_from_outcome(
        "diplomatic", "high_trust_friendly", "cultural_exchange", 0.9
    )
    print("   ✅ Recorded successful cultural exchange")

    # Simulate failed conflict resolution
    global_tribal_markov.learn_from_outcome("conflict", "major_conflict_strong", "warfare", 0.2)
    print("   ✅ Recorded failed warfare attempt")

    # Simulate successful resource management
    global_tribal_markov.learn_from_outcome("resource", "scarcity_winter", "cautious_trade", 0.8)
    print("   ✅ Recorded successful cautious trade")

    # Test 2: Manual save/load of Markov state
    print("\n2. Testing manual Markov state persistence...")

    test_file = "test_markov_state.json"

    # Save current state
    save_markov_state(test_file)
    print("   ✅ Saved Markov state to file")

    # Modify state to verify loading
    global_tribal_markov.diplomatic_chain.model.clear()
    print("   ✅ Cleared diplomatic chain for testing")

    # Load state back
    load_markov_state(test_file)
    restored_model = dict(global_tribal_markov.diplomatic_chain.model)

    if restored_model:
        print("   ✅ Successfully restored Markov state from file")
    else:
        print("   ❌ Failed to restore Markov state")

    # Test 3: Integration with PersistenceManager
    print("\n3. Testing PersistenceManager integration...")

    pm = PersistenceManager("test_persistence")

    # Test serialization
    try:
        markov_data = pm._serialize_markov_chains()
        if markov_data and "behavioral" in markov_data and "dialogue" in markov_data:
            print("   ✅ Successfully serialized Markov chains")
        else:
            print("   ❌ Failed to serialize Markov chains properly")
    except Exception as e:
        print(f"   ❌ Error during serialization: {e}")

    # Test deserialization
    try:
        pm._deserialize_markov_chains(markov_data)
        print("   ✅ Successfully deserialized Markov chains")
    except Exception as e:
        print(f"   ❌ Error during deserialization: {e}")

    # Test 4: Learning feedback integration
    print("\n4. Testing learning feedback integration...")

    # Test learning feedback method
    try:
        pm.learn_from_interaction("diplomatic", "peaceful_negotiation", "compromise_offer", 0.75)
        print("   ✅ Successfully recorded learning feedback")
    except Exception as e:
        print(f"   ❌ Error recording learning feedback: {e}")

    # Test 5: Decision making with learned patterns
    print("\n5. Testing decision making with learned patterns...")

    # Make decisions to verify learning has affected behavior
    for i in range(5):
        diplomatic_context = {
            "trust_level": 0.8,
            "relationship": "friendly",
            "traits": ["peaceful"],
            "recent_events": [],
        }

        actions = [
            "cultural_exchange",
            "trade_proposal",
            "alliance_proposal",
            "warfare",
        ]
        choice = global_tribal_markov.make_diplomatic_decision(diplomatic_context, actions)
        print(f"   Decision {i+1}: {choice}")

    # Test 6: Verify state persistence across "simulation runs"
    print("\n6. Testing persistence across simulation runs...")

    # Save a test world state with Markov data
    try:
        # Create minimal mock world object
        class MockWorld:
            def __init__(self):
                self.active_chunks = {}
                self.current_hour = 12
                self.current_day = 1
                self.current_season = 0
                self.total_minutes = 720
                self.factions = {}

        mock_world = MockWorld()

        success = pm.save_world_state(world=mock_world, save_name="markov_test")

        if success:
            print("   ✅ Successfully saved world state with Markov data")
        else:
            print("   ❌ Failed to save world state")

        # Load it back
        loaded_data = pm.load_world_state("markov_test")
        if loaded_data and "markov" in loaded_data:
            print("   ✅ Successfully loaded world state with Markov data")
            print(f"   📊 Markov data contains: {list(loaded_data['markov'].keys())}")
        else:
            print("   ❌ Failed to load world state or missing Markov data")

    except Exception as e:
        print(f"   ❌ Error during world state persistence: {e}")

    # Cleanup
    print("\n7. Cleaning up test files...")
    test_files = [test_file, "test_persistence/world_state_markov_test.json"]
    for file_path in test_files:
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                print(f"   ✅ Cleaned up {file_path}")
        except Exception as e:
            print(f"   ⚠️ Could not clean up {file_path}: {e}")

    # Remove test directory if empty
    try:
        if os.path.exists("test_persistence") and not os.listdir("test_persistence"):
            os.rmdir("test_persistence")
            print("   ✅ Cleaned up test directory")
    except Exception:
        pass

    print("\n✅ Markov persistence and learning system test completed!")


if __name__ == "__main__":
    test_markov_persistence_and_learning()
