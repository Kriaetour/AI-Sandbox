#!/usr/bin/env python3
"""
Test script to verify the population wave system is working correctly.
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from world.engine import WorldEngine
from factions.faction import Faction
import logging
import time


def test_population_waves():
    """Test the population wave system with a medium-length simulation."""
    # Configure logging
    logging.basicConfig(level=logging.INFO)

    print("Testing Population Wave System...")
    print("=" * 50)

    # Create world with waves enabled
    world = WorldEngine()

    # Verify wave system is enabled
    if not getattr(world, "wave_enabled", False):
        print("ERROR: Wave system not enabled!")
        return False

    print("Wave Configuration:")
    print(f"  Resource Wave Period: {getattr(world, 'abundance_cycle_length', 'N/A')} ticks")
    print(f"  Fertility Wave Period: {getattr(world, 'fertility_wave_length', 'N/A')} ticks")
    print(f"  Mortality Wave Period: {getattr(world, 'mortality_wave_length', 'N/A')} ticks")
    print(f"  Resource Wave Amplitude: {getattr(world, 'resource_wave_amplitude', 'N/A')}")
    print(f"  Fertility Wave Amplitude: {getattr(world, 'fertility_wave_amplitude', 'N/A')}")
    print(f"  Mortality Wave Amplitude: {getattr(world, 'mortality_wave_amplitude', 'N/A')}")
    print()

    # Create test faction
    faction = Faction(name="TestWaveFaction")
    world.factions["TestWaveFaction"] = faction

    # Spawn initial NPCs in a central location
    world.activate_chunk(0, 0)
    spawn_count = 20

    for i in range(spawn_count):
        from npcs.npc import NPC

        npc = NPC(name=f"wave_test_{i}", coordinates=(0, 0), faction_id="TestWaveFaction")
        npc.age = 50  # Prime age
        chunk = world.active_chunks[(0, 0)]
        chunk.npcs.append(npc)
    faction.npc_ids.add(npc.name)

    # Add faction territory
    faction.territory = [(0, 0)]

    # Run simulation and track population over time
    total_ticks = 2000  # Enough to see multiple wave cycles
    populations = []
    wave_data = []

    print(f"Running simulation for {total_ticks} ticks...")
    print("Tick | Pop | Resource Wave | Fertility Wave | Mortality Wave")
    print("-" * 65)

    start_time = time.time()

    for tick in range(total_ticks):
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
        populations.append(current_pop)
        wave_data.append(
            {
                "tick": tick,
                "population": current_pop,
                "resource_mult": resource_mult,
                "fertility_mult": fertility_mult,
                "mortality_mult": mortality_mult,
            }
        )

        # Print status every 100 ticks
        if tick % 100 == 0:
            print(
                f"{tick:4d} | {current_pop:3d} | {resource_mult:12.3f} | {fertility_mult:13.3f} | {mortality_mult:13.3f}"
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

    # Success criteria
    success = True

    if wave_range_resource < 0.5:
        print("WARNING: Resource wave range seems too small")
        success = False

    if wave_range_fertility < 0.3:
        print("WARNING: Fertility wave range seems too small")
        success = False

    if wave_range_mortality < 0.2:
        print("WARNING: Mortality wave range seems too small")
        success = False

    if max_pop - min_pop < 5:
        print("WARNING: Population fluctuation seems too small for wave effects")
        success = False

    if success:
        print("✅ Population wave system appears to be working correctly!")
    else:
        print("❌ Population wave system may not be working as expected")

    return success


if __name__ == "__main__":
    test_population_waves()
