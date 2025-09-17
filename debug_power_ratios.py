#!/usr/bin/env python3
"""
Debug script to analyze power ratios and state discretization during training.
"""

import random
import numpy as np

from world.engine import WorldEngine
from tribes.tribal_manager import TribalManager
from rl_military_agent import MilitaryRLAgent


def debug_power_ratios():
    """Debug power ratio calculations to understand state discretization."""

    print("DEBUGGING POWER RATIOS AND STATE DISCRETIZATION")
    print("=" * 60)

    # Create a test scenario
    world_seed = random.randint(0, 100000)
    world = WorldEngine(seed=world_seed, disable_faction_saving=True)
    tribal_manager = TribalManager()
    world._tribal_manager = tribal_manager

    agent = MilitaryRLAgent(epsilon=0.95, lr=0.2, gamma=0.9)

    # Create diverse tribes like in enhanced training
    num_tribes = 8
    tribe_info = []

    for i in range(num_tribes):
        random.seed(world_seed + i * 100)

        # Diverse tribe types
        tribe_types = [
            {"name": "Small_Village", "pop_range": (20, 100)},
            {"name": "Medium_Settlement", "pop_range": (100, 500)},
            {"name": "Large_Town", "pop_range": (500, 1200)},
            {"name": "Major_City", "pop_range": (1200, 2000)},
        ]

        tribe_type = random.choice(tribe_types)
        base_name = f"{tribe_type['name']}_{i+1}"
        location = (random.randint(-100, 100), random.randint(-100, 100))
        population = random.randint(*tribe_type['pop_range'])

        tribal_manager.create_tribe(base_name, base_name, location)

        # Create faction
        if base_name not in world.factions:
            from factions.faction import Faction
            faction = Faction(name=base_name)
            faction.territory = [location]
            faction.population = population
            faction.resources = {
                "food": random.randint(50, 800),
                "wood": random.randint(25, 600),
                "ore": random.randint(10, 400)
            }
            world.factions[base_name] = faction

        tribe_info.append((base_name, population))

    print("CREATED TRIBES:")
    for name, pop in tribe_info:
        print(f"  {name}: {pop} population")
    print()

    # Test different actor-target combinations
    active_tribes = list(tribal_manager.tribes.values())

    print("POWER RATIO ANALYSIS:")
    print("-" * 40)

    power_ratios = []
    discretized_states = []

    for i, actor_tribe in enumerate(active_tribes):
        for j, target_tribe in enumerate(active_tribes):
            if actor_tribe == target_tribe:
                continue

            # Calculate power ratio manually
            actor_power = agent._calculate_tribal_power(actor_tribe)
            target_power = agent._calculate_tribal_power(target_tribe)
            ratio = actor_power / target_power if target_power > 0 else 3.0

            # Get discretized state
            state_vector = agent.get_military_state(actor_tribe, [target_tribe], world)

            power_ratios.append(ratio)
            discretized_states.append(state_vector[0])  # power_ratio bin

            print(f"  {actor_tribe.name} ({actor_power:.1f}) vs {target_tribe.name} ({target_power:.1f})")
            print(f"    Power Ratio: {ratio:.3f} -> Bin: {state_vector[0]}")
            print(f"    Full State: {state_vector}")
            print()

    print("SUMMARY:")
    print(f"  Power Ratios Range: {min(power_ratios):.3f} - {max(power_ratios):.3f}")
    print(f"  Unique Power Ratio Bins: {len(set(discretized_states))}")
    print(f"  Most Common Bin: {max(set(discretized_states), key=discretized_states.count)}")

    # Show bin ranges
    print("\nPOWER RATIO BIN RANGES:")
    bins = np.linspace(0.0, 3.0, 15)
    for i in range(len(bins)-1):
        print(f"  Bin {i}: {bins[i]:.3f} - {bins[i+1]:.3f}")


if __name__ == "__main__":
    debug_power_ratios()