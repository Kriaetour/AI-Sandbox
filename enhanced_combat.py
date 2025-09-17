import random
import logging
from typing import Dict, Tuple, Any
from enum import Enum


class CombatType(Enum):
    """Types of combat encounters."""

    SKIRMISH = "skirmish"  # Small groups, low casualties
    RAID = "raid"  # Hit-and-run, resource focused
    BATTLE = "battle"  # Major engagement, high stakes
    SIEGE = "siege"  # Prolonged territorial assault


class CombatResult(Enum):
    """Possible combat outcomes."""

    DECISIVE_VICTORY = "decisive_victory"
    VICTORY = "victory"
    PYRRHIC_VICTORY = "pyrrhic_victory"
    STALEMATE = "stalemate"
    DEFEAT = "defeat"
    ROUT = "rout"


class EnhancedCombatManager:
    """
    Enhanced combat system with detailed mechanics, environmental factors, and resource impacts.
    """

    def __init__(self):
        self.logger = logging.getLogger("EnhancedCombat")
        self.active_combats = {}
        self.combat_history = []
        self.combat_id_counter = 0

    def initiate_combat(
        self,
        attacker_tribe,
        defender_tribe,
        location: Tuple[int, int],
        combat_type: CombatType,
        world_context: Dict = None,
    ) -> Dict[str, Any]:
        """
        Initiate enhanced combat between two tribes.
        """
        self.combat_id_counter += 1
        combat_id = f"combat_{self.combat_id_counter}"

        # Determine forces involved
        attacker_forces = self._calculate_forces(attacker_tribe, combat_type, role="attacker")
        defender_forces = self._calculate_forces(defender_tribe, combat_type, role="defender")

        # Apply environmental modifiers
        env_modifiers = self._get_environmental_modifiers(location, world_context or {})

        # Calculate combat power
        attacker_power = self._calculate_combat_power(
            attacker_forces, env_modifiers, role="attacker", tribe=attacker_tribe, combat_type=combat_type
        )
        defender_power = self._calculate_combat_power(
            defender_forces, env_modifiers, role="defender", tribe=defender_tribe, combat_type=combat_type
        )

        # Resolve combat
        result = self._resolve_combat(attacker_power, defender_power, combat_type)

        # Apply casualties and resource impacts
        casualties = self._calculate_casualties(
            result, attacker_forces, defender_forces, combat_type
        )
        resource_impacts = self._calculate_resource_impacts(
            result, attacker_tribe, defender_tribe, combat_type
        )

        combat_data = {
            "id": combat_id,
            "attacker": (
                attacker_tribe.name if hasattr(attacker_tribe, "name") else str(attacker_tribe)
            ),
            "defender": (
                defender_tribe.name if hasattr(defender_tribe, "name") else str(defender_tribe)
            ),
            "location": location,
            "type": combat_type.value,
            "attacker_forces": attacker_forces,
            "defender_forces": defender_forces,
            "attacker_power": attacker_power,
            "defender_power": defender_power,
            "result": result.value,
            "casualties": casualties,
            "resource_impacts": resource_impacts,
            "environmental_factors": env_modifiers,
        }

        # Apply effects to tribes
        self._apply_combat_effects(attacker_tribe, defender_tribe, combat_data)

        # Record in history
        self.combat_history.append(combat_data)

        self.logger.info(
            f"Combat resolved: {attacker_tribe.name if hasattr(attacker_tribe, 'name') else 'Unknown'} vs "
            f"{defender_tribe.name if hasattr(defender_tribe, 'name') else 'Unknown'} -> {result.value}"
        )

        return combat_data

    def _calculate_forces(self, tribe, combat_type: CombatType, role: str) -> Dict[str, int]:
        """Calculate the forces a tribe can bring to combat."""
        # Get tribe size (fallback to basic count)
        if hasattr(tribe, "members"):
            total_members = len(tribe.members)
        elif hasattr(tribe, "population"):
            total_members = tribe.population
        else:
            total_members = random.randint(10, 50)  # Fallback

        # Calculate combatants based on combat type and role
        if combat_type == CombatType.SKIRMISH:
            combatants = min(total_members // 4, random.randint(3, 8))
        elif combat_type == CombatType.RAID:
            combatants = min(total_members // 3, random.randint(5, 15))
        elif combat_type == CombatType.BATTLE:
            combatants = min(total_members // 2, random.randint(10, 30))
        elif combat_type == CombatType.SIEGE:
            combatants = min(int(total_members * 0.7), random.randint(15, 40))
        else:
            combatants = random.randint(5, 15)

        # Defenders get advantage in their territory
        if role == "defender":
            combatants = int(combatants * 1.2)

        # Categorize forces by type
        warriors = int(combatants * 0.6)
        scouts = int(combatants * 0.2)
        support = combatants - warriors - scouts

        return {
            "total": combatants,
            "warriors": max(1, warriors),
            "scouts": max(0, scouts),
            "support": max(0, support),
        }

    def _get_environmental_modifiers(
        self, location: Tuple[int, int], world_context: Dict
    ) -> Dict[str, float]:
        """Calculate environmental modifiers for combat."""
        modifiers = {"weather": 1.0, "terrain": 1.0, "time_of_day": 1.0, "season": 1.0}

        # Weather effects
        weather = world_context.get("weather", "CLEAR")
        if weather == "STORM":
            modifiers["weather"] = 0.7  # Severe combat penalty
        elif weather == "RAIN":
            modifiers["weather"] = 0.9  # Slight penalty
        elif weather == "SNOW":
            modifiers["weather"] = 0.8  # Movement penalty
        elif weather == "BLIZZARD":
            modifiers["weather"] = 0.5  # Extreme penalty

        # Time of day effects
        time_info = world_context.get("time", {})
        if time_info.get("is_day", True):
            modifiers["time_of_day"] = 1.1  # Slight bonus for day combat
        else:
            modifiers["time_of_day"] = 0.9  # Night combat penalty

        # Seasonal effects
        season = time_info.get("season", 0)
        if season == 3:  # Winter
            modifiers["season"] = 0.8  # Winter combat penalty
        elif season == 1:  # Summer
            modifiers["season"] = 1.1  # Summer combat bonus

        return modifiers

    def _calculate_combat_power(
        self, forces: Dict[str, int], env_modifiers: Dict[str, float], role: str, tribe=None, combat_type=None
    ) -> float:
        """Calculate total combat power considering all factors."""
        base_power = (
            forces["warriors"] * 3.0  # Warriors are most effective
            + forces["scouts"] * 1.5  # Scouts provide tactical advantage
            + forces["support"] * 1.0  # Support provides logistics
        )

        # Apply environmental modifiers
        for modifier in env_modifiers.values():
            base_power *= modifier

        # Role-specific bonuses
        if role == "defender":
            base_power *= 1.3  # Defensive advantage

        # Apply technology combat bonuses
        tech_combat_bonus = 0.0
        special_ability_bonus = 1.0
        if tribe:
            try:
                from technology_system import technology_manager
                multipliers = technology_manager.calculate_tribe_multipliers(tribe.id if hasattr(tribe, 'id') else str(tribe))
                tech_combat_bonus = multipliers.get("combat", 0.0)

                # Check for special combat abilities
                tribe_abilities = technology_manager.get_tribe_abilities(tribe.id if hasattr(tribe, 'id') else str(tribe))

                # Armor and defense bonuses
                if "iron_armor" in tribe_abilities or "steel_armor" in tribe_abilities or "bronze_armor" in tribe_abilities:
                    special_ability_bonus *= 1.15  # 15% armor bonus
                    if role == "defender":
                        special_ability_bonus *= 1.1  # Extra defensive bonus

                # Siege and tactical bonuses
                if "siege_weapons" in tribe_abilities or "advanced_siege" in tribe_abilities:
                    if combat_type == CombatType.SIEGE:
                        special_ability_bonus *= 1.25  # 25% siege bonus

                # Military organization bonuses
                if "military_hierarchy" in tribe_abilities or "professional_army" in tribe_abilities:
                    special_ability_bonus *= 1.1  # 10% organization bonus
                    # Better casualty distribution
                    if role == "attacker":
                        special_ability_bonus *= 1.05

                # Logistics bonus for support units
                if "logistics" in tribe_abilities:
                    support_bonus = forces.get("support", 0) * 0.5  # Support units more effective
                    special_ability_bonus *= (1.0 + support_bonus / max(forces["warriors"] + forces["scouts"] + forces["support"], 1))

            except (ImportError, AttributeError, Exception):
                # Technology system not available or tribe doesn't have tech
                pass

        if tech_combat_bonus > 0:
            base_power *= (1.0 + tech_combat_bonus)

        # Apply special ability bonuses
        base_power *= special_ability_bonus

        # Add some randomness
        base_power *= random.uniform(0.8, 1.2)

        return base_power

    def _resolve_combat(
        self, attacker_power: float, defender_power: float, combat_type: CombatType
    ) -> CombatResult:
        """Resolve combat and determine outcome."""
        power_ratio = attacker_power / defender_power if defender_power > 0 else 2.0

        # Base resolution with some randomness
        roll = random.uniform(0.7, 1.3)
        effective_ratio = power_ratio * roll

        # Determine result based on power ratio and combat type
        if effective_ratio >= 2.0:
            return CombatResult.DECISIVE_VICTORY
        elif effective_ratio >= 1.5:
            return CombatResult.VICTORY
        elif effective_ratio >= 1.1:
            return CombatResult.PYRRHIC_VICTORY
        elif effective_ratio >= 0.9:
            return CombatResult.STALEMATE
        elif effective_ratio >= 0.5:
            return CombatResult.DEFEAT
        else:
            return CombatResult.ROUT

    def _calculate_casualties(
        self,
        result: CombatResult,
        attacker_forces: Dict,
        defender_forces: Dict,
        combat_type: CombatType,
    ) -> Dict[str, Dict[str, int]]:
        """Calculate casualties based on combat result and type."""
        # Base casualty rates by result
        casualty_rates = {
            CombatResult.DECISIVE_VICTORY: {"winner": 0.05, "loser": 0.4},
            CombatResult.VICTORY: {"winner": 0.1, "loser": 0.3},
            CombatResult.PYRRHIC_VICTORY: {"winner": 0.2, "loser": 0.25},
            CombatResult.STALEMATE: {"winner": 0.15, "loser": 0.15},
            CombatResult.DEFEAT: {"winner": 0.25, "loser": 0.2},
            CombatResult.ROUT: {"winner": 0.4, "loser": 0.05},
        }

        # Combat type modifiers
        type_modifiers = {
            CombatType.SKIRMISH: 0.5,
            CombatType.RAID: 0.7,
            CombatType.BATTLE: 1.0,
            CombatType.SIEGE: 1.3,
        }

        rates = casualty_rates[result]
        modifier = type_modifiers[combat_type]

        # Determine who is winner/loser
        if result in [
            CombatResult.DECISIVE_VICTORY,
            CombatResult.VICTORY,
            CombatResult.PYRRHIC_VICTORY,
        ]:
            winner_forces = attacker_forces
            loser_forces = defender_forces
            winner_key = "attacker"
            loser_key = "defender"
        elif result in [CombatResult.DEFEAT, CombatResult.ROUT]:
            winner_forces = defender_forces
            loser_forces = attacker_forces
            winner_key = "defender"
            loser_key = "attacker"
        else:  # Stalemate
            winner_forces = attacker_forces
            loser_forces = defender_forces
            winner_key = "attacker"
            loser_key = "defender"

        # Calculate actual casualties
        def calculate_force_casualties(forces: Dict[str, int], rate: float) -> Dict[str, int]:
            return {
                "warriors": max(
                    0,
                    int(forces["warriors"] * rate * modifier * random.uniform(0.5, 1.5)),
                ),
                "scouts": max(
                    0,
                    int(forces["scouts"] * rate * modifier * random.uniform(0.5, 1.5)),
                ),
                "support": max(
                    0,
                    int(forces["support"] * rate * modifier * random.uniform(0.5, 1.5)),
                ),
            }

        casualties = {
            winner_key: calculate_force_casualties(winner_forces, rates["winner"]),
            loser_key: calculate_force_casualties(loser_forces, rates["loser"]),
        }

        return casualties

    def _calculate_resource_impacts(
        self,
        result: CombatResult,
        attacker_tribe,
        defender_tribe,
        combat_type: CombatType,
    ) -> Dict[str, Dict[str, float]]:
        """Calculate resource impacts from combat."""
        impacts = {"attacker": {}, "defender": {}}

        # Resource effects based on combat type
        if combat_type == CombatType.RAID:
            # Raids focus on resource acquisition
            if result in [CombatResult.DECISIVE_VICTORY, CombatResult.VICTORY]:
                impacts["attacker"]["food"] = random.uniform(10, 30)
                impacts["attacker"]["materials"] = random.uniform(5, 15)
                impacts["defender"]["food"] = -random.uniform(15, 40)
                impacts["defender"]["materials"] = -random.uniform(10, 25)

        elif combat_type == CombatType.SIEGE:
            # Sieges are resource-intensive
            impacts["attacker"]["food"] = -random.uniform(20, 50)
            impacts["defender"]["food"] = -random.uniform(30, 60)
            if result in [CombatResult.DECISIVE_VICTORY, CombatResult.VICTORY]:
                # Winner gets significant spoils
                impacts["attacker"]["food"] = random.uniform(40, 80)
                impacts["attacker"]["materials"] = random.uniform(30, 60)

        # General combat costs
        base_cost = {
            CombatType.SKIRMISH: 5,
            CombatType.RAID: 10,
            CombatType.BATTLE: 20,
            CombatType.SIEGE: 35,
        }

        cost = base_cost[combat_type]
        impacts["attacker"]["food"] = impacts["attacker"].get("food", 0) - cost
        impacts["defender"]["food"] = (
            impacts["defender"].get("food", 0) - cost * 0.7
        )  # Defenders use less

        return impacts

    def _apply_combat_effects(self, attacker_tribe, defender_tribe, combat_data: Dict):
        """Apply combat effects to the tribes."""
        try:
            # Apply casualties (reduce tribe population/members)
            casualties = combat_data["casualties"]

            # Apply resource impacts
            resource_impacts = combat_data["resource_impacts"]

            for tribe, key in [
                (attacker_tribe, "attacker"),
                (defender_tribe, "defender"),
            ]:
                if hasattr(tribe, "shared_resources"):
                    for resource, change in resource_impacts[key].items():
                        current = tribe.shared_resources.get(resource, 0)
                        tribe.shared_resources[resource] = max(0, current + change)

                # Record combat in tribal memory if possible
                if hasattr(tribe, "add_tribal_memory"):
                    tribe.add_tribal_memory(
                        "combat",
                        {
                            "result": combat_data["result"],
                            "opponent": (
                                combat_data["defender"]
                                if key == "attacker"
                                else combat_data["attacker"]
                            ),
                            "type": combat_data["type"],
                            "casualties": casualties[key],
                        },
                    )

        except Exception as e:
            self.logger.warning(f"Failed to apply combat effects: {e}")

    def get_combat_statistics(self, tribe_name: str = None) -> Dict[str, Any]:
        """Get combat statistics, optionally filtered by tribe."""
        if tribe_name:
            relevant_combats = [
                c
                for c in self.combat_history
                if c["attacker"] == tribe_name or c["defender"] == tribe_name
            ]
        else:
            relevant_combats = self.combat_history

        if not relevant_combats:
            return {"total_combats": 0}

        # Calculate statistics
        total_combats = len(relevant_combats)
        results = {}
        casualties_total = {"warriors": 0, "scouts": 0, "support": 0}

        for combat in relevant_combats:
            result = combat["result"]
            results[result] = results.get(result, 0) + 1

            # Sum casualties
            for side in ["attacker", "defender"]:
                for unit_type, count in combat["casualties"][side].items():
                    casualties_total[unit_type] += count

        return {
            "total_combats": total_combats,
            "results": results,
            "total_casualties": casualties_total,
            "average_casualties_per_combat": {
                unit_type: count / total_combats for unit_type, count in casualties_total.items()
            },
        }
