"""
Saying RL Interface: Expose state, actions, and reward for RL integration.
"""

from typing import Dict, List


def get_all_sayings(world) -> Dict[str, List[dict]]:
    """Return all sayings per faction: {faction: [saying_dict, ...]}"""
    return {fname: list(fac.memory.get("sayings", [])) for fname, fac in world.factions.items()}


def get_saying_stats(world) -> Dict[str, dict]:
    """Return saying stats per faction: count, avg_age, unique_texts, recent_count."""
    stats = {}
    tick = getattr(world, "_tick_count", 0)
    for fname, fac in world.factions.items():
        sayings = fac.memory.get("sayings", [])
        if not sayings:
            stats[fname] = {
                "count": 0,
                "avg_age": 0,
                "unique_texts": 0,
                "recent_count": 0,
            }
            continue
        ages = [tick - s.get("tick", tick) for s in sayings]
        texts = set(s.get("text") for s in sayings)
        recent_count = sum(1 for s in sayings if tick - s.get("tick", tick) <= 50)
        stats[fname] = {
            "count": len(sayings),
            "avg_age": sum(ages) / len(ages),
            "unique_texts": len(texts),
            "recent_count": recent_count,
        }
    return stats


def inject_saying(world, faction: str, text: str):
    """Inject a new saying into a faction's memory (RL action)."""
    fac = world.factions.get(faction)
    tick = getattr(world, "_tick_count", 0)
    if fac:
        entry = {"tick": tick, "text": text}
        fac.memory.setdefault("sayings", []).append(entry)
        return True
    return False


def suppress_saying(world, faction: str, text: str):
    """Remove a saying by text from a faction's memory (RL action)."""
    fac = world.factions.get(faction)
    if fac:
        sayings = fac.memory.get("sayings", [])
        fac.memory["sayings"] = [s for s in sayings if s.get("text") != text]
        return True
    return False


def compute_saying_reward(world) -> float:
    """Reward: encourage saying diversity, recency, and cultural richness using actual saying content."""
    from rl_env_state import get_rl_env_state

    enhanced_state = get_rl_env_state(world)
    recent_sayings = enhanced_state.get("recent_sayings", [])

    if not recent_sayings:
        # Fallback to statistical approach if no sayings available
        stats = get_saying_stats(world)
        if not stats:
            return 0.0
        total_unique = sum(s["unique_texts"] for s in stats.values())
        total_recent = sum(s["recent_count"] for s in stats.values())
        total_age = sum(s["avg_age"] for s in stats.values())
        n = len(stats)
        return (total_unique + 0.5 * total_recent) / max(1, n) - 0.05 * (total_age / max(1, n))

    # Use actual saying content for reward computation
    saying_diversity = len(set(recent_sayings))
    saying_count = len(recent_sayings)

    # Reward for cultural keywords that indicate wisdom/tradition
    cultural_keywords = [
        "remembers",
        "says",
        "wisdom",
        "life",
        "death",
        "land",
        "fires",
        "winds",
        "tomorrow",
        "absence",
    ]
    cultural_score = sum(
        1 for saying in recent_sayings for keyword in cultural_keywords if keyword in saying.lower()
    )

    # Base reward from diversity and cultural content
    reward = saying_diversity * 0.5 + cultural_score * 0.3 + saying_count * 0.1
    return reward
