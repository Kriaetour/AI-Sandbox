#!/usr/bin/env python3
"""
100% State Coverage Training - Systematic State Space Exploration

This script implements a comprehensive approach to achieve 100% coverage of the
647,280 possible military RL states through systematic exploration strategies.
"""

import argparse
import json
import os
import random
import time
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor, as_completed
from typing import List, Set, Tuple, Dict
from collections import defaultdict
import csv

# --------------------------------------------------------------------------------------
# Configuration Constants
# --------------------------------------------------------------------------------------

TOTAL_STATE_THEORETICAL = 647_280  # 15*12*8*8*7*8 = 647,280
UNIQUE_STATES_FILE = "artifacts/checkpoints/military_unique_states_100p.json"
CHECKPOINT_DIR = "artifacts/checkpoints"
MODEL_DIR = "artifacts/models"
METRICS_CSV = "artifacts/military_training_metrics.csv"

# State space dimensions
STATE_DIMS = [15, 12, 8, 8, 7, 8]  # power_ratio, tech_advantage, diplomatic, resource, force, territory

# --------------------------------------------------------------------------------------
# Utility Functions
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

def analyze_coverage_gaps(unique_states: Set[Tuple]) -> Dict:
    """Analyze which state combinations are missing."""
    if not unique_states:
        return {"missing_bins": {}, "total_missing": TOTAL_STATE_THEORETICAL}

    # Count occurrences per bin per dimension
    bin_counts = [defaultdict(int) for _ in range(6)]
    for state in unique_states:
        for dim, value in enumerate(state):
            bin_counts[dim][value] += 1

    missing_bins = {}
    total_missing = 0

    for dim in range(6):
        missing_bins[dim] = []
        for bin_idx in range(STATE_DIMS[dim]):
            if bin_counts[dim][bin_idx] == 0:
                missing_bins[dim].append(bin_idx)
                # Estimate missing combinations for this bin
                other_dims_product = 1
                for other_dim in range(6):
                    if other_dim != dim:
                        other_dims_product *= STATE_DIMS[other_dim]
                total_missing += other_dims_product

    return {
        "missing_bins": missing_bins,
        "total_missing": total_missing,
        "bin_counts": bin_counts
    }

def generate_targeted_scenarios(gaps: Dict, num_scenarios: int = 100) -> List[Dict]:
    """Generate scenarios specifically designed to hit missing state combinations."""
    scenarios = []

    # Handle case where no states exist yet
    if "missing_bins" not in gaps:
        # Create default missing bins for all dimensions
        gaps["missing_bins"] = {i: list(range(STATE_DIMS[i])) for i in range(6)}

    for _ in range(num_scenarios):
        scenario = {
            "target_dims": [],
            "tribe_configs": [],
            "world_seed": random.randint(0, 9999999)
        }

        # Focus on missing dimensions
        if 4 in gaps["missing_bins"] and gaps["missing_bins"][4]:  # force_readiness missing bin 0
            scenario["target_dims"].append(4)
            scenario["force_readiness_target"] = 0
        if 5 in gaps["missing_bins"] and gaps["missing_bins"][5]:  # territory_control missing bins 0,7
            scenario["target_dims"].append(5)
            scenario["territory_target"] = random.choice(gaps["missing_bins"][5])

        # Create tribe configurations to hit these targets
        num_tribes = random.randint(12, 20)  # Increased range for more diversity

        for i in range(num_tribes):
            tribe_config = {
                "population_range": (5, 100) if 4 in scenario["target_dims"] else (20, 800),  # Wider range
                "resource_multiplier": 0.05 if 4 in scenario["target_dims"] else random.uniform(0.2, 8.0),  # More extreme
                "territory_radius": 1 if 5 in scenario["target_dims"] and scenario.get("territory_target") == 0 else random.randint(1, 12),  # Include 1
                "tech_unlocks": 0 if 4 in scenario["target_dims"] else random.randint(0, 15),  # More tech options
                "diplomatic_bias": random.uniform(-1.5, 1.5)  # Wider diplomatic range
            }
            scenario["tribe_configs"].append(tribe_config)

        scenarios.append(scenario)

    return scenarios

# --------------------------------------------------------------------------------------
# Enhanced Episode Worker
# --------------------------------------------------------------------------------------

