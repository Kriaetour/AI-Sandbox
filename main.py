import os
import glob
import logging
import random
import time
import argparse
import sys
from typing import Tuple, Dict
from world.engine import WorldEngine
from world import WeatherManager
from factions.faction import Faction
from npcs.npc import NPC
from tribes.tribal_manager import TribalManager
from tribes.tribe import TribalRole, TribalSymbol

# Global simulation speed settings
SIM_SPEED_RL_DECISIONS = 20  # RL agent makes decisions every N ticks
SIM_SPEED_SOCIAL_INTERVAL = 5  # Social interactions happen every N ticks
SIM_SPEED_TICK_DELAY = 0.0  # Delay between ticks in seconds (for real-time
# viewing)


# Tribe name generation system
class TribeGenerator:
    """Generates varied tribe names and characteristics"""

    def __init__(self):
        # Attempt to pull dynamic pools from databank; fallback to legacy
        # defaults if unavailable.
        try:
            from databank import get_databank

            db = get_databank()
            self.name_prefixes = db.get_all("tribe_prefixes") or [
                "River",
                "Stone",
                "Forest",
                "Mountain",
                "Desert",
                "Plains",
                "Valley",
                "Canyon",
            ]
            self.name_suffixes = db.get_all("tribe_suffixes") or [
                "folk",
                "tribe",
                "clan",
                "people",
            ]
            self.music_styles = db.get_all("music_styles") or ["drumming circles"]
            self.seasonal_rituals = db.get_all("seasonal_rituals") or ["spring planting ceremonies"]
            self.spirit_guides = db.get_all("spirit_guides") or ["wolf spirits"]
            self.creation_myths = db.get_all("creation_myths") or ["born from the first river"]
            # Specializations/environments attempt databank-backed loading
            # (with local fallback).
            # Supports BOTH dynamic external data and legacy embedded lists.
            self.specializations = db.get_all("tribe_specializations") or [
                "fishing",
                "farming",
                "gathering",
                "hunting",
                "crafting",
                "trading",
                "mining",
                "herding",
                "building",
                "healing",
                "spiritual",
                "warfare",
                "exploration",
                "storytelling",
                "metalworking",
                "weaving",
                "pottery",
            ]
            self.environments = db.get_all("tribe_environments") or [
                "river valley",
                "mountain peak",
                "dense forest",
                "open plains",
                "desert oasis",
                "coastal bay",
                "island chain",
                "canyon walls",
                "marsh lands",
                "lake shore",
                "hill country",
                "cave network",
                "prairie grassland",
                "swamp delta",
                "forest grove",
                "rocky ridge",
            ]
            # Attempt to load external bias map if present
            ext_bias = db.get_all("environment_specialization_bias")
            self._external_bias_loaded = isinstance(ext_bias, dict) and bool(ext_bias)

            # Attempt to load inverse selection probability from databank.
            # Supports either a direct scalar value or a single-item list under
            # keys: 'inverse_selection_probability' or
            # 'tribe_inverse_selection_probability'.
            loaded_inverse_prob = None
            for key in (
                "inverse_selection_probability",
                "tribe_inverse_selection_probability",
            ):
                try:
                    candidate = db.get_all(
                        key
                    )  # may return list or scalar depending on implementation
                    if candidate is None:
                        continue
                    # If list-like and not empty, take first element
                    if isinstance(candidate, (list, tuple)) and candidate:
                        candidate = candidate[0]
                    if isinstance(candidate, (int, float, str)):
                        loaded_inverse_prob = candidate
                        break
                except Exception:
                    continue
            self.inverse_selection_probability = 0.4  # default
            if loaded_inverse_prob is not None:
                try:
                    val = float(loaded_inverse_prob)
                    if 0.0 <= val <= 1.0:
                        self.inverse_selection_probability = val
                except Exception:
                    pass
        except Exception:
            # Fallback to prior static definitions if databank load fails
            self.name_prefixes = [
                "River",
                "Stone",
                "Forest",
                "Mountain",
                "Desert",
                "Plains",
                "Valley",
                "Canyon",
                "Coast",
                "Island",
                "Peak",
                "Summit",
                "Grove",
                "Thicket",
                "Meadow",
                "Prairie",
                "Marsh",
                "Swamp",
                "Lake",
                "Stream",
                "Creek",
                "Hill",
                "Ridge",
                "Cliff",
                "Cave",
                "Spring",
                "Falls",
                "Bay",
                "Harbor",
            ]
            self.name_suffixes = [
                "folk",
                "tribe",
                "clan",
                "people",
                "guardians",
                "keepers",
                "walkers",
                "hunters",
                "gatherers",
                "builders",
                "weavers",
                "smiths",
                "farmers",
                "fishers",
                "herders",
                "riders",
                "dwellers",
                "settlers",
                "nomads",
                "warriors",
                "shamans",
                "elders",
                "spirits",
                "winds",
                "stars",
            ]
            self.specializations = [
                "fishing",
                "farming",
                "gathering",
                "hunting",
                "crafting",
                "trading",
                "mining",
                "herding",
                "building",
                "healing",
                "spiritual",
                "warfare",
                "exploration",
                "storytelling",
                "metalworking",
                "weaving",
                "pottery",
            ]
            self.environments = [
                "river valley",
                "mountain peak",
                "dense forest",
                "open plains",
                "desert oasis",
                "coastal bay",
                "island chain",
                "canyon walls",
                "marsh lands",
                "lake shore",
                "hill country",
                "cave network",
                "prairie grassland",
                "swamp delta",
                "forest grove",
                "rocky ridge",
            ]
            self.music_styles = [
                "drumming circles",
                "flute melodies",
                "chanting rituals",
                "bone whistles",
                "string instruments",
                "vocal harmonies",
                "percussion ensembles",
                "wind instruments",
                "throat singing",
                "rhythmic clapping",
                "nature sound imitation",
                "group singing",
            ]
            self.seasonal_rituals = [
                "spring planting ceremonies",
                "summer solstice festivals",
                "autumn harvest feasts",
                "winter storytelling gatherings",
                "rain dance ceremonies",
                "hunting blessing rites",
                "migration celebration dances",
                "moon phase observances",
                "equinox gatherings",
                "new year renewal rituals",
                "coming of age ceremonies",
                "elder honoring festivals",
            ]
            self.spirit_guides = [
                "wolf spirits",
                "eagle guardians",
                "bear protectors",
                "raven messengers",
                "salmon ancestors",
                "tree spirits",
                "mountain deities",
                "river guardians",
                "wind spirits",
                "fire keepers",
                "earth mothers",
                "sky fathers",
                "moon watchers",
                "sun dancers",
                "star guides",
                "ocean elders",
            ]
            self.creation_myths = [
                "born from the first river",
                "descended from mountain peaks",
                "gifted by forest spirits",
                "forged in desert fires",
                "carried by ocean currents",
                "shaped by canyon winds",
                "blessed by prairie stars",
                "protected by island ancestors",
                "guided by cave echoes",
                "nurtured by meadow flowers",
                "strengthened by storm clouds",
                "united by tribal fires",
            ]

        # Thematic suffix mapping for specializations
        self.specialization_suffixes = {
            "fishing": [
                "fishers",
                "anglers",
                "harvesters",
                "catchers",
                "netters",
            ],
            "farming": [
                "farmers",
                "growers",
                "cultivators",
                "tillers",
                "planters",
            ],
            "gathering": [
                "gatherers",
                "collectors",
                "foragers",
                "harvesters",
                "pickers",
            ],
            "hunting": [
                "hunters",
                "stalkers",
                "predators",
                "trackers",
                "pursuers",
            ],
            "crafting": [
                "crafters",
                "makers",
                "artisans",
                "builders",
                "workers",
            ],
            "trading": [
                "traders",
                "merchants",
                "exchangers",
                "dealers",
                "brokers",
            ],
            "mining": [
                "miners",
                "diggers",
                "extractors",
                "quarrymen",
                "delvers",
            ],
            "herding": [
                "herders",
                "shepherds",
                "keepers",
                "ranchers",
                "tenders",
            ],
            "building": [
                "builders",
                "constructors",
                "makers",
                "erectors",
                "architects",
            ],
            "healing": [
                "healers",
                "menders",
                "curers",
                "physicians",
                "shamans",
            ],
            "spiritual": [
                "spirits",
                "mystics",
                "shamans",
                "seers",
                "visionaries",
            ],
            "warfare": [
                "warriors",
                "fighters",
                "guardians",
                "defenders",
                "protectors",
            ],
            "exploration": [
                "explorers",
                "pathfinders",
                "discoverers",
                "scouts",
                "wanderers",
            ],
            "storytelling": [
                "storytellers",
                "bards",
                "chroniclers",
                "narrators",
                "keepers",
            ],
            "metalworking": [
                "smiths",
                "forgers",
                "metalworkers",
                "craftsmen",
                "shapers",
            ],
            "weaving": [
                "weavers",
                "spinners",
                "loomworkers",
                "textilers",
                "braiders",
            ],
            "pottery": [
                "potters",
                "shapers",
                "ceramists",
                "throwers",
                "molders",
            ],
        }

        # Environment -> specialization bias weights (higher = more likely).
        # Unlisted specializations default to weight 1 for that environment.
        # This allows weighted selection while preserving full diversity.
        # Adopt external bias map if provided; else fallback defaults
        if hasattr(self, "_external_bias_loaded") and self._external_bias_loaded:
            from databank import get_databank  # local import safe here

            try:
                db = get_databank()
                loaded_bias = db.get_all("environment_specialization_bias")
                self.environment_specialization_bias = (
                    loaded_bias if isinstance(loaded_bias, dict) else {}
                )
            except Exception:
                self.environment_specialization_bias = {}
        else:
            self.environment_specialization_bias = {
                "river valley": {
                    "fishing": 3,
                    "farming": 2,
                    "trading": 2,
                    "pottery": 1.5,
                },
                "coastal bay": {
                    "fishing": 4,
                    "trading": 2,
                    "crafting": 1.5,
                    "storytelling": 1.2,
                },
                "island chain": {
                    "fishing": 4,
                    "exploration": 3,
                    "trading": 2,
                    "spiritual": 1.5,
                },
                "lake shore": {
                    "fishing": 3,
                    "pottery": 2,
                    "gathering": 1.5,
                    "storytelling": 1.3,
                },
                "dense forest": {
                    "gathering": 3,
                    "hunting": 2,
                    "spiritual": 2,
                    "storytelling": 1.5,
                },
                "forest grove": {
                    "gathering": 3,
                    "spiritual": 2.5,
                    "storytelling": 1.8,
                    "healing": 1.5,
                },
                "open plains": {
                    "herding": 3,
                    "hunting": 2,
                    "warfare": 1.5,
                    "exploration": 1.5,
                },
                "prairie grassland": {
                    "herding": 3,
                    "farming": 2,
                    "hunting": 1.5,
                },
                "mountain peak": {
                    "mining": 3,
                    "metalworking": 2.5,
                    "exploration": 2,
                    "spiritual": 1.5,
                },
                "rocky ridge": {"mining": 3, "warfare": 2, "metalworking": 2},
                "cave network": {
                    "mining": 3,
                    "spiritual": 2,
                    "storytelling": 1.5,
                },
                "canyon walls": {
                    "exploration": 3,
                    "trading": 2,
                    "hunting": 1.5,
                },
                "desert oasis": {
                    "trading": 3,
                    "farming": 2,
                    "spiritual": 2,
                    "weaving": 1.5,
                },
                "swamp delta": {
                    "gathering": 3,
                    "healing": 2.5,
                    "spiritual": 2,
                    "fishing": 1.5,
                },
                "marsh lands": {"gathering": 3, "healing": 2, "fishing": 2},
                "hill country": {
                    "herding": 2.5,
                    "farming": 2,
                    "weaving": 1.5,
                    "storytelling": 1.3,
                },
            }

        # Probability of using specialization-first inverse selection strategy
        # (May be set from databank in try block; else ensure default exists.)
        if not hasattr(self, "inverse_selection_probability"):
            self.inverse_selection_probability = 0.4

        # Build inverse map: specialization -> {environment: weight}
        self._build_inverse_bias()

    def _build_inverse_bias(self):
        self.specialization_environment_bias = {}
        for env, spec_map in self.environment_specialization_bias.items():
            if not isinstance(spec_map, dict):
                continue
            for spec, weight in spec_map.items():
                if spec not in self.specialization_environment_bias:
                    self.specialization_environment_bias[spec] = {}
                # Combine weights if duplicates appear
                self.specialization_environment_bias[spec][env] = (
                    float(weight) if weight is not None else 1.0
                )
        # Ensure every specialization has at least a uniform mapping if absent
        for spec in getattr(self, "specializations", []):
            if spec not in self.specialization_environment_bias:
                self.specialization_environment_bias[spec] = {
                    env: 1.0 for env in getattr(self, "environments", [])
                }

    def generate_tribe_name(self, specialization: str = None) -> str:
        """Generate a tribe name, optionally themed to a specialization"""
        prefix = random.choice(self.name_prefixes)

        if specialization and specialization in self.specialization_suffixes:
            suffixes = self.specialization_suffixes[specialization]
            suffix = random.choice(suffixes)
        else:
            suffix = random.choice(self.name_suffixes)

        # Sometimes combine two prefixes for variety
        if random.random() < 0.3:
            prefix2 = random.choice([p for p in self.name_prefixes if p != prefix])
            return f"{prefix}{prefix2}{suffix}".title()

        return f"{prefix}{suffix}".title()

    def generate_faction_name(self, specialization: str = None) -> str:
        """Generate a faction name, optionally themed to a specialization"""
        # Faction-specific prefixes (more formal/organizational than tribal)
        faction_prefixes = [
            "United", "Imperial", "Royal", "Grand", "Supreme", "Eternal", "Ancient",
            "Noble", "Mighty", "Glorious", "Sovereign", "Exalted", "Divine", "Celestial",
            "Arcane", "Mystic", "Primal", "Sacred", "Holy", "Blessed", "Radiant",
            "Luminous", "Brilliant", "Majestic", "Regal", "Stately", "Proud", "Valiant"
        ]

        # Faction-specific suffixes (more structured than tribal)
        faction_suffixes = [
            "Empire", "Kingdom", "Dominion", "Alliance", "Federation", "Confederation",
            "Order", "Brotherhood", "Sisterhood", "Guild", "Consortium", "Syndicate",
            "Collective", "Union", "League", "Council", "Assembly", "Society",
            "Company", "Corporation", "Clan", "House", "Dynasty", "Realm", "Domain"
        ]

        # Specialization-specific suffixes
        specialization_suffixes = {
            "military": ["Legion", "Guard", "Army", "Warriors", "Battalion", "Regiment"],
            "economic": ["Merchants", "Traders", "Consortium", "Company", "Guild", "Syndicate"],
            "religious": ["Faith", "Temple", "Order", "Brotherhood", "Sisterhood", "Cult"],
            "magical": ["Arcane", "Mystic", "Enchanters", "Sorcerers", "Wizards", "Mages"],
            "political": ["Senate", "Council", "Assembly", "Parliament", "Congress", "Union"]
        }

        prefix = random.choice(faction_prefixes)

        if specialization and specialization in specialization_suffixes:
            suffixes = specialization_suffixes[specialization]
            suffix = random.choice(suffixes)
        else:
            suffix = random.choice(faction_suffixes)

        # Sometimes combine two prefixes for variety
        if random.random() < 0.3:
            prefix2 = random.choice([p for p in faction_prefixes if p != prefix])
            return f"{prefix} {prefix2} {suffix}"

        return f"{prefix} {suffix}"

    def generate_npc_name(self, tribe_name: str = None) -> str:
        """Generate a unique NPC name, optionally themed to a tribe"""
        # NPC name components - first names/prefixes
        npc_first_parts = [
            "Aar",
            "Bel",
            "Cor",
            "Dar",
            "Eld",
            "Fin",
            "Gor",
            "Har",
            "Ith",
            "Jor",
            "Kar",
            "Lor",
            "Mor",
            "Nor",
            "Orn",
            "Par",
            "Quil",
            "Ran",
            "Sar",
            "Tor",
            "Ulf",
            "Var",
            "Wyn",
            "Xor",
            "Yar",
            "Zor",
            "Ash",
            "Bryn",
            "Cael",
            "Dain",
            "Eryn",
            "Fael",
            "Glyn",
            "Hael",
            "Ilyn",
            "Jaen",
            "Kaen",
            "Laen",
            "Maen",
            "Naen",
        ]

        # NPC name components - last parts/suffixes
        npc_last_parts = [
            "on",
            "ar",
            "el",
            "in",
            "or",
            "us",
            "yn",
            "is",
            "as",
            "en",
            "ith",
            "ath",
            "eth",
            "oth",
            "uth",
            "a",
            "e",
            "i",
            "o",
            "u",
            "wen",
            "wyn",
            "wen",
            "lyn",
            "ran",
            "dan",
            "lan",
            "man",
            "nan",
            "van",
        ]

        # Sometimes use tribe-themed names
        if tribe_name and random.random() < 0.4:
            # Extract prefix from tribe name (e.g., "Riverfolk" -> "Riv")
            tribe_prefix = tribe_name[:3].lower()
            if random.random() < 0.5:
                last_part = random.choice(npc_last_parts)
                return f"{tribe_prefix.capitalize()}{last_part}"
            else:
                return f"{random.choice(npc_first_parts)}{tribe_prefix}"

        # Standard name generation
        first = random.choice(npc_first_parts)
        last = random.choice(npc_last_parts)

        # Sometimes combine two first parts for variety
        if random.random() < 0.2:
            first2 = random.choice([p for p in npc_first_parts if p != first])
            return f"{first}{first2}{last}".title()

        return f"{first}{last}".title()

    def generate_tribe_config(self, location: Tuple[int, int]) -> Dict:
        """Generate a complete tribe configuration"""
        # Decide selection strategy: environment-first vs specialization-first
        use_inverse = random.random() < getattr(self, "inverse_selection_probability", 0.0)

        if not use_inverse:
            # Environment-first (original approach)
            environment = random.choice(self.environments)
            bias = getattr(
                self,
                "environment_specialization_bias",
                {},
            ).get(environment)
            if bias:
                weights = []
                for spec in self.specializations:
                    w = bias.get(spec, 1)
                    if w <= 0:
                        w = 1
                    weights.append(w)
                try:
                    specialization = random.choices(self.specializations, weights=weights, k=1)[0]
                except Exception:
                    specialization = random.choice(self.specializations)
            else:
                specialization = random.choice(self.specializations)
        else:
            # Specialization-first (inverse selection)
            specialization = random.choice(self.specializations)
            env_bias = getattr(self, "specialization_environment_bias", {}).get(specialization)
            if env_bias:
                env_weights = []
                for env in self.environments:
                    w = env_bias.get(env, 1)
                    if w <= 0:
                        w = 1
                    env_weights.append(w)
                try:
                    environment = random.choices(self.environments, weights=env_weights, k=1)[0]
                except Exception:
                    environment = random.choice(self.environments)
            else:
                environment = random.choice(self.environments)

        name = self.generate_tribe_name(specialization)
        music_style = random.choice(self.music_styles)
        seasonal_rituals = random.choice(self.seasonal_rituals)
        spirit_guides = random.choice(self.spirit_guides)
        creation_myth = random.choice(self.creation_myths)

        return {
            "name": name,
            "location": location,
            "specialization": specialization,
            "environment": environment,
            "symbol": random.choice([s.value for s in TribalSymbol]),
            "music_style": music_style,
            "seasonal_rituals": [seasonal_rituals],  # Make it a list for compatibility
            "spirit_guides": spirit_guides,
            "creation_myth": creation_myth,
        }


