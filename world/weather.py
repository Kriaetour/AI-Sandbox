import random
import logging
from enum import Enum, auto
from .terrain import TerrainType


class WeatherType(Enum):
    """Types of weather and their effects."""

    CLEAR = auto()  # Default state, no special effects
    RAIN = auto()  # Slightly reduces movement, increases some resource yields
    STORM = auto()  # Severely reduces movement, NPCs seek shelter
    SNOW = auto()  # Reduces movement, hides ground resources
    BLIZZARD = auto()  # Severely reduces movement/visibility, shelter is top priority
    DROUGHT = auto()  # Reduces water/plant resources, may create 'thirst' need
    HEATWAVE = auto()  # Reduces water/plant resources, may create 'thirst' need


WEATHER_EFFECTS = {
    WeatherType.CLEAR: {
        "movement_modifier": 1.0,
        "resource_bonus": {},
        "npc_behavior": "normal",
    },
    WeatherType.RAIN: {
        "movement_modifier": 0.9,
        "resource_bonus": {"plants": 1.2, "water": 1.1},
        "npc_behavior": "seek_cover_if_idle",
    },
    WeatherType.STORM: {
        "movement_modifier": 0.5,
        "resource_bonus": {},
        "npc_behavior": "seek_shelter",
    },
    WeatherType.SNOW: {
        "movement_modifier": 0.7,
        "resource_bonus": {"ground_resources": 0.7},
        "npc_behavior": "move_cautiously",
    },
    WeatherType.BLIZZARD: {
        "movement_modifier": 0.3,
        "resource_bonus": {"ground_resources": 0.3},
        "npc_behavior": "shelter_priority",
    },
    WeatherType.DROUGHT: {
        "movement_modifier": 0.95,
        "resource_bonus": {"water": 0.3, "plants": 0.5},
        "npc_behavior": "seek_water",
    },
    WeatherType.HEATWAVE: {
        "movement_modifier": 0.9,
        "resource_bonus": {"water": 0.5, "plants": 0.7},
        "npc_behavior": "seek_water_and_shade",
    },
}


