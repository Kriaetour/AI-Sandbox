#!/usr/bin/env python3
"""
Enhanced Pathfinding Demo

This script demonstrates the new advanced pathfinding and resource harvesting
capabilities implemented for NPCs in the AI Sandbox simulation.

Features demonstrated:
- A* pathfinding with terrain-aware movement costs
- Extended resource detection beyond immediate neighbors
- NPC memory of resource locations
- Resource knowledge sharing between faction members
- Intelligent resource prioritization based on distance and need
- Coordinated harvesting to avoid resource conflicts
"""

import logging
import sys
import os

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from world.engine import WorldEngine
from npcs.npc import NPC
from pathfinding import PathfindingEngine, TerrainMovementCosts
from world.terrain import TerrainType


def setup_logging():
    """Setup basic logging for the demo."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler("pathfinding_demo.log"),
        ],
    )


def create_test_world():
    """Create a small test world with varied terrain and resources."""
    world = WorldEngine(seed=12345)

    # Generate a small area with varied terrain
    for x in range(-3, 4):
        for y in range(-3, 4):
            chunk = world.get_chunk(x, y)
            world.activate_chunk(x, y)

            # Add some resources for testing
            if x == 0 and y == 0:
                chunk.resources["food"] = 50.0
            elif x == 2 and y == 1:
                chunk.resources["food"] = 30.0
                chunk.resources["wood"] = 25.0
            elif x == -2 and y == -1:
                chunk.resources["wood"] = 40.0
                chunk.resources["stone"] = 20.0
            elif x == 1 and y == -2:
                chunk.resources["food"] = 15.0

    return world


def demonstrate_pathfinding():
    """Demonstrate the pathfinding capabilities."""
    print("=== Enhanced Pathfinding Demonstration ===\n")

    # Setup
    setup_logging()
    world = create_test_world()

    # Create test NPCs
    npc1 = NPC(name="Explorer", coordinates=(0, 0), faction_id="TestFaction")
    npc2 = NPC(name="Gatherer", coordinates=(0, 0), faction_id="TestFaction")

    # Initialize pathfinding
    pathfinder = PathfindingEngine(world)

    print("1. Testing A* Pathfinding Algorithm")
    print("-" * 40)

    start = (0, 0)
    goal = (3, 2)
    path = pathfinder.a_star_pathfind(start, goal)

    if path:
        print(f"Path from {start} to {goal}: {path}")
        print(f"Path length: {len(path)} steps")

        # Calculate total movement cost
        total_cost = 0
        for i in range(len(path) - 1):
            next_pos = path[i + 1]
            chunk = world.get_chunk(next_pos[0], next_pos[1])
            terrain_cost = TerrainMovementCosts.get_movement_cost(chunk.terrain)
            total_cost += terrain_cost

        print(f"Total movement cost: {total_cost:.2f}")
    else:
        print("No path found!")

    print("\n2. Testing Resource Detection")
    print("-" * 40)

    # Find food resources
    food_locations = pathfinder.find_all_resources_in_radius(start, "food", search_radius=5)
    print(f"Food resources within radius 5 of {start}:")
    for coords, amount in food_locations:
        distance = pathfinder.euclidean_distance(start, coords)
        print(f"  {coords}: {amount:.1f} units (distance: {distance:.1f})")

    # Find nearest food
    nearest_food = pathfinder.find_nearest_resource(start, "food", search_radius=10)
    if nearest_food:
        print(f"Nearest food resource: {nearest_food}")

    print("\n3. Testing Resource Memory and Knowledge Sharing")
    print("-" * 50)

    # Simulate NPC discovering resources
    world_context = {
        "current_chunk": world.get_chunk(0, 0),
        "nearby_chunks": [
            world.get_chunk(x, y)
            for x in range(-1, 2)
            for y in range(-1, 2)
            if not (x == 0 and y == 0)
        ],
        "world_engine": world,
        "time": {"total_minutes": 100, "season": 1},
    }

    # NPC1 discovers some resources
    npc1._update_resource_memory("food", (2, 1), 30.0, world_context)
    npc1._update_resource_memory("wood", (-2, -1), 40.0, world_context)

    print(f"NPC1 ({npc1.name}) knows about:")
    for resource_type, locations in npc1.known_resources.items():
        print(f"  {resource_type}: {locations}")

    # Share knowledge with NPC2
    npc1._share_resource_knowledge(npc2, "food")
    npc1._share_resource_knowledge(npc2, "wood")

    print(f"\nAfter knowledge sharing, NPC2 ({npc2.name}) knows about:")
    for resource_type, locations in npc2.known_resources.items():
        print(f"  {resource_type}: {locations}")

    print("\n4. Testing Optimal Harvesting Path")
    print("-" * 40)

    # Find optimal path visiting multiple food sources
    optimal_path = pathfinder.get_optimal_harvesting_path(
        start, "food", search_radius=5, max_stops=3
    )

    if optimal_path:
        print(f"Optimal harvesting path: {optimal_path}")
        print(f"Total steps: {len(optimal_path)}")
    else:
        print("No optimal harvesting path found")

    print("\n5. Testing Terrain Movement Costs")
    print("-" * 40)

    print("Movement costs by terrain type:")
    for terrain in TerrainType:
        cost = TerrainMovementCosts.get_movement_cost(terrain)
        print(f"  {terrain.name}: {cost:.1f}")

    print("\n6. Testing NPC Resource Decision Making")
    print("-" * 45)

    # Test enhanced resource seeking
    action1 = npc1._seek_any_resource_action(world_context, ["food", "wood"])
    action2 = npc2._seek_any_resource_action(world_context, ["food", "wood"])

    print(f"NPC1 action: {action1}")
    print(f"NPC2 action: {action2}")

    print("\n=== Demonstration Complete ===")
    print("\nKey improvements implemented:")
    print("✓ A* pathfinding with terrain-aware costs")
    print("✓ Extended resource detection (configurable radius)")
    print("✓ NPC memory of resource locations")
    print("✓ Resource knowledge sharing between faction members")
    print("✓ Intelligent resource prioritization")
    print("✓ Coordinated harvesting to avoid conflicts")
    print("✓ Multi-step navigation to distant resources")
    print("✓ Optimal harvesting path planning")


if __name__ == "__main__":
    demonstrate_pathfinding()
