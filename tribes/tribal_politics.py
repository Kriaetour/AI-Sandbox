import random
import logging
from typing import Dict, List
from .tribe import Tribe, TribalRole
from .tribal_roles import TribalRoleManager


class TribalPolitics:
    """Manages internal tribal politics and power dynamics"""

    def __init__(self, tribe: Tribe, role_manager: TribalRoleManager):
        self.tribe = tribe
        self.role_manager = role_manager
        self.logger = logging.getLogger(f"TribalPolitics.{tribe.name}")

        # Political state
        self.leadership_challenges: List[Dict] = []  # Pending leadership challenges
        self.resource_disputes: List[Dict] = []  # Resource allocation conflicts
        self.power_struggles: Dict[str, float] = {}  # NPC ID -> power level
        self.social_status: Dict[str, float] = {}  # NPC ID -> social standing (0-1)
        self.internal_conflicts: List[Dict] = []  # Ongoing internal disputes

        # Political history
        self.political_events: List[Dict] = []
        self.succession_history: List[Dict] = []

        self._initialize_social_status()

    def _initialize_social_status(self):
        """Initialize social status for all tribe members"""
        for npc_id in self.tribe.member_ids:
            # Base status depends on role
            role = self.tribe.social_roles.get(npc_id)
            if role == TribalRole.LEADER:
                base_status = 0.9
            elif role == TribalRole.SHAMAN:
                base_status = 0.8
            elif role in [TribalRole.WARRIOR, TribalRole.HUNTER]:
                base_status = 0.6
            elif role == TribalRole.CRAFTER:
                base_status = 0.5
            else:
                base_status = 0.4

            # Add some randomization
            self.social_status[npc_id] = base_status + random.uniform(-0.1, 0.1)
            self.social_status[npc_id] = max(0.1, min(1.0, self.social_status[npc_id]))

            # Initialize power levels
            self.power_struggles[npc_id] = self.social_status[npc_id] * 0.5

    def process_political_turn(self):
        """Process one turn of internal tribal politics"""
        self._check_leadership_stability()
        self._handle_resource_disputes()
        self._process_power_struggles()
        self._update_social_dynamics()
        self._resolve_internal_conflicts()

    def _check_leadership_stability(self):
        """Check if current leadership is stable or faces challenges"""
        if not self.tribe.leader_id:
            return

        leader_status = self.social_status.get(self.tribe.leader_id, 0.5)
        tribe_wellbeing = self.tribe.get_wellbeing_score()

        # Leadership becomes unstable if status is low or tribe is struggling
        instability_factor = (1.0 - leader_status) + (1.0 - tribe_wellbeing) * 0.5

        if instability_factor > 0.7 and random.random() < 0.1:  # 10% chance when unstable
            self._initiate_leadership_challenge()

    def _initiate_leadership_challenge(self):
        """Initiate a leadership challenge"""
        if not self.tribe.leader_id:
            return

        # Find potential challengers (high status, warrior/hunter roles preferred)
        challengers = []
        for npc_id, status in self.social_status.items():
            if npc_id != self.tribe.leader_id and status > 0.6:
                role = self.tribe.social_roles.get(npc_id)
                if role in [TribalRole.WARRIOR, TribalRole.HUNTER, TribalRole.SHAMAN]:
                    challengers.append((npc_id, status))

        if not challengers:
            return

        # Select challenger
        challenger_id, challenger_status = max(challengers, key=lambda x: x[1])

        challenge = {
            "challenger": challenger_id,
            "incumbent": self.tribe.leader_id,
            "reason": random.choice(
                [
                    "leadership weakness",
                    "resource mismanagement",
                    "failed diplomacy",
                    "cultural disrespect",
                ]
            ),
            "support_ratio": challenger_status / self.social_status.get(self.tribe.leader_id, 0.5),
            "turns_remaining": random.randint(2, 5),
        }

        self.leadership_challenges.append(challenge)
        self.logger.info(
            f"Leadership challenge initiated: {challenger_id} vs {self.tribe.leader_id}"
        )

    def _handle_resource_disputes(self):
        """Handle disputes over resource allocation"""
        # Check if resources are scarce
        total_resources = sum(self.tribe.shared_resources.values())
        resource_per_person = total_resources / max(len(self.tribe.member_ids), 1)

        if resource_per_person < 15 and random.random() < 0.15:  # 15% chance when scarce
            # Create resource dispute
            dispute_types = [
                "food_hoarding",
                "resource_wasting",
                "unequal_sharing",
                "prioritization_conflict",
            ]
            dispute_type = random.choice(dispute_types)

            # Find involved parties
            members = list(self.tribe.member_ids)
            if len(members) >= 2:
                involved = random.sample(members, min(3, len(members)))

                dispute = {
                    "type": dispute_type,
                    "involved": involved,
                    "severity": random.uniform(0.3, 0.8),
                    "turns_remaining": random.randint(1, 3),
                }

                self.resource_disputes.append(dispute)
                self.logger.info(f"Resource dispute created: {dispute_type} involving {involved}")

    def _process_power_struggles(self):
        """Process ongoing power struggles between tribe members"""
        # Power levels change based on contributions and social interactions
        for npc_id in list(self.power_struggles.keys()):
            if npc_id not in self.tribe.member_ids:
                continue

            # Base change from social status
            status_change = (self.social_status[npc_id] - 0.5) * 0.05

            # Random events can affect power
            if random.random() < 0.1:  # 10% chance of power event
                event_type = random.choice(["gain", "loss", "stable"])
                if event_type == "gain":
                    status_change += random.uniform(0.05, 0.15)
                    self.logger.debug(f"{npc_id} gained power through successful action")
                elif event_type == "loss":
                    status_change -= random.uniform(0.05, 0.15)
                    self.logger.debug(f"{npc_id} lost power due to mistake")

            # Update power level
            self.power_struggles[npc_id] += status_change
            self.power_struggles[npc_id] = max(0.0, min(1.0, self.power_struggles[npc_id]))

    def _update_social_dynamics(self):
        """Update social status based on various factors"""
        for npc_id in list(self.social_status.keys()):
            if npc_id not in self.tribe.member_ids:
                continue

            role = self.tribe.social_roles.get(npc_id)
            power_level = self.power_struggles.get(npc_id, 0.5)

            # Social status influenced by role, power, and tribal wellbeing
            role_multiplier = {
                TribalRole.LEADER: 1.2,
                TribalRole.SHAMAN: 1.1,
                TribalRole.WARRIOR: 1.0,
                TribalRole.HUNTER: 0.9,
                TribalRole.GATHERER: 0.8,
                TribalRole.CRAFTER: 0.9,
            }.get(role, 0.8)

            target_status = power_level * role_multiplier
            target_status = max(0.1, min(1.0, target_status))

            # Gradually move toward target status
            current_status = self.social_status[npc_id]
            change = (target_status - current_status) * 0.1  # 10% adjustment per turn
            self.social_status[npc_id] += change

    def _resolve_internal_conflicts(self):
        """Resolve ongoing internal conflicts"""
        # Resolve leadership challenges
        for challenge in self.leadership_challenges[:]:
            challenge["turns_remaining"] -= 1

            if challenge["turns_remaining"] <= 0:
                self._resolve_leadership_challenge(challenge)
                self.leadership_challenges.remove(challenge)

        # Resolve resource disputes
        for dispute in self.resource_disputes[:]:
            dispute["turns_remaining"] -= 1

            if dispute["turns_remaining"] <= 0:
                self._resolve_resource_dispute(dispute)
                self.resource_disputes.remove(dispute)

    def _resolve_leadership_challenge(self, challenge: Dict):
        """Resolve a leadership challenge"""
        challenger_status = self.social_status.get(challenge["challenger"], 0.5)
        incumbent_status = self.social_status.get(challenge["incumbent"], 0.5)

        # Challenge succeeds if challenger has higher status and good support
        success_chance = (challenger_status / max(incumbent_status, 0.1)) * challenge[
            "support_ratio"
        ]

        if random.random() < success_chance:
            # Leadership change
            old_leader = self.tribe.leader_id
            self.tribe.leader_id = challenge["challenger"]
            self.tribe.social_roles[challenge["challenger"]] = TribalRole.LEADER

            # Record succession
            succession_event = {
                "old_leader": old_leader,
                "new_leader": challenge["challenger"],
                "reason": challenge["reason"],
                "method": "challenge",
                "turn": len(self.succession_history),
            }
            self.succession_history.append(succession_event)

            self.logger.info(
                f"Leadership change: {old_leader} → {challenge['challenger']} via challenge"
            )
        else:
            # Challenge fails - reduce challenger status
            self.social_status[challenge["challenger"]] *= 0.9
            self.logger.info(f"Leadership challenge by {challenge['challenger']} failed")

    def _resolve_resource_dispute(self, dispute: Dict):
        """Resolve a resource dispute"""
        # Disputes generally resolve with some compromise
        resolution_type = random.choice(["compromise", "escalation", "resolution"])

        if resolution_type == "compromise":
            # Reduce severity and improve relations slightly
            for npc_id in dispute["involved"]:
                if npc_id in self.social_status:
                    self.social_status[npc_id] += 0.05
            self.logger.debug("Resource dispute resolved through compromise")
        elif resolution_type == "escalation":
            # Create internal conflict
            conflict = {
                "type": "resource_escalation",
                "involved": dispute["involved"],
                "severity": dispute["severity"] * 1.2,
                "turns_remaining": random.randint(3, 6),
            }
            self.internal_conflicts.append(conflict)
            self.logger.info("Resource dispute escalated to internal conflict")
        else:
            # Clean resolution
            self.logger.debug("Resource dispute resolved peacefully")

    def get_political_summary(self) -> Dict:
        """Get summary of current political state"""
        return {
            "leader_stability": (
                self.social_status.get(self.tribe.leader_id, 0.5) if self.tribe.leader_id else 0.0
            ),
            "active_challenges": len(self.leadership_challenges),
            "resource_disputes": len(self.resource_disputes),
            "internal_conflicts": len(self.internal_conflicts),
            "power_distribution": dict(
                sorted(self.power_struggles.items(), key=lambda x: x[1], reverse=True)[:5]
            ),
            "social_hierarchy": dict(
                sorted(self.social_status.items(), key=lambda x: x[1], reverse=True)[:5]
            ),
        }
