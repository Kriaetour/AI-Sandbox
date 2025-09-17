"""
Tribal Diplomacy RL Interface: Expose state, actions, and reward
for RL integration.
"""

import logging
from typing import Dict, List


def get_diplomacy_matrix(world) -> Dict[str, Dict[str, float]]:
    """Return the full diplomacy matrix: {tribe: {other: diplomacy_level}}."""
    matrix = {}
    # Get diplomacy from tribal manager
    tribal_manager = getattr(world, "_tribal_manager", None)
    if tribal_manager and hasattr(tribal_manager, "tribal_diplomacy"):
        tribes = list(tribal_manager.tribes.keys())
        for tribe_a in tribes:
            matrix[tribe_a] = {}
            for tribe_b in tribes:
                if tribe_a != tribe_b:
                    matrix[tribe_a][tribe_b] = tribal_manager.tribal_diplomacy.get_trust_level(
                        tribe_a, tribe_b
                    )
    return matrix


def get_diplomacy_stats(world) -> Dict[str, Dict[str, float]]:
    """Return summary stats for each tribe: allies, rivals, neutral,
    avg_diplomacy."""
    stats = {}
    tribal_manager = getattr(world, "_tribal_manager", None)
    if tribal_manager and hasattr(tribal_manager, "tribal_diplomacy"):
        tribes = list(tribal_manager.tribes.keys())
        for tribe_name in tribes:
            diplomacy_values = []
            for other_tribe in tribes:
                if tribe_name != other_tribe:
                    level = tribal_manager.tribal_diplomacy.get_trust_level(tribe_name, other_tribe)
                    diplomacy_values.append(level)

            if not diplomacy_values:
                stats[tribe_name] = {
                    "allies": 0,
                    "rivals": 0,
                    "neutral": 0,
                    "avg_diplomacy": 0.0,
                }
                continue

            allies = sum(1 for v in diplomacy_values if v > 0.5)
            rivals = sum(1 for v in diplomacy_values if v < -0.5)
            neutral = len(diplomacy_values) - allies - rivals
            avg_diplomacy = sum(diplomacy_values) / len(diplomacy_values)

            stats[tribe_name] = {
                "allies": allies,
                "rivals": rivals,
                "neutral": neutral,
                "avg_diplomacy": avg_diplomacy,
            }
    return stats


def get_tribal_state(world) -> Dict[str, Dict]:
    """Return comprehensive tribal state for RL: population, resources,
    culture, etc."""
    state = {}
    tribal_manager = getattr(world, "_tribal_manager", None)
    if tribal_manager:
        for tribe_name, tribe in tribal_manager.tribes.items():
            # Basic tribal info
            tribal_info = {
                "population": (len(tribe.members) if hasattr(tribe, "members") else 0),
                "location": getattr(tribe, "location", (0, 0)),
                "culture": getattr(tribe, "cultural_values", {}),
                "specialization": getattr(tribe, "economic_specialization", "general"),
                "resources": {},
                "military_strength": 0,
            }

            # Get faction resources if available
            faction = world.factions.get(tribe_name)
            if faction:
                tribal_info["resources"] = {
                    "food": faction.resources.get("food", 0),
                    "ore": faction.resources.get("ore", 0),
                    "wood": faction.resources.get("wood", 0),
                }
                # Estimate military strength from population
                tribal_info["military_strength"] = len(faction.members)

            state[tribe_name] = tribal_info

    return state


