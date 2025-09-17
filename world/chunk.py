from dataclasses import dataclass, field
from typing import List, Tuple, Any, Dict

from .terrain import TerrainType
from npcs.npc import NPC


@dataclass
class Chunk:
    """Represents a single chunk of the world.

    Resource Model (introduced Step C - depletion):
    - resources: current stock levels per resource type (plant, animal, fish, mineral, Wood...)
    - resource_capacity: maximum sustainable stock per resource type
    - resource_regen: per-tick regeneration amount (pre-seasonal multiplier) toward capacity
    The world engine will regenerate up to capacity each tick; factions harvest a fraction of stock.
    """

    coordinates: Tuple[int, int]
    terrain: TerrainType = TerrainType.PLAINS
    resources: Dict[str, float] = field(default_factory=dict)
    resource_capacity: Dict[str, float] = field(default_factory=dict)
    resource_regen: Dict[str, float] = field(default_factory=dict)
    npcs: List[NPC] = field(default_factory=list)
    factions: List[Any] = field(default_factory=list)
    landmarks: List[Any] = field(default_factory=list)
    event_triggers: List[Any] = field(default_factory=list)
    is_active: bool = False
    is_settlement: bool = False
    is_ruined: bool = False
    is_castle: bool = False

    def __post_init__(self):
        """Generate a unique ID based on coordinates."""
        self.id: str = f"{self.coordinates[0]}_{self.coordinates[1]}"

    def activate(self):
        """Activates the chunk, allowing simulation."""
        self.is_active = True

    def deactivate(self):
        """Deactivates the chunk, preparing it for serialization."""
        self.is_active = False

    def serialize(self) -> Dict[str, Any]:
        """Converts the chunk to a JSON-serializable dictionary for web API."""
        return {
            "coordinates": self.coordinates,
            "terrain": self.terrain.name,
            "resources": self.resources,
            "resource_capacity": self.resource_capacity,
            "npcs": [npc.serialize() for npc in self.npcs],
            "factions": self.factions,
            "is_active": self.is_active,
            "is_settlement": self.is_settlement,
            "is_ruined": self.is_ruined,
            "is_castle": self.is_castle,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Chunk":
        """Creates a chunk from a dictionary."""
        data["terrain"] = TerrainType[data["terrain"]]  # Convert string back to enum
        data["npcs"] = [NPC.from_dict(npc_data) for npc_data in data.get("npcs", [])]
        data["coordinates"] = tuple(data["coordinates"])
        # Handle resources: convert list to dict if necessary, or ensure it's a
        # dict
        if "resources" in data and isinstance(data["resources"], list):
            # Convert old list format to new dict format (e.g., ["food"] ->
            # {"food": 10.0})
            data["resources"] = {res: 10.0 for res in data["resources"]}  # Default quantity
        elif "resources" not in data:
            data["resources"] = {}
        # Backward compatibility: add new depletion fields if missing
        if "resource_capacity" not in data:
            data["resource_capacity"] = {}
        if "resource_regen" not in data:
            data["resource_regen"] = {}

        # Handle new is_settlement attribute for backward compatibility
        if "is_settlement" not in data:
            data["is_settlement"] = False
        # Handle new is_ruined attribute for backward compatibility
        if "is_ruined" not in data:
            data["is_ruined"] = False
        # Handle new is_castle attribute for backward compatibility
        if "is_castle" not in data:
            data["is_castle"] = False
        return cls(**data)
