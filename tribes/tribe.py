import logging
import random
import os
from dataclasses import dataclass, field
from typing import List, Tuple, Dict, Any, Optional, Set
from enum import Enum


class TribalRole(Enum):
    """Social roles within tribes"""

    HUNTER = "hunter"
    GATHERER = "gatherer"
    LEADER = "leader"
    SHAMAN = "shaman"
    WARRIOR = "warrior"
    CRAFTER = "crafter"


class TribalSymbol(Enum):
    """Symbolic representations for tribes"""

    EAGLE = "🦅"
    BEAR = "🐻"
    RAVEN = "🐦‍⬛"
    SERPENT = "🐍"
    STAG = "🦌"
    OWL = "🦉"
    FOX = "🦊"


@dataclass
class Tribe:
    """Represents a tribal group that can form from NPCs"""

    name: str
    symbol: str = field(default_factory=lambda: random.choice([s.value for s in TribalSymbol]))
    leader_id: Optional[str] = None
    member_ids: Set[str] = field(default_factory=set)
    territory: Set[Tuple[int, int]] = field(default_factory=set)
    camp_location: Optional[Tuple[int, int]] = None

    # Tribal resources and structures
    shared_resources: Dict[str, float] = field(
        default_factory=lambda: {"food": 0.0, "wood": 0.0, "stone": 0.0, "herbs": 0.0}
    )
    structures: Dict[str, int] = field(
        default_factory=lambda: {"campfire": 0, "shelter": 0, "storage": 0, "totem": 0}
    )

    # Social and cultural elements
    culture: Dict[str, Any] = field(
        default_factory=lambda: {
            "totems": [],  # Spiritual symbols
            "traditions": [],  # Cultural practices
            "stories": [],  # Tribal myths and legends
            "taboos": [],  # Forbidden actions
        }
    )
    cultural_quirks: Dict[str, Any] = field(
        default_factory=lambda: {
            "music_style": "",  # drumming, chanting, flute
            "body_markings": [],  # tattoos, paint patterns
            "ceremonial_dress": [],  # special clothing items
            "taboo_animals": [],  # animals considered sacred/forbidden
            "seasonal_rituals": [],  # special ceremonies by season
        }
    )

    # Tribal relationships
    alliances: Set[str] = field(default_factory=set)  # Allied tribe names
    rivalries: Set[str] = field(default_factory=set)  # Rival tribe names
    truces: Dict[str, int] = field(default_factory=dict)  # Tribe name -> turns remaining

    # Communication and language
    dialect: Dict[str, str] = field(default_factory=dict)  # Word -> tribal variant
    tribal_memory: List[Dict[str, Any]] = field(default_factory=list)

    # Economic and social systems
    resource_sharing: bool = True  # Whether tribe shares resources
    social_roles: Dict[str, TribalRole] = field(default_factory=dict)  # NPC ID -> role
    trade_network: Set[str] = field(default_factory=set)  # Connected tribes for trade
    barter_rates: Dict[str, Dict[str, float]] = field(
        default_factory=dict
    )  # Resource exchange rates
    economic_specialization: str = ""  # What the tribe specializes in

    # Spiritual beliefs and myth-making
    spiritual_beliefs: Dict[str, Any] = field(
        default_factory=lambda: {
            "creation_myth": "",
            "spirit_guides": [],  # Animal or nature spirits
            "sacred_sites": [],  # Special locations
            "prophecies": [],  # Tribal predictions/visions
            "ancestor_worship": False,
        }
    )

    # Migration and settlement patterns
    migration_patterns: List[Dict] = field(default_factory=list)  # Historical migration data
    seasonal_camps: Dict[str, Tuple[int, int]] = field(
        default_factory=dict
    )  # Seasonal camp locations

    # Tribal wellbeing metrics
    wellbeing: Dict[str, float] = field(
        default_factory=lambda: {
            "food_security": 0.5,  # How well fed the tribe is (0-1)
            "resource_availability": 0.5,  # Resource availability (0-1)
            "health": 0.7,  # Overall tribal health (0-1)
            "morale": 0.6,  # Tribal morale and cohesion (0-1)
            "security": 0.5,  # Safety and protection level (0-1)
            "cultural_richness": 0.4,  # Cultural development (0-1)
            "organizational_efficiency": 0.5,  # How well organized (0-1)
            "overall_wellbeing": 0.5,  # Composite wellbeing score (0-1)
        }
    )

    # Cultural Ledger (structured cultural DNA)
    cultural_ledger: Dict[str, Any] = field(
        default_factory=lambda: {
            "language": {  # evolving lexicon
                "lexicon": {},  # concept -> word
                "evolution_events": [],  # history of linguistic changes
                "usage": {},  # concept -> count
                "phonology": {},  # consonants, vowels, templates, affixes
                "volatility": 0.0,  # mutation propensity (0-1)
            },
            "rituals_customs": {  # social actions
                "rituals": [],  # list of ritual dicts
                "customs": [],  # simple named customs
            },
            "values": {  # core principles with weights
                "principles": {},  # value_name -> weight (0-1)
                "priority_order": [],  # cached sorted list
            },
            "history_myths": {  # narrative memory
                "significant_events": [],  # appended event summaries
                "myths": [],  # formalized myth strings
            },
        }
    )
    # Transient ritual/custom runtime state (not persisted in ledger directly)
    active_ritual_effects: List[Dict[str, Any]] = field(default_factory=list)
    custom_state: Dict[str, Any] = field(default_factory=dict)  # e.g., {'mourning_until': day}

    def __post_init__(self) -> None:
        self.logger = logging.getLogger(f"Tribe.{self.name}")
        if not self.culture["totems"]:
            self._generate_initial_culture()
        # Initialize default core values if empty
        if not self.cultural_ledger["values"]["principles"]:
            default_values = {
                "Honor": round(random.uniform(0.4, 0.8), 2),
                "Prosperity": round(random.uniform(0.4, 0.8), 2),
                "Survival": round(random.uniform(0.6, 0.9), 2),
            }
            self.cultural_ledger["values"]["principles"].update(default_values)

    def get_tribal_priorities(self) -> Dict[str, float]:
        """Return current high-level tribal priorities.

        Provides a stable structure for tests expecting seasonal modulation.
        Base priorities derive from wellbeing metrics as proxies. Values are 0-1.
        Keys: food_security, expansion, diplomacy, culture, defense.
        """
        wb = self.wellbeing
        priorities = {
            "food_security": wb.get("food_security", 0.5),
            "expansion": (wb.get("organizational_efficiency", 0.5) + wb.get("morale", 0.5)) / 2.0,
            "diplomacy": (wb.get("overall_wellbeing", 0.5) + wb.get("cultural_richness", 0.4))
            / 2.0,
            "culture": wb.get("cultural_richness", 0.4),
            "defense": wb.get("security", 0.5),
        }
        return priorities
        # Seed proto-lexicon if empty
        if not self.cultural_ledger["language"]["lexicon"]:
            core_concepts = [
                "food",
                "danger",
                "tribe",
                "trade",
                "water",
                "hunt",
                "ally",
                "spirit",
            ]
            # initialize phonology inventory & volatility
            self._init_phonology()
            for concept in core_concepts:
                self._add_language_entry(concept, evolution_reason="proto_seed")
        # Ritual schema migration (ensure stacking present)
        try:
            self.ensure_ritual_schema()
        except Exception:
            pass

    def ensure_ritual_schema(self) -> None:
        rituals = self.cultural_ledger.get("rituals_customs", {}).get("rituals", [])
        changed = False
        for r in rituals:
            if "stacking" not in r:
                r["stacking"] = "refresh"
                changed = True
        if changed:
            self.add_tribal_memory("ritual_schema_migrated", {"count": len(rituals)})
            self.logger.debug(
                f"{self.name} ritual schema migrated: stacking default applied to {len(rituals)} rituals"
            )

    # ===== Cultural Ledger Internal Helpers =====
    def _recalculate_value_priority(self) -> None:
        principles = self.cultural_ledger["values"]["principles"]
        ordered = sorted(principles.items(), key=lambda x: x[1], reverse=True)
        self.cultural_ledger["values"]["priority_order"] = [k for k, _ in ordered]

    def _add_language_entry(
        self,
        concept: str,
        word: Optional[str] = None,
        evolution_reason: str = "initial",
    ):
        lexicon = self.cultural_ledger["language"]["lexicon"]
        if word is None:
            word = self._generate_lexical_root(concept)
        previous = lexicon.get(concept)
        lexicon[concept] = word
        # initialize usage counter
        usage = self.cultural_ledger["language"].setdefault("usage", {})
        usage.setdefault(concept, 0)
        # etymology chain separate from events for quick lineage traversal
        ety = self.cultural_ledger["language"].setdefault("etymology", {})
        if concept not in ety:
            ety[concept] = []
        ety[concept].append(
            {
                "form": word,
                "previous": previous,
                "reason": evolution_reason,
                "sequence": len(ety[concept]),
            }
        )
        self.cultural_ledger["language"]["evolution_events"].append(
            {
                "concept": concept,
                "new_word": word,
                "previous": previous,
                "reason": evolution_reason,
                "turn_index": len(self.cultural_ledger["language"]["evolution_events"]),
            }
        )

    # ===== Public Cultural Ledger API =====
    def add_ritual(
        self,
        name: str,
        purpose: str,
        seasonal: Optional[str] = None,
        effects: Optional[Dict[str, float]] = None,
        stacking: str = "refresh",
        duration: Optional[int] = None,
    ):
        # stacking: refresh|stack|ignore; duration optional default if provided
        ritual = {
            "name": name,
            "purpose": purpose,
            "seasonal": seasonal,
            "effects": effects or {},
            "stacking": stacking,
        }
        if duration is not None:
            ritual["duration"] = duration
        self.cultural_ledger["rituals_customs"]["rituals"].append(ritual)
        self.add_tribal_memory("ritual_added", ritual)
        self.logger.debug(f"Ritual added to {self.name}: {name}")

    def add_custom(self, custom_name: str) -> None:
        if custom_name not in self.cultural_ledger["rituals_customs"]["customs"]:
            self.cultural_ledger["rituals_customs"]["customs"].append(custom_name)
            self.add_tribal_memory("custom_adopted", {"custom": custom_name})

    # ===== Ritual & Custom Effect Helpers =====
    def activate_ritual(self, ritual: Dict[str, Any], current_day: int, duration: int = 30) -> None:
        stacking = ritual.get("stacking", "refresh")  # refresh | stack | ignore
        name = ritual.get("name")
        effects = ritual.get("effects", {})
        # Check existing entries with same name
        existing_indexes = [
            i for i, r in enumerate(self.active_ritual_effects) if r.get("name") == name
        ]
        if existing_indexes:
            if stacking == "ignore":
                return
            if stacking == "refresh":
                # Refresh first occurrence expiry & effects
                idx = existing_indexes[0]
                self.active_ritual_effects[idx]["started_day"] = current_day
                self.active_ritual_effects[idx]["expires_day"] = current_day + max(1, duration)
                # Merge/override effects
                try:
                    self.active_ritual_effects[idx]["effects"].update(effects)
                except Exception:
                    self.active_ritual_effects[idx]["effects"] = effects
                self.add_tribal_memory("ritual_refreshed", {"name": name, "duration": duration})
                return
            if stacking == "stack":
                # Allow multiple stacked instances (fall through to append)
                pass
        entry = {
            "name": name,
            "effects": effects,
            "started_day": current_day,
            "expires_day": current_day + max(1, duration),
        }
        self.active_ritual_effects.append(entry)
        self.add_tribal_memory(
            "ritual_started",
            {"name": entry["name"], "duration": duration, "stacking": stacking},
        )

    def cleanup_ritual_effects(self, current_day: int) -> None:
        remaining = []
        for eff in self.active_ritual_effects:
            if current_day >= eff.get("expires_day", current_day):
                self.add_tribal_memory("ritual_expired", {"name": eff.get("name")})
            else:
                remaining.append(eff)
        self.active_ritual_effects = remaining

    def aggregate_effect_modifier(self, key: str) -> float:
        total = 0.0
        for eff in self.active_ritual_effects:
            val = eff.get("effects", {}).get(key)
            if isinstance(val, (int, float)):
                total += val
        return total

    def is_diplomacy_blocked(self, current_day: int) -> bool:
        mourning_until = self.custom_state.get("mourning_until")
        return isinstance(mourning_until, int) and current_day <= mourning_until

    def enforce_mourning(self, current_day: int, duration: int = 7) -> None:
        self.custom_state["mourning_until"] = current_day + duration
        self.add_tribal_memory("mourning_started", {"until": self.custom_state["mourning_until"]})

    def gift_giving_bonus(self) -> float:
        base = 0.0
        if "Gift-Giving" in self.cultural_ledger["rituals_customs"]["customs"]:
            base += 0.15
        base += self.aggregate_effect_modifier("gift_bias")
        return base

    # ===== Generational Transmission & Cultural Mutation =====
    def snapshot_culture(self) -> Dict[str, Any]:
        try:
            return {
                "values": {
                    "principles": dict(
                        self.cultural_ledger.get("values", {}).get("principles", {})
                    ),
                    "priority_order": list(
                        self.cultural_ledger.get("values", {}).get("priority_order", [])
                    ),
                },
                "rituals_customs": {
                    "rituals": [
                        dict(r)
                        for r in self.cultural_ledger.get("rituals_customs", {}).get("rituals", [])
                    ],
                    "customs": list(
                        self.cultural_ledger.get("rituals_customs", {}).get("customs", [])
                    ),
                },
                "language": {
                    "lexicon_size": len(
                        self.cultural_ledger.get("language", {}).get("lexicon", {})
                    ),
                    "prestige": self.cultural_ledger.get("language", {}).get("prestige", 0.0),
                },
                "timestamp": self.custom_state.get("last_snapshot_day"),
            }
        except Exception:
            return {}

    def cultural_mutation(self, event_type: str, current_day: int) -> None:
        try:
            values = self.cultural_ledger.get("values", {}).get("principles", {})
            if not values:
                return
            shift_map = {
                "plague_survived": {"Survival": +0.08, "Honor": -0.04},
                "betrayal": {"Honor": -0.07, "Prosperity": +0.03},
                "famine_long": {"Prosperity": +0.10, "Honor": -0.03},
                "devastating_war": {"Survival": +0.12, "Honor": -0.08},
            }
            adjustments = shift_map.get(event_type)
            if not adjustments:
                return
            applied = {}
            for k, delta in adjustments.items():
                if k in values:
                    before = values[k]
                    after = round(min(1.0, max(0.0, before + delta)), 3)
                    values[k] = after
                    applied[k] = {"before": before, "after": after}
            self._recalculate_value_priority()
            commemorated = None
            if random.random() < 0.4:
                ritual_name = {
                    "plague_survived": "Renewal Vigil",
                    "betrayal": "Oath Binding",
                    "famine_long": "Harvest Appeasement",
                    "devastating_war": "Remembrance Circle",
                }.get(event_type, f"Commemoration {event_type}")
                self.add_ritual(
                    ritual_name,
                    purpose=f"commemorate_{event_type}",
                    effects={"morale": 0.05},
                    stacking="ignore",
                    duration=25,
                )
                commemorated = ritual_name
            self.add_tribal_memory(
                "cultural_mutation",
                {
                    "event": event_type,
                    "day": current_day,
                    "value_shifts": applied,
                    "ritual_added": commemorated,
                },
            )
            if applied:
                self.logger.info(
                    f"[CulturalMutation] {self.name} mutated after {event_type}: shifts={applied}; ritual={commemorated}"
                )
        except Exception as e:
            self.logger.debug(f"Cultural mutation failed: {e}")

    def add_value(self, principle: str, weight: float) -> None:
        weight = max(0.0, min(1.0, weight))
        self.cultural_ledger["values"]["principles"][principle] = weight
        self._recalculate_value_priority()
        self.add_tribal_memory("value_added", {"principle": principle, "weight": weight})

    def adjust_value(self, principle: str, delta: float, reason: str = "") -> None:
        if principle in self.cultural_ledger["values"]["principles"]:
            new_weight = max(
                0.0,
                min(1.0, self.cultural_ledger["values"]["principles"][principle] + delta),
            )
            self.cultural_ledger["values"]["principles"][principle] = round(new_weight, 2)
            self._recalculate_value_priority()
            self.add_tribal_memory(
                "value_shifted",
                {"principle": principle, "delta": delta, "reason": reason},
            )

    def record_significant_event(
        self, summary: str, category: str, impact: Optional[Dict[str, float]] = None
    ):
        event_entry = {
            "summary": summary,
            "category": category,
            "impact": impact or {},
            "sequence": len(self.cultural_ledger["history_myths"]["significant_events"]) + 1,
        }
        self.cultural_ledger["history_myths"]["significant_events"].append(event_entry)
        self.add_tribal_memory("historic_event", event_entry)

    def formalize_myth(self) -> None:
        events = self.cultural_ledger["history_myths"]["significant_events"][-3:]
        if not events:
            return None
        myth = f"Legend of {self.name}: " + ", then ".join(e["summary"] for e in events)
        self.cultural_ledger["history_myths"]["myths"].append(myth)
        self.add_tribal_memory("myth_formalized", {"myth": myth})
        return myth

    def evolve_language(self, concept: str, reason: str = "cultural_shift") -> None:
        # If concept exists perform a sound shift; else create new entry
        lex = self.cultural_ledger["language"]["lexicon"]
        usage = self.cultural_ledger["language"].setdefault("usage", {})
        if concept in lex:
            old = lex[concept]
            shifted = self._sound_shift(old)
            if shifted != old:
                self._add_language_entry(concept, word=shifted, evolution_reason=reason + "_shift")
                self.add_tribal_memory(
                    "language_shift",
                    {"concept": concept, "from": old, "to": shifted, "reason": reason},
                )
                usage[concept] = usage.get(concept, 0) + 1
        else:
            self._add_language_entry(concept, evolution_reason=reason + "_new")
            self.add_tribal_memory("language_new", {"concept": concept, "reason": reason})
            usage[concept] = usage.get(concept, 0) + 1

    def get_value_priority(self) -> List[str]:
        return self.cultural_ledger["values"].get("priority_order", []).copy()

    def summarize_culture(self) -> Dict[str, Any]:
        cl = self.cultural_ledger
        return {
            "top_values": self.get_value_priority()[:3],
            "ritual_count": len(cl["rituals_customs"]["rituals"]),
            "customs": cl["rituals_customs"]["customs"][:5],
            "myth_count": len(cl["history_myths"]["myths"]),
            "lexicon_size": len(cl["language"]["lexicon"]),
        }

    def cultural_status_report(self) -> Dict[str, Any]:
        """Extended cultural snapshot for reporting/logging purposes.

        Returns lightweight dict (safe for frequent logging) including:
        - top_values: up to 3 current leading cultural values
        - value_scores: compact mapping of those values to scores
        - lexicon_size & prestige (language diffusion potential)
        - ritual_count and active_rituals (names only, max 3)
        - last_mutations: recent cultural mutation events (up to 3) derived from tribal_memory
        - streaks: famine/plague streak counters if present
        - commemorative_rituals: count of auto-added commemoration rituals (heuristic by purpose prefix)
        """
        try:
            ledger = self.cultural_ledger
            values = ledger.get("values", {}).get("principles", {})
            order = self.get_value_priority()[:3]
            value_scores = {k: values.get(k) for k in order}
            lang = ledger.get("language", {})
            prestige = lang.get("prestige", 0.0)
            rituals = ledger.get("rituals_customs", {}).get("rituals", [])
            commemorations = [
                r
                for r in rituals
                if isinstance(r, dict) and str(r.get("purpose", "")).startswith("commemorate_")
            ]
            active = []
            for eff in self.active_ritual_effects[:3]:
                nm = eff.get("name")
                if nm:
                    active.append(nm)
            # Extract last few mutation memories
            muts = [m for m in self.tribal_memory if m.get("event") == "cultural_mutation"]
            last_mutations = []
            for m in muts[-3:]:
                last_mutations.append(
                    {
                        "event": m.get("event"),
                        "trigger": m.get("event"),
                        "day": m.get("day"),
                        "values": list(m.get("value_shifts", {}).keys()),
                    }
                )
            cs = self.custom_state
            report = {
                "tribe": self.name,
                "top_values": order,
                "value_scores": value_scores,
                "lexicon_size": len(lang.get("lexicon", {})),
                "prestige": round(prestige, 3),
                "ritual_count": len(rituals),
                "active_rituals": active,
                "commemorative_rituals": len(commemorations),
                "last_mutations": last_mutations,
                "streaks": {k: cs.get(k) for k in ["famine_streak", "plague_streak"] if k in cs},
            }
            return report
        except Exception:
            return {"tribe": self.name, "error": "cultural_status_failed"}

    def _generate_initial_culture(self) -> None:
        """Generate initial cultural elements for the tribe"""
        possible_totems = [
            "fire",
            "sky",
            "earth",
            "water",
            "forest",
            "mountain",
            "river",
            "wind",
        ]
        self.culture["totems"] = random.sample(possible_totems, random.randint(1, 3))

        possible_traditions = [
            "storytelling around fire",
            "ritual hunting dances",
            "seasonal migration patterns",
            "communal meals",
            "shamanic healing ceremonies",
        ]
        self.culture["traditions"] = random.sample(possible_traditions, random.randint(1, 2))

        # Generate initial tribal stories
        self.culture["stories"] = [
            f"The tale of how {self.name} was blessed by the {random.choice(self.culture['totems'])} spirit"
        ]

        # Generate cultural quirks
        music_styles = ["drumming", "chanting", "flute", "rattles", "throat_singing"]
        self.cultural_quirks["music_style"] = random.choice(music_styles)

        marking_patterns = [
            "facial stripes",
            "body spirals",
            "animal tattoos",
            "geometric patterns",
            "clan symbols",
        ]
        self.cultural_quirks["body_markings"] = random.sample(
            marking_patterns, random.randint(1, 3)
        )

        ceremonial_items = [
            "feather headdresses",
            "bone necklaces",
            "hide robes",
            "totem masks",
            "ceremonial spears",
        ]
        self.cultural_quirks["ceremonial_dress"] = random.sample(
            ceremonial_items, random.randint(1, 2)
        )

        # Generate spiritual beliefs
        creation_myths = [
            f"The great {random.choice(self.culture['totems'])} created our people from the sacred {random.choice(['river', 'mountain', 'forest', 'cave'])}",
            f"Our ancestors emerged from the underworld guided by {random.choice(self.culture['totems'])} spirits",
            f"The sky people descended and taught us the ways of the {random.choice(self.culture['totems'])}",
        ]
        self.spiritual_beliefs["creation_myth"] = random.choice(creation_myths)

        spirit_animals = [
            "wolf",
            "eagle",
            "bear",
            "raven",
            "snake",
            "stag",
            "owl",
            "salmon",
        ]
        self.spiritual_beliefs["spirit_guides"] = random.sample(
            spirit_animals, random.randint(2, 4)
        )

        # Economic specialization
        specializations = [
            "hunting",
            "gathering",
            "crafting",
            "fishing",
            "trading",
            "farming",
        ]
        self.economic_specialization = random.choice(specializations)

    def add_member(self, npc_id: str, role: Optional[TribalRole] = None) -> None:
        """Add an NPC to the tribe"""
        self.member_ids.add(npc_id)
        if role:
            self.social_roles[npc_id] = role
            # If assigning leader role and no leader exists, set as leader
            if role == TribalRole.LEADER and not self.leader_id:
                self.leader_id = npc_id
        elif not self.leader_id:
            # First member becomes leader
            self.leader_id = npc_id
            self.social_roles[npc_id] = TribalRole.LEADER
        else:
            # Assign random role
            self.social_roles[npc_id] = random.choice(list(TribalRole))

        self.logger.info(
            f"NPC {npc_id} joined tribe {self.name} as {self.social_roles[npc_id].value}"
        )

    def remove_member(self, npc_id: str) -> None:
        """Remove an NPC from the tribe"""
        if npc_id in self.member_ids:
            self.member_ids.remove(npc_id)
            if npc_id in self.social_roles:
                del self.social_roles[npc_id]
            if npc_id == self.leader_id:
                self._elect_new_leader()
            self.logger.info(f"NPC {npc_id} left tribe {self.name}")

    def _elect_new_leader(self) -> None:
        """Elect a new leader when current leader leaves"""
        if self.member_ids:
            self.leader_id = random.choice(list(self.member_ids))
            self.social_roles[self.leader_id] = TribalRole.LEADER
            self.logger.info(f"New leader elected: {self.leader_id}")

    def claim_territory(self, coordinates: Tuple[int, int]) -> None:
        """Claim territory for the tribe"""
        self.territory.add(coordinates)
        self.logger.debug(f"Tribe {self.name} claimed territory at {coordinates}")

    def build_structure(self, structure_type: str, location: Tuple[int, int]) -> None:
        """Build a tribal structure"""
        if structure_type in self.structures:
            self.structures[structure_type] += 1
            if not self.camp_location:
                self.camp_location = location
            self.logger.info(f"Tribe {self.name} built {structure_type} at {location}")

    def add_shared_resource(self, resource_type: str, amount: float) -> None:
        """Add resources to tribal pool"""
        if resource_type in self.shared_resources:
            self.shared_resources[resource_type] += amount
            self.logger.debug(f"Tribe {self.name} gained {amount} {resource_type}")

    def take_shared_resource(self, resource_type: str, amount: float) -> float:
        """Take resources from tribal pool"""
        if resource_type in self.shared_resources:
            available = self.shared_resources[resource_type]
            taken = min(amount, available)
            self.shared_resources[resource_type] -= taken
            return taken
        return 0.0

    def form_alliance(self, other_tribe_name: str) -> None:
        """Form alliance with another tribe"""
        self.alliances.add(other_tribe_name)
        if other_tribe_name in self.rivalries:
            self.rivalries.remove(other_tribe_name)
        self.logger.info(f"Tribe {self.name} formed alliance with {other_tribe_name}")

    def declare_rivalry(self, other_tribe_name: str) -> None:
        """Declare rivalry with another tribe"""
        self.rivalries.add(other_tribe_name)
        if other_tribe_name in self.alliances:
            self.alliances.remove(other_tribe_name)
        self.logger.info(f"Tribe {self.name} declared rivalry with {other_tribe_name}")

    def negotiate_truce(self, other_tribe_name: str, duration: int = 10) -> None:
        """Negotiate truce with another tribe"""
        self.truces[other_tribe_name] = duration
        if other_tribe_name in self.rivalries:
            self.rivalries.remove(other_tribe_name)
        self.logger.info(
            f"Tribe {self.name} negotiated {duration}-turn truce with {other_tribe_name}"
        )

    def get_tribal_language(self, word: str) -> str:
        """Get tribal dialect variant of a word"""
        if word in self.dialect:
            # increment usage if mapped to concept
            usage = self.cultural_ledger["language"].get("usage", {})
            if word in self.cultural_ledger["language"]["lexicon"]:
                usage[word] = usage.get(word, 0) + 1
            return self.dialect[word]

        # Generate tribal variant
        tribal_word = self._generate_tribal_word(word)
        self.dialect[word] = tribal_word
        return tribal_word

    def _init_phonology(self):
        ph = self.cultural_ledger["language"]["phonology"]
        if ph:
            return
        consonant_pools = [
            list("ptkmnslr"),
            list("kgndrsthv"),
            list("bdfglmnprst"),
        ]
        vowel_pools = [
            list("aeiou"),
            list("aeiouy"),
            list("aeio"),
            list("eaiou"),
        ]  # slight ordering differences
        templates_choices = [
            ["CV", "CVC", "CVV"],
            ["CV", "VCV", "CVC", "CVVC"],
            ["CV", "CVC", "CVC", "CVCC"],
        ]
        ph["consonants"] = random.choice(consonant_pools)
        ph["vowels"] = random.choice(vowel_pools)
        ph["templates"] = random.choice(templates_choices)
        ph["affixes"] = {"abstract": random.choice(["-un", "-ar", "-esh", "-or"])}
        self.cultural_ledger["language"]["volatility"] = round(random.uniform(0.2, 0.7), 2)

    def _generate_lexical_root(self, concept: str) -> str:
        # Check if LLM lexicon generation is enabled
        if os.getenv("SANDBOX_LLM_LEXICON", "false").lower() == "true":
            try:
                from gemini_narrative import generate_lexical_root

                # Get tribal culture description for LLM context
                culture_desc = self._get_tribe_culture_description()
                # Get phonological hints from existing phonology
                ph = self.cultural_ledger["language"].get("phonology", {})
                phonological_hints = ""
                if ph:
                    cons = ph.get("consonants", [])
                    vows = ph.get("vowels", [])
                    if cons and vows:
                        phonological_hints = (
                            f"consonants: {','.join(cons[:3])}, vowels: {','.join(vows[:3])}"
                        )

                llm_word = generate_lexical_root(concept, culture_desc, phonological_hints)
                if llm_word and not llm_word.startswith("[LLM"):
                    return self._repair_phonotactics(llm_word)
            except ImportError:
                pass  # Fall back to algorithmic generation

        # Original algorithmic generation
        ph = self.cultural_ledger["language"].get("phonology", {})
        if not ph:
            self._init_phonology()
            ph = self.cultural_ledger["language"]["phonology"]
        tmpl = random.choice(ph.get("templates", ["CV", "CVC"]))
        cons = ph.get("consonants", ["k", "t", "m", "n", "s", "r"])
        vows = ph.get("vowels", ["a", "e", "i", "o", "u"])
        out = []
        i = 0
        while i < len(tmpl):
            ch = tmpl[i]
            if ch == "C":
                out.append(random.choice(cons))
            elif ch == "V":
                out.append(random.choice(vows))
            i += 1
        form = "".join(out)
        # small chance to append abstract affix for non-core concepts
        if (
            concept
            not in [
                "food",
                "danger",
                "tribe",
                "trade",
                "water",
                "hunt",
                "ally",
                "spirit",
            ]
            and random.random() < 0.2
        ):
            form += ph.get("affixes", {}).get("abstract", "")
        return self._repair_phonotactics(form)

    def _get_tribe_culture_description(self) -> str:
        """Generate a description of the tribe's culture for LLM context."""
        culture = self.cultural_ledger.get("cultural_ledger", {}).get("culture", {})
        wellbeing = self.cultural_ledger.get("cultural_ledger", {}).get("wellbeing", {})

        elements = []
        if culture.get("totems"):
            elements.append(f"totems: {', '.join(culture['totems'][:2])}")
        if culture.get("traditions"):
            elements.append(f"traditions: {', '.join(culture['traditions'][:2])}")
        if culture.get("stories"):
            elements.append(f"stories: {len(culture['stories'])} tribal myths")
        if self.economic_specialization:
            elements.append(f"specializes in {self.economic_specialization}")
        if wellbeing.get("cultural_richness", 0) > 0.7:
            elements.append("highly culturally developed")
        elif wellbeing.get("cultural_richness", 0) < 0.3:
            elements.append("culturally developing")

        location_desc = f"located at {self.camp_location}" if self.camp_location else ""
        return f"Tribal culture with {', '.join(elements)} {location_desc}".strip()

    def _sound_shift(self, word: str) -> str:
        """Apply a light probabilistic phonetic mutation to a word"""
        if not word:
            return word
        transformations = [
            ("k", "g"),
            ("g", "k"),
            ("t", "d"),
            ("d", "t"),
            ("p", "b"),
            ("b", "p"),
            ("sh", "s"),
            ("s", "sh"),
            ("a", "e"),
            ("e", "a"),
            ("i", "u"),
            ("u", "i"),
        ]
        vol = self.cultural_ledger["language"].get("volatility", 0.4)
        base_chance = 0.25 + vol * 0.35  # range ~0.25-0.60
        if random.random() < base_chance:
            src, tgt = random.choice(transformations)
            if src in word:
                mutated = word.replace(src, tgt, 1)
                return self._repair_phonotactics(mutated)
        return self._repair_phonotactics(word)

    def recent_linguistic_changes(self, limit: int = 5) -> list:
        events = self.cultural_ledger["language"]["evolution_events"]
        return events[-limit:]

    def language_report(self) -> Dict[str, Any]:
        lang = self.cultural_ledger.get("language", {})
        lex = lang.get("lexicon", {})
        usage = lang.get("usage", {})
        phon = lang.get("phonology", {})
        volatility = lang.get("volatility")
        alternates = lang.get("alternates", {})
        obsoleted = lang.get("obsolete", {})
        morph = lang.get("morphology", {})
        top_usage = sorted(usage.items(), key=lambda x: x[1], reverse=True)[:5]
        conv = lang.get("convergence", {}).get("partners", {})
        best_conv = None
        if conv:
            try:
                best_partner, best_metrics = max(
                    conv.items(), key=lambda kv: kv[1].get("concept_overlap", 0)
                )
                best_conv = {
                    "partner": best_partner,
                    "concept_overlap": best_metrics.get("concept_overlap"),
                    "avg_form_similarity": best_metrics.get("avg_form_similarity"),
                    "divergence": best_metrics.get("divergence"),
                }
            except Exception:
                best_conv = None
        return {
            "tribe": self.name,
            "lexicon_size": len(lex),
            "volatility": volatility,
            "templates": phon.get("templates") if phon else None,
            "consonant_count": len(phon.get("consonants", [])) if phon else 0,
            "vowel_count": len(phon.get("vowels", [])) if phon else 0,
            "top_usage": top_usage,
            "recent_events": self.recent_linguistic_changes(5),
            "alternate_count": len(alternates),
            "obsolete_count": len(obsoleted),
            "productive_affixes": [
                a
                for a, stats in morph.get("affixes", {}).items()
                if stats.get("productivity", 0) >= morph.get("productivity_threshold", 3)
            ],
            "derived_count": len(morph.get("derived", {})),
            "best_convergence_partner": best_conv,
        }

    def propose_synonym(self, concept: str, current_day: int = 0):
        lang = self.cultural_ledger.get("language", {})
        lex = lang.get("lexicon", {})
        if concept not in lex:
            return False
        alternates = lang.setdefault("alternates", {})
        if concept in alternates:  # already pending
            return False
        candidate = self._generate_lexical_root(concept)
        if candidate == lex[concept]:
            # try one more time
            candidate = self._sound_shift(candidate)
            if candidate == lex[concept]:
                return False
        alternates[concept] = {
            "candidate": candidate,
            "introduced_day": current_day,
            "status": "pending",
        }
        self.add_tribal_memory("synonym_proposed", {"concept": concept, "candidate": candidate})
        return True

    def evaluate_synonym(self, concept: str, current_day: int = 0):
        lang = self.cultural_ledger.get("language", {})
        alternates = lang.get("alternates", {})
        if concept not in alternates:
            return False
        entry = alternates[concept]
        if entry.get("status") != "pending":
            return False
        # Simple adoption probability influenced by volatility
        vol = lang.get("volatility", 0.4)
        adopt_prob = 0.45 + (vol - 0.5) * 0.3  # ~0.3-0.6 range typical
        if random.random() < adopt_prob:
            # adopt candidate as new form
            candidate = entry["candidate"]
            self._add_language_entry(concept, word=candidate, evolution_reason="synonym_adopt")
            entry["status"] = "adopted"
            self.add_tribal_memory("synonym_adopted", {"concept": concept, "form": candidate})
        else:
            entry["status"] = "discarded"
            self.add_tribal_memory(
                "synonym_discarded",
                {"concept": concept, "candidate": entry["candidate"]},
            )
        # Remove resolved alternates to keep structure light
        if concept in alternates:
            del alternates[concept]
        return True

    # === Obsolescence & Decay ===
    def decay_usage(self, decay_factor: float = 0.05):
        """Apply small decay to concept usage to allow obsolescence emergence."""
        lang = self.cultural_ledger.get("language", {})
        usage = lang.get("usage", {})
        for concept, count in list(usage.items()):
            if count <= 0:
                continue
            # Core concepts resist decay more strongly
            resistance = (
                0.5
                if concept
                in [
                    "food",
                    "danger",
                    "tribe",
                    "trade",
                    "water",
                    "hunt",
                    "ally",
                    "spirit",
                ]
                else 1.0
            )
            dec = max(0.0, count * decay_factor * resistance)
            usage[concept] = max(0, count - dec)

    def prune_obsolete(self, threshold: float = 0.8, min_age: int = 10):
        """Mark rarely used non-core concepts as obsolete; keep lineage but remove from active lexicon.
        threshold: absolute usage below which a word can be obsoleted (after scaling).
        min_age: minimum number of evolution events before pruning to avoid early removal.
        """
        lang = self.cultural_ledger.get("language", {})
        lex = lang.get("lexicon", {})
        usage = lang.get("usage", {})
        obsolete_store = lang.setdefault("obsolete", {})
        events_len = len(lang.get("evolution_events", []))
        if events_len < min_age:
            return 0
        removed = 0
        for concept, count in list(usage.items()):
            if concept in [
                "food",
                "danger",
                "tribe",
                "trade",
                "water",
                "hunt",
                "ally",
                "spirit",
            ]:
                continue
            if count < threshold and concept in lex:
                obsolete_store[concept] = {
                    "form": lex[concept],
                    "final_usage": count,
                    "retired_event_index": events_len,
                }
                del lex[concept]
                removed += 1
                self.add_tribal_memory("word_obsoleted", {"concept": concept, "usage": count})
        return removed

    # === Morphology Tracking ===
    def _init_morphology(self):
        lang = self.cultural_ledger.get("language", {})
        morph = lang.setdefault("morphology", {})
        morph.setdefault("affixes", {})  # affix -> {'count': int, 'productivity': int}
        morph.setdefault(
            "derived", {}
        )  # derived_concept -> {'base': base, 'affix': affix, 'form': str}
        morph.setdefault("productivity_threshold", 3)
        # Seed with phonology abstract affix if present
        aff = lang.get("phonology", {}).get("affixes", {})
        for a in aff.values():
            morph["affixes"].setdefault(a, {"count": 0, "productivity": 0})

    def derive_word(self, base_concept: str, semantic_shift: str, affix: Optional[str] = None):
        """Create a derived lexical item from a base concept using (or discovering) an affix.
        semantic_shift: short label for new concept (e.g., 'agent','tool','place').
        affix: optional explicit affix; if None, generate or reuse productive one.
        """
        lang = self.cultural_ledger.get("language", {})
        lex = lang.get("lexicon", {})
        if base_concept not in lex:
            return None
        if "morphology" not in lang:
            self._init_morphology()
        morph = lang["morphology"]
        affixes = morph["affixes"]

        base_form = lex[base_concept]
        derived_concept = (
            f"{base_concept}_{semantic_shift}" if semantic_shift else f"{base_concept}_{affix}"
        )
        if derived_concept in lex:
            return None

        # Try LLM-enhanced derivation first if enabled
        derived_form = None
        if os.getenv("SANDBOX_LLM_LEXICON", "false").lower() == "true":
            try:
                from gemini_narrative import generate_semantic_derivation

                culture_desc = self._get_tribe_culture_description()
                llm_derived = generate_semantic_derivation(
                    base_form, base_concept, semantic_shift, culture_desc
                )
                if llm_derived and not llm_derived.startswith("[LLM") and llm_derived != base_form:
                    derived_form = self._repair_phonotactics(llm_derived)
                    # Use a placeholder affix for LLM derivations
                    affix = semantic_shift[:2] if not affix else affix
            except ImportError:
                pass  # Fall back to algorithmic derivation

        # Algorithmic derivation if LLM failed or disabled
        if derived_form is None:
            # Choose existing productive affix or create new
            productive = [
                a
                for a, stats in affixes.items()
                if stats.get("productivity", 0) >= morph.get("productivity_threshold", 3)
            ]
            if not affix:
                if productive and random.random() < 0.7:
                    affix = random.choice(productive)
                else:
                    # generate new light affix from phonology vowels/consonants
                    ph = lang.get("phonology", {})
                    cons = ph.get("consonants", ["k", "t", "m", "n"])
                    vows = ph.get("vowels", ["a", "e", "i", "o"])
                    affix = random.choice(cons) + random.choice(vows)
            affixes.setdefault(affix, {"count": 0, "productivity": 0})
            # Simple derivation: append affix (or if already endswith affix, duplicate not)
            if not base_form.endswith(affix):
                derived_form = base_form + affix
            else:
                derived_form = base_form
            derived_form = self._repair_phonotactics(derived_form)

        self._add_language_entry(
            derived_concept, word=derived_form, evolution_reason="morph_derive"
        )
        usage = lang.setdefault("usage", {})
        usage[derived_concept] = 1
        # Update affix stats
        affixes[affix]["count"] += 1
        affixes[affix]["productivity"] = affixes[affix]["count"]  # simplistic measure for now
        morph["derived"][derived_concept] = {
            "base": base_concept,
            "affix": affix,
            "form": derived_form,
        }
        self.add_tribal_memory(
            "word_derived",
            {"base": base_concept, "derived": derived_concept, "affix": affix},
        )
        return derived_concept

    # === Phonotactic Repair ===
    def _repair_phonotactics(self, form: str) -> str:
        """Apply simple phonotactic constraints: collapse triple consonants, avoid vowel starvation, enforce basic syllable shape."""
        if not form:
            return form
        # Collapse any 3+ consonant clusters to 2 by removing middle consonants
        vowels = set(
            self.cultural_ledger.get("language", {})
            .get("phonology", {})
            .get("vowels", list("aeiou"))
        )
        repaired = []
        cluster = ""
        for ch in form:
            if ch not in vowels:
                cluster += ch
            else:
                if len(cluster) > 2:
                    cluster = cluster[:2]
                repaired.append(cluster)
                cluster = ""
                repaired.append(ch)
        if cluster:
            if len(cluster) > 2:
                cluster = cluster[:2]
            repaired.append(cluster)
        out = "".join(repaired)
        # Ensure word has at least one vowel
        if not any(c in vowels for c in out):
            out += random.choice(list(vowels))
        # Avoid starting with disallowed clusters (e.g., double same consonant)
        if len(out) >= 2 and out[0] == out[1] and out[0] not in vowels:
            out = out[1:]
        return out

    def _generate_tribal_word(self, word: str) -> str:
        """Generate a tribal variant of a word"""
        # Simple tribal word generation
        prefixes = ["ta", "ka", "mu", "ri", "sho", "gra"]
        suffixes = ["ak", "in", "or", "esh", "un", "ar"]

        if random.random() < 0.3:  # 30% chance to modify
            if random.random() < 0.5:
                return random.choice(prefixes) + word
            else:
                return word + random.choice(suffixes)
        return word

    def add_tribal_memory(self, event_type: str, details: Dict[str, Any]):
        """Add event to tribal memory"""
        memory_entry = {
            "turn": len(self.tribal_memory),
            "type": event_type,
            "details": details,
        }
        self.tribal_memory.append(memory_entry)

        # Keep only recent memories
        if len(self.tribal_memory) > 20:
            self.tribal_memory.pop(0)

    def get_tribal_stories(self) -> List[str]:
        """Get tribal stories and legends"""
        return self.culture["stories"].copy()

    def update_wellbeing(self):
        """Update tribal wellbeing based on current state"""
        # Food security based on food reserves vs population
        food_per_person = self.shared_resources.get("food", 0) / max(len(self.member_ids), 1)
        self.wellbeing["food_security"] = min(
            1.0, food_per_person / 10.0
        )  # 10 food units per person ideal

        # Resource availability
        total_resources = sum(self.shared_resources.values())
        resource_per_person = total_resources / max(len(self.member_ids), 1)
        self.wellbeing["resource_availability"] = min(
            1.0, resource_per_person / 20.0
        )  # 20 resource units per person ideal

        # Health (would be affected by shaman contributions, disease, etc.)
        # For now, base it on resource availability and shelter
        # PATCH: Remove shelter as a bottleneck for population sustainability
        shelter_ratio = 1.0  # Always sufficient shelter
        self.wellbeing["health"] = min(
            1.0, (self.wellbeing["resource_availability"] + shelter_ratio) / 2
        )

        # Morale based on culture, alliances, and leadership
        culture_score = len(self.culture["stories"]) * 0.1 + len(self.culture["traditions"]) * 0.2
        alliance_score = len(self.alliances) * 0.1
        leadership_score = 0.3 if self.leader_id else 0.0
        self.wellbeing["morale"] = min(1.0, culture_score + alliance_score + leadership_score)

        # Security based on warriors, territory, and lack of rivalries
        warrior_ratio = sum(
            1 for role in self.social_roles.values() if role == TribalRole.WARRIOR
        ) / max(len(self.member_ids), 1)
        territory_score = len(self.territory) * 0.05
        rivalry_penalty = len(self.rivalries) * 0.1
        self.wellbeing["security"] = min(
            1.0, max(0.0, warrior_ratio + territory_score - rivalry_penalty)
        )

        # Cultural richness
        story_score = len(self.culture["stories"]) * 0.05
        tradition_score = len(self.culture["traditions"]) * 0.1
        totem_score = len(self.culture["totems"]) * 0.2
        self.wellbeing["cultural_richness"] = min(1.0, story_score + tradition_score + totem_score)

        # Organizational efficiency based on role distribution and structures
        role_diversity = len(set(self.social_roles.values())) / 6.0  # 6 total roles
        structure_score = sum(self.structures.values()) * 0.1
        self.wellbeing["organizational_efficiency"] = min(1.0, role_diversity + structure_score)

        # Overall wellbeing as weighted average
        weights = {
            "food_security": 0.25,
            "resource_availability": 0.15,
            "health": 0.2,
            "morale": 0.15,
            "security": 0.15,
            "cultural_richness": 0.05,
            "organizational_efficiency": 0.05,
        }

        self.wellbeing["overall_wellbeing"] = sum(
            self.wellbeing[aspect] * weight for aspect, weight in weights.items()
        )

    def get_wellbeing_report(self) -> Dict[str, float]:
        """Get a detailed wellbeing report"""
        self.update_wellbeing()  # Ensure up to date
        return self.wellbeing.copy()

    def get_wellbeing_score(self) -> float:
        """Get the overall wellbeing score"""
        self.update_wellbeing()
        return self.wellbeing["overall_wellbeing"]

    def to_dict(self) -> Dict[str, Any]:
        """Convert tribe to dictionary for serialization"""
        return {
            "name": self.name,
            "symbol": self.symbol,
            "leader_id": self.leader_id,
            "member_ids": list(self.member_ids),
            "territory": list(self.territory),
            "camp_location": self.camp_location,
            "shared_resources": self.shared_resources,
            "structures": self.structures,
            "culture": self.culture,
            "cultural_quirks": self.cultural_quirks,
            "trade_network": list(self.trade_network),
            "barter_rates": self.barter_rates,
            "economic_specialization": self.economic_specialization,
            "spiritual_beliefs": self.spiritual_beliefs,
            "migration_patterns": self.migration_patterns,
            "seasonal_camps": self.seasonal_camps,
            "alliances": list(self.alliances),
            "rivalries": list(self.rivalries),
            "truces": self.truces,
            "dialect": self.dialect,
            "tribal_memory": self.tribal_memory,
            "resource_sharing": self.resource_sharing,
            "social_roles": {npc_id: role.value for npc_id, role in self.social_roles.items()},
            "cultural_ledger": self.cultural_ledger,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Tribe":
        """Create tribe from dictionary"""
        # Convert lists back to sets
        data["member_ids"] = set(data.get("member_ids", []))
        data["territory"] = set(tuple(coord) for coord in data.get("territory", []))
        data["alliances"] = set(data.get("alliances", []))
        data["rivalries"] = set(data.get("rivalries", []))
        data["trade_network"] = set(data.get("trade_network", []))

        # Convert social roles back to enum
        social_roles = {}
        for npc_id, role_str in data.get("social_roles", {}).items():
            social_roles[npc_id] = TribalRole(role_str)
        data["social_roles"] = social_roles

        tribe = cls(**data)
        try:
            tribe.ensure_ritual_schema()
        except Exception:
            pass
        return tribe

    def perform_ceremony(self, ceremony_type: str) -> Dict:
        """Perform a tribal ceremony"""
        ceremonies = {
            "hunting": {
                "description": f"{self.name} performs hunting ritual with {self.cultural_quirks['music_style']}",
                "benefits": {"morale": 0.1, "hunting_success": 0.15},
            },
            "healing": {
                "description": f"Shaman conducts healing ceremony honoring {random.choice(self.spiritual_beliefs['spirit_guides'])}",
                "benefits": {"health": 0.2, "morale": 0.1},
            },
            "initiation": {
                "description": f"Young warriors receive {random.choice(self.cultural_quirks['body_markings'])} in initiation ceremony",
                "benefits": {"morale": 0.15, "warrior_efficiency": 0.1},
            },
            "thanksgiving": {
                "description": f"Tribe gives thanks to {random.choice(self.culture['totems'])} with communal feast",
                "benefits": {"morale": 0.2, "food_preservation": 0.1},
            },
        }

        if ceremony_type in ceremonies:
            ceremony = ceremonies[ceremony_type]
            self.add_tribal_memory(
                "ceremony_performed",
                {
                    "type": ceremony_type,
                    "description": ceremony["description"],
                    "benefits": ceremony["benefits"],
                },
            )
            return ceremony
        return {}

    def establish_trade_route(self, other_tribe_name: str):
        """Establish trade route with another tribe"""
        self.trade_network.add(other_tribe_name)

        # Set up barter rates
        if other_tribe_name not in self.barter_rates:
            self.barter_rates[other_tribe_name] = {}
            # Initialize with fair exchange rates
            for resource in ["food", "wood", "stone", "herbs"]:
                self.barter_rates[other_tribe_name][resource] = 1.0

        self.add_tribal_memory(
            "trade_route_established",
            {
                "with_tribe": other_tribe_name,
                "specialization": self.economic_specialization,
            },
        )

    def migrate_seasonally(self, season: str, new_location: Tuple[int, int]):
        """Handle seasonal migration"""
        self.seasonal_camps[season] = new_location

        migration_record = {
            "season": season,
            "from_location": self.camp_location,
            "to_location": new_location,
            "reason": f"Following {self.culture['traditions'][0] if self.culture['traditions'] else 'traditional patterns'}",
        }
        self.migration_patterns.append(migration_record)

        self.add_tribal_memory("seasonal_migration", migration_record)

    def develop_prophecy(self) -> str:
        """Develop a tribal prophecy"""
        # Supplement spirit guides from global databank if local list is shallow
        try:
            from databank import get_databank

            if len(self.spiritual_beliefs["spirit_guides"]) < 3:
                extra_guides = get_databank().get_random("spirit_guides", count=2, unique=True)
                for g in extra_guides:
                    if g not in self.spiritual_beliefs["spirit_guides"]:
                        self.spiritual_beliefs["spirit_guides"].append(g)
        except Exception:
            pass
        prophecy_themes = [
            f"A great {random.choice(self.spiritual_beliefs['spirit_guides'])} will guide us to prosperity",
            f"The {random.choice(self.culture['totems'])} will bring abundant {random.choice(['food', 'game', 'water', 'shelter'])}",
            f"Warriors marked with {random.choice(self.cultural_quirks['body_markings'])} will lead us to victory",
            f"The {self.cultural_quirks['music_style']} will summon the spirits of our ancestors",
        ]

        prophecy = random.choice(prophecy_themes)
        self.spiritual_beliefs["prophecies"].append(prophecy)

        self.add_tribal_memory(
            "prophecy_developed",
            {
                "prophecy": prophecy,
                "spiritual_context": f"Received through communion with {random.choice(self.spiritual_beliefs['spirit_guides'])}",
            },
        )

        return prophecy

    def compete_for_resources(self, resource_type: str, competitor_tribe) -> Dict:
        """Compete with another tribe for resources"""
        # Competition based on tribal strengths
        our_strength = len(self.member_ids) * self.get_wellbeing_score()
        their_strength = len(competitor_tribe.member_ids) * competitor_tribe.get_wellbeing_score()

        # Add specialization bonus
        if resource_type == "food" and self.economic_specialization == "hunting":
            our_strength *= 1.2
        elif resource_type == "wood" and self.economic_specialization == "gathering":
            our_strength *= 1.2

        competition_result = {
            "resource_type": resource_type,
            "competitor": competitor_tribe.name,
            "our_strength": our_strength,
            "their_strength": their_strength,
            "outcome": (
                "victory"
                if our_strength > their_strength
                else "defeat" if our_strength < their_strength else "stalemate"
            ),
        }

        self.add_tribal_memory("resource_competition", competition_result)
        return competition_result
