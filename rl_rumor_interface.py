"""
Rumor RL Interface: Expose state, actions, and reward for RL integration.
"""

import logging
from typing import Dict, List
import random


def get_all_rumors(world) -> Dict[str, List[dict]]:
    """Return all rumors per faction: {faction: [rumor_dict, ...]}"""
    return {fname: list(fac.memory.get("rumors", [])) for fname, fac in world.factions.items()}


def get_rumor_stats(world) -> Dict[str, dict]:
    """Return rumor stats per faction: count, avg_age, unique_origins, avg_hops."""
    stats = {}
    tick = getattr(world, "_tick_count", 0)
    for fname, fac in world.factions.items():
        rumors = fac.memory.get("rumors", [])
        if not rumors:
            stats[fname] = {
                "count": 0,
                "avg_age": 0,
                "unique_origins": 0,
                "avg_hops": 0,
            }
            continue
        ages = [tick - r.get("tick", tick) for r in rumors]
        origins = set(r.get("origin") for r in rumors)
        hops = [r.get("hops", 0) for r in rumors]
        stats[fname] = {
            "count": len(rumors),
            "avg_age": sum(ages) / len(ages),
            "unique_origins": len(origins),
            "avg_hops": sum(hops) / len(hops) if hops else 0,
        }
    return stats


def inject_rumor(world, faction: str, text: str, origin: str = None):
    logger = logging.getLogger("rl_actions")
    """Inject a new rumor into a faction's memory (RL action)."""
    fac = world.factions.get(faction)
    tick = getattr(world, "_tick_count", 0)
    result = False
    if fac:
        rid = f"RL_{tick}_{faction}_{random.randint(0,9999)}"
        entry = {
            "id": rid,
            "text": text,
            "origin": origin or faction,
            "tick": tick,
            "hops": 0,
        }
        fac.memory.setdefault("rumors", []).append(entry)
        result = True
    logger.info(
        f"RL_ACTION: inject_rumor faction={faction} text={text} origin={origin} result={result}"
    )
    return result


def suppress_rumor(world, faction: str, rumor_id: str):
    logger = logging.getLogger("rl_actions")
    """Remove a rumor by id from a faction's memory (RL action)."""
    fac = world.factions.get(faction)
    result = False
    if fac:
        rumors = fac.memory.get("rumors", [])
        fac.memory["rumors"] = [r for r in rumors if r.get("id") != rumor_id]
        result = True
    logger.info(f"RL_ACTION: suppress_rumor faction={faction} rumor_id={rumor_id} result={result}")
    return result


def spread_rumor(world, source: str, target: str, rumor_id: str):
    logger = logging.getLogger("rl_actions")
    """Force a rumor to spread from source to target (RL action)."""
    fac_src = world.factions.get(source)
    fac_tgt = world.factions.get(target)
    result = False
    if fac_src and fac_tgt:
        rumor = next(
            (r for r in fac_src.memory.get("rumors", []) if r.get("id") == rumor_id),
            None,
        )
        if rumor:
            copied = rumor.copy()
            copied["hops"] = rumor.get("hops", 0) + 1
            fac_tgt.memory.setdefault("rumors", []).append(copied)
            result = True
    logger.info(
        f"RL_ACTION: spread_rumor source={source} target={target} rumor_id={rumor_id} result={result}"
    )
    return result


def targeted_rumor_campaign(world, source: str, targets: list, text: str, origin: str = None):
    """Spread a new rumor from source to multiple targets (RL action)."""
    logger = logging.getLogger("rl_actions")
    tick = getattr(world, "_tick_count", 0)
    result = False
    if source in world.factions:
        rid = f"RL_{tick}_{source}_{random.randint(0,9999)}"
        entry = {
            "id": rid,
            "text": text,
            "origin": origin or source,
            "tick": tick,
            "hops": 0,
        }
        for tgt in targets:
            fac_tgt = world.factions.get(tgt)
            if fac_tgt:
                fac_tgt.memory.setdefault("rumors", []).append(entry.copy())
                result = True
    logger.info(
        f"RL_ACTION: targeted_rumor_campaign source={source} targets={targets} text={text} origin={origin} result={result}"
    )
    return result


def compute_rumor_reward(world) -> float:
    """Reward: encourage rumor diversity, spread, and recency."""
    stats = get_rumor_stats(world)
    if not stats:
        return 0.0
    # Reward: sum of unique_origins + avg_hops across all factions, minus avg_age penalty
    total_unique = sum(s["unique_origins"] for s in stats.values())
    total_hops = sum(s["avg_hops"] for s in stats.values())
    total_age = sum(s["avg_age"] for s in stats.values())
    n = len(stats)
    reward = (total_unique + total_hops) / max(1, n) - 0.1 * (total_age / max(1, n))
    return reward