# Standalone faction name generator for import by other modules
def generate_faction_name(specialization: str = None) -> str:
    """Generate a faction name, optionally themed to a specialization."""
    generator = TribeGenerator()
    return generator.generate_faction_name(specialization)


# Plain text file logging only
root_logger = logging.getLogger()
root_logger.handlers.clear()  # Clear any existing handlers
logHandler = logging.FileHandler("log.txt", mode="w", encoding="utf-8")
formatter = logging.Formatter("%(asctime)s %(levelname)s %(name)s %(message)s")
logHandler.setFormatter(formatter)
root_logger.addHandler(logHandler)
_requested_level = os.environ.get("SANDBOX_LOG_LEVEL", "DEBUG").upper()
log_level = getattr(logging, _requested_level, logging.DEBUG)
root_logger.setLevel(log_level)
logger = logging.getLogger(__name__)

# Setup dialogue logger
dialogue_logger = logging.getLogger("dialogue")
dialogue_logger.handlers.clear()
dialogue_handler = logging.FileHandler("dialogue.log", mode="w", encoding="utf-8")
dialogue_formatter = logging.Formatter("%(asctime)s %(message)s")
dialogue_handler.setFormatter(dialogue_formatter)
dialogue_logger.addHandler(dialogue_handler)
dialogue_logger.setLevel(logging.INFO)


def read_log_file() -> str:
    """Read log.txt and strip leading null bytes."""
    with open("log.txt", "rb") as f:
        data = f.read().lstrip(b"\x00")
    return data.decode("utf-8", errors="ignore")


def clear_persistence() -> None:
    """Clears all saved chunk and faction data for a clean test run."""
    logger.info("--- Clearing persistence directory ---")
    if os.path.exists(WorldEngine.CHUNK_DIR):
        chunk_files = glob.glob(os.path.join(WorldEngine.CHUNK_DIR, "*.json"))
        for f in chunk_files:
            os.remove(f)
        logger.debug(f"Removed {len(chunk_files)} chunk files.")
    if os.path.exists(WorldEngine.FACTIONS_FILE):
        os.remove(WorldEngine.FACTIONS_FILE)
        logger.info("Removed factions file.")


def run_persistent_territory_simulation() -> None:
    """Demonstrates that faction territory claims are persisted across
    sessions."""
    clear_persistence()
    WORLD_SEED = 2025

    # --- SESSION 1: A faction expands and the world is shut down ---
    logger.info("--- SESSION 1: Faction expands and world shuts down ---")
    world1 = WorldEngine(seed=WORLD_SEED)

    # 1. Manually create a faction and an NPC pioneer
    start_coords = (10, 10)
    pioneer_faction_name = generate_faction_name("military")  # Generate a military-themed faction name
    fac = Faction(name=pioneer_faction_name, territory=[start_coords])
    world1.factions[fac.name] = fac
    npc = NPC(name="Zeb", coordinates=start_coords, faction_id=fac.name)
    start_chunk = world1.get_chunk(start_coords[0], start_coords[1])
    start_chunk.npcs.clear()
    start_chunk.npcs.append(npc)
    fac.add_member(npc.name)
    logger.info(
        f"- Faction '{fac.name}' established at {start_coords} " f"with pioneer '{npc.name}'."
    )

    # 2. Activate chunk and set NPC destination to new territory
    world1.activate_chunk(start_coords[0], start_coords[1])
    npc.destination = (10, 11)

    # 3. Run tick to move and claim territory
    world1.world_tick()

    # 4. Shut down the world to save all data
    world1.shutdown()

    # --- SESSION 2: Reload the world and verify the claim persisted ---
    logger.info("\n\n--- SESSION 2: Reloading world to verify persistence ---")
    world2 = WorldEngine(seed=WORLD_SEED)

    logger.info("- Verifying loaded faction state:")
    if "Pioneers" in world2.factions:
        reloaded_fac = world2.factions["Pioneers"]
        logger.info(
            f"  - Loaded faction '{reloaded_fac.name}' with territory: " f"{reloaded_fac.territory}"
        )
        if (10, 11) in reloaded_fac.territory and len(reloaded_fac.territory) == 2:
            logger.info(
                "  SUCCESS: Faction territory expansion was correctly saved " "and persisted."
            )
        else:
            logger.error("  FAILURE: Faction territory did not persist correctly.")
    else:
        logger.error("  FAILURE: 'Pioneers' faction was not loaded.")

    logger.info("\n\nVerification complete.")


def run_social_simulation() -> None:
    """Demonstrates the social interaction between NPCs."""
    clear_persistence()
    WORLD_SEED = 2026

    logger.info("--- Running Social Simulation ---")
    world = WorldEngine(seed=WORLD_SEED)

    # Generate a faction name for the social simulation
    social_faction_name = generate_faction_name("social")

    # Ensure faction exists
    if social_faction_name not in world.factions:
        world.factions[social_faction_name] = Faction(name=social_faction_name)

    # Create two NPCs in the same chunk and assign them to the faction
    npc1 = NPC(name="Alice", coordinates=(10, 10), faction_id=social_faction_name)
    npc2 = NPC(name="Bob", coordinates=(10, 10), faction_id=social_faction_name)

    # Add NPCs to the faction
    world.factions[social_faction_name].add_member(npc1.name)
    world.factions[social_faction_name].add_member(npc2.name)

    chunk = world.get_chunk(10, 10)
    chunk.npcs.extend([npc1, npc2])
    world.activate_chunk(10, 10)

    logger.info("--- Initial Dialogue Exchange ---")
    dialogue_context = "encounter"  # Or choose based on situation
    # Simple initial dialogue (tribal manager not yet initialized here)
    dialogue1 = npc1.generate_dialogue(npc2, dialogue_context, {})
    dialogue2 = npc2.generate_dialogue(npc1, dialogue_context, {})
    logger.debug(f"{npc1.name}: {dialogue1}")
    logger.debug(f"{npc2.name}: {dialogue2}")

    # Run a few ticks to observe social behavior
    num_ticks = int(input("Enter the number of ticks to run the simulation: "))
    logger.info(f"Running simulation for {num_ticks} days...")

    for i in range(num_ticks):
        world.world_tick()
        if i % 5 == 0:  # Every 5 days, exchange dialogue
            context = random.choice(["idle", "encounter", "trade", "hostility"])
            d1 = npc1.generate_dialogue(npc2, context, {})
            d2 = npc2.generate_dialogue(npc1, context, {})
            logger.debug(f"Day {i}: {npc1.name}: {d1}")
            logger.debug(f"Day {i}: {npc2.name}: {d2}")

    logger.info("Simulation complete.")
    world.shutdown()


