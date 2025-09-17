import random
import math
import logging
from typing import Dict, List, Tuple, Set, Optional
from .tribe import Tribe


class TribalTerritory:
    """Manages tribal territory claims and boundaries"""

    def __init__(self, tribe: Tribe):
        self.tribe = tribe
        self.claimed_tiles: Set[Tuple[int, int]] = set()
        self.border_tiles: Set[Tuple[int, int]] = set()
        self.resource_zones: Dict[Tuple[int, int], str] = {}  # Location -> resource type
        self.marked_boundaries: Set[Tuple[int, int]] = set()  # Tiles with boundary markers

    def claim_tile(self, location: Tuple[int, int], resource_type: Optional[str] = None):
        """Claim a tile for the tribe"""
        self.claimed_tiles.add(location)
        self.tribe.claim_territory(location)

        if resource_type:
            self.resource_zones[location] = resource_type

        # Update border tiles
        self._update_borders()

    def release_tile(self, location: Tuple[int, int]):
        """Release a claimed tile"""
        if location in self.claimed_tiles:
            self.claimed_tiles.remove(location)
            if location in self.resource_zones:
                del self.resource_zones[location]
            if location in self.marked_boundaries:
                self.marked_boundaries.remove(location)

            # Update border tiles
            self._update_borders()

    def _update_borders(self):
        """Update which tiles are on the border"""
        self.border_tiles.clear()

        for tile in self.claimed_tiles:
            x, y = tile
            # Check adjacent tiles
            adjacent = [
                (x + 1, y),
                (x - 1, y),
                (x, y + 1),
                (x, y - 1),
                (x + 1, y + 1),
                (x + 1, y - 1),
                (x - 1, y + 1),
                (x - 1, y - 1),
            ]

            for adj in adjacent:
                if adj not in self.claimed_tiles:
                    self.border_tiles.add(tile)
                    break

    def get_territory_size(self) -> int:
        """Get total territory size"""
        return len(self.claimed_tiles)

    def get_resource_richness(self) -> Dict[str, int]:
        """Get count of different resource types in territory"""
        richness = {}
        for resource_type in self.resource_zones.values():
            richness[resource_type] = richness.get(resource_type, 0) + 1
        return richness

    def mark_boundary(self, location: Tuple[int, int]):
        """Mark a boundary tile with tribal symbols"""
        if location in self.border_tiles:
            self.marked_boundaries.add(location)
            self.tribe.add_tribal_memory(
                "boundary_marked", {"location": location, "symbol": self.tribe.symbol}
            )

    def get_conflict_zones(
        self, other_territories: List["TribalTerritory"]
    ) -> List[Tuple[int, int]]:
        """Identify tiles that overlap with other tribes' territories"""
        conflict_zones = []

        for other_territory in other_territories:
            overlapping = self.claimed_tiles.intersection(other_territory.claimed_tiles)
            conflict_zones.extend(list(overlapping))

        return conflict_zones

    def expand_territory(self, center: Tuple[int, int], radius: int = 2):
        """Expand territory around a center point"""
        cx, cy = center
        new_claims = []

        for dx in range(-radius, radius + 1):
            for dy in range(-radius, radius + 1):
                if dx == 0 and dy == 0:  # Skip center
                    continue

                distance = math.sqrt(dx * dx + dy * dy)
                if distance <= radius:
                    tile = (cx + dx, cy + dy)
                    if tile not in self.claimed_tiles:
                        new_claims.append(tile)

        # Claim new tiles (limit expansion to prevent infinite growth)
        for tile in new_claims[:5]:  # Limit to 5 new tiles per expansion
            self.claim_tile(tile)