def propose_alliance(world, source_tribe: str, target_tribe: str) -> bool:
    """RL action: Propose an alliance between two tribes."""
    logger = logging.getLogger("rl_actions")
    tribal_manager = getattr(world, "_tribal_manager", None)

    if not tribal_manager or not hasattr(tribal_manager, "tribal_diplomacy"):
        logger.warning("RL_ACTION: propose_alliance failed - no tribal diplomacy system")
        return False

    # Check if tribes exist
    if source_tribe not in tribal_manager.tribes or target_tribe not in tribal_manager.tribes:
        logger.warning(
            f"RL_ACTION: propose_alliance failed - tribe not found: "
            f"{source_tribe} or {target_tribe}"
        )
        return False

    # Improve diplomacy
    current_level = tribal_manager.tribal_diplomacy.get_trust_level(source_tribe, target_tribe)
    new_level = min(1.0, current_level + 0.3)  # Significant positive boost

    tribal_manager.tribal_diplomacy.set_trust_level(source_tribe, target_tribe, new_level)

    logger.info(
        f"RL_ACTION: propose_alliance {source_tribe} -> {target_tribe} "
        f"(diplomacy: {current_level:.2f} -> {new_level:.2f})"
    )
    return True


def declare_rivalry(world, source_tribe: str, target_tribe: str) -> bool:
    """RL action: Declare rivalry/hostility toward another tribe."""
    logger = logging.getLogger("rl_actions")
    tribal_manager = getattr(world, "_tribal_manager", None)

    if not tribal_manager or not hasattr(tribal_manager, "tribal_diplomacy"):
        logger.warning("RL_ACTION: declare_rivalry failed - no tribal diplomacy system")
        return False

    # Check if tribes exist
    if source_tribe not in tribal_manager.tribes or target_tribe not in tribal_manager.tribes:
        logger.warning(
            f"RL_ACTION: declare_rivalry failed - tribe not found: {source_tribe} or {target_tribe}"
        )
        return False

    # Worsen diplomacy
    current_level = tribal_manager.tribal_diplomacy.get_trust_level(source_tribe, target_tribe)
    new_level = max(-1.0, current_level - 0.4)  # Significant negative impact

    tribal_manager.tribal_diplomacy.set_trust_level(source_tribe, target_tribe, new_level)

    logger.info(
        f"RL_ACTION: declare_rivalry {source_tribe} -> {target_tribe} (diplomacy: {current_level:.2f} -> {new_level:.2f})"
    )
    return True


def mediate_conflict(world, mediator_tribe: str, tribe_a: str, tribe_b: str) -> bool:
    """RL action: Attempt to mediate conflict between two rival tribes."""
    logger = logging.getLogger("rl_actions")
    tribal_manager = getattr(world, "_tribal_manager", None)

    if not tribal_manager or not hasattr(tribal_manager, "tribal_diplomacy"):
        logger.warning("RL_ACTION: mediate_conflict failed - no tribal diplomacy system")
        return False

    # Check if all tribes exist
    tribes = [mediator_tribe, tribe_a, tribe_b]
    for tribe in tribes:
        if tribe not in tribal_manager.tribes:
            logger.warning(f"RL_ACTION: mediate_conflict failed - tribe not found: {tribe}")
            return False

    # Check if there's actual conflict to mediate
    diplomacy_a_to_b = tribal_manager.tribal_diplomacy.get_trust_level(tribe_a, tribe_b)
    if diplomacy_a_to_b > -0.3:  # Not really hostile
        logger.info(
            f"RL_ACTION: mediate_conflict {mediator_tribe} - no significant conflict between {tribe_a} and {tribe_b}"
        )
        return False

    # Mediation attempt - small improvement for both sides
    improvement = 0.15
    tribal_manager.tribal_diplomacy.set_trust_level(
        tribe_a, tribe_b, min(1.0, diplomacy_a_to_b + improvement)
    )

    # Slight positive boost toward mediator
    mediator_a_level = tribal_manager.tribal_diplomacy.get_trust_level(tribe_a, mediator_tribe)
    mediator_b_level = tribal_manager.tribal_diplomacy.get_trust_level(tribe_b, mediator_tribe)
    tribal_manager.tribal_diplomacy.set_trust_level(
        tribe_a, mediator_tribe, min(1.0, mediator_a_level + 0.1)
    )
    tribal_manager.tribal_diplomacy.set_trust_level(
        tribe_b, mediator_tribe, min(1.0, mediator_b_level + 0.1)
    )

    logger.info(
        f"RL_ACTION: mediate_conflict {mediator_tribe} mediated between {tribe_a} and {tribe_b} (diplomacy improved by {improvement})"
    )
    return True


