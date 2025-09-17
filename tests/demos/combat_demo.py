#!/usr/bin/env python3
"""
Demo script for testing the enhanced combat system.
Shows combat statistics and detailed combat mechanics.
"""

from enhanced_combat import EnhancedCombatManager, CombatType


class MockTribe:
    """Mock tribe for testing combat system."""

    def __init__(self, name, population=30, location=(0, 0)):
        self.name = name
        self.population = population
        self.location = location
        self.shared_resources = {"food": 100, "materials": 50}
        self.members = {f"member_{i}": f"role_{i}" for i in range(population)}

    def add_tribal_memory(self, event_type, data):
        print(f"  {self.name} remembers {event_type}: {data}")


def demo_enhanced_combat():
    """Demonstrate the enhanced combat system."""
    print("=== ENHANCED COMBAT SYSTEM DEMO ===")

    combat_manager = EnhancedCombatManager()

    # Create mock tribes
    tribe_a = MockTribe("Mountain Warriors", population=35, location=(5, 5))
    tribe_b = MockTribe("River Hunters", population=28, location=(3, 7))

    print(f"\nTribe A: {tribe_a.name} (Population: {tribe_a.population})")
    print(f"  Resources: {tribe_a.shared_resources}")
    print(f"Tribe B: {tribe_b.name} (Population: {tribe_b.population})")
    print(f"  Resources: {tribe_b.shared_resources}")

    # Test different combat scenarios
    scenarios = [
        {
            "type": CombatType.SKIRMISH,
            "weather": "CLEAR",
            "time": {"hour": 10, "season": 1, "is_day": True},
            "description": "Small border skirmish during clear summer day",
        },
        {
            "type": CombatType.RAID,
            "weather": "RAIN",
            "time": {"hour": 2, "season": 0, "is_day": False},
            "description": "Night raid during spring rain",
        },
        {
            "type": CombatType.BATTLE,
            "weather": "STORM",
            "time": {"hour": 14, "season": 3, "is_day": True},
            "description": "Major battle during winter storm",
        },
        {
            "type": CombatType.SIEGE,
            "weather": "CLEAR",
            "time": {"hour": 8, "season": 2, "is_day": True},
            "description": "Siege warfare during autumn",
        },
    ]

    for i, scenario in enumerate(scenarios, 1):
        print(f"\n--- COMBAT SCENARIO {i}: {scenario['description']} ---")

        world_context = {"weather": scenario["weather"], "time": scenario["time"]}

        result = combat_manager.initiate_combat(
            tribe_a, tribe_b, tribe_b.location, scenario["type"], world_context
        )

        print(f"Combat Type: {result['type']}")
        print(f"Environmental Factors: {result['environmental_factors']}")
        print(
            f"Forces - Attacker: {result['attacker_forces']['total']} | Defender: {result['defender_forces']['total']}"
        )
        print(
            f"Combat Power - Attacker: {result['attacker_power']:.1f} | Defender: {result['defender_power']:.1f}"
        )
        print(f"Result: {result['result']}")
        print(
            f"Casualties - Attacker: {sum(result['casualties']['attacker'].values())} | Defender: {sum(result['casualties']['defender'].values())}"
        )

        # Show resource impacts
        if result["resource_impacts"]:
            print("Resource Changes:")
            for side in ["attacker", "defender"]:
                if result["resource_impacts"][side]:
                    changes = []
                    for resource, change in result["resource_impacts"][side].items():
                        sign = "+" if change >= 0 else ""
                        changes.append(f"{resource}: {sign}{change:.1f}")
                    if changes:
                        print(f"  {side.title()}: {', '.join(changes)}")

    # Show overall combat statistics
    print("\n--- COMBAT STATISTICS ---")
    stats = combat_manager.get_combat_statistics()
    print(f"Total Combats: {stats['total_combats']}")
    print(f"Results Distribution: {stats['results']}")
    print(f"Average Casualties per Combat: {stats['average_casualties_per_combat']}")

    # Show tribe-specific statistics
    print("\n--- TRIBE-SPECIFIC STATISTICS ---")
    for tribe in [tribe_a, tribe_b]:
        tribe_stats = combat_manager.get_combat_statistics(tribe.name)
        print(
            f"{tribe.name}: {tribe_stats['total_combats']} combats, Results: {tribe_stats.get('results', {})}"
        )


if __name__ == "__main__":
    demo_enhanced_combat()
