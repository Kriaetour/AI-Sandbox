#!/usr/bin/env python3
"""
Simple population decline test without parallelism to see the full decline pattern.
"""

import sys
import os

# Add the main directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from world.engine import WorldEngine
from factions.faction import Faction
from npcs.npc import NPC
import random


def simple_population_test():
    """Simple test without parallelism to track population changes."""
    print("Running simple population test...")

    # Set up a minimal world simulation
    random.seed(42)
    world = WorldEngine(seed=42)

    # Disable parallelism to avoid crashes
    world.use_parallelism = False

    # Create two factions with initial populations
    faction_a = Faction(name="TestA", territory=[(0, 0)])
    faction_b = Faction(name="TestB", territory=[(1, 1)])

    world.factions["TestA"] = faction_a
    world.factions["TestB"] = faction_b

    # Initial population setup
    initial_pop_per_faction = 5  # Smaller initial pop to avoid explosive growth
    for faction_name, faction in [("TestA", faction_a), ("TestB", faction_b)]:
        territory = faction.territory[0] if faction.territory else (0, 0)
        for i in range(initial_pop_per_faction):
            npc = NPC(
                name=f"{faction_name}_initial_{i}",
                coordinates=territory,
                faction_id=faction_name,
            )
            faction.add_member(npc.name)
            world.get_chunk(*territory).npcs.append(npc)
            world.activate_chunk(*territory)

    print(
        f"Initial setup: {len(faction_a.npc_ids)} + {len(faction_b.npc_ids)} = {len(faction_a.npc_ids) + len(faction_b.npc_ids)} total NPCs"
    )

    # Track key metrics over time
    previous_pop = len(faction_a.npc_ids) + len(faction_b.npc_ids)

    # Run simulation for moderate time to see pattern
    total_ticks = 1000

    for tick in range(total_ticks):
        try:
            # World tick
            world.world_tick()

            # Log every 50 ticks
            if tick % 50 == 0 or tick == total_ticks - 1:
                total_pop = sum(len(f.npc_ids) for f in world.factions.values())
                total_food = sum(f.resources.get("food", 0) for f in world.factions.values())

                # Get birth/death stats
                births = getattr(world, "_audit_births_tick", 0)
                starv_deaths = getattr(world, "_audit_starvation_deaths_tick", 0)
                natural_deaths = getattr(world, "_audit_natural_deaths_tick", 0)

                # Calculate population change
                pop_change = total_pop - previous_pop
                previous_pop = total_pop

                print(
                    f"[TICK {tick:4d}] Pop: {total_pop:3d} ({pop_change:+3d}) | Food: {total_food:6.1f} | B/D: {births}/{starv_deaths + natural_deaths}"
                )

                # Check for extreme population drops
                if total_pop < initial_pop_per_faction:
                    print("  🚨 Population dropped below initial level!")
                    break

                # Check starvation pressure
                for name, faction in world.factions.items():
                    pressure = getattr(faction, "_starvation_pressure", 0.0)
                    if pressure > 2.0:
                        print(f"  ⚠️  {name} high starvation pressure: {pressure:.2f}")

            # Reset per-tick counters
            world._audit_births_tick = 0
            world._audit_starvation_deaths_tick = 0
            world._audit_natural_deaths_tick = 0

        except Exception as e:
            print(f"Error at tick {tick}: {e}")
            break

    final_pop = sum(len(f.npc_ids) for f in world.factions.values())
    print(f"\nFinal population: {final_pop} (started with {initial_pop_per_faction * 2})")

    # Check balance parameters
    print("\nCurrent balance parameters:")
    for key, value in world.balance_params.items():
        if "STARV" in key or "REPRO" in key or "FOOD" in key:
            print(f"  {key}: {value}")


if __name__ == "__main__":
    simple_population_test()
