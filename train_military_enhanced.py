#!/usr/bin/env python3
"""
Enhanced Military RL Training with Better State Diversity
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


def create_diverse_tribes(world, tribal_manager, num_tribes=6):
    """Create tribes with highly diverse characteristics."""
    tribes_created = []

    for i in range(num_tribes):
        tribe_name = f"DiverseTribe_{i+1}_{random.randint(100,999)}"
        founder_id = f"founder_{tribe_name.lower()}"
        location = (random.randint(-50, 50), random.randint(-50, 50))

        # Diverse population ranges
        population_options = [
            random.randint(20, 80),    # Small tribes
            random.randint(150, 300),  # Medium tribes
            random.randint(400, 800),  # Large tribes
            random.randint(1000, 2000) # Huge tribes
        ]
        population = random.choice(population_options)

        # Diverse resource profiles
        resource_profiles = [
            {"food": random.randint(50, 150), "wood": random.randint(25, 100), "ore": random.randint(10, 50)},
            {"food": random.randint(200, 500), "wood": random.randint(150, 400), "ore": random.randint(75, 200)},
            {"food": random.randint(600, 1200), "wood": random.randint(500, 1000), "ore": random.randint(300, 600)},
        ]
        resources = random.choice(resource_profiles)

        # Create tribe
        tribal_manager.create_tribe(tribe_name, founder_id, location)

        # Create faction
        if tribe_name not in world.factions:
            from factions.faction import Faction
            faction = Faction(name=tribe_name)
            faction.territory = [location]
            faction.population = population
            faction.resources = resources
            world.factions[tribe_name] = faction

        tribes_created.append(tribe_name)

    return tribes_created


def run_enhanced_episode(episode_num, seed_offset=0):
    """Run a single episode with enhanced diversity."""
    try:
        world_seed = random.randint(0, 100000) + seed_offset * 1000 + episode_num * 500
        world = WorldEngine(seed=world_seed, disable_faction_saving=True)
        tribal_manager = TribalManager()
        world._tribal_manager = tribal_manager

        agent = MilitaryRLAgent(epsilon=0.95, lr=0.3, gamma=0.9)

        # Create diverse tribes (8-12 tribes)
        num_tribes = random.randint(8, 12)
        create_diverse_tribes(world, tribal_manager, num_tribes)

        episode_stats = {
            'combats_initiated': 0,
            'successful_combats': 0,
            'total_reward': 0,
            'states_visited': set(),
            'q_updates': []
        }

        # Run for 200 ticks (much longer than before)
        max_ticks = 200

        for tick in range(max_ticks):
            world.world_tick()

            active_tribes = list(tribal_manager.tribes.values())
            if len(active_tribes) < 2:
                continue

            # Multiple decisions per tick
            decisions_per_tick = random.randint(2, 5)

            for decision in range(decisions_per_tick):
                actor_tribe = random.choice(active_tribes)
                target_tribes = [t for t in active_tribes if t != actor_tribe]

                if not target_tribes:
                    continue

                target_tribe = random.choice(target_tribes)

                state_vector = agent.get_military_state(actor_tribe, [target_tribe])
                if state_vector is None:
                    continue

                action_idx = agent.choose_action(state_vector)
                actions = ['aggressive_attack', 'defensive_posture', 'strategic_retreat',
                          'force_reinforcement', 'tech_investment', 'diplomatic_pressure',
                          'siege_preparation', 'peaceful_approach']
                action_name = actions[action_idx]

                action_results = execute_military_action(action_name, actor_tribe, [target_tribe], tribal_manager, world)

                if action_name in ['aggressive_attack', 'siege_preparation']:
                    episode_stats['combats_initiated'] += 1
                    if action_results.get("success", False):
                        episode_stats['successful_combats'] += 1

                next_state_vector = agent.get_military_state(actor_tribe, [target_tribe])
                reward = compute_military_reward(action_results, state_vector, next_state_vector)

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


def run_enhanced_batch_training(num_episodes=100, num_workers=4):
    """Run enhanced batch training with better diversity."""
    print("ENHANCED MILITARY RL BATCH TRAINING")
    print("=" * 50)
    print("Features:")
    print("- Diverse tribe populations (20-2000)")
    print("- Varied resource distributions")
    print("- Longer episodes (200 ticks)")
    print("- More decisions per episode")
    print()

    print("Training Parameters:")
    print(f"- Episodes: {num_episodes}")
    print(f"- Workers: {num_workers}")
    print()

    start_time = time.time()

    # Run episodes in parallel
    args_list = [(i + 1, i) for i in range(num_episodes)]

    results = []
    with ProcessPoolExecutor(max_workers=num_workers) as executor:
        futures = [executor.submit(run_enhanced_episode, episode_num, seed_offset)
                  for episode_num, seed_offset in args_list]

        for future in as_completed(futures):
            result = future.result()
            results.append(result)

            if result['success']:
                episode = result['episode']
                stats = result['stats']
                success_rate = (stats['successful_combats'] / max(stats['combats_initiated'], 1)) * 100
                print(f"Episode {episode}: Combats={stats['combats_initiated']}, Success={stats['successful_combats']} ({success_rate:.1f}%), Reward={stats['total_reward']:.1f}, States={len(stats['states_visited'])}")
            else:
                print(f"Episode {result['episode']} failed: {result.get('error', 'Unknown error')}")
    # Aggregate results
    successful_episodes = [r for r in results if r['success']]
    total_combats = sum(r['stats']['combats_initiated'] for r in successful_episodes)
    total_successful = sum(r['stats']['successful_combats'] for r in successful_episodes)
    total_reward = sum(r['stats']['total_reward'] for r in successful_episodes)

    # Merge Q-tables
    master_agent = MilitaryRLAgent(epsilon=0.9, lr=0.2, gamma=0.9)
    all_states = set()

    for result in successful_episodes:
        for state, q_values in result['q_table'].items():
            all_states.add(state)
            if state not in master_agent.q_table:
                master_agent.q_table[state] = q_values.copy()
            else:
                # Average Q-values
                for i in range(len(q_values)):
                    master_agent.q_table[state][i] = (
                        master_agent.q_table[state][i] + q_values[i]
                    ) / 2

    # Save enhanced model
    save_path = "artifacts/models/military_qtable_enhanced.json"
    master_agent.save_q_table(save_path)

    elapsed = time.time() - start_time
    state_space = 645120
    coverage = (len(all_states) / state_space) * 100

    print("\n" + "=" * 50)
    print("ENHANCED TRAINING COMPLETE!")
    print("=" * 50)
    print(f"Successful Episodes: {len(successful_episodes)}/{num_episodes}")
    print(f"Total Combats: {total_combats}")
    print(f"Overall Success Rate: {total_successful/max(total_combats,1):.1%}")
    print(f"Total Reward: {total_reward:.1f}")
    print(f"States Learned: {len(all_states):,}")
    print(f"State Space Coverage: {coverage:.4f}%")
    print(f"Training Time: {elapsed:.1f}s")

    print("\nPERFORMANCE ANALYSIS:")
    print(f"- States per episode: {len(all_states)/max(len(successful_episodes),1):.1f}")
    print(f"- Combats per episode: {total_combats/max(len(successful_episodes),1):.1f}")

    if coverage >= 5:
        print("TARGET ACHIEVED: 5%+ state coverage!")
    elif coverage >= 1:
        print("MODERATE SUCCESS: 1%+ coverage")
    else:
        print("LOW COVERAGE: Need optimization")

    return len(all_states), coverage


if __name__ == "__main__":
    # Run enhanced training
    states_learned, coverage = run_enhanced_batch_training(num_episodes=50, num_workers=4)