#!/usr/bin/env python3
"""
Enhanced Batch Training: High-diversity scenario generation for Military RL Agent.

This script creates diverse training scenarios with:
- Wide population ranges (20-2000)
- Varied resource distributions
- Different technology levels
- Geographic spread
- Multiple tribe compositions
"""

import time
import random
from concurrent.futures import ProcessPoolExecutor, as_completed

from world.engine import WorldEngine
from tribes.tribal_manager import TribalManager
from rl_military_agent import MilitaryRLAgent
from rl_military_interface import (
    execute_military_action,
    compute_military_reward
)
from technology_system import technology_manager


def create_diverse_tribe(tribal_manager, world, episode_num, tribe_idx, seed_offset):
    """Create a tribe with diverse characteristics."""
    random.seed(seed_offset + episode_num * 100 + tribe_idx * 10)

    # Diverse tribe characteristics
    tribe_types = [
        {"name": "Small_Village", "pop_range": (20, 100), "resource_multiplier": 0.5},
        {"name": "Medium_Settlement", "pop_range": (100, 500), "resource_multiplier": 1.0},
        {"name": "Large_Town", "pop_range": (500, 1200), "resource_multiplier": 1.5},
        {"name": "Major_City", "pop_range": (1200, 2000), "resource_multiplier": 2.0},
    ]

    tribe_type = random.choice(tribe_types)
    base_name = f"{tribe_type['name']}_{episode_num}_{tribe_idx}"

    # Generate diverse location (much larger spread)
    location = (
        random.randint(-100, 100),
        random.randint(-100, 100)
    )

    # Generate population within type range
    population = random.randint(*tribe_type['pop_range'])

    # Generate resources with high variance
    resource_multiplier = tribe_type['resource_multiplier']
    base_resources = {
        "food": int(random.randint(50, 800) * resource_multiplier),
        "wood": int(random.randint(25, 600) * resource_multiplier),
        "ore": int(random.randint(10, 400) * resource_multiplier)
    }

    # Create tribe
    founder_id = f"founder_{base_name.lower()}"
    tribal_manager.create_tribe(base_name, founder_id, location)

    # Create corresponding faction with diverse characteristics
    if base_name not in world.factions:
        from factions.faction import Faction
        faction = Faction(name=base_name)
        faction.territory = [location]
        faction.population = population
        faction.resources = base_resources

        # Add some technology diversity
        if random.random() < 0.3:  # 30% chance of advanced tech
            # Simulate some technology unlocks
            tech_unlocks = random.sample([
                "weapons", "iron_weapons", "military_organization"
            ], random.randint(0, 2))
            if tech_unlocks:
                technology_manager.unlocked_technologies[base_name] = set(tech_unlocks)

        world.factions[base_name] = faction

    return base_name, population, base_resources


def run_enhanced_batch_episode(args):
    """Run a single episode with enhanced diversity."""
    episode_num, seed_offset = args

    try:
        # Create diverse scenario with unique seed
        world_seed = random.randint(0, 1000000) + seed_offset * 10000
        world = WorldEngine(seed=world_seed, disable_faction_saving=True)
        tribal_manager = TribalManager()
        world._tribal_manager = tribal_manager

        # Create agent for this episode
        agent = MilitaryRLAgent(epsilon=0.95, lr=0.2, gamma=0.9)

        # Create 6-12 tribes with maximum diversity
        num_tribes = random.randint(6, 12)

        # Initialize diverse tribes
        tribe_info = []
        for i in range(num_tribes):
            tribe_data = create_diverse_tribe(tribal_manager, world, episode_num, i, seed_offset)
            tribe_info.append(tribe_data)

        # Run episode with more frequent decisions
        episode_stats = {
            'combats_initiated': 0,
            'successful_combats': 0,
            'total_reward': 0.0,
            'states_visited': set(),
            'q_updates': [],
            'tribe_diversity': {
                'populations': [info[1] for info in tribe_info],
                'total_resources': [sum(info[2].values()) for info in tribe_info]
            }
        }

        # Run for 150 ticks with decisions every 8 ticks (more frequent)
        for tick in range(0, 150, 8):
            world.world_tick()

            # Get all tribes
            active_tribes = list(tribal_manager.tribes.values())

            if len(active_tribes) < 2:
                continue

            # Select random tribe for military action
            actor_tribe = random.choice(active_tribes)
            target_tribes = [t for t in active_tribes if t != actor_tribe]

            if not target_tribes:
                continue

            # Sometimes target multiple tribes for more complex scenarios
            num_targets = min(len(target_tribes), random.randint(1, 3))
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
                episode_stats['q_updates'].append((state_vector, action_idx, reward, next_state_vector))

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


