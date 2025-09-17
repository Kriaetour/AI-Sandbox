import random
import logging
from typing import Dict, List, Optional, Any
from .tribe import Tribe, TribalRole
from factions.faction import Faction


class TribalRoleBehavior:
    """Defines behavior patterns for different tribal roles"""

    ROLE_BEHAVIORS = {
        TribalRole.LEADER: {
            "primary_focus": "coordination",
            "decision_weight": 0.8,
            "social_priority": 0.9,
            "risk_tolerance": 0.6,
            "activities": ["organize", "negotiate", "plan", "inspire"],
            "preferred_actions": [
                "form_alliance",
                "negotiate_truce",
                "build_structure",
            ],
            "contributions": {
                "tribal": {
                    "organization": 1,  # High organizational contribution
                    "morale": 1,  # Boosts tribal morale
                    "diplomacy": 1,  # Handles external relations
                    "planning": 1,  # Strategic planning
                    "unity": 1,  # Maintains tribal unity
                },
                "faction": {
                    "diplomacy": 1,  # Represents tribe in faction politics
                    "leadership": 1,  # Provides leadership to faction
                    "influence": 1,  # Increases faction influence
                    "stability": 1,  # Contributes to faction stability
                },
            },
        },
        TribalRole.SHAMAN: {
            "primary_focus": "spiritual",
            "decision_weight": 0.7,
            "social_priority": 0.8,
            "risk_tolerance": 0.4,
            "activities": ["heal", "ritual", "divine", "teach"],
            "preferred_actions": [
                "spiritual_guidance",
                "healing_ceremony",
                "storytelling",
            ],
            "contributions": {
                "tribal": {
                    "health": 1,  # Heals tribe members
                    "morale": 1,  # Spiritual guidance
                    "culture": 1,  # Develops tribal culture
                    "wisdom": 1,  # Provides wisdom and guidance
                    "unity": 1,  # Spiritual unity
                },
                "faction": {
                    "culture": 1,  # Contributes to faction culture
                    "healing": 1,  # Provides healing services
                    "wisdom": 1,  # Shares spiritual wisdom
                    "influence": 1,  # Moderate spiritual influence
                },
            },
        },
        TribalRole.HUNTER: {
            "primary_focus": "hunting",
            "decision_weight": 0.6,
            "social_priority": 0.5,
            "risk_tolerance": 0.8,
            "activities": ["track", "hunt", "scout", "forage"],
            "preferred_actions": ["hunt_prey", "scout_territory", "gather_food"],
            "contributions": {
                "tribal": {
                    "food": 1,  # Primary food source
                    "scouting": 1,  # Explores new areas
                    "resources": 1,  # Gathers animal products
                    "defense": 1,  # Protects from wildlife
                    "survival": 1,  # Hunting survival skills
                },
                "faction": {
                    "food": 1,  # Supplies faction with food
                    "resources": 1,  # Animal products and materials
                    "expansion": 1,  # Helps expand faction territory
                    "military": 0,  # Minor military contribution
                },
            },
        },
        TribalRole.GATHERER: {
            "primary_focus": "gathering",
            "decision_weight": 0.5,
            "social_priority": 0.6,
            "risk_tolerance": 0.3,
            "activities": ["collect", "forage", "craft", "preserve"],
            "preferred_actions": ["gather_resources", "craft_tools", "preserve_food"],
            "contributions": {
                "tribal": {
                    "resources": 1,  # Gathers wood, stone, herbs
                    "food": 1,  # Forages for food
                    "crafting": 1,  # Basic crafting
                    "preservation": 1,  # Preserves food/resources
                    "sustainability": 1,  # Sustainable gathering
                },
                "faction": {
                    "resources": 1,  # Supplies raw materials
                    "food": 1,  # Supplementary food source
                    "crafting": 0,  # Basic crafted goods
                    "sustainability": 1,  # Promotes sustainable practices
                },
            },
        },
        TribalRole.WARRIOR: {
            "primary_focus": "defense",
            "decision_weight": 0.7,
            "social_priority": 0.4,
            "risk_tolerance": 0.9,
            "activities": ["guard", "fight", "patrol", "train"],
            "preferred_actions": ["defend_territory", "raid_rivals", "train_combat"],
            "contributions": {
                "tribal": {
                    "defense": 1,  # Primary defense
                    "security": 1,  # Protects tribe
                    "territory": 1,  # Expands/maintains territory
                    "training": 1,  # Trains others in combat
                    "courage": 1,  # Provides courage and protection
                },
                "faction": {
                    "military": 1,  # Strong military contribution
                    "defense": 1,  # Protects faction interests
                    "expansion": 1,  # Helps expand faction territory
                    "influence": 1,  # Military influence
                },
            },
        },
        TribalRole.CRAFTER: {
            "primary_focus": "crafting",
            "decision_weight": 0.6,
            "social_priority": 0.7,
            "risk_tolerance": 0.4,
            "activities": ["build", "repair", "create", "improve"],
            "preferred_actions": ["build_structure", "craft_tools", "repair_equipment"],
            "contributions": {
                "tribal": {
                    "structures": 0.8,  # High contribution to building
                    "tools": 0.9,  # Creates tools for others
                    "resources": 0.3,  # Moderate resource gathering
                    "culture": 0.4,  # Creates cultural items
                    "defense": 0.2,  # Minor defensive contributions
                },
                "faction": {
                    "resources": 0.4,  # Contributes crafted goods
                    "technology": 0.6,  # Advances faction technology
                    "wealth": 0.5,  # Creates tradeable goods
                    "influence": 0.3,  # Moderate influence gain
                },
            },
        },
    }

    @staticmethod
    def get_role_behavior(role: TribalRole) -> Dict:
        """Get behavior configuration for a role"""
        return TribalRoleBehavior.ROLE_BEHAVIORS.get(role, {})

    @staticmethod
    def get_role_contributions(role: TribalRole) -> Dict:
        """Get contribution metrics for a role"""
        behavior = TribalRoleBehavior.get_role_behavior(role)
        return behavior.get("contributions", {})

    @staticmethod
    def calculate_tribal_contribution(
        role: TribalRole, efficiency: float = 1.0
    ) -> Dict[str, float]:
        """Calculate tribal contribution for a role"""
        contributions = TribalRoleBehavior.get_role_contributions(role)
        tribal_contribs = contributions.get("tribal", {})

        # Apply efficiency modifier (based on experience, health, etc.)
        result = {}
        for aspect, base_value in tribal_contribs.items():
            result[aspect] = base_value * efficiency

        return result

    @staticmethod
    def calculate_faction_contribution(
        role: TribalRole, efficiency: float = 1.0
    ) -> Dict[str, float]:
        """Calculate faction contribution for a role"""
        contributions = TribalRoleBehavior.get_role_contributions(role)
        faction_contribs = contributions.get("faction", {})

        # Apply efficiency modifier
        result = {}
        for aspect, base_value in faction_contribs.items():
            result[aspect] = base_value * efficiency

        return result

    @staticmethod
    def apply_tribal_contribution(
        tribe: "Tribe", role: TribalRole, npc_id: str, efficiency: float = 1.0
    ):
        """Apply a role's contribution to tribal wellbeing"""
        contributions = TribalRoleBehavior.calculate_tribal_contribution(role, efficiency)

        # Apply contributions to tribe
        for aspect, amount in contributions.items():
            if aspect == "food":
                tribe.add_shared_resource("food", round(amount * 2))  # Food contribution
            elif aspect == "resources":
                tribe.add_shared_resource("wood", round(amount * 1.5))
                tribe.add_shared_resource("stone", round(amount * 1.5))
                tribe.add_shared_resource("herbs", round(amount))
            elif aspect == "structures":
                # Contribute to building structures (this would be used when building)
                pass  # Handled by build_structure method
            elif aspect == "health":
                # Contribute to tribal health (reduce sickness, improve recovery)
                pass  # Would integrate with health system
            elif aspect == "morale":
                # Boost tribal morale
                pass  # Would affect tribal events and cohesion
            elif aspect == "culture":
                # Contribute to cultural development
                if random.random() < amount * 0.1:  # Chance to add cultural element
                    possible_stories = [
                        f"{npc_id} shared wisdom about the ancient ways",
                        f"{npc_id} created a new tribal tradition",
                        f"{npc_id} discovered a sacred site",
                    ]
                    tribe.culture["stories"].append(random.choice(possible_stories))
            elif aspect == "defense":
                # Contribute to defensive capabilities
                pass  # Would affect territory defense
            elif aspect == "scouting":
                # Contribute to exploration
                if random.random() < amount * 0.2:  # Chance to discover new territory
                    # This would integrate with territory expansion
                    pass

        # Record contribution in tribal memory
        tribe.add_tribal_memory(
            "role_contribution",
            {
                "npc_id": npc_id,
                "role": role.value,
                "contributions": contributions,
                "efficiency": efficiency,
            },
        )

    @staticmethod
    def apply_faction_contribution(
        faction: "Faction", role: TribalRole, npc_id: str, efficiency: float = 1.0
    ):
        """Apply a role's contribution to faction wellbeing"""
        contributions = TribalRoleBehavior.calculate_faction_contribution(role, efficiency)

        # Apply contributions to faction
        for aspect, amount in contributions.items():
            if aspect == "food":
                faction.add_resource("food", round(amount * 3))
            elif aspect == "resources":
                faction.add_resource("Wood", round(amount * 2))
                faction.add_resource("Ore", round(amount * 1.5))
            elif aspect == "wealth":
                # Would contribute to faction wealth/economy
                pass  # Could add wealth resource
            elif aspect == "military":
                # Contribute to faction military strength
                pass  # Would affect faction combat capabilities
            elif aspect == "diplomacy":
                # Improve faction diplomatic relations
                for other_faction in faction.relationships.keys():
                    if faction.relationships[other_faction] < 0.5:  # If not hostile
                        faction.update_opinion(other_faction, amount * 0.1)
            elif aspect == "influence":
                # Increase faction influence
                pass  # Would affect faction politics
            elif aspect == "technology":
                # Advance faction technology
                pass  # Would unlock new capabilities
            elif aspect == "culture":
                # Contribute to faction culture
                if random.random() < amount * 0.05:  # Chance to add cultural element
                    faction.add_saying_memory(f"Wisdom from {npc_id}: The spirits guide our people")
            elif aspect == "healing":
                # Provide healing services to faction
                pass  # Would affect faction member health
            elif aspect == "expansion":
                # Help expand faction territory
                pass  # Would contribute to territory growth
            elif aspect == "leadership":
                # Provide leadership to faction
                pass  # Would affect faction organization
            elif aspect == "stability":
                # Contribute to faction stability
                pass  # Would reduce internal conflicts

        # Record contribution in faction memory
        faction.add_event_memory(f"{npc_id} ({role.value}) contributed to faction wellbeing")

    @staticmethod
    def decide_action(
        npc_id: str, role: TribalRole, tribe: Tribe, available_actions: List[str]
    ) -> str:
        """Decide what action an NPC should take based on their role"""

        behavior = TribalRoleBehavior.get_role_behavior(role)
        if not behavior:
            return random.choice(available_actions) if available_actions else "idle"

        # Weight actions based on role preferences
        preferred_actions = behavior.get("preferred_actions", [])
        action_weights = {}

        for action in available_actions:
            weight = 1.0
            if action in preferred_actions:
                weight *= 3.0  # Strong preference for role-specific actions

            # Consider tribal needs
            if action == "hunt_prey" and tribe.shared_resources.get("food", 0) < 20:
                weight *= 2.0
            elif action == "gather_resources" and tribe.shared_resources.get("wood", 0) < 15:
                weight *= 2.0
            elif action == "defend_territory" and tribe.rivalries:
                weight *= 2.0
            elif action == "build_structure" and len(tribe.structures) < 3:
                weight *= 1.5

            action_weights[action] = weight

        # Select action based on weights
        actions = list(action_weights.keys())
        weights = list(action_weights.values())

        if actions:
            return random.choices(actions, weights=weights, k=1)[0]

        return "idle"

    @staticmethod
    def get_role_dialogue(role: TribalRole, intent: str) -> str:
        """Get role-specific dialogue"""

        dialogue_patterns = {
            TribalRole.LEADER: {
                "greeting": [
                    "Welcome to our tribe!",
                    "I lead these people.",
                    "Our tribe is strong together.",
                ],
                "command": [
                    "Follow my lead!",
                    "We must act as one!",
                    "Listen to your leader!",
                ],
                "inspiration": [
                    "Together we are unstoppable!",
                    "Our spirits guide us!",
                    "For the tribe!",
                ],
            },
            TribalRole.SHAMAN: {
                "greeting": [
                    "The spirits welcome you.",
                    "I commune with the ancestors.",
                    "The spirits speak to me.",
                ],
                "guidance": [
                    "The spirits show me the way.",
                    "Listen to the ancient wisdom.",
                    "The ancestors guide our path.",
                ],
                "healing": [
                    "I will heal your wounds.",
                    "The spirits will mend you.",
                    "Ancient remedies will help.",
                ],
            },
            TribalRole.HUNTER: {
                "greeting": [
                    "Fresh from the hunt!",
                    "The wild is my home.",
                    "I track the greatest prey.",
                ],
                "success": [
                    "The hunt was good!",
                    "Fresh meat for the tribe!",
                    "I bring food for all!",
                ],
                "scouting": [
                    "I found their tracks.",
                    "Danger approaches.",
                    "The wild speaks to me.",
                ],
            },
            TribalRole.GATHERER: {
                "greeting": [
                    "I bring the earth's gifts.",
                    "The forest provides.",
                    "Nature sustains us.",
                ],
                "collection": [
                    "I found these herbs.",
                    "The berries are ripe.",
                    "Wood for our fires.",
                ],
                "crafting": [
                    "I made this tool.",
                    "Carefully crafted.",
                    "Useful for the tribe.",
                ],
            },
            TribalRole.WARRIOR: {
                "greeting": [
                    "Ready for battle!",
                    "I protect the tribe.",
                    "Strength and courage!",
                ],
                "defense": [
                    "None shall pass!",
                    "I defend our lands!",
                    "Our territory is sacred!",
                ],
                "threat": [
                    "Feel our wrath!",
                    "We are warriors!",
                    "Challenge us at your peril!",
                ],
            },
            TribalRole.CRAFTER: {
                "greeting": [
                    "I build for the tribe.",
                    "My hands create.",
                    "Craftsman at your service.",
                ],
                "creation": ["A fine tool!", "Built to last.", "Useful for all."],
                "improvement": [
                    "I can make this better.",
                    "Let me strengthen it.",
                    "Quality craftsmanship.",
                ],
            },
        }

        role_dialogue = dialogue_patterns.get(role, {})
        if intent in role_dialogue:
            return random.choice(role_dialogue[intent])

        return f"I am a {role.value}."

        return f"I am a {role.value}."


