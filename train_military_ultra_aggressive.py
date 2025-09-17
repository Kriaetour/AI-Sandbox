#!/usr/bin/env python3
"""
Ultra-Aggressive Military RL Training - Maximum State Exploration
"""

import time
import random
import json
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime

def run_ultra_aggressive_episode(args):
    """Run episode with maximum exploration."""
    from world.engine import WorldEngine
    from tribes.tribal_manager import TribalManager
    from rl_military_agent import MilitaryRLAgent
    from rl_military_interface import (
        execute_military_action,
        compute_military_reward
    )

    episode_num, seed_offset = args

    try:
        # Maximum diversity setup
        world_seed = random.randint(0, 10000000) + seed_offset * 100000
        world = WorldEngine(seed=world_seed, disable_faction_saving=True)
        tribal_manager = TribalManager()
        world._tribal_manager = tribal_manager

        # Ultra-aggressive agent
        agent = MilitaryRLAgent(epsilon=0.6, lr=0.3, gamma=0.9)  # Maximum exploration

        # Create maximum tribe diversity
        num_tribes = random.randint(15, 25)  # Lots of tribes
        tribes = []

        for i in range(num_tribes):
            tribe = create_max_diversity_tribe(tribal_manager, world, episode_num, i, seed_offset)
            tribes.append(tribe)

        episode_stats = {
            'combats_initiated': 0,
            'successful_combats': 0,
            'total_reward': 0.0,
            'states_visited': set(),
            'q_updates': 0,
        }

        # Run for maximum time with frequent decisions
        for tick in range(0, 400, 3):  # More frequent decisions
            world.world_tick()

            active_tribes = list(tribal_manager.tribes.values())
            if len(active_tribes) < 3:  # Need at least 3 tribes for conflicts
                continue

            # Multiple aggressive decisions per tick
            num_decisions = random.randint(4, 10)  # Lots of decisions
            for _ in range(num_decisions):
                actor_tribe = random.choice(active_tribes)
                target_tribes = [t for t in active_tribes if t != actor_tribe]

                if len(target_tribes) < 2:
                    continue

                # Target multiple tribes aggressively
                num_targets = min(len(target_tribes), random.randint(3, 8))
                selected_targets = random.sample(target_tribes, num_targets)

                state_vector = agent.get_military_state(actor_tribe, selected_targets, world)
                if state_vector is None:
                    continue

                action_idx = agent.choose_action(state_vector)
                actions = ['aggressive_attack', 'defensive_posture', 'strategic_retreat',
                          'force_reinforcement', 'tech_investment', 'diplomatic_pressure',
                          'siege_preparation', 'peaceful_approach']
                action_name = actions[action_idx]

                action_results = execute_military_action(action_name, actor_tribe, selected_targets, tribal_manager, world)

                if action_name in ['aggressive_attack', 'siege_preparation']:
                    episode_stats['combats_initiated'] += 1
                    if action_results.get("success", False):
                        episode_stats['successful_combats'] += 1

                next_state_vector = agent.get_military_state(actor_tribe, selected_targets, world)
                reward = compute_military_reward(action_results, state_vector, next_state_vector)

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

def create_max_diversity_tribe(tribal_manager, world, episode_num, tribe_idx, seed_offset):
    """Create tribe with maximum possible diversity."""
    from technology_system import technology_manager

    random.seed(seed_offset + episode_num * 1000 + tribe_idx * 100)

    # All possible tribe types for maximum diversity
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
        {"name": "Mega_City", "pop_range": (3000, 6000), "resource_multiplier": 5.0},
        {"name": "Empire_Capital", "pop_range": (5000, 10000), "resource_multiplier": 8.0},
    ]

    tribe_type = random.choice(tribe_types)
    base_name = f"{tribe_type['name']}_{episode_num}_{tribe_idx}"

    # Create faction with extreme diversity
    faction = world.factions.create_faction(
        name=base_name,
        population=random.randint(*tribe_type['pop_range']),
        resources={
            'food': random.randint(1000, 10000) * tribe_type['resource_multiplier'],
            'wood': random.randint(1000, 10000) * tribe_type['resource_multiplier'],
            'ore': random.randint(500, 5000) * tribe_type['resource_multiplier'],
        }
    )

    # Maximum technology diversity - unlock everything possible
    all_techs = [
        "weapons", "iron_weapons", "steel_weapons", "military_organization",
        "siege_engineering", "horseback_riding", "archery", "shield_making",
        "castle_building", "naval_warfare", "gunpowder", "cannon"
    ]

    num_techs = random.randint(2, len(all_techs))
    tech_unlocks = random.sample(all_techs, num_techs)
    if tech_unlocks:
        technology_manager.unlocked_technologies[base_name] = set(tech_unlocks)

    world.factions[base_name] = faction
    return base_name

