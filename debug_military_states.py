#!/usr/bin/env python3
"""
Debug Military State Generation
"""

import random
from world.engine import WorldEngine
from tribes.tribal_manager import TribalManager
from rl_military_agent import MilitaryRLAgent
from factions import Faction

def debug_state_generation():
    """Debug why states aren't being learned."""
    print("🔍 Debugging Military State Generation")
    print("=" * 50)

    # Create a simple scenario
    world_seed = random.randint(0, 10000000)
    world = WorldEngine(seed=world_seed, disable_faction_saving=True)
    tribal_manager = TribalManager()
    world._tribal_manager = tribal_manager

    # Create agent
    agent = MilitaryRLAgent(epsilon=0.1, lr=0.1, gamma=0.95)

    # Create some tribes
    num_tribes = 5
    tribes = []

    for i in range(num_tribes):
        # Create faction first
        faction_name = f"TestTribe_{i}"
        faction = Faction(
            name=faction_name,
            resources={
                'food': random.randint(100, 1000),
                'Wood': random.randint(100, 1000),
                'Ore': random.randint(50, 500),
            }
        )
        # Add population as an attribute
        faction.population = random.randint(50, 500)
        world.factions[faction_name] = faction

        # Create tribe
        tribe = tribal_manager.create_tribe(faction_name, world)
        tribes.append(tribe)

        print(f"Created tribe: {tribe.name} with faction: {faction_name}")
        print(f"  Population: {faction.population}")
        print(f"  Tribe ID: {getattr(tribe, 'id', 'No ID')}")

    # Test state generation
    print("\n🧪 Testing State Generation:")
    print("-" * 30)

    for i, actor_tribe in enumerate(tribes):
        enemy_tribes = [t for t in tribes if t != actor_tribe]

        if enemy_tribes:
            print(f"\nActor: {actor_tribe.name}")
            print(f"Enemies: {[t.name for t in enemy_tribes]}")

            # Test power calculation
            power = agent._calculate_tribal_power(actor_tribe)
            print(f"Power: {power}")

            # Test state generation
            state = agent.get_military_state(actor_tribe, enemy_tribes, world)
            print(f"State: {state}")

            # Check if state is in Q-table
            in_q_table = state in agent.q_table
            print(f"State in Q-table: {in_q_table}")

            if in_q_table:
                print(f"Q-values: {agent.q_table[state]}")

    # Test action selection and Q-update
    print("\n🎯 Testing Action Selection & Learning:")
    print("-" * 40)

    actor_tribe = tribes[0]
    enemy_tribes = tribes[1:3]

    # Generate state
    state = agent.get_military_state(actor_tribe, enemy_tribes, world)
    print(f"Initial state: {state}")

    # Choose action
    action = agent.choose_action(state)
    print(f"Chosen action: {action} ({agent.action_names[action]})")

    # Simulate reward
    reward = random.uniform(-10, 10)
    print(f"Simulated reward: {reward}")

    # Generate next state
    next_state = agent.get_military_state(actor_tribe, enemy_tribes, world)
    print(f"Next state: {next_state}")

    # Update Q-table
    agent.update_q_table(state, action, reward, next_state)
    print(f"Q-table updated for state: {state}")

    # Check if state is now in Q-table
    print(f"State in Q-table after update: {state in agent.q_table}")
    if state in agent.q_table:
        print(f"Updated Q-values: {agent.q_table[state]}")

    print(f"\nTotal states in Q-table: {len(agent.q_table)}")

if __name__ == "__main__":
    debug_state_generation()