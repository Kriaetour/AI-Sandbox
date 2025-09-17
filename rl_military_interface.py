#!/usr/bin/env python3
"""
Military Interface: Functions for military actions and state assessment.

This module provides the interface between the Military RL Agent and the
tribal simulation, including military actions, state assessment, and rewards.
"""

from typing import Dict, List, Any
import random

from tribes.tribal_manager import TribalManager
from world.engine import WorldEngine


def get_military_actions() -> List[str]:
    """Get list of available military actions."""
    return [
        "aggressive_attack",    # Launch immediate offensive
        "defensive_posture",    # Fortify and defend
        "strategic_retreat",    # Withdraw to safer position
        "force_reinforcement",  # Build up military forces
        "tech_investment",      # Invest in military technology
        "diplomatic_pressure",  # Use threats with diplomacy
        "siege_preparation",    # Prepare for siege warfare
        "peaceful_approach"     # Avoid combat, focus on growth
    ]


def execute_military_action(
    action: str,
    tribe,
    target_tribes: List,
    tribal_manager: TribalManager,
    world: WorldEngine
) -> Dict[str, Any]:
    """
    Execute a military action and return the results.

    Args:
        action: The military action to execute
        tribe: The acting tribe
        target_tribes: List of potential target tribes
        tribal_manager: The tribal manager instance
        world: The world engine instance

    Returns:
        Dict containing action results and outcomes
    """
    results = {
        "action": action,
        "success": False,
        "combat_initiated": False,
        "casualties": 0,
        "territory_gained": 0,
        "resources_captured": 0,
        "diplomatic_impact": 0.0,
        "description": ""
    }

    if action == "aggressive_attack":
        results.update(_execute_aggressive_attack(tribe, target_tribes, tribal_manager, world))

    elif action == "defensive_posture":
        results.update(_execute_defensive_posture(tribe, tribal_manager, world))

    elif action == "strategic_retreat":
        results.update(_execute_strategic_retreat(tribe, tribal_manager, world))

    elif action == "force_reinforcement":
        results.update(_execute_force_reinforcement(tribe, tribal_manager, world))

    elif action == "tech_investment":
        results.update(_execute_tech_investment(tribe, tribal_manager, world))

    elif action == "diplomatic_pressure":
        results.update(_execute_diplomatic_pressure(tribe, target_tribes, tribal_manager, world))

    elif action == "siege_preparation":
        results.update(_execute_siege_preparation(tribe, target_tribes, tribal_manager, world))

    elif action == "peaceful_approach":
        results.update(_execute_peaceful_approach(tribe, tribal_manager, world))

    return results


def get_military_state_vector(
    tribe,
    enemy_tribes: List,
    tribal_manager: TribalManager,
    world: WorldEngine
) -> List[float]:
    """
    Get military state vector for RL agent.

    Returns a vector representing the current military situation:
    [power_ratio, tech_advantage, diplomatic_status, resource_availability,
     force_readiness, territory_control, enemy_aggression, defensive_position]
    """
    if not tribe:
        return [0.0] * 8

    # Power ratio (our power vs average enemy power)
    our_power = _calculate_tribal_military_power(tribe, world)
    enemy_powers = [_calculate_tribal_military_power(enemy, world) for enemy in enemy_tribes]
    avg_enemy_power = sum(enemy_powers) / len(enemy_powers) if enemy_powers else 1.0
    power_ratio = our_power / avg_enemy_power if avg_enemy_power > 0 else 2.0

    # Technology advantage
    our_tech_level = _calculate_military_tech_level(tribe)
    enemy_tech_levels = [_calculate_military_tech_level(enemy) for enemy in enemy_tribes]
    avg_enemy_tech = sum(enemy_tech_levels) / len(enemy_tech_levels) if enemy_tech_levels else 0.0
    tech_advantage = our_tech_level - avg_enemy_tech

    # Diplomatic status (simplified - would integrate with diplomacy system)
    diplomatic_status = 0.0

    # Resource availability
    resource_availability = _calculate_resource_availability(tribe, world)

    # Force readiness
    force_readiness = _calculate_force_readiness(tribe, world)

    # Territory control
    territory_control = _calculate_territory_control(tribe, world)

    # Enemy aggression level
    enemy_aggression = _calculate_enemy_aggression(enemy_tribes, world)

    # Defensive position advantage
    defensive_position = _calculate_defensive_position(tribe, world)

    return [
        power_ratio,
        tech_advantage,
        diplomatic_status,
        resource_availability,
        force_readiness,
        territory_control,
        enemy_aggression,
        defensive_position
    ]


