#!/usr/bin/env python3
"""
Population decline diagnostic test to understand what's causing population to drop to 20 after 5000 ticks.
"""

import sys
import os

# Add the main directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from world.engine import WorldEngine
from factions.faction import Faction
from npcs.npc import NPC
import random


def test_population_decline_diagnostic():
    """Run a focused diagnostic to understand population decline over time."""
    print("Running population decline diagnostic...")

    # Set up a minimal world simulation
    random.seed(42)
    world = WorldEngine(seed=42)

    # Create two factions with initial populations
    faction_a = Faction(name="TestA", territory=[(0, 0)])
    faction_b = Faction(name="TestB", territory=[(1, 1)])

    world.factions["TestA"] = faction_a
    world.factions["TestB"] = faction_b

    # Initial population setup
    initial_pop_per_faction = 10
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
    diagnostic_data = []

    # Run simulation for specific ticks to see decline pattern
    test_ticks = [100, 500, 1000, 2000, 3000, 4000, 5000]

    for tick in range(max(test_ticks) + 1):
        # World tick
        world.world_tick()

        # Log detailed data at specific intervals
        if tick in test_ticks or tick % 500 == 0:
            total_pop = sum(len(f.npc_ids) for f in world.factions.values())
            total_food = sum(f.resources.get("food", 0) for f in world.factions.values())

            # Get birth/death stats from world audit
            births_this_tick = getattr(world, "_audit_births_tick", 0)
            starv_deaths_this_tick = getattr(world, "_audit_starvation_deaths_tick", 0)
            natural_deaths_this_tick = getattr(world, "_audit_natural_deaths_tick", 0)

            # Get starvation pressure for factions
            faction_data = {}
            for name, faction in world.factions.items():
                pressure = getattr(faction, "_starvation_pressure", 0.0)
                food = faction.resources.get("food", 0)
                pop = len(faction.npc_ids)
                food_per_capita = food / max(1, pop)

                # Check fertility factors
                try:
                    # Get recent economic history for capacity estimation
                    capacity_est = None
                    if hasattr(faction, "_econ_history") and faction._econ_history:
                        recent = faction._econ_history[-30:]
                        avg_dfood = sum(e.get("dFood", 0.0) for e in recent) / max(1, len(recent))
                        per_cap_need = 1.0 / 1440.0  # Default per capita need per tick
                        if avg_dfood > 0:
                            capacity_est = pop + (avg_dfood / per_cap_need)
                        else:
                            capacity_est = pop

                    faction_data[name] = {
                        "pop": pop,
                        "food": food,
                        "food_per_capita": food_per_capita,
                        "pressure": pressure,
                        "capacity_est": capacity_est,
                    }
                except Exception:
                    faction_data[name] = {
                        "pop": pop,
                        "food": food,
                        "food_per_capita": food_per_capita,
                        "pressure": pressure,
                        "capacity_est": "error",
                    }

            diagnostic_entry = {
                "tick": tick,
                "total_pop": total_pop,
                "total_food": total_food,
                "births": births_this_tick,
                "starv_deaths": starv_deaths_this_tick,
                "natural_deaths": natural_deaths_this_tick,
                "factions": faction_data,
            }

            diagnostic_data.append(diagnostic_entry)

            print(
                f"[TICK {tick:4d}] Pop: {total_pop:3d} | Food: {total_food:6.1f} | Births: {births_this_tick} | Deaths (starv/nat): {starv_deaths_this_tick}/{natural_deaths_this_tick}"
            )
            for name, data in faction_data.items():
                print(
                    f"  {name}: pop={data['pop']:2d} food={data['food']:5.1f} per_cap={data['food_per_capita']:4.1f} pressure={data['pressure']:4.2f} capacity={data['capacity_est']}"
                )

        # Reset per-tick counters
        world._audit_births_tick = 0
        world._audit_starvation_deaths_tick = 0
        world._audit_natural_deaths_tick = 0

    print(f"\n{'='*80}")
    print("DIAGNOSTIC SUMMARY:")
    print(f"{'='*80}")

    print(f"Initial population: {initial_pop_per_faction * 2}")
    print(f"Final population: {sum(len(f.npc_ids) for f in world.factions.values())}")

    # Analyze trends
    print("\nPopulation over time:")
    for entry in diagnostic_data:
        if entry["tick"] in test_ticks:
            print(f"  Tick {entry['tick']:4d}: {entry['total_pop']:3d} NPCs")

    print("\nKey Issues Identified:")
    final_entry = diagnostic_data[-1]

    # Check if food availability is the issue
    total_final_food = final_entry["total_food"]
    total_final_pop = final_entry["total_pop"]
    if total_final_pop > 0:
        final_food_per_capita = total_final_food / total_final_pop
        print(f"- Final food per capita: {final_food_per_capita:.2f}")
        if final_food_per_capita < 2.0:
            print("  ⚠️  Low food per capita may be limiting births")

    # Check birth rate trends
    recent_births = [entry for entry in diagnostic_data[-5:]]
    avg_births = sum(entry["births"] for entry in recent_births) / len(recent_births)
    avg_deaths = sum(
        entry["starv_deaths"] + entry["natural_deaths"] for entry in recent_births
    ) / len(recent_births)

    print(f"- Recent average births per tick: {avg_births:.2f}")
    print(f"- Recent average deaths per tick: {avg_deaths:.2f}")
    print(f"- Net population change per tick: {avg_births - avg_deaths:.2f}")

    if avg_births < avg_deaths:
        print("  🚨 Population is declining - deaths exceed births!")

    # Check starvation pressure
    max_pressure = 0
    for entry in diagnostic_data:
        for faction_data in entry["factions"].values():
            if isinstance(faction_data["pressure"], (int, float)):
                max_pressure = max(max_pressure, faction_data["pressure"])

    print(f"- Maximum starvation pressure observed: {max_pressure:.2f}")
    if max_pressure > 3.0:
        print("  ⚠️  High starvation pressure detected")

    return diagnostic_data


if __name__ == "__main__":
    test_population_decline_diagnostic()
