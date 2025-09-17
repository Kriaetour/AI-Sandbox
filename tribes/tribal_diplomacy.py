import random
import logging
from typing import Dict, List, Tuple, Set, Optional, Any
from datetime import datetime
from enum import Enum
from .tribe import Tribe


class DiplomaticEvent(Enum):
    """Types of diplomatic events that can trigger"""

    RAID = "raid"
    GIFTING = "gifting"
    CULTURAL_EXCHANGE = "cultural_exchange"
    RESOURCE_DISPUTE = "resource_dispute"
    TERRITORY_CONFLICT = "territory_conflict"
    ALLIANCE_BETRAYAL = "alliance_betrayal"
    TRADE_DISPUTE = "trade_dispute"
    CEREMONIAL_VISIT = "ceremonial_visit"
    SHARED_HUNTING = "shared_hunting"
    MUTUAL_DEFENSE = "mutual_defense"
    # ===== EXPANDED INTERACTION TYPES =====
    FESTIVAL_INVITATION = "festival_invitation"
    RITUAL_SHARING = "ritual_sharing"
    CEREMONY_PARTICIPATION = "ceremony_participation"
    MINOR_DISAGREEMENT = "minor_disagreement"
    RESOURCE_THEFT = "resource_theft"
    BOUNDARY_DISPUTE = "boundary_dispute"
    HUNTING_GROUNDS_CONFLICT = "hunting_grounds_conflict"
    CULTURAL_OFFENSE = "cultural_offense"
    LEADER_MEDIATION = "leader_mediation"
    AUTHORITY_CHALLENGE = "authority_challenge"


class AllianceType(Enum):
    """Types of alliances that can form"""

    TRADE_ALLIANCE = "trade_alliance"
    DEFENSIVE_PACT = "defensive_pact"
    FULL_ALLIANCE = "full_alliance"
    TEMPORARY_TRUCE = "temporary_truce"
    BLOOD_BROTHERHOOD = "blood_brotherhood"