def run_tribal_simulation(num_ticks: int = 50):
    """Demonstrates the integrated tribal system with world engine."""
    clear_persistence()
    WORLD_SEED = 2027

    logger.info("--- Running Tribal Simulation ---")

    # Initialize world and tribal systems
    world = WorldEngine(seed=WORLD_SEED)

    # Initialize the three main factions
    world.factions["Human"] = Faction(name="Human", territory=[])
    world.factions["Predator"] = Faction(name="Predator", territory=[])
    world.factions["Wildlife"] = Faction(name="Wildlife", territory=[])
    logger.info("Initialized main factions: Human, Predator, Wildlife")

    tribal_manager = TribalManager()
    weather_manager = WeatherManager(world)

    # Initialize tribe generator
    tribe_generator = TribeGenerator()

    # Create varied number of tribes (4-8) with random characteristics
    num_tribes = random.randint(4, 8)
    logger.info(f"Generating {num_tribes} varied tribes")

    total_spawned_npcs = 0
    created_tribe_locations = []  # Track locations since Tribe may not store location attribute
    for i in range(num_tribes):
        # Generate random location for the tribe
        location = (random.randint(-20, 20), random.randint(-20, 20))

        # Generate tribe configuration
        tribe_config = tribe_generator.generate_tribe_config(location)
        tribe_name = tribe_config["name"]
        founder_id = f"founder_{tribe_name.lower().replace(' ', '_')}"

        # Create the tribe (tribes are subdivisions within the Human faction)
        tribe = tribal_manager.create_tribe(tribe_name, founder_id, location)
        created_tribe_locations.append(location)
        logger.info(
            f"Created tribe '{tribe_name}' at {location} with specialization: "
            f"{tribe_config['specialization']}"
        )

        # Tribes are subdivisions of the Human faction - no separate
        # faction needed
        # All tribal NPCs belong to the "Human" faction

        # Add some initial members and spawn NPC entities so the world has a
        # population
        member_count = random.randint(3, 7)
        for j in range(member_count):  # Vary member count
            member_id = f"{tribe_name.lower().replace(' ', '_')}_member_{j}"
            tribal_manager.tribes[tribe_name].add_member(member_id, random.choice(list(TribalRole)))
            # Spawn NPC with same identifier as name for simplicity
            try:
                # All tribal NPCs belong to Human faction
                npc = NPC(
                    name=member_id,
                    coordinates=location,
                    faction_id="Human",
                )
                # Cultural inheritance snapshot if available
                try:
                    if hasattr(npc, "inherit_culture"):
                        npc.inherit_culture(tribal_manager.tribes[tribe_name])
                except Exception:
                    pass
                # Add NPC to chunk & Human faction
                chunk = world.get_chunk(location[0], location[1])
                if npc not in chunk.npcs:
                    chunk.npcs.append(npc)
                world.factions["Human"].add_member(npc.name)
                total_spawned_npcs += 1
            except Exception as e:
                logger.error(f"Failed to spawn NPC '{member_id}' for tribe " f"'{tribe_name}': {e}")

        # Apply generated characteristics to the tribe
        if hasattr(tribal_manager.tribes[tribe_name], "economic_specialization"):
            tribal_manager.tribes[tribe_name].economic_specialization = tribe_config[
                "specialization"
            ]
        if hasattr(tribal_manager.tribes[tribe_name], "cultural_quirks"):
            tribal_manager.tribes[tribe_name].cultural_quirks.update(
                {
                    "music_style": tribe_config["music_style"],
                    "seasonal_rituals": tribe_config["seasonal_rituals"],
                    "spirit_guides": tribe_config["spirit_guides"],
                }
            )
        if hasattr(tribal_manager.tribes[tribe_name], "spiritual_beliefs"):
            tribal_manager.tribes[tribe_name].spiritual_beliefs.update(
                {"creation_myth": tribe_config["creation_myth"]}
            )

    logger.info(
        f"Spawned {total_spawned_npcs} NPCs across {num_tribes} tribes " f"for tribal simulation"
    )

    # Collect all tribe locations for chunk activation
    # Use stored creation locations (tribe may not persist a .location attr)
    tribe_locations = created_tribe_locations

    # Activate chunks around tribal camps
    for location in tribe_locations:
        world.activate_chunk(location[0], location[1])
        # Activate surrounding chunks for territory
        for dx in [-1, 0, 1]:
            for dy in [-1, 0, 1]:
                world.activate_chunk(location[0] + dx, location[1] + dy)

    logger.info(
        "Initialized %d tribes with world integration",
        len(tribal_manager.tribes),
    )

    # Run tribal simulation
    logger.info(f"Running tribal simulation for {num_ticks} days...")
    logger.info(f"Starting tribal simulation with {len(tribal_manager.tribes)} tribes")

    for i in range(num_ticks):
        # Process tribal dynamics
        tribal_manager.process_tribal_dynamics(world)
        # Update weather
        weather_manager.update_weather(world.current_hour)
        # Process world tick
        world.world_tick()

        # Log tribal status every 10 days
        if i % 10 == 0:
            logger.info(f"Day {i}: Processing...")
            logger.info(f"Day {i}: Tribal Status Update")
            for tribe_name, tribe in tribal_manager.tribes.items():
                wellbeing = tribe.get_wellbeing_score()
                logger.info(
                    f"  {tribe_name}: {len(tribe.member_ids)} members, "
                    f"wellbeing {wellbeing:.2f}"
                )

                # Show cultural and economic info
                if tribe.cultural_quirks["music_style"]:
                    logger.info(
                        f"    Culture: {tribe.cultural_quirks['music_style']} "
                        f"music, totems: {', '.join(tribe.culture['totems'])}"
                    )
                if tribe.economic_specialization:
                    logger.info(f"    Specialization: {tribe.economic_specialization}")
                if tribe.spiritual_beliefs["prophecies"]:
                    num_prophecies = len(tribe.spiritual_beliefs["prophecies"])
                    logger.info(f"    Active Prophecies: {num_prophecies}")

                # Show diplomatic relations
                # Cache diplomacy handle to shorten lines
                td = tribal_manager.tribal_diplomacy
                for other_tribe in tribal_manager.tribes:
                    if other_tribe != tribe_name:
                        relation = td.get_diplomatic_status(
                            tribe, tribal_manager.tribes[other_tribe]
                        )
                        if relation:
                            trust = round(relation.get("trust_level", 0.5))
                            logger.info(f"    ↔ {other_tribe}: Trust {trust}")

                # Show trade networks
                if tribe.trade_network:
                    partners = ", ".join(tribe.trade_network)
                    logger.info(f"    Trade Partners: {partners}")

                # Active ritual/custom effects summary (compact)
                if hasattr(tribe, "active_ritual_effects") and tribe.active_ritual_effects:
                    # Show up to 3 active ritual names with days remaining
                    try:
                        current_day = getattr(world, "current_day", 0)
                        summaries = []
                        for eff in tribe.active_ritual_effects[:3]:
                            rem = max(
                                0,
                                eff.get("expires_day", current_day) - current_day,
                            )
                            summaries.append(f"{eff.get('name')}({rem}d)")
                        more = (
                            ""
                            if len(tribe.active_ritual_effects) <= 3
                            else f" +{len(tribe.active_ritual_effects)-3}"
                        )
                        rituals_str = ", ".join(summaries) + more
                        logger.info(f"    Rituals: {rituals_str}")
                    except Exception:
                        pass

                # Cultural status enhancement line (compact)
                try:
                    if hasattr(tribe, "cultural_status_report"):
                        cstat = tribe.cultural_status_report()
                        # Lexicon details moved to DEBUG to reduce verbosity
                        vals = [
                            (v, round(cstat["value_scores"][v], 2)) for v in cstat["top_values"]
                        ]
                        pres = cstat["prestige"]
                        rit = cstat["ritual_count"]
                        act = len(cstat["active_rituals"])
                        mut = [m["trigger"] for m in cstat["last_mutations"]]
                        streaks = cstat.get("streaks")
                        logger.info(f"    Culture+: vals={vals}")
                        logger.info(
                            f"    pres={pres} rit={rit} act={act} mut={mut} " f"streaks={streaks}"
                        )
                        lexsz = cstat["lexicon_size"]
                        logger.debug(
                            "    Culture+ Lexicon Detail: lexicon_size=%s",
                            lexsz,
                        )
                except Exception:
                    pass

                logger.info("")  # Empty line for readability
            # Language diagnostics (compact)
            for tribe_name, tribe in tribal_manager.tribes.items():
                try:
                    report = tribe.language_report()
                    pidgin_partners = list(
                        tribe.cultural_ledger.get("language", {}).get("pidgins", {}).keys()
                    )
                    lex_size = report["lexicon_size"]
                    vol = report["volatility"]
                    best_conv = report.get("best_convergence_partner")
                    recent = [e["concept"] for e in report["recent_events"]]
                    logger.debug(f"    Lang {tribe_name}: size={lex_size} vol={vol}")
                    pidgins_count = len(pidgin_partners)
                    logger.debug(f"    best_conv={best_conv}")
                    logger.debug(f"    pidgins={pidgins_count}")
                    logger.debug(f"    recent={recent}")
                except Exception:
                    pass

    logger.info("Tribal simulation complete.")
    try:
        if hasattr(tribal_manager, "save_latest_language_analytics"):
            tribal_manager.save_latest_language_analytics()
    except Exception:
        pass
    # Population diagnostics before world shutdown
    try:
        if hasattr(world, "diagnostics_snapshot"):
            snap = world.diagnostics_snapshot()
            msg = (
                "Population Diagnostics (tribal run): "
                f"tick={snap['tick']} "
                f"total={snap['total_npcs']} "
                f"actionable={snap['actionable_npcs']} "
                f"idle={snap['idle_npcs']} "
                f"idle%={snap['idle_pct']:.1f} "
                f"no_action_streak={snap['no_action_streak']}"
            )
            logger.info(msg)
    except Exception:
        pass
    world.shutdown()

    # Final cultural summary block
    logger.info("=== Final Cultural Summaries ===")
    for tribe_name, tribe in tribal_manager.tribes.items():
        try:
            if hasattr(tribe, "cultural_status_report"):
                cs = tribe.cultural_status_report()
                last_mut = [m["trigger"] for m in cs["last_mutations"]]
                logger.info(
                    f"{tribe_name}: values={cs['value_scores']} "
                    f"prestige={cs['prestige']} "
                    f"rituals={cs['ritual_count']} "
                    f"commemorations={cs['commemorative_rituals']} "
                    f"last_mut={last_mut}"
                )
                logger.debug(
                    "%s: lexicon_size=%s",
                    tribe_name,
                    cs["lexicon_size"],
                )
        except Exception:
            pass

    # Export cultural summary artifact
    try:
        if hasattr(tribal_manager, "export_cultural_summary"):
            tribal_manager.export_cultural_summary()
    except Exception:
        pass


