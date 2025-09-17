"""
Flexible RL Reward Shaping for the AI Sandbox.
Combine social, demographic, and cultural metrics with custom weights.
"""

from typing import Dict, Tuple
from rl_rumor_interface import compute_rumor_reward
from rl_saying_interface import compute_saying_reward
from rl_env_state import get_rl_env_state
from gemini_narrative import explain_rl_reward


def compute_shaped_reward(world, weights=None):
    """
    Compute a shaped RL reward as a weighted sum of metrics.
    weights: dict with keys (cohesion, allies, hostiles, rumor, saying, pop_stability, deaths, births, etc.)
    Example weights:
        {'cohesion': 1.0, 'allies': 0.5, 'hostiles': -0.5, 'rumor': 0.3, 'saying': 0.3, 'pop_stability': 0.2, 'deaths': -0.2}
    """
    if weights is None:
        weights = {
            "cohesion": 1.0,
            "allies": 0.5,
            "hostiles": -0.5,
            "rumor": 0.3,
            "saying": 0.3,
            "pop_stability": 0.2,
            "deaths": -0.2,
            "births": 0.1,
        }
    state = get_rl_env_state(world)
    reward = 0.0
    # Social cohesion (mean opinion)
    reward += weights.get("cohesion", 0) * state.get("avg_opinion", 0)
    # Allies/hostiles
    reward += weights.get("allies", 0) * state.get("total_allies", 0)
    reward += weights.get("hostiles", 0) * state.get("total_hostiles", 0)
    # Rumor and saying rewards
    reward += weights.get("rumor", 0) * compute_rumor_reward(world)
    reward += weights.get("saying", 0) * compute_saying_reward(world)
    # Population stability (adaptive based on current population context)
    pop = state.get("population", 0)
    # Use current population as the stability target (adaptive stability)
    stability_target = max(50, pop)  # Don't go below 50 for stability calculations
    reward += weights.get("pop_stability", 0) * (
        1.0 - abs(pop - stability_target) / max(stability_target, 50)
    )
    # Deaths and births (per tick)
    reward += weights.get("deaths", 0) * state.get("deaths_starv_tick", 0)
    reward += weights.get("births", 0) * state.get("births_tick", 0)
    # Add more as needed
    return reward


def compute_shaped_reward_with_explanation(
    world, weights=None, action_taken: str = "", include_llm_explanation: bool = True
) -> Tuple[float, str, Dict[str, float]]:
    """
    Compute shaped reward with optional LLM explanation and component breakdown.

    Args:
        world: The world object
        weights: Reward weights dictionary
        action_taken: Description of the action taken
        include_llm_explanation: Whether to generate LLM explanation

    Returns:
        Tuple of (total_reward, explanation_string, reward_components_dict)
    """
    if weights is None:
        weights = {
            "cohesion": 1.0,
            "allies": 0.5,
            "hostiles": -0.5,
            "rumor": 0.3,
            "saying": 0.3,
            "pop_stability": 0.2,
            "deaths": -0.2,
            "births": 0.1,
        }

    state = get_rl_env_state(world)
    reward_components = {}

    # Social cohesion (mean opinion)
    cohesion_reward = weights.get("cohesion", 0) * state.get("avg_opinion", 0)
    reward_components["cohesion"] = cohesion_reward

    # Allies/hostiles
    allies_reward = weights.get("allies", 0) * state.get("total_allies", 0)
    reward_components["allies"] = allies_reward
    hostiles_reward = weights.get("hostiles", 0) * state.get("total_hostiles", 0)
    reward_components["hostiles"] = hostiles_reward

    # Rumor and saying rewards
    rumor_reward = weights.get("rumor", 0) * compute_rumor_reward(world)
    reward_components["rumor"] = rumor_reward
    saying_reward = weights.get("saying", 0) * compute_saying_reward(world)
    reward_components["saying"] = saying_reward

    # Population stability (reward for population near 300)
    pop = state.get("population", 0)
    pop_stability_reward = weights.get("pop_stability", 0) * (1.0 - abs(pop - 300) / 300)
    reward_components["pop_stability"] = pop_stability_reward

    # Deaths and births (per tick)
    deaths_reward = weights.get("deaths", 0) * state.get("deaths_starv_tick", 0)
    reward_components["deaths"] = deaths_reward
    births_reward = weights.get("births", 0) * state.get("births_tick", 0)
    reward_components["births"] = births_reward

    # Calculate total reward
    total_reward = sum(reward_components.values())

    if include_llm_explanation:
        explanation = explain_rl_reward(reward_components, total_reward, action_taken)
    else:
        explanation = f"Total reward: {total_reward:.2f}"

    return total_reward, explanation, reward_components
