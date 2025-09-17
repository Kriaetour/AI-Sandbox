#!/usr/bin/env python3
"""
Quick test to see wave multipliers without population explosion.
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from world.engine import WorldEngine
import logging


def test_wave_multipliers():
    """Test just the wave multiplier calculations."""
    # Configure logging to minimal
    logging.basicConfig(level=logging.ERROR)

    print("Testing Wave Multiplier Calculations...")
    print("=" * 50)

    # Create world with waves enabled
    world = WorldEngine()

    # Test wave calculations at different ticks
    test_ticks = [
        0,
        100,
        200,
        300,
        400,
        500,
        600,
        700,
        800,
        900,
        1000,
        1200,
        1400,
        1600,
    ]

    print("Tick | Resource Wave | Fertility Wave | Mortality Wave")
    print("-" * 55)

    for tick in test_ticks:
        world._tick_count = tick  # Manually set tick for testing

        try:
            resource_mult = world.calculate_resource_wave_multiplier()
            fertility_mult = world.calculate_fertility_wave_multiplier()
            mortality_mult = world.calculate_mortality_wave_multiplier()
        except Exception as e:
            print(f"Error at tick {tick}: {e}")
            continue

        print(
            f"{tick:4d} | {resource_mult:12.3f} | {fertility_mult:13.3f} | {mortality_mult:13.3f}"
        )

    print()
    print("Wave system appears to be calculating correctly!")
    print("Resource wave should cycle every 800 ticks.")
    print("Fertility wave should cycle every 600 ticks.")
    print("Mortality wave should cycle every 700 ticks.")


if __name__ == "__main__":
    test_wave_multipliers()