def run_combined_social_tribal_simulation(num_ticks: int):
    """Run combined simulation with tribal dynamics and social interactions."""
    start_time = time.time()
    clear_persistence()
    WORLD_SEED = 2029

    logger.info("--- Running Combined Social-Tribal Simulation ---")

    # Initialize world and tribal systems
    world = WorldEngine(seed=WORLD_SEED)
    tribal_manager = TribalManager()
    weather_manager = WeatherManager(world)

    # Initialize tribe generator
    tribe_generator = TribeGenerator()

    # Create varied number of tribes (3-5) with random characteristics
    num_tribes = random.randint(3, 5)
    logger.info("Generating %d varied tribes for combined simulation", num_tribes)

    # Track all NPCs for social interactions
    all_npcs = []

    for i in range(num_tribes):
        # Generate random location for the tribe
        location = (random.randint(-20, 20), random.randint(-20, 20))

        # Generate tribe configuration
        tribe_config = tribe_generator.generate_tribe_config(location)
        tribe_name = tribe_config["name"]
        founder_id = f"founder_{tribe_name.lower().replace(' ', '_')}"

        # Create the tribe
        tribe = tribal_manager.create_tribe(tribe_name, founder_id, location)
        tribe.economic_specialization = tribe_config["specialization"]

        # Create faction for this tribe if it doesn't exist
        if tribe_name not in world.factions:
            world.factions[tribe_name] = Faction(
                name=tribe_name,
                territory=[location],
            )

        # Add individual NPCs to the tribe and faction
        num_members = random.randint(2, 4)  # Vary member count
        for j in range(num_members):
            member_id = f"{tribe_name.lower().replace(' ', '_')}_member_{j}"
            # Short names like Riv0, Sto1, etc.
            npc_name = f"{tribe_name[:3]}{j}"

            # Create NPC
            npc = NPC(
                name=npc_name,
                coordinates=location,
                faction_id=tribe_name,
            )
            # Generational cultural inheritance
            try:
                tribe_obj = tribal_manager.tribes.get(tribe_name)
                if tribe_obj and hasattr(npc, "inherit_culture"):
                    npc.inherit_culture(tribe_obj)
            except Exception:
                pass

            # Assign personality traits
            personality_traits = ["introvert", "extrovert", "neutral"]
            npc.traits.append(random.choice(personality_traits))

            # Add to tribe
            role = random.choice(list(TribalRole))
            tribal_manager.tribes[tribe_name].add_member(member_id, role)

            # Add to faction
            world.factions[tribe_name].add_member(npc.name)

            # Add to chunk
            chunk = world.get_chunk(location[0], location[1])
            chunk.npcs.append(npc)
            all_npcs.append(npc)

            logger.info(
                "Created NPC '%s' in tribe '%s' at %s",
                npc_name,
                tribe_name,
                location,
            )

        # Apply generated characteristics to the tribe
        if hasattr(tribal_manager.tribes[tribe_name], "cultural_quirks"):
            tribal_manager.tribes[tribe_name].cultural_quirks.update(
                {
                    "music_style": tribe_config["music_style"],
                    "seasonal_rituals": tribe_config["seasonal_rituals"],
                    "spirit_guides": tribe_config["spirit_guides"],
                }
            )
        if hasattr(tribal_manager.tribes[tribe_name], "spiritual_beliefs"):
            tribal_manager.tribes[tribe_name].spiritual_beliefs.update(
                {"creation_myth": tribe_config["creation_myth"]}
            )

        # Activate chunks around tribal camps
        world.activate_chunk(location[0], location[1])
        for dx in [-1, 0, 1]:
            for dy in [-1, 0, 1]:
                world.activate_chunk(location[0] + dx, location[1] + dy)

    logger.info(
        "Initialized %d tribes with %d total NPCs",
        len(tribal_manager.tribes),
        len(all_npcs),
    )

    logger.info("Combined Social-Tribal Simulation starting...")
    logger.info(
        "Running with %d tribes and %d NPCs",
        len(tribal_manager.tribes),
        len(all_npcs),
    )
    logger.info("NPCs will interact socially during tribal dynamics")
    logger.info("")

    # Initialize timing variables for component breakdown
    tribal_time = 0
    world_time = 0
    social_time = 0
    logging_time = 0

    # Run simulation with cProfile
    import cProfile
    import pstats
    from io import StringIO

    profiler = cProfile.Profile()
    profiler.enable()

    # Run combined simulation
    for i in range(num_ticks):
        tick_start = time.time()

        # Process tribal dynamics
        tribal_start = time.time()
        tribal_manager.process_tribal_dynamics(world)
        tribal_delta = time.time() - tribal_start
        tribal_time += tribal_delta

        # Process world tick (moves NPCs, updates factions)
        world_start = time.time()
        world.world_tick()
        world_delta = time.time() - world_start
        world_time += world_delta

        # Update weather (treat as part of logging/other overhead, fast call)
        weather_manager.update_weather(world.current_hour)

        social_delta = 0.0
        # Social interactions every few ticks
        if i % 5 == 0:
            social_start = time.time()
            current_npcs = []
            for chunk in world.active_chunks.values():
                current_npcs.extend(chunk.npcs)

            if len(current_npcs) >= 2:
                npc1, npc2 = random.sample(current_npcs, 2)
                if (
                    abs(npc1.coordinates[0] - npc2.coordinates[0]) <= 1
                    and abs(npc1.coordinates[1] - npc2.coordinates[1]) <= 1
                ):
                    contexts = ["encounter", "trade", "idle", "hostility"]
                    context = random.choice(contexts)
                    dialogue1 = npc1.generate_dialogue(
                        npc2,
                        context,
                        tribal_manager.tribal_diplomacy,
                        tribal_manager.tribes,
                    )
                    dialogue2 = npc2.generate_dialogue(
                        npc1,
                        context,
                        tribal_manager.tribal_diplomacy,
                        tribal_manager.tribes,
                    )
                    logger.debug(
                        "💬 %s (%s): %s",
                        npc1.name,
                        npc1.faction_id,
                        dialogue1,
                    )
                    logger.debug(
                        "💬 %s (%s): %s",
                        npc2.name,
                        npc2.faction_id,
                        dialogue2,
                    )
                    # Log to dialogue file
                    dialogue_logger.info(
                        "[TICK %d] %s->%s (%s) | %s",
                        i,
                        npc1.name,
                        npc2.name,
                        context,
                        dialogue1,
                    )
                    dialogue_logger.info(
                        "[TICK %d] %s->%s (%s) | %s",
                        i,
                        npc2.name,
                        npc1.name,
                        context,
                        dialogue2,
                    )
            social_delta = time.time() - social_start
            social_time += social_delta

        # Residual time in this tick counts as logging/other overhead
        tick_elapsed = time.time() - tick_start
        accounted = tribal_delta + world_delta + social_delta
        residual = tick_elapsed - accounted
        logging_time += residual

    profiler.disable()

    # Calculate total time for component breakdown
    total_time = tribal_time + world_time + social_time + logging_time

    # Print cProfile results
    s = StringIO()
    ps = pstats.Stats(profiler, stream=s).sort_stats("cumulative")
    ps.print_stats(20)
    profiling_output = s.getvalue()

    print("\n" + "=" * 60)
    print("PROFILING RESULTS - cProfile Output")
    print("=" * 60)
    print(profiling_output)

    # Print component timing breakdown
    print("\n" + "=" * 60)
    print("PROFILING RESULTS - Component Timing Breakdown")
    print("=" * 60)
    print(f"Total simulation time: {total_time:.2f} seconds")
    print(f"Time per tick: {total_time/num_ticks:.6f} seconds")
    print()

    def pct(part):
        return (part / total_time * 100) if total_time > 0 else 0.0

    print(f"Tribal Dynamics: {tribal_time:.2f}s ({pct(tribal_time):.1f}%)")
    print(f"World Tick: {world_time:.2f}s ({pct(world_time):.1f}%)")
    print(f"Social Interactions: {social_time:.2f}s ({pct(social_time):.1f}%)")
    print(f"Logging: {logging_time:.2f}s ({pct(logging_time):.1f}%)")

    logger.info("Combined social-tribal simulation complete.")
    try:
        if hasattr(tribal_manager, "save_latest_language_analytics"):
            tribal_manager.save_latest_language_analytics()
    except Exception:
        pass
    # Population diagnostics before world shutdown
    try:
        if hasattr(world, "diagnostics_snapshot"):
            snap = world.diagnostics_snapshot()
            msg = (
                "Population Diagnostics (combined run): "
                f"tick={snap['tick']} "
                f"total={snap['total_npcs']} "
                f"actionable={snap['actionable_npcs']} "
                f"idle={snap['idle_npcs']} "
                f"idle%={snap['idle_pct']:.1f} "
                f"no_action_streak={snap['no_action_streak']}"
            )
            logger.info(msg)
    except Exception:
        pass
    world.shutdown()
    end_time = time.time()
    elapsed = end_time - start_time
    print(f"Simulation completed in {elapsed:.2f} seconds")

    # Final cultural summaries for combined simulation
    logger.info("=== Final Cultural Summaries (Combined) ===")
    for tribe_name, tribe in tribal_manager.tribes.items():
        try:
            if hasattr(tribe, "cultural_status_report"):
                cs = tribe.cultural_status_report()
                last_mut = [m["trigger"] for m in cs["last_mutations"]]
                logger.info(
                    f"{tribe_name}: values={cs['value_scores']} "
                    f"prestige={cs['prestige']} "
                    f"rituals={cs['ritual_count']} "
                    f"commemorations={cs['commemorative_rituals']} "
                    f"last_mut={last_mut}"
                )
                lex_size = cs["lexicon_size"]
                logger.debug("%s: lexicon_size=%s", tribe_name, lex_size)
        except Exception:
            pass

    # Export cultural summary artifact
    try:
        if hasattr(tribal_manager, "export_cultural_summary"):
            tribal_manager.export_cultural_summary()
    except Exception:
        pass


def run_narrative_simulation(
    num_ticks: int = 1000,
    narrative_interval: int = 100,
    init_pop_min: int = 300,
    init_pop_max: int = 400,
):
    """
    Run simulation with periodic LLM narrative generation for storytelling.
    This mode enables LLM for narrative purposes without using it for training.
    """
    print("[NARRATIVE] Starting narrative simulation with periodic LLM " "consultation")
    print(f"[NARRATIVE] Ticks: {num_ticks}, Narrative interval: " f"{narrative_interval}")
    print(f"[NARRATIVE] Population range: {init_pop_min}-{init_pop_max}")

    # Import required modules
    from core_sim import _configure_environment_flags, _parse_features
    from world.engine import WorldEngine
    from tribes.tribal_manager import TribalManager
    from tribes.tribe import TribalRole
    from npcs.npc import NPC
    from gemini_narrative import generate_narrative
    import time
    import random

    # Setup environment (similar to core_sim)
    features = _parse_features()
    _configure_environment_flags(features)

    # Create world
    world = WorldEngine(seed=42, disable_faction_saving=True)

    # Initialize the three main factions
    world.factions["Human"] = Faction(name="Human", territory=[])
    world.factions["Predator"] = Faction(name="Predator", territory=[])
    world.factions["Wildlife"] = Faction(name="Wildlife", territory=[])

    # Bootstrap initial population (similar to RL control)
    tm = TribalManager()
    target_pop = random.randint(init_pop_min, init_pop_max)

    # Create a default tribe for bootstrapping using TribeGenerator
    tribe_generator = TribeGenerator()
    tribe_name = tribe_generator.generate_tribe_name()
    founder_name = tribe_generator.generate_npc_name(tribe_name)
    founder = NPC(
        name=founder_name,
        coordinates=(0, 0),
        faction_id="Human",
    )  # All tribal NPCs belong to Human faction
    tm.create_tribe(tribe_name, founder_name, (0, 0))
    # Tribes are subdivisions of Human faction - no separate faction needed
    world.factions["Human"].add_member(founder.name)
    world.get_chunk(0, 0).npcs.append(founder)
    world.activate_chunk(0, 0)

    # Bootstrap additional population
    roles = [
        TribalRole.LEADER,
        TribalRole.WARRIOR,
        TribalRole.GATHERER,
        TribalRole.SHAMAN,
        TribalRole.CRAFTER,
        TribalRole.HUNTER,
    ]
    tribe_names = [tribe_name]
    spawn_needed = target_pop - 1  # -1 for founder
    ri = 0

    while spawn_needed > 0 and tribe_names:
        tname = tribe_names[ri % len(tribe_names)]
        loc = getattr(tm.tribes[tname], "location", (0, 0))
        npc_name = tribe_generator.generate_npc_name(tname)
        npc = NPC(
            name=npc_name,
            coordinates=loc,
            faction_id="Human",
        )  # All tribal NPCs belong to Human faction
        try:
            tm.tribes[tname].add_member(npc_name, random.choice(roles))
            # Add to Human faction
            world.factions["Human"].add_member(npc.name)
            world.get_chunk(*loc).npcs.append(npc)
            world.activate_chunk(*loc)
        except Exception:
            pass
        spawn_needed -= 1
        ri += 1

    # Provision food
    for ch in world.active_chunks.values():
        ch.resources["food"] = max(ch.resources.get("food", 0), 200)
        ch.resources["plant"] = max(ch.resources.get("plant", 0), 150)

    initial_pop = sum(len(ch.npcs) for ch in world.active_chunks.values())
    print(f"[NARRATIVE] Starting simulation with {initial_pop} " f"initial population")

    # Track narrative events
    narrative_events = []
    last_narrative_tick = 0

    def narrative_callback(world, tick):
        nonlocal last_narrative_tick, narrative_events

        # Generate narrative at specified intervals
        if tick - last_narrative_tick >= narrative_interval:
            try:
                print(f"\n[NARRATIVE] Generating story at tick {tick}...")

                # Get current world state for narrative
                total_population = sum(len(chunk.npcs) for chunk in world.chunks.values())
                active_tribes = len(world.factions)

                # Generate a narrative summary
                prompt = (
                    "Create a narrative summary of the current simulation "
                    f"state at tick {tick}.\n"
                    f"Population: {total_population} NPCs across "
                    f"{active_tribes} tribes.\n"
                    "Describe the current state of the world, tribal "
                    "dynamics, and any notable events.\n"
                    "Keep it engaging and story-like, around 100-150 words."
                )

                narrative = generate_narrative(prompt, max_tokens=200)
                print(f"[NARRATIVE] 📖 {narrative}")

                # Store narrative event
                narrative_events.append(
                    {
                        "tick": tick,
                        "population": total_population,
                        "tribes": active_tribes,
                        "story": narrative,
                    }
                )

                last_narrative_tick = tick

            except Exception as e:
                print(f"[NARRATIVE] Error generating narrative: {e}")

    # Run simulation loop (similar to core_sim but with narrative callback)
    start_time = time.time()
    tick = 0

    try:
        while tick < num_ticks:
            # Run one tick
            world.world_tick()

            # Call narrative callback
            narrative_callback(world, tick)

            tick += 1

            # Progress indicator
            if tick % 100 == 0:
                current_pop = sum(len(chunk.npcs) for chunk in world.chunks.values())
                print(f"[NARRATIVE] Tick {tick}/{num_ticks} - " f"Population: {current_pop}")

        end_time = time.time()
        final_pop = sum(len(chunk.npcs) for chunk in world.chunks.values())

        print("\n[NARRATIVE] Simulation complete!")
        print(f"[NARRATIVE] Total time: {end_time - start_time:.1f} seconds")
        print(f"[NARRATIVE] Final population: {final_pop}")
        print(f"[NARRATIVE] Summaries: {len(narrative_events)}")

    except Exception as e:
        print(f"[NARRATIVE] Failed to run narrative simulation: {e}")


