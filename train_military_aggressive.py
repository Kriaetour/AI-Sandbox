#!/usr/bin/env python3
"""
Aggressive Military RL Training - Optimized for Speed
"""

import time
import random
import json
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime

def run_ultra_episode_aggressive(args):
    """Run episode with aggressive exploration."""
    from world.engine import WorldEngine
    from tribes.tribal_manager import TribalManager
    from rl_military_agent import MilitaryRLAgent
    from rl_military_interface import (
        execute_military_action,
        compute_military_reward
    )

    episode_num, seed_offset, diversity_level = args

    try:
        # Ultra-fast scenario setup
        world_seed = random.randint(0, 10000000) + seed_offset * 100000
        world = WorldEngine(seed=world_seed, disable_faction_saving=True)
        tribal_manager = TribalManager()
        world._tribal_manager = tribal_manager

        # Aggressive agent settings
        agent = MilitaryRLAgent(epsilon=0.4, lr=0.2, gamma=0.95)  # Higher exploration, faster learning

        # Maximum tribe diversity
        num_tribes = random.randint(12, 20)  # More tribes = more potential conflicts

        # Create ultra-diverse tribes
        tribe_info = []
        for i in range(num_tribes):
            tribe_data = create_ultra_diverse_tribe(tribal_manager, world, episode_num, i, seed_offset, diversity_level)
            tribe_info.append(tribe_data)

        episode_stats = {
            'combats_initiated': 0,
            'successful_combats': 0,
            'total_reward': 0.0,
            'states_visited': set(),
            'q_updates': 0,
        }

        # Extended episode length for more learning
        for tick in range(0, 300, 4):  # More frequent decisions
            world.world_tick()

            active_tribes = list(tribal_manager.tribes.values())
            if len(active_tribes) < 2:
                continue

            # Multiple aggressive decisions per tick
            num_decisions = random.randint(3, 8)  # More decisions
            for _ in range(num_decisions):
                actor_tribe = random.choice(active_tribes)
                target_tribes = [t for t in active_tribes if t != actor_tribe]

                if not target_tribes:
                    continue

                # Target multiple tribes for more conflicts
                num_targets = min(len(target_tribes), random.randint(2, 6))
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

def create_ultra_diverse_tribe(tribal_manager, world, episode_num, tribe_idx, seed_offset, diversity_level=1.0):
    """Create tribe with maximum diversity."""
    from technology_system import technology_manager

    random.seed(seed_offset + episode_num * 1000 + tribe_idx * 100)

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

    tribe_type = random.choice(tribe_types)
    base_name = f"{tribe_type['name']}_{episode_num}_{tribe_idx}"

    # Create faction with extreme diversity
    faction = world.factions.create_faction(
        name=base_name,
        population=random.randint(*tribe_type['pop_range']),
        resources={
            'food': random.randint(100, 5000) * tribe_type['resource_multiplier'],
            'wood': random.randint(100, 5000) * tribe_type['resource_multiplier'],
            'ore': random.randint(50, 2500) * tribe_type['resource_multiplier'],
        }
    )

    # Maximum technology diversity
    tech_probability = min(0.9, 0.3 + diversity_level * 0.2)
    if random.random() < tech_probability:
        all_techs = [
            "weapons", "iron_weapons", "steel_weapons", "military_organization",
            "siege_engineering", "horseback_riding", "archery", "shield_making"
        ]
        num_techs = random.randint(1, min(len(all_techs), int(diversity_level * 4)))
        tech_unlocks = random.sample(all_techs, num_techs)
        if tech_unlocks:
            technology_manager.unlocked_technologies[base_name] = set(tech_unlocks)

    world.factions[base_name] = faction
    return base_name, faction.population, faction.resources

