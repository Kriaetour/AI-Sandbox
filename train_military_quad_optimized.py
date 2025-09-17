#!/usr/bin/env python3
"""
Optimized Ultra-Extended Training for Quad-Core Systems.

This version focuses on memory efficiency, better state exploration,
and optimal CPU utilization for quad-core systems rather than parallelism.
"""

import time
import random
import json
import os
import gc
from concurrent.futures import ProcessPoolExecutor, as_completed
from datetime import datetime

from world.engine import WorldEngine
from tribes.tribal_manager import TribalManager
from rl_military_agent import MilitaryRLAgent
from rl_military_interface import (
    execute_military_action,
    compute_military_reward
)
from technology_system import technology_manager


def create_ultra_diverse_tribe(tribal_manager, world, episode_num, tribe_idx, seed_offset, diversity_level=1.0):
    """Create a tribe with ultra-high diversity for maximum state coverage."""
    random.seed(seed_offset + episode_num * 1000 + tribe_idx * 100)

    # Ultra-diverse tribe characteristics - expanded for better coverage
    tribe_types = [
        {"name": "Tiny_Outpost", "pop_range": (5, 50), "resource_multiplier": 0.2},
        {"name": "Small_Village", "pop_range": (20, 150), "resource_multiplier": 0.5},
        {"name": "Medium_Settlement", "pop_range": (100, 600), "resource_multiplier": 1.0},
        {"name": "Large_Town", "pop_range": (400, 1200), "resource_multiplier": 1.5},
        {"name": "Major_City", "pop_range": (1000, 2000), "resource_multiplier": 2.0},
        {"name": "Metropolis", "pop_range": (1800, 3000), "resource_multiplier": 3.0},
        {"name": "Nomadic_Clan", "pop_range": (10, 100), "resource_multiplier": 0.3},
        {"name": "Fortified_Citadel", "pop_range": (800, 2500), "resource_multiplier": 2.5},
        {"name": "Tribal_Confederation", "pop_range": (1500, 4000), "resource_multiplier": 4.0},
    ]

    # Add extreme diversity for later episodes
    if diversity_level > 1.5:
        tribe_types.extend([
            {"name": "Mega_City", "pop_range": (3000, 5000), "resource_multiplier": 5.0},
            {"name": "Dwarf_Outpost", "pop_range": (2, 20), "resource_multiplier": 0.1},
            {"name": "Resource_Rich_Haven", "pop_range": (200, 800), "resource_multiplier": 6.0},
        ])

    tribe_type = random.choice(tribe_types)
    base_name = f"{tribe_type['name']}_{episode_num}_{tribe_idx}"

    # Generate ultra-diverse location
    location = (
        random.randint(-200, 200),
        random.randint(-200, 200)
    )

    # Generate population with more variation
    population = random.randint(*tribe_type['pop_range'])
    population = int(population * random.uniform(0.8, 1.3))

    # Generate resources with extreme variance
    resource_multiplier = tribe_type['resource_multiplier'] * random.uniform(0.5, 2.0)
    base_resources = {
        "food": int(random.randint(10, 1000) * resource_multiplier),
        "wood": int(random.randint(5, 800) * resource_multiplier),
        "ore": int(random.randint(1, 500) * resource_multiplier)
    }

    # Create tribe (following the working pattern)
    founder_id = f"founder_{base_name.lower()}"
    tribal_manager.create_tribe(base_name, founder_id, location)

    # Create faction with ultra-diverse characteristics
    if base_name not in world.factions:
        from factions.faction import Faction
        faction = Faction(name=base_name)
        faction.territory = [location]
        faction.population = population
        faction.resources = base_resources

        # Technology diversity
        tech_probability = min(0.8, 0.2 + diversity_level * 0.1)
        if random.random() < tech_probability:
            all_techs = [
                "weapons", "iron_weapons", "steel_weapons", "military_organization",
                "siege_engineering", "horseback_riding", "archery", "shield_making"
            ]
            num_techs = random.randint(0, min(len(all_techs), int(diversity_level * 3)))
            tech_unlocks = random.sample(all_techs, num_techs)
            if tech_unlocks:
                technology_manager.unlocked_technologies[base_name] = set(tech_unlocks)

        world.factions[base_name] = faction

    return base_name, population, base_resources