def generate_event(faction, world, tick) -> str:
    """Generate a short saying-style event line."""
    try:
        from databank import get_databank

        saying = random.choice(get_databank().get_all("sayings"))
        return f"Saying: {faction.name} shares: '{saying}'"
    except Exception:
        return f"Saying: {faction.name} speaks of enduring cycles."


def generate_rumor(faction, world, tick) -> str:
    location = random.choice(faction.territory) if getattr(faction, "territory", None) else (0, 0)
    other_factions = (
        [f for f in getattr(world, "factions", {}).keys() if f != faction.name]
        if hasattr(world, "factions")
        else []
    )
    other_faction = random.choice(other_factions) if other_factions else "Unknown"
    try:
        from databank import get_databank

        db = get_databank()
        rumor_texts = db.get_random("rumors", 1, unique=True)
        if rumor_texts:
            # Simple embedding of faction context when placeholders not present
            base = rumor_texts[0]
            # Placeholder substitution supported
            return f"Rumor: {base}".format(
                faction=faction.name,
                other_faction=other_faction,
                location=location,
            )
    except Exception:
        pass
    # Fallback legacy templates
    templates = [
        "{faction} is planning an attack on {other_faction}.",
        "{faction} found a hidden artifact.",
        "{faction} is low on resources.",
        "{faction} is forming an alliance with {other_faction}.",
        "{faction} is building a stronghold at {location}.",
        "{faction} is recruiting new members.",
        "{faction} is exploring the wilds near {location}.",
        "{faction} is trading with {other_faction}.",
        "{faction} is facing internal strife.",
        "{faction} is celebrating a festival at {location}.",
    ]
    template = random.choice(templates)
    return "Rumor: " + template.format(
        faction=faction.name, location=location, other_faction=other_faction
    )


def generate_saying(faction, world, tick) -> str:
    try:
        from databank import get_databank

        db = get_databank()
        saying = db.get_random("sayings", 1, unique=True)
        if saying:
            return f"'{saying[0]}'"
    except Exception:
        pass
    fallback = [
        "Unity is strength.",
        "The river remembers.",
        "Every end is a new beginning.",
    ]
    return f"'{random.choice(fallback)}'"


def setup_logging(level=logging.INFO) -> None:
    """Setup logging configuration."""
    root_logger = logging.getLogger()
    root_logger.handlers.clear()  # Clear any existing handlers

    # File handler - always logs all levels to file
    logHandler = logging.FileHandler("log.txt", mode="w", encoding="utf-8")
    formatter = logging.Formatter("%(asctime)s %(levelname)s %(name)s %(message)s")
    logHandler.setFormatter(formatter)
    root_logger.addHandler(logHandler)

    # Console handler - respects the selected logging level
    console_handler = logging.StreamHandler()
    console_formatter = logging.Formatter("%(levelname)s: %(message)s")
    console_handler.setFormatter(console_formatter)
    # Only show messages at or above selected level
    console_handler.setLevel(level)
    root_logger.addHandler(console_handler)

    root_logger.setLevel(logging.DEBUG)  # Root logger accepts all levels
    logging.getLogger(__name__)

    # Set the level for the file handler to DEBUG (log everything to file)
    logHandler.setLevel(logging.DEBUG)

    # Console handler level is already set above


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="AI Sandbox unified simulation runner")
    parser.add_argument(
        "--log",
        dest="log_level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Console log level (file always DEBUG)",
    )
    sub = parser.add_subparsers(dest="mode", help="Simulation mode (use one)")

    # Core balanced simulation (from core_sim.py)
    p_core = sub.add_parser(
        "core",
        help=("Balanced core stability simulation " "(population, waves, dialogue)"),
    )
    p_core.add_argument(
        "--ticks",
        type=int,
        default=1000,
        help="Number of ticks (default 1000)",
    )
    # Backward-compatible optional positional ticks (deprecated)
    p_core.add_argument(
        "ticks_positional",
        nargs="?",
        type=int,
        help=argparse.SUPPRESS,
    )

    # Persistence territory demo
    sub.add_parser("territory", help="Territory persistence demonstration")

    # Simple social
    p_social = sub.add_parser("social", help="NPC social dialogue showcase")
    p_social.add_argument("--ticks", type=int, default=50, help="Number of ticks (default 50)")

    # Tribal only
    p_tribal = sub.add_parser("tribal", help="Tribal dynamics only simulation")
    p_tribal.add_argument("--ticks", type=int, default=100, help="Number of ticks (default 100)")

    # Combined
    p_combined = sub.add_parser(
        "combined", help="Combined tribal + social simulation with profiling"
    )
    p_combined.add_argument("--ticks", type=int, default=200, help="Number of ticks (default 200)")
    p_combined.add_argument(
        "--profile",
        action="store_true",
        help="(Reserved) Profiling already integrated",
    )

    # Population wave focused core simulation (alias of core but called out)
    p_waves = sub.add_parser(
        "waves",
        help=("Population wave stability demo " "(uses core sim with wave overrides)"),
    )
    p_waves.add_argument("--ticks", type=int, default=600, help="Number of ticks (default 600)")

    # RL training prototype
    p_rl = sub.add_parser(
        "rl",
        help="Prototype RL control loop (tabular Q-learning)",
    )
    p_rl.add_argument(
        "--ticks",
        type=int,
        default=2000,
        help="Max ticks per RL episode (default 2000)",
    )
    p_rl.add_argument(
        "--episodes",
        type=int,
        default=1,
        help="Number of RL episodes to run (default 1)",
    )
    p_rl.add_argument(
        "--epsilon-start",
        type=float,
        default=0.3,
        help="Starting epsilon for multi-episode training",
    )
    p_rl.add_argument("--epsilon-min", type=float, default=0.05, help="Minimum epsilon floor")
    p_rl.add_argument(
        "--epsilon-decay",
        type=float,
        default=0.92,
        help="Multiplicative epsilon decay per episode",
    )
    p_rl.add_argument(
        "--intervention-interval",
        type=int,
        default=20,
        help="How often (in ticks) the RL agent makes decisions (default 20)",
    )
    p_rl.add_argument(
        "--save-q",
        type=str,
        default=None,
        help="Path to save Q-table after training",
    )
    p_rl.add_argument(
        "--load-q",
        type=str,
        default=None,
        help="Path to load existing Q-table before training",
    )
    p_rl.add_argument(
        "--init-pop-min",
        type=int,
        default=330,
        help="Minimum initial population for RL episodes (default 330)",
    )
    p_rl.add_argument(
        "--init-pop-max",
        type=int,
        default=350,
        help="Maximum initial population for RL episodes (default 350)",
    )

    # Military RL-enhanced simulation
    p_military_rl = sub.add_parser("military-rl", help="Run simulation with optimized military RL agents")
    p_military_rl.add_argument(
        "--ticks",
        type=int,
        default=2000,
        help="Number of ticks to run (default 2000)",
    )
    p_military_rl.add_argument(
        "--model",
        type=str,
        required=False,
        help="Path to trained military model (auto-selected if not provided)",
    )
    p_military_rl.add_argument(
        "--epsilon",
        type=float,
        default=0.1,
        help="Exploration rate for military decisions (default 0.1, use 0.0 for pure exploitation)",
    )
    p_military_rl.add_argument(
        "--decision-interval",
        type=int,
        default=20,
        help="Ticks between military RL decisions (default 20)",
    )
    p_military_rl.add_argument(
        "--tribes",
        type=int,
        default=8,
        help="Number of tribes to create (default 8)",
    )

    # RL-controlled simulation (uses trained agent)
    p_rl_control = sub.add_parser("rl-control", help="Run simulation with trained RL agent control")
    p_rl_control.add_argument(
        "--ticks",
        type=int,
        default=2000,
        help="Number of ticks to run (default 2000)",
    )
    p_rl_control.add_argument(
        "--load-q",
        type=str,
        required=False,
        help=("Path to trained Q-table file " "(auto-selected if not provided)"),
    )
    p_rl_control.add_argument(
        "--control-interval",
        type=int,
        default=10,
        help="Ticks between RL decisions (default 10)",
    )
    p_rl_control.add_argument(
        "--init-pop-min", type=int, default=330, help="Minimum initial population"
    )
    p_rl_control.add_argument(
        "--init-pop-max", type=int, default=350, help="Maximum initial population"
    )

    # Narrative mode with LLM storytelling (no training)
    p_narrative = sub.add_parser(
        "narrative",
        help="Run simulation with periodic LLM narrative generation (no training)",
    )
    p_narrative.add_argument(
        "--ticks",
        type=int,
        default=1000,
        help="Number of ticks to run (default 1000)",
    )
    p_narrative.add_argument(
        "--narrative-interval",
        type=int,
        default=100,
        help="Ticks between narrative generations (default 100)",
    )
    p_narrative.add_argument(
        "--init-pop-min",
        type=int,
        default=300,
        help="Minimum initial population",
    )
    p_narrative.add_argument(
        "--init-pop-max",
        type=int,
        default=400,
        help="Maximum initial population",
    )

    # Interactive menu subcommand (same as default when no subcommand)
    sub.add_parser("menu", help="Interactive menu (default if no subcommand)")

    return parser


def main_cli(argv=None) -> None:
    parser = _build_arg_parser()
    args = parser.parse_args(argv)

    setup_logging(getattr(logging, args.log_level, logging.INFO))

    if not args.mode:
        # Launch interactive menu if no mode provided
        return interactive_menu()

    if args.mode == "core":
        from core_sim import run_core_sim

        run_core_sim(args.ticks)
    elif args.mode == "territory":
        run_persistent_territory_simulation()
    elif args.mode == "social":
        # Maintain original prompt if user passes 0 or negative
        ticks = args.ticks
        if ticks <= 0:
            try:
                ticks = int(input("Enter ticks for social simulation: "))
            except Exception:
                ticks = 50
        # Set env var consumed by social sim for tick count
        os.environ["AI_SANDBOX_SOCIAL_TICKS"] = str(ticks)
        # Call social sim (input() reads are avoided via env override)
        run_social_simulation()
    elif args.mode == "tribal":
        run_tribal_simulation(args.ticks)
    elif args.mode == "combined":
        run_combined_social_tribal_simulation(args.ticks)
    elif args.mode == "waves":
        from core_sim import run_core_sim

        run_core_sim(args.ticks)
    elif args.mode == "rl":
        try:
            if args.episodes and args.episodes > 1:
                from rl_agent import run_rl_training

                run_rl_training(
                    episodes=args.episodes,
                    max_ticks=args.ticks,
                    epsilon_start=args.epsilon_start,
                    epsilon_min=args.epsilon_min,
                    epsilon_decay=args.epsilon_decay,
                    intervention_interval=args.intervention_interval,
                    init_pop_min=args.init_pop_min,
                    init_pop_max=args.init_pop_max,
                    save_path=args.save_q,
                    load_path=args.load_q,
                )
            else:
                from rl_agent import run_simple_rl_episode

                run_simple_rl_episode(
                    max_ticks=args.ticks,
                    init_pop_min=args.init_pop_min,
                    init_pop_max=args.init_pop_max,
                )
        except Exception as e:
            print(f"[RL] Failed to run RL session: {e}")
    elif args.mode == "rl-control":
        try:
            from rl_agent import run_simulation_with_rl_control

            run_simulation_with_rl_control(
                num_ticks=args.ticks,
                qtable_path=args.load_q,
                control_interval=args.control_interval,
                init_pop_min=args.init_pop_min,
                init_pop_max=args.init_pop_max,
            )
        except Exception as e:
            print(f"[RL-CONTROL] Failed to run RL-controlled simulation: {e}")
    elif args.mode == "narrative":
        try:
            run_narrative_simulation(
                num_ticks=args.ticks,
                narrative_interval=args.narrative_interval,
                init_pop_min=args.init_pop_min,
                init_pop_max=args.init_pop_max,
            )
        except Exception as e:
            print(f"[NARRATIVE] Failed to run narrative simulation: {e}")
    elif args.mode == "menu":
        interactive_menu()
    else:
        parser.error(f"Unknown mode: {args.mode}")

    # end legacy menu removal


