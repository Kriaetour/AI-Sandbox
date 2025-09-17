#!/usr/bin/env python3
"""
Military RL Agent: Strategic military decision-making for tribal warfare.

This agent learns optimal military strategies including when to attack, defend,
force composition, and technology utilization in combat scenarios.
"""

import random
import json
from collections import defaultdict
from typing import Dict, List, Tuple, Any
import numpy as np

from technology_system import technology_manager


def _default_q_values(num_actions: int) -> List[float]:
    """Helper function to create default Q-values for multiprocessing compatibility."""
    return [0.0] * num_actions


class QTableDefaultDict(dict):
    """Custom defaultdict for Q-table that is multiprocessing-compatible."""
    def __init__(self, num_actions: int):
        super().__init__()
        self.num_actions = num_actions

    def __missing__(self, key):
        self[key] = [0.0] * self.num_actions
        return self[key]


class MilitaryRLAgent:
    """RL Agent for learning optimal military strategies in tribal warfare."""

    def __init__(
        self,
        num_actions: int = 8,
        epsilon: float = 0.1,
        lr: float = 0.1,
        gamma: float = 0.95,
    ):
        self.num_actions = num_actions
        self.epsilon = epsilon  # Exploration rate
        self.lr = lr  # Learning rate
        self.gamma = gamma  # Discount factor

        # Q-table: state -> action values
        # States represent military situation (power ratios, technology, diplomacy)
        self.q_table: Dict[Tuple, List[float]] = QTableDefaultDict(self.num_actions)

        # Action names for military decisions
        self.action_names = [
            "aggressive_attack",    # Launch immediate offensive
            "defensive_posture",    # Fortify and defend
            "strategic_retreat",    # Withdraw to safer position
            "force_reinforcement",  # Build up military forces
            "tech_investment",      # Invest in military technology
            "diplomatic_pressure",  # Use threats with diplomacy
            "siege_preparation",    # Prepare for siege warfare
            "peaceful_approach"     # Avoid combat, focus on growth
        ]

        # State discretization bins for military analysis - INCREASED RESOLUTION
        self.state_bins = {
            "power_ratio": np.linspace(0.0, 3.0, 15),      # Increased from 10 to 15 bins
            "tech_advantage": np.linspace(-2.0, 2.0, 12),  # Increased from 8 to 12 bins
            "diplomatic_status": np.linspace(-1.0, 1.0, 8), # Increased from 6 to 8 bins
            "resource_availability": np.linspace(0.0, 2.0, 8), # Increased from 6 to 8 bins
            "force_readiness": np.linspace(0.0, 1.0, 7),   # Increased from 5 to 7 bins
            "territory_control": np.linspace(0.0, 1.0, 8), # Increased from 6 to 8 bins
        }

        # Combat history for learning
        self.combat_history = []
        self.last_action = None
        self.last_state = None

    def get_military_state(self, tribe, enemy_tribes, world_context=None) -> Tuple:
        """Get discretized military state representation."""
        if not tribe or not enemy_tribes:
            return (0, 0, 0, 0, 0, 0)

        # Store world context for power calculations
        self._world = world_context

        # Calculate power ratios
        our_power = self._calculate_tribal_power(tribe)
        enemy_powers = [self._calculate_tribal_power(enemy) for enemy in enemy_tribes]
        avg_enemy_power = sum(enemy_powers) / len(enemy_powers) if enemy_powers else 1.0
        power_ratio = our_power / avg_enemy_power if avg_enemy_power > 0 else 3.0

        # Technology advantage
        our_tech_level = self._calculate_technology_level(tribe)
        enemy_tech_levels = [self._calculate_technology_level(enemy) for enemy in enemy_tribes]
        avg_enemy_tech = sum(enemy_tech_levels) / len(enemy_tech_levels) if enemy_tech_levels else 0.0
        tech_advantage = our_tech_level - avg_enemy_tech

        # Diplomatic status - calculate based on faction relationships
        diplomatic_status = self._calculate_diplomatic_status(tribe, enemy_tribes)

        # Resource availability - calculate from faction resources
        resource_availability = self._calculate_resource_availability(tribe)

        # Force readiness
        force_readiness = self._calculate_force_readiness(tribe)

        # Territory control - calculate based on faction territory
        territory_control = self._calculate_territory_control(tribe)

        # Discretize values
        state = (
            np.digitize(power_ratio, self.state_bins["power_ratio"]) - 1,
            np.digitize(tech_advantage, self.state_bins["tech_advantage"]) - 1,
            np.digitize(diplomatic_status, self.state_bins["diplomatic_status"]) - 1,
            np.digitize(resource_availability, self.state_bins["resource_availability"]) - 1,
            np.digitize(force_readiness, self.state_bins["force_readiness"]) - 1,
            np.digitize(territory_control, self.state_bins["territory_control"]) - 1,
        )

        return state

    def _state_to_key(self, state: Tuple) -> str:
        """Convert state tuple to string key for Q-table lookup."""
        return str(state)

    def choose_action(self, state: Tuple) -> int:
        """Choose military action using epsilon-greedy policy."""
        state_key = self._state_to_key(state)

        if random.random() < self.epsilon:
            # Exploration: random action
            return random.randint(0, self.num_actions - 1)
        else:
            # Exploitation: best known action
            if state_key in self.q_table:
                return np.argmax(self.q_table[state_key])
            else:
                # Unknown state: random action
                return random.randint(0, self.num_actions - 1)

    def update_q_table(self, state: Tuple, action: int, reward: float, next_state: Tuple):
        """Update Q-table using Q-learning algorithm."""
        state_key = self._state_to_key(state)
        next_state_key = self._state_to_key(next_state)

        current_q = self.q_table[state_key][action]
        max_next_q = max(self.q_table[next_state_key]) if next_state_key in self.q_table else 0.0

        # Q-learning update
        new_q = current_q + self.lr * (reward + self.gamma * max_next_q - current_q)
        self.q_table[state_key][action] = new_q

    def _calculate_tribal_power(self, tribe) -> float:
        """Calculate military power of a tribe."""
        if not tribe:
            return 0.0

        base_power = 0.0

        # Population contributes to military potential
        # Get population from faction data, not tribe object
        try:
            # Try to get population from faction if world is available
            if hasattr(self, '_world') and self._world and tribe.name in self._world.factions:
                faction = self._world.factions[tribe.name]
                if hasattr(faction, 'population'):
                    base_power += faction.population * 0.1
            elif hasattr(tribe, 'population'):
                base_power += tribe.population * 0.1
        except Exception:
            # Fallback: estimate population from tribe size if available
            if hasattr(tribe, 'member_ids'):
                base_power += len(tribe.member_ids) * 10.0  # Estimate 10 power per member

        # Technology bonuses
        if hasattr(tribe, 'id'):
            try:
                multipliers = technology_manager.calculate_tribe_multipliers(tribe.id)
                tech_bonus = multipliers.get("combat", 0.0)
                base_power *= (1.0 + tech_bonus)
            except Exception:
                pass

        # Military specialization (would be calculated from faction composition)
        military_modifier = 1.0

        return base_power * military_modifier

    def _calculate_technology_level(self, tribe) -> float:
        """Calculate technology level for military purposes."""
        if not tribe or not hasattr(tribe, 'id'):
            return 0.0

        try:
            unlocked_techs = technology_manager.unlocked_technologies.get(tribe.id, set())
            military_techs = [
                "weapons", "iron_weapons", "steel_weapons",
                "military_organization", "siege_engineering"
            ]

            tech_score = 0.0
            for tech in military_techs:
                if tech in unlocked_techs:
                    tech_info = technology_manager.technologies.get(tech, {})
                    tech_score += getattr(tech_info, 'trade_value', 100) / 1000.0

            return tech_score
        except Exception:
            return 0.0

    def _calculate_force_readiness(self, tribe) -> float:
        """Calculate military readiness (0.0 to 1.0) with population and tech factors."""
        if not tribe:
            return 0.0

        readiness = 0.3  # Lower base readiness

        # Population factor - larger tribes have better organization
        if hasattr(self, '_world') and self._world and tribe.name in self._world.factions:
            faction = self._world.factions[tribe.name]
            if hasattr(faction, 'population'):
                pop_factor = min(0.3, faction.population / 2000.0)  # Cap at 0.3 for large tribes
                readiness += pop_factor

        # Technology improves readiness
        if hasattr(tribe, 'id'):
            try:
                abilities = technology_manager.get_tribe_abilities(tribe.id)
                tech_bonus = 0.0
                if "military_hierarchy" in abilities:
                    tech_bonus += 0.15
                if "professional_army" in abilities:
                    tech_bonus += 0.2
                if "logistics" in abilities:
                    tech_bonus += 0.1
                if "iron_weapons" in abilities:
                    tech_bonus += 0.1
                if "steel_weapons" in abilities:
                    tech_bonus += 0.15
                readiness += tech_bonus
            except Exception:
                pass

        # Add some randomness based on tribe name for diversity
        name_factor = (hash(tribe.name + "readiness") % 100) / 500.0  # Small random factor
        readiness += name_factor

        return min(1.0, readiness)

    def _calculate_diplomatic_status(self, tribe, enemy_tribes) -> float:
        """Calculate diplomatic status with enemies (-1.0 to 1.0)."""
        if not tribe or not enemy_tribes:
            return 0.0

        total_diplomatic_score = 0.0
        count = 0

        for enemy in enemy_tribes:
            # Check faction relationships if available
            if hasattr(self, '_world') and self._world:
                if tribe.name in self._world.factions and enemy.name in self._world.factions:
                    our_faction = self._world.factions[tribe.name]
                    # Check relationships
                    relationship = our_faction.relationships.get(enemy.name, 0.0)
                    total_diplomatic_score += relationship
                    count += 1

        if count > 0:
            return total_diplomatic_score / count
        else:
            # Random diplomatic status based on tribe names for diversity
            return (hash(tribe.name) % 2000 - 1000) / 1000.0

    def _calculate_resource_availability(self, tribe) -> float:
        """Calculate resource availability (0.0 to 2.0) with better normalization."""
        if not tribe:
            return 0.0

        # Get resources from faction if available
        if hasattr(self, '_world') and self._world and tribe.name in self._world.factions:
            faction = self._world.factions[tribe.name]
            if hasattr(faction, 'resources'):
                resources = faction.resources
                # Calculate resource richness with logarithmic scaling for better distribution
                food = resources.get('food', 0)
                wood = resources.get('Wood', 0)  # Note: Wood with capital W
                ore = resources.get('Ore', 0)    # Note: Ore with capital O

                # Use piecewise scaling to spread values evenly across bins
                total_resources = food + wood + ore
                if total_resources > 0:
                    # Piecewise scaling for better distribution across 0.0-2.0 range
                    if total_resources < 100:
                        scaled = total_resources / 100.0 * 0.4  # 0-0.4 for poor tribes
                    elif total_resources < 1000:
                        scaled = 0.4 + (total_resources - 100) / 900.0 * 0.6  # 0.4-1.0 for medium
                    elif total_resources < 10000:
                        scaled = 1.0 + (total_resources - 1000) / 9000.0 * 0.6  # 1.0-1.6 for wealthy
                    else:
                        scaled = 1.6 + min(0.4, (total_resources - 10000) / 50000.0 * 0.4)  # 1.6-2.0 for ultra-wealthy
                    return min(2.0, scaled)
                else:
                    return 0.0

        # Fallback: random resource availability based on tribe name
        return (hash(tribe.name + "resources") % 2000) / 1000.0

    def _calculate_territory_control(self, tribe) -> float:
        """Calculate territory control (0.0 to 1.0) with better scaling."""
        if not tribe:
            return 0.0

        # Get territory from faction if available
        if hasattr(self, '_world') and self._world and tribe.name in self._world.factions:
            faction = self._world.factions[tribe.name]
            if hasattr(faction, 'territory') and faction.territory:
                territory_size = len(faction.territory)
                # Use square root scaling for better distribution
                # Small territories: 5->0.22, 25->0.5, 61->0.78, 100->1.0
                control = min(1.0, territory_size ** 0.5 / 10.0)
                return control

        # Fallback: random territory control based on tribe name
        return (hash(tribe.name + "territory") % 1000) / 1000.0

    def get_action_name(self, action: int) -> str:
        """Get human-readable name for action."""
        if 0 <= action < len(self.action_names):
            return self.action_names[action]
        return f"unknown_action_{action}"

    def save_q_table(self, filepath: str):
        """Save Q-table to file."""
        # Convert defaultdict to regular dict and tuple keys to strings for JSON serialization
        q_table_dict = {}
        for state, values in self.q_table.items():
            if isinstance(state, tuple):
                state_key = str(state)
            else:
                state_key = state
            q_table_dict[state_key] = values

        with open(filepath, 'w') as f:
            json.dump(q_table_dict, f, indent=2)

    def load_q_table(self, filepath: str):
        """Load Q-table from file."""
        try:
            with open(filepath, 'r') as f:
                q_table_dict = json.load(f)

                # Convert string keys back to tuples if they were originally tuples
                converted_dict = {}
                for key, values in q_table_dict.items():
                    if key.startswith('(') and key.endswith(')'):
                        # Try to convert back to tuple
                        try:
                            # Remove parentheses and split by comma
                            tuple_str = key[1:-1]
                            tuple_values = []
                            for val in tuple_str.split(','):
                                val = val.strip()
                                if val.isdigit():
                                    tuple_values.append(int(val))
                                else:
                                    tuple_values.append(float(val))
                            converted_dict[tuple(tuple_values)] = values
                        except (ValueError, TypeError):
                            converted_dict[key] = values
                    else:
                        converted_dict[key] = values

                self.q_table = defaultdict(lambda: [0.0] * self.num_actions, converted_dict)
        except FileNotFoundError:
            print(f"Q-table file {filepath} not found, starting with empty table")

    def get_military_analysis(self, tribe, enemy_tribes) -> Dict[str, Any]:
        """Provide detailed military analysis for decision support."""
        state = self.get_military_state(tribe, enemy_tribes)

        analysis = {
            "current_state": state,
            "recommended_action": self.choose_action(state),
            "action_name": self.get_action_name(self.choose_action(state)),
            "power_assessment": self._calculate_tribal_power(tribe),
            "technology_level": self._calculate_technology_level(tribe),
            "force_readiness": self._calculate_force_readiness(tribe),
            "q_values": self.q_table[state] if state in self.q_table else [0.0] * self.num_actions
        }

        return analysis