def run_optimized_episode(args):
    """Optimized episode runner with memory efficiency."""
    episode_num, seed_offset, diversity_level = args

    try:
        # Create scenario with memory optimization
        world_seed = random.randint(0, 10000000) + seed_offset * 100000
        world = WorldEngine(seed=world_seed, disable_faction_saving=True)
        tribal_manager = TribalManager()
        world._tribal_manager = tribal_manager

        # Agent with optimized exploration decay
        epsilon = max(0.02, 0.4 - episode_num * 0.000008)  # Slower decay for more exploration
        agent = MilitaryRLAgent(epsilon=epsilon, lr=0.12, gamma=0.95)  # Adjusted learning rate

        # Create 6-12 tribes (optimized for quad-core)
        num_tribes = random.randint(6, 12)

        # Initialize tribes
        tribe_info = []
        for i in range(num_tribes):
            tribe_data = create_ultra_diverse_tribe(tribal_manager, world, episode_num, i, seed_offset, diversity_level)
            tribe_info.append(tribe_data)

        # Run episode with optimized decision frequency
        episode_stats = {
            'combats_initiated': 0,
            'successful_combats': 0,
            'total_reward': 0.0,
            'states_visited': set(),
            'q_updates': 0,
            'tribe_diversity': {
                'populations': [info[1] for info in tribe_info],
                'total_resources': [sum(info[2].values()) for info in tribe_info]
            }
        }

        # Run for 150 ticks with decisions every 4 ticks (more frequent decisions)
        for tick in range(0, 150, 4):
            world.world_tick()

            active_tribes = list(tribal_manager.tribes.values())

            if len(active_tribes) < 2:
                continue

            # Multiple decisions per tick - increased for better learning
            num_decisions = random.randint(3, 6)
            for _ in range(num_decisions):
                actor_tribe = random.choice(active_tribes)
                target_tribes = [t for t in active_tribes if t != actor_tribe]

                if not target_tribes:
                    continue

                target_tribe = random.choice(target_tribes)

                # Get state and make decision
                state = agent.get_state(actor_tribe, target_tribe, world)
                action_idx = agent.choose_action(state)

                # Execute action
                success = execute_military_action(
                    actor_tribe, target_tribe, action_idx, world
                )

                # Compute reward
                reward = compute_military_reward(
                    actor_tribe, target_tribe, action_idx, success, world
                )

                # Learn
                next_state = agent.get_state(actor_tribe, target_tribe, world)
                agent.learn(state, action_idx, reward, next_state)

                # Track stats
                episode_stats['combats_initiated'] += 1
                if success:
                    episode_stats['successful_combats'] += 1
                episode_stats['total_reward'] += reward
                episode_stats['states_visited'].add(state)
                episode_stats['q_updates'] += 1

        # Clean up memory
        del world
        del tribal_manager
        gc.collect()

        return {
            'success': True,
            'episode': episode_num,
            'q_table': agent.q_table,
            'stats': episode_stats
        }

    except Exception as e:
        return {
            'success': False,
            'episode': episode_num,
            'error': str(e),
            'q_table': {},
            'stats': {}
        }