def run_enhanced_parallel_batch(num_episodes=100, num_workers=4):
    """Run enhanced episodes in parallel with maximum diversity."""
    print("Starting Enhanced Parallel Batch Training")
    print(f"Episodes: {num_episodes} | Workers: {num_workers}")
    print("Enhanced Features: Wide population ranges, diverse resources, technology variation")
    print("=" * 80)

    start_time = time.time()

    # Create argument list
    args_list = [(i + 1, i) for i in range(num_episodes)]

    # Run episodes in parallel
    results = []
    with ProcessPoolExecutor(max_workers=num_workers) as executor:
        futures = [executor.submit(run_enhanced_batch_episode, args) for args in args_list]

        for future in as_completed(futures):
            result = future.result()
            results.append(result)

            if result['success']:
                episode = result['episode']
                stats = result['stats']
                diversity = stats['tribe_diversity']
                print(f"Episode {episode:3d} | States: {len(stats['states_visited']):2d} | "
                      f"Combats: {stats['combats_initiated']:2d} | "
                      f"Success: {stats['successful_combats']/max(stats['combats_initiated'],1):.1%} | "
                      f"Pop Range: {min(diversity['populations']):4d}-{max(diversity['populations']):4d} | "
                      f"Reward: {stats['total_reward']:7.1f}")
            else:
                print(f"Episode {result['episode']:3d} | ERROR: {result['error']}")

    # Aggregate results
    successful_episodes = [r for r in results if r['success']]
    total_combats = sum(r['stats']['combats_initiated'] for r in successful_episodes)
    total_successful = sum(r['stats']['successful_combats'] for r in successful_episodes)
    total_reward = sum(r['stats']['total_reward'] for r in successful_episodes)
    total_states = sum(len(r['stats']['states_visited']) for r in successful_episodes)

    # Merge Q-tables
    master_agent = MilitaryRLAgent(epsilon=0.9, lr=0.2, gamma=0.9)
    all_states = set()
    for result in successful_episodes:
        for state in result['q_table'].keys():
            all_states.add(state)
        for state, q_values in result['q_table'].items():
            if state not in master_agent.q_table:
                master_agent.q_table[state] = q_values
            else:
                # Average Q-values
                for i in range(len(q_values)):
                    master_agent.q_table[state][i] = (
                        master_agent.q_table[state][i] + q_values[i]
                    ) / 2

    # Save enhanced model
    save_path = "artifacts/models/military_qtable_enhanced_diversity.json"
    master_agent.save_q_table(save_path)

    elapsed = time.time() - start_time
    print("\nEnhanced Batch Training Complete!")
    print(f"Successful Episodes: {len(successful_episodes)}/{num_episodes}")
    print(f"Total States Learned: {len(all_states)}")
    print(f"State Coverage: {len(all_states)/645120:.6f}%")
    print(f"Total Combats: {total_combats}")
    print(f"Overall Success Rate: {total_successful/max(total_combats,1):.1%}")
    print(f"Total Reward: {total_reward:.1f}")
    print(f"Training Time: {elapsed:.1f} seconds")
    print(f"States per Episode: {total_states/len(successful_episodes):.1f}")
    print(f"Model saved to: {save_path}")


if __name__ == "__main__":
    # Run enhanced training with diversity focus - MUCH LONGER TRAINING
    run_enhanced_parallel_batch(num_episodes=500, num_workers=4)