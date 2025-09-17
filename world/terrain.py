from enum import Enum, auto


class TerrainType(Enum):
    """Enumeration for different types of terrain in a chunk."""

    PLAINS = auto()
    FOREST = auto()
    MOUNTAINS = auto()
    DESERT = auto()
    WATER = auto()
    SWAMP = auto()
    TUNDRA = auto()
    JUNGLE = auto()
    HILLS = auto()
    VALLEY = auto()
    CANYON = auto()
    COASTAL = auto()
    ISLAND = auto()
    VOLCANIC = auto()
    SAVANNA = auto()
    TAIGA = auto()
    STEPPE = auto()
    BADLANDS = auto()
    GLACIER = auto()
    OASIS = auto()