class TribalDiplomacy:
    """Manages diplomatic relations and interactions between tribes"""

    def __init__(self, tribes: Dict[str, Tribe]):
        self.tribes = tribes
        self.logger = logging.getLogger("TribalDiplomacy")

        # ===== SEASONAL AWARENESS =====
        self.seasonal_context = None  # Will be set by TribalManager

        # Diplomatic state
        self.diplomatic_relations: Dict[Tuple[str, str], Dict] = (
            {}
        )  # (tribe1, tribe2) -> relation data
        self.active_negotiations: List[Dict] = []  # Ongoing diplomatic talks
        # Active trade deals
        self.trade_agreements: Dict[Tuple[str, str], Dict] = {}
        # Tribe -> allied tribes
        self.alliance_networks: Dict[str, Set[str]] = {}
        # Tribe -> {other_tribe: reputation}
        self.reputation_scores: Dict[str, Dict[str, float]] = {}
        # Enhanced diplomatic features
        # Ongoing diplomatic events
        self.active_events: List[Dict] = []
        # Alliance specifics
        self.alliance_details: Dict[Tuple[str, str], Dict] = {}
        # Tribe -> {other_tribe: cultural_influence}
        self.cultural_influences: Dict[str, Dict[str, float]] = {}
        # Historical diplomatic events
        self.event_history: List[Dict] = []

        # Diplomatic history
        self.diplomatic_history: List[Dict] = []
        self.conflict_history: List[Dict] = []

        self._initialize_diplomacy()

    def set_seasonal_context(self, seasonal_context):
        """Set the current seasonal context for diplomatic decision-making"""
        self.seasonal_context = seasonal_context
        if seasonal_context:
            self.logger.debug(
                f"TribalDiplomacy: Updated seasonal context to "
                f"{seasonal_context['season_name']}"
            )

    def _get_seasonal_modifiers(self, season: Optional[int] = None):
        """Get diplomatic behavior modifiers based on current season.

        Backward compatibility: tests may call with an explicit season index.
        If `season` is None, uses `self.seasonal_context`.
        """
        if season is None:
            if not self.seasonal_context:
                return {
                    "trade_likelihood": 1.0,
                    "conflict_likelihood": 1.0,
                    "alliance_likelihood": 1.0,
                }
            season = self.seasonal_context["season"]
        # 0=Spring, 1=Summer, 2=Autumn, 3=Winter

        if season == 3:  # Winter
            return {
                "trade_likelihood": 0.6,  # Reduced trade in winter
                "conflict_likelihood": 0.4,  # Avoid conflicts in harsh season
                "alliance_likelihood": 1.3,  # Alliances more valuable
                "expansion_likelihood": 0.3,  # Limited expansion in winter
            }
        elif season == 2:  # Autumn
            return {
                "trade_likelihood": 1.4,  # High trade for winter preparation
                "conflict_likelihood": 0.8,  # Some conflicts over resources
                "alliance_likelihood": 1.1,  # Form alliances for trade
                "expansion_likelihood": 0.7,  # Limited expansion
            }
        elif season == 0:  # Spring
            return {
                "trade_likelihood": 1.2,  # Good trade opportunities
                "conflict_likelihood": 1.1,  # Territorial disputes
                "alliance_likelihood": 1.2,  # New alliances for expansion
                "expansion_likelihood": 1.4,  # High expansion season
            }
        else:  # Summer (season == 1)
            return {
                "trade_likelihood": 1.3,  # Peak trade season
                "conflict_likelihood": 1.0,  # Normal conflict levels
                "alliance_likelihood": 1.0,  # Normal alliance formation
                "expansion_likelihood": 1.2,  # Good expansion opportunities
            }

    def _initialize_diplomacy(self):
        """Initialize diplomatic relations between all tribe pairs"""
        tribe_names = list(self.tribes.keys())

        for i, tribe1 in enumerate(tribe_names):
            for tribe2 in tribe_names[i + 1 :]:
                # Initialize neutral relations
                key = tuple(sorted([tribe1, tribe2]))
                self.diplomatic_relations[key] = {
                    "trust_level": 0.5,  # 0-1 scale
                    "trade_volume": 0,
                    "conflict_count": 0,
                    "alliance_status": False,
                    "last_interaction": None,
                    "border_tension": 0.0,
                }

                # Initialize reputation scores
                if tribe1 not in self.reputation_scores:
                    self.reputation_scores[tribe1] = {}
                if tribe2 not in self.reputation_scores:
                    self.reputation_scores[tribe2] = {}

                self.reputation_scores[tribe1][tribe2] = 0.5
                self.reputation_scores[tribe2][tribe1] = 0.5

                # Initialize cultural influences
                if tribe1 not in self.cultural_influences:
                    self.cultural_influences[tribe1] = {}
                if tribe2 not in self.cultural_influences:
                    self.cultural_influences[tribe2] = {}

                self.cultural_influences[tribe1][tribe2] = 0.0
                self.cultural_influences[tribe2][tribe1] = 0.0

    def get_diplomatic_standing(self, tribe1: str, tribe2: str) -> str:
        """Convert trust level to diplomatic standing"""
        relation_key = tuple(sorted([tribe1, tribe2]))
        trust_level = self.diplomatic_relations.get(relation_key, {}).get("trust_level", 0.5)
        alliance_status = self.diplomatic_relations.get(relation_key, {}).get(
            "alliance_status", False
        )

        # If allied, use alliance-based standings
        if alliance_status:
            if trust_level >= 0.8:
                return "Trusted Ally"
            elif trust_level >= 0.6:
                return "Reliable Ally"
            else:
                return "Unstable Ally"

        # Non-allied standings based on trust
        if trust_level >= 0.9:
            return "Trusted Friend"
        elif trust_level >= 0.8:
            return "Friendly"
        elif trust_level >= 0.7:
            return "Cordial"
        elif trust_level >= 0.6:
            return "Neutral"
        elif trust_level >= 0.4:
            return "Wary"
        elif trust_level >= 0.3:
            return "Distrusted"
        elif trust_level >= 0.2:
            return "Hostile"
        else:
            return "Bitter Enemy"

    def is_good_standing_for_trade(self, tribe1: str, tribe2: str) -> bool:
        """Check if diplomatic standing is good enough for trade"""
        standing = self.get_diplomatic_standing(tribe1, tribe2)
        good_standings = [
            "Trusted Ally",
            "Reliable Ally",
            "Trusted Friend",
            "Friendly",
            "Cordial",
        ]
        return standing in good_standings

    def is_good_standing_for_alliance(self, tribe1: str, tribe2: str) -> bool:
        """Check if diplomatic standing is good enough for alliance"""
        standing = self.get_diplomatic_standing(tribe1, tribe2)
        good_standings = ["Trusted Friend", "Friendly", "Cordial"]
        return standing in good_standings

    def is_poor_standing(self, tribe1: str, tribe2: str) -> bool:
        """Check if diplomatic standing is poor"""
        standing = self.get_diplomatic_standing(tribe1, tribe2)
        poor_standings = ["Hostile", "Bitter Enemy", "Distrusted"]
        return standing in poor_standings

    # NOTE: Previous simple `_choose_negotiation_type` removed in favor of
    # unified dispatcher defined later; retained logic now lives in
    # `_choose_negotiation_type_simple`.

    # ===== ENHANCED DIPLOMACY FEATURES =====

    def calculate_cultural_influence(self, tribe1: str, tribe2: str) -> float:
        """Calculate cultural influence between tribes"""
        tribe1_obj = self.tribes[tribe1]
        tribe2_obj = self.tribes[tribe2]

        influence_score = 0.0

        # Shared totems increase influence
        shared_totems = set(tribe1_obj.culture.get("totems", [])) & set(
            tribe2_obj.culture.get("totems", [])
        )
        influence_score += len(shared_totems) * 0.1
        # Shared spirit guides increase influence
        shared_spirits = set(tribe1_obj.spiritual_beliefs["spirit_guides"]) & set(
            tribe2_obj.spiritual_beliefs["spirit_guides"]
        )
        influence_score += len(shared_spirits) * 0.15

        # Similar music styles increase influence
        if tribe1_obj.cultural_quirks["music_style"] == tribe2_obj.cultural_quirks["music_style"]:
            influence_score += 0.1

        # Shared traditions increase influence
        shared_traditions = set(tribe1_obj.culture["traditions"]) & set(
            tribe2_obj.culture["traditions"]
        )
        influence_score += len(shared_traditions) * 0.2

        # Economic specialization compatibility
        if tribe1_obj.economic_specialization and tribe2_obj.economic_specialization:
            if tribe1_obj.economic_specialization != tribe2_obj.economic_specialization:
                influence_score += 0.1  # Different specs complement each other

        return min(1.0, influence_score)

    def get_trust_level(self, tribe1: str, tribe2: str) -> float:
        """Get the trust level between two tribes (0.0 to 1.0)"""
        relation_key = tuple(sorted([tribe1, tribe2]))
        return self.diplomatic_relations.get(relation_key, {}).get("trust_level", 0.5)

    def set_trust_level(self, tribe1: str, tribe2: str, trust_level: float):
        """Set the trust level between two tribes (0.0 to 1.0)"""
        relation_key = tuple(sorted([tribe1, tribe2]))
        if relation_key not in self.diplomatic_relations:
            self.diplomatic_relations[relation_key] = {
                "trust_level": 0.5,
                "trade_volume": 0,
                "conflict_count": 0,
                "alliance_status": False,
                "last_interaction": None,
                "border_tension": 0.0,
            }
        self.diplomatic_relations[relation_key]["trust_level"] = max(0.0, min(1.0, trust_level))

    def trigger_diplomatic_event(
        self, event_type: DiplomaticEvent, initiating_tribe: str, target_tribe: str
    ) -> Dict[str, Any]:
        """Trigger a diplomatic event between tribes"""
        event_data = {
            "event_type": event_type.value,
            "initiating_tribe": initiating_tribe,
            "target_tribe": target_tribe,
            "timestamp": datetime.now(),
            "status": "ongoing",
            "duration": random.randint(3, 10),  # Event duration in turns
            "cultural_modifier": self.calculate_cultural_influence(initiating_tribe, target_tribe),
        }

        # Calculate event impact based on type and cultural influence
        impact = self._calculate_event_impact(event_data)

        # Log to communication file
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open("communication_log.txt", "a", encoding="utf-8") as comm_log:
            comm_log.write(
                f"[{timestamp}] 🎭 DIPLOMATIC EVENT: {initiating_tribe} "
                f"initiates {event_type.value} with {target_tribe}\n"
            )
            comm_log.write(
                f"[{timestamp}] 📊 Cultural influence: "
                f"{event_data['cultural_modifier']:.2f}, "
                f"Expected impact: {impact:.2f}\n\n"
            )

        self.active_events.append(event_data)
        self.event_history.append(event_data.copy())

        return event_data

    def _calculate_event_impact(self, event_data: Dict) -> float:
        """Calculate the diplomatic impact of an event"""
        event_type = event_data["event_type"]
        cultural_modifier = event_data["cultural_modifier"]

        base_impacts = {
            DiplomaticEvent.RAID.value: -0.4,
            DiplomaticEvent.GIFTING.value: 0.3,
            DiplomaticEvent.CULTURAL_EXCHANGE.value: 0.2,
            DiplomaticEvent.RESOURCE_DISPUTE.value: -0.2,
            DiplomaticEvent.TERRITORY_CONFLICT.value: -0.3,
            DiplomaticEvent.ALLIANCE_BETRAYAL.value: -0.6,
            DiplomaticEvent.TRADE_DISPUTE.value: -0.25,
            DiplomaticEvent.CEREMONIAL_VISIT.value: 0.15,
            DiplomaticEvent.SHARED_HUNTING.value: 0.25,
            DiplomaticEvent.MUTUAL_DEFENSE.value: 0.35,
        }

        base_impact = base_impacts.get(event_type, 0.0)

        # Cultural influence modifies the impact
        if cultural_modifier > 0.3:
            base_impact *= (
                1.0 + cultural_modifier * 0.5
            )  # Positive cultural influence amplifies positive events
        elif cultural_modifier < 0.1:
            base_impact *= (
                1.0 - (0.1 - cultural_modifier) * 2.0
            )  # Low cultural influence reduces positive events

        return base_impact

    def process_diplomatic_events(self):
        """Process ongoing diplomatic events"""
        events_to_remove = []

        for event in self.active_events:
            event["duration"] -= 1

            if event["duration"] <= 0:
                # Event concludes
                self._resolve_diplomatic_event(event)
                events_to_remove.append(event)

        # Remove completed events
        for event in events_to_remove:
            self.active_events.remove(event)

    def _resolve_diplomatic_event(self, event_data: Dict):
        """Resolve a completed diplomatic event"""
        initiating_tribe = event_data["initiating_tribe"]
        target_tribe = event_data["target_tribe"]
        event_type = event_data["event_type"]

        impact = self._calculate_event_impact(event_data)

        # Apply impact to diplomatic relations
        relation_key = tuple(sorted([initiating_tribe, target_tribe]))
        if relation_key in self.diplomatic_relations:
            self.diplomatic_relations[relation_key]["trust_level"] += impact
            self.diplomatic_relations[relation_key]["trust_level"] = max(
                0.0, min(1.0, self.diplomatic_relations[relation_key]["trust_level"])
            )

        # Update cultural influence
        if (
            initiating_tribe in self.cultural_influences
            and target_tribe in self.cultural_influences[initiating_tribe]
        ):
            self.cultural_influences[initiating_tribe][target_tribe] += impact * 0.1
        if (
            target_tribe in self.cultural_influences
            and initiating_tribe in self.cultural_influences[target_tribe]
        ):
            self.cultural_influences[target_tribe][initiating_tribe] += impact * 0.1

        # Record significant events in faction memory
        self._record_event_in_faction_memory(event_type, initiating_tribe, target_tribe, impact)

        # Special event resolutions
        if event_type == DiplomaticEvent.GIFTING.value and impact > 0:
            self._process_gifting_event(initiating_tribe, target_tribe)
        elif event_type == DiplomaticEvent.ALLIANCE_BETRAYAL.value:
            self._process_betrayal_event(initiating_tribe, target_tribe)
        # ===== EXPANDED EVENT RESOLUTIONS =====
        elif event_type == DiplomaticEvent.FESTIVAL_INVITATION.value:
            self._process_festival_invitation_event(initiating_tribe, target_tribe)
        elif event_type == DiplomaticEvent.RITUAL_SHARING.value:
            self._process_ritual_sharing_event(initiating_tribe, target_tribe)
        elif event_type == DiplomaticEvent.MINOR_DISAGREEMENT.value:
            self._process_minor_disagreement_event(initiating_tribe, target_tribe)
        elif event_type == DiplomaticEvent.RESOURCE_THEFT.value:
            self._process_resource_theft_event(initiating_tribe, target_tribe)
        elif event_type == DiplomaticEvent.BOUNDARY_DISPUTE.value:
            self._process_boundary_dispute_event(initiating_tribe, target_tribe)
        elif event_type == DiplomaticEvent.CULTURAL_OFFENSE.value:
            self._process_cultural_offense_event(initiating_tribe, target_tribe)
        elif event_type == DiplomaticEvent.LEADER_MEDIATION.value:
            self._process_leader_mediation_event(
                initiating_tribe, (target_tribe, initiating_tribe)
            )  # Note: target_tribe is the mediator

        # Log resolution
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open("communication_log.txt", "a", encoding="utf-8") as comm_log:
            comm_log.write(
                f"[{timestamp}] ✅ EVENT RESOLVED: {event_type} between "
                f"{initiating_tribe} and {target_tribe}\n"
            )
            comm_log.write(f"[{timestamp}] 📈 Trust impact: {impact:.2f}\n\n")

        # Apply social consequences to tribal NPCs
        self._apply_social_consequences_from_event(event_data)

    def _apply_social_consequences_from_event(self, event_data) -> None:
        """Apply social consequences to NPCs based on diplomatic events."""
        initiating_tribe = event_data["initiating_tribe"]
        target_tribe = event_data["target_tribe"]
        event_type = event_data["event_type"]
        # Impact is not needed for NPC consequence mapping here

        # Map diplomatic events to social consequences
        consequence_mapping = {
            DiplomaticEvent.GIFTING.value: "gift",
            DiplomaticEvent.ALLIANCE_BETRAYAL.value: "betrayal",
            DiplomaticEvent.RAID.value: "conflict",
            DiplomaticEvent.TRADE_DISPUTE.value: "failed_negotiation",
            DiplomaticEvent.CULTURAL_EXCHANGE.value: "shared_achievement",
            DiplomaticEvent.SHARED_HUNTING.value: "shared_achievement",
            DiplomaticEvent.MUTUAL_DEFENSE.value: "alliance_help",
            DiplomaticEvent.CEREMONIAL_VISIT.value: "successful_negotiation",
            # ===== EXPANDED EVENT MAPPINGS =====
            DiplomaticEvent.FESTIVAL_INVITATION.value: "festival_invitation",
            DiplomaticEvent.RITUAL_SHARING.value: "ritual_sharing",
            DiplomaticEvent.CEREMONY_PARTICIPATION.value: ("ceremony_participation"),
            DiplomaticEvent.MINOR_DISAGREEMENT.value: "minor_disagreement",
            DiplomaticEvent.RESOURCE_THEFT.value: "resource_theft",
            DiplomaticEvent.BOUNDARY_DISPUTE.value: "boundary_dispute",
            DiplomaticEvent.HUNTING_GROUNDS_CONFLICT.value: ("hunting_grounds_conflict"),
            DiplomaticEvent.CULTURAL_OFFENSE.value: "cultural_offense",
            DiplomaticEvent.LEADER_MEDIATION.value: "leader_mediation",
            DiplomaticEvent.AUTHORITY_CHALLENGE.value: "authority_challenge",
        }

        consequence_type = consequence_mapping.get(event_type, "conflict")

        # Get NPCs from both tribes (simplified - get first available NPC)
        initiating_npcs = []
        target_npcs = []

        # This would need to be integrated with the actual NPC system
        # For now, we'll create a placeholder for the concept
        if hasattr(self.tribes[initiating_tribe], "npcs"):
            initiating_npcs = self.tribes[initiating_tribe].npcs[:2]  # Get up to 2 NPCs
        if hasattr(self.tribes[target_tribe], "npcs"):
            target_npcs = self.tribes[target_tribe].npcs[:2]  # Get up to 2 NPCs

        # Apply consequences between representative NPCs
        if initiating_npcs and target_npcs:
            for init_npc in initiating_npcs:
                for target_npc in target_npcs:
                    # Import the consequence application function
                    from ..communication import apply_social_consequence

                    apply_social_consequence(
                        init_npc,
                        target_npc,
                        consequence_type,
                        details=f"{event_type} event",
                        topic="diplomacy",
                    )

    def process_social_memory_decay(self) -> None:
        """Process social memory decay for all tribal NPCs and factions."""
        for tribe_name, tribe in self.tribes.items():
            # Decay NPC memories
            if hasattr(tribe, "npcs"):
                for npc in tribe.npcs:
                    if hasattr(npc, "decay_social_memory"):
                        npc.decay_social_memory()

            # Decay faction memories
            if hasattr(tribe, "faction") and tribe.faction:
                if hasattr(tribe.faction, "decay_faction_memory"):
                    tribe.faction.decay_faction_memory()

        self.logger.info("Processed social memory decay for all tribal NPCs and factions")

    def _record_event_in_faction_memory(
        self, event_type: str, initiating_tribe: str, target_tribe: str, impact: float
    ) -> None:
        """Record significant diplomatic events in faction memories."""
        # Record for initiating tribe
        if (
            hasattr(self.tribes[initiating_tribe], "faction")
            and self.tribes[initiating_tribe].faction
        ):
            faction = self.tribes[initiating_tribe].faction
            if hasattr(faction, "add_memory_event"):
                if event_type in [
                    DiplomaticEvent.ALLIANCE_BETRAYAL.value,
                    DiplomaticEvent.RESOURCE_THEFT.value,
                ]:
                    faction.add_memory_event(
                        "diplomatic_betrayal",
                        f"Committed {event_type} against {target_tribe}",
                        target_tribe,
                        abs(impact),
                    )
                elif event_type == DiplomaticEvent.GIFTING.value and impact > 0:
                    faction.add_memory_event(
                        "diplomatic_gift",
                        f"Gave gift to {target_tribe}",
                        target_tribe,
                        impact,
                    )
                elif event_type in [
                    DiplomaticEvent.CULTURAL_OFFENSE.value,
                    DiplomaticEvent.BOUNDARY_DISPUTE.value,
                ]:
                    faction.add_memory_event(
                        "diplomatic_conflict",
                        f"Engaged in {event_type} with {target_tribe}",
                        target_tribe,
                        abs(impact),
                    )

        # Record for target tribe
        if hasattr(self.tribes[target_tribe], "faction") and self.tribes[target_tribe].faction:
            faction = self.tribes[target_tribe].faction
            if hasattr(faction, "add_memory_event"):
                if event_type in [
                    DiplomaticEvent.ALLIANCE_BETRAYAL.value,
                    DiplomaticEvent.RESOURCE_THEFT.value,
                ]:
                    faction.add_memory_event(
                        "betrayal_suffered",
                        f"Suffered {event_type} from {initiating_tribe}",
                        initiating_tribe,
                        abs(impact),
                    )
                elif event_type == DiplomaticEvent.GIFTING.value and impact > 0:
                    faction.add_memory_event(
                        "gift_received",
                        f"Received gift from {initiating_tribe}",
                        initiating_tribe,
                        impact,
                    )
                elif event_type in [
                    DiplomaticEvent.CULTURAL_OFFENSE.value,
                    DiplomaticEvent.BOUNDARY_DISPUTE.value,
                ]:
                    faction.add_memory_event(
                        "conflict_suffered",
                        f"Suffered {event_type} from {initiating_tribe}",
                        initiating_tribe,
                        abs(impact),
                    )

    def _record_alliance_memory(
        self, tribe1: str, tribe2: str, action: str, alliance_type: str
    ) -> None:
        """Record alliance formations and breakups in faction memories."""
        intensity = 1.0 if action == "formed" else 0.8  # Breakups are slightly

        # Record for tribe1
        if hasattr(self.tribes[tribe1], "faction") and self.tribes[tribe1].faction:
            faction = self.tribes[tribe1].faction
            if hasattr(faction, "add_memory_event"):
                if action == "formed":
                    faction.add_memory_event(
                        "alliance_formed",
                        f"Formed {alliance_type} with {tribe2}",
                        tribe2,
                        intensity,
                    )
                else:
                    faction.add_memory_event(
                        "alliance_broken",
                        f"Ended {alliance_type} with {tribe2}",
                        tribe2,
                        intensity,
                    )

        # Record for tribe2
        if hasattr(self.tribes[tribe2], "faction") and self.tribes[tribe2].faction:
            faction = self.tribes[tribe2].faction
            if hasattr(faction, "add_memory_event"):
                if action == "formed":
                    faction.add_memory_event(
                        "alliance_formed",
                        f"Formed {alliance_type} with {tribe1}",
                        tribe1,
                        intensity,
                    )
                else:
                    faction.add_memory_event(
                        "alliance_broken",
                        f"Ended {alliance_type} with {tribe1}",
                        tribe1,
                        intensity,
                    )

    def _process_gifting_event(self, giver: str, receiver: str) -> None:
        """Process resource gifting between tribes"""
        from markov_behavior import make_markov_choice

        giver_tribe = self.tribes[giver]
        receiver_tribe = self.tribes[receiver]

        # Transfer some resources
        gift_amount = random.uniform(5, 15)

        # Use Markov-based resource selection instead of random choice
        available_resources = list(giver_tribe.shared_resources.keys())
        if available_resources:
            tribe_context = {
                "economic_specialization": getattr(giver_tribe, "economic_specialization", ""),
                "traits": getattr(giver_tribe, "traits", []),
                "resource_abundance": sum(giver_tribe.shared_resources.values())
                / max(1, len(giver_tribe.shared_resources)),
            }
            resource_type = make_markov_choice(
                available_resources, "gifting_resources", "resource", tribe_context
            )
        else:
            resource_type = "food"  # Fallback

        if giver_tribe.shared_resources[resource_type] >= gift_amount:
            giver_tribe.shared_resources[resource_type] -= gift_amount
            receiver_tribe.shared_resources[resource_type] += gift_amount

            # Markov learning: gifting generally improves relations,
            # high success score
            self._record_markov_learning("resource", "gifting_resources", resource_type, 0.8)

            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            with open("communication_log.txt", "a", encoding="utf-8") as comm_log:
                comm_log.write(
                    f"[{timestamp}] 🎁 {giver} gifted {gift_amount:.1f} "
                    f"{resource_type} to {receiver}\n\n"
                )

    def _process_betrayal_event(self, betrayer: str, betrayed: str) -> None:
        """Process alliance betrayal"""
        relation_key = tuple(sorted([betrayer, betrayed]))

        # Break any existing alliance
        if self.diplomatic_relations[relation_key]["alliance_status"]:
            self.diplomatic_relations[relation_key]["alliance_status"] = False
            self.tribes[betrayer].alliances.discard(betrayed)
            self.tribes[betrayed].alliances.discard(betrayer)

            # Add to rivalries
            self.tribes[betrayer].rivalries.add(betrayed)
            self.tribes[betrayed].rivalries.add(betrayer)

            # Markov learning: betrayal generally leads to negative outcomes
            # for long-term relations
            self._record_markov_learning(
                "diplomatic", "alliance_betrayal", "betrayal", 0.2
            )  # Low success score

            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            with open("communication_log.txt", "a", encoding="utf-8") as comm_log:
                comm_log.write(
                    f"[{timestamp}] 💔 ALLIANCE BROKEN: {betrayer} " f"betrayed {betrayed}!\n"
                )
                comm_log.write(f"[{timestamp}] ⚔️ They are now rivals\n\n")

    # ===== EXPANDED EVENT PROCESSING METHODS =====

    def _process_festival_invitation_event(self, host: str, guest: str) -> None:
        """Process tribal festival invitation"""
        from markov_behavior import make_markov_choice

        host_tribe = self.tribes[host]
        # guest_tribe is not used directly; omit variable to avoid lint warning

        # Festival types based on tribal culture - use Markov choice
        festival_types = [
            "harvest",
            "hunting",
            "spirit",
            "coming_of_age",
            "peace",
        ]

        # Build context for cultural decision
        host_context = {
            "cultural_focus": getattr(host_tribe, "cultural_focus", "spiritual"),
            "season": "spring",  # Could be passed in from world context
            "traits": getattr(host_tribe, "traits", []),
            "stability": "stable",  # Could be calculated from recent events
        }

        festival_type = make_markov_choice(
            festival_types, "festival_planning", "cultural", host_context
        )

        # Chance for guest to participate
        participation_chance = random.random()
        if participation_chance > 0.3:  # 70% chance to participate
            # Boost cultural influence
            cultural_boost = random.uniform(0.05, 0.15)
            if host in self.cultural_influences and guest in self.cultural_influences[host]:
                self.cultural_influences[host][guest] += cultural_boost
            if guest in self.cultural_influences and host in self.cultural_influences[guest]:
                self.cultural_influences[guest][host] += cultural_boost

            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            with open("communication_log.txt", "a", encoding="utf-8") as comm_log:
                comm_log.write(
                    f"[{timestamp}] 🎪 {guest} participates in "
                    f"{host}'s {festival_type} festival!\n"
                )
                comm_log.write(
                    f"[{timestamp}] 🌟 Cultural bonds strengthened "
                    f"(+{cultural_boost:.2f} influence)\n\n"
                )
        else:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            with open("communication_log.txt", "a", encoding="utf-8") as comm_log:
                comm_log.write(
                    f"[{timestamp}] 🎪 {guest} declines " f"{host}'s festival invitation\n\n"
                )

    def _process_ritual_sharing_event(self, sharer: str, receiver: str) -> None:
        """Process sharing of cultural rituals between tribes"""
        from markov_behavior import make_markov_choice

        sharer_tribe = self.tribes[sharer]
        receiver_tribe = self.tribes[receiver]

        # Share a cultural element - use Markov choice
        ritual_types = ["ceremony", "tradition", "story", "song", "dance"]

        # Build context for cultural sharing decision
        sharer_context = {
            "cultural_focus": getattr(sharer_tribe, "cultural_focus", "spiritual"),
            "traits": getattr(sharer_tribe, "traits", []),
            "stability": "stable",  # Could be calculated from recent events
            "season": "spring",  # Could be passed in from world context
        }

        ritual_type = make_markov_choice(ritual_types, "ritual_sharing", "cultural", sharer_context)

        # Add to receiver's culture
        if ritual_type == "ceremony":
            receiver_tribe.cultural_quirks["seasonal_rituals"].append(f"learned from {sharer}")
        elif ritual_type == "tradition":
            receiver_tribe.culture["traditions"].append(f"{ritual_type} from {sharer}")
        elif ritual_type == "story":
            receiver_tribe.culture["stories"].append(f"myth from {sharer}")

        # Boost cultural richness
        cultural_boost = random.uniform(0.1, 0.2)
        receiver_tribe.wellbeing["cultural_richness"] = min(
            1.0, receiver_tribe.wellbeing["cultural_richness"] + cultural_boost
        )

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open("communication_log.txt", "a", encoding="utf-8") as comm_log:
            comm_log.write(f"[{timestamp}] 📚 {sharer} shares " f"{ritual_type} with {receiver}\n")
            comm_log.write(
                f"[{timestamp}] 🎭 {receiver}'s cultural richness increased "
                f"(+{cultural_boost:.2f})\n\n"
            )

    def _process_minor_disagreement_event(self, tribe1: str, tribe2: str) -> None:
        """Process minor disagreements between tribes"""
        from markov_behavior import make_markov_choice

        disagreement_topics = [
            "hunting grounds boundaries",
            "resource gathering rights",
            "campfire usage",
            "storytelling traditions",
            "trade route preferences",
        ]

        # Use Markov choice for disagreement topic
        tribe1_obj = self.tribes[tribe1]
        conflict_context = {
            "conflict_intensity": "minor",
            "military_strength": getattr(tribe1_obj, "military_strength", 0.5),
            "culture_type": getattr(tribe1_obj, "culture_type", "balanced"),
            "traits": getattr(tribe1_obj, "traits", []),
        }

        topic = make_markov_choice(
            disagreement_topics,
            "minor_disagreement",
            "conflict",
            conflict_context,
        )

        # Small trust penalty
        relation_key = tuple(sorted([tribe1, tribe2]))
        if relation_key in self.diplomatic_relations:
            self.diplomatic_relations[relation_key]["trust_level"] -= 0.05
            self.diplomatic_relations[relation_key]["trust_level"] = max(
                0.0, self.diplomatic_relations[relation_key]["trust_level"]
            )

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open("communication_log.txt", "a", encoding="utf-8") as comm_log:
            comm_log.write(
                f"[{timestamp}] 💬 Minor disagreement between "
                f"{tribe1} and {tribe2} over {topic}\n"
            )
            comm_log.write(f"[{timestamp}] 😕 Trust slightly decreased\n\n")

    def _process_resource_theft_event(self, thief: str, victim: str) -> None:
        """Process resource theft between tribes"""
        from markov_behavior import make_markov_choice

        thief_tribe = self.tribes[thief]
        victim_tribe = self.tribes[victim]

        # Steal some resources
        theft_amount = random.uniform(3, 10)

        # Use Markov choice for which resource to steal
        available_resources = list(victim_tribe.shared_resources.keys())
        if available_resources:
            thief_context = {
                "economic_specialization": getattr(thief_tribe, "economic_specialization", ""),
                "traits": getattr(thief_tribe, "traits", []),
                "resource_abundance": (
                    sum(thief_tribe.shared_resources.values())
                    / max(1, len(thief_tribe.shared_resources))
                ),
                "season": "winter",  # Theft more likely in scarcity seasons
            }
            resource_type = make_markov_choice(
                available_resources,
                "resource_theft",
                "resource",
                thief_context,
            )
        else:
            resource_type = "food"  # Fallback

        if victim_tribe.shared_resources[resource_type] >= theft_amount:
            victim_tribe.shared_resources[resource_type] -= theft_amount
            thief_tribe.shared_resources[resource_type] += (
                theft_amount * 0.8
            )  # Some loss in transfer

            # Major trust penalty
            relation_key = tuple(sorted([thief, victim]))
            if relation_key in self.diplomatic_relations:
                self.diplomatic_relations[relation_key]["trust_level"] -= 0.2
                self.diplomatic_relations[relation_key]["trust_level"] = max(
                    0.0, self.diplomatic_relations[relation_key]["trust_level"]
                )

            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            with open("communication_log.txt", "a", encoding="utf-8") as comm_log:
                comm_log.write(
                    f"[{timestamp}] 🕵️ {thief} steals {theft_amount:.1f} "
                    f"{resource_type} from {victim}!\n"
                )
                comm_log.write(f"[{timestamp}] 😡 Major trust violation (-0.2 trust)\n\n")

    def _process_boundary_dispute_event(self, tribe1: str, tribe2: str) -> None:
        """Process territorial boundary disputes"""
        dispute_types = [
            "hunting territory",
            "gathering grounds",
            "camping sites",
            "trade routes",
        ]
        dispute_type = random.choice(dispute_types)

        # Moderate trust penalty
        relation_key = tuple(sorted([tribe1, tribe2]))
        if relation_key in self.diplomatic_relations:
            self.diplomatic_relations[relation_key]["trust_level"] -= 0.1
            self.diplomatic_relations[relation_key]["trust_level"] = max(
                0.0, self.diplomatic_relations[relation_key]["trust_level"]
            )
            self.diplomatic_relations[relation_key]["border_tension"] += 0.3

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open("communication_log.txt", "a", encoding="utf-8") as comm_log:
            comm_log.write(
                f"[{timestamp}] 🗺️ Boundary dispute between {tribe1} and "
                f"{tribe2} over {dispute_type}\n"
            )
            comm_log.write(f"[{timestamp}] ⚠️ Border tension increased\n\n")

    def _process_cultural_offense_event(self, offender: str, offended: str) -> None:
        """Process cultural offense between tribes"""
        offenses = [
            "insulting a totem animal",
            "mocking a sacred tradition",
            "disrespecting a spirit guide",
            "ignoring ceremonial protocols",
            "defiling a sacred site",
        ]
        offense = random.choice(offenses)

        # Severe cultural penalty
        relation_key = tuple(sorted([offender, offended]))
        if relation_key in self.diplomatic_relations:
            self.diplomatic_relations[relation_key]["trust_level"] -= 0.25
            self.diplomatic_relations[relation_key]["trust_level"] = max(
                0.0, self.diplomatic_relations[relation_key]["trust_level"]
            )

        # Reduce cultural influence
        if offender in self.cultural_influences and offended in self.cultural_influences[offender]:
            self.cultural_influences[offender][offended] -= 0.1
        if offended in self.cultural_influences and offender in self.cultural_influences[offended]:
            self.cultural_influences[offended][offender] -= 0.1

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open("communication_log.txt", "a", encoding="utf-8") as comm_log:
            comm_log.write(
                f"[{timestamp}] 🙅 Cultural offense: {offender} {offense} of " f"{offended}\n"
            )
            comm_log.write(f"[{timestamp}] 😤 Severe diplomatic incident (-0.25 trust)\n\n")

    def _process_leader_mediation_event(self, mediator: str, dispute_tribes: tuple) -> None:
        """Process leader mediation in tribal disputes"""
        tribe1, tribe2 = dispute_tribes

        # Check if mediation succeeds
        mediation_success = random.random() > 0.4  # 60% success rate

        if mediation_success:
            # Improve relations between disputing tribes
            relation_key = tuple(sorted([tribe1, tribe2]))
            if relation_key in self.diplomatic_relations:
                self.diplomatic_relations[relation_key]["trust_level"] += 0.1
                self.diplomatic_relations[relation_key]["trust_level"] = min(
                    1.0, self.diplomatic_relations[relation_key]["trust_level"]
                )
                self.diplomatic_relations[relation_key]["border_tension"] -= 0.2

            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            with open("communication_log.txt", "a", encoding="utf-8") as comm_log:
                comm_log.write(
                    f"[{timestamp}] ⚖️ {mediator} successfully mediates "
                    f"dispute between {tribe1} and {tribe2}\n"
                )
                comm_log.write(f"[{timestamp}] 🤝 Relations improved " f"(+0.1 trust)\n\n")
        else:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            with open("communication_log.txt", "a", encoding="utf-8") as comm_log:
                comm_log.write(
                    f"[{timestamp}] ⚖️ {mediator}'s mediation between "
                    f"{tribe1} and {tribe2} fails\n\n"
                )

    def form_dynamic_alliance(self, tribe1: str, tribe2: str, alliance_type: AllianceType) -> bool:
        """Form a dynamic alliance between tribes"""
        relation_key = tuple(sorted([tribe1, tribe2]))

        # Check if alliance is appropriate
        trust_level = self.diplomatic_relations[relation_key]["trust_level"]
        cultural_influence = self.calculate_cultural_influence(tribe1, tribe2)

        success_chance = (trust_level + cultural_influence) / 2

        if random.random() < success_chance:
            # Form alliance
            self.diplomatic_relations[relation_key]["alliance_status"] = True
            self.tribes[tribe1].alliances.add(tribe2)
            self.tribes[tribe2].alliances.add(tribe1)

            # Store alliance details
            self.alliance_details[relation_key] = {
                "type": alliance_type.value,
                "formed_at": datetime.now(),
                "trust_level": trust_level,
                "cultural_influence": cultural_influence,
                "duration": self._get_alliance_duration(alliance_type),
                "benefits": self._get_alliance_benefits(alliance_type),
            }

            # Record alliance formation in faction memories
            self._record_alliance_memory(tribe1, tribe2, "formed", alliance_type.value)

            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            with open("communication_log.txt", "a", encoding="utf-8") as comm_log:
                comm_log.write(
                    f"[{timestamp}] 🤝 {alliance_type.value.upper()} FORMED: "
                    f"{tribe1} and {tribe2} allied!\n"
                )
                comm_log.write(
                    f"[{timestamp}] 📋 Benefits: "
                    f"{', '.join(self.alliance_details[relation_key]['benefits'])}\n\n"
                )

            return True

        return False

    def _get_alliance_duration(self, alliance_type: AllianceType) -> int:
        """Get expected duration of alliance type"""
        durations = {
            AllianceType.TRADE_ALLIANCE: 20,
            AllianceType.DEFENSIVE_PACT: 30,
            AllianceType.FULL_ALLIANCE: 50,
            AllianceType.TEMPORARY_TRUCE: 10,
            AllianceType.BLOOD_BROTHERHOOD: 100,
        }
        return durations.get(alliance_type, 20)

    def _get_alliance_benefits(self, alliance_type: AllianceType) -> List[str]:
        """Get benefits of alliance type"""
        benefits = {
            AllianceType.TRADE_ALLIANCE: ["Trade bonuses", "Resource sharing"],
            AllianceType.DEFENSIVE_PACT: ["Mutual defense", "Warning system"],
            AllianceType.FULL_ALLIANCE: [
                "Trade bonuses",
                "Mutual defense",
                "Resource sharing",
                "Cultural exchange",
            ],
            AllianceType.TEMPORARY_TRUCE: ["No raiding", "Safe passage"],
            AllianceType.BLOOD_BROTHERHOOD: [
                "Full alliance benefits",
                "Cultural integration",
                "Intermarriage rights",
            ],
        }
        return benefits.get(alliance_type, ["Basic cooperation"])

    def check_alliance_stability(self) -> None:
        """Check stability of existing alliances"""
        for relation_key, alliance_data in self.alliance_details.items():
            tribe1, tribe2 = relation_key
            alliance_data["duration"] -= 1

            # Check if alliance should break
            current_trust = self.diplomatic_relations[relation_key]["trust_level"]
            original_trust = alliance_data["trust_level"]

            stability_factor = current_trust / original_trust if original_trust > 0 else 1.0

            if stability_factor < 0.6 or alliance_data["duration"] <= 0:
                # Alliance breaks
                self._break_alliance(tribe1, tribe2, alliance_data)

    def _break_alliance(self, tribe1: str, tribe2: str, alliance_data: Dict):
        """Break an alliance between tribes"""
        relation_key = tuple(sorted([tribe1, tribe2]))

        self.diplomatic_relations[relation_key]["alliance_status"] = False
        self.tribes[tribe1].alliances.discard(tribe2)
        self.tribes[tribe2].alliances.discard(tribe1)

        # Reduce trust
        trust_penalty = 0.1
        self.diplomatic_relations[relation_key]["trust_level"] -= trust_penalty
        self.diplomatic_relations[relation_key]["trust_level"] = max(
            0.0, self.diplomatic_relations[relation_key]["trust_level"]
        )

        # Remove alliance details
        if relation_key in self.alliance_details:
            del self.alliance_details[relation_key]

        # Record alliance breakup in faction memories
        self._record_alliance_memory(
            tribe1, tribe2, "broken", alliance_data.get("type", "alliance")
        )

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open("communication_log.txt", "a", encoding="utf-8") as comm_log:
            comm_log.write(
                f"[{timestamp}] 💔 ALLIANCE BROKEN: {tribe1} and {tribe2} "
                f"ended their {alliance_data['type']}\n"
            )
            comm_log.write(f"[{timestamp}] 📉 Trust reduced by {trust_penalty}\n\n")

    def generate_random_diplomatic_events(self):
        """Generate random diplomatic events based on current relations"""
        tribe_names = list(self.tribes.keys())

        for tribe_name in tribe_names:
            if random.random() < 0.1:  # 10% chance per tribe per turn
                other_tribes = [t for t in tribe_names if t != tribe_name]
                if other_tribes:
                    # Use Markov choice for target selection
                    from markov_behavior import make_markov_choice

                    # Build context for initiator tribe
                    initiator_tribe = self.tribes[tribe_name]
                    diplomacy_context = {
                        "traits": getattr(initiator_tribe, "traits", []),
                        "relationship": "varied",
                        "trust_level": 0.5,
                        "recent_events": [],
                    }

                    target_tribe = make_markov_choice(
                        other_tribes,
                        "target_selection",
                        "diplomatic",
                        diplomacy_context,
                    )
                    event_type = self._choose_random_event(tribe_name, target_tribe)

                    if event_type:
                        self.trigger_diplomatic_event(event_type, tribe_name, target_tribe)

    def _choose_random_event(self, tribe1: str, tribe2: str) -> Optional[DiplomaticEvent]:
        """Choose a random event using relations and faction memory."""
        relation_key = tuple(sorted([tribe1, tribe2]))
        trust_level = self.diplomatic_relations[relation_key]["trust_level"]
        standing = self.get_diplomatic_standing(tribe1, tribe2)

        # Get memory influence from both tribes
        memory_modifier = 0.0
        if hasattr(self.tribes[tribe1], "faction") and self.tribes[tribe1].faction:
            faction_memory = self.tribes[tribe1].faction.get_memory_influence(tribe2)
            memory_modifier += (
                faction_memory["hostility_modifier"] - faction_memory["trust_modifier"]
            )

        # Event probabilities based on standing, modified by memory
        base_weights = []
        events = []

        if standing in ["Trusted Ally", "Reliable Ally"]:
            events = [
                DiplomaticEvent.GIFTING,
                DiplomaticEvent.CULTURAL_EXCHANGE,
                DiplomaticEvent.CEREMONIAL_VISIT,
                DiplomaticEvent.SHARED_HUNTING,
            ]
            base_weights = [0.3, 0.3, 0.2, 0.2]
            # Memory can make positive events more or less likely
            if memory_modifier > 0.2:  # Grudges reduce positive events
                base_weights = [w * 0.7 for w in base_weights]
        elif standing in ["Friendly", "Cordial"]:
            events = [
                DiplomaticEvent.GIFTING,
                DiplomaticEvent.CULTURAL_EXCHANGE,
                DiplomaticEvent.TRADE_DISPUTE,
                DiplomaticEvent.CEREMONIAL_VISIT,
            ]
            base_weights = [0.25, 0.25, 0.2, 0.3]
        elif standing in ["Neutral", "Wary"]:
            events = [
                DiplomaticEvent.RESOURCE_DISPUTE,
                DiplomaticEvent.TERRITORY_CONFLICT,
                DiplomaticEvent.GIFTING,
                DiplomaticEvent.CULTURAL_EXCHANGE,
            ]
            base_weights = [0.3, 0.3, 0.2, 0.2]
            # Memory influences neutral events
            if memory_modifier > 0.3:  # Strong grudges raise negatives
                base_weights[0] += 0.1  # More resource disputes
                base_weights[1] += 0.1  # More territory conflicts
                base_weights[2] -= 0.1  # Fewer gifts
                base_weights[3] -= 0.1  # Fewer exchanges
        else:  # Hostile, Bitter Enemy
            events = [
                DiplomaticEvent.RAID,
                DiplomaticEvent.RESOURCE_DISPUTE,
                DiplomaticEvent.TERRITORY_CONFLICT,
                DiplomaticEvent.ALLIANCE_BETRAYAL,
            ]
            base_weights = [0.4, 0.3, 0.2, 0.1]
            # Memory can intensify hostility
            if memory_modifier > 0.4:  # Very strong grudges
                base_weights[0] += 0.1  # More raids
                base_weights[3] += 0.1  # More betrayals

        # Normalize weights
        total_weight = sum(base_weights)
        if total_weight > 0:
            base_weights = [w / total_weight for w in base_weights]

        # Use Markov-based event selection instead of weighted random
        from markov_behavior import make_markov_choice

        if events:
            # Build context for diplomatic event decision
            tribe1_obj = self.tribes[tribe1]
            diplomacy_context = {
                "trust_level": trust_level,
                "relationship": standing.lower().replace(" ", "_"),
                "traits": getattr(tribe1_obj, "traits", []),
                "recent_events": [],  # Could track recent diplomatic history
            }

            # Convert events to strings for Markov choice
            event_names = [event.value for event in events]
            chosen_event_name = make_markov_choice(
                event_names,
                f"diplomatic_{standing.lower()}",
                "diplomatic",
                diplomacy_context,
            )

            # Convert back to enum
            for event in events:
                if event.value == chosen_event_name:
                    return event

        return None

    def _get_standing_score(self, tribe1: str, tribe2: str) -> float:
        """Convert diplomatic standing to numerical score for ranking"""
        standing = self.get_diplomatic_standing(tribe1, tribe2)
        standing_scores = {
            "Trusted Ally": 1.0,
            "Reliable Ally": 0.9,
            "Trusted Friend": 0.85,
            "Friendly": 0.75,
            "Cordial": 0.65,
            "Neutral": 0.5,
            "Wary": 0.35,
            "Distrusted": 0.25,
            "Hostile": 0.15,
            "Bitter Enemy": 0.05,
            "Unstable Ally": 0.7,
        }
        return standing_scores.get(standing, 0.5)

    def process_diplomatic_turn(self):
        """Process one turn of inter-tribal diplomacy"""
        self._update_relations()
        self._initiate_proactive_negotiations()
        self._handle_active_negotiations()
        self._process_trade_agreements()
        self._check_alliance_stability()
        self._generate_diplomatic_events()

    def _update_relations(self):
        """Update diplomatic relations based on various factors"""
        for key, relation in self.diplomatic_relations.items():
            tribe1_name, tribe2_name = key
            tribe1 = self.tribes.get(tribe1_name)
            tribe2 = self.tribes.get(tribe2_name)

            if not tribe1 or not tribe2:
                continue

            # Factors affecting relations
            trust_change = 0.0

            # Shared alliances improve relations
            common_allies = len(tribe1.alliances & tribe2.alliances)
            trust_change += common_allies * 0.02

            # Shared rivalries improve relations
            common_rivals = len(tribe1.rivalries & tribe2.rivalries)
            trust_change += common_rivals * 0.02

            # Border proximity can cause tension
            # (This would be calculated based on actual territory proximity)
            border_tension = relation["border_tension"]
            trust_change -= border_tension * 0.01

            # Trade relationships improve trust
            if relation["trade_volume"] > 0:
                trust_change += 0.01

            # Gradual trust decay toward neutral
            trust_change += (0.5 - relation["trust_level"]) * 0.005

            # Update trust level
            relation["trust_level"] += trust_change
            relation["trust_level"] = max(0.0, min(1.0, relation["trust_level"]))

            # Update reputation scores
            self.reputation_scores[tribe1_name][tribe2_name] = relation["trust_level"]
            self.reputation_scores[tribe2_name][tribe1_name] = relation["trust_level"]

    def _initiate_proactive_negotiations(self):
        """Proactively initiate negotiations based on tribe needs."""
        for tribe_name, tribe in self.tribes.items():
            # Only leaders can initiate negotiations (with some probability)
            if random.random() < 0.15:  # Back to 15% chance
                self._evaluate_negotiation_opportunities(tribe)

    def _evaluate_negotiation_opportunities(self, tribe: Tribe):
        """Evaluate if a tribe should initiate negotiations with others"""
        # Check resource needs
        resource_needs = self._assess_resource_needs(tribe)

        # Check security concerns
        security_concerns = self._assess_security_needs(tribe)

        # Check expansion opportunities
        expansion_opportunities = self._assess_expansion_opportunities(tribe)

        # Prioritize negotiation targets based on reputation and proximity
        potential_targets = self._rank_potential_negotiation_targets(tribe)

        for target_name in potential_targets[:3]:  # Consider top 3 targets
            target_tribe = self.tribes[target_name]
            relation_key = tuple(sorted([tribe.name, target_name]))
            trust_level = self.diplomatic_relations[relation_key]["trust_level"]

            # Decide negotiation type based on needs and trust
            negotiation_type = self._choose_negotiation_type(
                tribe,
                target_tribe,
                resource_needs,
                security_concerns,
                expansion_opportunities,
                trust_level,
            )

            if negotiation_type:
                self._initiate_smart_negotiation(
                    tribe,
                    target_tribe,
                    negotiation_type,
                    resource_needs,
                    security_concerns,
                    expansion_opportunities,
                )

    def _assess_resource_needs(self, tribe: Tribe) -> Dict[str, float]:
        """Assess tribe's resource needs and surpluses"""
        needs = {}
        total_resources = sum(tribe.shared_resources.values())

        for resource, amount in tribe.shared_resources.items():
            if total_resources > 0:
                relative_amount = amount / total_resources
                if relative_amount < 0.15:  # Less than 15% of total resources
                    needs[resource] = 1.0 - relative_amount  # Higher need = higher value
                elif relative_amount > 0.4:  # More than 40% of total resources
                    needs[resource] = -(relative_amount - 0.4)

        return needs

    def _assess_security_needs(self, tribe: Tribe) -> float:
        """Assess tribe's security concerns (0-1 scale)"""
        security_score = 0.0

        # Population size affects security
        if len(tribe.member_ids) < 5:
            security_score += 0.3

        # Check for rivalries
        rival_count = len(tribe.rivalries)
        security_score += min(rival_count * 0.2, 0.4)

        # Check alliance strength
        ally_count = len(tribe.alliances)
        security_score -= min(ally_count * 0.15, 0.3)

        return max(0.0, min(1.0, security_score))

    def _assess_expansion_opportunities(self, tribe: Tribe) -> float:
        """Assess tribe's expansion opportunities (0-1 scale)"""
        opportunity_score = 0.0

        # Population pressure
        if len(tribe.member_ids) > 10:
            opportunity_score += 0.3

        # Economic success
        wellbeing = tribe.get_wellbeing_score()
        if wellbeing > 0.8:
            opportunity_score += 0.2

        # Current territory size (simplified)
        # In a real implementation, this would check actual territory size
        opportunity_score += 0.1

        return max(0.0, min(1.0, opportunity_score))

    def _rank_potential_negotiation_targets(self, tribe: Tribe) -> List[str]:
        """Rank potential negotiation targets by desirability"""
        targets = []

        for other_name, other_tribe in self.tribes.items():
            if other_name == tribe.name:
                continue

            # Calculate target score based on multiple factors
            relation_key = tuple(sorted([tribe.name, other_name]))

            # Distance factor simplified; all are reachable for now

            # Trade potential
            trade_potential = 0.0
            for resource in tribe.shared_resources:
                if resource in other_tribe.shared_resources:
                    tribe_amount = tribe.shared_resources[resource]
                    other_amount = other_tribe.shared_resources[resource]
                    if (
                        tribe_amount > 20 and other_amount < 10
                    ):  # Tribe has surplus, other has deficit
                        trade_potential += 0.2
                    elif (
                        other_amount > 20 and tribe_amount < 10
                    ):  # Other has surplus, tribe has deficit
                        trade_potential += 0.2

            # Alliance potential
            alliance_potential = 0.0
            if (
                self.is_good_standing_for_alliance(tribe.name, other_name)
                and not self.diplomatic_relations[relation_key]["alliance_status"]
            ):
                alliance_potential = 0.3

            # Standing score (convert standing to numerical score)
            standing_score = self._get_standing_score(tribe.name, other_name)

            # Overall score
            score = (standing_score * 0.4) + (trade_potential * 0.3) + (alliance_potential * 0.3)

            targets.append((other_name, score))

        # Sort by score (highest first)
        targets.sort(key=lambda x: x[1], reverse=True)
        return [name for name, score in targets]

    def _choose_negotiation_type_detailed(
        self,
        tribe: Tribe,
        target_tribe: Tribe,
        resource_needs: Dict,
        security_concerns: float,
        expansion_opportunities: float,
        trust_level: float,
    ) -> Optional[str]:
        """Detailed negotiation type selection (full version used internally).

        This was formerly the original implementation; indentation and
        structure corrected after introducing a dispatcher for backward
        compatibility with legacy 3-argument test calls.
        """
        seasonal_modifiers = self._get_seasonal_modifiers()
        season_name = (
            self.seasonal_context.get("season_name", "Unknown")
            if self.seasonal_context
            else "Unknown"
        )

        tribe_modifiers = getattr(tribe, "priority_modifiers", {})
        # target_modifiers reserved for future weighting; not needed now
        # target_modifiers = getattr(target_tribe, "priority_modifiers", {})

        alliance_likelihood = (
            0.3
            * seasonal_modifiers.get("alliance_likelihood", 1.0)
            * tribe_modifiers.get("alliance_value", 1.0)
        )
        trade_likelihood = (
            0.4
            * seasonal_modifiers.get("trade_likelihood", 1.0)
            * tribe_modifiers.get("trade_willingness", 1.0)
        )

        self.logger.debug(
            f"Tribe {tribe.name} negotiation consideration in {season_name}: "
            f"alliance_likelihood={alliance_likelihood:.2f}, trade_likelihood={trade_likelihood:.2f}"
        )

        # Alliance consideration (season + trust gated)
        if (
            self.is_good_standing_for_alliance(tribe.name, target_tribe.name)
            and random.random() < alliance_likelihood
        ):
            relation_key = tuple(sorted([tribe.name, target_tribe.name]))
            if not self.diplomatic_relations[relation_key]["alliance_status"]:
                self.logger.debug(
                    f"Tribe {tribe.name} considering alliance with {target_tribe.name} during {season_name}"
                )
                return "alliance"

        # Trade consideration (resource pressure or surplus)
        has_resource_needs = any(need > 0.3 for need in resource_needs.values())
        has_resource_surplus = any(need < -0.2 for need in resource_needs.values())
        if (
            (has_resource_needs or has_resource_surplus)
            and self.is_good_standing_for_trade(tribe.name, target_tribe.name)
            and random.random() < trade_likelihood
        ):
            if self._would_trade_be_mutually_beneficial(tribe, target_tribe, resource_needs):
                self.logger.debug(
                    f"Tribe {tribe.name} considering trade with {target_tribe.name} during {season_name}"
                )
                return "trade"

        # Truce consideration (security concerns scaled by season)
        truce_threshold = 0.6
        if (
            self.seasonal_context and self.seasonal_context["season"] == 3
        ):  # Winter lowers threshold
            truce_threshold = 0.4
        if security_concerns > truce_threshold and not self.is_poor_standing(
            tribe.name, target_tribe.name
        ):
            self.logger.debug(
                f"Tribe {tribe.name} considering truce with {target_tribe.name} during {season_name}"
            )
            return "truce"

        # Threat consideration (lower in harsh seasons via seasonal modifiers)
        conflict_likelihood = (
            0.2
            * seasonal_modifiers.get("conflict_likelihood", 1.0)
            * tribe_modifiers.get("conflict_likelihood", 1.0)
        )
        if (
            self.is_poor_standing(tribe.name, target_tribe.name)
            and random.random() < conflict_likelihood
        ):
            self.logger.debug(
                f"Tribe {tribe.name} considering threat against {target_tribe.name} during {season_name}"
            )
            return "threat"

        return None

    # Dispatcher preserving old simplified signature used in tests
    def _choose_negotiation_type(self, *args, **kwargs):
        """Dispatcher supporting legacy and detailed negotiation selection.

        Usage patterns:
        1) Legacy/tests: _choose_negotiation_type(tribe_a, tribe_b, context_dict)
           -> routes to simple heuristic selection.
        2) Internal/detailed: _choose_negotiation_type(tribe, target_tribe, resource_needs,
              security_concerns=<float>, expansion_opportunities=<float>, trust_level=<float>)
           -> routes to detailed probabilistic evaluation.
        """
        if len(args) == 3 and not kwargs:
            tribe_a, tribe_b, _context = args
            return self._choose_negotiation_type_simple(tribe_a, tribe_b)
        return self._choose_negotiation_type_detailed(*args, **kwargs)

    def _choose_negotiation_type_simple(self, tribe_a: Tribe, tribe_b: Tribe):
        """Simplified negotiation heuristic.

        Decides among 'alliance_talks', 'trade_expansion', 'deescalation', 'status_quo'
        based on trust and seasonal modifiers only. Designed for lightweight tests
        and legacy integration points.
        """
        key = tuple(sorted([tribe_a.name, tribe_b.name]))
        trust = self.diplomatic_relations.get(key, {}).get("trust_level", 0.5)
        mods = self._get_seasonal_modifiers()
        alliance_score = trust * mods.get("alliance_likelihood", 1.0)
        trade_score = mods.get("trade_likelihood", 1.0)
        conflict_pressure = (1.0 - trust) * mods.get("conflict_likelihood", 1.0)
        if alliance_score > max(trade_score, conflict_pressure):
            return "alliance_talks"
        if trade_score >= max(alliance_score, conflict_pressure):
            return "trade_expansion"
        if conflict_pressure > 0.9:
            return "deescalation"
        return "status_quo"

    def _would_trade_be_mutually_beneficial(
        self, tribe1: Tribe, tribe2: Tribe, tribe1_needs: Dict
    ) -> bool:
        """Check if trade would benefit both tribes"""
        mutual_benefit = False

        for resource, need in tribe1_needs.items():
            if need > 0.3:  # Tribe1 needs this resource
                if tribe2.shared_resources.get(resource, 0) > 15:  # Tribe2 has surplus
                    mutual_benefit = True
                    break
            elif need < -0.2:  # Tribe1 has surplus
                if tribe2.shared_resources.get(resource, 0) < 10:  # Tribe2 needs this resource
                    mutual_benefit = True
                    break

        return mutual_benefit

    def _initiate_smart_negotiation(
        self,
        tribe: Tribe,
        target_tribe: Tribe,
        negotiation_type: str,
        resource_needs: Dict,
        security_concerns: float,
        expansion_opportunities: float,
    ):
        """Initiate a negotiation with smart terms based on tribe conditions"""

        negotiation_data = {
            "initiator": tribe.name,
            "target": target_tribe.name,
            "type": negotiation_type,
            "turns_remaining": random.randint(3, 6),
            "terms": {},
        }

        # Customize terms based on negotiation type
        if negotiation_type == "trade":
            negotiation_data["terms"] = self._create_trade_terms(
                tribe, target_tribe, resource_needs
            )
        elif negotiation_type == "alliance":
            negotiation_data["terms"] = self._create_alliance_terms(tribe, target_tribe)
        elif negotiation_type == "truce":
            negotiation_data["terms"] = self._create_truce_terms(
                tribe, target_tribe, security_concerns
            )
        elif negotiation_type == "threat":
            negotiation_data["terms"] = self._create_threat_terms(tribe, target_tribe)

        self.active_negotiations.append(negotiation_data)
        self.logger.debug(
            f"Smart negotiation initiated: {tribe.name} → {target_tribe.name} ({negotiation_type})"
        )

        # Log to communication log file in DM format
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open("communication_log.txt", "a", encoding="utf-8") as comm_log:
            comm_log.write(
                f"[{timestamp}] 💬 {tribe.name} initiates {negotiation_type} negotiations with {target_tribe.name}\n"
            )
            comm_log.write(
                f"[{timestamp}] 🤝 Diplomatic talks begin between {tribe.name} and {target_tribe.name}\n\n"
            )

        self.logger.debug(
            f"💬 {tribe.name} initiates {negotiation_type} negotiations with {target_tribe.name}"
        )

    def _create_trade_terms(self, tribe: Tribe, target_tribe: Tribe, resource_needs: Dict) -> Dict:
        """Create specific trade terms"""
        terms = {"offers": [], "requests": []}

        # What tribe offers
        for resource, need in resource_needs.items():
            if need < -0.2:  # Surplus
                amount = min(int(abs(need) * 10), 5)  # Convert to actual amount
                if tribe.shared_resources.get(resource, 0) >= amount:
                    terms["offers"].append({"resource": resource, "amount": amount})

        # What tribe requests
        for resource, need in resource_needs.items():
            if need > 0.3:  # Deficit
                amount = min(int(need * 8), 4)  # Reasonable request amount
                terms["requests"].append({"resource": resource, "amount": amount})

        return terms

    def _create_alliance_terms(self, tribe: Tribe, target_tribe: Tribe) -> Dict:
        """Create alliance terms"""
        return {
            "mutual_defense": True,
            "trade_benefits": True,
            "duration": random.randint(20, 50),  # Alliance duration in turns
        }

    def _create_truce_terms(
        self, tribe: Tribe, target_tribe: Tribe, security_concerns: float
    ) -> Dict:
        """Create truce terms"""
        duration = int(security_concerns * 20) + 5  # Longer truce if more concerned
        return {
            "duration": duration,
            "no_aggression": True,
            "limited_trade": random.random() < 0.5,  # 50% chance of limited trade
        }

    def _create_threat_terms(self, tribe: Tribe, target_tribe: Tribe) -> Dict:
        """Create threat/demand terms"""
        return {
            "demand": "territory_concession",  # Could be territory, resources, etc.
            "consequence": "hostilities",
            "deadline": 3,  # Turns to comply
        }

    def _handle_active_negotiations(self):
        """Process ongoing diplomatic negotiations"""
        for negotiation in self.active_negotiations[:]:
            negotiation["turns_remaining"] -= 1

            if negotiation["turns_remaining"] <= 0:
                self._resolve_negotiation(negotiation)
                self.active_negotiations.remove(negotiation)

    def _resolve_negotiation(self, negotiation: Dict):
        """Resolve a diplomatic negotiation with enhanced logic"""
        tribe1_name = negotiation["initiator"]
        tribe2_name = negotiation["target"]
        negotiation_type = negotiation["type"]
        terms = negotiation.get("terms", {})

        tribe1 = self.tribes.get(tribe1_name)
        tribe2 = self.tribes.get(tribe2_name)

        if not tribe1 or not tribe2:
            return

        # Enhanced success calculation considering reputation and terms
        success_chance = self._calculate_negotiation_success_chance(
            tribe1, tribe2, negotiation_type, terms
        )

        if random.random() < success_chance:
            self._successful_negotiation(negotiation, tribe1, tribe2)
        else:
            self._failed_negotiation(negotiation, tribe1, tribe2)

    def _calculate_negotiation_success_chance(
        self, tribe1: Tribe, tribe2: Tribe, negotiation_type: str, terms: Dict
    ) -> float:
        """Calculate negotiation success chance based on multiple factors"""
        relation_key = tuple(sorted([tribe1.name, tribe2.name]))
        trust_level = self.diplomatic_relations[relation_key]["trust_level"]

        # Base chance from trust
        base_chance = trust_level

        # Leader skill influence
        leader1_skill = self._get_leader_diplomacy_skill(tribe1)
        leader2_skill = self._get_leader_diplomacy_skill(tribe2)

        # Initiator has advantage
        skill_factor = (leader1_skill * 0.6) + (leader2_skill * 0.4)
        base_chance += skill_factor * 0.3

        # Terms influence
        terms_modifier = self._evaluate_negotiation_terms(tribe1, tribe2, negotiation_type, terms)
        base_chance += terms_modifier

        # Negotiation type modifiers
        type_modifiers = {
            "trade": 0.1,  # Trade is generally acceptable
            "alliance": -0.1,  # Alliances require high trust
            "truce": 0.0,  # Neutral
            "threat": -0.3,  # Threats are hard to succeed
        }
        base_chance += type_modifiers.get(negotiation_type, 0.0)

        # Clamp to reasonable range
        return max(0.05, min(0.95, base_chance))

    def _get_leader_diplomacy_skill(self, tribe: Tribe) -> float:
        """Get the diplomacy skill of a tribe's leader"""
        # In a real implementation, this would check leader stats
        # For now, use a random factor influenced by tribe wellbeing
        wellbeing = tribe.get_wellbeing_score()
        base_skill = random.uniform(0.3, 0.8)
        return base_skill + (wellbeing - 0.5) * 0.4  # Wellbeing influences skill

    def _evaluate_negotiation_terms(
        self, tribe1: Tribe, tribe2: Tribe, negotiation_type: str, terms: Dict
    ) -> float:
        """Evaluate how favorable the negotiation terms are"""
        modifier = 0.0

        if negotiation_type == "trade":
            modifier = self._evaluate_trade_terms(tribe1, tribe2, terms)
        elif negotiation_type == "alliance":
            modifier = self._evaluate_alliance_terms(tribe1, tribe2, terms)
        elif negotiation_type == "truce":
            modifier = self._evaluate_truce_terms(tribe1, tribe2, terms)
        elif negotiation_type == "threat":
            modifier = self._evaluate_threat_terms(tribe1, tribe2, terms)

        return modifier

    def _evaluate_trade_terms(self, tribe1: Tribe, tribe2: Tribe, terms: Dict) -> float:
        """Evaluate trade terms fairness"""
        fairness_score = 0.0

        offers = terms.get("offers", [])
        requests = terms.get("requests", [])

        # Calculate value of offers (what tribe1 gives to tribe2)
        offer_value = 0
        for offer in offers:
            resource = offer["resource"]
            amount = offer["amount"]
            # Simplified: each unit has value 1, but scarcity increases value
            scarcity = 1.0 - (
                tribe1.shared_resources.get(resource, 0) / 50.0
            )  # Less available = more valuable
            offer_value += amount * scarcity

        # Calculate value of requests (what tribe2 gives to tribe1)
        request_value = 0
        for request in requests:
            resource = request["resource"]
            amount = request["amount"]
            scarcity = 1.0 - (tribe2.shared_resources.get(resource, 0) / 50.0)
            request_value += amount * scarcity

        # Fair trade is when values are roughly equal
        if offer_value > 0 and request_value > 0:
            ratio = min(offer_value, request_value) / max(offer_value, request_value)
            fairness_score = (ratio - 0.5) * 0.4  # Convert to modifier
        elif offer_value > request_value:
            fairness_score = -0.2  # Tribe1 offers more than receives
        else:
            fairness_score = 0.1  # Tribe1 receives more than offers

        return fairness_score

    def _evaluate_alliance_terms(self, tribe1: Tribe, tribe2: Tribe, terms: Dict) -> float:
        """Evaluate alliance terms"""
        modifier = 0.0

        if terms.get("mutual_defense", False):
            modifier += 0.1  # Mutual defense is valuable

        if terms.get("trade_benefits", False):
            modifier += 0.1  # Trade benefits are valuable

        duration = terms.get("duration", 30)
        if duration > 40:
            modifier += 0.05  # Long alliances are more valuable
        elif duration < 20:
            modifier -= 0.05  # Short alliances are less valuable

        return modifier

    def _evaluate_truce_terms(self, tribe1: Tribe, tribe2: Tribe, terms: Dict) -> float:
        """Evaluate truce terms"""
        modifier = 0.0

        duration = terms.get("duration", 10)
        if duration > 15:
            modifier += 0.1  # Long truces are valuable for security
        elif duration < 5:
            modifier -= 0.1  # Short truces are less valuable

        if terms.get("limited_trade", False):
            modifier += 0.05  # Trade during truce is a bonus

        return modifier

    def _evaluate_threat_terms(self, tribe1: Tribe, tribe2: Tribe, terms: Dict) -> float:
        """Evaluate threat terms (usually negative for target)"""
        # For threats, the evaluation is from the perspective of the target
        # Threats are generally unfavorable
        modifier = -0.2

        demand = terms.get("demand", "")
        if demand == "territory_concession":
            # Check relative strength
            tribe1_strength = len(tribe1.member_ids) + len(tribe1.alliances) * 2
            tribe2_strength = len(tribe2.member_ids) + len(tribe2.alliances) * 2

            if tribe1_strength > tribe2_strength * 1.5:
                modifier += 0.1  # Strong tribe can make credible threats
            else:
                modifier -= 0.1  # Weak tribe's threats are laughable

        return modifier

    def _successful_negotiation(self, negotiation: Dict, tribe1: Tribe, tribe2: Tribe):
        """Handle successful negotiation with enhanced terms handling"""
        negotiation_type = negotiation["type"]
        terms = negotiation.get("terms", {})

        if negotiation_type == "alliance":
            self._execute_alliance_agreement(tribe1, tribe2, terms)

        elif negotiation_type == "trade":
            self._execute_trade_agreement(tribe1, tribe2, terms)

        elif negotiation_type == "truce":
            self._execute_truce_agreement(tribe1, tribe2, terms)

        elif negotiation_type == "threat":
            self._execute_threat_resolution(tribe1, tribe2, terms)

        # Update diplomatic relations positively
        relation_key = tuple(sorted([tribe1.name, tribe2.name]))
        trust_increase = 0.1 + (random.random() * 0.1)  # 0.1 to 0.2 increase
        self.diplomatic_relations[relation_key]["trust_level"] += trust_increase
        self.diplomatic_relations[relation_key]["trust_level"] = min(
            1.0, self.diplomatic_relations[relation_key]["trust_level"]
        )

        # Update reputation scores
        self.reputation_scores[tribe1.name][tribe2.name] += trust_increase * 0.8
        self.reputation_scores[tribe2.name][tribe1.name] += trust_increase * 0.8

        self.logger.debug(
            f"Successful {negotiation_type} negotiation between {tribe1.name} and {tribe2.name}"
        )

        # Log to communication log file in DM format
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open("communication_log.txt", "a", encoding="utf-8") as comm_log:
            comm_log.write(
                f"[{timestamp}] 🤝 {tribe1.name} and {tribe2.name} successfully negotiated {negotiation_type}!\n"
            )
            comm_log.write(
                f"[{timestamp}] 🎉 Relations between {tribe1.name} and {tribe2.name} have improved\n\n"
            )

        self.logger.debug(
            f"🤝 {tribe1.name} and {tribe2.name} successfully negotiated {negotiation_type}!"
        )

    def _execute_alliance_agreement(self, tribe1: Tribe, tribe2: Tribe, terms: Dict):
        """Execute alliance agreement with specific terms"""
        tribe1.form_alliance(tribe2.name)
        tribe2.form_alliance(tribe1.name)

        # Update diplomatic relations
        relation_key = tuple(sorted([tribe1.name, tribe2.name]))
        self.diplomatic_relations[relation_key]["alliance_status"] = True

        # Apply alliance benefits
        if terms.get("mutual_defense", False):
            # In a real implementation, this would affect combat calculations
            self.logger.info(
                f"Mutual defense pact established between {tribe1.name} and {tribe2.name}"
            )

        if terms.get("trade_benefits", False):
            # Improve trade relations
            self.diplomatic_relations[relation_key]["trade_volume"] += 2

        duration = terms.get("duration", 30)
        self.logger.info(
            f"Alliance formed between {tribe1.name} and {tribe2.name} for {duration} turns"
        )

    def _execute_trade_agreement(self, tribe1: Tribe, tribe2: Tribe, terms: Dict):
        """Execute trade agreement with specific terms"""
        offers = terms.get("offers", [])
        requests = terms.get("requests", [])

        # Execute immediate trade
        trade_executed = False

        # Tribe1 gives offers to tribe2
        for offer in offers:
            resource = offer["resource"]
            amount = offer["amount"]
            if tribe1.take_shared_resource(resource, amount) > 0:
                tribe2.add_shared_resource(resource, amount)
                trade_executed = True

        # Tribe2 gives requests to tribe1
        for request in requests:
            resource = request["resource"]
            amount = request["amount"]
            if tribe2.take_shared_resource(resource, amount) > 0:
                tribe1.add_shared_resource(resource, amount)
                trade_executed = True

        if trade_executed:
            # Establish ongoing trade agreement
            agreement_key = tuple(sorted([tribe1.name, tribe2.name]))
            agreement = {
                "tribe1_offers": offers,
                "tribe2_offers": [
                    {"resource": r["resource"], "amount": r["amount"]} for r in requests
                ],
                "duration": 15,  # Standard trade agreement duration
                "turns_remaining": 15,
                "established_turn": len(self.diplomatic_history),
            }

            self.trade_agreements[agreement_key] = agreement

            # Update diplomatic relations
            self.diplomatic_relations[agreement_key]["trade_volume"] += 1
            self.diplomatic_relations[agreement_key]["trust_level"] += 0.05

            self.logger.info(f"Trade agreement executed between {tribe1.name} and {tribe2.name}")
        else:
            self.logger.warning(
                f"Trade agreement between {tribe1.name} and {tribe2.name} could not be executed - insufficient resources"
            )

    def _execute_truce_agreement(self, tribe1: Tribe, tribe2: Tribe, terms: Dict):
        """Execute truce agreement"""
        duration = terms.get("duration", 10)

        tribe1.negotiate_truce(tribe2.name, duration)
        tribe2.negotiate_truce(tribe1.name, duration)

        # Reduce border tension
        relation_key = tuple(sorted([tribe1.name, tribe2.name]))
        self.diplomatic_relations[relation_key]["border_tension"] *= 0.5

        if terms.get("limited_trade", False):
            # Allow some trade during truce
            self.diplomatic_relations[relation_key]["trade_volume"] += 0.5

        self.logger.info(
            f"Truce negotiated between {tribe1.name} and {tribe2.name} for {duration} turns"
        )

    def _execute_threat_resolution(self, tribe1: Tribe, tribe2: Tribe, terms: Dict):
        """Execute threat resolution - usually unfavorable for target"""
        demand = terms.get("demand", "")

        if demand == "territory_concession":
            # In a real implementation, this would involve territory transfer
            # For now, just reduce trust and increase tension
            relation_key = tuple(sorted([tribe1.name, tribe2.name]))
            self.diplomatic_relations[relation_key]["trust_level"] -= 0.15
            self.diplomatic_relations[relation_key]["border_tension"] += 0.3

            self.logger.info(
                f"{tribe1.name} made territorial demands on {tribe2.name} - relations strained"
            )
        else:
            # Generic threat response
            self.logger.info(f"Threat from {tribe1.name} to {tribe2.name} partially successful")

    def _failed_negotiation(self, negotiation: Dict, tribe1: Tribe, tribe2: Tribe):
        """Handle failed negotiation with reputation consequences"""
        negotiation_type = negotiation["type"]

        # Calculate trust penalty based on negotiation type and current trust
        relation_key = tuple(sorted([tribe1.name, tribe2.name]))
        current_trust = self.diplomatic_relations[relation_key]["trust_level"]

        # Failed negotiations hurt more when trust is already low
        trust_penalty = 0.05 + (0.15 * (1.0 - current_trust))

        # Different negotiation types have different failure penalties
        type_multipliers = {
            "alliance": 1.5,  # Failed alliance attempts hurt a lot
            "trade": 0.8,  # Failed trade hurts less
            "truce": 1.2,  # Failed truce attempts are serious
            "threat": 2.0,  # Failed threats can lead to retaliation
        }

        trust_penalty *= type_multipliers.get(negotiation_type, 1.0)

        # Apply trust penalty
        self.diplomatic_relations[relation_key]["trust_level"] -= trust_penalty
        self.diplomatic_relations[relation_key]["trust_level"] = max(
            0.0, self.diplomatic_relations[relation_key]["trust_level"]
        )

        # Update reputation scores
        reputation_penalty = trust_penalty * 0.7
        self.reputation_scores[tribe1.name][tribe2.name] -= reputation_penalty
        self.reputation_scores[tribe2.name][tribe1.name] -= (
            reputation_penalty * 0.5
        )  # Target is less affected

        # Additional consequences for certain failure types
        if negotiation_type == "threat":
            # Failed threats can lead to rivalries
            if current_trust < 0.3 and random.random() < 0.4:
                tribe1.declare_rivalry(tribe2.name)
                tribe2.declare_rivalry(tribe1.name)
                self.diplomatic_relations[relation_key]["border_tension"] += 0.4
                self.logger.info(
                    f"Failed threat led to rivalry between {tribe1.name} and {tribe2.name}"
                )

        elif negotiation_type == "alliance":
            # Failed alliance can increase tension
            self.diplomatic_relations[relation_key]["border_tension"] += 0.2

        self.logger.info(
            f"Diplomatic negotiation failed between {tribe1.name} and {tribe2.name} - trust decreased by {trust_penalty:.2f}"
        )

        # Log to communication log file in DM format
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open("communication_log.txt", "a", encoding="utf-8") as comm_log:
            comm_log.write(
                f"[{timestamp}] ❌ {tribe1.name} and {tribe2.name} failed {negotiation_type} negotiation - relations strained!\n"
            )
            comm_log.write(
                f"[{timestamp}] 😠 Tensions rise between {tribe1.name} and {tribe2.name}\n\n"
            )

        self.logger.debug(
            f"❌ {tribe1.name} and {tribe2.name} failed {negotiation_type} negotiation - relations strained!"
        )

    def _establish_trade_agreement(self, tribe1: Tribe, tribe2: Tribe, terms: Dict):
        """Establish a trade agreement between tribes"""
        agreement_key = tuple(sorted([tribe1.name, tribe2.name]))

        # Determine trade terms based on tribe resources and needs
        tribe1_offers = []
        tribe2_offers = []

        # Tribe1 offers what it has excess of
        for resource, amount in tribe1.shared_resources.items():
            if amount > 20:  # Excess threshold
                offer_amount = min(amount * 0.2, 5)  # Offer 20% up to 5 units
                if offer_amount >= 1:
                    tribe1_offers.append({"resource": resource, "amount": round(offer_amount)})

        # Tribe2 offers what it has excess of
        for resource, amount in tribe2.shared_resources.items():
            if amount > 20:
                offer_amount = min(amount * 0.2, 5)
                if offer_amount >= 1:
                    tribe2_offers.append({"resource": resource, "amount": round(offer_amount)})

        agreement = {
            "tribe1_offers": tribe1_offers,
            "tribe2_offers": tribe2_offers,
            "duration": random.randint(5, 15),
            "turns_remaining": random.randint(5, 15),
            "established_turn": len(self.diplomatic_history),
        }

        self.trade_agreements[agreement_key] = agreement

        # Update diplomatic relations
        self.diplomatic_relations[agreement_key]["trade_volume"] += 1
        self.diplomatic_relations[agreement_key]["trust_level"] += 0.1

        self.logger.info(f"Trade agreement established between {tribe1.name} and {tribe2.name}")

    def _process_trade_agreements(self):
        """Process active trade agreements"""
        for agreement_key, agreement in list(self.trade_agreements.items()):
            agreement["turns_remaining"] -= 1

            if agreement["turns_remaining"] <= 0:
                # Agreement expires
                del self.trade_agreements[agreement_key]
                self.logger.info(
                    f"Trade agreement expired between {agreement_key[0]} and {agreement_key[1]}"
                )
                continue

            # Execute trade
            tribe1_name, tribe2_name = agreement_key
            tribe1 = self.tribes.get(tribe1_name)
            tribe2 = self.tribes.get(tribe2_name)

            if tribe1 and tribe2:
                # Tribe1 gives to tribe2
                for offer in agreement["tribe1_offers"]:
                    resource = offer["resource"]
                    amount = offer["amount"]
                    if tribe1.take_shared_resource(resource, amount) > 0:
                        tribe2.add_shared_resource(resource, amount)

                # Tribe2 gives to tribe1
                for offer in agreement["tribe2_offers"]:
                    resource = offer["resource"]
                    amount = offer["amount"]
                    if tribe2.take_shared_resource(resource, amount) > 0:
                        tribe1.add_shared_resource(resource, amount)

    def _check_alliance_stability(self):
        """Check stability of existing alliances"""
        for tribe_name, allies in list(self.alliance_networks.items()):
            tribe = self.tribes.get(tribe_name)
            if not tribe:
                continue

            unstable_allies = []
            for ally_name in allies:
                if ally_name not in self.tribes:
                    unstable_allies.append(ally_name)
                    continue

                # Check if alliance should break
                relation_key = tuple(sorted([tribe_name, ally_name]))
                trust_level = self.diplomatic_relations[relation_key]["trust_level"]

                # Low trust can break alliances
                if trust_level < 0.3 and random.random() < 0.05:  # 5% chance when trust is low
                    unstable_allies.append(ally_name)
                    tribe.declare_rivalry(ally_name)
                    self.tribes[ally_name].declare_rivalry(tribe_name)

                    self.diplomatic_relations[relation_key]["alliance_status"] = False
                    self.logger.info(f"Alliance broken between {tribe_name} and {ally_name}")

            # Remove broken alliances
            for ally in unstable_allies:
                allies.discard(ally)

    def _generate_diplomatic_events(self):
        """Generate random diplomatic events"""
        if random.random() < 0.1:  # 10% chance per turn
            self._create_random_diplomatic_event()

    def _create_random_diplomatic_event(self):
        """Create a random diplomatic event"""
        from markov_behavior import make_markov_choice

        tribe_names = list(self.tribes.keys())
        if len(tribe_names) < 2:
            return

        tribe1_name, tribe2_name = random.sample(tribe_names, 2)
        tribe1 = self.tribes[tribe1_name]
        tribe2 = self.tribes[tribe2_name]

        event_types = [
            "cultural_exchange",
            "border_incident",
            "trade_opportunity",
            "alliance_proposal",
        ]

        # Use Markov choice for event type
        tribe1_context = {
            "traits": getattr(tribe1, "traits", []),
            "relationship": "neutral",  # Default, could be calculated
            "trust_level": 0.5,  # Default, could be calculated
            "recent_events": [],
        }

        event_type = make_markov_choice(
            event_types, "random_diplomatic_event", "diplomatic", tribe1_context
        )

        if event_type == "cultural_exchange":
            # Tribes exchange cultural elements
            if tribe1.culture["stories"] and tribe2.culture["stories"]:
                # Use Markov choice for story selection
                story1_options = tribe1.culture["stories"]
                story2_options = tribe2.culture["stories"]

                cultural_context = {
                    "cultural_focus": getattr(tribe1, "cultural_focus", "storytelling"),
                    "traits": getattr(tribe1, "traits", []),
                    "stability": "stable",
                    "season": "spring",
                }

                story_exchange = make_markov_choice(
                    story1_options, "story_sharing", "cultural", cultural_context
                )
                tribe2.culture["stories"].append(f"Story from {tribe1.name}: {story_exchange}")

                cultural_context["cultural_focus"] = getattr(
                    tribe2, "cultural_focus", "storytelling"
                )
                cultural_context["traits"] = getattr(tribe2, "traits", [])
                story_exchange = make_markov_choice(
                    story2_options, "story_sharing", "cultural", cultural_context
                )
                tribe1.culture["stories"].append(f"Story from {tribe2.name}: {story_exchange}")

                # Improve relations
                relation_key = tuple(sorted([tribe1_name, tribe2_name]))
                self.diplomatic_relations[relation_key]["trust_level"] += 0.05

                self.logger.info(f"Cultural exchange between {tribe1_name} and {tribe2_name}")

        elif event_type == "border_incident":
            # Minor border conflict
            relation_key = tuple(sorted([tribe1_name, tribe2_name]))
            self.diplomatic_relations[relation_key]["border_tension"] += 0.2
            self.diplomatic_relations[relation_key]["trust_level"] -= 0.1

            self.logger.info(f"Border incident between {tribe1_name} and {tribe2_name}")

        elif event_type == "trade_opportunity":
            # Initiate trade negotiation
            negotiation = {
                "initiator": tribe1_name,
                "target": tribe2_name,
                "type": "trade",
                "turns_remaining": random.randint(2, 4),
            }
            self.active_negotiations.append(negotiation)

        elif event_type == "alliance_proposal":
            # Propose alliance if relations are good
            relation_key = tuple(sorted([tribe1_name, tribe2_name]))
            if self.diplomatic_relations[relation_key]["trust_level"] > 0.6:
                negotiation = {
                    "initiator": tribe1_name,
                    "target": tribe2_name,
                    "type": "alliance",
                    "turns_remaining": random.randint(3, 5),
                }
                self.active_negotiations.append(negotiation)

    def initiate_negotiation(
        self, initiator: str, target: str, negotiation_type: str, **kwargs
    ) -> bool:
        """Initiate a diplomatic negotiation"""
        if initiator not in self.tribes or target not in self.tribes:
            return False

        negotiation = {
            "initiator": initiator,
            "target": target,
            "type": negotiation_type,
            "turns_remaining": kwargs.get("duration", random.randint(2, 5)),
            **kwargs,
        }

        self.active_negotiations.append(negotiation)
        self.logger.info(
            f"Diplomatic negotiation initiated: {initiator} → {target} ({negotiation_type})"
        )
        return True

    def arrange_trade_agreement(self, tribe1: Tribe, tribe2: Tribe) -> Dict:
        """Arrange a trade agreement between two tribes"""
        return self._establish_trade_agreement(tribe1, tribe2, {})

    def get_diplomatic_status(self, tribe1: Tribe, tribe2: Tribe) -> Dict:
        """Get diplomatic status between two tribes"""
        key = tuple(sorted([tribe1.name, tribe2.name]))
        return self.diplomatic_relations.get(key, {})

    def get_diplomacy_summary(self) -> Dict:
        """Get summary of current diplomatic state"""
        return {
            "active_negotiations": len(self.active_negotiations),
            "trade_agreements": len(self.trade_agreements),
            "alliance_networks": {
                tribe: list(allies) for tribe, allies in self.alliance_networks.items()
            },
            "high_tension_relations": [
                {"tribes": key, "tension": data["border_tension"]}
                for key, data in self.diplomatic_relations.items()
                if data["border_tension"] > 0.5
            ],
        }

    def update_tribes(self, tribes: Dict[str, Tribe]):
        """Update diplomacy system when tribes are added or removed"""
        self.tribes = tribes
        self._initialize_diplomacy()

    def add_tribe(self, tribe: Tribe):
        """Add a new tribe to the diplomacy system"""
        if tribe.name not in self.tribes:
            self.tribes[tribe.name] = tribe

        # Initialize relations with all existing tribes
        for existing_tribe_name in list(self.tribes.keys()):
            if existing_tribe_name != tribe.name:
                key = tuple(sorted([tribe.name, existing_tribe_name]))
                if key not in self.diplomatic_relations:
                    self.diplomatic_relations[key] = {
                        "trust_level": 0.5,
                        "trade_volume": 0,
                        "conflict_count": 0,
                        "alliance_status": False,
                        "last_interaction": None,
                        "border_tension": 0.0,
                    }

                    # Initialize reputation scores
                    if tribe.name not in self.reputation_scores:
                        self.reputation_scores[tribe.name] = {}
                    if existing_tribe_name not in self.reputation_scores:
                        self.reputation_scores[existing_tribe_name] = {}

                    self.reputation_scores[tribe.name][existing_tribe_name] = 0.5
                    self.reputation_scores[existing_tribe_name][tribe.name] = 0.5

                    # Initialize cultural influences
                    if tribe.name not in self.cultural_influences:
                        self.cultural_influences[tribe.name] = {}
                    if existing_tribe_name not in self.cultural_influences:
                        self.cultural_influences[existing_tribe_name] = {}

                    self.cultural_influences[tribe.name][existing_tribe_name] = 0.0
                    self.cultural_influences[existing_tribe_name][tribe.name] = 0.0

        # Duplicate function removed - keeping the first definition at line 1105
        """Generate random diplomatic events between tribes"""

        # Duplicate function removed - keeping the first definition at line 1136
        """Choose a random diplomatic event based on tribe relationship"""

    def _record_markov_learning(
        self, decision_type: str, context: str, action: str, outcome_success: float
    ):
        """Record learning feedback for Markov chains based on diplomatic outcomes."""
        try:
            from markov_behavior import global_tribal_markov

            global_tribal_markov.learn_from_outcome(decision_type, context, action, outcome_success)
            self.logger.debug(
                f"Markov learning recorded: {decision_type} '{context}' -> '{action}' (success: {outcome_success})"
            )
        except Exception as e:
            self.logger.error(f"Failed to record Markov learning: {e}")