def form_trade_agreement(world, tribe_a: str, tribe_b: str) -> bool:
    """RL action: Establish or strengthen trade relations between tribes."""
    logger = logging.getLogger("rl_actions")
    tribal_manager = getattr(world, "_tribal_manager", None)

    if not tribal_manager or not hasattr(tribal_manager, "tribal_diplomacy"):
        logger.warning("RL_ACTION: form_trade_agreement failed - no tribal diplomacy system")
        return False

    # Check if tribes exist
    if tribe_a not in tribal_manager.tribes or tribe_b not in tribal_manager.tribes:
        logger.warning(
            f"RL_ACTION: form_trade_agreement failed - tribe not found: {tribe_a} or {tribe_b}"
        )
        return False

    # Boost diplomacy through trade
    current_level = tribal_manager.tribal_diplomacy.get_trust_level(tribe_a, tribe_b)
    new_level = min(1.0, current_level + 0.25)  # Moderate positive boost

    tribal_manager.tribal_diplomacy.set_trust_level(tribe_a, tribe_b, new_level)

    logger.info(
        f"RL_ACTION: form_trade_agreement {tribe_a} <-> {tribe_b} (diplomacy: {current_level:.2f} -> {new_level:.2f})"
    )
    return True


def compute_diplomacy_reward(world) -> float:
    """Compute reward based on overall diplomatic stability and cooperation."""
    tribal_manager = getattr(world, "_tribal_manager", None)
    if not tribal_manager or not hasattr(tribal_manager, "tribal_diplomacy"):
        return 0.0

    total_diplomacy = 0.0
    relationship_count = 0

    # Sum all diplomatic relationships
    tribes = list(tribal_manager.tribes.keys())
    for i, source_tribe in enumerate(tribes):
        for target_tribe in tribes[i + 1 :]:  # Avoid double-counting
            diplomacy_level = tribal_manager.tribal_diplomacy.get_trust_level(
                source_tribe, target_tribe
            )
            total_diplomacy += diplomacy_level
            relationship_count += 1

    if relationship_count == 0:
        return 0.0

    avg_diplomacy = total_diplomacy / relationship_count

    # Reward positive diplomacy, penalize negative
    reward = avg_diplomacy * 10.0  # Scale to reasonable reward range

    return reward


def get_diplomacy_actions() -> List[str]:
    """Return list of available diplomacy actions for RL."""
    return [
        "propose_alliance",
        "declare_rivalry",
        "mediate_conflict",
        "form_trade_agreement",
        "diplomacy_noop",
    ]


def get_diplomacy_state_vector(world) -> List[float]:
    """Return normalized state vector for diplomacy RL."""
    stats = get_diplomacy_stats(world)
    tribal_state = get_tribal_state(world)

    state_vector = []

    # Overall diplomacy metrics
    all_avg_diplomacy = [s["avg_diplomacy"] for s in stats.values()]
    if all_avg_diplomacy:
        state_vector.extend(
            [
                (sum(all_avg_diplomacy) / len(all_avg_diplomacy)),  # Global avg diplomacy
                max(all_avg_diplomacy),  # Best relationship
                min(all_avg_diplomacy),  # Worst relationship
            ]
        )
    else:
        state_vector.extend([0.0, 0.0, 0.0])

    # Tribal population balance (normalized)
    populations = [t["population"] for t in tribal_state.values()]
    if populations:
        max_pop = max(populations)
        avg_pop = sum(populations) / len(populations)
        state_vector.extend(
            [
                avg_pop / 100.0,  # Normalized average population
                max_pop / 200.0,  # Normalized max population
                (
                    len([p for p in populations if p > 10]) / len(populations)
                ),  # Fraction of established tribes
            ]
        )
    else:
        state_vector.extend([0.0, 0.0, 0.0])

    # Resource distribution (simplified)
    total_food = sum(t["resources"].get("food", 0) for t in tribal_state.values())
    state_vector.append(total_food / 1000.0)  # Normalized total food

    return state_vector