class TribalConflict:
    """Manages conflicts between tribes"""

    def __init__(self):
        self.active_conflicts: Dict[str, Dict] = {}  # Conflict ID -> conflict data
        self.conflict_history: List[Dict] = []

    def initiate_conflict(
        self,
        initiating_tribe: Tribe,
        target_tribe: Tribe,
        conflict_type: str,
        location: Tuple[int, int],
    ) -> str:
        """Initiate a conflict between tribes"""

        conflict_id = f"{initiating_tribe.name}_vs_{target_tribe.name}_{len(self.active_conflicts)}"

        conflict_data = {
            "id": conflict_id,
            "type": conflict_type,  # "territory", "resources", "revenge", "raid"
            "initiator": initiating_tribe.name,
            "target": target_tribe.name,
            "location": location,
            "start_turn": len(self.conflict_history),
            "status": "active",
            "casualties": {"initiator": 0, "target": 0},
            "resources_lost": {"initiator": 0, "target": 0},
        }

        self.active_conflicts[conflict_id] = conflict_data

        # Record in tribal memories
        initiating_tribe.add_tribal_memory(
            "conflict_started",
            {
                "conflict_id": conflict_id,
                "type": conflict_type,
                "target": target_tribe.name,
                "location": location,
            },
        )

        target_tribe.add_tribal_memory(
            "conflict_started",
            {
                "conflict_id": conflict_id,
                "type": conflict_type,
                "initiator": initiating_tribe.name,
                "location": location,
            },
        )

        return conflict_id

    def resolve_conflict(self, conflict_id: str, resolution: str) -> Dict:
        """Resolve an active conflict"""

        if conflict_id not in self.active_conflicts:
            return {"error": "Conflict not found"}

        conflict = self.active_conflicts[conflict_id]
        conflict["status"] = "resolved"
        conflict["resolution"] = resolution
        conflict["end_turn"] = len(self.conflict_history)

        # Record resolution
        self.conflict_history.append(conflict.copy())

        # Clean up active conflicts
        del self.active_conflicts[conflict_id]

        return conflict

    def simulate_skirmish(
        self, conflict_id: str, tribes: Optional[Dict[str, Tribe]] = None
    ) -> Dict:
        """Simulate a small skirmish in an active conflict.

        Cultural value influence:
        - Honor: Flat +2 power (represents zealous commitment); extra +1 when type == 'revenge'.
        - Prosperity: +2 in 'resources' conflicts, otherwise +1 (motivated by material gain / protection of assets).
        - Survival: +3 when defending (target role) in 'territory' or 'raid' conflicts, otherwise +1.
        Secondary (2nd priority) value small situational +1 when its trigger matches.
        Safe fallback when tribes mapping or ledger missing: no modifiers.
        """

        if conflict_id not in self.active_conflicts:
            return {"error": "Conflict not found"}

        conflict = self.active_conflicts[conflict_id]

        # Base combat rolls
        initiator_power = random.randint(5, 15)
        target_power = random.randint(5, 15)

        power_modifiers = {"initiator": 0, "target": 0}
        value_context = {"initiator": None, "target": None}

        def apply_value_modifiers(tribe: Tribe, role: str, base_power: int) -> int:
            try:
                priorities = (
                    tribe.get_value_priority() if hasattr(tribe, "get_value_priority") else []
                )
                if not priorities:
                    return base_power
                top = priorities[0]
                second = priorities[1] if len(priorities) > 1 else None
                conflict_type = conflict.get("type", "")
                bonus = 0
                # Top value effects
                if top == "Honor":
                    bonus += 2
                    if conflict_type == "revenge":
                        bonus += 1
                elif top == "Prosperity":
                    bonus += 2 if conflict_type == "resources" else 1
                elif top == "Survival":
                    if role == "target" and conflict_type in ("territory", "raid"):
                        bonus += 3
                    else:
                        bonus += 1
                # Secondary value small situational bump
                if second:
                    if second == "Honor" and conflict_type in ("raid", "revenge"):
                        bonus += 1
                    elif second == "Prosperity" and conflict_type == "resources":
                        bonus += 1
                    elif second == "Survival" and role == "target":
                        bonus += 1
                power_modifiers[role] = bonus
                value_context[role] = {"top": top, "second": second}
                return base_power + bonus
            except Exception:  # Defensive: never break conflict loop
                return base_power

        if tribes:
            initiator_name = conflict.get("initiator")
            target_name = conflict.get("target")
            initiator_tribe = tribes.get(initiator_name)
            target_tribe = tribes.get(target_name)
            if initiator_tribe:
                initiator_power = apply_value_modifiers(
                    initiator_tribe, "initiator", initiator_power
                )
            if target_tribe:
                target_power = apply_value_modifiers(target_tribe, "target", target_power)

        # Determine outcome
        if initiator_power > target_power:
            winner = "initiator"
            loser = "target"
            casualties = max(
                0,
                random.randint(0, 2) - (1 if power_modifiers.get("target", 0) >= 3 else 0),
            )
        elif target_power > initiator_power:
            winner = "target"
            loser = "initiator"
            casualties = max(
                0,
                random.randint(0, 2) - (1 if power_modifiers.get("initiator", 0) >= 3 else 0),
            )
        else:
            winner = "draw"
            loser = None
            casualties = random.randint(0, 1)

        if loser:
            conflict["casualties"][loser] += casualties

        result = {
            "conflict_id": conflict_id,
            "outcome": winner,
            "initiator_power": initiator_power,
            "target_power": target_power,
            "casualties": casualties,
            "location": conflict["location"],
            "value_context": value_context,
            "power_modifiers": power_modifiers,
        }
        return result

    def get_active_conflicts(self, tribe_name: Optional[str] = None) -> List[Dict]:
        """Get active conflicts, optionally filtered by tribe"""
        conflicts = list(self.active_conflicts.values())

        if tribe_name:
            conflicts = [
                c for c in conflicts if c["initiator"] == tribe_name or c["target"] == tribe_name
            ]

        return conflicts

    def get_conflict_statistics(self) -> Dict:
        """Get overall conflict statistics"""
        total_conflicts = len(self.conflict_history) + len(self.active_conflicts)
        resolved_conflicts = len(self.conflict_history)

        if total_conflicts == 0:
            return {"total_conflicts": 0, "resolution_rate": 0.0}

        resolution_rate = resolved_conflicts / total_conflicts

        # Count conflict types
        type_counts = {}
        for conflict in self.conflict_history:
            conflict_type = conflict.get("type", "unknown")
            type_counts[conflict_type] = type_counts.get(conflict_type, 0) + 1

        return {
            "total_conflicts": total_conflicts,
            "resolved_conflicts": resolved_conflicts,
            "active_conflicts": len(self.active_conflicts),
            "resolution_rate": resolution_rate,
            "conflict_types": type_counts,
        }

    def process_conflicts_turn(self, tribes: Dict[str, Tribe]):
        """Process active conflicts each turn"""
        for conflict_id, conflict in list(self.active_conflicts.items()):
            # Chance for skirmish
            if random.random() < 0.3:  # 30% chance per turn
                result = self.simulate_skirmish(conflict_id, tribes)
                if "error" not in result:
                    logging.getLogger("TribalConflict").info(
                        f"Skirmish in conflict {conflict_id}: {result['outcome']} (mods {result.get('power_modifiers')})"
                    )

            # Chance for conflict resolution
            if random.random() < 0.1:  # 10% chance per turn
                resolutions = [
                    "peace_treaty",
                    "territorial_compromise",
                    "victory",
                    "stalemate",
                ]
                resolution = random.choice(resolutions)
                result = self.resolve_conflict(conflict_id, resolution)
                if "error" not in result:
                    logging.getLogger("TribalConflict").info(
                        f"Conflict {conflict_id} resolved with: {resolution}"
                    )