def test_expanded_diplomatic_events():
    """Test the expanded diplomatic event system."""
    print("\n" + "=" * 60)
    print("🧪 TESTING EXPANDED DIPLOMATIC EVENTS")
    print("=" * 60)

    # Create test tribes
    from .tribe import Tribe
    from main import generate_faction_name

    pioneers_name = generate_faction_name("military")  # Generate a military-themed faction name
    tribe1 = Tribe(pioneers_name, "Mountain Valley")
    tribe2 = Tribe("Wildlife", "Dark Forest")
    tribe3 = Tribe("Predators", "Great Plains")

    tribes = {pioneers_name: tribe1, "Wildlife": tribe2, "Predators": tribe3}

    diplomacy = TribalDiplomacy(tribes)

    # Set up some initial relationships
    pioneers_wildlife_key = tuple(sorted([pioneers_name, "Wildlife"]))
    pioneers_predators_key = tuple(sorted([pioneers_name, "Predators"]))
    wildlife_predators_key = tuple(sorted(["Wildlife", "Predators"]))

    diplomacy.diplomatic_relations[pioneers_wildlife_key]["trust_level"] = 0.2  # Hostile
    diplomacy.diplomatic_relations[pioneers_predators_key]["trust_level"] = 0.7  # Friendly
    diplomacy.diplomatic_relations[wildlife_predators_key]["trust_level"] = 0.4  # Neutral-negative

    print("\n🏛️ Test Tribes:")
    print(
        f"  {pioneers_name} (Mountain Valley) - Relations: Wildlife: {diplomacy.diplomatic_relations[pioneers_wildlife_key]['trust_level']:.2f}, Predators: {diplomacy.diplomatic_relations[pioneers_predators_key]['trust_level']:.2f}"
    )
    print(
        f"  Wildlife (Dark Forest) - Relations: {pioneers_name}: {diplomacy.diplomatic_relations[pioneers_wildlife_key]['trust_level']:.2f}, Predators: {diplomacy.diplomatic_relations[wildlife_predators_key]['trust_level']:.2f}"
    )
    print(
        f"  Predators (Great Plains) - Relations: {pioneers_name}: {diplomacy.diplomatic_relations[pioneers_predators_key]['trust_level']:.2f}, Wildlife: {diplomacy.diplomatic_relations[wildlife_predators_key]['trust_level']:.2f}"
    )

    # Test 1: Generate random events between hostile tribes
    print(f"\n1️⃣ Testing random events between hostile tribes ({pioneers_name} vs Wildlife)...")
    for i in range(5):
        event = diplomacy._choose_random_event(pioneers_name, "Wildlife")
        if event:
            print(f"  Event {i+1}: {event.value}")
        else:
            print(f"  Event {i+1}: No event generated")

    # Test 2: Generate random events between friendly tribes
    print(f"\n2️⃣ Testing random events between friendly tribes ({pioneers_name} vs Predators)...")
    for i in range(5):
        event = diplomacy._choose_random_event(pioneers_name, "Predators")
        if event:
            print(f"  Event {i+1}: {event.value}")
        else:
            print(f"  Event {i+1}: No event generated")

    # Test 3: Process specific expanded events
    print("\n3️⃣ Testing specific expanded event processing...")

    # Festival invitation
    print("  Processing festival invitation...")
    diplomacy._process_festival_invitation_event(pioneers_name, "Wildlife")
    print(
        f"  Relations after festival: {diplomacy.diplomatic_relations[pioneers_wildlife_key]['trust_level']:.2f}"
    )

    # Resource theft
    print("  Processing resource theft...")
    diplomacy._process_resource_theft_event("Wildlife", pioneers_name)
    print(
        f"  Relations after theft: {diplomacy.diplomatic_relations[pioneers_wildlife_key]['trust_level']:.2f}"
    )

    # Cultural offense
    print("  Processing cultural offense...")
    diplomacy._process_cultural_offense_event("Predators", "Wildlife")
    print(
        f"  Relations after offense: {diplomacy.diplomatic_relations[wildlife_predators_key]['trust_level']:.2f}"
    )

    # Leader mediation
    print("  Processing leader mediation...")
    diplomacy._process_leader_mediation_event(
        "Pioneers", ("Wildlife", "Predators")
    )  # Pioneers mediating dispute between Wildlife and Predators
    print(
        f"  Relations after mediation: {diplomacy.diplomatic_relations[pioneers_wildlife_key]['trust_level']:.2f}"
    )

    # Test 4: Generate random diplomatic events
    print("\n4️⃣ Testing random diplomatic event generation...")
    events_generated = []
    for i in range(20):  # Try multiple times to get some events
        events = diplomacy.generate_random_diplomatic_events()
        if events:
            events_generated.extend(events)

    if events_generated:
        print(f"  Generated {len(events_generated)} random events:")
        for event in events_generated:
            print(f"    {event['tribe1']} → {event['tribe2']}: {event['event'].value}")
    else:
        print("  No random events generated (this is normal due to 5% chance per attempt)")

    print("\n✅ Expanded diplomatic events test completed!")


if __name__ == "__main__":
    # Run expanded diplomatic events test
    test_expanded_diplomatic_events()