def run_targeted_episode_worker(args):
    """Run episode with specific targeting for missing state combinations."""
    (
        episode_num,
        scenario_config,
        base_epsilon,
        debug,
    ) = args

    # Local imports for isolation (avoids cost at module import time)
    from world.engine import WorldEngine
    from tribes.tribal_manager import TribalManager
    from rl_military_agent import MilitaryRLAgent
    from rl_military_interface import execute_military_action, compute_military_reward

    random.seed(scenario_config["world_seed"] + episode_num * 137)

    try:
        world = WorldEngine(seed=scenario_config["world_seed"], disable_faction_saving=True)
        tribal_manager = TribalManager()
        world._tribal_manager = tribal_manager

        agent = MilitaryRLAgent(epsilon=min(0.95, max(0.05, base_epsilon)), lr=0.25, gamma=0.9)

        # Create tribes with targeted configurations
        tribes = []
        for i, config in enumerate(scenario_config["tribe_configs"]):
            t = create_targeted_tribe(
                tribal_manager, world, episode_num, i,
                config, scenario_config["world_seed"]
            )
            tribes.append(t)

        if debug:
            print(f"[DBG ep{episode_num}] created {len(tribes)} tribes for targeted scenario")

        if len(tribal_manager.tribes) < 3:
            return {"episode": episode_num, "states_visited": [], "success": True}

        states_visited = set()
        q_updates = 0

        # Extended decision loop for better exploration
        for _tick in range(0, 200, 3):  # Longer episodes
            world.world_tick()
            active = list(tribal_manager.tribes.values())
            if len(active) < 3:
                continue

            decisions = random.randint(12, 20)  # Increased from 8-12 to 12-20
            for _ in range(decisions):
                actor = random.choice(active)
                targets_pool = [t for t in active if t != actor]
                if len(targets_pool) < 2:
                    continue

                sel_count = min(len(targets_pool), random.randint(3, 7))  # Increased from 2-5 to 3-7
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

                # Force Q-table entry
                agent.q_table[state]

        return {
            "episode": episode_num,
            "q_table": agent.q_table,
            "states_visited": [list(s) for s in states_visited],
            "stats": {"q_updates": q_updates, "states": len(states_visited)},
            "success": True,
        }

    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        return {"episode": episode_num, "error": str(e), "traceback": error_details, "success": False}

