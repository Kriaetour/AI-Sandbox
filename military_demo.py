#!/usr/bin/env python3
"""
Military RL Agent Demo: Demonstrate the military decision-making framework.

This script shows how the Military RL Agent analyzes situations and makes strategic decisions.
"""

from rl_military_agent import MilitaryRLAgent
from rl_military_interface import get_military_actions
from tribes.tribe import Tribe


def create_demo_tribes():
    """Create demo tribes with different characteristics."""
    # Create basic tribe
    basic_tribe = Tribe("Basic Tribe", (0, 0))
    basic_tribe.id = "basic_tribe"
    basic_tribe.population = 100

    # Create advanced tribe with technology
    advanced_tribe = Tribe("Advanced Tribe", (5, 5))
    advanced_tribe.id = "advanced_tribe"
    advanced_tribe.population = 120

    # Create elite tribe with superior technology
    elite_tribe = Tribe("Elite Tribe", (10, 10))
    elite_tribe.id = "elite_tribe"
    elite_tribe.population = 80

    return basic_tribe, advanced_tribe, elite_tribe


def demo_military_analysis():
    """Demonstrate military analysis capabilities."""
    print("🎖️  Military RL Agent Strategic Analysis Demo")
    print("=" * 60)

    # Create agent and tribes
    agent = MilitaryRLAgent()
    basic_tribe, advanced_tribe, elite_tribe = create_demo_tribes()

    # Add some technology to tribes (simulating unlocked technologies)
    from technology_system import technology_manager

    # Basic tribe: basic weapons
    technology_manager.unlocked_technologies["basic_tribe"] = {"tools", "weapons"}

    # Advanced tribe: iron weapons and military organization
    technology_manager.unlocked_technologies["advanced_tribe"] = {
        "tools", "weapons", "iron_weapons", "military_organization"
    }

    # Elite tribe: steel weapons and advanced military tech
    technology_manager.unlocked_technologies["elite_tribe"] = {
        "tools", "weapons", "iron_weapons", "steel_weapons",
        "military_organization", "siege_engineering"
    }

    print("\n🏹 TRIBE COMPARISON:")
    tribes = [
        ("Basic Tribe", basic_tribe),
        ("Advanced Tribe", advanced_tribe),
        ("Elite Tribe", elite_tribe)
    ]

    for name, tribe in tribes:
        # Get military analysis
        analysis = agent.get_military_analysis(tribe, [])

        print(f"\n{name}:")
        print(f"  Population: {tribe.population}")
        print(f"  Combat Bonus: +{analysis['technology_level']*100:.1f}%")
        print(f"  Force Readiness: {analysis['force_readiness']:.1f}")
        print(f"  Recommended Action: {analysis['action_name']}")

    print("\n⚔️  COMBAT SCENARIOS:")
    print("-" * 40)

    # Scenario 1: Basic vs Advanced
    print("\n📊 Scenario 1: Basic Tribe vs Advanced Tribe")
    state = agent.get_military_state(basic_tribe, [advanced_tribe])
    action = agent.choose_action(state)
    print(f"Basic Tribe (power ratio: ~{0.8:.1f}) → {agent.get_action_name(action)}")

    # Scenario 2: Advanced vs Elite
    print("\n📊 Scenario 2: Advanced Tribe vs Elite Tribe")
    state = agent.get_military_state(advanced_tribe, [elite_tribe])
    action = agent.choose_action(state)
    print(f"Advanced Tribe (power ratio: ~{1.2:.1f}) → {agent.get_action_name(action)}")

    # Scenario 3: Elite vs Basic
    print("\n📊 Scenario 3: Elite Tribe vs Basic Tribe")
    state = agent.get_military_state(elite_tribe, [basic_tribe])
    action = agent.choose_action(state)
    print(f"Elite Tribe (power ratio: ~{1.8:.1f}) → {agent.get_action_name(action)}")

    print("\n🎯 MILITARY ACTIONS AVAILABLE:")
    actions = get_military_actions()
    for i, action in enumerate(actions, 1):
        print(f"{i}. {action}")

    print("\n📈 TRAINING READY:")
    print("The Military RL Agent is ready for training with:")
    print(f"• {len(agent.state_bins)} state dimensions")
    print(f"• {len(actions)} possible actions")
    print("• Technology integration with combat bonuses")
    print("• Strategic decision-making framework")

    print("\n🚀 NEXT STEPS:")
    print("1. Run training: python train_military_rl.py --episodes 100")
    print("2. Integrate with main simulation")
    print("3. Add real-time military coordination")
    print("4. Expand with diplomacy integration")

    print("\n🎖️  Military RL Agent Demo Complete!")


if __name__ == "__main__":
    demo_military_analysis()