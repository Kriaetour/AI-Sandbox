#!/usr/bin/env python3
"""
Controlled population wave test with reduced fertility to see realistic fluctuations.
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from world.engine import WorldEngine
from factions.faction import Faction
from npcs.npc import NPC
import logging
import time


def test_controlled_population_waves():
    """Test population waves with more reasonable birth rates."""
    # Configure logging to show fewer birth messages
    logging.basicConfig(level=logging.WARNING)

    print("Testing Controlled Population Wave System...")
    print("=" * 50)

    # Create world with waves enabled
    world = WorldEngine()
    start_time = time.time()

    # Temporarily adjust birth rates to be much more conservative
    world.balance_params = getattr(world, "balance_params", {})
    world.balance_params.update(
        {
            "LOW_POP_REPRO_MULT": 1.2,  # Reduced from 1.5
            "FOOD_PER_DAY_PER_NPC": 2.0,  # Increased food requirement
        }
    )

    print("Wave Configuration:")
    print(f"  Resource Wave Period: {getattr(world, 'abundance_cycle_length', 'N/A')} ticks")
    print(f"  Fertility Wave Period: {getattr(world, 'fertility_wave_length', 'N/A')} ticks")
    print(f"  Mortality Wave Period: {getattr(world, 'mortality_wave_length', 'N/A')} ticks")
    print()

    # Create test faction with limited resources
    faction = Faction(name="TestWaveFaction")
    world.factions["TestWaveFaction"] = faction

    # Spawn fewer initial NPCs
    world.activate_chunk(0, 0)
    spawn_count = 2  # Smaller starting population for speed

    for i in range(spawn_count):
        npc = NPC(name=f"wave_test_{i}", coordinates=(0, 0), faction_id="TestWaveFaction")
        npc.age = 30  # Younger, fertile age
        chunk = world.active_chunks[(0, 0)]
        chunk.npcs.append(npc)
        faction.npc_ids.add(npc.name)

    # Add some initial resources but not excessive
    faction.resources["food"] = 20.0  # Minimal initial resources
    faction.territory = [(0, 0)]

    # Add some resources to the chunk
    chunk = world.active_chunks[(0, 0)]
    chunk.resources["food"] = 40.0  # Reduced resources for faster test

    # Run simulation and track population over time
    total_ticks = 400  # Reduced for faster test
    populations = []
    wave_data = []

    print(f"Running controlled simulation for {total_ticks} ticks...")
    print("Tick | Pop | Food | Resource | Fertility | Mortality | Status")
    print("-" * 75)

    start_time = time.time()

    for tick in range(total_ticks):
        # Timeout check: fail if test takes too long (e.g., 30 seconds)
        if time.time() - start_time > 30:
            raise TimeoutError("test_controlled_population_waves exceeded 30 seconds; possible infinite loop or hang.")
        # Capture wave multipliers
        try:
            resource_mult = world.calculate_resource_wave_multiplier()
            fertility_mult = world.calculate_fertility_wave_multiplier()
            mortality_mult = world.calculate_mortality_wave_multiplier()
        except Exception:
            resource_mult = fertility_mult = mortality_mult = 1.0

        # Run simulation step
        world.world_tick()

        # Track population
        current_pop = len(faction.npc_ids)
        current_food = faction.resources.get("food", 0.0)
        populations.append(current_pop)
        wave_data.append(
            {
                "tick": tick,
                "population": current_pop,
                "food": current_food,
                "resource_mult": resource_mult,
                "fertility_mult": fertility_mult,
                "mortality_mult": mortality_mult,
            }
        )

        # Print status every 100 ticks or when population changes significantly
        if tick % 100 == 0 or (tick > 0 and abs(current_pop - populations[-2]) > 1):
            # Determine status based on wave multipliers
            status = ""
            if resource_mult > 1.2:
                status += "Abundant "
            elif resource_mult < 0.8:
                status += "Scarce "
            if fertility_mult > 1.2:
                status += "Fertile "
            elif fertility_mult < 0.8:
                status += "Infertile "
            if mortality_mult > 1.2:
                status += "Deadly"
            elif mortality_mult < 0.8:
                status += "Safe"

            print(
                f"{tick:4d} | {current_pop:3d} | {current_food:4.0f} | {resource_mult:8.3f} | {fertility_mult:9.3f} | {mortality_mult:9.3f} | {status}"
            )

    elapsed = time.time() - start_time
    print()
    print(f"Simulation completed in {elapsed:.2f} seconds")
    print()

    # Analyze results
    final_pop = len(faction.npc_ids)
    min_pop = min(populations)
    max_pop = max(populations)
    avg_pop = sum(populations) / len(populations)

    print("Population Statistics:")
    print(f"  Initial Population: {spawn_count}")
    print(f"  Final Population: {final_pop}")
    print(f"  Minimum Population: {min_pop}")
    print(f"  Maximum Population: {max_pop}")
    print(f"  Average Population: {avg_pop:.1f}")
    print(f"  Population Range: {max_pop - min_pop}")
    print()

    # Check for wave effects
    wave_range_resource = max(d["resource_mult"] for d in wave_data) - min(
        d["resource_mult"] for d in wave_data
    )
    wave_range_fertility = max(d["fertility_mult"] for d in wave_data) - min(
        d["fertility_mult"] for d in wave_data
    )
    wave_range_mortality = max(d["mortality_mult"] for d in wave_data) - min(
        d["mortality_mult"] for d in wave_data
    )

    print("Wave Multiplier Ranges:")
    print(f"  Resource Wave Range: {wave_range_resource:.3f}")
    print(f"  Fertility Wave Range: {wave_range_fertility:.3f}")
    print(f"  Mortality Wave Range: {wave_range_mortality:.3f}")
    print()

    # Check for population fluctuations over time windows
    window_size = 200
    fluctuations = []
    for i in range(0, len(populations) - window_size, window_size):
        window = populations[i : i + window_size]
        fluctuation = max(window) - min(window)
        fluctuations.append(fluctuation)

    avg_fluctuation = sum(fluctuations) / len(fluctuations) if fluctuations else 0
    print(f"Average Population Fluctuation per {window_size}-tick window: {avg_fluctuation:.1f}")

    # Success criteria
    success = True

    if wave_range_resource < 0.5:
        print("WARNING: Resource wave range seems too small")
        success = False

    if max_pop - min_pop < 2:
        print("WARNING: Population fluctuation seems too small for wave effects")
        success = False

    if avg_fluctuation < 1:
        print("WARNING: Population doesn't seem to be fluctuating much")
        success = False

    if success:
        print("✅ Population wave system appears to be working correctly!")
    else:
        print("❌ Population wave system may need tuning")

    # --- Matplotlib Visualization ---
        # Skip plotting in test context for speed

    return success


if __name__ == "__main__":
    test_controlled_population_waves()
