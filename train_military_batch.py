#!/usr/bin/env python3
"""
Batch Training: Parallel and grouped episode processing for Military RL Agent.

This script provides multiple batch processing approaches:
1. Parallel episodes using multiprocessing
2. Grouped batch episodes with shared learning
3. Vectorized scenario processing
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


def run_single_batch_episode(args):
    """Run a single episode for parallel processing."""
    episode_num, seed_offset = args

    try:
        # Create diverse scenario
        world_seed = random.randint(0, 100000) + seed_offset * 1000
        world = WorldEngine(seed=world_seed, disable_faction_saving=True)
        tribal_manager = TribalManager()
        world._tribal_manager = tribal_manager

        # Create agent for this episode (create locally to avoid pickling issues)
        agent = MilitaryRLAgent(epsilon=0.95, lr=0.2, gamma=0.9)

        # Create 5-8 tribes with randomization
        num_tribes = random.randint(5, 8)

        # Initialize tribes
        for i in range(num_tribes):
            tribe_name = f"Tribe_{episode_num}_{i+1}"
            founder_id = f"founder_{tribe_name.lower()}"
            location = (random.randint(-30, 30), random.randint(-30, 30))
            population = random.randint(50, 200)
            resources = {
                "food": random.randint(100, 500),
                "wood": random.randint(50, 400),
                "ore": random.randint(25, 200)
            }
            
            # Create tribe using correct method
            tribal_manager.create_tribe(tribe_name, founder_id, location)
            
            # Create corresponding faction
            if tribe_name not in world.factions:
                from factions.faction import Faction
                faction = Faction(name=tribe_name)
                faction.territory = [location]
                faction.population = population
                faction.resources = resources
                world.factions[tribe_name] = faction

        # Run episode
        episode_stats = {
            'combats_initiated': 0,
            'successful_combats': 0,
            'total_reward': 0.0,
            'states_visited': set(),
            'q_updates': []
        }

        # Run for 100 ticks with decisions every 10 ticks
        for tick in range(0, 100, 10):
            world.world_tick()

            # Get all tribes for military decisions
            active_tribes = list(tribal_manager.tribes.values())

            if len(active_tribes) < 2:
                continue

            # Select random tribe for military action
            actor_tribe = random.choice(active_tribes)
            target_tribes = [t for t in active_tribes if t != actor_tribe]

            if not target_tribes:
                continue

            target_tribe = random.choice(target_tribes)

            # Get military state (discretized)
            state_vector = agent.get_military_state(actor_tribe, [target_tribe], world)
            if state_vector is None:
                continue

            # Agent chooses action
            action_idx = agent.choose_action(state_vector)
            actions = ['aggressive_attack', 'defensive_posture', 'strategic_retreat',
                      'force_reinforcement', 'tech_investment', 'diplomatic_pressure',
                      'siege_preparation', 'peaceful_approach']
            action_name = actions[action_idx]

            # Execute action
            action_results = execute_military_action(action_name, actor_tribe, [target_tribe], tribal_manager, world)

            # Track combat initiation
            if action_name in ['aggressive_attack', 'siege_preparation']:
                episode_stats['combats_initiated'] += 1
                if action_results.get("success", False):
                    episode_stats['successful_combats'] += 1

            # Get next state (discretized)
            next_state_vector = agent.get_military_state(actor_tribe, [target_tribe], world)

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


def run_parallel_batch(num_episodes=50, num_workers=4):
    """Run episodes in parallel using multiprocessing."""
    print("Starting Parallel Batch Training")
    print(f"Episodes: {num_episodes} | Workers: {num_workers}")
    print("=" * 60)

    start_time = time.time()

    # Create argument list for parallel processing
    args_list = [(i + 1, i) for i in range(num_episodes)]

    # Run episodes in parallel
    results = []
    with ProcessPoolExecutor(max_workers=num_workers) as executor:
        futures = [executor.submit(run_single_batch_episode, args) for args in args_list]

        for future in as_completed(futures):
            result = future.result()
            results.append(result)

            if result['success']:
                episode = result['episode']
                stats = result['stats']
                print(f"Episode {episode:2d} | States: {len(stats['states_visited']):2d} | "
                      f"Combats: {stats['combats_initiated']:2d} | "
                      f"Success: {stats['successful_combats']/max(stats['combats_initiated'],1):.1%} | "
                      f"Reward: {stats['total_reward']:6.1f}")
            else:
                print(f"Episode {result['episode']:2d} | ERROR: {result['error']}")

    # Aggregate results
    successful_episodes = [r for r in results if r['success']]
    total_combats = sum(r['stats']['combats_initiated'] for r in successful_episodes)
    total_successful = sum(r['stats']['successful_combats'] for r in successful_episodes)
    total_reward = sum(r['stats']['total_reward'] for r in successful_episodes)

    # Merge Q-tables from all episodes
    master_agent = MilitaryRLAgent(epsilon=0.9, lr=0.2, gamma=0.9)
    for result in successful_episodes:
        for state, q_values in result['q_table'].items():
            if state not in master_agent.q_table:
                master_agent.q_table[state] = q_values
            else:
                # Average Q-values
                for i in range(len(q_values)):
                    master_agent.q_table[state][i] = (
                        master_agent.q_table[state][i] + q_values[i]
                    ) / 2

    # Save merged model
    save_path = "artifacts/models/military_qtable_batch_parallel.json"
    master_agent.save_q_table(save_path)

    elapsed = time.time() - start_time
    print("Parallel Batch Training Complete!")
    print(f"Successful Episodes: {len(successful_episodes)}/{num_episodes}")
    print(f"Total Combats: {total_combats}")
    print(f"Overall Success Rate: {total_successful/max(total_combats,1):.1%}")
    print(f"Total Reward: {total_reward:.1f}")
    print(f"States Learned: {len(master_agent.q_table)}")
    print(f"Training Time: {elapsed:.1f}s")
    print(f"Model saved to: {save_path}")


def run_grouped_batch(batch_size=10, num_batches=20):
    """Run episodes in groups, updating agent after each batch."""
    print("Starting Grouped Batch Training")
    print(f"Batch Size: {batch_size} | Num Batches: {num_batches}")
    print("=" * 60)

    start_time = time.time()

    # Master agent that accumulates learning
    master_agent = MilitaryRLAgent(epsilon=0.95, lr=0.2, gamma=0.9)

    total_combats = 0
    total_successful = 0
    total_reward = 0

    for batch in range(num_batches):
        print(f"\n[*] Processing Batch {batch + 1}/{num_batches}")

        batch_results = []

        # Run episodes in this batch
        for episode_in_batch in range(batch_size):
            episode_num = batch * batch_size + episode_in_batch + 1

            try:
                result = run_single_batch_episode((episode_num, episode_num))
                batch_results.append(result)

                if result['success']:
                    stats = result['stats']
                    print(f"  Episode {episode_num:2d} | States: {len(stats['states_visited']):2d} | "
                          f"Combats: {stats['combats_initiated']:2d} | "
                          f"Success: {stats['successful_combats']/max(stats['combats_initiated'],1):.1%} | "
                          f"Reward: {stats['total_reward']:6.1f}")

            except Exception as e:
                print(f"  Episode {episode_num:2d} | ERROR: {e}")

        # Merge Q-tables from this batch into master agent
        for result in batch_results:
            if result['success']:
                for state, q_values in result['q_table'].items():
                    if state not in master_agent.q_table:
                        master_agent.q_table[state] = q_values.copy()
                    else:
                        # Weighted average favoring master agent
                        for i in range(len(q_values)):
                            master_agent.q_table[state][i] = (
                                master_agent.q_table[state][i] * 0.7 + q_values[i] * 0.3
                            )

        # Update statistics
        successful_in_batch = [r for r in batch_results if r['success']]
        batch_combats = sum(r['stats']['combats_initiated'] for r in successful_in_batch)
        batch_successful = sum(r['stats']['successful_combats'] for r in successful_in_batch)
        batch_reward = sum(r['stats']['total_reward'] for r in successful_in_batch)

        total_combats += batch_combats
        total_successful += batch_successful
        total_reward += batch_reward

        # Progress update
        elapsed = time.time() - start_time
        overall_success = total_successful / max(total_combats, 1)
        print(f"  Batch {batch + 1} Complete | Total States: {len(master_agent.q_table)} | "
              f"Overall Success: {overall_success:.1%} | Time: {elapsed:.1f}s")

        # Save checkpoint
        if (batch + 1) % 5 == 0:
            checkpoint_path = f"artifacts/models/military_qtable_batch_checkpoint_{batch + 1}.json"
            master_agent.save_q_table(checkpoint_path)
            print(f"  [+] Checkpoint saved to {checkpoint_path}")

    # Final save
    final_path = "artifacts/models/military_qtable_batch_grouped.json"
    master_agent.save_q_table(final_path)

    elapsed = time.time() - start_time
    print("Grouped Batch Training Complete!")
    print(f"Total Episodes: {batch_size * num_batches}")
    print(f"Total Combats: {total_combats}")
    print(f"Overall Success Rate: {total_successful/max(total_combats,1):.1%}")
    print(f"Total Reward: {total_reward:.1f}")
    print(f"States Learned: {len(master_agent.q_table)}")
    print(f"Training Time: {elapsed:.1f}s")
    print(f"Model saved to: {final_path}")


def run_vectorized_batch(num_scenarios=20, ticks_per_scenario=50):
    """Run multiple scenarios simultaneously in vectorized fashion."""
    print("Starting Vectorized Batch Training")
    print(f"Scenarios: {num_scenarios} | Ticks per Scenario: {ticks_per_scenario}")
    print("=" * 60)

    start_time = time.time()

    # Create multiple worlds and agents
    worlds = []
    agents = []
    tribal_managers = []

    for i in range(num_scenarios):
        world_seed = random.randint(0, 100000) + i * 1000
        world = WorldEngine(seed=world_seed, disable_faction_saving=True)
        tribal_manager = TribalManager()
        world._tribal_manager = tribal_manager

        # Create tribes for this scenario
        num_tribes = random.randint(4, 7)
        for j in range(num_tribes):
            tribe_name = f"VecTribe_{i}_{j+1}"
            founder_id = f"founder_{tribe_name.lower()}"
            location = (random.randint(-25, 25), random.randint(-25, 25))
            population = random.randint(50, 150)
            resources = {
                "food": random.randint(100, 300),
                "wood": random.randint(50, 200),
                "ore": random.randint(25, 100)
            }
            
            # Create tribe using correct method
            tribal_manager.create_tribe(tribe_name, founder_id, location)
            
            # Create corresponding faction
            if tribe_name not in world.factions:
                from factions.faction import Faction
                faction = Faction(name=tribe_name)
                faction.territory = [location]
                faction.population = population
                faction.resources = resources
                world.factions[tribe_name] = faction

        worlds.append(world)
        tribal_managers.append(tribal_manager)
        agents.append(MilitaryRLAgent(epsilon=0.9, lr=0.2, gamma=0.9))

    # Master agent for accumulating learning
    master_agent = MilitaryRLAgent(epsilon=0.9, lr=0.2, gamma=0.9)

    total_combats = 0
    total_successful = 0
    total_reward = 0

    # Run all scenarios simultaneously
    for tick in range(0, ticks_per_scenario, 10):
        print(f"Tick {tick}/{ticks_per_scenario}")

        # Process each scenario
        for scenario_idx, (world, tribal_manager, agent) in enumerate(zip(worlds, tribal_managers, agents)):
            world.world_tick()

            active_tribes = list(tribal_manager.tribes.values())
            if len(active_tribes) < 2:
                continue

            # Make multiple decisions per scenario per tick
            for decision in range(3):  # 3 decisions per tick
                actor_tribe = random.choice(active_tribes)
                target_tribes = [t for t in active_tribes if t != actor_tribe]

                if not target_tribes:
                    continue

                target_tribe = random.choice(target_tribes)

                # Get state and make decision
                state = agent.get_military_state(actor_tribe, [target_tribe])
                action_idx = agent.choose_action(state)
                actions = ['aggressive_attack', 'defensive_posture', 'strategic_retreat',
                          'force_reinforcement', 'tech_investment', 'diplomatic_pressure',
                          'siege_preparation', 'peaceful_approach']
                action_name = actions[action_idx]

                # Execute action
                action_results = execute_military_action(action_name, actor_tribe, [target_tribe], tribal_manager, world)

                # Get next state
                next_state = agent.get_military_state(actor_tribe, [target_tribe])

                # Track stats
                if action_name in ['aggressive_attack', 'siege_preparation']:
                    total_combats += 1
                    if action_results.get("success", False):
                        total_successful += 1

                # Get reward and learn
                reward = compute_military_reward(action_results, state, next_state)
                total_reward += reward

                if next_state is not None:
                    agent.update_q_table(state, action_idx, reward, next_state)

                    # Also update master agent
                    master_agent.update_q_table(state, action_idx, reward, next_state)

        # Progress update every 10 ticks
        if tick % 50 == 0 and tick > 0:
            elapsed = time.time() - start_time
            success_rate = total_successful / max(total_combats, 1)
            print(f"  Progress | Combats: {total_combats} | Success: {success_rate:.1%} | "
                  f"Reward: {total_reward:6.1f} | States: {len(master_agent.q_table)} | "
                  f"Time: {elapsed:.1f}s")

    # Save final model
    save_path = "artifacts/models/military_qtable_batch_vectorized.json"
    master_agent.save_q_table(save_path)

    elapsed = time.time() - start_time
    success_rate = total_successful / max(total_combats, 1)

    print("Vectorized Batch Training Complete!")
    print(f"Scenarios: {num_scenarios}")
    print(f"Total Combats: {total_combats}")
    print(f"Overall Success Rate: {success_rate:.1%}")
    print(f"Total Reward: {total_reward:.1f}")
    print(f"States Learned: {len(master_agent.q_table)}")
    print(f"Training Time: {elapsed:.1f}s")
    print(f"Model saved to: {save_path}")


def main():
    """Main function with batch training options."""
    print("Military RL Agent - Batch Training Options")
    print("=" * 60)
    print("1. Parallel Batch (Fastest - uses multiple CPU cores)")
    print("2. Grouped Batch (Balanced - processes in groups)")
    print("3. Vectorized Batch (Intensive - multiple scenarios simultaneously)")
    print("=" * 60)

    try:
        choice = input("Select batch training mode (1-3): ").strip()

        if choice == "1":
            num_episodes = int(input("Number of episodes (default 50): ") or "50")
            num_workers = int(input("Number of workers (default 4): ") or "4")
            run_parallel_batch(num_episodes, num_workers)

        elif choice == "2":
            batch_size = int(input("Batch size (default 10): ") or "10")
            num_batches = int(input("Number of batches (default 20): ") or "20")
            run_grouped_batch(batch_size, num_batches)

        elif choice == "3":
            num_scenarios = int(input("Number of scenarios (default 20): ") or "20")
            ticks_per_scenario = int(input("Ticks per scenario (default 50): ") or "50")
            run_vectorized_batch(num_scenarios, ticks_per_scenario)

        else:
            print("Invalid choice. Running parallel batch by default...")
            run_parallel_batch(50, 4)

    except KeyboardInterrupt:
        print("\n[!] Training interrupted by user")
    except Exception as e:
        print(f"\nError during training: {e}")


if __name__ == "__main__":
    main()