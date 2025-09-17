"""
Pathfinding utilities for NPCs to navigate the world and find resources efficiently.

This module provides:
- A* pathfinding algorithm for optimal route planning
- Terrain-aware movement cost calculation
- Multi-step navigation for distant targets
- Resource search algorithms with configurable radius
"""

import heapq
import math
from typing import List, Tuple, Optional, Dict, Set
from dataclasses import dataclass
from world.terrain import TerrainType


@dataclass
class PathNode:
    """A node in the pathfinding graph."""

    coordinates: Tuple[int, int]
    g_cost: float = float("inf")  # Cost from start
    h_cost: float = 0.0  # Heuristic cost to goal
    f_cost: float = float("inf")  # Total cost (g + h)
    parent: Optional["PathNode"] = None
    terrain: Optional[TerrainType] = None

    def __lt__(self, other):
        return self.f_cost < other.f_cost


class TerrainMovementCosts:
    """Defines movement costs for different terrain types."""

    # Base movement costs for each terrain type (higher = slower/more difficult)
    TERRAIN_COSTS = {
        TerrainType.PLAINS: 1.0,  # Easy movement
        TerrainType.FOREST: 1.2,  # Slightly difficult
        TerrainType.HILLS: 1.3,  # Moderately difficult
        TerrainType.MOUNTAINS: 2.0,  # Difficult movement
        TerrainType.DESERT: 1.5,  # Hot and difficult
        TerrainType.SWAMP: 1.8,  # Very difficult
        TerrainType.TUNDRA: 1.4,  # Cold and difficult
        TerrainType.JUNGLE: 1.6,  # Dense vegetation
        TerrainType.WATER: 3.0,  # Very slow (swimming/boats)
        TerrainType.VALLEY: 0.9,  # Easy movement
        TerrainType.CANYON: 1.7,  # Difficult navigation
        TerrainType.COASTAL: 1.1,  # Slightly difficult
        TerrainType.ISLAND: 1.0,  # Normal movement on land
        TerrainType.VOLCANIC: 2.5,  # Dangerous terrain
        TerrainType.SAVANNA: 0.8,  # Easy movement
        TerrainType.TAIGA: 1.3,  # Cold forest
        TerrainType.STEPPE: 0.9,  # Easy grassland
        TerrainType.BADLANDS: 1.9,  # Harsh terrain
        TerrainType.GLACIER: 2.2,  # Very difficult
        TerrainType.OASIS: 0.8,  # Easy movement
    }

    @classmethod
    def get_movement_cost(cls, terrain: TerrainType) -> float:
        """Get the movement cost for a given terrain type."""
        return cls.TERRAIN_COSTS.get(terrain, 1.0)