def interactive_menu() -> None:
    while True:
        print("\n=== AI Sandbox Interactive Menu ===")
        print("1. Core Simulations")
        print("2. Training")
        print("3. Tests & Demos")
        print("4. Tools & Analysis")
        print("5. Settings")
        print("6. Exit")
        choice = input("Select option: ").strip()

        if choice == "1":
            core_simulations_menu()
        elif choice == "2":
            training_menu()
        elif choice == "3":
            tests_demos_menu()
        elif choice == "4":
            tools_analysis_menu()
        elif choice == "5":
            settings_menu()
        elif choice == "6":
            print("Exiting AI Sandbox.")
            break
        else:
            print("Invalid choice.")


def core_simulations_menu() -> None:
    """Core simulation modes submenu."""
    while True:
        print("\n--- Core Simulations ---")
        print("1. Complete simulation (tribal + social + weather)")
        print("2. Population management (stability testing)")
        print("3. Social simulation (dialogue focus)")
        print("4. Tribal simulation (culture focus)")
        print("5. Military RL Enhanced (optimized strategic warfare)")
        print("6. Live RL Simulation (real-time AI control)")
        print("7. Back to main menu")
        choice = input("Select option: ").strip()

        if choice == "1":
            # Complete simulation - combined tribal + social + weather + RL population management
            print("Complete simulation includes:")
            print("- Tribal dynamics with multiple cultures")
            print("- Social dialogue between NPCs")
            print("- Weather system integration")
            print("- RL-controlled population management")
            print("")

            ticks = input("Ticks (default 200): ").strip() or "200"
            try:
                t = int(ticks)
            except (ValueError, TypeError):
                t = 200

            # Run truly complete simulation with integrated RL control
            try:
                run_complete_simulation_with_rl(t)
            except Exception as e:
                print(f"[COMPLETE] Failed to run complete simulation: {e}")
                import traceback

                traceback.print_exc()
        elif choice == "2":
            # Population management - core balanced simulation
            from core_sim import run_core_sim

            ticks = input("Ticks (default 500): ").strip() or "500"
            try:
                t = int(ticks)
            except (ValueError, TypeError):
                t = 500
            run_core_sim(t)
        elif choice == "3":
            ticks = input("Ticks (default 60): ").strip() or "60"
            try:
                t = int(ticks)
            except (ValueError, TypeError):
                t = 60
            os.environ["AI_SANDBOX_SOCIAL_TICKS"] = str(t)
            run_social_simulation()
        elif choice == "4":
            ticks = input("Ticks (default 150): ").strip() or "150"
            try:
                t = int(ticks)
            except (ValueError, TypeError):
                t = 150
            run_tribal_simulation(t)
        elif choice == "5":
            # NEW: Military RL Enhanced
            print("⚔️  Military RL Enhanced Simulation:")
            print("- Optimized military strategy AI")
            print("- 71,954 trained states for strategic decisions")
            print("- Context-aware tactical planning")
            print("- Enhanced tribal warfare dynamics")
            print("")

            ticks = input("Ticks (default 1000): ").strip() or "1000"
            epsilon = input("Exploration rate (0.0 for pure optimal, 0.1 for learning, default 0.0): ").strip() or "0.0"
            tribes = input("Number of tribes (default 6): ").strip() or "6"
            
            try:
                t = int(ticks)
                e = float(epsilon)
                tr = int(tribes)
            except (ValueError, TypeError):
                t, e, tr = 1000, 0.0, 6

            try:
                from military_rl_integration import run_simulation_with_military_rl
                run_simulation_with_military_rl(
                    num_ticks=t,
                    epsilon=e,
                    num_tribes=tr,
                    verbose=True
                )
            except Exception as e:
                print(f"[MILITARY RL] Failed to run military RL simulation: {e}")
                import traceback
                traceback.print_exc()
        elif choice == "6":
            # Live RL Simulation
            print("🎮 Live RL Simulation:")
            print("- Real-time RL agent decision making")
            print("- Population + Diplomacy control")
            print("- Live learning and adaptation")
            print("")

            ticks = input("Ticks (default 300): ").strip() or "300"
            try:
                t = int(ticks)
            except (ValueError, TypeError):
                t = 300

            try:
                run_live_rl_simulation(t)
            except Exception as e:
                print(f"[RL LIVE] Failed to run live RL simulation: {e}")
                import traceback
                traceback.print_exc()
        elif choice == "7":
            break
        else:
            print("Invalid choice.")


def training_menu() -> None:
    """Training submenu for RL and machine learning."""
    while True:
        print("\n--- Training ---")
        print("1. RL training (basic)")
        print("2. Train RL agent (advanced - multi-range, parallel, LLM)")
        print("3. RL-controlled simulation")
        print("4. Train Diplomacy RL agent")
        print("5. Back to main menu")
        choice = input("Select option: ").strip()

        if choice == "1":
            # Basic RL Training (simple parameters)
            try:
                episodes = input("Number of episodes (default 10): ").strip() or "10"
                try:
                    ep = int(episodes)
                except (ValueError, TypeError):
                    ep = 10
                ticks = input("Max ticks per episode (default 2000): ").strip() or "2000"
                try:
                    t = int(ticks)
                except (ValueError, TypeError):
                    t = 2000
                from rl_agent import run_rl_training

                run_rl_training(episodes=ep, max_ticks=t)
            except Exception as e:
                print(f"[RL] Failed to run basic RL training: {e}")
        elif choice == "2":
            # Advanced RL training (multi-range, parallel, LLM features)
            try:
                import subprocess

                print(
                    "Launching advanced RL training (multi-range populations, parallel processing, LLM narratives)..."
                )
                subprocess.run([sys.executable, "train_rl_agent.py"])
            except Exception as e:
                print(f"[TRAIN-RL] Failed to launch advanced RL training: {e}")
        elif choice == "3":
            # RL-controlled simulation
            try:
                ticks = input("Ticks (default 2000): ").strip() or "2000"
                try:
                    t = int(ticks)
                except (ValueError, TypeError):
                    t = 2000
                from rl_agent import run_simulation_with_rl_control

                run_simulation_with_rl_control(num_ticks=t)
            except Exception as e:
                print(f"[RL-CONTROL] Failed to run RL-controlled simulation: {e}")
        elif choice == "4":
            # Diplomacy RL training
            try:
                import subprocess

                print("Launching Diplomacy RL training (tribal diplomacy strategies)...")
                subprocess.run([sys.executable, "train_diplomacy_rl.py"])
            except Exception as e:
                print(f"[DIPLOMACY-RL] Failed to launch diplomacy RL training: {e}")
        elif choice == "5":
            break
        else:
            print("Invalid choice.")


def tests_demos_menu():
    """Tests and demonstrations submenu."""
    while True:
        print("\n--- Tests & Demos ---")
        print("1. Territory persistence demo")
        print("2. Population wave demo")
        print("3. Narrative simulation")
        print("4. Back to main menu")
        choice = input("Select option: ").strip()

        if choice == "1":
            run_persistent_territory_simulation()
        elif choice == "2":
            from core_sim import run_core_sim

            ticks = input("Ticks (default 600): ").strip() or "600"
            try:
                t = int(ticks)
            except (ValueError, TypeError):
                t = 600
            run_core_sim(t)
        elif choice == "3":
            # Narrative simulation
            try:
                ticks = input("Ticks (default 1000): ").strip() or "1000"
                try:
                    t = int(ticks)
                except (ValueError, TypeError):
                    t = 1000
                narrative_interval = input("Narrative interval (default 100): ").strip() or "100"
                try:
                    interval = int(narrative_interval)
                except (ValueError, TypeError):
                    interval = 100
                run_narrative_simulation(num_ticks=t, narrative_interval=interval)
            except Exception as e:
                print(f"[NARRATIVE] Failed to run narrative simulation: {e}")
        elif choice == "4":
            break
        else:
            print("Invalid choice.")


def tools_analysis_menu():
    """Tools and analysis submenu."""
    while True:
        print("\n--- Tools & Analysis ---")
        print("1. Analyze Q-tables")
        print("2. Plot RL analytics")
        print("3. Back to main menu")
        choice = input("Select option: ").strip()

        if choice == "1":
            # Analyze Q-tables
            try:
                import subprocess

                print("Launching Q-table analysis...")
                subprocess.run([sys.executable, "analyze_qtables.py"])
            except Exception as e:
                print(f"[ANALYZE] Failed to launch Q-table analysis: {e}")
        elif choice == "2":
            # Plot RL analytics
            try:
                import subprocess

                print("Launching RL analytics plotting...")
                subprocess.run([sys.executable, "plot_rl_analytics.py"])
            except Exception as e:
                print(f"[PLOT] Failed to launch RL analytics plotting: {e}")
        elif choice == "3":
            break
        else:
            print("Invalid choice.")


def settings_menu():
    """Settings submenu."""
    while True:
        print("\n--- Settings ---")
        print("1. Set console log level")
        print("2. Simulation speed settings")
        print("3. Back to main menu")
        choice = input("Select option: ").strip()

        if choice == "1":
            lvl = input("Log level (DEBUG/INFO/WARNING/ERROR) [INFO]: ").strip().upper() or "INFO"
            if lvl not in ("DEBUG", "INFO", "WARNING", "ERROR"):
                print("Invalid log level.")
            else:
                setup_logging(getattr(logging, lvl))
                print(f"Console log level set to {lvl}")
        elif choice == "2":
            simulation_speed_menu()
        elif choice == "3":
            break
        else:
            print("Invalid choice.")


def simulation_speed_menu():
    """Simulation speed settings submenu."""
    global SIM_SPEED_RL_DECISIONS, SIM_SPEED_SOCIAL_INTERVAL, SIM_SPEED_TICK_DELAY

    while True:
        print("\n--- Simulation Speed Settings ---")
        print(f"1. RL Decision Interval: Every {SIM_SPEED_RL_DECISIONS} ticks")
        print(f"2. Social Interaction Interval: Every {SIM_SPEED_SOCIAL_INTERVAL} ticks")
        print(f"3. Tick Delay: {SIM_SPEED_TICK_DELAY:.2f} seconds")
        print("4. Preset: Fast (minimal delays)")
        print("5. Preset: Normal (balanced)")
        print("6. Preset: Slow (detailed viewing)")
        print("7. Back to settings")
        choice = input("Select option: ").strip()

        if choice == "1":
            try:
                val = int(
                    input(f"RL decision interval (ticks) [{SIM_SPEED_RL_DECISIONS}]: ").strip()
                    or SIM_SPEED_RL_DECISIONS
                )
                if val > 0:
                    SIM_SPEED_RL_DECISIONS = val
                    print(f"RL decision interval set to {val} ticks")
                else:
                    print("Value must be positive")
            except ValueError:
                print("Invalid number")
        elif choice == "2":
            try:
                val = int(
                    input(
                        f"Social interaction interval (ticks) [{SIM_SPEED_SOCIAL_INTERVAL}]: "
                    ).strip()
                    or SIM_SPEED_SOCIAL_INTERVAL
                )
                if val > 0:
                    SIM_SPEED_SOCIAL_INTERVAL = val
                    print(f"Social interaction interval set to {val} ticks")

                else:
                    print("Value must be positive")
            except ValueError:
                print("Invalid number")
        elif choice == "3":
            try:
                val = float(
                    input(f"Tick delay (seconds) [{SIM_SPEED_TICK_DELAY:.2f}]: ").strip()
                    or SIM_SPEED_TICK_DELAY
                )
                if val >= 0:
                    SIM_SPEED_TICK_DELAY = val
                    print(f"Tick delay set to {val:.2f} seconds")
                else:
                    print("Value must be non-negative")
            except ValueError:
                print("Invalid number")
        elif choice == "4":
            # Fast preset
            SIM_SPEED_RL_DECISIONS = 10
            SIM_SPEED_SOCIAL_INTERVAL = 2
            SIM_SPEED_TICK_DELAY = 0.0
            print("Set to Fast preset: RL every 10 ticks, social every 2 ticks, no delay")
        elif choice == "5":
            # Normal preset
            SIM_SPEED_RL_DECISIONS = 20
            SIM_SPEED_SOCIAL_INTERVAL = 5
            SIM_SPEED_TICK_DELAY = 0.0
            print("Set to Normal preset: RL every 20 ticks, social every 5 ticks, no delay")
        elif choice == "6":
            # Slow preset
            SIM_SPEED_RL_DECISIONS = 50
            SIM_SPEED_SOCIAL_INTERVAL = 10
            SIM_SPEED_TICK_DELAY = 0.1
            print("Set to Slow preset: RL every 50 ticks, social every 10 ticks, 0.1s delay")
        elif choice == "7":
            break
        else:
            print("Invalid choice.")


