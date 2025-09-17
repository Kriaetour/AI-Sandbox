#!/usr/bin/env python3
"""
Ultra-Extended Batch Training: Massive-scale training for Military RL Agent.

This script runs extremely long training sessions (10,000+ episodes) to achieve
10-20% state coverage of the 645,120 possible military states.

Features:
- Checkpointing every 1,000 episodes
- Progressive diversity increase
- Parallel processing with 8 workers
- Memory-efficient Q-table merging
- Progress tracking and statistics
"""

import time
import random
import json
import os
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

    # Ultra-diverse tribe characteristics with more variation
    tribe_types = [
        {"name": "Tiny_Outpost", "pop_range": (5, 50), "resource_multiplier": 0.2},
        {"name": "Small_Village", "pop_range": (20, 150), "resource_multiplier": 0.5},
        {"name": "Medium_Settlement", "pop_range": (100, 600), "resource_multiplier": 1.0},
        {"name": "Large_Town", "pop_range": (400, 1200), "resource_multiplier": 1.5},
        {"name": "Major_City", "pop_range": (1000, 2000), "resource_multiplier": 2.0},
        {"name": "Metropolis", "pop_range": (1800, 3000), "resource_multiplier": 3.0},
    ]

    # Increase diversity with episode progression
    if diversity_level > 1.0:
        # Add more extreme variations for later episodes
        tribe_types.extend([
            {"name": "Nomadic_Clan", "pop_range": (10, 100), "resource_multiplier": 0.3},
            {"name": "Fortified_Citadel", "pop_range": (800, 2500), "resource_multiplier": 2.5},
            {"name": "Tribal_Confederation", "pop_range": (1500, 4000), "resource_multiplier": 4.0},
        ])

    tribe_type = random.choice(tribe_types)
    base_name = f"{tribe_type['name']}_{episode_num}_{tribe_idx}"

    # Generate ultra-diverse location (much larger spread)
    location = (
        random.randint(-200, 200),
        random.randint(-200, 200)
    )

    # Generate population within type range with more variation
    population = random.randint(*tribe_type['pop_range'])
    # Add some random variation
    population = int(population * random.uniform(0.8, 1.3))

    # Generate resources with extreme variance
    resource_multiplier = tribe_type['resource_multiplier'] * random.uniform(0.5, 2.0)
    base_resources = {
        "food": int(random.randint(10, 1000) * resource_multiplier),
        "wood": int(random.randint(5, 800) * resource_multiplier),
        "ore": int(random.randint(1, 500) * resource_multiplier)
    }

    # Create tribe
    founder_id = f"founder_{base_name.lower()}"
    tribal_manager.create_tribe(base_name, founder_id, location)

    # Create corresponding faction with ultra-diverse characteristics
    if base_name not in world.factions:
        from factions.faction import Faction
        faction = Faction(name=base_name)
        faction.territory = [location]
        faction.population = population
        faction.resources = base_resources

        # Add extreme technology diversity
        tech_probability = min(0.8, 0.2 + diversity_level * 0.1)  # Up to 80% chance
        if random.random() < tech_probability:
            # Simulate technology unlocks with more variety
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


def run_ultra_episode(args):
    """Run a single ultra-diverse episode."""
    episode_num, seed_offset, diversity_level = args

    try:
        # Create ultra-diverse scenario
        world_seed = random.randint(0, 10000000) + seed_offset * 100000
        world = WorldEngine(seed=world_seed, disable_faction_saving=True)
        tribal_manager = TribalManager()
        world._tribal_manager = tribal_manager

        # Create agent with varying exploration
        epsilon = max(0.05, 0.3 - episode_num * 0.00001)  # Decrease exploration over time
        agent = MilitaryRLAgent(epsilon=epsilon, lr=0.15, gamma=0.92)

        # Create 8-16 tribes for maximum diversity
        num_tribes = random.randint(8, 16)

        # Initialize ultra-diverse tribes
        tribe_info = []
        for i in range(num_tribes):
            tribe_data = create_ultra_diverse_tribe(tribal_manager, world, episode_num, i, seed_offset, diversity_level)
            tribe_info.append(tribe_data)

        # Run episode with more decisions
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

        # Run for 200 ticks with decisions every 6 ticks (more frequent)
        for tick in range(0, 200, 6):
            world.world_tick()

            # Get all tribes
            active_tribes = list(tribal_manager.tribes.values())

            if len(active_tribes) < 2:
                continue

            # Make multiple decisions per tick for more state coverage
            num_decisions = random.randint(2, 5)
            for _ in range(num_decisions):
                # Select random tribe for military action
                actor_tribe = random.choice(active_tribes)
                target_tribes = [t for t in active_tribes if t != actor_tribe]

                if not target_tribes:
                    continue

                # Target multiple tribes for complex scenarios
                num_targets = min(len(target_tribes), random.randint(1, 4))
                selected_targets = random.sample(target_tribes, num_targets)

                # Get military state
                state_vector = agent.get_military_state(actor_tribe, selected_targets, world)
                if state_vector is None:
                    continue

                # Agent chooses action
                action_idx = agent.choose_action(state_vector)
                actions = ['aggressive_attack', 'defensive_posture', 'strategic_retreat',
                          'force_reinforcement', 'tech_investment', 'diplomatic_pressure',
                          'siege_preparation', 'peaceful_approach']
                action_name = actions[action_idx]

                # Execute action
                action_results = execute_military_action(action_name, actor_tribe, selected_targets, tribal_manager, world)

                # Track combat initiation
                if action_name in ['aggressive_attack', 'siege_preparation']:
                    episode_stats['combats_initiated'] += 1
                    if action_results.get("success", False):
                        episode_stats['successful_combats'] += 1

                # Get next state
                next_state_vector = agent.get_military_state(actor_tribe, selected_targets, world)

                # Get reward
                reward = compute_military_reward(action_results, state_vector, next_state_vector)

                # Agent learns
                if next_state_vector is not None:
                    agent.update_q_table(state_vector, action_idx, reward, next_state_vector)
                    episode_stats['q_updates'] += 1

                episode_stats['total_reward'] += reward
                episode_stats['states_visited'].add(tuple(state_vector) if isinstance(state_vector, list) else state_vector)

        return {
            'episode': episode_num,
            'stats': episode_stats,
            'q_table': agent.q_table,
            'success': True
        }

    except Exception as e:
        return {
            'episode': episode_num,
            'error': str(e),
            'success': False
        }