def run_aggressive_training(num_episodes=50000, num_workers=8, checkpoint_interval=2000):
    """Run aggressive training for faster learning."""
    print("🚀 Starting AGGRESSIVE Military RL Training")
    print(f"Target Episodes: {num_episodes} | Workers: {num_workers}")
    print("Goal: Accelerated learning towards 10-20% state coverage")
    print("=" * 80)

    start_time = time.time()

    # Try to resume
    master_agent, start_episode, total_states_learned = load_checkpoint()
    if master_agent is None:
        from rl_military_agent import MilitaryRLAgent
        master_agent = MilitaryRLAgent(epsilon=0.4, lr=0.2, gamma=0.95)
        start_episode = 0
        total_states_learned = 0
        print("Starting fresh aggressive training")

    batch_size = 1000  # Smaller batches for more frequent updates
    successful_episodes = []

    for batch_start in range(start_episode, num_episodes, batch_size):
        batch_end = min(batch_start + batch_size, num_episodes)

        print(f"\n⚡ Processing Episodes {batch_start+1}-{batch_end} (Aggressive Mode)")

        # Submit aggressive episodes
        futures = []
        with ThreadPoolExecutor(max_workers=num_workers) as executor:
            for ep in range(batch_start, batch_end):
                seed_offset = ep // 1000
                diversity_level = min(2.0, 1.0 + ep / 10000)
                future = executor.submit(run_ultra_episode_aggressive, (ep, seed_offset, diversity_level))
                futures.append(future)

            # Process results
            for future in as_completed(futures):
                result = future.result()
                if result['success']:
                    successful_episodes.append(result)
                    # Merge Q-table
                    for state, actions in result['q_table'].items():
                        if state not in master_agent.q_table:
                            master_agent.q_table[state] = actions.copy()
                        else:
                            for action_idx, q_value in actions.items():
                                if action_idx not in master_agent.q_table[state]:
                                    master_agent.q_table[state][action_idx] = q_value
                                else:
                                    master_agent.q_table[state][action_idx] = (
                                        master_agent.q_table[state][action_idx] + q_value
                                    ) / 2

                    # Count new states
                    new_states = len(result['stats']['states_visited'])
                    total_states_learned += new_states

                    if len(successful_episodes) % 50 == 0:
                        coverage = (total_states_learned / 645120) * 100
                        print(f"  Episode {result['episode']:5d} | New States: {new_states:2d} | "
                              f"Total: {total_states_learned:5d} | Coverage: {coverage:5.2f}%")

        # Save checkpoint
        if (batch_end - start_episode) % checkpoint_interval == 0:
            save_checkpoint(master_agent, batch_end, total_states_learned, start_time)

    # Final save
    final_path = "artifacts/models/military_qtable_aggressive_final.json"
    master_agent.save_q_table(final_path)

    elapsed = time.time() - start_time
    final_coverage = (total_states_learned / 645120) * 100

    print("\n" + "=" * 80)
    print("AGGRESSIVE TRAINING COMPLETE!")
    print(f"Total Episodes: {len(successful_episodes)}/{num_episodes}")
    print(f"Total States Learned: {total_states_learned}")
    print(f"Final State Coverage: {final_coverage:.4f}%")
    print(f"Total Training Time: {elapsed:.1f} seconds")
    print(f"Average States per Episode: {total_states_learned/max(1, len(successful_episodes)):.1f}")
    print(f"Final Model: {final_path}")
    print("=" * 80)

def load_checkpoint(checkpoint_dir="artifacts/checkpoints"):
    """Load latest checkpoint with actual learning progress."""
    from rl_military_agent import MilitaryRLAgent

    if not os.path.exists(checkpoint_dir):
        return None, 0, 0

    checkpoints = [f for f in os.listdir(checkpoint_dir) if f.startswith('checkpoint_metadata')]
    if not checkpoints:
        return None, 0, 0

    checkpoints.sort(key=lambda x: int(x.split('ep')[1].split('.')[0]))

    # Find the last checkpoint with actual learning (not just repeating 600 states)
    last_good_checkpoint = None
    for cp in reversed(checkpoints):
        try:
            with open(f'{checkpoint_dir}/{cp}', 'r') as f:
                data = json.load(f)
            if data.get('total_states', 0) > 600:  # Look for checkpoints with more than 600 states
                last_good_checkpoint = cp
                break
        except Exception:
            continue

    # If no checkpoint has more than 600 states, use episode 20000 (last good learning point)
    if last_good_checkpoint is None:
        last_good_checkpoint = "checkpoint_metadata_ep20000.json"

    episode_num = int(last_good_checkpoint.split('ep')[1].split('.')[0])

    with open(f'{checkpoint_dir}/{last_good_checkpoint}', 'r') as f:
        metadata = json.load(f)

    model_file = f'{checkpoint_dir}/military_qtable_checkpoint_ep{episode_num}.json'
    if os.path.exists(model_file):
        master_agent = MilitaryRLAgent(epsilon=0.4, lr=0.2, gamma=0.95)
        master_agent.load_q_table(model_file)
        total_states = metadata['total_states']
        print(f"Resumed from checkpoint: Episode {episode_num}, {total_states} states")
        return master_agent, episode_num, total_states
    else:
        return None, 0, 0

def save_checkpoint(master_agent, episode_num, total_states, start_time, checkpoint_dir="artifacts/checkpoints"):
    """Save checkpoint."""
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
    print(f"Checkpoint saved: Episode {episode_num}, {total_states} states ({coverage:.4f}%)")

if __name__ == "__main__":
    run_aggressive_training(num_episodes=50000, num_workers=8, checkpoint_interval=2000)