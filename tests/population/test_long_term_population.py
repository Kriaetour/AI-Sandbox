#!/usr/bin/env python3
"""
Long-term population stability test for 5000 ticks to verify the fix.
"""

import sys
import os

# Add the main directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from world.engine import WorldEngine
from factions.faction import Faction
from npcs.npc import NPC
import random


def long_term_population_test():
    """Test population stability over 5000 ticks."""
    print("Running long-term population stability test (5000 ticks)...")

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
    initial_pop_per_faction = 5
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
    population_history = []

    # Run simulation for 5000 ticks
    total_ticks = 5000

    for tick in range(total_ticks):
        try:
            # World tick
            world.world_tick()

            # Log every 250 ticks
            if tick % 250 == 0 or tick == total_ticks - 1:
                total_pop = sum(len(f.npc_ids) for f in world.factions.values())
                total_food = sum(f.resources.get("food", 0) for f in world.factions.values())

                # Get birth/death stats
                births = getattr(world, "_audit_births_tick", 0)
                starv_deaths = getattr(world, "_audit_starvation_deaths_tick", 0)
                natural_deaths = getattr(world, "_audit_natural_deaths_tick", 0)

                population_history.append(
                    {
                        "tick": tick,
                        "population": total_pop,
                        "food": total_food,
                        "births": births,
                        "deaths": starv_deaths + natural_deaths,
                    }
                )

                print(
                    f"[TICK {tick:4d}] Pop: {total_pop:3d} | Food: {total_food:8.1f} | B/D: {births}/{starv_deaths + natural_deaths}"
                )

                # Check for population collapse
                if total_pop < 5:
                    print(f"  🚨 Population collapsed to {total_pop}!")
                    break

            # Reset per-tick counters
            world._audit_births_tick = 0
            world._audit_starvation_deaths_tick = 0
            world._audit_natural_deaths_tick = 0

        except Exception as e:
            print(f"Error at tick {tick}: {e}")
            break

    # Analyze results
    final_pop = population_history[-1]["population"]
    initial_pop = initial_pop_per_faction * 2

    print(f"\n{'='*60}")
    print("LONG-TERM STABILITY ANALYSIS:")
    print(f"{'='*60}")
    print(f"Initial population: {initial_pop}")
    print(f"Final population: {final_pop}")
    print(
        f"Population change: {final_pop - initial_pop:+d} ({((final_pop/initial_pop - 1) * 100):+.1f}%)"
    )

    # Check for stability
    if len(population_history) >= 4:
        recent_pops = [entry["population"] for entry in population_history[-4:]]
        pop_variance = max(recent_pops) - min(recent_pops)
        avg_recent_pop = sum(recent_pops) / len(recent_pops)

        print(
            f"Recent population range: {min(recent_pops)} - {max(recent_pops)} (variance: {pop_variance})"
        )
        print(f"Recent average population: {avg_recent_pop:.1f}")

        # Check stability criteria
        if pop_variance < avg_recent_pop * 0.1:  # Less than 10% variance
            print("✅ Population is STABLE (low variance)")
        elif pop_variance < avg_recent_pop * 0.2:  # Less than 20% variance
            print("⚠️  Population is MODERATELY STABLE")
        else:
            print("❌ Population is UNSTABLE (high variance)")

    # Check if population survived
    if final_pop >= 20:
        print("✅ Population SURVIVED 5000 ticks")
    else:
        print("❌ Population DID NOT SURVIVE (below 20)")

    return population_history


if __name__ == "__main__":
    long_term_population_test()