def compute_military_reward(
    action_results: Dict[str, Any],
    previous_state: List[float],
    current_state: List[float]
) -> float:
    """
    Compute reward for military action based on outcomes and state changes.

    Reward components:
    - Combat success/failure
    - Territory/Resource gains
    - Casualty minimization
    - Strategic positioning
    - Long-term advantage
    """
    reward = 0.0

    # Combat outcomes
    if action_results.get("combat_initiated", False):
        if action_results.get("success", False):
            reward += 50.0  # Successful combat
            reward += action_results.get("territory_gained", 0) * 10.0
            reward += action_results.get("resources_captured", 0) * 2.0
        else:
            reward -= 30.0  # Failed combat

    # Casualty management
    casualties = action_results.get("casualties", 0)
    reward -= casualties * 5.0  # Penalty for casualties

    # Strategic positioning improvements
    if current_state and previous_state and len(previous_state) > 7:
        # Reward for improving power ratio
        power_ratio_improvement = current_state[0] - previous_state[0]
        reward += power_ratio_improvement * 20.0

        # Reward for improving territory control
        territory_improvement = current_state[5] - previous_state[5]
        reward += territory_improvement * 15.0

        # Reward for improving defensive position
        defense_improvement = current_state[7] - previous_state[7]
        reward += defense_improvement * 10.0

    # Diplomatic impact
    diplomatic_impact = action_results.get("diplomatic_impact", 0.0)
    reward += diplomatic_impact * 25.0

    # Action-specific bonuses/penalties
    action = action_results.get("action", "")
    if action == "peaceful_approach":
        reward += 10.0  # Reward peaceful development
    elif action == "tech_investment":
        reward += 15.0  # Reward technology investment
    elif action == "aggressive_attack":
        if not action_results.get("success", False):
            reward -= 20.0  # Extra penalty for failed aggression

    return reward


def _execute_aggressive_attack(tribe, target_tribes, tribal_manager, world):
    """Execute aggressive attack action."""
    if not target_tribes:
        return {"success": False, "description": "No targets available"}

    # Select weakest target
    target = min(target_tribes, key=lambda t: _calculate_tribal_military_power(t, world))

    # Calculate success probability based on power ratio
    our_power = _calculate_tribal_military_power(tribe, world)
    enemy_power = _calculate_tribal_military_power(target, world)
    success_prob = min(0.9, our_power / enemy_power) if enemy_power > 0 else 0.5

    success = random.random() < success_prob

    results = {
        "success": success,
        "combat_initiated": True,
        "target": target.name if hasattr(target, 'name') else str(target),
        "description": f"Aggressive attack on {target.name if hasattr(target, 'name') else str(target)}"
    }

    if success:
        results.update({
            "territory_gained": random.randint(1, 3),
            "resources_captured": random.randint(50, 200),
            "casualties": random.randint(5, 20),
            "diplomatic_impact": -0.3  # Negative diplomatic impact
        })
    else:
        results.update({
            "casualties": random.randint(10, 30),
            "diplomatic_impact": -0.1
        })

    return results


def _execute_defensive_posture(tribe, tribal_manager, world):
    """Execute defensive posture action."""
    return {
        "success": True,
        "description": "Adopted defensive posture, improving fortifications",
        "diplomatic_impact": 0.1,  # Slight positive diplomatic impact
        "defensive_bonus": 0.2
    }