def run_ultra_training_optimized(num_episodes=20000, num_workers=8, checkpoint_interval=1000, batch_size=200):
    """Optimized training for quad-core systems with memory efficiency."""

    print("Starting OPTIMIZED Ultra-Extended Military RL Training")
    print(f"Target Episodes: {num_episodes}")
    print(f"Workers: {num_workers} (optimized for quad-core)")
    print(f"Batch Size: {batch_size}")
    print(f"Checkpoint Interval: {checkpoint_interval}")
    print("=" * 80)

    start_time = time.time()

    # Check for existing checkpoint
    checkpoint_dir = "artifacts/checkpoints"
    os.makedirs(checkpoint_dir, exist_ok=True)

    start_episode = 0
    master_agent = MilitaryRLAgent(epsilon=0.1, lr=0.1, gamma=0.9)

    # Try to resume from latest checkpoint
    checkpoint_files = [f for f in os.listdir(checkpoint_dir) if f.startswith("military_checkpoint_ep")]
    if checkpoint_files:
        checkpoint_files.sort(key=lambda x: int(x.split('_ep')[1].split('.')[0]))
        latest_checkpoint = checkpoint_files[-1]
        checkpoint_path = os.path.join(checkpoint_dir, latest_checkpoint)

        try:
            with open(checkpoint_path, 'r') as f:
                checkpoint_data = json.load(f)

            start_episode = checkpoint_data['episode']
            master_agent.q_table = checkpoint_data['q_table']
            total_states_learned = len(master_agent.q_table)

            print(f"Resuming from checkpoint: Episode {start_episode}")
            print(f"States already learned: {total_states_learned}")

        except Exception as e:
            print(f"Failed to load checkpoint: {e}")
            start_episode = 0

    total_states_learned = len(master_agent.q_table)
    successful_episodes = []

    for batch_start in range(start_episode, num_episodes, batch_size):
        batch_end = min(batch_start + batch_size, num_episodes)
        current_batch_size = batch_end - batch_start

        print(f"\nProcessing Episodes {batch_start+1}-{batch_end} (Batch {batch_start//batch_size + 1})")

        # Progressive diversity increase
        diversity_level = 1.0 + (batch_start / num_episodes) * 3.0

        # Create args with optimized parameters
        args_list = [(batch_start + i + 1, batch_start + i, diversity_level) for i in range(current_batch_size)]

        # Run batch with memory monitoring
        batch_results = []
        with ProcessPoolExecutor(max_workers=num_workers) as executor:
            futures = [executor.submit(run_optimized_episode, args) for args in args_list]

            for future in as_completed(futures):
                result = future.result()
                batch_results.append(result)

                if result['success']:
                    episode = result['episode']
                    stats = result['stats']
                    diversity = stats['tribe_diversity']
                    print(f"Ep {episode:5d} | States: {len(stats['states_visited']):2d} | "
                          f"Combats: {stats['combats_initiated']:2d} | "
                          f"Success: {stats['successful_combats']/max(stats['combats_initiated'],1):.1%} | "
                          f"Pop: {min(diversity['populations']):4d}-{max(diversity['populations']):4d} | "
                          f"Reward: {stats['total_reward']:7.1f}")
                else:
                    print(f"Ep {result['episode']:5d} | ERROR: {result['error']}")

        # Process results and merge Q-tables
        successful_episodes.extend([r for r in batch_results if r['success']])

        # Merge Q-tables efficiently
        batch_states = set()
        for result in successful_episodes[-current_batch_size:]:  # Only process recent results
            if result['success']:
                for state in result['q_table'].keys():
                    batch_states.add(state)

                # Merge Q-values
                for state, q_values in result['q_table'].items():
                    if state not in master_agent.q_table:
                        master_agent.q_table[state] = q_values
                    else:
                        # Blend Q-values
                        for i in range(len(q_values)):
                            master_agent.q_table[state][i] = (
                                master_agent.q_table[state][i] * 0.7 + q_values[i] * 0.3
                            )

        # Update total states
        total_states_learned = len(master_agent.q_table)

        # Periodic checkpoint
        if (batch_end) % checkpoint_interval == 0 or batch_end >= num_episodes:
            checkpoint_path = os.path.join(checkpoint_dir, f"military_checkpoint_ep{batch_end}.json")
            checkpoint_data = {
                'episode': batch_end,
                'q_table': master_agent.q_table,
                'timestamp': datetime.now().isoformat(),
                'total_states': total_states_learned,
                'training_time': time.time() - start_time
            }

            with open(checkpoint_path, 'w') as f:
                json.dump(checkpoint_data, f, indent=2)

            print(f"Checkpoint saved: Episode {batch_end}, {total_states_learned} states ({total_states_learned/645120*100:.4f}%)")

        # Memory cleanup
        del batch_results
        gc.collect()

    # Final save
    final_path = "artifacts/models/military_qtable_ultra_optimized_final.json"
    master_agent.save_q_table(final_path)

    elapsed = time.time() - start_time
    final_coverage = (total_states_learned / 645120) * 100

    print("\n" + "=" * 80)
    print("OPTIMIZED ULTRA-EXTENDED TRAINING COMPLETE!")
    print(f"Total Episodes: {len(successful_episodes)}/{num_episodes}")
    print(f"Total States Learned: {total_states_learned}")
    print(f"Final State Coverage: {final_coverage:.4f}%")
    print(f"Total Training Time: {elapsed:.1f} seconds")
    print(f"Average States per Episode: {total_states_learned/max(1, len(successful_episodes)):.1f}")
    print(f"Final Model: {final_path}")
    print("=" * 80)


if __name__ == "__main__":
    # Optimized for quad-core: 8 workers, larger batches, memory optimization
    run_ultra_training_optimized(
        num_episodes=20000,
        num_workers=8,  # Optimal for quad-core
        checkpoint_interval=1000,
        batch_size=200  # Larger batches for better CPU utilization
    )