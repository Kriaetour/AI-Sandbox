#!/usr/bin/env python3
"""Ultra-Aggressive Military RL Training (V2)

Key improvements over original version:
 - Reliable unique state tracking independent of Q-table size
 - Persistent resume of discovered states (JSON file)
 - Per-dimension coverage + recent new state rate instrumentation
 - Adaptive exploration: increases epsilon if plateau detected
 - Smaller, more frequent checkpoints for faster diagnostics

Usage (examples):
  python train_military_ultra_aggressive_v2.py --episodes 5000
  python train_military_ultra_aggressive_v2.py --resume --episodes 20000 --workers 6

The script intentionally remains single-file to simplify iteration while
diagnosing the 600-state plateau.
"""

from __future__ import annotations

import argparse
import json
import math
import os
import random
import time
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Set, Tuple


# --------------------------------------------------------------------------------------
# Configuration Constants
# --------------------------------------------------------------------------------------

TOTAL_STATE_THEORETICAL = 645_120  # 15*12*8*8*7*8
UNIQUE_STATES_FILE = "artifacts/checkpoints/military_unique_states.json"
CHECKPOINT_DIR = "artifacts/checkpoints"
MODEL_DIR = "artifacts/models"
PLATEAU_WINDOW = 2000  # Episodes
PLATEAU_MIN_NEW = 25   # If fewer than this many new states in plateau window -> adapt
ADAPTIVE_EPSILON_INCREMENT = 0.05
ADAPTIVE_EPSILON_MAX = 0.85


# --------------------------------------------------------------------------------------
# Utility
# --------------------------------------------------------------------------------------

def ensure_dirs():
    os.makedirs(CHECKPOINT_DIR, exist_ok=True)
    os.makedirs(MODEL_DIR, exist_ok=True)


def load_unique_states() -> Set[Tuple[int, int, int, int, int, int]]:
    if not os.path.exists(UNIQUE_STATES_FILE):
        return set()
    try:
        with open(UNIQUE_STATES_FILE, "r") as f:
            data = json.load(f)
        raw_states = data.get("states", [])
        return {tuple(s) for s in raw_states if isinstance(s, list) and len(s) == 6}
    except Exception:
        return set()


def save_unique_states(states: Set[Tuple[int, int, int, int, int, int]]):
    try:
        with open(UNIQUE_STATES_FILE, "w") as f:
            json.dump({"count": len(states), "states": [list(s) for s in states]}, f, indent=2)
    except Exception as e:
        print(f"[WARN] Failed saving unique states: {e}")


def save_checkpoint(agent, episode: int, unique_states: Set[Tuple], epsilon: float, training_start: float):
    ensure_dirs()
    meta = {
        "episode": episode,
        "unique_states": len(unique_states),
        "coverage_percent": (len(unique_states) / TOTAL_STATE_THEORETICAL) * 100.0,
        "epsilon": epsilon,
        "timestamp": time.time(),
        "training_time_sec": time.time() - training_start,
    }
    meta_path = os.path.join(CHECKPOINT_DIR, f"ultra_v2_meta_ep{episode}.json")
    with open(meta_path, "w") as f:
        json.dump(meta, f, indent=2)
    agent.save_q_table(os.path.join(CHECKPOINT_DIR, f"military_qtable_ultra_v2_ep{episode}.json"))
    save_unique_states(unique_states)
    print(
        f"💾 Checkpoint ep={episode} states={meta['unique_states']} "
        f"({meta['coverage_percent']:.4f}%) epsilon={epsilon:.2f}"
    )


# --------------------------------------------------------------------------------------
# Worker Episode Execution
# --------------------------------------------------------------------------------------