class TribalDiplomacy:
    """Manages diplomatic relations between tribes"""

    def __init__(self):
        self.diplomatic_history: List[Dict] = []

    def negotiate_peace(
        self, tribe1: Tribe, tribe2: Tribe, negotiator_role: str = "leader"
    ) -> Dict:
        """Negotiate peace between two tribes"""

        # Success based on tribal relationships and negotiator
        base_success = 0.5

        if tribe2.name in tribe1.alliances:
            base_success += 0.3
        elif tribe2.name in tribe1.rivalries:
            base_success -= 0.3

        # Leader negotiation bonus
        if negotiator_role == "leader":
            base_success += 0.2

        success = random.random() < base_success

        negotiation_result = {
            "tribe1": tribe1.name,
            "tribe2": tribe2.name,
            "type": "peace_negotiation",
            "success": success,
            "negotiator": negotiator_role,
            "terms": self._generate_peace_terms() if success else None,
        }

        # Record in diplomatic history
        self.diplomatic_history.append(negotiation_result)

        # Update tribal relationships if successful
        if success:
            tribe1.negotiate_truce(tribe2.name, duration=20)
            tribe2.negotiate_truce(tribe1.name, duration=20)

            # Record in tribal memories
            tribe1.add_tribal_memory(
                "peace_negotiated",
                {"with_tribe": tribe2.name, "negotiator": negotiator_role},
            )
            tribe2.add_tribal_memory(
                "peace_negotiated",
                {"with_tribe": tribe1.name, "negotiator": negotiator_role},
            )

        return negotiation_result

    def _generate_peace_terms(self) -> Dict:
        """Generate terms for a peace agreement"""
        terms = {
            "duration": random.randint(10, 30),
            "territory_exchange": random.choice([True, False]),
            "resource_sharing": random.choice([True, False]),
            "alliance_formation": random.random() < 0.3,
        }
        return terms

    def arrange_trade_agreement(self, tribe1: Tribe, tribe2: Tribe) -> Dict:
        """Arrange a trade agreement between tribes"""

        trade_result = {
            "tribe1": tribe1.name,
            "tribe2": tribe2.name,
            "type": "trade_agreement",
            "resources": self._select_trade_resources(tribe1, tribe2),
            "duration": random.randint(15, 45),
        }

        # Record in diplomatic history
        self.diplomatic_history.append(trade_result)

        # Record in tribal memories
        tribe1.add_tribal_memory(
            "trade_agreement",
            {"with_tribe": tribe2.name, "resources": trade_result["resources"]},
        )
        tribe2.add_tribal_memory(
            "trade_agreement",
            {"with_tribe": tribe1.name, "resources": trade_result["resources"]},
        )

        return trade_result

    def _select_trade_resources(self, tribe1: Tribe, tribe2: Tribe) -> Dict:
        """Select resources for trade based on tribal resources"""
        available_resources = ["food", "wood", "stone", "herbs"]

        tribe1_offers = []
        tribe2_offers = []

        # Tribe1 offers what it has in abundance
        for resource in available_resources:
            if tribe1.shared_resources.get(resource, 0) > 10:
                tribe1_offers.append(resource)

        # Tribe2 offers what it has in abundance
        for resource in available_resources:
            if tribe2.shared_resources.get(resource, 0) > 10:
                tribe2_offers.append(resource)

        # Select 1-2 resources each
        tribe1_selection = random.sample(
            tribe1_offers, min(len(tribe1_offers), random.randint(1, 2))
        )
        tribe2_selection = random.sample(
            tribe2_offers, min(len(tribe2_offers), random.randint(1, 2))
        )

        return {"tribe1_offers": tribe1_selection, "tribe2_offers": tribe2_selection}

    def get_diplomatic_status(self, tribe1_name: str, tribe2_name: str) -> Dict:
        """Get diplomatic status between two tribes"""
        # This would be expanded to check actual tribal relationships
        return {
            "tribe1": tribe1_name,
            "tribe2": tribe2_name,
            "relationship": "neutral",  # Would check alliances/rivalries
            "active_truces": [],  # Would check active truces
            "trade_agreements": [],  # Would check active trade agreements
        }