def create_targeted_tribe(tribal_manager, world, episode_num, tribe_idx, config, world_seed):
    """Create tribe with specific configuration to target missing states."""
    from technology_system import technology_manager
    from factions.faction import Faction

    random.seed(world_seed * 1000 + episode_num * 997 + tribe_idx * 13)

    archetypes = [
        ("Outpost", config["population_range"], 0.3),
        ("Village", config["population_range"], 0.6),
        ("Town", config["population_range"], 1.2),
        ("City", config["population_range"], 2.0),
        ("Citadel", config["population_range"], 2.6),
        ("Confederation", config["population_range"], 4.2),
        ("Metropolis", config["population_range"], 5.0),
        ("Capital", config["population_range"], 7.5),
    ]

    name_root, pop_range, res_mult = random.choice(archetypes)
    base_name = f"{name_root}_{episode_num}_{tribe_idx}"

    faction = Faction(name=base_name)
    faction.population = random.randint(*pop_range)

    # Targeted resource levels
    base_resources = max(10, int(random.randint(10, 100) * config["resource_multiplier"]))
    faction.resources = {
        "food": float(max(1, int(random.randint(1, max(10, base_resources // 3)) + base_resources * random.uniform(0.5, 2.0)))),
        "Wood": float(max(1, int(random.randint(1, max(10, base_resources // 3)) + base_resources * random.uniform(0.5, 2.0)))),
        "Ore": float(max(1, int(random.randint(1, max(5, base_resources // 6)) + base_resources * random.uniform(0.5, 2.0)))),
    }

    # Targeted territory
    territory_radius = min(config["territory_radius"], 8)  # Cap at 8 to avoid world boundary issues
    territory = []
    cx = random.randint(-40, 40)  # Reduced range to avoid edge issues
    cy = random.randint(-40, 40)
    for dx in range(-territory_radius, territory_radius + 1):
        for dy in range(-territory_radius, territory_radius + 1):
            if abs(dx) + abs(dy) <= territory_radius:
                territory.append((cx + dx, cy + dy))
    faction.territory = territory

    # Diplomatic relationships with bias
    for existing_name, existing_faction in world.factions.items():
        rel = config["diplomatic_bias"] + random.uniform(-0.2, 0.2)
        rel = max(-1.0, min(1.0, rel))
        faction.relationships[existing_name] = rel
        if isinstance(existing_faction, Faction):
            existing_faction.relationships[base_name] = rel

    # Targeted technology unlocks
    all_techs = [
        "weapons", "iron_weapons", "steel_weapons", "military_organization",
        "siege_engineering", "horseback_riding", "archery", "shield_making",
        "castle_building", "naval_warfare", "gunpowder", "cannon"
    ]

    unlock_count = config["tech_unlocks"]
    if unlock_count > 0:
        # Ensure we don't try to sample more techs than available
        max_techs = len(all_techs)
        actual_unlock_count = min(unlock_count, max_techs)
        technology_manager.unlocked_technologies[base_name] = set(random.sample(all_techs, actual_unlock_count))
    else:
        technology_manager.unlocked_technologies[base_name] = set()

    world.factions[base_name] = faction

    # Create tribe entity
    if base_name not in tribal_manager.tribes:
        tribe = tribal_manager.create_tribe(base_name, (cx, cy))
        if not hasattr(tribe, 'id'):
            setattr(tribe, 'id', base_name)

    return tribal_manager.tribes[base_name]

# --------------------------------------------------------------------------------------
# Main 100% Coverage Training
# --------------------------------------------------------------------------------------

def train_100_percent(
    episodes: int,
    workers: int = 8,
    resume: bool = True,
    executor_type: str = "thread",
    merge_q: bool = True,
    adaptive_batch: bool = False,
    batch_initial: int = 50,
    batch_min: int = 10,
    batch_max: int = 200,
    batch_target_seconds: float = 8.0,
    batch_ema_alpha: float = 0.3,
):
    """Main training function for achieving 100% state coverage."""
    from rl_military_agent import MilitaryRLAgent

    ensure_dirs()
    training_start = time.time()

    # Load existing states
    unique_states = load_unique_states() if resume else set()
    agent = MilitaryRLAgent(epsilon=0.8, lr=0.25, gamma=0.9)  # Higher epsilon for exploration

    # Initialize metrics CSV
    csv_writer = None
    csv_file = None
    if adaptive_batch or True:  # Always log for now
        csv_file = open(METRICS_CSV, 'w', newline='')
        csv_writer = csv.writer(csv_file)
        csv_writer.writerow([
            'batch_start_ep', 'batch_end_ep', 'new_states', 'batch_seconds', 'ema_seconds',
            'states_per_second', 'cumulative_states', 'coverage_percent', 'q_updates'
        ])

    # Initialize metrics CSV
    csv_writer = None
    if adaptive_batch or True:  # Always log for now
        csv_file = open(METRICS_CSV, 'w', newline='')
        csv_writer = csv.writer(csv_file)
        csv_writer.writerow([
            'batch_start_ep', 'batch_end_ep', 'new_states', 'batch_seconds', 'ema_seconds',
            'states_per_second', 'cumulative_states', 'coverage_percent', 'q_updates'
        ])

    print("=" * 100)
    print("🚀 100% STATE COVERAGE TRAINING INITIATED")
    print("=" * 100)
    print(f"Target: {TOTAL_STATE_THEORETICAL:,} states (100.0%)")
    print(f"Current: {len(unique_states):,} states ({len(unique_states)/TOTAL_STATE_THEORETICAL*100:.2f}%)")
    print(f"Remaining: {TOTAL_STATE_THEORETICAL - len(unique_states):,} states")
    print(f"Executor: {executor_type} | Merge Q-Tables: {merge_q}")
    print("=" * 100)

    # Phase 1: Analyze gaps and create targeted scenarios
    print("\n📊 PHASE 1: Analyzing Coverage Gaps...")
    gaps = analyze_coverage_gaps(unique_states)
    print(f"Missing combinations estimated: {gaps['total_missing']:,}")

    for dim, missing in gaps['missing_bins'].items():
        if missing:
            dim_names = ['power_ratio', 'tech_advantage', 'diplomatic', 'resource', 'force_readiness', 'territory']
            print(f"  {dim_names[dim]} missing bins: {missing}")

    # Phase 2: Generate targeted scenarios
    print("\n🎯 PHASE 2: Generating Targeted Scenarios...")
    scenarios = generate_targeted_scenarios(gaps, num_scenarios=2000)  # Increased from 1000
    print(f"Generated {len(scenarios)} targeted scenarios")

    # Phase 3: Execute training with systematic exploration
    print("\n⚡ PHASE 3: Executing Systematic Exploration...")

    episode_count = 0
    batch_size = batch_initial if adaptive_batch else 200  # Increased default batch size

    ExecutorClass = ThreadPoolExecutor if executor_type == "thread" else ProcessPoolExecutor
    ema_batch_time = None
    with ExecutorClass(max_workers=workers) as pool:
        while episode_count < episodes and len(unique_states) < TOTAL_STATE_THEORETICAL:
            batch_start = episode_count
            batch_end = min(episode_count + batch_size, episodes)
            batch_t0 = time.time()
            states_before = len(unique_states)

            batch_scenarios = random.sample(scenarios, min(batch_size, len(scenarios)))

            futures = []
            for ep_idx in range(batch_start, batch_end):
                scenario = batch_scenarios[ep_idx - batch_start]
                # Epsilon scheduling: high exploration early, decrease over time
                progress_ratio = ep_idx / episodes
                scheduled_epsilon = max(0.4, 0.9 - (progress_ratio * 0.5))  # 0.9 -> 0.4 over training
                futures.append(
                    pool.submit(
                        run_targeted_episode_worker,
                        (ep_idx, scenario, scheduled_epsilon, False)
                    )
                )

            for fut in as_completed(futures):
                result = fut.result()
                if not result.get("success"):
                    error_msg = result.get("error", "Unknown error")
                    if "traceback" in result:
                        print(f"[ERR] Episode {result.get('episode')} failed: {error_msg}")
                        print(f"[TRACEBACK] {result['traceback'][:500]}...")  # First 500 chars
                    else:
                        print(f"[ERR] Episode {result.get('episode')} failed: {error_msg}")
                    continue

                for st in result["states_visited"]:
                    if isinstance(st, list) and len(st) == 6:
                        unique_states.add(tuple(int(x) for x in st))

                if merge_q:
                    for state, qvals in result["q_table"].items():
                        if state not in agent.q_table:
                            agent.q_table[state] = qvals

            episode_count = batch_end
            batch_elapsed = time.time() - batch_t0
            new_states = len(unique_states) - states_before

            # Write metrics to CSV
            if csv_writer:
                states_per_second = new_states / batch_elapsed if batch_elapsed > 0 else 0
                q_updates = sum(result.get("stats", {}).get("q_updates", 0) for result in [fut.result() for fut in futures] if result.get("success"))
                csv_writer.writerow([
                    batch_start, batch_end, new_states, batch_elapsed, ema_batch_time or 0,
                    states_per_second, len(unique_states), (len(unique_states) / TOTAL_STATE_THEORETICAL) * 100, q_updates
                ])

            # Progress reporting & smoothing
            coverage = (len(unique_states) / TOTAL_STATE_THEORETICAL) * 100
            if ema_batch_time is None:
                ema_batch_time = batch_elapsed
            else:
                ema_batch_time = batch_ema_alpha * batch_elapsed + (1 - batch_ema_alpha) * ema_batch_time
            print(
                f"Progress: {episode_count}/{episodes} episodes | "
                f"States: {len(unique_states):,} ({coverage:.3f}%) | "
                f"Remaining: {TOTAL_STATE_THEORETICAL - len(unique_states):,} | "
                f"Batch {batch_size} took {batch_elapsed:.2f}s (EMA {ema_batch_time:.2f}s)"
            )

            # Adaptive batch tuning
            if adaptive_batch and batch_elapsed > 0:
                # Aim for batch_target_seconds; simple proportional control
                effective_time = ema_batch_time if ema_batch_time else batch_elapsed
                ratio = batch_target_seconds / effective_time
                # Dampening factor to avoid oscillation
                new_batch = int(batch_size * (0.5 + 0.5 * ratio))
                new_batch = max(batch_min, min(batch_max, new_batch))
                if new_batch != batch_size:
                    print(f"[ADAPT] {batch_size} -> {new_batch} (raw={batch_elapsed:.2f}s ema={ema_batch_time:.2f}s target={batch_target_seconds}s)")
                    batch_size = new_batch

            # Checkpoint every 500 episodes
            if episode_count % 500 == 0:
                checkpoint_file = os.path.join(CHECKPOINT_DIR, f"military_100p_checkpoint_ep{episode_count}.json")
                agent.save_q_table(checkpoint_file)
                save_unique_states(unique_states)
                print(f"💾 Checkpoint saved: {checkpoint_file}")

            # Check for completion
            if len(unique_states) >= TOTAL_STATE_THEORETICAL:
                print("\n🎉 100% COVERAGE ACHIEVED!")
                break

    # Final results
    final_coverage = (len(unique_states) / TOTAL_STATE_THEORETICAL) * 100
    training_time = time.time() - training_start

    print("\n" + "=" * 100)
    print("🏁 TRAINING COMPLETE")
    print("=" * 100)
    print(f"Episodes processed: {episode_count}")
    print(f"Unique states discovered: {len(unique_states):,}")
    print(f"Final coverage: {final_coverage:.4f}%")
    print(f"Training time: {training_time:.1f} seconds")
    print(f"States per second: {len(unique_states)/training_time:.1f}")

    if final_coverage >= 100.0:
        print("\n🎯 MISSION ACCOMPLISHED: 100% STATE COVERAGE ACHIEVED!")
    else:
        remaining = TOTAL_STATE_THEORETICAL - len(unique_states)
        print(f"\n📈 Progress made: {remaining:,} states still needed for 100%")

    # Save final model
    final_model = os.path.join(MODEL_DIR, f"military_100p_final_ep{episode_count}.json")
    agent.save_q_table(final_model)
    save_unique_states(unique_states)

    # Close CSV
    if csv_file:
        csv_file.close()

    print(f"Final model saved: {final_model}")
    print(f"Unique states saved: {UNIQUE_STATES_FILE}")
    print(f"Metrics CSV saved: {METRICS_CSV}")
    print("=" * 100)

# --------------------------------------------------------------------------------------
# CLI
# --------------------------------------------------------------------------------------

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="100% State Coverage Training")
    parser.add_argument("--episodes", type=int, default=10000, help="Number of episodes to run")
    parser.add_argument("--workers", type=int, default=8, help="Number of workers (threads or processes)")
    parser.add_argument("--resume", action="store_true", default=True, help="Resume from existing states")
    parser.add_argument("--executor", choices=["thread", "process"], default="thread", help="Executor type")
    parser.add_argument("--merge-q", action="store_true", help="Enable merging Q-tables from workers (default: disabled for faster coverage)")
    parser.add_argument("--no-merge-q", action="store_true", help="Disable merging Q-tables (deprecated, use --merge-q instead)")
    parser.add_argument("--adaptive-batch", action="store_true", help="Enable adaptive batch sizing")
    parser.add_argument("--batch-initial", type=int, default=50, help="Initial batch size when adaptive on")
    parser.add_argument("--batch-min", type=int, default=10, help="Minimum adaptive batch size")
    parser.add_argument("--batch-max", type=int, default=200, help="Maximum adaptive batch size")
    parser.add_argument("--batch-target-seconds", type=float, default=8.0, help="Target seconds per batch for adaptation")
    parser.add_argument("--batch-ema-alpha", type=float, default=0.3, help="EMA alpha for batch time smoothing (0-1)")

    args = parser.parse_args()
    train_100_percent(
        args.episodes,
        args.workers,
        args.resume,
        executor_type=args.executor,
        merge_q=args.merge_q or (args.no_merge_q and not args.merge_q),
        adaptive_batch=args.adaptive_batch,
        batch_initial=args.batch_initial,
        batch_min=args.batch_min,
        batch_max=args.batch_max,
        batch_target_seconds=args.batch_target_seconds,
        batch_ema_alpha=args.batch_ema_alpha,
    )