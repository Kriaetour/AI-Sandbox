#!/usr/bin/env python3
"""
Test script to verify Markov-based tribal decision integration
"""
import sys
import os

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from markov_behavior import make_markov_choice, global_tribal_markov


def test_markov_integration():
    """Test the Markov chain integration for tribal decisions."""

    print("Testing Markov-based tribal decision-making...")

    # Test diplomatic decisions
    print("\n1. Testing diplomatic decisions:")
    diplomatic_context = {
        "trust_level": 0.8,
        "relationship": "friendly",
        "traits": ["peaceful", "generous"],
        "recent_events": [],
    }

    diplomatic_actions = [
        "cultural_exchange",
        "trade_proposal",
        "alliance_proposal",
        "gift_giving",
    ]
    choice = global_tribal_markov.make_diplomatic_decision(diplomatic_context, diplomatic_actions)
    print(f"   High trust friendly context -> {choice}")

    # Test resource decisions
    print("\n2. Testing resource decisions:")
    resource_context = {
        "season": "winter",
        "resource_abundance": 0.2,
        "economic_specialization": "hunter-gatherer",
        "traits": ["aggressive"],
    }

    resource_actions = [
        "resource_hoarding",
        "cautious_trade",
        "territory_expansion",
        "aggressive_gathering",
    ]
    choice = global_tribal_markov.make_resource_decision(resource_context, resource_actions)
    print(f"   Winter scarcity context -> {choice}")

    # Test conflict decisions
    print("\n3. Testing conflict decisions:")
    conflict_context = {
        "conflict_intensity": "major",
        "military_strength": 0.9,
        "culture_type": "warrior",
        "traits": ["aggressive"],
    }

    conflict_actions = ["show_of_force", "escalation", "warfare", "diplomatic_talk"]
    choice = global_tribal_markov.make_conflict_decision(conflict_context, conflict_actions)
    print(f"   Major conflict strong warrior context -> {choice}")

    # Test cultural decisions
    print("\n4. Testing cultural decisions:")
    cultural_context = {
        "stability": "stable",
        "season": "spring",
        "recent_conflicts": 0,
        "cultural_focus": "artistic",
    }

    cultural_actions = [
        "artistic_focus",
        "cultural_flowering",
        "knowledge_sharing",
        "ritual_innovation",
    ]
    choice = global_tribal_markov.make_cultural_decision(cultural_context, cultural_actions)
    print(f"   Stable peaceful artistic context -> {choice}")

    # Test generic make_markov_choice function
    print("\n5. Testing generic Markov choice:")
    simple_options = ["option_a", "option_b", "option_c"]
    choice = make_markov_choice(simple_options, "test_context", "diplomatic")
    print(f"   Generic choice -> {choice}")

    print("\n✅ All Markov integration tests completed successfully!")


if __name__ == "__main__":
    test_markov_integration()
