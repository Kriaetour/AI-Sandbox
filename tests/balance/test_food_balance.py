#!/usr/bin/env python3
"""
Test food balance after fixing resource regeneration rates.
"""

import sys
import os

# Add the main directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from world.engine import WorldEngine
from factions.faction import Faction
from npcs.npc import NPC
import random


def test_food_balance():
    """Test that food production and consumption are balanced."""
    print("Testing food balance after resource regeneration fixes...")

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

    # Track food production vs consumption
    food_history = []

    # Run simulation for longer time to see food balance over time
    total_ticks = 2000

    for tick in range(total_ticks):
        try:
            # World tick
            world.world_tick()

            # Log every 100 ticks
            if tick % 100 == 0 or tick == total_ticks - 1:
                total_pop = sum(len(f.npc_ids) for f in world.factions.values())
                total_food = sum(f.resources.get("food", 0) for f in world.factions.values())

                # Calculate theoretical consumption
                food_per_day = 1.0
                ticks_per_day = 1440
                food_consumption_per_tick = (food_per_day / ticks_per_day) * total_pop

                food_history.append(
                    {
                        "tick": tick,
                        "population": total_pop,
                        "food": total_food,
                        "consumption_per_tick": food_consumption_per_tick,
                    }
                )

                print(
                    f"[TICK {tick:4d}] Pop: {total_pop:3d} | Food: {total_food:7.1f} | Consumption/tick: {food_consumption_per_tick:.3f}"
                )

            # Reset per-tick counters
            world._audit_births_tick = 0
            world._audit_starvation_deaths_tick = 0
            world._audit_natural_deaths_tick = 0

        except Exception as e:
            print(f"Error at tick {tick}: {e}")
            break

    # Analyze food balance
    print(f"\n{'='*60}")
    print("FOOD BALANCE ANALYSIS:")
    print(f"{'='*60}")

    if len(food_history) >= 3:
        start_food = food_history[1]["food"]  # Skip tick 0 due to initialization
        end_food = food_history[-1]["food"]
        food_change = end_food - start_food
        ticks_elapsed = food_history[-1]["tick"] - food_history[1]["tick"]
        food_change_per_tick = food_change / ticks_elapsed if ticks_elapsed > 0 else 0

        final_pop = food_history[-1]["population"]
        final_consumption = food_history[-1]["consumption_per_tick"]

        print(f"Initial food (tick {food_history[1]['tick']}): {start_food:.1f}")
        print(f"Final food (tick {food_history[-1]['tick']}): {end_food:.1f}")
        print(f"Food change: {food_change:+.1f} over {ticks_elapsed} ticks")
        print(f"Food change per tick: {food_change_per_tick:+.3f}")
        print(f"Final population: {final_pop}")
        print(f"Final consumption per tick: {final_consumption:.3f}")

        # Calculate net balance
        net_balance = food_change_per_tick + final_consumption  # Production - consumption
        print(f"Net production per tick: {net_balance:.3f}")

        # Check balance quality
        if abs(net_balance) < 0.5:
            print("✅ Food production and consumption are WELL BALANCED")
        elif abs(net_balance) < 1.5:
            print("⚠️  Food production and consumption are MODERATELY BALANCED")
        elif net_balance > 3.0:
            print("❌ Food production is EXCESSIVE (still exploding)")
        else:
            print("⚠️  Food production is moderately higher than consumption")

        # Check food stability
        recent_foods = [entry["food"] for entry in food_history[-3:]]
        food_variance = max(recent_foods) - min(recent_foods)
        avg_recent_food = sum(recent_foods) / len(recent_foods)

        if food_variance < avg_recent_food * 0.1:
            print("✅ Food levels are STABLE")
        else:
            print("⚠️  Food levels are fluctuating")

    return food_history


if __name__ == "__main__":
    test_food_balance()
