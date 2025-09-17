"""
RL Environment State Extraction: Memory-derived features for RL observation/state.
"""

from typing import Dict, Tuple
from rl_opinion_interface import get_opinion_stats
from rl_rumor_interface import get_rumor_stats
from rl_saying_interface import get_saying_stats
from gemini_narrative import generate_rl_state_description


def get_rl_env_state(world) -> Dict[str, float]:
    """Return a dict of RL-relevant state features from world memory and stats."""
    state = {}
    # Opinion features
    op_stats = get_opinion_stats(world)
    if op_stats:
        state["avg_opinion"] = sum(s["mean"] for s in op_stats.values()) / len(op_stats)
        state["min_opinion"] = min(s["min"] for s in op_stats.values())
        state["max_opinion"] = max(s["max"] for s in op_stats.values())
        state["total_allies"] = sum(s["allies"] for s in op_stats.values())
        state["total_hostiles"] = sum(s["hostiles"] for s in op_stats.values())
    # Rumor features
    ru_stats = get_rumor_stats(world)
    if ru_stats:
        state["avg_rumor_count"] = sum(s["count"] for s in ru_stats.values()) / len(ru_stats)
        state["avg_rumor_age"] = sum(s["avg_age"] for s in ru_stats.values()) / len(ru_stats)
        state["avg_rumor_hops"] = sum(s["avg_hops"] for s in ru_stats.values()) / len(ru_stats)
        state["total_rumor_origins"] = sum(s["unique_origins"] for s in ru_stats.values())
    # Saying features - include actual saying texts, not just stats
    sa_stats = get_saying_stats(world)
    if sa_stats:
        state["avg_saying_count"] = sum(s["count"] for s in sa_stats.values()) / len(sa_stats)
        state["avg_saying_age"] = sum(s["avg_age"] for s in sa_stats.values()) / len(sa_stats)
        state["total_saying_diversity"] = sum(s["unique_texts"] for s in sa_stats.values())
        # Include actual saying texts for RL learning
        all_sayings = []
        for fname, fac in world.factions.items():
            sayings = fac.memory.get("sayings", [])
            all_sayings.extend(
                [s.get("text", "") for s in sayings[-5:]]
            )  # Last 5 sayings per faction
        state["recent_sayings"] = all_sayings[:10]  # Limit to 10 most recent sayings total
    # Demographic features
    state["population"] = sum(len(ch.npcs) for ch in world.active_chunks.values())
    state["births_tick"] = getattr(world, "_audit_births_tick", 0)
    state["deaths_starv_tick"] = getattr(world, "_audit_starvation_deaths_tick", 0)
    state["deaths_natural_tick"] = getattr(world, "_audit_natural_deaths_tick", 0)
    # Optionally: add more features as needed
    return state


def get_enhanced_rl_env_state(
    world, include_llm_description: bool = True
) -> Tuple[Dict[str, float], str]:
    """
    Return enhanced RL state with optional LLM-generated description.

    Args:
        world: The world object
        include_llm_description: Whether to generate LLM description

    Returns:
        Tuple of (numerical_state_dict, description_string)
    """
    numerical_state = get_rl_env_state(world)

    if include_llm_description:
        # Get additional context from world
        world_context = ""
        if hasattr(world, "active_chunks") and world.active_chunks:
            total_food = sum(
                sum(npc.food for npc in ch.npcs) for ch in world.active_chunks.values()
            )
            avg_food = (
                total_food / numerical_state["population"]
                if numerical_state["population"] > 0
                else 0
            )
            world_context = f"Average food per person: {avg_food:.1f}"

        description = generate_rl_state_description(numerical_state, world_context)
    else:
        description = ""

    return numerical_state, description