def _execute_strategic_retreat(tribe, tribal_manager, world):
    """Execute strategic retreat action."""
    return {
        "success": True,
        "description": "Strategic retreat to safer position",
        "casualties": random.randint(1, 5),  # Minimal casualties
        "diplomatic_impact": -0.05
    }


def _execute_force_reinforcement(tribe, tribal_manager, world):
    """Execute force reinforcement action."""
    return {
        "success": True,
        "description": "Reinforcing military forces",
        "force_growth": random.randint(10, 30),
        "resource_cost": random.randint(100, 300)
    }


def _execute_tech_investment(tribe, tribal_manager, world):
    """Execute technology investment action."""
    return {
        "success": True,
        "description": "Investing in military technology",
        "tech_progress": random.randint(5, 15),
        "resource_cost": random.randint(200, 500)
    }


def _execute_diplomatic_pressure(tribe, target_tribes, tribal_manager, world):
    """Execute diplomatic pressure action."""
    if not target_tribes:
        return {"success": False, "description": "No targets available"}

    return {
        "success": random.random() < 0.7,
        "description": "Applying diplomatic pressure",
        "diplomatic_impact": random.uniform(-0.2, 0.3)
    }


def _execute_siege_preparation(tribe, target_tribes, tribal_manager, world):
    """Execute siege preparation action."""
    return {
        "success": True,
        "description": "Preparing siege equipment and tactics",
        "siege_bonus": 0.3,
        "resource_cost": random.randint(150, 400)
    }


def _execute_peaceful_approach(tribe, tribal_manager, world):
    """Execute peaceful approach action."""
    return {
        "success": True,
        "description": "Focusing on peaceful development and growth",
        "growth_bonus": 0.15,
        "diplomatic_impact": 0.2
    }


def _calculate_tribal_military_power(tribe, world) -> float:
    """Calculate military power of a tribe."""
    if not tribe:
        return 0.0

    power = 0.0

    # Population-based power
    if hasattr(tribe, 'population'):
        power += tribe.population * 0.1

    # Technology bonuses
    if hasattr(tribe, 'id'):
        try:
            from technology_system import technology_manager
            multipliers = technology_manager.calculate_tribe_multipliers(tribe.id)
            combat_bonus = multipliers.get("combat", 0.0)
            power *= (1.0 + combat_bonus)
        except Exception:
            pass

    return power


def _calculate_military_tech_level(tribe) -> float:
    """Calculate military technology level."""
    if not tribe or not hasattr(tribe, 'id'):
        return 0.0

    try:
        from technology_system import technology_manager
        unlocked_techs = technology_manager.unlocked_technologies.get(tribe.id, set())
        military_techs = ["weapons", "iron_weapons", "steel_weapons", "military_organization"]
        return len(unlocked_techs.intersection(military_techs)) * 0.25
    except Exception:
        return 0.0


def _calculate_resource_availability(tribe, world) -> float:
    """Calculate resource availability (0.0 to 1.0)."""
    # Simplified - would check actual faction resources
    return random.uniform(0.3, 0.9)


def _calculate_force_readiness(tribe, world) -> float:
    """Calculate military readiness."""
    if not tribe:
        return 0.0

    readiness = 0.5

    # Technology improves readiness
    if hasattr(tribe, 'id'):
        try:
            from technology_system import technology_manager
            abilities = technology_manager.get_tribe_abilities(tribe.id)
            if "military_hierarchy" in abilities:
                readiness += 0.2
            if "professional_army" in abilities:
                readiness += 0.15
        except Exception:
            pass

    return min(1.0, readiness)


def _calculate_territory_control(tribe, world) -> float:
    """Calculate territory control percentage."""
    # Simplified - would calculate from actual territory
    return random.uniform(0.4, 0.8)


def _calculate_enemy_aggression(enemy_tribes, world) -> float:
    """Calculate enemy aggression level."""
    if not enemy_tribes:
        return 0.0
    return random.uniform(0.2, 0.8)


def _calculate_defensive_position(tribe, world) -> float:
    """Calculate defensive position advantage."""
    # Simplified - would consider terrain, fortifications, etc.
    return random.uniform(0.3, 0.9)