def run_ultra_aggressive_training(start_episode=20001, num_episodes=100000, num_workers=8):
    """Run ultra-aggressive training for maximum state coverage."""
    print("🔥 ULTRA-AGGRESSIVE Military RL Training")
    print(f"Starting from Episode: {start_episode}")
    print(f"Target Episodes: {num_episodes} | Workers: {num_workers}")
    print("Goal: Maximum state exploration towards 10-20% coverage")
    print("=" * 80)

    start_time = time.time()

    # Load from episode 20000 (last good checkpoint)
    from rl_military_agent import MilitaryRLAgent
    master_agent = MilitaryRLAgent(epsilon=0.6, lr=0.3, gamma=0.9)

    checkpoint_dir = "artifacts/checkpoints"
    model_file = f'{checkpoint_dir}/military_qtable_checkpoint_ep20000.json'
    if os.path.exists(model_file):
        master_agent.load_q_table(model_file)
        print("Loaded model from episode 20000")
    else:
        print("Starting with fresh model")

    total_states_learned = 600  # Start from known good point
    successful_episodes = []

    batch_size = 500  # Smaller batches for more frequent updates
    end_episode = start_episode + num_episodes

    for batch_start in range(start_episode, end_episode, batch_size):
        batch_end = min(batch_start + batch_size, end_episode)

        print(f"\n🔥 Processing Episodes {batch_start}-{batch_end} (Ultra-Aggressive)")

        # Submit ultra-aggressive episodes
        futures = []
        with ThreadPoolExecutor(max_workers=num_workers) as executor:
            for ep in range(batch_start, batch_end):
                seed_offset = ep // 1000
                future = executor.submit(run_ultra_aggressive_episode, (ep, seed_offset))
                futures.append(future)

            # Process results
            for future in as_completed(futures):
                result = future.result()
                if result['success']:
                    successful_episodes.append(result)

                    # Merge Q-table aggressively
                    for state, actions in result['q_table'].items():
                        if state not in master_agent.q_table:
                            master_agent.q_table[state] = actions.copy()
                            total_states_learned += 1  # Count new states
                        else:
                            # Update existing states
                            for action_idx, q_value in actions.items():
                                if action_idx not in master_agent.q_table[state]:
                                    master_agent.q_table[state][action_idx] = q_value
                                else:
                                    # Weighted average favoring new learning
                                    old_q = master_agent.q_table[state][action_idx]
                                    master_agent.q_table[state][action_idx] = (old_q * 0.7) + (q_value * 0.3)

                    if len(successful_episodes) % 100 == 0:
                        coverage = (total_states_learned / 645120) * 100
                        elapsed = time.time() - start_time
                        print(f"  Episode {result['episode']:6d} | Total States: {total_states_learned:6d} | "
                              f"Coverage: {coverage:6.2f}% | Time: {elapsed/60:.1f}m")

        # Save checkpoint every 2000 episodes
        if (batch_end - start_episode) % 2000 == 0:
            save_ultra_checkpoint(master_agent, batch_end, total_states_learned, start_time)

    # Final save
    final_path = "artifacts/models/military_qtable_ultra_aggressive_final.json"
    master_agent.save_q_table(final_path)

    elapsed = time.time() - start_time
    final_coverage = (total_states_learned / 645120) * 100

    print("\n" + "=" * 80)
    print("ULTRA-AGGRESSIVE TRAINING COMPLETE!")
    print(f"Total Episodes: {len(successful_episodes)}")
    print(f"Total States Learned: {total_states_learned}")
    print(f"Final State Coverage: {final_coverage:.4f}%")
    print(f"Total Training Time: {elapsed:.1f} seconds")
    print(f"Average States per Episode: {total_states_learned/max(1, len(successful_episodes)):.1f}")
    print(f"Final Model: {final_path}")
    print("=" * 80)

def save_ultra_checkpoint(master_agent, episode_num, total_states, start_time, checkpoint_dir="artifacts/checkpoints"):
    """Save ultra-aggressive checkpoint."""
    os.makedirs(checkpoint_dir, exist_ok=True)

    # Save metadata
    metadata = {
        'episode': episode_num,
        'total_states': total_states,
        'timestamp': datetime.now().isoformat(),
        'training_time': time.time() - start_time,
        'coverage_percent': (total_states / 645120) * 100
    }

    with open(f'{checkpoint_dir}/checkpoint_metadata_ep{episode_num}.json', 'w') as f:
        json.dump(metadata, f, indent=2)

    # Save model
    master_agent.save_q_table(f'{checkpoint_dir}/military_qtable_checkpoint_ep{episode_num}.json')

    coverage = (total_states / 645120) * 100
    print(f"💾 Ultra Checkpoint saved: Episode {episode_num}, {total_states} states ({coverage:.4f}%)")

if __name__ == "__main__":
    run_ultra_aggressive_training(start_episode=20001, num_episodes=100000, num_workers=8)