def run_episode_worker(args):
    """Run one ultra-aggressive episode; return Q-table fragment + states visited.

    Returns dict with: episode, q_table, states_visited (list of tuples), stats.
    """
    (
        episode_num,
        seed_offset,
        base_epsilon,
        debug,
    ) = args

    # Local imports for isolation (avoids cost at module import time)
    from world.engine import WorldEngine
    from tribes.tribal_manager import TribalManager
    from rl_military_agent import MilitaryRLAgent
    from rl_military_interface import (
        execute_military_action,
        compute_military_reward,
    )

    random.seed(seed_offset + episode_num * 137)

    try:
        world_seed = random.randint(0, 9_999_999) + seed_offset * 250_000
        world = WorldEngine(seed=world_seed, disable_faction_saving=True)
        tribal_manager = TribalManager()
        world._tribal_manager = tribal_manager

        # Slight epsilon jitter per episode for diversity
        agent = MilitaryRLAgent(epsilon=min(0.95, max(0.05, random.gauss(base_epsilon, 0.05))), lr=0.25, gamma=0.9)

        # Build diverse tribes
        num_tribes = random.randint(12, 22)
        tribes = []
        for idx in range(num_tribes):
            t = create_diverse_tribe(tribal_manager, world, episode_num, idx, seed_offset)
            tribes.append(t)

        if debug:
            print(f"[DBG ep{episode_num}] created_tribes={len(tribes)} manager_has={len(tribal_manager.tribes)} first={[t.name for t in tribes[:3]]}")

        if len(tribal_manager.tribes) < 3:
            return {
                "episode": episode_num,
                "q_table": {},
                "states_visited": [],
                "stats": {"reason": "insufficient_tribes", "tribes": len(tribal_manager.tribes)},
                "success": True,
            }

        states_visited: Set[Tuple[int, int, int, int, int, int]] = set()
        q_updates = 0
        total_reward = 0.0

        # Rapid decision loop (shortened for debug)
        decision_iterations = 0
        for _tick in range(0, 120, 4):  # Reduced from 360 to 120
            world.world_tick()
            active = list(tribal_manager.tribes.values())
            if len(active) < 3:
                continue
            decisions = random.randint(5, 9)
            for _ in range(decisions):
                actor = random.choice(active)
                targets_pool = [t for t in active if t != actor]
                if len(targets_pool) < 2:
                    continue
                sel_count = min(len(targets_pool), random.randint(2, 6))
                selected = random.sample(targets_pool, sel_count)
                state = agent.get_military_state(actor, selected, world)
                if state is None:
                    continue
                states_visited.add(tuple(int(x) for x in state))
                action_idx = agent.choose_action(state)
                action_name = agent.get_action_name(action_idx)
                action_results = execute_military_action(action_name, actor, selected, tribal_manager, world)
                next_state = agent.get_military_state(actor, selected, world)
                reward = compute_military_reward(action_results, state, next_state)
                if next_state is not None:
                    agent.update_q_table(state, action_idx, reward, next_state)
                    q_updates += 1
                total_reward += reward
                decision_iterations += 1
                if debug and decision_iterations == 1:
                    print(f"[DBG ep{episode_num}] first_state={state} action={action_name}")
                # Force Q-table entry creation for this state
                agent.q_table[state]

        return {
            "episode": episode_num,
            "q_table": agent.q_table,
            "states_visited": [list(s) for s in states_visited],
            "stats": {"q_updates": q_updates, "reward": total_reward, "states": len(states_visited)},
            "success": True,
        }
    except Exception as e:  # pragma: no cover (diagnostic path)
        return {"episode": episode_num, "error": str(e), "success": False}