def run_live_rl_simulation(num_ticks: int = 300):
    """Run live RL simulation with real-time agent decision making."""
    import time
    import random
    import logging
    from world.engine import WorldEngine
    from tribes.tribal_manager import TribalManager
    from world import WeatherManager
    from rl_live_integration import (
        initialize_rl_agents,
        make_rl_decisions,
        update_rl_learning,
        save_rl_state,
        get_rl_status
    )
    from core_sim import setup_dialogue_logger

    # Set up logger
    logger = logging.getLogger(__name__)
    setup_logging()

    # Setup dialogue logger
    dialogue_logger = setup_dialogue_logger()
    dialogue_logger.info("=== Live RL Simulation Dialogue Log Started ===")

    logger.info(f"🎮 Starting Live RL Simulation for {num_ticks} ticks")
    start_time = time.time()

    # Clear any existing persistence
    clear_persistence()
    WORLD_SEED = random.randint(1000, 9999)

    # Initialize world and systems
    world = WorldEngine(seed=WORLD_SEED)
    tribal_manager = TribalManager()
    weather_manager = WeatherManager(world)

    # Initialize tribe generator
    tribe_generator = TribeGenerator()

    # Create tribes
    num_tribes = random.randint(3, 5)
    logger.info(f"🎭 Generating {num_tribes} tribes for RL simulation")

    all_npcs = []

    for i in range(num_tribes):
        location = (random.randint(-15, 15), random.randint(-15, 15))
        tribe_config = tribe_generator.generate_tribe_config(location)
        tribe_name = tribe_config["name"]
        founder_id = f"founder_{tribe_name.lower().replace(' ', '_')}"

        # Create tribe
        tribe = tribal_manager.create_tribe(tribe_name, founder_id, location)
        tribe.economic_specialization = tribe_config["specialization"]

        # Create faction
        if tribe_name not in world.factions:
            world.factions[tribe_name] = Faction(name=tribe_name, territory=[location])

        # Add NPCs
        num_members = random.randint(2, 4)
        for j in range(num_members):
            member_id = f"{tribe_name.lower().replace(' ', '_')}_member_{j}"
            npc_name = f"{tribe_name[:3]}{j}"

            npc = NPC(name=npc_name, coordinates=location, faction_id=tribe_name)

            # Cultural inheritance
            try:
                tribe_obj = tribal_manager.tribes.get(tribe_name)
                if tribe_obj and hasattr(npc, "inherit_culture"):
                    npc.inherit_culture(tribe_obj)
            except Exception:
                pass

            # Add personality
            personality_traits = ["introvert", "extrovert", "neutral"]
            npc.traits.append(random.choice(personality_traits))

            # Add to systems
            role = random.choice(list(TribalRole))
            tribal_manager.tribes[tribe_name].add_member(member_id, role)
            world.factions[tribe_name].add_member(npc.name)

            # Add to world
            chunk = world.get_chunk(location[0], location[1])
            chunk.npcs.append(npc)
            all_npcs.append(npc)

        # Apply tribe characteristics
        if hasattr(tribal_manager.tribes[tribe_name], "cultural_quirks"):
            tribal_manager.tribes[tribe_name].cultural_quirks.update(
                {
                    "music_style": tribe_config["music_style"],
                    "seasonal_rituals": tribe_config["seasonal_rituals"],
                    "spirit_guides": tribe_config["spirit_guides"],
                }
            )

        # Activate chunks
        world.activate_chunk(location[0], location[1])
        for dx in [-1, 0, 1]:
            for dy in [-1, 0, 1]:
                world.activate_chunk(location[0] + dx, location[1] + dy)

    # Initialize RL Agents
    logger.info("🤖 Initializing RL Agents...")
    rl_initialized = initialize_rl_agents(auto_load=True)

    if not rl_initialized:
        logger.warning("⚠️  No RL agents available. Running simulation without RL control.")
        print("⚠️  No trained RL agents found. Train agents first or continue without RL.")

    rl_status = get_rl_status()
    logger.info(f"RL Status: {rl_status}")

    # Attach RL manager to WorldEngine for integrated decision making
    if rl_initialized:
        from rl_live_integration import rl_manager
        world.rl_agent_manager = rl_manager
        logger.info("🔗 RL Agent Manager attached to WorldEngine")

    # Simulation loop
    logger.info(f"🚀 Live RL Simulation starting with {len(tribal_manager.tribes)} tribes and {len(all_npcs)} NPCs")

    for tick in range(num_ticks):
        tick_start = time.time()

        # Process tribal dynamics
        tribal_manager.process_tribal_dynamics(world)

        # Process world tick
        world.world_tick()

        # Update weather
        weather_manager.update_weather(world.current_hour)

        # RL Decision Making
        if rl_initialized:
            rl_actions = make_rl_decisions(world)

            if rl_actions:
                logger.info(f"🎯 RL Actions at tick {tick}: {rl_actions}")

                # Calculate reward and update learning
                # This is a simplified reward - you can make it more sophisticated
                current_pop = sum(len(ch.npcs) for ch in world.active_chunks.values())
                reward = current_pop * 0.01  # Simple population-based reward

                update_rl_learning(world, reward)

        # Social interactions (every few ticks)
        if tick % 5 == 0:
            current_npcs = []
            for chunk in world.active_chunks.values():
                current_npcs.extend(chunk.npcs)

            if len(current_npcs) >= 2:
                npc1, npc2 = random.sample(current_npcs, 2)
                if (abs(npc1.coordinates[0] - npc2.coordinates[0]) <= 1 and
                    abs(npc1.coordinates[1] - npc2.coordinates[1]) <= 1):
                    try:
                        # Trigger social interaction
                        if hasattr(npc1, 'interact_with') and hasattr(npc2, 'interact_with'):
                            npc1.interact_with(npc2)
                    except Exception as e:
                        logger.debug(f"Social interaction error: {e}")

        # Progress reporting
        if tick % 50 == 0:
            current_pop = sum(len(ch.npcs) for ch in world.active_chunks.values())
            logger.info(f"📊 Tick {tick}/{num_ticks} - Population: {current_pop}, Tribes={len(tribal_manager.tribes)}")

        # Small delay for real-time feel
        elapsed = time.time() - tick_start
        if elapsed < 0.01:  # Cap at 100 FPS
            time.sleep(0.01 - elapsed)

    # Save RL state
    if rl_initialized:
        save_rl_state()
        logger.info("💾 RL agent states saved")

    # Final statistics
    end_time = time.time()
    total_time = end_time - start_time

    final_pop = sum(len(ch.npcs) for ch in world.active_chunks.values())
    final_tribes = len(tribal_manager.tribes)

    logger.info("🎉 Live RL Simulation Complete!")
    logger.info(f"⏱️  Total time: {total_time:.2f}s ({total_time/num_ticks:.3f}s per tick)")
    logger.info(f"👥 Final population: {final_pop}")
    logger.info(f"🏛️  Final tribes: {final_tribes}")
    logger.info(f"🎮 RL Status: {get_rl_status()}")

    print("\nLive RL Simulation Complete!")
    print(f"Total time: {total_time:.2f}s")
    print(f"Final population: {final_pop}")
    print(f"Final tribes: {final_tribes}")
    print(f"RL agents active: {rl_initialized}")