class WeatherManager:
    """
    Central controller for dynamic weather across the world.
    Assigns weather to regions or chunks, driven by the global clock.
    """

    def __init__(self, world, update_interval=1):
        self.world = world
        self.update_interval = update_interval  # in-game hours between updates
        self.logger = logging.getLogger("WeatherManager")
        self.current_weather = {}  # {(region or chunk): weather_state}
        self.last_update_time = 0

    def update_weather(self, current_time):
        """
        Update weather for all regions/chunks if enough time has passed.
        """
        if current_time - self.last_update_time < self.update_interval:
            return  # Not time to update yet
        self.last_update_time = current_time

        # Example: assign weather to each chunk (can be region-based if desired)
        for chunk in self.world.chunks.values():
            new_weather = self._determine_weather(chunk)
            self.current_weather[chunk.coordinates] = new_weather
            chunk.weather = new_weather  # Attach weather to chunk for easy access
            self.logger.debug(f"Chunk {chunk.coordinates} weather set to {new_weather.name}")

    def _determine_weather(self, chunk):
        """
        Decide the weather for a given chunk, factoring in biome and season.
        """
        biome = chunk.terrain  # TerrainType
        # Get current season from world
        season = getattr(self.world, "current_season", 0)  # 0=Spring, 1=Summer, 2=Autumn, 3=Winter

        # Probability tables: {biome: {season: [(WeatherType, probability), ...]}}
        # Probabilities should sum to 1.0 for each (biome, season)
        # For brevity, only a few biomes are fully detailed; others default to generic
        weather_probabilities = {
            TerrainType.JUNGLE: {
                0: [
                    (WeatherType.RAIN, 0.5),
                    (WeatherType.CLEAR, 0.3),
                    (WeatherType.STORM, 0.1),
                    (WeatherType.HEATWAVE, 0.1),
                ],
                1: [
                    (WeatherType.RAIN, 0.4),
                    (WeatherType.CLEAR, 0.3),
                    (WeatherType.STORM, 0.15),
                    (WeatherType.HEATWAVE, 0.15),
                ],
                2: [
                    (WeatherType.RAIN, 0.5),
                    (WeatherType.CLEAR, 0.3),
                    (WeatherType.STORM, 0.1),
                    (WeatherType.HEATWAVE, 0.1),
                ],
                3: [
                    (WeatherType.RAIN, 0.3),
                    (WeatherType.CLEAR, 0.3),
                    (WeatherType.STORM, 0.1),
                    (WeatherType.SNOW, 0.1),
                    (WeatherType.BLIZZARD, 0.05),
                    (WeatherType.HEATWAVE, 0.15),
                ],
            },
            TerrainType.SWAMP: {
                0: [
                    (WeatherType.RAIN, 0.5),
                    (WeatherType.CLEAR, 0.3),
                    (WeatherType.STORM, 0.1),
                    (
                        (WeatherType.FOG if hasattr(WeatherType, "FOG") else WeatherType.CLEAR),
                        0.1,
                    ),
                ],
                1: [
                    (WeatherType.RAIN, 0.4),
                    (WeatherType.CLEAR, 0.3),
                    (WeatherType.STORM, 0.15),
                    (WeatherType.HEATWAVE, 0.15),
                ],
                2: [
                    (WeatherType.RAIN, 0.5),
                    (WeatherType.CLEAR, 0.3),
                    (WeatherType.STORM, 0.1),
                    (WeatherType.HEATWAVE, 0.1),
                ],
                3: [
                    (WeatherType.RAIN, 0.3),
                    (WeatherType.CLEAR, 0.3),
                    (WeatherType.STORM, 0.1),
                    (WeatherType.SNOW, 0.1),
                    (WeatherType.BLIZZARD, 0.05),
                    (WeatherType.HEATWAVE, 0.15),
                ],
            },
            TerrainType.TUNDRA: {
                0: [
                    (WeatherType.SNOW, 0.3),
                    (WeatherType.CLEAR, 0.4),
                    (WeatherType.RAIN, 0.2),
                    (WeatherType.BLIZZARD, 0.1),
                ],
                1: [
                    (WeatherType.CLEAR, 0.5),
                    (WeatherType.RAIN, 0.2),
                    (WeatherType.SNOW, 0.2),
                    (WeatherType.HEATWAVE, 0.1),
                ],
                2: [
                    (WeatherType.SNOW, 0.4),
                    (WeatherType.CLEAR, 0.3),
                    (WeatherType.RAIN, 0.1),
                    (WeatherType.BLIZZARD, 0.2),
                ],
                3: [
                    (WeatherType.SNOW, 0.5),
                    (WeatherType.BLIZZARD, 0.3),
                    (WeatherType.CLEAR, 0.1),
                    (WeatherType.DROUGHT, 0.1),
                ],
            },
            TerrainType.GLACIER: {
                0: [
                    (WeatherType.SNOW, 0.5),
                    (WeatherType.CLEAR, 0.3),
                    (WeatherType.BLIZZARD, 0.2),
                ],
                1: [
                    (WeatherType.SNOW, 0.4),
                    (WeatherType.CLEAR, 0.3),
                    (WeatherType.BLIZZARD, 0.2),
                    (WeatherType.HEATWAVE, 0.1),
                ],
                2: [
                    (WeatherType.SNOW, 0.5),
                    (WeatherType.CLEAR, 0.2),
                    (WeatherType.BLIZZARD, 0.3),
                ],
                3: [
                    (WeatherType.SNOW, 0.6),
                    (WeatherType.BLIZZARD, 0.3),
                    (WeatherType.CLEAR, 0.1),
                ],
            },
            TerrainType.DESERT: {
                0: [
                    (WeatherType.CLEAR, 0.5),
                    (WeatherType.DROUGHT, 0.2),
                    (WeatherType.HEATWAVE, 0.2),
                    (WeatherType.STORM, 0.1),
                ],
                1: [
                    (WeatherType.CLEAR, 0.3),
                    (WeatherType.DROUGHT, 0.3),
                    (WeatherType.HEATWAVE, 0.3),
                    (WeatherType.STORM, 0.1),
                ],
                2: [
                    (WeatherType.CLEAR, 0.5),
                    (WeatherType.DROUGHT, 0.2),
                    (WeatherType.HEATWAVE, 0.2),
                    (WeatherType.STORM, 0.1),
                ],
                3: [
                    (WeatherType.CLEAR, 0.4),
                    (WeatherType.DROUGHT, 0.3),
                    (WeatherType.HEATWAVE, 0.2),
                    (WeatherType.STORM, 0.1),
                ],
            },
            TerrainType.BADLANDS: {
                0: [
                    (WeatherType.CLEAR, 0.4),
                    (WeatherType.DROUGHT, 0.2),
                    (WeatherType.HEATWAVE, 0.2),
                    (WeatherType.STORM, 0.2),
                ],
                1: [
                    (WeatherType.CLEAR, 0.2),
                    (WeatherType.DROUGHT, 0.3),
                    (WeatherType.HEATWAVE, 0.4),
                    (WeatherType.STORM, 0.1),
                ],
                2: [
                    (WeatherType.CLEAR, 0.4),
                    (WeatherType.DROUGHT, 0.2),
                    (WeatherType.HEATWAVE, 0.2),
                    (WeatherType.STORM, 0.2),
                ],
                3: [
                    (WeatherType.CLEAR, 0.3),
                    (WeatherType.DROUGHT, 0.3),
                    (WeatherType.HEATWAVE, 0.2),
                    (WeatherType.STORM, 0.2),
                ],
            },
            # Add more biomes as needed...
        }

        # Default probabilities for generic biomes
        default_probs = {
            0: [
                (WeatherType.CLEAR, 0.5),
                (WeatherType.RAIN, 0.2),
                (WeatherType.STORM, 0.1),
                (WeatherType.SNOW, 0.1),
                (WeatherType.HEATWAVE, 0.1),
            ],
            1: [
                (WeatherType.CLEAR, 0.5),
                (WeatherType.RAIN, 0.15),
                (WeatherType.STORM, 0.1),
                (WeatherType.SNOW, 0.05),
                (WeatherType.HEATWAVE, 0.2),
            ],
            2: [
                (WeatherType.CLEAR, 0.5),
                (WeatherType.RAIN, 0.2),
                (WeatherType.STORM, 0.1),
                (WeatherType.SNOW, 0.1),
                (WeatherType.HEATWAVE, 0.1),
            ],
            3: [
                (WeatherType.CLEAR, 0.4),
                (WeatherType.RAIN, 0.1),
                (WeatherType.STORM, 0.1),
                (WeatherType.SNOW, 0.3),
                (WeatherType.BLIZZARD, 0.1),
            ],
        }

        # Get the right probability table
        biome_probs = weather_probabilities.get(biome, default_probs)
        season_probs = biome_probs.get(season, default_probs[season])

        # Weighted random choice
        r = random.random()
        cumulative = 0.0
        for weather_type, prob in season_probs:
            cumulative += prob
            if r < cumulative:
                return weather_type
        # Fallback
        return season_probs[-1][0]

    def get_weather(self, coordinates):
        """
        Get the current weather for a given chunk or region.
        """
        return self.current_weather.get(coordinates, WeatherType.CLEAR)

    def get_weather_effects(self, weather_type):
        """
        Return the effects for a given weather type.
        """
        return WEATHER_EFFECTS.get(weather_type, WEATHER_EFFECTS[WeatherType.CLEAR])