def save_checkpoint(master_agent, episode_num, total_states, start_time, checkpoint_dir="artifacts/checkpoints"):
    """Save training checkpoint."""
    os.makedirs(checkpoint_dir, exist_ok=True)

    checkpoint_data = {
        'episode': episode_num,
        'total_states': total_states,
        'training_time': time.time() - start_time,
        'timestamp': datetime.now().isoformat(),
        'q_table_size': len(master_agent.q_table),
        'state_coverage_percent': (total_states / 645120) * 100
    }

    checkpoint_path = f"{checkpoint_dir}/military_training_checkpoint_ep{episode_num}.json"
    master_agent.save_q_table(checkpoint_path)

    # Save metadata
    with open(f"{checkpoint_dir}/checkpoint_metadata_ep{episode_num}.json", 'w') as f:
        json.dump(checkpoint_data, f, indent=2)

    print(f"Checkpoint saved: Episode {episode_num}, {total_states} states ({total_states/645120:.4f}%)")


def run_ultra_training(num_episodes=20000, num_workers=8, checkpoint_interval=1000):
    """Run ultra-extended training to achieve 10-20% state coverage."""
    print("Starting Ultra-Extended Military RL Training")
    print(f"Target Episodes: {num_episodes} | Workers: {num_workers}")
    print("Goal: 10-20% state coverage (64K-129K states)")
    print("=" * 80)

    start_time = time.time()
    master_agent = MilitaryRLAgent(epsilon=0.1, lr=0.15, gamma=0.92)
    total_states_learned = 0

    # Process episodes in batches
    batch_size = 500
    for batch_start in range(0, num_episodes, batch_size):
        batch_end = min(batch_start + batch_size, num_episodes)
        current_batch_size = batch_end - batch_start

        print(f"\nProcessing Episodes {batch_start+1}-{batch_end} (Batch {batch_start//batch_size + 1})")

        # Increase diversity over time
        diversity_level = 1.0 + (batch_start / num_episodes) * 2.0

        # Create argument list for this batch
        args_list = [(batch_start + i + 1, batch_start + i, diversity_level) for i in range(current_batch_size)]

        # Run batch in parallel
        batch_results = []
        with ProcessPoolExecutor(max_workers=num_workers) as executor:
            futures = [executor.submit(run_ultra_episode, args) for args in args_list]

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

        # Process successful results
        successful_episodes = [r for r in batch_results if r['success']]

        # Merge Q-tables efficiently
        batch_states = set()
        for result in successful_episodes:
            for state in result['q_table'].keys():
                batch_states.add(state)

            for state, q_values in result['q_table'].items():
                if state not in master_agent.q_table:
                    master_agent.q_table[state] = q_values.copy()
                else:
                    # Weighted average favoring existing values
                    for i in range(len(q_values)):
                        existing = master_agent.q_table[state][i]
                        new_val = q_values[i]
                        master_agent.q_table[state][i] = (existing * 0.7 + new_val * 0.3)

        total_states_learned += len(batch_states)

        # Checkpoint every checkpoint_interval episodes
        if (batch_end) % checkpoint_interval == 0 or batch_end == num_episodes:
            save_checkpoint(master_agent, batch_end, total_states_learned, start_time)

        # Progress report
        elapsed = time.time() - start_time
        coverage_percent = (total_states_learned / 645120) * 100
        print(f"\nBatch Complete | Total States: {total_states_learned} | Coverage: {coverage_percent:.4f}%")
        print(f"Time Elapsed: {elapsed:.1f}s | Rate: {total_states_learned/elapsed:.1f} states/sec")

        # Check if we've reached target
        if coverage_percent >= 20.0:
            print("🎉 TARGET ACHIEVED: 20% state coverage reached!")
            break
        elif coverage_percent >= 10.0:
            print("✅ GOOD PROGRESS: 10% state coverage reached!")

    # Final save
    final_path = "artifacts/models/military_qtable_ultra_extended.json"
    master_agent.save_q_table(final_path)

    elapsed = time.time() - start_time
    final_coverage = (total_states_learned / 645120) * 100

    print("\n" + "=" * 80)
    print("ULTRA-EXTENDED TRAINING COMPLETE!")
    print(f"Total Episodes: {len([r for r in batch_results if r['success']])}/{num_episodes}")
    print(f"Total States Learned: {total_states_learned}")
    print(f"Final State Coverage: {final_coverage:.4f}%")
    print(f"Total Training Time: {elapsed:.1f} seconds")
    print(f"Average States per Episode: {total_states_learned/max(1, len(successful_episodes)):.1f}")
    print(f"Final Model: {final_path}")
    print("=" * 80)


if __name__ == "__main__":
    # Run ultra-extended training for maximum state coverage
    # Target: 10-20% of 645,120 states (64,512 - 129,024 states)
    run_ultra_training(num_episodes=20000, num_workers=8, checkpoint_interval=1000)