def run_complete_simulation_with_rl(num_ticks: int = 1000):
    import time
    import random
    import logging
    from world.engine import WorldEngine
    from tribes.tribal_manager import TribalManager
    from world import WeatherManager
    from rl_agent import (
        TabularQLearningAgent,
        ACTION_NAMES,
        select_qtable_for_population,
    )
    from core_sim import setup_dialogue_logger
    import json

    # Set up logger for this function
    logger = logging.getLogger(__name__)

    # Ensure logging is set up
    setup_logging()

    # Setup dialogue logger
    dialogue_logger = setup_dialogue_logger()
    dialogue_logger.info("=== Complete Simulation Dialogue Log Started ===")

    logger.info(f"Starting complete simulation with RL control for {num_ticks} ticks")
    start_time = time.time()

    start_time = time.time()
    clear_persistence()
    WORLD_SEED = 2029

    logger.info("--- Running Complete Simulation with RL Population Control ---")

    # Initialize world and tribal systems
    world = WorldEngine(seed=WORLD_SEED)
    tribal_manager = TribalManager()
    weather_manager = WeatherManager(world)

    # Initialize tribe generator
    tribe_generator = TribeGenerator()

    # Create varied number of tribes (3-5) with random characteristics
    num_tribes = random.randint(3, 5)
    logger.info(f"Generating {num_tribes} varied tribes for complete simulation")

    # Track all NPCs for social interactions
    all_npcs = []

    for i in range(num_tribes):
        # Generate random location for the tribe
        location = (random.randint(-20, 20), random.randint(-20, 20))

        # Generate tribe configuration
        tribe_config = tribe_generator.generate_tribe_config(location)
        tribe_name = tribe_config["name"]
        founder_id = f"founder_{tribe_name.lower().replace(' ', '_')}"

        # Create the tribe
        tribe = tribal_manager.create_tribe(tribe_name, founder_id, location)
        tribe.economic_specialization = tribe_config["specialization"]

        # Create faction for this tribe if it doesn't exist
        if tribe_name not in world.factions:
            world.factions[tribe_name] = Faction(name=tribe_name, territory=[location])

        # Add individual NPCs to the tribe and faction
        num_members = random.randint(2, 4)  # Vary member count
        for j in range(num_members):
            member_id = f"{tribe_name.lower().replace(' ', '_')}_member_{j}"
            npc_name = f"{tribe_name[:3]}{j}"  # Short names like Riv0, Sto1, etc.

            # Create NPC
            npc = NPC(name=npc_name, coordinates=location, faction_id=tribe_name)
            # Generational cultural inheritance
            try:
                tribe_obj = tribal_manager.tribes.get(tribe_name)
                if tribe_obj and hasattr(npc, "inherit_culture"):
                    npc.inherit_culture(tribe_obj)
            except Exception:
                pass

            # Assign personality traits
            personality_traits = ["introvert", "extrovert", "neutral"]
            npc.traits.append(random.choice(personality_traits))

            # Add to tribe
            role = random.choice(list(TribalRole))
            tribal_manager.tribes[tribe_name].add_member(member_id, role)

            # Add to faction
            world.factions[tribe_name].add_member(npc.name)

            # Add to chunk
            chunk = world.get_chunk(location[0], location[1])
            chunk.npcs.append(npc)
            all_npcs.append(npc)

            logger.info(f"Created NPC '{npc_name}' in tribe '{tribe_name}' at {location}")

        # Apply generated characteristics to the tribe
        if hasattr(tribal_manager.tribes[tribe_name], "cultural_quirks"):
            tribal_manager.tribes[tribe_name].cultural_quirks.update(
                {
                    "music_style": tribe_config["music_style"],
                    "seasonal_rituals": tribe_config["seasonal_rituals"],
                    "spirit_guides": tribe_config["spirit_guides"],
                }
            )
        if hasattr(tribal_manager.tribes[tribe_name], "spiritual_beliefs"):
            tribal_manager.tribes[tribe_name].spiritual_beliefs.update(
                {"creation_myth": tribe_config["creation_myth"]}
            )

        # Activate chunks around tribal camps
        world.activate_chunk(location[0], location[1])
        for dx in [-1, 0, 1]:
            for dy in [-1, 0, 1]:
                world.activate_chunk(location[0] + dx, location[1] + dy)


    # Initialize RL Agent for population control
    logger.info("Initializing RL population control agent...")
    qtable_path = select_qtable_for_population(50, 100)
    if not qtable_path:
        logger.warning("No suitable Q-table found, running without RL population control")
        rl_agent = None
    else:
        rl_agent = TabularQLearningAgent(
            num_actions=len(ACTION_NAMES),
            epsilon=0.0,  # No exploration - use trained policy
            lr=0.0,  # No learning
            gamma=0.95,
            pop_bin_size=10,
            food_bin_size=500,
            births_cap=5,
            starv_cap=5,
        )
        try:
            with open(qtable_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            for k, qvals in data.items():
                try:
                    state_key = (
                        tuple(int(x) for x in k.strip("()").split(",")) if k.startswith("(") else k
                    )
                except Exception:
                    state_key = k
                rl_agent.q[state_key] = qvals
            logger.info(f"Loaded RL Q-table with {len(rl_agent.q)} states from {qtable_path}")
        except Exception as e:
            logger.warning(f"Failed to load RL Q-table: {e}")
            rl_agent = None

    # --- Military RL Integration ---
    logger.info("Initializing Military RL Controller...")
    try:
        from military_rl_integration import MilitaryRLController
        military_controller = MilitaryRLController(epsilon=0.0, decision_interval=20)
        logger.info(f"Military RL Controller loaded with {military_controller.agent.q_table and len(military_controller.agent.q_table)} states")
    except Exception as e:
        logger.warning(f"Failed to initialize Military RL Controller: {e}")
        military_controller = None

    logger.info(f"Initialized {len(tribal_manager.tribes)} tribes with {len(all_npcs)} total NPCs")
    logger.info("Complete simulation starting with RL population control...")
    logger.info(f"Running with {len(tribal_manager.tribes)} tribes and {len(all_npcs)} NPCs")
    logger.info("NPCs will interact socially while participating in tribal dynamics")
    logger.info(f"RL agent will control population parameters every {SIM_SPEED_RL_DECISIONS} ticks")
    logger.info("")

    # Initialize timing variables for component breakdown
    tribal_time = 0
    world_time = 0
    social_time = 0
    rl_time = 0
    logging_time = 0


    # --- Patch: Diagnostics, Auto-Respawn, Logging Control ---
    pop_zero_ticks = 0
    last_print_tick = -1
    LOGGING_ENABLED = False  # Set to False to reduce logging for perf

    for i in range(num_ticks):
        tick_start = time.time()

        # Process tribal dynamics
        tribal_start = time.time()
        tribal_manager.process_tribal_dynamics(world)
        tribal_delta = time.time() - tribal_start
        tribal_time += tribal_delta

        # Process world tick (moves NPCs, updates factions)
        world_start = time.time()
        world.world_tick()
        world_delta = time.time() - world_start
        world_time += world_delta

        # Update weather (treat as part of logging/other overhead, fast call)
        weather_manager.update_weather(world.current_hour)

        # RL Population Control (every SIM_SPEED_RL_DECISIONS ticks)
        rl_delta = 0.0
        if rl_agent and i % SIM_SPEED_RL_DECISIONS == 0:
            if LOGGING_ENABLED:
                logger.info(f"[RL] RL block entered at tick {i}, rl_agent exists: {rl_agent is not None}")
            rl_start = time.time()
            try:
                # Get current state as dictionary (matching RL agent interface)
                current_pop = sum(len(ch.npcs) for ch in world.active_chunks.values())
                total_food = sum(ch.resources.get("food", 0) for ch in world.active_chunks.values())

                # Create state dictionary for RL agent
                state = {
                    "population": current_pop,
                    "food": total_food,
                    "births": getattr(world, "_audit_births_tick", 0),
                    "deaths_starv": getattr(world, "_audit_starvation_deaths_tick", 0),
                    "deaths_nat": 0,  # Not tracking natural deaths separately
                }

                # Get RL action
                action_idx = rl_agent.select_action(state)
                action_name = ACTION_NAMES[action_idx]

                # Apply action to world parameters
                if action_name == "repro_up":
                    world.balance_params["reproduction_rate"] = min(
                        0.1, world.balance_params.get("reproduction_rate", 0.03) * 1.2
                    )
                elif action_name == "repro_down":
                    world.balance_params["reproduction_rate"] = max(
                        0.01, world.balance_params.get("reproduction_rate", 0.03) * 0.8
                    )
                elif action_name == "mortality_amp_up":
                    world.balance_params["mortality_rate"] = min(
                        0.05, world.balance_params.get("mortality_rate", 0.01) * 1.5
                    )
                elif action_name == "mortality_amp_down":
                    world.balance_params["mortality_rate"] = max(
                        0.005, world.balance_params.get("mortality_rate", 0.01) * 0.7
                    )

                if LOGGING_ENABLED:
                    logger.info(f"[RL] tick={i} pop={current_pop} action={action_name}")

            except Exception as e:
                if LOGGING_ENABLED:
                    logger.info(f"[RL] Control error at tick {i}: {e}")

            rl_delta = time.time() - rl_start
            rl_time += rl_delta

        # --- Military RL Control (every 20 ticks) ---
        military_delta = 0.0
        if military_controller and i % 20 == 0:
            try:
                military_start = time.time()
                results = military_controller.make_military_decisions(world, tribal_manager, i)
                if LOGGING_ENABLED and results["actions"] > 0:
                    logger.info(f"[MILITARY RL] tick={i} actions={results['actions']} reward={results['reward']:.2f}")
                military_delta = time.time() - military_start
            except Exception as e:
                if LOGGING_ENABLED:
                    logger.info(f"[MILITARY RL] Control error at tick {i}: {e}")
        # (Optionally: add military_delta to a timing variable if you want breakdown)

        social_delta = 0.0
        # Social interactions every SIM_SPEED_SOCIAL_INTERVAL ticks
        if i % SIM_SPEED_SOCIAL_INTERVAL == 0:
            social_start = time.time()
            current_npcs = []
            for chunk in world.active_chunks.values():
                current_npcs.extend(chunk.npcs)

            if len(current_npcs) >= 2:
                npc1, npc2 = random.sample(current_npcs, 2)
                if (
                    abs(npc1.coordinates[0] - npc2.coordinates[0]) <= 1
                    and abs(npc1.coordinates[1] - npc2.coordinates[1]) <= 1
                ):
                    context = random.choice(["encounter", "trade", "idle", "hostility"])
                    dialogue1 = npc1.generate_dialogue(
                        npc2,
                        context,
                        tribal_manager.tribal_diplomacy,
                        tribal_manager.tribes,
                    )
                    dialogue2 = npc2.generate_dialogue(
                        npc1,
                        context,
                        tribal_manager.tribal_diplomacy,
                        tribal_manager.tribes,
                    )
                    if LOGGING_ENABLED:
                        logger.debug(f"💬 {npc1.name} ({npc1.faction_id}): {dialogue1}")
                        logger.debug(f"💬 {npc2.name} ({npc2.faction_id}): {dialogue2}")
                        # Log to dialogue file
                        dialogue_logger.info(
                            f"[TICK {i}] {npc1.name}->{npc2.name} ({context}) | {dialogue1}"
                        )
                        dialogue_logger.info(
                            f"[TICK {i}] {npc2.name}->{npc1.name} ({context}) | {dialogue2}"
                        )
            social_delta = time.time() - social_start
            social_time += social_delta

        # --- Population auto-respawn logic ---
        current_pop = sum(len(ch.npcs) for ch in world.active_chunks.values())
        if current_pop == 0:
            pop_zero_ticks += 1
        else:
            pop_zero_ticks = 0

        if pop_zero_ticks > 10:
            # Auto-respawn minimal population (1 tribe, 2 NPCs)
            print(f"[AUTO-RESPAWN] Population zero for {pop_zero_ticks} ticks at tick {i}. Respawning...")
            tribe_name = f"AutoTribe_{i}"
            location = (random.randint(-20, 20), random.randint(-20, 20))
            tribe = tribal_manager.create_tribe(tribe_name, f"founder_{tribe_name}", location)
            if tribe_name not in world.factions:
                world.factions[tribe_name] = Faction(name=tribe_name, territory=[location])
            for j in range(2):
                member_id = f"{tribe_name.lower()}_member_{j}"
                npc_name = f"{tribe_name[:3]}{j}"
                npc = NPC(name=npc_name, coordinates=location, faction_id=tribe_name)
                tribal_manager.tribes[tribe_name].add_member(member_id, random.choice(list(TribalRole)))
                world.factions[tribe_name].add_member(npc.name)
                chunk = world.get_chunk(location[0], location[1])
                chunk.npcs.append(npc)
                all_npcs.append(npc)
            pop_zero_ticks = 0

        # Residual time in this tick counts as logging/other overhead
        tick_elapsed = time.time() - tick_start
        accounted = tribal_delta + world_delta + rl_delta + social_delta
        residual = tick_elapsed - accounted
        logging_time += residual

        # --- Progress prints and diagnostics ---
        if i % 10 == 0:
            print(f"[PROGRESS] Tick {i}/{num_ticks}")
        if i % 50 == 0:
            pop_count = sum(len(ch.npcs) for ch in world.active_chunks.values())
            tribe_count = len(tribal_manager.tribes)
            print(f"[DIAG] Tick {i}: Population={pop_count}, Tribes={tribe_count}")
        # Optionally, print more detailed diagnostics here

        # Optionally, print a final summary at the end
        if i == num_ticks - 1:
            pop_count = sum(len(ch.npcs) for ch in world.active_chunks.values())
            tribe_count = len(tribal_manager.tribes)
            print(f"[COMPLETE] Final Tick: Population={pop_count}, Tribes={tribe_count}")

    # Final statistics
    end_time = time.time()
    total_time = end_time - start_time
    final_pop = sum(len(ch.npcs) for ch in world.active_chunks.values())

    logger.info("")
    logger.info("=== Complete Simulation Results ===")
    logger.info(f"Total runtime: {total_time:.1f} seconds")
    logger.info(f"Final population: {final_pop}")
    logger.info("Performance breakdown:")
    logger.info(f"  Tribal processing: {tribal_time:.1f}s ({tribal_time/total_time*100:.1f}%)")
    logger.info(f"  World simulation: {world_time:.1f}s ({world_time/total_time*100:.1f}%)")
    logger.info(f"  RL population control: {rl_time:.1f}s ({rl_time/total_time*100:.1f}%)")
    logger.info(f"  Social interactions: {social_time:.1f}s ({social_time/total_time*100:.1f}%)")
    logger.info(f"  Logging/overhead: {logging_time:.1f}s ({logging_time/total_time*100:.1f}%)")
    logger.info(f"Tribes: {len(tribal_manager.tribes)}")
    logger.info(f"Active chunks: {len(world.active_chunks)}")


if __name__ == "__main__":
    parser = _build_arg_parser()
    args = parser.parse_args()
    # Backward compatibility: if core mode and positional provided, override --ticks
    if getattr(args, "mode", None) == "core" and getattr(args, "ticks_positional", None) is not None:
        args.ticks = args.ticks_positional

    setup_logging(getattr(logging, args.log_level, logging.INFO))

    if not args.mode:
        # Launch interactive menu if no mode provided
        interactive_menu()
    elif args.mode == "core":
        from core_sim import run_core_sim

        run_core_sim(args.ticks)
    elif args.mode == "territory":
        run_persistent_territory_simulation()
    elif args.mode == "social":
        # Maintain original prompt if user passes 0 or negative
        ticks = args.ticks
        if ticks <= 0:
            try:
                ticks = int(input("Enter ticks for social simulation: "))
            except Exception:
                ticks = 50
        # Set env var consumed by social sim for tick count
        os.environ["AI_SANDBOX_SOCIAL_TICKS"] = str(ticks)
        # Call social sim (input() reads are avoided via env override)
        run_social_simulation()
    elif args.mode == "tribal":
        run_tribal_simulation(args.ticks)
    elif args.mode == "combined":
        run_combined_social_tribal_simulation(args.ticks)
    elif args.mode == "waves":
        from core_sim import run_core_sim

        run_core_sim(args.ticks)
    elif args.mode == "rl":
        try:
            if args.episodes and args.episodes > 1:
                from rl_agent import run_rl_training

                run_rl_training(
                    episodes=args.episodes,
                    max_ticks=args.ticks,
                    epsilon_start=args.epsilon_start,
                    epsilon_min=args.epsilon_min,
                    epsilon_decay=args.epsilon_decay,
                    intervention_interval=args.intervention_interval,
                    init_pop_min=args.init_pop_min,
                    init_pop_max=args.init_pop_max,
                    save_path=args.save_q,
                    load_path=args.load_q,
                )
            else:
                from rl_agent import run_simple_rl_episode

                run_simple_rl_episode(
                    max_ticks=args.ticks,
                    init_pop_min=args.init_pop_min,
                    init_pop_max=args.init_pop_max,
                )
        except Exception as e:
            print(f"[RL] Failed to run RL session: {e}")
    elif args.mode == "rl-control":
        try:
            from rl_agent import run_simulation_with_rl_control

            run_simulation_with_rl_control(
                num_ticks=args.ticks,
                qtable_path=args.load_q,
                control_interval=args.control_interval,
                init_pop_min=args.init_pop_min,
                init_pop_max=args.init_pop_max,
            )
        except Exception as e:
            print(f"[RL-CONTROL] Failed to run RL-controlled simulation: {e}")
    elif args.mode == "narrative":
        try:
            run_narrative_simulation(
                num_ticks=args.ticks,
                narrative_interval=args.narrative_interval,
                init_pop_min=args.init_pop_min,
                init_pop_max=args.init_pop_max,
            )
        except Exception as e:
            print(f"[NARRATIVE] Failed to run narrative simulation: {e}")
    elif args.mode == "menu":
        interactive_menu()
    else:
        parser.error(f"Unknown mode: {args.mode}")