def create_diverse_tribe(tribal_manager, world, episode_num: int, tribe_idx: int, seed_offset: int):
    from technology_system import technology_manager
    from factions.faction import Faction

    random.seed(seed_offset * 10_000 + episode_num * 997 + tribe_idx * 13)
    archetypes = [
        ("Outpost", (8, 40), 0.3),
        ("Village", (30, 180), 0.6),
        ("Town", (150, 800), 1.2),
        ("City", (700, 1800), 2.0),
        ("Citadel", (1200, 2600), 2.6),
        ("Confederation", (2000, 4200), 4.2),
        ("Metropolis", (2500, 5400), 5.0),
        ("Capital", (4000, 8800), 7.5),
    ]
    name_root, pop_range, res_mult = random.choice(archetypes)
    base_name = f"{name_root}_{episode_num}_{tribe_idx}"
    # Construct faction directly (world.factions is a dict; no create_faction helper here)
    faction = Faction(name=base_name)
    # Attach ad-hoc population attribute (agent power calc checks this gracefully)
    faction.population = random.randint(*pop_range)
    # More varied resource levels with extreme randomization for diversity
    # Mix of destitute, poor, medium, wealthy, and ultra-wealthy tribes
    resource_profiles = [
        (5, 50),      # Destitute
        (20, 200),    # Poor
        (100, 1000),  # Medium
        (500, 5000),  # Wealthy
        (2000, 20000), # Very wealthy
        (10000, 50000), # Ultra wealthy
    ]
    profile = random.choice(resource_profiles)
    base_resources = random.randint(*profile)

    # Add extreme randomization multiplier
    multiplier = random.uniform(0.1, 10.0)  # 10x range!
    base_resources = int(base_resources * multiplier)

    faction.resources = {
        "food": float(int(random.randint(1, max(10, base_resources // 3)) + base_resources * random.uniform(0.5, 2.0))),
        "Wood": float(int(random.randint(1, max(10, base_resources // 3)) + base_resources * random.uniform(0.5, 2.0))),
        "Ore": float(int(random.randint(1, max(5, base_resources // 6)) + base_resources * random.uniform(0.5, 2.0))),
    }
    # Create varied territory footprint for territory_control feature diversity
    territory_radius = random.randint(1, 6)  # Increased max radius
    territory = []
    cx = random.randint(-50, 50)
    cy = random.randint(-50, 50)
    for dx in range(-territory_radius, territory_radius + 1):
        for dy in range(-territory_radius, territory_radius + 1):
            if abs(dx) + abs(dy) <= territory_radius:
                territory.append((cx + dx, cy + dy))
    faction.territory = territory
    # Random diplomatic relationships seeded for earlier factions only (others fill later)
    for existing_name, existing_faction in world.factions.items():
        rel = random.uniform(-1.0, 1.0)
        faction.relationships[existing_name] = rel
        # Ensure reciprocity (symmetric) but with slight noise
        if isinstance(existing_faction, Faction):
            existing_faction.relationships[base_name] = max(-1.0, min(1.0, rel + random.uniform(-0.05, 0.05)))
    all_techs = [
        "weapons",
        "iron_weapons",
        "steel_weapons",
        "military_organization",
        "siege_engineering",
        "horseback_riding",
        "archery",
        "shield_making",
        "castle_building",
        "naval_warfare",
        "gunpowder",
        "cannon",
    ]
    # More varied tech unlocks for better force_readiness diversity
    unlock_count = random.randint(0, len(all_techs))  # Allow 0 techs for some tribes
    if unlock_count > 0:
        technology_manager.unlocked_technologies[base_name] = set(random.sample(all_techs, unlock_count))
    else:
        technology_manager.unlocked_technologies[base_name] = set()
    world.factions[base_name] = faction

    # Ensure a tribe entity exists with same name so TribalManager can provide actors
    # Randomize starting camp near territory center
    start_loc = (cx, cy)
    if base_name not in tribal_manager.tribes:
        tribe = tribal_manager.create_tribe(base_name, start_loc)
        # Harmonize tribe id for technology mapping
        if not hasattr(tribe, 'id'):
            try:
                setattr(tribe, 'id', base_name)
            except Exception:
                pass
    else:
        tribe = tribal_manager.tribes[base_name]

    return tribe


# --------------------------------------------------------------------------------------
# Instrumentation
# --------------------------------------------------------------------------------------

def dimension_coverage(unique_states: Set[Tuple[int, int, int, int, int, int]]):
    if not unique_states:
        return {"dims": [0] * 6, "entropy": 0.0}
    dims = list(zip(*unique_states))
    counts = [len(set(d)) for d in dims]
    # Simple entropy proxy: log(product of unique counts)/log(product of max bins)
    max_bins = [15, 12, 8, 8, 7, 8]
    prod = 1
    prod_max = 1
    for c, m in zip(counts, max_bins):
        prod *= max(1, c)
        prod_max *= m
    entropy_ratio = math.log(prod) / math.log(prod_max)
    return {"dims": counts, "entropy": entropy_ratio}


# --------------------------------------------------------------------------------------
# Main Training Loop
# --------------------------------------------------------------------------------------

def train(
    episodes: int,
    start_episode: int,
    workers: int,
    base_epsilon: float,
    checkpoint_interval: int,
    resume: bool,
    progress_chunk: int,
    debug: bool,
):
    from rl_military_agent import MilitaryRLAgent

    ensure_dirs()
    training_start = time.time()
    unique_states = load_unique_states() if resume else set()
    agent = MilitaryRLAgent(epsilon=base_epsilon, lr=0.25, gamma=0.9)

    last_plateau_check_ep = start_episode
    unique_count_history: List[Tuple[int, int]] = []  # (episode, unique_states)

    total_target_episode = start_episode + episodes
    # Force smaller batch size for rapid diagnostic feedback
    batch_size = 100

    print("=" * 90)
    print(
        f"Ultra-Aggressive V2 Training | start={start_episode} -> target={total_target_episode} | "
        f"workers={workers} resume={resume}"
    )
    print(f"Initial unique states: {len(unique_states)} ({(len(unique_states)/TOTAL_STATE_THEORETICAL)*100:.4f}%)")
    print("=" * 90)

    for batch_start in range(start_episode, total_target_episode, batch_size):
        batch_end = min(batch_start + batch_size, total_target_episode)
        futures = []
        processed_in_batch = 0
        batch_local_states = set()
        with ThreadPoolExecutor(max_workers=workers) as pool:
            for ep in range(batch_start, batch_end):
                seed_offset = ep // 1000
                futures.append(
                    pool.submit(
                        run_episode_worker,
                        (
                            ep,
                            seed_offset,
                            base_epsilon,
                            debug,
                        ),
                    )
                )
            for fut in as_completed(futures):
                result = fut.result()
                if not result.get("success"):
                    print(f"[ERR] Episode {result.get('episode')} failed: {result.get('error')}")
                    continue
                if debug and result.get("stats", {}).get("reason") == "insufficient_tribes":
                    print(f"[DBG ep{result['episode']}] skipped - insufficient tribes")
                # Merge Q-table lazily: only add new states, no averaging here
                for state, qvals in result["q_table"].items():
                    if state not in agent.q_table:
                        agent.q_table[state] = qvals
                    else:
                        # Favor newest value for faster adaptation
                        for i, v in enumerate(qvals):
                            agent.q_table[state][i] = (agent.q_table[state][i] * 0.6) + (v * 0.4)
                # Merge states
                for st in result["states_visited"]:
                    if isinstance(st, list) and len(st) == 6:
                        tup = tuple(int(x) for x in st)
                        unique_states.add(tup)
                        batch_local_states.add(tup)

                processed_in_batch += 1
                if progress_chunk > 0 and processed_in_batch % progress_chunk == 0:
                    coverage_live = (len(unique_states) / TOTAL_STATE_THEORETICAL) * 100
                    print(
                        f"  .. progress: {processed_in_batch}/{len(futures)} eps in batch | "
                        f"batch_new={len(batch_local_states)} total_unique={len(unique_states)} "
                        f"({coverage_live:.4f}%)"
                    )
                    sys.stdout.flush()

        # Instrumentation after batch
        coverage = (len(unique_states) / TOTAL_STATE_THEORETICAL) * 100
        dim_cov = dimension_coverage(unique_states)
        recent_history_segment = [uc for ep, uc in unique_count_history if ep >= batch_start - 1000]
        new_states_last_1k = 0
        if recent_history_segment:
            earliest = recent_history_segment[0]
            new_states_last_1k = len(unique_states) - earliest
        unique_count_history.append((batch_end, len(unique_states)))

        print(
            f"Batch {batch_start}-{batch_end} | unique={len(unique_states)} ({coverage:.4f}%) "
            f"dims={dim_cov['dims']} entropy={dim_cov['entropy']:.3f} new_last1k={new_states_last_1k} eps={base_epsilon:.2f} "
            f"batch_worker_states={len(batch_local_states)}"
        )
        sys.stdout.flush()

        # Defensive warning if no unique states after processing episodes
        if batch_end > batch_start and len(unique_states) == 0:
            print(f"[WARN] Batch processed {batch_end - batch_start} episodes but unique_states still 0. Check state merging logic.")

        # Plateau detection & adaptation
        if batch_end - last_plateau_check_ep >= PLATEAU_WINDOW:
            # Determine unique count at start of window
            start_window_count = 0
            for ep, uc in unique_count_history:
                if ep >= batch_end - PLATEAU_WINDOW:
                    start_window_count = uc
                    break
            gain = len(unique_states) - start_window_count
            if gain < PLATEAU_MIN_NEW and base_epsilon < ADAPTIVE_EPSILON_MAX:
                old_eps = base_epsilon
                base_epsilon = min(ADAPTIVE_EPSILON_MAX, base_epsilon + ADAPTIVE_EPSILON_INCREMENT)
                print(
                    f"[ADAPT] Plateau detected (gain={gain} < {PLATEAU_MIN_NEW}). "
                    f"Increasing epsilon {old_eps:.2f} -> {base_epsilon:.2f}"
                )
            last_plateau_check_ep = batch_end

        # Periodic checkpoint
        if (batch_end - start_episode) % checkpoint_interval == 0:
            save_checkpoint(agent, batch_end, unique_states, base_epsilon, training_start)

    # Final save
    final_model = os.path.join(MODEL_DIR, f"military_qtable_ultra_v2_final_ep{total_target_episode}.json")
    agent.save_q_table(final_model)
    save_unique_states(unique_states)
    print("=" * 90)
    print("TRAINING COMPLETE (Ultra V2)")
    print(f"Episodes processed: {episodes}")
    print(f"Unique states: {len(unique_states)} ({(len(unique_states)/TOTAL_STATE_THEORETICAL)*100:.4f}%)")
    print(f"Model saved: {final_model}")
    print("=" * 90)


# --------------------------------------------------------------------------------------
# CLI
# --------------------------------------------------------------------------------------

def parse_args():
    p = argparse.ArgumentParser(description="Ultra-Aggressive Military RL Training V2")
    p.add_argument("--episodes", type=int, default=5000, help="Number of episodes to run in this invocation")
    p.add_argument("--start-episode", type=int, default=1, help="Starting episode number")
    p.add_argument("--workers", type=int, default=8, help="Thread workers (<= logical cores)")
    p.add_argument("--epsilon", type=float, default=0.55, help="Base epsilon exploration rate")
    p.add_argument(
        "--checkpoint-interval",
        type=int,
        default=1000,
        help="Episodes between checkpoints (approximate; aligns to batch ends)",
    )
    p.add_argument("--resume", action="store_true", help="Resume from persisted unique state set")
    p.add_argument(
        "--progress-chunk",
        type=int,
        default=50,
        help="Print incremental progress every N completed episodes within a batch (0=disable)",
    )
    p.add_argument("--debug", action="store_true", help="Enable verbose debug instrumentation")
    return p.parse_args()


if __name__ == "__main__":  # pragma: no cover
    args = parse_args()
    train(
        episodes=args.episodes,
        start_episode=args.start_episode,
        workers=args.workers,
        base_epsilon=args.epsilon,
        checkpoint_interval=args.checkpoint_interval,
        resume=args.resume,
        progress_chunk=args.progress_chunk,
        debug=args.debug,
    )