class TribalRoleManager:
    """Manages role assignments and transitions within tribes"""

    def __init__(self, tribe: Tribe):
        self.tribe = tribe
        self.logger = logging.getLogger(f"TribalRoleManager.{tribe.name}")
        self.activities_organized_this_turn = (
            False  # Prevent multiple leaders organizing activities
        )

    def assign_leadership_roles(self, npcs: Dict[str, Any]):
        """Assign leadership roles to NPCs based on their tribal roles and influence."""
        # Get NPCs with leadership potential
        leader_candidates = []
        shaman_candidates = []
        warrior_captain_candidates = []
        elder_candidates = []

        for npc_id, npc in npcs.items():
            if npc_id in self.tribe.member_ids:
                tribal_role = self.tribe.social_roles.get(npc_id)

                # Calculate leadership potential based on role and NPC attributes
                leadership_potential = 0.0

                if tribal_role == TribalRole.LEADER:
                    leadership_potential = 1.0
                    leader_candidates.append((npc_id, leadership_potential))
                elif tribal_role == TribalRole.SHAMAN:
                    leadership_potential = 0.8
                    shaman_candidates.append((npc_id, leadership_potential))
                elif tribal_role == TribalRole.WARRIOR:
                    leadership_potential = 0.6
                    warrior_captain_candidates.append((npc_id, leadership_potential))
                elif hasattr(npc, "personality") and npc.personality == "wise":
                    leadership_potential = 0.7
                    elder_candidates.append((npc_id, leadership_potential))

        # Assign leadership roles to top candidates
        if leader_candidates:
            leader_id, _ = max(leader_candidates, key=lambda x: x[1])
            if leader_id in npcs:
                npcs[leader_id].set_leadership_role("leader", influence_multiplier=1.2)

        if shaman_candidates:
            shaman_id, _ = max(shaman_candidates, key=lambda x: x[1])
            if shaman_id in npcs:
                npcs[shaman_id].set_leadership_role("shaman", influence_multiplier=1.1)

        if warrior_captain_candidates:
            captain_id, _ = max(warrior_captain_candidates, key=lambda x: x[1])
            if captain_id in npcs:
                npcs[captain_id].set_leadership_role("warrior_captain", influence_multiplier=1.0)

        if elder_candidates:
            elder_id, _ = max(elder_candidates, key=lambda x: x[1])
            if elder_id in npcs:
                npcs[elder_id].set_leadership_role("elder", influence_multiplier=0.9)

        self.logger.info(f"Assigned leadership roles for tribe {self.tribe.name}")

    def get_tribal_leaders(self, npcs: Dict[str, Any]) -> List[Any]:
        """Get list of NPCs with leadership roles in this tribe."""
        leaders = []
        for npc_id in self.tribe.member_ids:
            if (
                npc_id in npcs
                and hasattr(npcs[npc_id], "leadership_role")
                and npcs[npc_id].leadership_role
            ):
                leaders.append(npcs[npc_id])
        return leaders

    def assign_role(self, npc_id: str, role: TribalRole):
        """Assign a role to an NPC"""
        self.tribe.social_roles[npc_id] = role

    def reassign_roles(self):
        """Reassign roles based on tribal needs and balance surpluses"""

        # Count current roles
        role_counts = {}
        for npc_id, role in self.tribe.social_roles.items():
            role_counts[role] = role_counts.get(role, 0) + 1

        # Define role requirements and ideal ratios
        min_roles = {
            TribalRole.LEADER: 1,
            TribalRole.SHAMAN: 1,
            TribalRole.HUNTER: max(1, len(self.tribe.member_ids) // 4),
            TribalRole.GATHERER: max(1, len(self.tribe.member_ids) // 4),
            TribalRole.WARRIOR: max(1, len(self.tribe.member_ids) // 6),
            TribalRole.CRAFTER: max(1, len(self.tribe.member_ids) // 6),
        }

        # Ideal ratios (as percentages of total members)
        ideal_ratios = {
            TribalRole.LEADER: 0.1,  # 10% leaders
            TribalRole.SHAMAN: 0.1,  # 10% shamans
            TribalRole.HUNTER: 0.25,  # 25% hunters
            TribalRole.GATHERER: 0.25,  # 25% gatherers
            TribalRole.WARRIOR: 0.15,  # 15% warriors
            TribalRole.CRAFTER: 0.15,  # 15% crafters
        }

        total_members = len(self.tribe.member_ids)

        # Phase 1: Ensure minimum requirements are met
        for role, min_count in min_roles.items():
            current_count = role_counts.get(role, 0)
            if current_count < min_count:
                # Find NPCs without roles or reassign from less critical roles
                candidates = []
                for npc_id in self.tribe.member_ids:
                    if npc_id not in self.tribe.social_roles:
                        candidates.append(npc_id)
                    elif self.tribe.social_roles[npc_id] not in min_roles:
                        candidates.append(npc_id)

                # If still not enough, reassign from roles that have surplus
                if len(candidates) < (min_count - current_count):
                    surplus_candidates = []
                    for role_check, count in role_counts.items():
                        if (
                            role_check != role and count > min_roles.get(role_check, 0) + 1
                        ):  # +1 buffer
                            # Find NPCs in this surplus role
                            for npc_id in self.tribe.member_ids:
                                if self.tribe.social_roles.get(npc_id) == role_check:
                                    surplus_candidates.append((npc_id, role_check))

                    # Sort by how far over minimum they are (reassign from biggest surpluses first)
                    surplus_candidates.sort(
                        key=lambda x: role_counts[x[1]] - min_roles.get(x[1], 0),
                        reverse=True,
                    )
                    candidates.extend([npc_id for npc_id, _ in surplus_candidates])

                for _ in range(min_count - current_count):
                    if candidates:
                        npc_id = candidates.pop(
                            0
                        )  # Take from front (unassigned first, then surpluses)
                        old_role = self.tribe.social_roles.get(npc_id)
                        self.assign_role(npc_id, role)

                        if old_role:
                            self.tribe.add_tribal_memory(
                                "role_reassignment",
                                {
                                    "npc_id": npc_id,
                                    "old_role": old_role.value,
                                    "new_role": role.value,
                                    "reason": "minimum_requirement",
                                },
                            )

        # Phase 2: Balance surpluses and deficits for optimal tribal function
        # Recount after minimum requirements
        role_counts = {}
        for npc_id, role in self.tribe.social_roles.items():
            role_counts[role] = role_counts.get(role, 0) + 1

        # Calculate ideal counts
        ideal_counts = {}
        for role, ratio in ideal_ratios.items():
            ideal_counts[role] = max(min_roles.get(role, 1), int(total_members * ratio))

        # Find surplus and deficit roles
        surplus_roles = []
        deficit_roles = []

        for role in TribalRole:
            current = role_counts.get(role, 0)
            ideal = ideal_counts.get(role, 0)
            min_req = min_roles.get(role, 0)

            if current > ideal + 1:  # Surplus (more than ideal + buffer)
                surplus_roles.append((role, current - ideal))
            elif current < ideal and current >= min_req:  # Deficit but above minimum
                deficit_roles.append((role, ideal - current))

        # Sort surpluses by amount (biggest first) and deficits by need
        surplus_roles.sort(key=lambda x: x[1], reverse=True)
        deficit_roles.sort(key=lambda x: x[1], reverse=True)

        # Reassign from surpluses to deficits
        reassignment_count = 0
        max_reassignments = total_members // 4  # Limit reassignments to prevent chaos

        for deficit_role, deficit_amount in deficit_roles:
            if reassignment_count >= max_reassignments:
                break

            for surplus_role, surplus_amount in surplus_roles:
                if surplus_amount <= 0 or reassignment_count >= max_reassignments:
                    continue

                # Find NPCs in surplus role
                surplus_npcs = [
                    npc_id
                    for npc_id in self.tribe.member_ids
                    if self.tribe.social_roles.get(npc_id) == surplus_role
                ]

                # Reassign up to the deficit amount or available surplus
                reassign_count = min(deficit_amount, surplus_amount, len(surplus_npcs))

                for _ in range(reassign_count):
                    if surplus_npcs:
                        npc_id = random.choice(surplus_npcs)
                        surplus_npcs.remove(npc_id)

                        old_role = self.tribe.social_roles[npc_id]
                        self.assign_role(npc_id, deficit_role)

                        self.tribe.add_tribal_memory(
                            "role_rebalancing",
                            {
                                "npc_id": npc_id,
                                "old_role": old_role.value,
                                "new_role": deficit_role.value,
                                "reason": "tribal_balance",
                            },
                        )

                        reassignment_count += 1
                        deficit_amount -= 1
                        surplus_amount -= 1

                        if deficit_amount <= 0:
                            break

                # Update surplus amount
                surplus_roles = [
                    (r, amt if r != surplus_role else surplus_amount) for r, amt in surplus_roles
                ]

                if deficit_amount <= 0:
                    break

    def promote_member(self, npc_id: str, new_role: TribalRole):
        """Promote an NPC to a higher role"""
        if npc_id in self.tribe.member_ids:
            old_role = self.tribe.social_roles.get(npc_id)
            self.tribe.social_roles[npc_id] = new_role

            # Record promotion in tribal memory
            self.tribe.add_tribal_memory(
                "role_change",
                {
                    "npc_id": npc_id,
                    "old_role": old_role.value if old_role else None,
                    "new_role": new_role.value,
                    "type": "promotion",
                },
            )

    def get_role_distribution(self) -> Dict[TribalRole, int]:
        """Get current role distribution in the tribe"""
        distribution = {}
        for role in TribalRole:
            distribution[role] = 0

        for npc_id, role in self.tribe.social_roles.items():
            distribution[role] += 1

        return distribution

    def get_unassigned_members(self) -> List[str]:
        """Get list of tribe members without assigned roles"""
        return [npc_id for npc_id in self.tribe.member_ids if npc_id not in self.tribe.social_roles]

    def process_role_contributions(self, faction: Optional["Faction"] = None):
        """Process contributions from all tribal roles to tribal and faction wellbeing"""
        for npc_id, role in self.tribe.social_roles.items():
            # Calculate efficiency based on tribal wellbeing and random factors
            base_efficiency = 0.7 + (random.random() * 0.3)  # 0.7-1.0 base efficiency
            wellbeing_modifier = (
                self.tribe.get_wellbeing_score() * 0.3
            )  # Wellbeing affects efficiency
            efficiency = min(1.0, base_efficiency + wellbeing_modifier)

            # Apply tribal contribution
            TribalRoleBehavior.apply_tribal_contribution(self.tribe, role, npc_id, efficiency)

            # Apply faction contribution if faction provided
            if faction:
                TribalRoleBehavior.apply_faction_contribution(faction, role, npc_id, efficiency)

        # Update tribal wellbeing after all contributions
        self.tribe.update_wellbeing()

        # Update faction wellbeing if provided
        if faction:
            faction.update_wellbeing()

        self.logger.info(
            f"Processed role contributions for {len(self.tribe.social_roles)} tribal members"
        )

    def process_role_activities(self):
        """Process role-specific activities each turn"""
        # Reset activity organization flag at the start of each turn
        self.activities_organized_this_turn = False
        for npc_id, role in self.tribe.social_roles.items():
            if role == TribalRole.HUNTER:
                # Hunters gather food
                if random.random() < 0.3:  # 30% chance per turn
                    food_gained = random.randint(1, 3)
                    self.tribe.add_shared_resource("food", food_gained)

            elif role == TribalRole.GATHERER:
                # Gatherers collect resources
                if random.random() < 0.4:  # 40% chance per turn
                    resources = ["wood", "stone", "herbs"]
                    resource = random.choice(resources)
                    amount = random.randint(1, 2)
                    self.tribe.add_shared_resource(resource, amount)

            elif role == TribalRole.CRAFTER:
                # Crafters improve structures or create tools
                if random.random() < 0.2:  # 20% chance per turn
                    # Small chance to improve existing structures
                    if self.tribe.structures.get("campfire", 0) > 0:
                        # Improve campfire quality (conceptually)
                        pass

            elif role == TribalRole.SHAMAN:
                # Shamans develop spiritual beliefs
                if random.random() < 0.1:  # 10% chance per turn
                    self._develop_spiritual_beliefs()

            elif role == TribalRole.LEADER:
                # Leaders organize and plan
                if random.random() < 0.15:  # 15% chance per turn
                    self._organize_tribal_activities()

            elif role == TribalRole.WARRIOR:
                # Warriors patrol and defend
                if random.random() < 0.25:  # 25% chance per turn
                    self._patrol_territory()

    def _develop_spiritual_beliefs(self):
        """Shaman develops spiritual beliefs"""
        beliefs = [
            "Fire brings warmth and protection",
            "The spirits of ancestors guide us",
            "Nature provides for those who respect it",
            "Dreams reveal hidden truths",
        ]

        if random.random() < 0.3:  # 30% chance to add new belief
            new_belief = random.choice(beliefs)
            if new_belief not in self.tribe.spiritual_beliefs["creation_myth"]:
                self.tribe.spiritual_beliefs["creation_myth"] = new_belief
                self.logger.info(f"Shaman developed new spiritual belief: {new_belief}")

    def _organize_tribal_activities(self):
        """Leader organizes tribal activities"""
        # Prevent multiple leaders from organizing activities in the same turn
        if self.activities_organized_this_turn:
            return

        activities = [
            "hunting_party",
            "resource_gathering",
            "structure_building",
            "ceremony",
        ]

        if random.random() < 0.4:  # 40% chance to organize activity
            activity = random.choice(activities)
            self.tribe.add_tribal_memory(
                "organized_activity", {"activity": activity, "organized_by": "leader"}
            )
            self.logger.info(f"Leader organized {activity} for the tribe")
            self.activities_organized_this_turn = True

    def _patrol_territory(self):
        """Warrior patrols tribal territory"""
        if random.random() < 0.2:  # 20% chance to find something
            discoveries = [
                "resource_deposit",
                "threat_signs",
                "boundary_marker",
                "animal_tracks",
            ]
            discovery = random.choice(discoveries)

            self.tribe.add_tribal_memory(
                "patrol_discovery",
                {"discovery": discovery, "location": "territory_edge"},
            )
            self.logger.info(f"Warrior discovered {discovery} while patrolling")