class PathfindingEngine:
    """Advanced pathfinding engine for NPCs."""

    def __init__(self, world_engine):
        """Initialize with reference to world engine for chunk access."""
        self.world_engine = world_engine

    def manhattan_distance(self, pos1: Tuple[int, int], pos2: Tuple[int, int]) -> float:
        """Calculate Manhattan distance between two positions."""
        return abs(pos1[0] - pos2[0]) + abs(pos1[1] - pos2[1])

    def euclidean_distance(self, pos1: Tuple[int, int], pos2: Tuple[int, int]) -> float:
        """Calculate Euclidean distance between two positions."""
        return math.sqrt((pos1[0] - pos2[0]) ** 2 + (pos1[1] - pos2[1]) ** 2)

    def get_neighbors(self, pos: Tuple[int, int]) -> List[Tuple[int, int]]:
        """Get valid neighboring coordinates (8-directional movement)."""
        x, y = pos
        neighbors = []

        # 8-directional movement including diagonals
        for dx in [-1, 0, 1]:
            for dy in [-1, 0, 1]:
                if dx == 0 and dy == 0:
                    continue
                neighbors.append((x + dx, y + dy))

        return neighbors

    def is_passable(self, coordinates: Tuple[int, int]) -> bool:
        """Check if a position is passable (basic check, can be expanded)."""
        try:
            # Most terrains are passable, but could add restrictions here
            # For now, all terrain types are passable with different costs
            return True
        except Exception:
            return False

    def get_terrain_at(self, coordinates: Tuple[int, int]) -> Optional[TerrainType]:
        """Get the terrain type at given coordinates."""
        try:
            chunk = self.world_engine.get_chunk(coordinates[0], coordinates[1])
            return chunk.terrain
        except Exception:
            return None

    def a_star_pathfind(
        self, start: Tuple[int, int], goal: Tuple[int, int], max_distance: int = 20
    ) -> Optional[List[Tuple[int, int]]]:
        """
        A* pathfinding algorithm with terrain-aware costs.

        Args:
            start: Starting coordinates
            goal: Goal coordinates
            max_distance: Maximum search distance to prevent infinite loops

        Returns:
            List of coordinates representing the path, or None if no path found
        """
        if start == goal:
            return [start]

        # Check if goal is too far
        if self.manhattan_distance(start, goal) > max_distance:
            return None

        open_set = []
        closed_set: Set[Tuple[int, int]] = set()
        nodes: Dict[Tuple[int, int], PathNode] = {}

        # Initialize start node
        start_node = PathNode(start, g_cost=0.0)
        start_node.h_cost = self.euclidean_distance(start, goal)
        start_node.f_cost = start_node.g_cost + start_node.h_cost
        nodes[start] = start_node

        heapq.heappush(open_set, start_node)

        while open_set:
            current_node = heapq.heappop(open_set)
            current_pos = current_node.coordinates

            if current_pos in closed_set:
                continue

            closed_set.add(current_pos)

            # Check if we reached the goal
            if current_pos == goal:
                path = []
                while current_node:
                    path.append(current_node.coordinates)
                    current_node = current_node.parent
                return path[::-1]  # Reverse to get start->goal order

            # Explore neighbors
            for neighbor_pos in self.get_neighbors(current_pos):
                if neighbor_pos in closed_set or not self.is_passable(neighbor_pos):
                    continue

                # Calculate movement cost
                terrain = self.get_terrain_at(neighbor_pos)
                movement_cost = TerrainMovementCosts.get_movement_cost(terrain) if terrain else 1.0

                # Add diagonal penalty for diagonal movement
                is_diagonal = (
                    abs(neighbor_pos[0] - current_pos[0]) == 1
                    and abs(neighbor_pos[1] - current_pos[1]) == 1
                )
                if is_diagonal:
                    movement_cost *= 1.414  # sqrt(2) for diagonal movement

                tentative_g_cost = current_node.g_cost + movement_cost

                if neighbor_pos not in nodes:
                    nodes[neighbor_pos] = PathNode(neighbor_pos, terrain=terrain)

                neighbor_node = nodes[neighbor_pos]

                if tentative_g_cost < neighbor_node.g_cost:
                    neighbor_node.parent = current_node
                    neighbor_node.g_cost = tentative_g_cost
                    neighbor_node.h_cost = self.euclidean_distance(neighbor_pos, goal)
                    neighbor_node.f_cost = neighbor_node.g_cost + neighbor_node.h_cost

                    heapq.heappush(open_set, neighbor_node)

        return None  # No path found

    def find_nearest_resource(
        self,
        start: Tuple[int, int],
        resource_type: str,
        search_radius: int = 10,
        min_amount: float = 1.0,
    ) -> Optional[Tuple[int, int]]:
        """
        Find the nearest chunk containing a specific resource type.

        Args:
            start: Starting coordinates
            resource_type: Type of resource to search for (e.g., 'food', 'wood', etc.)
            search_radius: Maximum distance to search
            min_amount: Minimum amount of resource required

        Returns:
            Coordinates of nearest chunk with resource, or None if not found
        """
        best_pos = None
        best_distance = float("inf")
        best_amount = 0

        # Search in expanding circles
        for radius in range(1, search_radius + 1):
            for dx in range(-radius, radius + 1):
                for dy in range(-radius, radius + 1):
                    # Only check positions on the current radius boundary
                    if abs(dx) != radius and abs(dy) != radius:
                        continue

                    pos = (start[0] + dx, start[1] + dy)

                    try:
                        chunk = self.world_engine.get_chunk(pos[0], pos[1])
                        resource_amount = chunk.resources.get(resource_type, 0)

                        if resource_amount >= min_amount:
                            distance = self.euclidean_distance(start, pos)

                            # Prioritize by amount/distance ratio for efficiency
                            efficiency = resource_amount / max(distance, 1.0)
                            best_efficiency = (
                                best_amount / max(best_distance, 1.0) if best_pos else 0
                            )

                            if efficiency > best_efficiency:
                                best_pos = pos
                                best_distance = distance
                                best_amount = resource_amount

                    except Exception:
                        continue

        return best_pos

    def find_all_resources_in_radius(
        self,
        start: Tuple[int, int],
        resource_type: str,
        search_radius: int = 10,
        min_amount: float = 1.0,
    ) -> List[Tuple[Tuple[int, int], float]]:
        """
        Find all chunks with a specific resource within radius.

        Args:
            start: Starting coordinates
            resource_type: Type of resource to search for
            search_radius: Maximum distance to search
            min_amount: Minimum amount of resource required

        Returns:
            List of (coordinates, amount) tuples sorted by distance
        """
        resources = []

        for dx in range(-search_radius, search_radius + 1):
            for dy in range(-search_radius, search_radius + 1):
                pos = (start[0] + dx, start[1] + dy)
                distance = self.euclidean_distance(start, pos)

                if distance > search_radius:
                    continue

                try:
                    chunk = self.world_engine.get_chunk(pos[0], pos[1])
                    resource_amount = chunk.resources.get(resource_type, 0)

                    if resource_amount >= min_amount:
                        resources.append((pos, resource_amount))

                except Exception:
                    continue

        # Sort by distance
        resources.sort(key=lambda x: self.euclidean_distance(start, x[0]))
        return resources

    def get_optimal_harvesting_path(
        self,
        start: Tuple[int, int],
        resource_type: str,
        search_radius: int = 10,
        max_stops: int = 5,
    ) -> List[Tuple[int, int]]:
        """
        Create an optimal path that visits multiple resource locations.

        This is a simplified traveling salesman problem solver.

        Args:
            start: Starting coordinates
            resource_type: Type of resource to collect
            search_radius: How far to search for resources
            max_stops: Maximum number of resource locations to visit

        Returns:
            Optimal path visiting multiple resource locations
        """
        # Find all available resources
        resources = self.find_all_resources_in_radius(start, resource_type, search_radius)

        if not resources:
            return []

        # Limit to max_stops closest resources
        resources = resources[:max_stops]

        if len(resources) == 1:
            # Single resource - just path to it
            path = self.a_star_pathfind(start, resources[0][0])
            return path if path else []

        # For multiple resources, use nearest neighbor heuristic
        current_pos = start
        visited = set()
        full_path = []

        while len(visited) < len(resources):
            nearest_resource = None
            nearest_distance = float("inf")

            for pos, amount in resources:
                if pos not in visited:
                    distance = self.euclidean_distance(current_pos, pos)
                    if distance < nearest_distance:
                        nearest_distance = distance
                        nearest_resource = pos

            if nearest_resource:
                # Path to next resource
                segment = self.a_star_pathfind(current_pos, nearest_resource)
                if segment:
                    if full_path:  # Don't duplicate starting position
                        segment = segment[1:]
                    full_path.extend(segment)
                    current_pos = nearest_resource
                    visited.add(nearest_resource)
                else:
                    break  # Can't reach this resource
            else:
                break

        return full_path


def calculate_resource_priority_score(
    npc,
    resource_type: str,
    amount: float,
    distance: float,
    season_modifier: float = 1.0,
) -> float:
    """
    Calculate a priority score for a resource based on various factors.

    Args:
        npc: The NPC considering the resource
        resource_type: Type of resource
        amount: Amount of resource available
        distance: Distance to the resource
        season_modifier: Seasonal multiplier for resource value

    Returns:
        Priority score (higher = more important)
    """
    # Base score starts with amount
    score = amount * season_modifier

    # Factor in NPC's needs
    if resource_type == "food":
        food_need = 100 - npc.needs.get("food", 100)
        score *= 1 + food_need / 100  # Higher multiplier when hungrier

    # Distance penalty (closer is better)
    distance_penalty = 1.0 / (1.0 + distance * 0.1)
    score *= distance_penalty

    # Faction needs could be considered here
    # TODO: Add faction-level resource priorities

    return score
