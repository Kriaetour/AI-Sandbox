"""
Opinion RL Interface: Expose state, actions, and reward for RL integration.
"""

import logging
from typing import Dict


def get_opinion_matrix(world) -> Dict[str, Dict[str, float]]:
    """Return the full opinion matrix: {faction: {other: opinion}}."""
    matrix = {}
    for fname, fac in world.factions.items():
        opinions = fac.memory.get("opinions", {})
        matrix[fname] = dict(opinions)
    return matrix


def get_opinion_stats(world) -> Dict[str, Dict[str, float]]:
    """Return summary stats for each faction: mean, min, max, allies, hostiles."""
    stats = {}
    for fname, fac in world.factions.items():
        opinions = list(fac.memory.get("opinions", {}).values())
        if not opinions:
            stats[fname] = {"mean": 0, "min": 0, "max": 0, "allies": 0, "hostiles": 0}
            continue
        mean = sum(opinions) / len(opinions)
        minv = min(opinions)
        maxv = max(opinions)
        allies = sum(1 for v in opinions if v > 0.5)
        hostiles = sum(1 for v in opinions if v < -0.5)
        stats[fname] = {
            "mean": mean,
            "min": minv,
            "max": maxv,
            "allies": allies,
            "hostiles": hostiles,
        }
    return stats


def adjust_opinion(world, source: str, target: str, delta: float):
    """Adjust the opinion of source faction toward target by delta."""
    fac = world.factions.get(source)
    if fac and target in world.factions:
        fac.adjust_opinion(target, delta)
        return True
    return False


def rl_social_action(world, action: str, source: str, target: str = None, extra: dict = None):
    """Perform a high-level RL social action (gift, insult, mediate, propaganda, multi_mediation). Logs all actions."""
    logger = logging.getLogger("rl_actions")
    result = False
    if action == "gift" and target:
        result = adjust_opinion(world, source, target, +0.2)
    elif action == "insult" and target:
        result = adjust_opinion(world, source, target, -0.2)
    elif action == "mediate" and target:
        ok1 = adjust_opinion(world, source, target, +0.1)
        ok2 = adjust_opinion(world, target, source, +0.1)
        result = ok1 and ok2
    elif action == "propaganda" and target:
        for fname in world.factions:
            if fname != source:
                adjust_opinion(world, source, fname, +0.05)
            if fname != target:
                adjust_opinion(world, target, fname, -0.05)
        result = True
    elif action == "multi_mediation" and extra:
        # Mediate between two other factions (improve both directions)
        f1, f2 = extra.get("f1"), extra.get("f2")
        if f1 in world.factions and f2 in world.factions:
            ok1 = adjust_opinion(world, f1, f2, +0.1)
            ok2 = adjust_opinion(world, f2, f1, +0.1)
            result = ok1 and ok2
    # Log the action
    logger.info(
        f"RL_ACTION: {action} source={source} target={target} extra={extra} result={result}"
    )
    return result


def compute_opinion_reward(world) -> float:
    """Reward: mean social cohesion + number of allies - number of hostiles (normalized)."""
    stats = get_opinion_stats(world)
    if not stats:
        return 0.0
    mean_cohesion = sum(s["mean"] for s in stats.values()) / len(stats)
    total_allies = sum(s["allies"] for s in stats.values())
    total_hostiles = sum(s["hostiles"] for s in stats.values())
    # Normalize by number of factions
    n = len(stats)
    reward = mean_cohesion + (total_allies - total_hostiles) / max(1, n)
    return reward
