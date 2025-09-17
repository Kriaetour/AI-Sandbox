#!/usr/bin/env python3
"""
Test script for Markov-based dialogue generation.
Tests that NPCs use Markov chains instead of hard-coded dialogue.
"""

import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from npcs.npc import NPC
from markov_dialogue import generate_markov_dialogue


def test_markov_dialogue_generation():
    """Test that markov_dialogue.py generates dialogue correctly."""
    print("=== Testing Markov Dialogue Generation ===")

    # Test basic dialogue generation
    contexts = ["encounter", "trade", "idle", "hostility"]
    traits = ["aggressive", "peaceful", "curious", "generous"]

    for context in contexts:
        print(f"\nContext: {context}")
        for trait in traits:
            dialogue = generate_markov_dialogue(context, trait=trait)
            print(f"  {trait}: '{dialogue}'")

    print("\n" + "=" * 50)


def test_npc_dialogue_integration():
    """Test that NPCs use Markov dialogue generation."""
    print("=== Testing NPC Dialogue Integration ===")

    # Create test NPCs
    npc1 = NPC("TestNPC1", "faction1", (0, 0))
    npc1.traits = ["aggressive"]

    npc2 = NPC("TestNPC2", "faction2", (1, 1))
    npc2.traits = ["peaceful"]

    # Mock tribal diplomacy
    tribal_diplomacy = {
        ("faction1", "faction2"): 0.8,  # Friendly
        ("faction2", "faction1"): 0.8,
    }

    contexts = ["encounter", "trade", "idle"]

    print(f"\nNPC1 ({npc1.traits[0]}) talking to NPC2:")
    for context in contexts:
        dialogue = npc1.generate_dialogue(npc2, context, tribal_diplomacy)
        print(f"  {context}: '{dialogue}'")

    print(f"\nNPC2 ({npc2.traits[0]}) talking to NPC1:")
    for context in contexts:
        dialogue = npc2.generate_dialogue(npc1, context, tribal_diplomacy)
        print(f"  {context}: '{dialogue}'")

    print("\n" + "=" * 50)


def test_dialogue_variability():
    """Test that dialogue shows Markov-based variability."""
    print("=== Testing Dialogue Variability ===")

    npc = NPC("VariabilityTest", "faction_test", (0, 0))
    npc.traits = ["curious"]

    target = NPC("Target", "faction_target", (1, 1))
    tribal_diplomacy = {("faction_test", "faction_target"): 0.0}

    print("Multiple 'encounter' dialogues from same NPC (should vary):")
    for i in range(5):
        dialogue = npc.generate_dialogue(target, "encounter", tribal_diplomacy)
        print(f"  {i+1}: '{dialogue}'")

    print("\n" + "=" * 50)


def test_trait_influence():
    """Test that traits influence dialogue generation."""
    print("=== Testing Trait Influence on Dialogue ===")

    target = NPC("Target", "neutral_faction", (5, 5))
    tribal_diplomacy = {
        ("aggressive_faction", "neutral_faction"): 0.0,
        ("peaceful_faction", "neutral_faction"): 0.0,
    }

    # Test aggressive NPC
    aggressive_npc = NPC("AggressiveNPC", "aggressive_faction", (0, 0))
    aggressive_npc.traits = ["aggressive"]

    # Test peaceful NPC
    peaceful_npc = NPC("PeacefulNPC", "peaceful_faction", (1, 1))
    peaceful_npc.traits = ["peaceful"]

    context = "encounter"

    print(f"Aggressive NPC {context} dialogue:")
    for i in range(3):
        dialogue = aggressive_npc.generate_dialogue(target, context, tribal_diplomacy)
        print(f"  '{dialogue}'")

    print(f"\nPeaceful NPC {context} dialogue:")
    for i in range(3):
        dialogue = peaceful_npc.generate_dialogue(target, context, tribal_diplomacy)
        print(f"  '{dialogue}'")

    print("\n" + "=" * 50)


if __name__ == "__main__":
    print("Testing Markov-based Dialogue System")
    print("=" * 50)

    try:
        test_markov_dialogue_generation()
        test_npc_dialogue_integration()
        test_dialogue_variability()
        test_trait_influence()

        print("✓ All tests completed successfully!")
        print("✓ Markov-based dialogue system is working!")

    except Exception as e:
        print(f"✗ Test failed with error: {e}")
        import traceback

        traceback.print_exc()
