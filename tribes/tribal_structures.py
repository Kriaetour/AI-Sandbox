import random
from typing import Dict, List, Tuple, Optional
from .tribe import Tribe


class TribalStructure:
    """Represents a tribal structure"""

    def __init__(
        self,
        structure_type: str,
        location: Tuple[int, int],
        tribe: Tribe,
        quality: float = 1.0,
    ):
        self.structure_type = structure_type
        self.location = location
        self.tribe = tribe
        self.quality = quality  # 0.0 to 1.0
        self.condition = 1.0  # 0.0 to 1.0, degrades over time
        self.capacity = self._get_capacity()
        self.benefits = self._get_benefits()

    def _get_capacity(self) -> int:
        """Get capacity based on structure type"""
        capacities = {
            "campfire": 8,  # Gathering around fire
            "shelter": 4,  # Sleeping shelter
            "storage": 50,  # Resource storage units
            "totem": 0,  # Spiritual, no capacity
            "watchtower": 2,  # Lookout posts
            "workshop": 3,  # Crafting stations
            "ritual_circle": 6,  # Ceremonial gatherings
        }
        return capacities.get(self.structure_type, 0)

    def _get_benefits(self) -> Dict[str, float]:
        """Get benefits provided by this structure"""
        benefits = {
            "campfire": {"morale": 0.2, "social": 0.3, "warmth": 0.4},
            "shelter": {"safety": 0.5, "rest": 0.6, "protection": 0.4},
            "storage": {"resource_preservation": 0.8, "organization": 0.3},
            "totem": {"spiritual": 0.4, "cultural": 0.3, "morale": 0.2},
            "watchtower": {"security": 0.6, "awareness": 0.5},
            "workshop": {"crafting_efficiency": 0.5, "skill_training": 0.3},
            "ritual_circle": {"spiritual": 0.5, "cultural": 0.4, "unity": 0.3},
        }
        return benefits.get(self.structure_type, {})

    def degrade(self, amount: float = 0.01):
        """Degrade structure condition over time"""
        self.condition = max(0.0, self.condition - amount)

    def repair(self, repair_amount: float = 0.2):
        """Repair structure condition"""
        self.condition = min(1.0, self.condition + repair_amount)

    def get_effective_capacity(self) -> int:
        """Get effective capacity considering condition"""
        return int(self.capacity * self.condition)

    def get_effective_benefits(self) -> Dict[str, float]:
        """Get effective benefits considering condition and quality"""
        effective_benefits = {}
        for benefit, value in self.benefits.items():
            effective_benefits[benefit] = value * self.condition * self.quality
        return effective_benefits

    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization"""
        return {
            "structure_type": self.structure_type,
            "location": self.location,
            "quality": self.quality,
            "condition": self.condition,
        }


class TribalCamp:
    """Manages tribal camp and structures"""

    STRUCTURE_COSTS = {
        "campfire": {"wood": 3, "stone": 1},
        "shelter": {"wood": 8, "stone": 2},
        "storage": {"wood": 6, "stone": 4},
        "totem": {"wood": 4, "stone": 3},
        "watchtower": {"wood": 12, "stone": 6},
        "workshop": {"wood": 10, "stone": 5},
        "ritual_circle": {"stone": 8},
    }

    def __init__(self, tribe: Tribe, center_location: Tuple[int, int]):
        self.tribe = tribe
        self.center_location = center_location
        self.structures: List[TribalStructure] = []
        self.layout_radius = 3  # Camp spread radius

    def can_build_structure(self, structure_type: str) -> bool:
        """Check if tribe can build a structure"""
        if structure_type not in self.STRUCTURE_COSTS:
            return False

        costs = self.STRUCTURE_COSTS[structure_type]
        for resource, amount in costs.items():
            if self.tribe.shared_resources.get(resource, 0) < amount:
                return False

        return True

    def build_structure(
        self, structure_type: str, location: Optional[Tuple[int, int]] = None
    ) -> bool:
        """Build a structure at specified or random location"""

        if not self.can_build_structure(structure_type):
            return False

        # Deduct resources
        costs = self.STRUCTURE_COSTS[structure_type]
        for resource, amount in costs.items():
            self.tribe.take_shared_resource(resource, amount)

        # Determine location
        if location is None:
            location = self._find_build_location()

        # Create structure
        quality = random.uniform(0.7, 1.0)  # Base quality with some variation
        structure = TribalStructure(structure_type, location, self.tribe, quality)
        self.structures.append(structure)

        # Update tribe structures count
        self.tribe.build_structure(structure_type, location)

        # Record in tribal memory
        self.tribe.add_tribal_memory(
            "structure_built",
            {"type": structure_type, "location": location, "quality": quality},
        )

        return True

    def _find_build_location(self) -> Tuple[int, int]:
        """Find a suitable location for building"""
        # Try to build near existing structures
        if self.structures:
            base_location = random.choice(self.structures).location
            # Build within 2 tiles of existing structure
            dx = random.randint(-2, 2)
            dy = random.randint(-2, 2)
            return (base_location[0] + dx, base_location[1] + dy)
        else:
            # Build near camp center
            dx = random.randint(-1, 1)
            dy = random.randint(-1, 1)
            return (self.center_location[0] + dx, self.center_location[1] + dy)

    def get_camp_benefits(self) -> Dict[str, float]:
        """Calculate total benefits from all camp structures"""
        total_benefits = {}

        for structure in self.structures:
            benefits = structure.get_effective_benefits()
            for benefit, value in benefits.items():
                total_benefits[benefit] = total_benefits.get(benefit, 0) + value

        return total_benefits

    def get_camp_capacity(self) -> Dict[str, int]:
        """Get total capacity by structure type"""
        capacities = {}

        for structure in self.structures:
            structure_type = structure.structure_type
            capacity = structure.get_effective_capacity()
            capacities[structure_type] = capacities.get(structure_type, 0) + capacity

        return capacities

    def maintain_structures(self):
        """Maintain and repair structures"""
        for structure in self.structures:
            # Natural degradation
            structure.degrade(0.005)  # Small degradation each turn

            # Auto-repair if resources available and structure is damaged
            if structure.condition < 0.8:
                repair_cost = {"wood": 1, "stone": 1}
                can_repair = True
                for resource, amount in repair_cost.items():
                    if self.tribe.shared_resources.get(resource, 0) < amount:
                        can_repair = False
                        break

                if can_repair:
                    for resource, amount in repair_cost.items():
                        self.tribe.take_shared_resource(resource, amount)
                    structure.repair(0.1)

    def get_structure_info(self) -> List[Dict]:
        """Get information about all structures"""
        return [structure.to_dict() for structure in self.structures]

    def destroy_structure(self, location: Tuple[int, int]) -> bool:
        """Destroy a structure at location"""
        for i, structure in enumerate(self.structures):
            if structure.location == location:
                # Remove from tribe count
                if structure.structure_type in self.tribe.structures:
                    self.tribe.structures[structure.structure_type] = max(
                        0, self.tribe.structures[structure.structure_type] - 1
                    )

                # Remove structure
                del self.structures[i]

                # Record destruction
                self.tribe.add_tribal_memory(
                    "structure_destroyed",
                    {"type": structure.structure_type, "location": location},
                )

                return True
        return False

    def process_camp_turn(self):
        """Process actions for the camp each turn"""
        # Maintain and repair structures
        self.maintain_structures()

        # Advance architectural development
        architecture = TribalArchitecture(self.tribe)
        architecture.advance_architecture()

        # Suggest next structure to build
        next_structure = architecture.suggest_next_structure()
        if next_structure:
            self.build_structure(next_structure)

        # Gather resources if storage available
        if "storage" in self.tribe.structures:
            storage_structure = next(
                (s for s in self.structures if s.structure_type == "storage"), None
            )
            if storage_structure:
                # Storage provides preservation benefits
                preservation_bonus = storage_structure.get_effective_benefits().get(
                    "resource_preservation", 0
                )
                # Apply preservation to existing resources
                for resource in ["food", "wood", "stone", "herbs"]:
                    if resource in self.tribe.shared_resources:
                        # Small preservation effect
                        self.tribe.shared_resources[resource] *= 1.0 + preservation_bonus * 0.01


class TribalArchitecture:
    """Manages tribal architectural development"""

    DEVELOPMENT_STAGES = [
        "nomadic",  # No permanent structures
        "basic_camp",  # Campfire, basic shelters
        "established",  # Storage, totems, workshops
        "advanced",  # Watchtowers, ritual circles
        "civilized",  # Complex multi-purpose structures
    ]

    def __init__(self, tribe: Tribe):
        self.tribe = tribe
        self.development_stage = "nomadic"
        self.architectural_knowledge = set()

    def advance_architecture(self):
        """Advance tribal architectural knowledge"""

        # Determine advancement based on tribe size and existing structures
        structure_count = sum(self.tribe.structures.values())
        member_count = len(self.tribe.member_ids)

        if member_count >= 8 and structure_count >= 3:
            if self.development_stage == "nomadic":
                self.development_stage = "basic_camp"
                self._unlock_basic_structures()
        elif member_count >= 12 and structure_count >= 6:
            if self.development_stage == "basic_camp":
                self.development_stage = "established"
                self._unlock_established_structures()
        elif member_count >= 16 and structure_count >= 10:
            if self.development_stage == "established":
                self.development_stage = "advanced"
                self._unlock_advanced_structures()

    def _unlock_basic_structures(self):
        """Unlock basic camp structures"""
        self.architectural_knowledge.update(["campfire", "shelter", "storage"])

    def _unlock_established_structures(self):
        """Unlock established camp structures"""
        self.architectural_knowledge.update(["totem", "workshop"])

    def _unlock_advanced_structures(self):
        """Unlock advanced structures"""
        self.architectural_knowledge.update(["watchtower", "ritual_circle"])

    def get_available_structures(self) -> List[str]:
        """Get list of structures the tribe can build"""
        return list(self.architectural_knowledge)

    def suggest_next_structure(self) -> Optional[str]:
        """Suggest the next most beneficial structure to build"""

        # Priority based on current needs
        priorities = []

        # Always need basic structures first
        if "campfire" not in self.tribe.structures or self.tribe.structures["campfire"] == 0:
            priorities.append("campfire")
        if (
            "shelter" not in self.tribe.structures
            or self.tribe.structures["shelter"] < len(self.tribe.member_ids) // 4
        ):
            priorities.append("shelter")
        if "storage" not in self.tribe.structures or self.tribe.structures["storage"] < 2:
            priorities.append("storage")

        # Then cultural/functional structures
        if "totem" not in self.tribe.structures or self.tribe.structures["totem"] == 0:
            priorities.append("totem")
        if "workshop" not in self.tribe.structures or self.tribe.structures["workshop"] == 0:
            priorities.append("workshop")

        # Advanced structures for security and ceremony
        if self.tribe.rivalries and (
            "watchtower" not in self.tribe.structures or self.tribe.structures["watchtower"] == 0
        ):
            priorities.append("watchtower")
        if (
            "ritual_circle" not in self.tribe.structures
            or self.tribe.structures["ritual_circle"] == 0
        ):
            priorities.append("ritual_circle")

        # Return first available priority
        for structure in priorities:
            if structure in self.architectural_knowledge:
                return structure

        return None
