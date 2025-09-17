import random
import logging
import json
import os
import gzip
from datetime import datetime
from typing import Dict, List, Tuple, Optional, Set, Any
from .tribe import Tribe, TribalRole
from .tribal_conflict import TribalTerritory, TribalConflict
from .tribal_communication import TribalCommunication
from .tribal_roles import TribalRoleManager
from .tribal_structures import TribalCamp, TribalArchitecture
from .tribal_politics import TribalPolitics
from .tribal_diplomacy import TribalDiplomacy

# Try importing with fallbacks for optional dependencies
try:
    from npcs import NPC
except ImportError:
    # Fallback if npcs module has issues
    NPC = None

try:
    from gemini_narrative import generate_tribe_story
except ImportError:
    # Fallback if gemini_narrative has dependencies issues
    def generate_tribe_story(*args, **kwargs) -> str:
        return "Tribe story generation not available"


class TribalManager:
    """Main coordinator for all tribal systems"""

    def __init__(self) -> None:
        self.tribes: Dict[str, Tribe] = {}
        self.tribal_communication = TribalCommunication()
        self.tribal_conflict = TribalConflict()
        self.tribal_diplomacy = TribalDiplomacy(self.tribes)  # Pass tribes dict
        # Backwards compatibility alias expected by some tests
        self.diplomacy = self.tribal_diplomacy

        # Per-tribe managers
        self.role_managers: Dict[str, TribalRoleManager] = {}
        self.territories: Dict[str, TribalTerritory] = {}
        self.camps: Dict[str, TribalCamp] = {}
        self.architectures: Dict[str, TribalArchitecture] = {}
        self.politics: Dict[str, TribalPolitics] = {}  # Add politics managers

        self.logger = logging.getLogger("TribalManager")
        # Language analytics retention settings
        self._analytics_retention = 15  # keep newest N uncompressed JSON snapshots
        self._analytics_compress_older = True  # compress snapshots beyond retention window
        self._analytics_max_compressed = 60  # cap total compressed backups (older pruned)
        # Archive validation tracking
        self._last_archive_validation_day = None  # day number last integrity validation ran
        # Reconstruction log size management
        self._reconstruction_log_max = 500  # max events before compaction

    def create_tribe(
        self,
        name: str,
        founder_or_location,
        maybe_location: Optional[Tuple[int, int]] = None,
    ) -> Tribe:
        """Create a new tribe.

        Backwards compatible invocation patterns (to satisfy mixed tests):
        - create_tribe(name, founder_id, (x,y))  [original]
        - create_tribe(name, (x,y))              [tests that omit explicit founder]

        If founder omitted, an auto founder id is synthesized.
        """
        # Disambiguate arguments
        if isinstance(founder_or_location, tuple) and maybe_location is None:
            starting_location = founder_or_location
            founder_id = f"{name.lower()}_founder"
        else:
            founder_id = founder_or_location
            starting_location = maybe_location if maybe_location else (0, 0)

        tribe = Tribe(name=name)
        tribe.add_member(founder_id, TribalRole.LEADER)
        tribe.camp_location = starting_location

        # Initialize tribal systems
        self.tribes[name] = tribe
        self.tribal_diplomacy.add_tribe(tribe)  # Add to diplomacy system
        self.role_managers[name] = TribalRoleManager(tribe)
        self.territories[name] = TribalTerritory(tribe)
        self.camps[name] = TribalCamp(tribe, starting_location)
        self.architectures[name] = TribalArchitecture(tribe)
        self.politics[name] = TribalPolitics(tribe, self.role_managers[name])

        # Claim starting territory
        self.territories[name].claim_tile(starting_location)
        self.territories[name].expand_territory(starting_location, radius=1)

        # Give initial resources for basic camp setup
        tribe.add_shared_resource("wood", 5)
        tribe.add_shared_resource("stone", 3)

        # Build initial campfire
        self.camps[name].build_structure("campfire", starting_location)

        self.logger.info(f"Created new tribe: {name} at {starting_location}")
        # === Cultural Ledger Seed ===
        try:
            if not tribe.cultural_ledger["rituals_customs"]["rituals"]:
                tribe.add_ritual(
                    name="Founding Fire",
                    purpose="Solidify identity at formation",
                    seasonal=None,
                    effects={"morale": 0.05, "cultural_richness": 0.02},
                )
                tribe.record_significant_event(
                    summary="The tribe gathered around the first fire",
                    category="founding",
                    impact={"morale": 0.05},
                )
                tribe.formalize_myth()
        except Exception as e:
            self.logger.debug(f"Cultural ledger seed failed for {name}: {e}")
        return tribe

    # === Seasonal Adaptation Helpers (test support) ===
    def _adjust_tribal_priorities_for_season(
        self, tribe: "Tribe", seasonal_context: Dict[str, Any]
    ):
        """Lightweight seasonal modulation of tribe wellbeing proxies.

        Tests call this expecting side-effects on priorities; we adjust internal
        wellbeing metrics slightly so subsequent get_tribal_priorities reflects change.
        """
        season = seasonal_context.get("season", 0)
        # Spring boost expansion & culture
        if season == 0:
            tribe.wellbeing["organizational_efficiency"] = min(
                1.0, tribe.wellbeing.get("organizational_efficiency", 0.5) + 0.05
            )
            tribe.wellbeing["cultural_richness"] = min(
                1.0, tribe.wellbeing.get("cultural_richness", 0.4) + 0.04
            )
        # Summer boost food security
        elif season == 1:
            tribe.wellbeing["food_security"] = min(
                1.0, tribe.wellbeing.get("food_security", 0.5) + 0.06
            )
        # Autumn boost resource availability (maps to food_security proxy slightly)
        elif season == 2:
            tribe.wellbeing["resource_availability"] = min(
                1.0, tribe.wellbeing.get("resource_availability", 0.5) + 0.05
            )
        # Winter boost defense/security
        elif season == 3:
            tribe.wellbeing["security"] = min(1.0, tribe.wellbeing.get("security", 0.5) + 0.07)
        # Recompute composite
        tribe.wellbeing["overall_wellbeing"] = min(
            1.0,
            sum(
                [
                    tribe.wellbeing.get("food_security", 0.5),
                    tribe.wellbeing.get("resource_availability", 0.5),
                    tribe.wellbeing.get("health", 0.7),
                    tribe.wellbeing.get("morale", 0.6),
                    tribe.wellbeing.get("security", 0.5),
                ]
            )
            / 5.0,
        )

    # Convenience negotiation wrapper if tests invoke internal method with fewer args
    def choose_negotiation_type(self, tribe_a: "Tribe", tribe_b: "Tribe") -> str:
        return self.tribal_diplomacy._choose_negotiation_type(
            tribe_a,
            tribe_b,
            security_concerns=0.5,
            expansion_opportunities=0.5,
            trust_level=0.5,
        )

    def add_member_to_tribe(self, tribe_name: str, npc_id: str) -> bool:
        """Add an NPC to an existing tribe"""

        if tribe_name not in self.tribes:
            return False

        tribe = self.tribes[tribe_name]
        tribe.add_member(npc_id)

        # Reassign roles to accommodate new member and balance the tribe
        self.role_managers[tribe_name].reassign_roles()

        return True

    def merge_tribes(
        self, tribe1_name: str, tribe2_name: str, dominant_tribe: str
    ) -> Optional[Tribe]:
        """Merge two tribes into one"""

        if tribe1_name not in self.tribes or tribe2_name not in self.tribes:
            return None

        tribe1 = self.tribes[tribe1_name]
        tribe2 = self.tribes[tribe2_name]

        # Determine which tribe dominates
        if dominant_tribe == tribe1_name:
            dominant, subordinate = tribe1, tribe2
        else:
            dominant, subordinate = tribe2, tribe1

        # Merge members
        for member_id in subordinate.member_ids:
            dominant.add_member(member_id)
            dominant.social_roles[member_id] = subordinate.social_roles.get(
                member_id, TribalRole.GATHERER
            )

        # Merge resources
        for resource, amount in subordinate.shared_resources.items():
            dominant.add_shared_resource(resource, amount)

        # Merge territory
        dominant_territory = self.territories[dominant.name]
        subordinate_territory = self.territories[subordinate.name]

        for tile in subordinate_territory.claimed_tiles:
            dominant_territory.claim_tile(tile)

        # Merge structures
        dominant_camp = self.camps[dominant.name]
        subordinate_camp = self.camps[subordinate.name]

        for structure in subordinate_camp.structures:
            dominant_camp.structures.append(structure)

        # Update tribe structures count
        for structure_type, count in subordinate.structures.items():
            dominant.structures[structure_type] += count

        # Record merger in tribal memory
        dominant.add_tribal_memory(
            "tribe_merged",
            {
                "absorbed_tribe": subordinate.name,
                "new_members": len(subordinate.member_ids),
                "new_territory": len(subordinate_territory.claimed_tiles),
            },
        )

        # Remove subordinate tribe
        self._remove_tribe(subordinate.name)

        self.logger.info(f"Tribes merged: {subordinate.name} absorbed into {dominant.name}")
        return dominant

    def split_tribe(
        self, tribe_name: str, split_location: Tuple[int, int], leader_id: str
    ) -> Optional[Tribe]:
        """Split a tribe into two"""

        if tribe_name not in self.tribes:
            return None

        original_tribe = self.tribes[tribe_name]

        # Create new tribe
        new_tribe_name = f"{original_tribe.name}_Split_{random.randint(100, 999)}"
        new_tribe = Tribe(name=new_tribe_name)
        new_tribe.symbol = original_tribe.symbol  # Keep same symbol for continuity

        # Move leader and some members to new tribe
        new_tribe.add_member(leader_id, TribalRole.LEADER)

        # Move some members (about 40% of total)
        members_to_move = random.sample(
            list(original_tribe.member_ids - {leader_id}),
            max(1, len(original_tribe.member_ids) // 3),
        )

        for member_id in members_to_move:
            original_tribe.remove_member(member_id)
            new_tribe.add_member(
                member_id,
                original_tribe.social_roles.get(member_id, TribalRole.GATHERER),
            )

        # Split resources
        for resource, amount in original_tribe.shared_resources.items():
            split_amount = amount // 2
            original_tribe.shared_resources[resource] -= split_amount
            new_tribe.add_shared_resource(resource, split_amount)

        # Split territory around split location
        original_territory = self.territories[tribe_name]
        new_territory = TribalTerritory(new_tribe)

        # Find tiles near split location
        nearby_tiles = []
        sx, sy = split_location
        for tile in original_territory.claimed_tiles:
            tx, ty = tile
            distance = abs(tx - sx) + abs(ty - sy)
            if distance <= 3:  # Within 3 tiles
                nearby_tiles.append(tile)

        # Move some nearby tiles to new tribe
        tiles_to_move = random.sample(nearby_tiles, min(len(nearby_tiles) // 2, 5))
        for tile in tiles_to_move:
            original_territory.release_tile(tile)
            new_territory.claim_tile(tile)

        # Set up new tribe systems
        self.tribes[new_tribe_name] = new_tribe
        self.role_managers[new_tribe_name] = TribalRoleManager(new_tribe)
        self.territories[new_tribe_name] = new_territory
        self.camps[new_tribe_name] = TribalCamp(new_tribe, split_location)
        self.architectures[new_tribe_name] = TribalArchitecture(new_tribe)

        # Build initial structure for new tribe
        self.camps[new_tribe_name].build_structure("campfire", split_location)

        # Record split in both tribes' memories
        original_tribe.add_tribal_memory(
            "tribe_split",
            {
                "new_tribe": new_tribe_name,
                "members_lost": len(members_to_move),
                "territory_lost": len(tiles_to_move),
            },
        )

        new_tribe.add_tribal_memory(
            "tribe_formed",
            {
                "from_split": True,
                "parent_tribe": original_tribe.name,
                "initial_members": len(new_tribe.member_ids),
            },
        )

        self.logger.info(f"Tribe {tribe_name} split into {new_tribe_name}")
        return new_tribe

    def _remove_tribe(self, tribe_name: str) -> None:
        """Remove a tribe from all systems"""
        if tribe_name in self.tribes:
            del self.tribes[tribe_name]
        if tribe_name in self.role_managers:
            del self.role_managers[tribe_name]
        if tribe_name in self.territories:
            del self.territories[tribe_name]
        if tribe_name in self.camps:
            del self.camps[tribe_name]
        if tribe_name in self.architectures:
            del self.architectures[tribe_name]

    def get_tribe_info(self, tribe_name: str) -> Optional[Dict]:
        """Get comprehensive information about a tribe"""
        if tribe_name not in self.tribes:
            return None

        tribe = self.tribes[tribe_name]
        territory = self.territories[tribe_name]
        camp = self.camps[tribe_name]
        architecture = self.architectures[tribe_name]

        return {
            "name": tribe.name,
            "symbol": tribe.symbol,
            "leader": tribe.leader_id,
            "member_count": len(tribe.member_ids),
            "territory_size": territory.get_territory_size(),
            "structures": tribe.structures.copy(),
            "shared_resources": tribe.shared_resources.copy(),
            "alliances": list(tribe.alliances),
            "rivalries": list(tribe.rivalries),
            "development_stage": architecture.development_stage,
            "camp_benefits": camp.get_camp_benefits(),
            "cultural_totems": tribe.culture["totems"].copy(),
            "tribal_stories": tribe.get_tribal_stories(),
        }

    def update_tribes(self) -> None:
        """Update all tribal systems for a game turn"""

        for tribe_name, tribe in self.tribes.items():
            # Maintain structures
            self.camps[tribe_name].maintain_structures()

            # Advance architectural knowledge
            self.architectures[tribe_name].advance_architecture()

            # Update tribal relationships (truces expire)
            expired_truces = []
            for other_tribe, turns_remaining in tribe.truces.items():
                tribe.truces[other_tribe] = turns_remaining - 1
                if tribe.truces[other_tribe] <= 0:
                    expired_truces.append(other_tribe)

            for expired_tribe in expired_truces:
                del tribe.truces[expired_tribe]

    def get_all_tribes_info(self) -> List[Dict]:
        """Get information about all tribes"""
        return [
            self.get_tribe_info(name) for name in self.tribes.keys() if self.get_tribe_info(name)
        ]

    def find_tribe_by_location(self, location: Tuple[int, int]) -> Optional[str]:
        """Find which tribe controls a given location"""
        for tribe_name, territory in self.territories.items():
            if location in territory.claimed_tiles:
                return tribe_name
        return None

    def get_tribal_conflicts(self) -> List[Dict]:
        """Get all active tribal conflicts"""
        return self.tribal_conflict.get_active_conflicts()

    def get_tribal_diplomacy_status(self, tribe1: str, tribe2: str) -> Dict:
        """Get diplomatic status between two tribes"""
        return self.tribal_diplomacy.get_diplomatic_status(tribe1, tribe2)

    def is_diplomacy_allowed(self, tribe_name: str, current_day: int) -> bool:
        tribe = self.tribes.get(tribe_name)
        if not tribe:
            return False
        if hasattr(tribe, "is_diplomacy_blocked") and tribe.is_diplomacy_blocked(current_day):
            return False
        return True

    def process_tribal_contributions(self, faction_manager=None) -> None:
        """Process role contributions for all tribes and their associated factions"""
        total_contributions = 0

        for tribe_name, tribe in self.tribes.items():
            # Get associated faction if faction_manager provided
            faction = None
            if faction_manager:
                # Find faction that contains tribal members
                for faction_name, faction_obj in faction_manager.factions.items():
                    if any(member in faction_obj.npc_ids for member in tribe.member_ids):
                        faction = faction_obj
                        break

            # Process contributions for this tribe
            if tribe_name in self.role_managers:
                self.role_managers[tribe_name].process_role_contributions(faction)
                total_contributions += len(tribe.social_roles)

        self.logger.info(
            f"Processed {total_contributions} role contributions across {len(self.tribes)} tribes"
        )

    def process_tribal_dynamics(self, world=None) -> None:
        # === Cultural Value Influence (pre-pass) ===
        # Adjust diplomacy bias based on top cultural values before other processing
        for tribe_name, tribe in self.tribes.items():
            if hasattr(self.tribal_diplomacy, "set_cultural_modifiers"):
                priority = (
                    tribe.get_value_priority() if hasattr(tribe, "get_value_priority") else []
                )
                modifiers = {}
                if priority:
                    # Example heuristic: first value slightly boosts related diplomatic posture
                    top = priority[0]
                    if top == "Honor":
                        modifiers["betrayal_risk"] = -0.1
                    if top == "Prosperity":
                        modifiers["trade_bias"] = 0.1
                    if top == "Survival":
                        modifiers["defense_bias"] = 0.1
                try:
                    self.tribal_diplomacy.set_cultural_modifiers(tribe_name, modifiers)
                except Exception:
                    pass

        # === Cultural Value Drift (gentle normalization) ===
        # Every dynamics tick, very small pull toward 0.5 for values not recently adjusted.
        for tribe_name, tribe in self.tribes.items():
            try:
                ledger = getattr(tribe, "cultural_ledger", None)
                if not ledger:
                    continue
                # --- Prestige scaffold (compute lightweight dynamic prestige) ---
                lang = ledger.get("language", {})
                myths = ledger.get("history_myths", {}).get("myths", [])
                values = ledger.get("values", {}).get("principles", {})
                richness = (
                    tribe.wellbeing.get("cultural_richness", 0.0)
                    if hasattr(tribe, "wellbeing")
                    else 0.0
                )
                trade_links = len(getattr(tribe, "trade_network", []))
                lex_size = len(lang.get("lexicon", {}))
                prestige_raw = (
                    richness * 0.35
                    + min(lex_size / 40.0, 1.0) * 0.25
                    + min(len(myths) / 6.0, 1.0) * 0.15
                    + min(trade_links / 5.0, 1.0) * 0.15
                    + (sum(values.values()) / max(len(values), 1)) * 0.10
                    if values
                    else 0
                )
                prestige = round(min(1.0, prestige_raw), 3)
                lang["prestige"] = prestige
                principles = ledger.get("values", {}).get("principles", {})
                if not principles:
                    continue
                # Optional: track last adjustment (if method existed); here we infer by absence of recent events.
                for val_name, val_data in principles.items():
                    score = val_data.get("score", 0.5)
                    drift_strength = 0.005  # gentle daily drift
                    if score > 0.5:
                        score = max(0.5, score - drift_strength)
                    elif score < 0.5:
                        score = min(0.5, score + drift_strength)
                    val_data["score"] = round(score, 3)
                # Recalculate ordering if changed
                if hasattr(tribe, "_recalculate_value_priority"):
                    tribe._recalculate_value_priority()
            except Exception:
                continue

        # ===== EVENT-AWARE FACTION STRATEGY =====
        event_manager = None
        if world and hasattr(world, "event_manager"):
            event_manager = world.event_manager
        # Track per-tribe active adverse events this tick for mutation triggers
        _active_environmental_events: Dict[str, Set[str]] = {}
        for tribe_name, tribe in self.tribes.items():
            location = getattr(tribe, "camp_location", None)
            if not location or not event_manager:
                continue
            active_events = event_manager.get_events_for_location(location)
            for event in active_events:
                code = None
                # Resource Boom: increase trade willingness
                if event.name == "Bountiful Harvest":
                    tribe.tribal_memory.append(
                        {
                            "event": "resource_boom",
                            "action": "increase_trade",
                            "turn": getattr(world, "current_day", 0),
                        }
                    )
                    self.logger.info(
                        f"Tribe {tribe_name} has a resource boom and is open to trade!"
                    )
                    try:
                        tribe.evolve_language(concept="abundance", reason="event_boom")
                    except Exception:
                        pass
                # Famine: seek trade, raid, or alliance
                if event.name == "Famine":
                    code = "famine"
                    tribe.tribal_memory.append(
                        {
                            "event": "famine",
                            "action": "seek_trade_or_raid",
                            "turn": getattr(world, "current_day", 0),
                        }
                    )
                    self.logger.info(
                        f"Tribe {tribe_name} is suffering famine and may seek trade, raid, or alliance."
                    )
                    try:
                        tribe.evolve_language(concept="scarcity", reason="event_famine")
                    except Exception:
                        pass
                # Plague: consider migration
                if event.name == "The Wasting Sickness":
                    code = "plague"
                    tribe.tribal_memory.append(
                        {
                            "event": "plague",
                            "action": "consider_migration",
                            "turn": getattr(world, "current_day", 0),
                        }
                    )
                    self.logger.info(f"Tribe {tribe_name} is considering migration due to plague.")
                    try:
                        tribe.evolve_language(concept="sickness", reason="event_plague")
                    except Exception:
                        pass
                # Wildfire: shelter or migrate
                if event.name == "Wildfire":
                    code = "wildfire"
                    tribe.tribal_memory.append(
                        {
                            "event": "wildfire",
                            "action": "shelter_or_migrate",
                            "turn": getattr(world, "current_day", 0),
                        }
                    )
                    self.logger.info(
                        f"Tribe {tribe_name} is sheltering or migrating due to wildfire."
                    )
                    try:
                        tribe.evolve_language(concept="firestorm", reason="event_wildfire")
                    except Exception:
                        pass
                if code:
                    _active_environmental_events.setdefault(tribe_name, set()).add(code)

        # === Cultural Mutation Trigger Evaluation (environmental) ===
        if world and hasattr(world, "current_day"):
            _mut_day = getattr(world, "current_day", 0)
            for tribe_name, tribe in self.tribes.items():
                try:
                    cs = getattr(tribe, "custom_state", {})
                    active = _active_environmental_events.get(tribe_name, set())
                    # Famine streak tracking
                    famine_streak = cs.get("famine_streak", 0)
                    if "famine" in active:
                        famine_streak += 1
                    else:
                        # If famine just ended after long streak trigger mutation
                        if famine_streak >= 5:  # threshold for long famine
                            last = cs.get("last_famine_mutation_day", -1)
                            if last != _mut_day:  # gate per-day
                                tribe.cultural_mutation("famine_long", _mut_day)
                                cs["last_famine_mutation_day"] = _mut_day
                        famine_streak = 0
                    cs["famine_streak"] = famine_streak
                    # Plague streak tracking
                    plague_streak = cs.get("plague_streak", 0)
                    if "plague" in active:
                        plague_streak += 1
                    else:
                        if plague_streak >= 3:  # survived multi-day plague
                            last = cs.get("last_plague_mutation_day", -1)
                            if last != _mut_day:
                                tribe.cultural_mutation("plague_survived", _mut_day)
                                cs["last_plague_mutation_day"] = _mut_day
                        plague_streak = 0
                    cs["plague_streak"] = plague_streak
                except Exception:
                    continue

        # === Cultural Mutation Trigger Evaluation (conflict casualties) ===
        try:
            if world and hasattr(world, "current_day") and hasattr(self, "tribal_conflict"):
                current_day = getattr(world, "current_day", 0)
                history = getattr(self.tribal_conflict, "conflict_history", [])
                # For each tribe track last checked conflict index
                last_index_global = len(history) - 1
                for tribe_name, tribe in self.tribes.items():
                    cs = getattr(tribe, "custom_state", {})
                    last_checked = cs.get("last_conflict_history_index", -1)
                    mutated_conflicts = cs.get("mutated_conflicts", set())
                    # Iterate new conflicts only
                    for idx in range(last_checked + 1, len(history)):
                        conf = history[idx]
                        if not isinstance(conf, dict):
                            continue
                        cid = conf.get("id")
                        if cid in mutated_conflicts:
                            continue
                        initiator = conf.get("initiator")
                        target = conf.get("target")
                        if tribe_name not in (initiator, target):
                            continue
                        casualties = conf.get("casualties", {})
                        total_cas = sum(v for v in casualties.values() if isinstance(v, int))
                        # Devastating war heuristic
                        if total_cas >= 6:
                            tribe.cultural_mutation("devastating_war", current_day)
                            mutated_conflicts.add(cid)
                        # Betrayal heuristic: peace_treaty followed quickly by new conflict from same initiator
                        try:
                            resolution = conf.get("resolution")
                            if resolution == "peace_treaty":
                                # Record peace marker
                                peace_markers = cs.get("recent_peace_markers", [])
                                peace_markers.append(
                                    {
                                        "with": (initiator if target == tribe_name else target),
                                        "day": current_day,
                                    }
                                )
                                # Keep only last 10 markers
                                if len(peace_markers) > 10:
                                    peace_markers = peace_markers[-10:]
                                cs["recent_peace_markers"] = peace_markers
                            else:
                                # If this conflict is of type 'raid' or 'revenge' soon (<5 days) after peace with opposite tribe -> betrayal
                                conflict_type = conf.get("type")
                                if conflict_type in ("raid", "revenge"):
                                    peace_markers = cs.get("recent_peace_markers", [])
                                    counterpart = initiator if target == tribe_name else target
                                    for pm in peace_markers:
                                        if (
                                            pm.get("with") == counterpart
                                            and (current_day - pm.get("day", current_day)) <= 5
                                        ):
                                            last_betrayal = cs.get("last_betrayal_mutation_day", -1)
                                            if last_betrayal != current_day:
                                                tribe.cultural_mutation("betrayal", current_day)
                                                cs["last_betrayal_mutation_day"] = current_day
                                            break
                        except Exception:
                            pass
                    cs["last_conflict_history_index"] = last_index_global
                    cs["mutated_conflicts"] = mutated_conflicts
        except Exception:
            pass

        # === Periodic Cultural Evolution Hooks ===
        if world and hasattr(world, "current_day"):
            current_day = getattr(world, "current_day", 0)
            # --- Ritual / Custom Maintenance & Triggers ---
            try:
                # Season start trigger (assumes world has current_season and DAYS_PER_SEASON)
                season_index = getattr(world, "current_season", None)
                days_per_season = getattr(world, "DAYS_PER_SEASON", 0)
                if days_per_season and current_day % days_per_season == 0:
                    # Season boundary – activate any matching seasonal rituals
                    season_names = getattr(
                        world, "season_names", ["Spring", "Summer", "Autumn", "Winter"]
                    )
                    season_name = (
                        season_names[season_index]
                        if isinstance(season_index, int) and 0 <= season_index < len(season_names)
                        else None
                    )
                    if season_name:
                        for tribe in self.tribes.values():
                            rituals = tribe.cultural_ledger.get("rituals_customs", {}).get(
                                "rituals", []
                            )
                            for r in rituals:
                                if (
                                    r.get("seasonal")
                                    and r.get("seasonal").lower() == season_name.lower()
                                ):
                                    tribe.activate_ritual(r, current_day=current_day, duration=30)
                                    self.logger.info(
                                        f"[Ritual] {tribe.name} begins seasonal ritual '{r.get('name')}' ({season_name})"
                                    )
                # Daily cleanup of expired ritual effects
                for tribe in self.tribes.values():
                    before = len(tribe.active_ritual_effects)
                    tribe.cleanup_ritual_effects(current_day)
                    after = len(tribe.active_ritual_effects)
                    if after < before:
                        self.logger.debug(
                            f"[Ritual] {tribe.name} expired {before-after} ritual effects"
                        )
                # Leader change mourning trigger
                for tribe in self.tribes.values():
                    try:
                        last_leader = tribe.custom_state.get("last_leader_id")
                        if last_leader is None:
                            tribe.custom_state["last_leader_id"] = tribe.leader_id
                        elif last_leader != tribe.leader_id:
                            tribe.custom_state["last_leader_id"] = tribe.leader_id
                            if tribe.enforce_mourning(current_day, days=7):
                                self.logger.info(
                                    f"[Custom] {tribe.name} enters mourning after leader change; diplomacy blocked for 7 days"
                                )
                    except Exception:
                        pass
                # Alliance formation celebration trigger
                for tribe in self.tribes.values():
                    try:
                        current_alliances = set(getattr(tribe, "alliances", set()))
                        known_alliances = tribe.custom_state.get("known_alliances", set())
                        new_alliances = current_alliances - known_alliances
                        if new_alliances:
                            tribe.custom_state["known_alliances"] = current_alliances
                            rituals = tribe.cultural_ledger.get("rituals_customs", {}).get(
                                "rituals", []
                            )
                            for r in rituals:
                                if r.get("trigger") == "alliance_formed":
                                    tribe.activate_ritual(
                                        r,
                                        current_day=current_day,
                                        duration=r.get("duration", 20),
                                    )
                                    self.logger.info(
                                        f"[Ritual] {tribe.name} celebrates new alliance(s) {new_alliances} via '{r.get('name','alliance_ritual')}'"
                                    )
                        else:
                            if "known_alliances" not in tribe.custom_state:
                                tribe.custom_state["known_alliances"] = current_alliances
                    except Exception:
                        pass
            except Exception:
                pass
            if current_day % 7 == 0:  # Weekly linguistic evolution sample
                for tribe_name, tribe in self.tribes.items():
                    try:
                        # 50% chance evolve a core concept (shift) else pick an existing word to shift
                        lex = tribe.cultural_ledger.get("language", {}).get("lexicon", {})
                        if lex and random.random() < 0.5:
                            target_concept = random.choice(list(lex.keys()))
                        else:
                            target_concept = random.choice(
                                ["trade", "hunt", "spirit", "ally", "water"]
                            )
                        tribe.evolve_language(concept=target_concept, reason="periodic")
                    except Exception:
                        continue
                # Attempt cultural exchange borrowing among high-trust allied tribes
                try:
                    for a_name, a_tribe in self.tribes.items():
                        for b_name in getattr(a_tribe, "alliances", set()):
                            if b_name not in self.tribes:
                                continue
                            b_tribe = self.tribes[b_name]
                            # Skip if mourning blocks diplomacy for either tribe
                            if (
                                hasattr(a_tribe, "is_diplomacy_blocked")
                                and a_tribe.is_diplomacy_blocked(current_day)
                            ) or (
                                hasattr(b_tribe, "is_diplomacy_blocked")
                                and b_tribe.is_diplomacy_blocked(current_day)
                            ):
                                self.logger.debug(
                                    f"[Custom] Diplomacy blocked between {a_name} and {b_name} due to mourning custom"
                                )
                                continue
                            # Simple trust heuristic: if both list each other as alliance and random gate
                            if a_name in getattr(b_tribe, "alliances", set()):
                                # Prestige-weighted borrowing probability: higher-prestige language diffuses more
                                a_prestige = a_tribe.cultural_ledger.get("language", {}).get(
                                    "prestige", 0.0
                                )
                                b_prestige = b_tribe.cultural_ledger.get("language", {}).get(
                                    "prestige", 0.0
                                )
                                prestige_diff = abs(a_prestige - b_prestige)
                                base_prob = 0.08  # baseline diffusion chance
                                # Directional bias: lower prestige tribe more likely to borrow
                                if a_prestige > b_prestige:
                                    a_to_b_prob = base_prob + prestige_diff * 0.25
                                    b_to_a_prob = base_prob * 0.4  # suppressed reverse flow
                                elif b_prestige > a_prestige:
                                    b_to_a_prob = base_prob + prestige_diff * 0.25
                                    a_to_b_prob = base_prob * 0.4
                                else:
                                    a_to_b_prob = b_to_a_prob = base_prob
                                # Random gate: attempt one direction selected by weighted draw
                                roll = random.random()
                                attempt_direction = None
                                if roll < a_to_b_prob:
                                    attempt_direction = "a_to_b"
                                elif roll < a_to_b_prob + b_to_a_prob:
                                    attempt_direction = "b_to_a"
                                else:
                                    continue
                                a_lex = a_tribe.cultural_ledger.get("language", {}).get(
                                    "lexicon", {}
                                )
                                b_lex = b_tribe.cultural_ledger.get("language", {}).get(
                                    "lexicon", {}
                                )
                                if not a_lex or not b_lex:
                                    continue
                                # Choose a concept one has that the other lacks
                                a_unique = [c for c in a_lex.keys() if c not in b_lex]
                                b_unique = [c for c in b_lex.keys() if c not in a_lex]
                                if attempt_direction == "a_to_b" and a_unique:
                                    concept = random.choice(a_unique)
                                    b_tribe.evolve_language(
                                        concept=concept, reason="borrow_prestige"
                                    )
                                elif attempt_direction == "b_to_a" and b_unique:
                                    concept = random.choice(b_unique)
                                    a_tribe.evolve_language(
                                        concept=concept, reason="borrow_prestige"
                                    )
                except Exception:
                    pass
            if current_day % 10 == 0:  # Weighted myth formation attempt window
                for tribe_name, tribe in self.tribes.items():
                    try:
                        ledger = getattr(tribe, "cultural_ledger", {})
                        events = ledger.get("history_myths", {}).get("significant_events", [])
                        myths = ledger.get("history_myths", {}).get("myths", [])
                        backlog = max(0, len(events) - len(myths))
                        if backlog <= 0:
                            continue
                        # Probability scales with backlog but capped
                        probability = min(0.15 + backlog * 0.05, 0.75)
                        if random.random() < probability:
                            tribe.formalize_myth()
                    except Exception:
                        continue
            if current_day % 15 == 0:  # Cultural summary logging
                for tribe_name, tribe in self.tribes.items():
                    try:
                        summary = tribe.summarize_culture()
                        self.logger.info(
                            f"[Culture] {tribe_name} values={summary['top_values']} rituals={summary['ritual_count']} myths={summary['myth_count']} lexicon={summary['lexicon_size']}"
                        )
                    except Exception:
                        continue
                # Event-triggered word derivation
                for tribe_name, tribe in self.tribes.items():
                    try:
                        events = tribe.cultural_ledger["history_myths"]["significant_events"][
                            -5:
                        ]  # last 5 events
                        for event in events:
                            summary = event.get("summary", "").lower()
                            if "birth" in summary or "child" in summary or "new member" in summary:
                                lang = tribe.cultural_ledger.get("language", {})
                                lex = lang.get("lexicon", {})
                                if len(lex) >= 3:
                                    base_candidates = [
                                        "life",
                                        "growth",
                                        "family",
                                        "people",
                                    ]
                                    available_bases = [c for c in base_candidates if c in lex]
                                    if available_bases:
                                        base = random.choice(available_bases)
                                        shift = random.choice(["agent", "collective", "quality"])
                                        tribe.derive_word(base, shift)
                                        break  # Only derive once per culture update cycle
                    except Exception:
                        continue
                # Generate tribe stories if LLM enabled
                if os.getenv("SANDBOX_LLM_DIALOGUE", "false").lower() == "true":
                    for tribe_name, tribe in self.tribes.items():
                        try:
                            population = len(
                                [npc for npc in self.npcs.values() if npc.faction_id == tribe_name]
                            )
                            events = tribe.cultural_ledger["history_myths"]["significant_events"][
                                -3:
                            ]  # last 3 events
                            event_summaries = [e.get("summary", str(e)) for e in events]
                            if event_summaries:
                                story = generate_tribe_story(
                                    tribe_name, population, event_summaries
                                )
                                self.logger.info(f"[Tribe Story] {tribe_name}: {story}")
                        except Exception as e:
                            self.logger.debug(f"Failed to generate story for {tribe_name}: {e}")
                # LLM-guided concept discovery (every 25 days)
                if (
                    current_day % 25 == 0
                    and os.getenv("SANDBOX_LLM_LEXICON", "false").lower() == "true"
                ):
                    for tribe_name, tribe in self.tribes.items():
                        try:
                            # Only attempt discovery for tribes with established lexicons
                            lang = tribe.cultural_ledger.get("language", {})
                            lex = lang.get("lexicon", {})
                            if len(lex) < 8:  # Need a basic vocabulary first
                                continue

                            # Get recent events and existing concepts
                            events = tribe.cultural_ledger.get("history_myths", {}).get(
                                "significant_events", []
                            )[-5:]
                            event_summaries = [
                                e.get("summary", "") for e in events if e.get("summary")
                            ]
                            existing_concepts = list(lex.keys())

                            if event_summaries:
                                from gemini_narrative import discover_new_concept

                                culture_desc = tribe._get_tribe_culture_description()
                                new_concept = discover_new_concept(
                                    event_summaries, culture_desc, existing_concepts
                                )

                                if (
                                    new_concept
                                    and new_concept not in lex
                                    and not new_concept.startswith("[LLM")
                                ):
                                    # Create a word for this new concept
                                    word = tribe._generate_lexical_root(new_concept)
                                    tribe._add_language_entry(
                                        new_concept,
                                        word=word,
                                        evolution_reason="llm_concept_discovery",
                                    )
                                    usage = lang.setdefault("usage", {})
                                    usage[new_concept] = 1
                                    self.logger.info(
                                        f"[LLM Concept] {tribe_name} discovered concept '{new_concept}' -> '{word}'"
                                    )
                        except Exception as e:
                            self.logger.debug(f"Failed LLM concept discovery for {tribe_name}: {e}")
                # Cultural borrowing between allied tribes (every 35 days)
                if current_day % 35 == 0:
                    self._cultural_borrowing(current_day)

    def _form_pidgins(self, current_day: int = 0):
        """Form pidgin lexicons for high-interaction, low-similarity allied tribe pairs.

        NOTE: Method name standardized from '_form_pidgeons'; legacy name retained as alias
        for backward compatibility with any external references.
        """
        tribe_items = list(self.tribes.items())
        if len(tribe_items) < 2:
            return
        for name_a, tribe_a in tribe_items:
            lang_a = tribe_a.cultural_ledger.get("language", {})
            conv_a = lang_a.get("convergence", {}).get("partners", {})
            for name_b in getattr(tribe_a, "alliances", set()):
                if name_b not in self.tribes or name_a >= name_b:
                    continue  # avoid double and self
                tribe_b = self.tribes[name_b]
                lang_b = tribe_b.cultural_ledger.get("language", {})
                conv_b = lang_b.get("convergence", {}).get("partners", {})
                # Only if both list each other as allies
                if name_a not in getattr(tribe_b, "alliances", set()):
                    continue
                # Require convergence metrics
                metrics = conv_a.get(name_b) or conv_b.get(name_a)
                if not metrics:
                    continue
                # Only if divergence is high (e.g., >0.45) and concept overlap is low (<0.5)
                if (
                    metrics.get("divergence", 1.0) < 0.45
                    or metrics.get("concept_overlap", 1.0) > 0.5
                ):
                    continue
                # Form pidgin: shared minimal lexicon for core concepts
                core_concepts = [
                    "food",
                    "trade",
                    "ally",
                    "spirit",
                    "water",
                    "danger",
                    "hunt",
                ]
                lex_a = lang_a.get("lexicon", {})
                lex_b = lang_b.get("lexicon", {})
                pidgin = {}
                for concept in core_concepts:
                    a = lex_a.get(concept)
                    b = lex_b.get(concept)
                    if a and b:
                        # Pick shorter or more frequent form, or random
                        form = a if len(a) <= len(b) else b
                        if random.random() < 0.5:
                            form = random.choice([a, b])
                        pidgin[concept] = form
                    elif a:
                        pidgin[concept] = a
                    elif b:
                        pidgin[concept] = b
                # Store pidgin in both tribes
                lang_a.setdefault("pidgins", {})[name_b] = {
                    "lexicon": pidgin,
                    "formed_day": current_day,
                    "with": name_b,
                    "divergence": metrics.get("divergence"),
                    "concept_overlap": metrics.get("concept_overlap"),
                }
                lang_b.setdefault("pidgins", {})[name_a] = {
                    "lexicon": pidgin,
                    "formed_day": current_day,
                    "with": name_a,
                    "divergence": metrics.get("divergence"),
                    "concept_overlap": metrics.get("concept_overlap"),
                }
                tribe_a.add_tribal_memory(
                    "pidgin_formed",
                    {
                        "with": name_b,
                        "concepts": list(pidgin.keys()),
                        "divergence": metrics.get("divergence"),
                    },
                )
                tribe_b.add_tribal_memory(
                    "pidgin_formed",
                    {
                        "with": name_a,
                        "concepts": list(pidgin.keys()),
                        "divergence": metrics.get("divergence"),
                    },
                )

    # Backward compatibility alias
    _form_pidgeons = _form_pidgins

    def _cultural_borrowing(self, current_day: int = 0):
        """Enable cultural word borrowing between allied tribes using LLM."""
        if not os.getenv("SANDBOX_LLM_LEXICON", "false").lower() == "true":
            return

        tribe_items = list(self.tribes.items())
        if len(tribe_items) < 2:
            return

        for name_a, tribe_a in tribe_items:
            for name_b in getattr(tribe_a, "alliances", set()):
                if name_b not in self.tribes or name_a >= name_b:
                    continue  # avoid double and self
                tribe_b = self.tribes[name_b]

                # Only if both list each other as allies
                if name_a not in getattr(tribe_b, "alliances", set()):
                    continue

                try:
                    lang_a = tribe_a.cultural_ledger.get("language", {})
                    lang_b = tribe_b.cultural_ledger.get("language", {})
                    lex_a = lang_a.get("lexicon", {})
                    lex_b = lang_b.get("lexicon", {})

                    # Only borrow if tribes have substantial lexicons
                    if len(lex_a) < 10 or len(lex_b) < 10:
                        continue

                    # Find concepts that tribe_a has but tribe_b doesn't
                    borrowable_concepts = [
                        c
                        for c in lex_a.keys()
                        if c not in lex_b
                        and c
                        not in [
                            "food",
                            "water",
                            "danger",
                            "tribe",
                            "trade",
                            "hunt",
                            "ally",
                            "spirit",
                        ]
                    ]

                    if borrowable_concepts:
                        concept = random.choice(borrowable_concepts)
                        original_word = lex_a[concept]

                        # Get culture descriptions
                        culture_a = tribe_a._get_tribe_culture_description()
                        culture_b = tribe_b._get_tribe_culture_description()

                        # Use LLM to adapt the word
                        from gemini_narrative import generate_cultural_borrowing

                        adapted_word = generate_cultural_borrowing(
                            original_word, concept, culture_b, culture_a
                        )

                        if (
                            adapted_word
                            and not adapted_word.startswith("[LLM")
                            and adapted_word != original_word
                        ):
                            # Add the borrowed word to tribe_b's lexicon
                            tribe_b._add_language_entry(
                                concept,
                                word=adapted_word,
                                evolution_reason="cultural_borrowing",
                            )
                            usage_b = lang_b.setdefault("usage", {})
                            usage_b[concept] = 1

                            # Track borrowing
                            borrowing_info = lang_b.setdefault("borrowing", {})
                            borrowing_info[concept] = {
                                "original_word": original_word,
                                "adapted_word": adapted_word,
                                "from_tribe": name_a,
                                "borrowed_day": current_day,
                            }

                            tribe_b.add_tribal_memory(
                                "word_borrowed",
                                {
                                    "concept": concept,
                                    "from_tribe": name_a,
                                    "original": original_word,
                                    "adapted": adapted_word,
                                },
                            )

                            self.logger.info(
                                f"[Cultural Borrowing] {name_b} borrowed '{concept}' from {name_a}: '{original_word}' -> '{adapted_word}'"
                            )
                            break  # Only one borrowing per tribe pair per cycle

                except Exception as e:
                    self.logger.debug(
                        f"Failed cultural borrowing between {name_a} and {name_b}: {e}"
                    )

    def generate_language_analytics(self, current_day: int = 0):
        """Aggregate language-related metrics across all tribes.

        Returns a dict suitable for JSON export containing per-tribe metrics
        and global aggregates. Does not mutate state.
        """
        data = {
            "generated_day": current_day,
            "tribes": {},
            "pidgin_pair_count": 0,
            "global": {
                "total_lexicon": 0,
                "average_prestige": 0.0,
                "average_volatility": 0.0,
                "total_obsolete": 0,
                "total_alternates": 0,
                "total_myths": 0,
            },
        }
        pidgin_pairs = set()
        total_prestige = 0.0
        total_volatility = 0.0
        for tribe_name, tribe in self.tribes.items():
            try:
                lang = tribe.cultural_ledger.get("language", {})
                lex = lang.get("lexicon", {})
                usage = lang.get("usage", {})
                alternates = lang.get("alternates", {})
                obsolete = lang.get("obsolete", {})
                morphology = lang.get("morphology", {})
                pidgins = lang.get("pidgins", {})
                convergence = lang.get("convergence", {}).get("partners", {})
                prestige = lang.get("prestige", 0.0)
                volatility = lang.get("volatility", 0.0)
                myths = tribe.cultural_ledger.get("history_myths", {}).get("myths", [])
                # track pidgin pair counting once
                for partner in pidgins.keys():
                    key = tuple(sorted([tribe_name, partner]))
                    pidgin_pairs.add(key)
                lexicon_size = len(lex)
                top_usage = sorted(usage.items(), key=lambda x: x[1], reverse=True)[:5]
                data["tribes"][tribe_name] = {
                    "lexicon_size": lexicon_size,
                    "prestige": round(prestige, 3),
                    "volatility": round(volatility, 3),
                    "alternates": len(alternates),
                    "obsolete": len(obsolete),
                    "pidgin_partners": list(pidgins.keys()),
                    "convergence_partners": list(convergence.keys()),
                    "avg_usage": (
                        round(sum(usage.values()) / max(1, len(usage)), 3) if usage else 0
                    ),
                    "top_usage": top_usage,
                    "affix_productivity": morphology.get("affix_usage", {}),
                    "derived_forms": len(morphology.get("derived", {})),
                    "myth_count": len(myths),
                }
                data["global"]["total_lexicon"] += lexicon_size
                data["global"]["total_obsolete"] += len(obsolete)
                data["global"]["total_alternates"] += len(alternates)
                data["global"]["total_myths"] += len(myths)
                total_prestige += prestige
                total_volatility += volatility
            except Exception:
                continue
        tribe_count = max(1, len(self.tribes))
        data["global"]["average_prestige"] = round(total_prestige / tribe_count, 3)
        data["global"]["average_volatility"] = round(total_volatility / tribe_count, 3)
        data["pidgin_pair_count"] = len(pidgin_pairs)
        return data

    def _persist_language_analytics(self, analytics: dict):
        """Save analytics snapshot to persistence/language_analytics/ as JSON."""
        base_dir = os.path.join("persistence", "language_analytics")
        try:
            os.makedirs(base_dir, exist_ok=True)
            day = analytics.get("generated_day", 0)
            path = os.path.join(base_dir, f"analytics_day_{day}.json")
            with open(path, "w", encoding="utf-8") as f:
                json.dump(analytics, f, ensure_ascii=False, indent=2)
            self.logger.debug(f"Saved language analytics snapshot: {path}")
            # Enforce retention after save
            self._enforce_analytics_retention(base_dir)
        except Exception as e:
            self.logger.warning(f"Failed to persist language analytics: {e}")

    def _reconstruct_missing_snapshot(self, missing_day: int, base_dir: str) -> bool:
        """Attempt to reconstruct a deleted/corrupt snapshot.

        Strategy:
        1. If an uncompressed JSON for that day still exists (edge race), compress it and return True.
        2. Otherwise locate the nearest NEWER intact uncompressed JSON (analytics_day_X.json with X > missing_day) and
           clone minimal header inserting a reconstruction marker (not a true historical restoration but keeps continuity).
        3. If none newer, write a tiny gap marker JSON for the missing day.
        Returns True if a reconstruction or gap marker file was written, else False.
        """
        try:
            target_json = os.path.join(base_dir, f"analytics_day_{missing_day}.json")
            if os.path.isfile(target_json):  # race: file exists uncompressed
                try:
                    # Just compress to restore compressed lineage
                    with open(target_json, "rb") as f_in, gzip.open(
                        target_json + ".gz", "wb"
                    ) as f_out:
                        f_out.writelines(f_in)
                    self.logger.info(
                        f"[LangAnalytics][Reconstruct] Compressed existing JSON for day {missing_day}"
                    )
                    self._log_reconstruction_event(
                        day=missing_day, action="compressed_existing", details={}
                    )
                    return True
                except Exception:
                    pass
            # Scan for newer intact JSONs
            json_files = [
                f
                for f in os.listdir(base_dir)
                if f.startswith("analytics_day_") and f.endswith(".json")
            ]
            newer = []
            for f in json_files:
                day = self._extract_day(f)
                if day > missing_day:
                    newer.append((day, f))
            newer.sort()
            reconstructed_path = target_json
            if newer:
                # Use earliest newer snapshot as template baseline
                template_day, template_file = newer[0]
                try:
                    with open(os.path.join(base_dir, template_file), "r", encoding="utf-8") as f:
                        template_data = json.load(f)
                except Exception:
                    template_data = {}
                recon = {
                    "generated_day": missing_day,
                    "reconstructed": True,
                    "source_template_day": template_day,
                    "tribes": template_data.get("tribes", {}),
                    "pidgin_pair_count": template_data.get("pidgin_pair_count", 0),
                    "global": template_data.get("global", {}),
                    "note": "Reconstructed placeholder; original corrupt archive removed.",
                }
                reconstruction_action = "reconstructed_from_template"
            else:
                # Write gap marker (empty placeholder)
                recon = {
                    "generated_day": missing_day,
                    "reconstructed": True,
                    "gap_only": True,
                    "tribes": {},
                    "pidgin_pair_count": 0,
                    "global": {},
                    "note": "Gap marker inserted; no data available for this day.",
                }
                reconstruction_action = "gap_marker"
            with open(reconstructed_path, "w", encoding="utf-8") as f:
                json.dump(recon, f, ensure_ascii=False, indent=2)
            # Also produce compressed form to mirror original state
            try:
                with open(reconstructed_path, "rb") as f_in, gzip.open(
                    reconstructed_path + ".gz", "wb"
                ) as f_out:
                    f_out.writelines(f_in)
                self.logger.info(
                    f"[LangAnalytics][Reconstruct] Added reconstructed snapshot for day {missing_day}"
                )
            except Exception as ce:
                self.logger.debug(f"Reconstruction compression failed for day {missing_day}: {ce}")
            # Log reconstruction (including gap markers)
            try:
                self._log_reconstruction_event(
                    day=missing_day,
                    action=reconstruction_action,
                    details={
                        "template_day": recon.get("source_template_day"),
                        "gap_only": recon.get("gap_only", False),
                    },
                )
            except Exception:
                pass
            return True
        except Exception as e:
            self.logger.debug(f"Reconstruction failed for day {missing_day}: {e}")
            return False

    def _log_reconstruction_event(self, day: int, action: str, details: Dict):
        """Append a reconstruction event to reconstruction_log.json.

        Stored as a JSON list of event objects (chronological append). If file does not exist,
        it is created. On corruption, a new file is started and old is renamed with .corrupt timestamp.
        """
        base_dir = os.path.join("persistence", "language_analytics")
        os.makedirs(base_dir, exist_ok=True)
        log_path = os.path.join(base_dir, "reconstruction_log.json")
        event = {
            "ts": datetime.utcnow().isoformat() + "Z",
            "day": day,
            "action": action,
            "details": details or {},
        }
        data = []
        if os.path.isfile(log_path):
            try:
                with open(log_path, "r", encoding="utf-8") as f:
                    existing = json.load(f)
                if isinstance(existing, list):
                    data = existing
            except Exception:
                # Corrupt log: rename and start anew
                try:
                    corrupt_name = (
                        f"reconstruction_log_{int(datetime.utcnow().timestamp())}.corrupt"
                    )
                    os.rename(log_path, os.path.join(base_dir, corrupt_name))
                except Exception:
                    pass
                data = []
        data.append(event)
        # Compact if exceeding threshold
        if len(data) > self._reconstruction_log_max:
            data = self._compact_reconstruction_log_data(data)
        try:
            with open(log_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            self.logger.debug(f"Failed to write reconstruction log: {e}")

    def _compact_reconstruction_log_data(self, events: List[Dict]) -> List[Dict]:
        """Reduce reconstruction log size while preserving recent detail and historical summary.

        Strategy:
        - Keep newest 300 events verbatim
        - Summarize older events (the remainder) into a single synthetic summary block capturing counts per action and day span.
        """
        try:
            if len(events) <= self._reconstruction_log_max:
                return events
            keep = 300
            recent = events[-keep:]
            older = events[:-keep]
            if not older:
                return events
            action_counts = {}
            first_day = None
            last_day = None
            for ev in older:
                day = ev.get("day")
                if isinstance(day, int):
                    if first_day is None or day < first_day:
                        first_day = day
                    if last_day is None or day > last_day:
                        last_day = day
                action = ev.get("action", "unknown")
                action_counts[action] = action_counts.get(action, 0) + 1
            summary_event = {
                "ts": datetime.utcnow().isoformat() + "Z",
                "action": "compaction_summary",
                "details": {
                    "range": {"first_day": first_day, "last_day": last_day},
                    "total_collapsed": len(older),
                    "action_breakdown": action_counts,
                },
            }
            return [summary_event] + recent
        except Exception as e:
            self.logger.debug(f"Compaction failed: {e}")
            return events

    def _get_reconstruction_summary(self) -> Dict:
        """Produce lightweight summary of reconstruction log for embedding in analytics exports."""
        base_dir = os.path.join("persistence", "language_analytics")
        log_path = os.path.join(base_dir, "reconstruction_log.json")
        summary = {
            "total_events": 0,
            "compressed": False,
            "recent_actions": {},
            "recent_reconstructed_days": [],
        }
        try:
            if not os.path.isfile(log_path):
                return summary
            with open(log_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            if not isinstance(data, list):
                return summary
            summary["total_events"] = len(data)
            # Detect compaction summary presence
            if data and data[0].get("action") == "compaction_summary":
                summary["compressed"] = True
            # Consider last 25 non-summary events
            recent = [e for e in data if e.get("action") != "compaction_summary"][-25:]
            for ev in recent:
                act = ev.get("action")
                summary["recent_actions"][act] = summary["recent_actions"].get(act, 0) + 1
                if act in (
                    "gap_marker",
                    "reconstructed_from_template",
                    "compressed_existing",
                ):
                    d = ev.get("day")
                    if isinstance(d, int):
                        summary["recent_reconstructed_days"].append(d)
            # Deduplicate & sort days
            summary["recent_reconstructed_days"] = sorted(set(summary["recent_reconstructed_days"]))
        except Exception as e:
            self.logger.debug(f"Reconstruction summary failed: {e}")
        return summary

    # === Analytics Archive Integrity Validation ===
    def _validate_analytics_archives(
        self, sample: int = 5, auto_repair: bool = False
    ) -> Dict[str, Dict[str, str]]:
        """Validate readability of recent compressed analytics archives.

        Attempts to open and parse up to `sample` most recent .json.gz files.
        Returns dict mapping filename -> {status: 'ok'|'corrupt'|'error', detail: msg}.
        """
        results: Dict[str, Dict[str, str]] = {}
        base_dir = os.path.join("persistence", "language_analytics")
        try:
            if not os.path.isdir(base_dir):
                return results
            gz_files = [
                f
                for f in os.listdir(base_dir)
                if f.startswith("analytics_day_") and f.endswith(".json.gz")
            ]
            if not gz_files:
                return results
            # Sort descending by extracted day
            gz_files.sort(key=lambda x: self._extract_day(x), reverse=True)
            for fname in gz_files[:sample]:
                fpath = os.path.join(base_dir, fname)
                try:
                    with gzip.open(fpath, "rt", encoding="utf-8") as f:
                        data = json.load(f)
                    # Lightweight sanity checks
                    if "generated_day" in data and "tribes" in data:
                        results[fname] = {"status": "ok", "detail": "parsed"}
                    else:
                        results[fname] = {
                            "status": "error",
                            "detail": "missing expected keys",
                        }
                except (OSError, json.JSONDecodeError) as e:
                    results[fname] = {"status": "corrupt", "detail": str(e)}
                    if auto_repair:
                        try:
                            os.remove(fpath)
                            results[fname]["repaired"] = "deleted"
                            self.logger.warning(
                                f"[LangAnalytics][Integrity] Removed corrupt archive {fname}"
                            )
                            day = self._extract_day(fname)
                            if day >= 0:
                                if self._reconstruct_missing_snapshot(day, base_dir):
                                    results[fname]["reconstruction"] = "created"
                                else:
                                    results[fname]["reconstruction"] = "failed"
                        except Exception as del_err:
                            results[fname]["repaired"] = f"delete_failed: {del_err}"
                except Exception as e:  # unexpected
                    results[fname] = {"status": "error", "detail": str(e)}
        except Exception as outer:
            self.logger.debug(f"Archive validation sweep failed: {outer}")
        # Log summary
        if results:
            ok = sum(1 for r in results.values() if r["status"] == "ok")
            corrupt = sum(1 for r in results.values() if r["status"] == "corrupt")
            err = sum(1 for r in results.values() if r["status"] == "error")
            self.logger.info(
                f"[LangAnalytics][Integrity] validated={len(results)} ok={ok} corrupt={corrupt} other_errors={err}"
            )
        return results

    def run_language_archive_validation(
        self, sample: int = 5, auto_repair: bool = False
    ) -> Dict[str, Dict[str, str]]:
        """Public helper to manually trigger archive validation.

        auto_repair: if True, delete corrupt gzip archives encountered.
        """
        return self._validate_analytics_archives(sample=sample, auto_repair=auto_repair)

    # === Cultural Summary Export ===
    def export_cultural_summary(self, path: str = None, include_csv: bool = True) -> Optional[str]:
        """Export per-tribe cultural status snapshots to JSON (and optional CSV).

        JSON structure:
        {
          'generated_ts': iso8601,
          'tribe_count': N,
          'tribes': {
             tribe_name: {cultural_status_report()...}
          },
          'aggregates': {
             'avg_lexicon': float, 'avg_prestige': float,
             'value_frequency': {value_name: count}
          }
        }
        Returns primary JSON filepath or None on failure.
        """
        try:
            from datetime import datetime as _dt

            base_dir = path or os.path.join("persistence", "cultural_exports")
            os.makedirs(base_dir, exist_ok=True)
            snapshot = {
                "generated_ts": _dt.utcnow().isoformat() + "Z",
                "tribe_count": len(self.tribes),
                "tribes": {},
                "aggregates": {},
            }
            total_lex = 0
            total_prestige = 0.0
            value_freq = {}
            for name, tribe in self.tribes.items():
                if hasattr(tribe, "cultural_status_report"):
                    cs = tribe.cultural_status_report()
                else:
                    continue
                snapshot["tribes"][name] = cs
                total_lex += cs.get("lexicon_size", 0)
                total_prestige += cs.get("prestige", 0.0)
                for v in cs.get("top_values", []):
                    value_freq[v] = value_freq.get(v, 0) + 1
            n = max(1, len(snapshot["tribes"]))
            snapshot["aggregates"] = {
                "avg_lexicon": round(total_lex / n, 2),
                "avg_prestige": round(total_prestige / n, 3),
                "value_frequency": value_freq,
            }
            # Write JSON
            json_name = f"cultural_summary_{int(_dt.utcnow().timestamp())}.json"
            json_path = os.path.join(base_dir, json_name)
            with open(json_path, "w", encoding="utf-8") as f:
                json.dump(snapshot, f, ensure_ascii=False, indent=2)
            self.logger.info(f"[CultureExport] Wrote JSON cultural summary -> {json_path}")
            # Optional CSV (wide format)
            if include_csv:
                try:
                    import csv

                    csv_name = json_name.replace(".json", ".csv")
                    csv_path = os.path.join(base_dir, csv_name)
                    fieldnames = [
                        "tribe",
                        "lexicon_size",
                        "prestige",
                        "ritual_count",
                        "commemorative_rituals",
                        "top_values",
                        "active_rituals",
                        "last_mutations",
                        "famine_streak",
                        "plague_streak",
                    ]
                    with open(csv_path, "w", newline="", encoding="utf-8") as cf:
                        writer = csv.DictWriter(cf, fieldnames=fieldnames)
                        writer.writeheader()
                        for tname, data in snapshot["tribes"].items():
                            writer.writerow(
                                {
                                    "tribe": tname,
                                    "lexicon_size": data.get("lexicon_size"),
                                    "prestige": data.get("prestige"),
                                    "ritual_count": data.get("ritual_count"),
                                    "commemorative_rituals": data.get("commemorative_rituals"),
                                    "top_values": "|".join(data.get("top_values", [])),
                                    "active_rituals": "|".join(data.get("active_rituals", [])),
                                    "last_mutations": "|".join(
                                        [
                                            m.get("trigger", "")
                                            for m in data.get("last_mutations", [])
                                        ]
                                    ),
                                    "famine_streak": data.get("streaks", {}).get("famine_streak"),
                                    "plague_streak": data.get("streaks", {}).get("plague_streak"),
                                }
                            )
                    self.logger.info(f"[CultureExport] Wrote CSV cultural summary -> {csv_path}")
                except Exception as ce:
                    self.logger.debug(f"CSV export failed: {ce}")
            return json_path
        except Exception as e:
            self.logger.warning(f"Failed cultural summary export: {e}")
            return None

    def save_latest_language_analytics(self):
        """Manually force-save the most recent analytics snapshot."""
        if getattr(self, "_last_language_analytics", None):
            try:
                self._persist_language_analytics(self._last_language_analytics)
                return True
            except Exception:
                return False
        return False

    def configure_analytics_retention(
        self,
        keep_latest: int = None,
        compress_older: bool = None,
        max_compressed: int = None,
    ):
        """Adjust retention policy at runtime.

        keep_latest: how many recent JSON snapshots to keep uncompressed
        compress_older: whether to gzip older snapshots instead of deleting immediately
        max_compressed: maximum number of compressed (.gz) snapshots retained
        """
        if keep_latest is not None and keep_latest >= 0:
            self._analytics_retention = keep_latest
        if compress_older is not None:
            self._analytics_compress_older = bool(compress_older)
        if max_compressed is not None and max_compressed >= 0:
            self._analytics_max_compressed = max_compressed
        self.logger.info(
            f"Updated analytics retention: keep={self._analytics_retention} compress={self._analytics_compress_older} max_compressed={self._analytics_max_compressed}"
        )

    def _enforce_analytics_retention(self, base_dir: str):
        """Apply rolling window + optional compression for analytics snapshots."""
        try:
            files = [
                f
                for f in os.listdir(base_dir)
                if f.startswith("analytics_day_")
                and (f.endswith(".json") or f.endswith(".json.gz"))
            ]
            # Separate plain and compressed
            plain = sorted(
                [f for f in files if f.endswith(".json")],
                key=lambda x: self._extract_day(x),
            )
            compressed = sorted(
                [f for f in files if f.endswith(".json.gz")],
                key=lambda x: self._extract_day(x),
            )
            # If too many plain, move oldest beyond retention to compression or delete
            if len(plain) > self._analytics_retention:
                overflow = plain[0 : len(plain) - self._analytics_retention]
                for fname in overflow:
                    full = os.path.join(base_dir, fname)
                    if self._analytics_compress_older:
                        self._compress_snapshot(full)
                    else:
                        os.remove(full)
            # Refresh lists after compression
            files = [
                f
                for f in os.listdir(base_dir)
                if f.startswith("analytics_day_")
                and (f.endswith(".json") or f.endswith(".json.gz"))
            ]
            compressed = sorted(
                [f for f in files if f.endswith(".json.gz")],
                key=lambda x: self._extract_day(x),
            )
            # Prune compressed if exceeding cap
            if len(compressed) > self._analytics_max_compressed:
                prune = compressed[0 : len(compressed) - self._analytics_max_compressed]
                for fname in prune:
                    os.remove(os.path.join(base_dir, fname))
        except Exception as e:
            self.logger.debug(f"Analytics retention pass skipped: {e}")

    def _extract_day(self, filename: str) -> int:
        try:
            core = filename.split("analytics_day_")[1]
            num_part = core.split(".json")[0].replace(".gz", "")
            return int(num_part)
        except Exception:
            return -1

    def _compress_snapshot(self, path: str):
        try:
            if not path.endswith(".json"):
                return
            gz_path = path + ".gz"
            with open(path, "rb") as f_in, gzip.open(gz_path, "wb") as f_out:
                f_out.writelines(f_in)
            os.remove(path)
            self.logger.debug(f"Compressed analytics snapshot: {gz_path}")
        except Exception as e:
            self.logger.debug(f"Compression failed for {path}: {e}")

    def _sync_tribe_faction_territories(self, world):
        """Sync tribal territories with faction territories"""
        for tribe_name, territory in self.territories.items():
            if tribe_name in world.factions:
                faction = world.factions[tribe_name]
                # Update faction territory to match tribal territory
                faction.territory = list(territory.claimed_tiles)
                if faction.territory:
                    self.logger.debug(
                        f"Synced faction '{tribe_name}' territory: {len(faction.territory)} tiles"
                    )

        # Process resource competition
        self.process_resource_competition()

        # Establish trade networks
        self.establish_trade_networks()

        self.logger.info("Processed tribal dynamics for all tribes")

    def _process_territory_expansion(self, world):
        """Process territory expansion for tribes"""
        for tribe_name, territory in self.territories.items():
            tribe = self.tribes[tribe_name]

            # Chance to expand territory based on tribe size and resources
            expansion_chance = min(0.1, len(tribe.member_ids) * 0.02)  # Max 10% chance per turn

            if random.random() < expansion_chance:
                # Find a border tile to expand from
                if territory.border_tiles:
                    expand_from = random.choice(list(territory.border_tiles))

                    # Try to expand in a random adjacent direction
                    directions = [
                        (0, 1),
                        (1, 0),
                        (0, -1),
                        (-1, 0),
                        (1, 1),
                        (1, -1),
                        (-1, 1),
                        (-1, -1),
                    ]
                    random.shuffle(directions)

                    for dx, dy in directions:
                        new_tile = (expand_from[0] + dx, expand_from[1] + dy)

                        # Check if tile is already claimed by another tribe
                        tile_claimed = False
                        for (
                            other_tribe_name,
                            other_territory,
                        ) in self.territories.items():
                            if (
                                other_tribe_name != tribe_name
                                and new_tile in other_territory.claimed_tiles
                            ):
                                tile_claimed = True
                                break

                        if not tile_claimed:
                            # Claim the new tile
                            territory.claim_tile(new_tile)
                            self.logger.info(
                                f"Tribe '{tribe_name}' expanded territory to {new_tile}"
                            )
                            break

    def _assign_leadership_roles(self):
        """Assign leadership roles to NPCs in all tribes."""
        # This would need access to the NPC objects - placeholder for integration
        # In a full implementation, this would get NPCs from the world engine
        for tribe_name, role_manager in self.role_managers.items():
            # For now, we'll skip the actual assignment since we don't have NPC objects here
            # In the full system, this would be called with: role_manager.assign_leadership_roles(npcs)
            pass

    def get_tribal_wellbeing_report(self) -> Dict[str, Dict[str, float]]:
        """Get wellbeing reports for all tribes"""
        report = {}
        for tribe_name, tribe in self.tribes.items():
            report[tribe_name] = tribe.get_wellbeing_report()
        return report

    def to_dict(self) -> Dict:
        """Serialize all tribal data"""
        return {
            "tribes": {name: tribe.to_dict() for name, tribe in self.tribes.items()},
            "tribal_conflict": self.tribal_conflict.conflict_history,
            "tribal_diplomacy": self.tribal_diplomacy.diplomatic_history,
        }

    def from_dict(self, data: Dict):
        """Deserialize tribal data"""
        # Recreate tribes
        for name, tribe_data in data.get("tribes", {}).items():
            tribe = Tribe.from_dict(tribe_data)
            self.tribes[name] = tribe

            # Recreate supporting systems
            self.role_managers[name] = TribalRoleManager(tribe)
            self.territories[name] = TribalTerritory(tribe)
            self.camps[name] = TribalCamp(tribe, tribe.camp_location or (0, 0))
            self.architectures[name] = TribalArchitecture(tribe)

        # Restore conflict and diplomacy history
        self.tribal_conflict.conflict_history = data.get("tribal_conflict", [])
        self.tribal_diplomacy.diplomatic_history = data.get("tribal_diplomacy", [])

    def process_tribal_events(self):
        """Process random tribal events and ceremonies with seasonal awareness"""

        # Get seasonal context if available (passed from world engine)
        seasonal_context = getattr(self, "_current_seasonal_context", None)
        season = seasonal_context["season"] if seasonal_context else 0
        season_name = seasonal_context["season_name"] if seasonal_context else "Spring"

        for tribe_name, tribe in self.tribes.items():
            # ===== SEASONAL ACTIVITY PRIORITIES =====
            self._process_seasonal_activities(tribe, season, season_name)

            # ===== REGULAR TRIBAL CEREMONIES (adjusted for season) =====
            # Seasonal ceremony likelihood adjustments
            ceremony_chance = 0.1  # Base 10% chance
            if season == 3:  # Winter - fewer ceremonies, conserve energy
                ceremony_chance = 0.05
            elif season == 1:  # Summer - more ceremonies
                ceremony_chance = 0.15

            if random.random() < ceremony_chance:
                ceremony_types = self._get_seasonal_ceremony_types(season)
                ceremony_type = random.choice(ceremony_types)
                ceremony_result = tribe.perform_ceremony(ceremony_type)

                if ceremony_result:
                    self.logger.info(
                        f"Tribe {tribe_name} performed {ceremony_type} ceremony: {ceremony_result['description']}"
                    )

            # ===== SEASONAL PROPHECY DEVELOPMENT =====
            prophecy_chance = 0.05  # Base 5% chance
            if season == 2:  # Autumn - more prophecies about coming winter
                prophecy_chance = 0.08

            if random.random() < prophecy_chance:
                prophecy = tribe.develop_prophecy()
                self.logger.info(f"Tribe {tribe_name} developed prophecy: {prophecy}")

            # ===== SEASONAL MIGRATION =====
            # Seasonal migration happens more frequently and is season-appropriate
            migration_chance = 0.03  # Base 3% chance
            if season == 0 or season == 2:  # Spring and Autumn - migration seasons
                migration_chance = 0.06

            if random.random() < migration_chance:
                # Use current season for migration
                season_names = ["spring", "summer", "autumn", "winter"]
                current_season = season_names[season]

                # Generate nearby migration location
                if tribe.camp_location:
                    cx, cy = tribe.camp_location
                    dx = random.randint(-5, 5)
                    dy = random.randint(-5, 5)
                    new_location = (cx + dx, cy + dy)
                    tribe.migrate_seasonally(current_season, new_location)
                    self.logger.info(
                        f"Tribe {tribe_name} migrated to seasonal camp at {new_location} for {current_season}"
                    )

    def _process_seasonal_activities(self, tribe, season, season_name):
        """Process season-specific tribal activities"""

        # ===== WINTER ACTIVITIES =====
        if season == 3:  # Winter
            # Focus on survival, shelter building, storytelling
            if random.random() < 0.15:  # 15% chance
                activity_type = random.choice(
                    [
                        "shelter_reinforcement",
                        "storytelling_session",
                        "resource_conservation",
                    ]
                )
                if activity_type == "shelter_reinforcement":
                    tribe.add_tribal_memory(
                        "winter_preparation",
                        {
                            "activity": "shelter_reinforcement",
                            "description": "Tribe reinforces shelters against winter storms",
                        },
                    )
                    self.logger.info(f"Tribe {tribe.name} reinforced shelters for winter")
                elif activity_type == "storytelling_session":
                    tribe.add_tribal_memory(
                        "cultural_activity",
                        {
                            "activity": "winter_storytelling",
                            "description": "Elders share stories during long winter nights",
                        },
                    )
                    self.logger.info(f"Tribe {tribe.name} held winter storytelling session")
                elif activity_type == "resource_conservation":
                    # Reduce resource consumption rate
                    self.logger.info(
                        f"Tribe {tribe.name} implemented winter resource conservation measures"
                    )

        # ===== AUTUMN ACTIVITIES =====
        elif season == 2:  # Autumn
            # Focus on preparation, food storage, gathering
            if random.random() < 0.20:  # 20% chance - high activity in preparation season
                activity_type = random.choice(
                    ["harvest_gathering", "food_preservation", "winter_preparation"]
                )
                if activity_type == "harvest_gathering":
                    # Bonus resource gathering
                    bonus_food = random.randint(5, 15)
                    tribe.add_shared_resource("food", bonus_food)
                    tribe.add_tribal_memory(
                        "seasonal_activity",
                        {
                            "activity": "autumn_harvest",
                            "description": f"Tribe gathered {bonus_food} extra food for winter",
                            "bonus_food": bonus_food,
                        },
                    )
                    self.logger.info(
                        f"Tribe {tribe.name} conducted autumn harvest gathering (+{bonus_food} food)"
                    )
                elif activity_type == "food_preservation":
                    # Convert some resources to preserved food
                    current_food = tribe.shared_resources.get("food", 0)
                    if current_food > 10:
                        preserved_amount = min(5, current_food // 3)
                        tribe.add_shared_resource("preserved_food", preserved_amount)
                        self.logger.info(
                            f"Tribe {tribe.name} preserved {preserved_amount} food for winter"
                        )

        # ===== SPRING ACTIVITIES =====
        elif season == 0:  # Spring
            # Focus on expansion, exploration, renewal
            if random.random() < 0.18:  # 18% chance
                activity_type = random.choice(
                    ["territory_scouting", "renewal_ceremony", "expansion_planning"]
                )
                if activity_type == "territory_scouting":
                    tribe.add_tribal_memory(
                        "expansion_activity",
                        {
                            "activity": "spring_scouting",
                            "description": "Scouts explore new territory for spring expansion",
                        },
                    )
                    self.logger.info(f"Tribe {tribe.name} conducted spring territory scouting")
                elif activity_type == "renewal_ceremony":
                    tribe.add_tribal_memory(
                        "seasonal_ceremony",
                        {
                            "activity": "spring_renewal",
                            "description": "Tribe celebrates renewal and new beginnings",
                        },
                    )
                    self.logger.info(f"Tribe {tribe.name} held spring renewal ceremony")

        # ===== SUMMER ACTIVITIES =====
        elif season == 1:  # Summer
            # Focus on peak activity, trade, social events
            if random.random() < 0.12:  # 12% chance
                activity_type = random.choice(
                    ["trading_expedition", "summer_festival", "peak_gathering"]
                )
                if activity_type == "trading_expedition":
                    tribe.add_tribal_memory(
                        "economic_activity",
                        {
                            "activity": "summer_trading",
                            "description": "Tribe sends trading expedition during peak travel season",
                        },
                    )
                    self.logger.info(f"Tribe {tribe.name} organized summer trading expedition")
                elif activity_type == "summer_festival":
                    # Boost morale and inter-tribal relations
                    tribe.add_tribal_memory(
                        "cultural_celebration",
                        {
                            "activity": "summer_festival",
                            "description": "Tribe celebrates summer abundance with grand festival",
                        },
                    )
                    self.logger.info(f"Tribe {tribe.name} held summer abundance festival")

    def _get_seasonal_ceremony_types(self, season):
        """Get ceremony types appropriate for the current season"""
        base_ceremonies = ["hunting", "healing", "initiation", "thanksgiving"]

        if season == 3:  # Winter
            return [
                "healing",
                "thanksgiving",
                "protection",
            ]  # Focus on survival and gratitude
        elif season == 2:  # Autumn
            return [
                "thanksgiving",
                "harvest",
                "preparation",
            ]  # Focus on gratitude and preparation
        elif season == 0:  # Spring
            return [
                "initiation",
                "renewal",
                "hunting",
            ]  # Focus on new beginnings and growth
        else:  # Summer
            return [
                "hunting",
                "celebration",
                "abundance",
            ]  # Focus on peak activity and celebration

        return base_ceremonies

    def process_resource_competition(self):
        """Process resource competition between tribes"""
        tribe_names = list(self.tribes.keys())

        # Check for resource competition between nearby tribes
        for i, tribe1_name in enumerate(tribe_names):
            for tribe2_name in tribe_names[i + 1 :]:
                tribe1 = self.tribes[tribe1_name]
                tribe2 = self.tribes[tribe2_name]

                # Check if tribes are close enough for competition
                if tribe1.camp_location and tribe2.camp_location:
                    distance = abs(tribe1.camp_location[0] - tribe2.camp_location[0]) + abs(
                        tribe1.camp_location[1] - tribe2.camp_location[1]
                    )

                    if distance <= 10 and random.random() < 0.1:  # Close tribes, 10% chance
                        # Compete for a random resource
                        resource_types = ["food", "wood", "stone", "herbs"]
                        resource_type = random.choice(resource_types)

                        competition_result = tribe1.compete_for_resources(resource_type, tribe2)

                        if competition_result["outcome"] == "victory":
                            # Winner gets resources
                            reward_amount = random.randint(5, 15)
                            tribe1.add_shared_resource(resource_type, reward_amount)
                            self.logger.info(
                                f"Tribe {tribe1_name} won resource competition for {resource_type}, gaining {reward_amount}"
                            )
                        elif competition_result["outcome"] == "defeat":
                            # Loser loses some resources
                            loss_amount = random.randint(3, 8)
                            if tribe1.take_shared_resource(resource_type, loss_amount) > 0:
                                self.logger.info(
                                    f"Tribe {tribe1_name} lost resource competition for {resource_type}, losing {loss_amount}"
                                )

    def establish_trade_networks(self):
        """Establish trade networks between compatible tribes"""
        tribe_names = list(self.tribes.keys())

        for tribe1_name in tribe_names:
            for tribe2_name in tribe_names:
                if tribe1_name != tribe2_name:
                    tribe1 = self.tribes[tribe1_name]
                    tribe2 = self.tribes[tribe2_name]

                    # Establish trade if tribes are allied or have good relations
                    if (
                        tribe2_name in tribe1.alliances
                        or self.tribal_diplomacy.is_good_standing_for_trade(
                            tribe1_name, tribe2_name
                        )
                    ):

                        if tribe2_name not in tribe1.trade_network:
                            gift_bias = 0.0
                            try:
                                if hasattr(tribe1, "gift_giving_bonus"):
                                    gift_bias += tribe1.gift_giving_bonus()
                                if hasattr(tribe2, "gift_giving_bonus"):
                                    gift_bias += tribe2.gift_giving_bonus()
                            except Exception:
                                gift_bias = 0.0
                            base_prob = 0.25
                            effective_prob = min(0.9, base_prob + gift_bias)
                            if random.random() < effective_prob:
                                tribe1.establish_trade_route(tribe2_name)
                                tribe2.establish_trade_route(tribe1_name)
                                self.logger.info(
                                    f"Trade route established between {tribe1_name} and {tribe2_name} (gift_bias={gift_bias:.2f}, prob={effective_prob:.2f})"
                                )
                            else:
                                if gift_bias > 0:
                                    self.logger.debug(
                                        f"[Custom] Gift bonus influenced trade attempt {tribe1_name}<->{tribe2_name} (bias {gift_bias:.2f}) but roll failed"
                                    )
                            # === Cultural Diffusion on new trade route ===
                            try:
                                t1_ledger = getattr(tribe1, "cultural_ledger", {})
                                t2_ledger = getattr(tribe2, "cultural_ledger", {})
                                r1 = t1_ledger.get("rituals_customs", {}).get("rituals", [])
                                r2 = t2_ledger.get("rituals_customs", {}).get("rituals", [])
                                share_prob = 0.4
                                if r1 and random.random() < share_prob:
                                    sample = random.choice(r1)
                                    # Tag as adopted
                                    if isinstance(sample, dict):
                                        adopted = dict(sample)
                                        adopted["adopted_from"] = tribe1_name
                                    else:
                                        adopted = {
                                            "name": str(sample),
                                            "adopted_from": tribe1_name,
                                        }
                                    tribe2.add_ritual(
                                        **{
                                            k: v
                                            for k, v in adopted.items()
                                            if k
                                            in [
                                                "name",
                                                "purpose",
                                                "seasonal",
                                                "effects",
                                            ]
                                        }
                                    )
                                if r2 and random.random() < share_prob:
                                    sample = random.choice(r2)
                                    if isinstance(sample, dict):
                                        adopted = dict(sample)
                                        adopted["adopted_from"] = tribe2_name
                                    else:
                                        adopted = {
                                            "name": str(sample),
                                            "adopted_from": tribe2_name,
                                        }
                                    tribe1.add_ritual(
                                        **{
                                            k: v
                                            for k, v in adopted.items()
                                            if k
                                            in [
                                                "name",
                                                "purpose",
                                                "seasonal",
                                                "effects",
                                            ]
                                        }
                                    )
                                self.logger.info(
                                    f"[Diffusion] Ritual exchange evaluated between {tribe1_name} and {tribe2_name}"
                                )
                            except Exception:
                                pass

    def check_tribal_population_replacement(self, world_engine):
        """Check tribal populations and trigger recruitment if needed."""
        self.logger.info("Checking tribal populations for replacement needs...")

        for tribe_name, tribe in self.tribes.items():
            current_population = len(tribe.member_ids)

            # Population replacement thresholds
            min_population = 4  # Minimum sustainable tribal population - increased from 3
            target_population = 7  # Target population to aim for - increased from 6

            if current_population < min_population:
                self.logger.warning(
                    f"Tribe '{tribe_name}' has critically low population: {current_population}"
                )

                # Try to recruit new members
                recruits_added = self._recruit_tribal_members(
                    tribe, world_engine, target_population - current_population
                )

                if recruits_added > 0:
                    self.logger.info(
                        f"  -> Recruited {recruits_added} new members for tribe '{tribe_name}'"
                    )
                    tribe.add_tribal_memory(
                        "population_growth",
                        {
                            "type": "recruitment",
                            "new_members": recruits_added,
                            "reason": "population_replacement",
                        },
                    )

            elif current_population < target_population:
                # Less urgent but still recruit occasionally
                if random.random() < 0.05:  # 5% chance per tick
                    recruits_added = self._recruit_tribal_members(tribe, world_engine, 1)
                    if recruits_added > 0:
                        self.logger.info(
                            f"  -> Recruited {recruits_added} new member for tribe '{tribe_name}' (maintenance)"
                        )

    def _recruit_tribal_members(self, tribe, world_engine, max_recruits):
        """Recruit new members to join a tribe when population is low."""
        recruits_added = 0

        # Find suitable chunks for recruitment (near tribal territory)
        recruitment_chunks = []

        # Check tribal territory first - look for chunks that have NPCs we can recruit
        if tribe.camp_location:
            cx, cy = tribe.camp_location
            for dx in [-5, -4, -3, -2, -1, 0, 1, 2, 3, 4, 5]:
                for dy in [-5, -4, -3, -2, -1, 0, 1, 2, 3, 4, 5]:
                    try:
                        chunk = world_engine.get_chunk(cx + dx, cy + dy)
                        # Look for chunks that have NPCs we can potentially recruit
                        if len(chunk.npcs) > 0:
                            recruitment_chunks.append(chunk)
                    except (AttributeError, TypeError):
                        continue

        # Remove duplicates and limit to reasonable number
        seen_coords = set()
        unique_chunks = []
        for chunk in recruitment_chunks:
            coords = chunk.coordinates
            if coords not in seen_coords:
                seen_coords.add(coords)
                unique_chunks.append(chunk)
        recruitment_chunks = unique_chunks[:10]

        # First try to recruit existing NPCs
        for chunk in recruitment_chunks:
            if recruits_added >= max_recruits:
                break

            # Find NPCs that could join the tribe
            available_npcs = []
            for npc in chunk.npcs:
                # Must be adult, healthy, and not already in a tribe
                if (
                    npc.age >= npc.GROWN_AGE
                    and npc.health > 50
                    and (not hasattr(npc, "tribe_id") or not npc.tribe_id)
                ):

                    # Check if NPC is already in this tribe
                    if npc.name not in tribe.member_ids:
                        available_npcs.append(npc)

            if available_npcs:
                # Recruit the most suitable NPC (healthy, skilled)
                recruit = max(
                    available_npcs,
                    key=lambda npc: npc.health + sum(npc.skills.values()),
                )

                # Add to tribe
                tribe.add_member(recruit.name, TribalRole.GATHERER)  # Start as gatherer

                # Mark NPC as tribal member
                recruit.tribe_id = tribe.name

                recruits_added += 1

                self.logger.info(
                    f"  -> {recruit.name} joined tribe '{tribe.name}' in chunk {chunk.coordinates}"
                )

                # Update NPC memory
                if not hasattr(recruit, "memory"):
                    recruit.memory = []
                recruit.memory.append(
                    {
                        "type": "joined_tribe",
                        "tribe": tribe.name,
                        "location": chunk.coordinates,
                        "tick": world_engine._tick_count,
                    }
                )

                # Keep memory manageable
                if len(recruit.memory) > 10:
                    recruit.memory.pop(0)

                # Reassign roles to balance the tribe
                if tribe.name in self.role_managers:
                    self.role_managers[tribe.name].reassign_roles()

        # If we still need more recruits and couldn't find any existing NPCs, spawn new ones
        if recruits_added < max_recruits:
            recruits_needed = max_recruits - recruits_added
            spawned_recruits = self._spawn_tribal_recruits(tribe, world_engine, recruits_needed)
            recruits_added += spawned_recruits

        return recruits_added

    def _spawn_tribal_recruits(self, tribe, world_engine, max_recruits):
        """Spawn new NPCs to join a tribe when no existing NPCs are available."""
        recruits_added = 0

        if not tribe.camp_location:
            return 0

        cx, cy = tribe.camp_location

        for _ in range(max_recruits):
            # Find a suitable chunk near the tribal camp
            spawn_attempts = 0
            spawned = False

            while spawn_attempts < 20 and not spawned:
                # Try to spawn in a nearby chunk
                dx = random.randint(-3, 3)
                dy = random.randint(-3, 3)
                spawn_coords = (cx + dx, cy + dy)

                try:
                    chunk = world_engine.get_chunk(spawn_coords[0], spawn_coords[1])

                    # Check if chunk has space and is suitable
                    if len(chunk.npcs) < world_engine.CHUNK_POPULATION_CAP:
                        # Generate a new NPC
                        if tribe.name == "Wildlife":
                            child_name = tribe.get_random_animal_name()
                        else:
                            try:
                                from databank import get_databank

                                db = get_databank()
                                base = db.get_random("names")[0]
                                # Tribe-biased mutation using lexicon syllables
                                lexicon = (
                                    getattr(tribe, "cultural_ledger", {})
                                    .get("language", {})
                                    .get("lexicon", {})
                                )
                                if lexicon:
                                    syllables = []
                                    for w in list(lexicon.values())[:5]:
                                        # crude syllable split
                                        for seg in [w[i : i + 2] for i in range(0, len(w), 2)]:
                                            if 1 < len(seg) <= 3:
                                                syllables.append(seg)
                                    if syllables and random.random() < 0.5:
                                        mut = random.choice(syllables)
                                        # Insert mutation in middle
                                        mid = len(base) // 2
                                        base = base[:mid] + mut.capitalize() + base[mid:]
                                # Optional epithet or title (low probability)
                                if random.random() < 0.15:
                                    epithet = db.get_random("epithets")[0]
                                    base = f"{base} {epithet}"
                                child_name = base
                            except Exception:
                                child_name = random.choice(
                                    world_engine.NAME_PREFIXES
                                ) + random.choice(world_engine.NAME_SUFFIXES)

                        # Create new NPC
                        new_npc = NPC(
                            name=child_name,
                            coordinates=spawn_coords,
                            faction_id=tribe.name,  # Tribal NPCs are also faction members
                            age=random.randint(18, 35),  # Young adult
                            health=random.randint(70, 100),
                            skills={
                                "combat": random.randint(5, 15),
                                "crafting": random.randint(5, 15),
                                "wordbinding": random.randint(5, 15),
                                "magic": random.randint(0, 10),
                            },
                        )

                        # Set tribal affiliation
                        new_npc.tribe_id = tribe.name

                        # Add to chunk
                        chunk.npcs.append(new_npc)

                        # Add to tribe
                        tribe.add_member(new_npc.name, TribalRole.GATHERER)

                        # Record tribal memory
                        tribe.add_tribal_memory(
                            "population_growth",
                            {
                                "type": "recruitment_spawn",
                                "new_member": new_npc.name,
                                "location": spawn_coords,
                                "season": getattr(world_engine, "current_season", 0),
                            },
                        )

                        recruits_added += 1
                        spawned = True

                        self.logger.info(
                            f"  -> Spawned new tribal recruit {new_npc.name} for tribe '{tribe.name}' at {spawn_coords}"
                        )

                except Exception as e:
                    self.logger.debug(f"Failed to spawn recruit at {spawn_coords}: {e}")
                    continue

        return recruits_added

    def _adjust_tribal_priorities_for_season_global(self, seasonal_context):
        """Adjust tribal priorities and behavior based on current season"""
        season = seasonal_context["season"]
        season_name = seasonal_context["season_name"]

        # 0=Spring, 1=Summer, 2=Autumn, 3=Winter
        is_winter = season == 3
        is_autumn = season == 2
        is_spring = season == 0
        is_summer = season == 1

        self.logger.debug(f"Adjusting tribal priorities for {season_name}")

        for tribe_name, tribe in self.tribes.items():
            # ===== WINTER: SURVIVAL FOCUS =====
            if is_winter:
                # Winter: Reduce expansion, focus on survival
                # Increase food conservation thresholds
                tribe.priority_modifiers = getattr(tribe, "priority_modifiers", {})
                tribe.priority_modifiers.update(
                    {
                        "expansion_likelihood": 0.3,  # Much less territorial expansion
                        "trade_willingness": 0.6,  # Reduce trade willingness
                        "conflict_likelihood": 0.4,  # Avoid conflicts in winter
                        "resource_sharing": 1.2,  # More willing to share in crisis
                        "alliance_value": 1.3,  # Alliances more valuable for survival
                        "food_threshold": 1.5,  # Need more food reserves
                    }
                )

            # ===== AUTUMN: PREPARATION FOCUS =====
            elif is_autumn:
                # Autumn: Prepare for winter, increase resource gathering
                tribe.priority_modifiers = getattr(tribe, "priority_modifiers", {})
                tribe.priority_modifiers.update(
                    {
                        "expansion_likelihood": 0.7,  # Moderate expansion
                        "trade_willingness": 1.4,  # High trade for winter prep
                        "conflict_likelihood": 0.6,  # Moderate conflicts
                        "resource_sharing": 0.8,  # Less sharing, preparing for winter
                        "alliance_value": 1.1,  # Alliances valuable for trade
                        "food_threshold": 1.3,  # Start building reserves
                    }
                )

            # ===== SPRING: EXPANSION FOCUS =====
            elif is_spring:
                # Spring: Expansion, growth, new alliances
                tribe.priority_modifiers = getattr(tribe, "priority_modifiers", {})
                tribe.priority_modifiers.update(
                    {
                        "expansion_likelihood": 1.4,  # High territorial expansion
                        "trade_willingness": 1.2,  # Good trade opportunities
                        "conflict_likelihood": 1.1,  # Moderate conflicts for territory
                        "resource_sharing": 1.0,  # Normal sharing
                        "alliance_value": 1.2,  # New alliances for expansion
                        "food_threshold": 0.8,  # Food more available
                    }
                )

            # ===== SUMMER: ABUNDANCE FOCUS =====
            elif is_summer:
                # Summer: Peak activity, expansion, diplomacy
                tribe.priority_modifiers = getattr(tribe, "priority_modifiers", {})
                tribe.priority_modifiers.update(
                    {
                        "expansion_likelihood": 1.2,  # High expansion
                        "trade_willingness": 1.3,  # High trade activity
                        "conflict_likelihood": 1.0,  # Normal conflict levels
                        "resource_sharing": 1.1,  # Generous sharing
                        "alliance_value": 1.0,  # Normal alliance value
                        "food_threshold": 0.7,  # Food abundant
                    }
                )

            # Log priority adjustments
            if hasattr(tribe, "priority_modifiers"):
                self.logger.debug(
                    f"Tribe {tribe_name} {season_name} priorities: "
                    f"expansion={tribe.priority_modifiers.get('expansion_likelihood', 1.0):.1f}, "
                    f"trade={tribe.priority_modifiers.get('trade_willingness', 1.0):.1f}, "
                    f"conflict={tribe.priority_modifiers.get('conflict_likelihood', 1.0):.1f}"
                )

    # ===== Language Convergence Metrics =====
    def _compute_convergence_metrics(self, current_day: int = 0):
        """Compute pairwise language similarity metrics across all tribes.
        Metrics per pair:
          - concept_overlap: |intersection(concepts)| / |union(concepts)|
          - shared_concepts: count shared
          - avg_form_similarity: mean( 1 - edit_distance/ max_len ) over shared concepts
          - divergence: 1 - (concept_overlap * 0.6 + avg_form_similarity * 0.4)
        Stored under each tribe.cultural_ledger['language']['convergence']['partners'][other].
        """
        tribe_items = list(self.tribes.items())
        if len(tribe_items) < 2:
            return
        # Pre-initialize convergence containers
        for _, tribe in tribe_items:
            lang = tribe.cultural_ledger.get("language", {})
            conv = lang.setdefault("convergence", {})
            conv.setdefault("partners", {})
            conv["last_computed_day"] = current_day

        def edit_distance(a: str, b: str) -> int:
            if a == b:
                return 0
            la, lb = len(a), len(b)
            if la == 0:
                return lb
            if lb == 0:
                return la
            # DP row optimization
            prev = list(range(lb + 1))
            for i, ca in enumerate(a, 1):
                cur = [i]
                for j, cb in enumerate(b, 1):
                    cost = 0 if ca == cb else 1
                    cur.append(
                        min(
                            prev[j] + 1,  # deletion
                            cur[j - 1] + 1,  # insertion
                            prev[j - 1] + cost,  # substitution
                        )
                    )
                prev = cur
            return prev[-1]

        for i in range(len(tribe_items)):
            name_a, tribe_a = tribe_items[i]
            lex_a = tribe_a.cultural_ledger.get("language", {}).get("lexicon", {})
            concepts_a = set(lex_a.keys())
            for j in range(i + 1, len(tribe_items)):
                name_b, tribe_b = tribe_items[j]
                lex_b = tribe_b.cultural_ledger.get("language", {}).get("lexicon", {})
                concepts_b = set(lex_b.keys())
                union = concepts_a | concepts_b
                inter = concepts_a & concepts_b
                if not union:
                    concept_overlap = 0.0
                else:
                    concept_overlap = round(len(inter) / len(union), 4)
                # Form similarity only over shared concepts
                sims = []
                for concept in inter:
                    a_form = lex_a.get(concept, "")
                    b_form = lex_b.get(concept, "")
                    if not a_form or not b_form:
                        continue
                    dist = edit_distance(a_form, b_form)
                    max_len = max(len(a_form), len(b_form)) or 1
                    sims.append(1 - (dist / max_len))
                avg_form_similarity = round(sum(sims) / len(sims), 4) if sims else 0.0
                divergence = round(1 - (concept_overlap * 0.6 + avg_form_similarity * 0.4), 4)
                metrics = {
                    "concept_overlap": concept_overlap,
                    "shared_concepts": len(inter),
                    "avg_form_similarity": avg_form_similarity,
                    "divergence": divergence,
                    "computed_day": current_day,
                }
                tribe_a.cultural_ledger["language"]["convergence"]["partners"][name_b] = metrics
                tribe_b.cultural_ledger["language"]["convergence"]["partners"][name_a] = metrics
        # Optional: add memory entries for tribes with notable high overlap
        for _, tribe in tribe_items:
            try:
                partners = (
                    tribe.cultural_ledger.get("language", {})
                    .get("convergence", {})
                    .get("partners", {})
                )
                if not partners:
                    continue
                # Find partner with highest concept overlap
                best = max(partners.items(), key=lambda kv: kv[1].get("concept_overlap", 0.0))
                if best[1].get("concept_overlap", 0) >= 0.5:  # threshold for notable convergence
                    tribe.add_tribal_memory(
                        "language_convergence_update",
                        {
                            "partner": best[0],
                            "concept_overlap": best[1]["concept_overlap"],
                            "avg_form_similarity": best[1]["avg_form_similarity"],
                        },
                    )
            except Exception:
                continue
